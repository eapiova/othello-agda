"""Bounded crash/recovery validation of the production ZIP append protocol.

Synthetic archives only; no checker, solver, or mathematical evidence is changed.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
import full_row_records6 as records
from provenance import source_identity
from run_job import atomic_json, run_job, utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT=BASE/'full-row-storage-validation6-20261018'
UNIT='othello6-'+OUT.name+'.service'
CAP=128*1024


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def crash(path):
    # Kill the actual ZipFile append after it overwrites the old central directory,
    # before ZipFile.close can write its replacement. The durable journal is real.
    raw=b'new member payload'*200
    records._write_append_journal(path,'new.bin',raw)
    archive=zipfile.ZipFile(path,'a')
    archive.writestr('new.bin',raw)
    archive.fp.flush();os.fsync(archive.fp.fileno())
    os._exit(73)


def worker():
    plan=json.loads((OUT/'plan.json').read_text())
    assert sha(Path(__file__))==plan['helper_sha256']
    assert sha(ROOT/'tools/full_row_records6.py')==plan['records_helper_sha256']
    fixtures=OUT/'fixtures';fixtures.mkdir()
    outcomes=[]
    for existing in (False,True):
        path=fixtures/('existing.zip' if existing else 'empty.zip')
        if existing:
            with zipfile.ZipFile(path,'w') as archive:
                archive.writestr('old.bin',b'old accepted payload'*200)
            original=path.read_bytes()
        else:
            original=None
        child=subprocess.run(['/usr/bin/python3','-B',str(Path(__file__)),'crash',str(path)])
        assert child.returncode==73 and records.journal_path(path).exists()
        assert records.recover_append(path,lambda _:False)=='rolled-back'
        assert not records.journal_path(path).exists()
        assert (path.read_bytes()==original) if existing else not path.exists()
        outcomes.append(dict(case='interrupted-existing' if existing else 'interrupted-new',
            child_exit=child.returncode,exact_pre_append_archive_restored=True))
    path=fixtures/'existing.zip';original=path.read_bytes()
    records.append_stored(path,'uncommitted.bin',b'uncommitted data')
    assert records.recover_append(path,lambda _:False)=='rolled-back'
    assert path.read_bytes()==original
    outcomes.append(dict(case='closed-but-uncommitted',exact_pre_append_archive_restored=True))
    raw=b'accepted and committed data'
    result=records.append_stored(path,'committed.bin',raw)
    assert records.recover_append(path,lambda j:j['member_sha256']==hashlib.sha256(raw).hexdigest())=='committed'
    with zipfile.ZipFile(path) as archive:
        assert archive.read('old.bin')==b'old accepted payload'*200
        assert archive.read('committed.bin')==raw
    assert not records.journal_path(path).exists()
    outcomes.append(dict(case='closed-and-committed',all_payloads_retained=True))
    source=fixtures/'receipt.log';source.write_bytes(b'full exact receipt\x00\xff\n'*100)
    os.chmod(source,0o640);os.utime(source,ns=(1700000000123456789,1700000000987654321))
    info=source.stat();archive=fixtures/'evidence.zip'
    result=records.archive_cohort(archive,'cohort-0000.tar.zst',fixtures,['receipt.log'],{'test':'exact'})
    entry=result['manifest']['entries'][0]
    assert entry['mode']==0o640 and entry['mtime_ns']==info.st_mtime_ns
    assert entry['sha256']==sha(source)
    records.commit_append(archive)
    with zipfile.ZipFile(archive) as z:
        restored=records.verify_cohort_blob(z.read('cohort-0000.tar.zst'),result['manifest'],{'receipt.log':source.read_bytes()})
    outcomes.append(dict(case='cohort-lossless',bytes_mode_and_ns_mtime_preserved=True))
    shutil.rmtree(fixtures)
    own=batch.allocated(OUT)
    assert own+16384<CAP and plan['prior_allocated_study_bytes']+own+16384<12*2**30
    assert shutil.disk_usage(ROOT).free-1024**2>=80*2**30
    atomic_json(OUT/'report.json',dict(accepted=True,finished_utc=utc(),cases=outcomes,
        checker_runs=0,mathematical_evidence_changed=False,mathematical_objective_complete=False))


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    sandbox=['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(OUT),str(OUT),
        '--proc','/proc','--dev-bind','/dev','/dev','--tmpfs','/tmp','--die-with-parent','--']
    record=run_job(OUT.name,sandbox+['/usr/bin/python3','-B',str(Path(__file__)),'worker'],
        OUT/'records',root=OUT/'control',timeout=60,cpu_limit=30,rss_limit_gib=.4,log_limit_mib=.05,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if record['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    closure=json.loads((BASE/'private-core-package6-20261018/closure.json').read_text())
    assert closure['accepted'] and closure['combined_scope_cpu_seconds']+45<6000
    common.OUT=ROOT/'results/audit-no-output6-20261018';legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    assert str(OUT) in [entry['path'] for entry in registry['roots']]
    paths={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}|{Path(e['path']) for e in registry['roots'] if Path(e['path'])!=OUT}
    prior=legacy['allocated_study_bytes']+sum(batch.allocated(path) for path in paths)
    assert prior+CAP<12*2**30 and shutil.disk_usage(ROOT).free-1024**2>=80*2**30
    ledger=Ledger(ROOT/'results/study6-ledger.json')
    assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    plan=dict(helper_sha256=sha(Path(__file__)),records_helper_sha256=sha(ROOT/'tools/full_row_records6.py'),
        prior_allocated_study_bytes=prior,previous_combined_scope_cpu_seconds=closure['combined_scope_cpu_seconds'],
        new_controller_allowance_seconds=5,scope_cap_cpu_seconds=6000,own_cap_bytes=CAP)
    atomic_json(OUT/'plan.json',plan)
    allowance=ledger.withhold('assembly',5,'Bounded synthetic append-interruption and exact evidence-cohort recovery validation; existing6000 calibration cap preserved')
    reservation=ledger.reserve('assembly',40,OUT.name)
    control=source_identity(OUT/'control')
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=control))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=512M',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%',
        '--property=TasksMax=32','--property=KillMode=control-group','--property=RuntimeMaxSec=80',
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__)),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation)))


if __name__=='__main__':
    action=sys.argv[1]
    if action=='launch':launch()
    elif action=='supervise':raise SystemExit(supervise())
    elif action=='worker':worker()
    elif action=='crash':crash(Path(sys.argv[2]))
    else:raise ValueError(action)
