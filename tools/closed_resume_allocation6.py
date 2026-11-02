"""Preserve exact closed comparison paths, sharing only non-archive duplicate inodes."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess

import assembly6
from closed_pilot_allocation6 import MANIFEST, MANIFEST_SHA, candidate
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, utc
from wire_workflow6 import require

TARGETS = (
 ('initial-lower-global-narrow-20261015', 'initial-lower-global-narrow6',
  'd465484ccdabcc1493d4d8f7389e04d5e5d7aa168f5174711cc9b706487fc28b',
  'e7546f897a988f9dcd9bb9c67fdecc32bf7c51a34fa18cbc8fd36716ec7afeeb'),
 ('initial-lower-global-direct-20261013', 'initial-lower-global-direct6',
  'b969982ff0dc3dbb6fae6cbdb778d0e850df28b29f6591df81b5ee4a17aa12d3',
  '90c69a986e0d659a296d4ec299a08aadf18b2180d612637a7cb9df27930d93a2'),
 ('initial-lower-global-private-20261013', 'initial-lower-global-private6',
  'eb38d1a8f2f078104962425da66984c5095eaae1acfb2bc601429696b8bd50b4',
  '4f664085ad69ec8afd6e6c580fc1cfa1fb65d2f207010af71282b38619cd0203'))
DONOR = ('initial-lower-global-named-resume-20261012', 'initial-lower-global-named6',
 'ebda1e507d094dac7b63cf5032db62935676b9e129d2529e67c6bae65f983388',
 'd9b784fa425dfa284c550ecaad3305580de471d05754933d1cc9f81a68412220')


def inspect(runs, spec):
    label, folder, receipt_sha, report_sha = spec
    outer = runs / ('six-' + label); base = outer / 'results' / folder; check = base / 'check'
    receipt = outer / 'results' / (label + '.json'); report = base / 'report.json'
    require(assembly6.sha(receipt) == receipt_sha and assembly6.sha(report) == report_sha,
            'exact terminal comparison receipts required')
    rec = json.loads(receipt.read_text()); data = json.loads(report.read_text())
    state = subprocess.run(['systemctl','--user','show','othello6-'+label+'.service',
        '-p','MainPID','-p','ActiveState'], capture_output=True, text=True).stdout
    require('MainPID=0' in state and 'ActiveState=active' not in state
            and 'ActiveState=activating' not in state and rec['finished_utc']
            and rec['source_unchanged'] and rec['expected_source_matches'], 'terminal source only')
    require(rec['source_sha256'] == source_identity(outer)['source_sha256'], 'frozen outer source changed')
    source, pool = source_identity(check), assembly6.interfaces(check)
    require(source == data['checked_source'] and digest_entries(pool) == data['last_interface_pool_sha256'],
            'closed comparison sources or interface pool changed')
    if not data['accepted']:
        gate = data['last_storage_gate']
        require(label == TARGETS[0][0] and data['status'] == 'checking' and rec['exit_code'] == 1
            and gate['allocated_study_bytes'] + gate['reserved_extra_bytes'] >= 10*2**30
            and len(data['phases']) == 73 and all(p['record']['accepted'] for p in data['phases']),
            'only the recorded accepted storage-stop prefix is allowed')
    else:
        require(data['status'] == 'complete' and rec['accepted'], 'complete donor acceptance required')
    return check, dict(source=source,pool=pool,receipt_sha256=receipt_sha,report_sha256=report_sha,
                      receipt=str(receipt),report=str(report))


def recover(runs, output):
    runs, output = Path(runs).resolve(), Path(output).absolute()
    require(not output.exists() and runs in output.parents, 'fresh same-study maintenance receipt required')
    require(assembly6.sha(MANIFEST) == MANIFEST_SHA, 'archive manifest pin changed')
    original = json.loads(MANIFEST.read_text())
    protected = {tuple(row['source_inode']) for row in original['entries'].values()}; del original
    donor, ds = inspect(runs, DONOR); db = dict(source_files(donor)); checks = {str(donor): ds}; rows = []
    for spec in TARGETS:
        check, state = inspect(runs, spec); checks[str(check)] = state; sources = dict(source_files(check))
        for name in list(state['pool']) + list(sources):
            interface = name in state['pool']
            if (ds['pool'].get(name) != state['pool'][name] if interface else db.get(name) != sources[name]):
                continue
            target, canonical = check/name, donor/name
            if not candidate(target, canonical, protected): continue
            if interface:
                src = name.split('/agda/',1)[1][:-1]
                require(sources[src] == db[src], 'matching interface source required')
            h = assembly6.sha(target); require(assembly6.sha(canonical) == h, 'duplicate bytes differ')
            st = target.stat(); rows.append(dict(path=str(target),canonical=str(canonical),sha256=h,
                original_inode=st.st_ino,mtime_ns=st.st_mtime_ns,mode=st.st_mode,allocated_bytes=st.st_blocks*512))
    plan = dict(checks=checks,replacements=rows,archive_manifest_sha256=MANIFEST_SHA,
                protected_inode_count=len(protected),created_utc=utc())
    raw = gzip.compress(json.dumps(plan,separators=(',',':')).encode(),mtime=0)
    journal = output.with_suffix('.plan.json.gz');require(not journal.exists(),'fresh journal required')
    require(allocated(runs) + len(raw) + 2**20 < 10*2**30, 'maintenance must fit existing artifact cap')
    with journal.open('xb') as f: f.write(raw);f.flush();os.fsync(f.fileno())
    result = dict(format='othello-closed-resume-allocation6-v1',status='prepared',created_utc=utc(),
        journal=str(journal),journal_sha256=hashlib.sha256(raw).hexdigest(),replacements=len(rows),
        before_allocated_bytes=allocated(runs),protected_archive_inodes_excluded=True)
    atomic_json(output,result)
    for row in rows:
        a,b=Path(row['path']),Path(row['canonical']);tmp=a.with_name(a.name+'.resume-share-tmp')
        require(not tmp.exists() and candidate(a,b,protected)
            and assembly6.sha(a)==assembly6.sha(b)==row['sha256'], 'copy changed since prepared journal')
        os.link(b,tmp);os.replace(tmp,a)
    for path, state in checks.items():
        check=Path(path)
        require(source_identity(check)==state['source'] and assembly6.interfaces(check)==state['pool']
            and assembly6.sha(Path(state['receipt']))==state['receipt_sha256']
            and assembly6.sha(Path(state['report']))==state['report_sha256'],'protected closed evidence changed')
    require(assembly6.sha(MANIFEST)==MANIFEST_SHA,'original manifest changed')
    result.update(status='complete',finished_utc=utc(),recovered_allocated_bytes=sum(r['allocated_bytes'] for r in rows),
        after_allocated_bytes=allocated(runs),all_source_and_interface_bytes_preserved=True,
        all_receipts_preserved=True,future_writable_checks_require_private_copy=True)
    atomic_json(output,result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(recover(a.runs,a.output)))
