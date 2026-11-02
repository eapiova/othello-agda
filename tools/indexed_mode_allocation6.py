#!/usr/bin/env python3
"""Reclaim exact closed experiment duplicates before a private new check."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from archive_indexed_support6 import FROZEN, SOURCE
from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger
from wire_workflow6 import require

LABEL = 'indexed-mode-allocation-20261009'


def valid_folder(folder):
    """Allow bounded nested result directories, never traversal or aliases."""
    return (isinstance(folder, str) and
            bool(re.fullmatch(r'[A-Za-z0-9-]+(?:/[A-Za-z0-9-]+){0,2}', folder)))


CODE = r'''
import json,os,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'tools'))
import assembly6
from owner_cache_dedup6 import allocated
from provenance import digest_entries,source_identity
from run_job import atomic_json,utc
runs=root.parent;output=root/'results'/sys.argv[3];assert not output.exists()
donor_label,donor_folder,donor_hash=json.loads(sys.argv[4])
donor_outer=runs/('six-'+donor_label)
donor=donor_outer/'results'/donor_folder/'check'
report=donor.parent/'report.json'
assert assembly6.sha(report)==donor_hash
data=json.loads(report.read_text());donor_source=source_identity(donor);donor_pool=assembly6.interfaces(donor)
assert donor_source==data['checked_source'] and digest_entries(donor_pool)==data['last_interface_pool_sha256']
status=subprocess.run(['systemctl','--user','show','othello6-'+donor_label+'.service','-p','ActiveState','-p','MainPID'],capture_output=True,text=True,check=True).stdout
assert 'ActiveState=active' not in status and 'MainPID=0' in status
protected={str(report):assembly6.sha(report)}
roots={};rows=[];source_rows=[]
from provenance import source_files
donor_sources={n:p for n,p in source_files(donor)}
for label,folder,report_hash in json.loads(sys.argv[2]):
 outer=runs/('six-'+label);check=outer/'results'/folder/'check';rp=check.parent/'report.json'
 assert assembly6.sha(rp)==report_hash
 status=subprocess.run(['systemctl','--user','show','othello6-'+label+'.service','-p','ActiveState','-p','MainPID'],capture_output=True,text=True,check=True).stdout
 assert 'ActiveState=active' not in status and 'MainPID=0' in status
 actual=outer/'results'/(label+'.json');a=json.loads(actual.read_text());r=json.loads(rp.read_text())
 assert a.get('finished_utc') and a['source_unchanged'] and a['expected_source_matches']
 assert bool(a['accepted'])==bool(r['accepted'])
 identity=source_identity(check);pool=assembly6.interfaces(check)
 assert identity==r['checked_source'] and digest_entries(pool)==r['last_interface_pool_sha256']
 roots[str(check)]={'source':identity,'pool':pool}
 protected[str(rp)]=report_hash;protected[str(actual)]=assembly6.sha(actual)
 for name,h in pool.items():
  if donor_pool.get(name)!=h:continue
  target=check/name;canonical=donor/name
  assert not target.is_symlink() and not canonical.is_symlink()
  x=target.stat();y=canonical.stat()
  if (x.st_dev,x.st_ino)==(y.st_dev,y.st_ino) or x.st_nlink!=1:continue
  if (x.st_size,x.st_mtime_ns,x.st_mode,x.st_dev)!=(y.st_size,y.st_mtime_ns,y.st_mode,y.st_dev):continue
  source=name.split('/agda/',1)[1][:-1]
  assert (check/source).read_bytes()==(donor/source).read_bytes()
  rows.append({'path':str(target),'canonical':str(canonical),'sha256':h,'mtime_ns':x.st_mtime_ns,'mode':x.st_mode,
               'original_inode':x.st_ino,'reclaimed_allocated_bytes':x.st_blocks*512})
 for name,content in source_files(check):
  if donor_sources.get(name)!=content:continue
  target=check/name;canonical=donor/name;x=target.stat();y=canonical.stat()
  if (x.st_dev,x.st_ino)==(y.st_dev,y.st_ino) or x.st_nlink!=1:continue
  if (x.st_size,x.st_mtime_ns,x.st_mode,x.st_dev)!=(y.st_size,y.st_mtime_ns,y.st_mode,y.st_dev):continue
  assert not target.is_symlink() and not canonical.is_symlink()
  source_rows.append({'path':str(target),'canonical':str(canonical),'sha256':assembly6.sha(target),
    'mtime_ns':x.st_mtime_ns,'mode':x.st_mode,'original_inode':x.st_ino,'reclaimed_allocated_bytes':x.st_blocks*512})
receipt={'format':'othello-indexed-mode-allocation6-v1','status':'prepared','created_utc':utc(),
 'scope':'exact byte/source/mtime/mode matches in terminal experiment caches and sources; no new proof claims',
 'protected_receipts':protected,'replacements':rows,'source_replacements':source_rows,'initial_allocated_study_bytes':allocated(runs),
 'rollback':'copy2 canonical bytes into a private inode before any future writable check',
 'donor_source':donor_source,'donor_interface_pool_sha256':digest_entries(donor_pool)}
atomic_json(output,receipt)
for row in rows+source_rows:
 target=pathlib.Path(row['path']);canonical=pathlib.Path(row['canonical']);tmp=target.with_name(target.name+'.closed-share-tmp')
 assert not tmp.exists() and target.stat().st_nlink==1 and assembly6.sha(target)==assembly6.sha(canonical)==row['sha256']
 assert (target.stat().st_mtime_ns,target.stat().st_mode)==(row['mtime_ns'],row['mode'])
 os.link(canonical,tmp);os.replace(tmp,target)
assert source_identity(donor)==donor_source and assembly6.interfaces(donor)==donor_pool
assert all(source_identity(pathlib.Path(p))==d['source'] and assembly6.interfaces(pathlib.Path(p))==d['pool'] for p,d in roots.items())
assert all(assembly6.sha(pathlib.Path(p))==h for p,h in protected.items())
receipt.update(status='complete',finished_utc=utc(),sources_unchanged=True,interface_bytes_unchanged=True,
 protected_receipts_unchanged=True,reclaimed_allocated_bytes=sum(r['reclaimed_allocated_bytes'] for r in rows+source_rows),
 final_allocated_study_bytes=allocated(runs))
atomic_json(output,receipt)
print(json.dumps({k:receipt[k] for k in ('status','reclaimed_allocated_bytes','initial_allocated_study_bytes','final_allocated_study_bytes')}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default=LABEL)
    parser.add_argument('--targets', type=Path)
    parser.add_argument('--donor', type=Path,help='JSON triple of closed donor label, folder, and report hash')
    args = parser.parse_args()
    require(bool(re.fullmatch(r'[A-Za-z0-9-]+', args.label)), 'invalid allocation job label')
    targets = json.loads(args.targets.read_text()) if args.targets else [
        ['indexed-cache-mode-20261009','indexed-cache-mode6','7c6a36c047022f57557b79b9a360bb1755f58fae65b03d6182e6ee94f0a280f3'],
        ['indexed-warning-mode-20261009','indexed-cache-mode6','c33de5896ca5bca467469d896241c5e3354255d824b6dddf1027ddce4f60eab9']]
    donor=json.loads(args.donor.read_text()) if args.donor else [
        'indexed-wire-pilot-fixed-20261009','indexed-wire6','3ebe3636d784dc95ba2a4f31011a82e370ab1fda023df0770185017cc6ef4aa3']
    require(0 < len(targets) <= 4, 'one to four closed targets required')
    for target,folder,h in targets+[donor]:
        require(bool(re.fullmatch(r'[A-Za-z0-9-]+',target)) and valid_folder(folder) and
                bool(re.fullmatch(r'[0-9a-f]{64}',h)), 'invalid closed target')
    label=args.label
    output_name=label+'-allocation.json'
    root = Path(__file__).resolve().parents[1]
    out = root / 'results/remote6' / label
    out.mkdir(parents=True, exist_ok=False)
    ledger = Ledger(root / 'results/study6-ledger.json')
    reservation = ledger.reserve('assembly', 22, label)
    wrapper = '''import json,pathlib,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'tools'))
from run_job import run_job
r=run_job(sys.argv[2],['python3','-c',sys.argv[4],str(root),sys.argv[7],sys.argv[8],sys.argv[9]],root/'results',root=root,
 timeout=50,cpu_limit=20,rss_limit_gib=.5,log_limit_mib=1,reservation_id=sys.argv[3],expected_source_sha256=sys.argv[5],
 metadata={'purpose':'exact closed experiment interface allocation recovery','inline_code_sha256':sys.argv[6]})
print(json.dumps(r))
'''
    digest = hashlib.sha256(CODE.encode()).hexdigest()
    atomic_json(out / 'job.json', dict(label=label, host='desktop', remote_root=FROZEN,
                source_sha256=SOURCE, reservation_id=reservation['reservation_id'], category='assembly',
                mode='capped closed immutable cache allocation recovery', inline_code_sha256=digest))
    record = json.loads(ssh('desktop', ['python3', '-c', wrapper, FROZEN, label,
                       reservation['reservation_id'], CODE, SOURCE, digest,json.dumps(targets),output_name,json.dumps(donor)]).stdout)
    atomic_json(out / (label + '.json'), record)
    ledger.finish(reservation['reservation_id'], out / (label + '.json'))
    for name in (label + '.log', output_name):
        (out / name).write_bytes(ssh('desktop', ['cat', FROZEN + '/results/' + name]).stdout)
    print(json.dumps({k:record[k] for k in ('accepted', 'cpu_seconds', 'wall_seconds', 'peak_rss_gib')}))
    if not record['accepted']: raise SystemExit('allocation recovery stopped; retain the receipt')


if __name__ == '__main__': main()
