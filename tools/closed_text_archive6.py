"""Lossless staged archive of closed generated artifacts outside active donors.

AI-assisted maintenance only. Keeps all proof interface files in place and
preserves every selected source/receipt byte and its metadata before unlink.
"""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile

import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity
from run_job import atomic_json,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT=BASE/'closed-text-archive6-20261018'
OLD=BASE/'relocated-current-artifacts'
UNIT='othello6-'+OUT.name+'.service'
RESERVE,OUTER,ALLOWANCE=180,150,10


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(2**20),b''):h.update(block)
    return h.hexdigest()


def worker():
    batch.authorized()
    plan=json.loads((OUT/'plan.json').read_text())
    assert all(sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    donors={Path(k):tuple(v) for k,v in plan['donors'].items()}
    removed={};archives=[]
    def storage():
        own=batch.allocated(OUT)
        released=sum(e['allocated_bytes'] for e in removed.values())
        assert own+4*2**20<=40*2**20
        assert plan['prior_allocated_study_bytes']+own-released+4*2**20<12*2**30
        assert shutil.disk_usage(ROOT).free-2**20>=80*2**30
        atomic_json(OUT/'storage.json',dict(checked_utc=utc(),own_output_bytes=own,
            removed_allocated_bytes=released,allocated_study_bytes=plan['prior_allocated_study_bytes']+own-released))
    with contextlib.ExitStack() as stack:
        for donor in donors:
            lock=stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before=batch.donor_snapshot(donors)
        for stage,files in plan['stages'].items():
            entries={};archive=OUT/(stage+'.zip');storage()
            with zipfile.ZipFile(archive,'x') as saved:
                for name,identity in files.items():
                    file=OLD/name;s=file.stat()
                    assert file.is_file() and not file.is_symlink() and s.st_nlink==1
                    assert [s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino]==identity
                    raw=file.read_bytes();assert len(raw)==s.st_size<=16*2**20
                    info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=s.st_mode<<16
                    info.extra=struct.pack('<HHQ',0xa6da,8,s.st_mtime_ns)
                    saved.writestr(info,raw,compress_type=zipfile.ZIP_ZSTANDARD,compresslevel=19)
                    entries[name]=dict(size=s.st_size,sha256=hashlib.sha256(raw).hexdigest(),
                        mode=s.st_mode,mtime_ns=s.st_mtime_ns,identity=identity,allocated_bytes=s.st_blocks*512)
                    storage()
            with archive.open('rb') as stream:os.fsync(stream.fileno())
            with zipfile.ZipFile(archive) as saved:
                assert set(saved.namelist())==set(entries)
                for name,e in entries.items():
                    info=saved.getinfo(name)
                    assert hashlib.sha256(saved.read(name)).hexdigest()==e['sha256']
                    assert info.external_attr>>16==e['mode']
                    assert info.extra==struct.pack('<HHQ',0xa6da,8,e['mtime_ns'])
            manifest=dict(created_utc=utc(),original_root=str(OLD),archive=str(archive),
                archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
                entries=entries,all_bytes_modes_and_ns_mtimes_preserved=True,complete=False)
            manifest_path=OUT/(stage+'-manifest.json');atomic_json(manifest_path,manifest)
            with manifest_path.open('rb') as stream:os.fsync(stream.fileno())
            fd=os.open(OUT,os.O_RDONLY);os.fsync(fd);os.close(fd)
            for name,e in entries.items():
                file=OLD/name;s=file.stat()
                assert [s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino]==e['identity'] and sha(file)==e['sha256']
                file.unlink();removed[name]=e;storage()
            manifest.update(complete=True,finished_utc=utc());atomic_json(manifest_path,manifest)
            archives.append(dict(manifest=str(manifest_path),archive=str(archive),archive_bytes=archive.stat().st_size,
                archive_sha256=manifest['archive_sha256'],files=len(entries),raw_bytes=sum(e['size'] for e in entries.values())))
        assert batch.donor_snapshot(donors)==before
        assert all(sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=True,archives=archives,
            files=len(removed),raw_bytes=sum(e['size'] for e in removed.values()),
            released_allocated_bytes=sum(e['allocated_bytes'] for e in removed.values()),
            donor_sources_and_interfaces_unchanged=True,all_proof_interfaces_left_in_place=True,
            p1_unchanged=True,original_desktop_runs_and_NAMOR_untouched=True,
            new_game_row_checks=0,mathematical_objective_complete=False))


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    sandbox=['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(BASE),str(BASE),
        '--proc','/proc','--dev-bind','/dev','/dev','--tmpfs','/tmp','--die-with-parent','--']
    result=run_job(OUT.name,sandbox+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],
        OUT/'records',root=OUT/'control',timeout=500,cpu_limit=OUTER,rss_limit_gib=1.8,
        log_limit_mib=2,reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior=json.loads((ROOT/'results/complete-lower-row-sources-index6-20261018.json').read_text())
    assert prior['accepted'] and prior['combined_scope_cpu_seconds']+RESERVE+ALLOWANCE+1210<=6000
    common.OUT=ROOT/'results/audit-no-output6-20261018'
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    paths={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths|={Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+8*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    donors=json.loads((BASE/'packed-lower-cache6-20261018/plan.json').read_text())['donors']
    protected={Path(p).resolve() for p in donors}
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    p1={(ROOT/p).resolve() for p in history['p1_files']}
    stages={'controllers-and-logs':{},'receipts-and-inactive-source':{}}
    for file in sorted(OLD.rglob('*')):
        if file.is_symlink() or not file.is_file() or file.suffix not in ['.py','.log','.json','.jsonl','.agda','.agda-lib','.c']:continue
        target=file.resolve()
        if target in p1 or any(target.is_relative_to(p) for p in protected):continue
        s=file.stat()
        if s.st_nlink!=1 or s.st_size==0:continue
        assert s.st_size<=16*2**20
        stage='controllers-and-logs' if file.suffix in ['.py','.log'] else 'receipts-and-inactive-source'
        stages[stage][file.relative_to(OLD).as_posix()]=[s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino]
    assert sum(len(files) for files in stages.values())<=12000
    assert sum(v[0] for files in stages.values() for v in files.values())<=160*2**20
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    helpers=['closed_text_archive6.py','completion_batch6.py','run_job.py','provenance.py','study6.py']
    plan=dict(created_utc=utc(),stages=stages,donors=donors,p1_files=history['p1_files'],
        helper_sha256={n:sha(ROOT/'tools'/n) for n in helpers},control_source=source_identity(OUT/'control'),
        prior_allocated_study_bytes=used,previous_combined_scope_cpu_seconds=prior['combined_scope_cpu_seconds'],
        reservation=RESERVE,new_controller_allowance_seconds=ALLOWANCE,scope_cpu_cap=6000,
        retained_study_cap_gib=12,root_free_floor_gib=80,own_output_cap_mib=40,
        hard_memory_gib=2,swap_bytes=0,core_bytes=0,mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Losslessly archive closed copied controllers, logs, receipts and inactive sources outside every current donor; preserve every byte/metadata and leave all proof interfaces in place; inline6000 usage retained')
    reservation=ledger.reserve('assembly',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=2G',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%',
        '--property=TasksMax=64','--property=KillMode=control-group','--property=RuntimeMaxSec=530',
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,files=sum(len(f) for f in stages.values()))))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
