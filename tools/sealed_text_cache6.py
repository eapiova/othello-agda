"""Bounded direct-global row check and exact read-only ZIP cache-view replay."""
import contextlib
import errno
import fcntl
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
from provenance import source_identity
from run_job import atomic_json,build_lock,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/othello-agda-desktop-artifacts-20261018/sealed-text-cache6-20261018')
CHECK=OUT/'check';VIEW=OUT/'view';UNIT='othello6-'+OUT.name+'.service'
BIG=OUT.with_name('text-upper-probe6-20261018-fixed')
DONOR=OUT.with_name('text-parametric-assembly6-20261018')
RESERVE=150;OUTER=125;ALLOWANCE=10
previous.OUT=OUT;previous.CHECK=CHECK
common.OUT=OUT;common.HARD_GIB=4;common.RESERVATION_CPU=RESERVE


def physical_storage(frozen,reserve=0):
    own=int(subprocess.check_output(['du','-s','-x','-B1',str(OUT)],text=True).split()[0])
    used=frozen['prior_allocated_study_bytes']+own
    assert own+reserve<=120*2**20 and used+reserve<12*2**30
    free=shutil.disk_usage(ROOT).free
    assert free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
    return dict(allocated_study_bytes=used,own_output_bytes=own,root_free_bytes=free,
        reserved_bytes=reserve,virtual_view_excluded_from_physical_bytes=True,checked_utc=utc())


def sandbox():
    args=previous.sandbox()
    if os.path.ismount(VIEW):args=args[:-1]+['--ro-bind',str(VIEW),str(VIEW),'--']
    return args


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text())
    assert all(common.sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    assert common.sha(OUT.with_name('global-archive-probe6-20261018')/'archive-fs')==plan['filesystem_binary_sha256']
    expected={Path(k):tuple(v) for k,v in plan['donors'].items()}
    frozen=json.loads((OUT/'storage-freeze.json').read_text())
    common.storage=lambda reserve=0:physical_storage(frozen,reserve)
    phases={};fuse=None;failure=None;view_checks=None;cleanup=None;source=None
    fields=['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']
    with contextlib.ExitStack() as stack:
        for donor in expected:
            f=stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stack.enter_context(common.watched())
        before=batch.donor_snapshot(expected)
        try:
            prep=run_job('prepare',sandbox()+['/usr/bin/python3','-B',str(ROOT/'tools/seal_text_cache6.py'),str(OUT)],
                OUT/'records',root=OUT/'control',timeout=140,cpu_limit=65,rss_limit_gib=1.5,log_limit_mib=2,
                expected_source_sha256=plan['control_source']['source_sha256'])
            phases['prepare']={k:prep[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
            assert prep['accepted'],'Archive/source preparation failed'
            source=json.loads((OUT/'emission.json').read_text())['source']
            assert source_identity(CHECK)==source and not assembly6.interfaces(CHECK)
            stack.enter_context(build_lock(CHECK))
            VIEW.mkdir()
            fslog=stack.enter_context((OUT/'filesystem.log').open('wb'))
            fuse=subprocess.Popen([str(OUT.with_name('global-archive-probe6-20261018')/'archive-fs'),str(OUT/'text-cache.zip'),str(VIEW)],stdout=fslog,stderr=subprocess.STDOUT)
            start=time.monotonic()
            while not os.path.ismount(VIEW):
                assert fuse.poll() is None,'Archive filesystem terminated before mount'
                assert time.monotonic()-start<10,'Archive mount not ready'
                time.sleep(.05)
            from study_archive6 import verify_view
            view_checks=verify_view(VIEW,OUT/'archive-manifest.json')
            denied=False
            try:
                with (VIEW/'write-denial-probe').open('wb') as stream:stream.write(b'not allowed')
            except OSError as e:
                assert e.errno in [errno.EROFS,errno.EACCES];denied=True
            assert denied and not (VIEW/'write-denial-probe').exists()
            view_checks['write_denied']=True
            atomic_json(OUT/'view-verification.json',view_checks)
            targets=[('archive-cache-replay','src/Tests/SealedTextReplay6.agda',20)]
            for label,target,cap in targets:
                common.storage(8*2**20)
                args=sandbox()+[batch.full_map.AGDA,'--no-libraries','-i','src']
                for donor in expected:
                    selected=VIEW if donor==BIG/'check' else donor
                    args+=['-i',str(selected/'src')]
                args+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules',
                    target,'+RTS','-M2800M','-s','-RTS']
                result=run_job(label,args,OUT/'records',root=CHECK,timeout=100,cpu_limit=cap,
                    rss_limit_gib=3.6,log_limit_mib=2,expected_source_sha256=source['source_sha256'],
                    metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,
                        archive_view_read_only=True,archive_view_fully_hash_warmed=True,
                        new_initial_bounds_proved=False,unowned_citations_remain=True))
                phases[label]={k:result[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
                assert result['accepted'],'Global/ZIP-view check incomplete: '+label
            assert verify_view(VIEW,OUT/'archive-manifest.json')=={k:v for k,v in view_checks.items() if k!='write_denied'}
        except BaseException as error:
            failure=repr(error)
        finally:
            unmount=None
            if os.path.ismount(VIEW):
                unmount=subprocess.run(['/usr/bin/fusermount3','-u',str(VIEW)],capture_output=True,text=True,timeout=8)
            if fuse is not None:
                try:fuse.wait(timeout=5)
                except subprocess.TimeoutExpired:fuse.terminate();fuse.wait(timeout=5)
            cleanup=dict(unmounted=not os.path.ismount(VIEW),fuse_exit=None if fuse is None else fuse.returncode,
                unmount_exit=None if unmount is None else unmount.returncode,
                unmount_stderr=None if unmount is None else unmount.stderr)
            atomic_json(OUT/'view-cleanup.json',cleanup)
        intact=batch.donor_snapshot(expected)==before
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        p1=all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items())
        same=source is None or source_identity(CHECK)==source
        complete=len(phases)==2 and all(r['accepted'] for r in phases.values()) and failure is None and cleanup['unmounted']
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),phases=phases,all_phases_accepted=complete,
            failure=failure,view_checks=view_checks,cleanup=cleanup,accepted_donors_unchanged=intact,
            p1_unchanged=p1,source_unchanged=same,original_source_removed=False,
            accepted_dense10000_row_interface_replayed=complete,new_distinct_common_map_rows=0,
            full_workflow_forecast_validated=False,production_go=False,initial_bounds_proved=False,
            mathematical_objective_complete=False))
        assert complete and intact and p1 and same,'Archive/global probe incomplete; preserve receipts'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=280,cpu_limit=OUTER,rss_limit_gib=3.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists()
    assert common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    closed=json.loads((DONOR/'closure.json').read_text());assert closed['accepted']
    prior=json.loads((OUT.with_name('retired-vector-archive6-20261018')/'closure.json').read_text())['combined_scope_cpu_seconds'];assert prior+RESERVE+ALLOWANCE<=1500
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    externals={Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in extras|externals)
    assert used+120*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir();control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),legacy_snapshot=legacy,
        extra_roots=[str(p) for p in sorted(extras|externals)],prior_allocated_study_bytes=used,
        own_output_cap_bytes=120*2**20,retained_study_cap_gib=12,root_free_floor_gib=80,
        external_physical_bytes_counted=True,read_only_virtual_view_excluded_from_physical_disk_allocation=True))
    expected=json.loads((DONOR/'plan.json').read_text())['donors']
    expected[str(DONOR/'check')]=[closed['source_sha256'],closed['interface_pool_sha256']]
    helpers=['sealed_text_cache6.py','seal_text_cache6.py','study_archive6.py','study_archive_fs6.c']+list(json.loads((DONOR/'plan.json').read_text())['helper_sha256'])
    plan=dict(created_utc=utc(),control_source=source_identity(control),donors=expected,
        helper_sha256={n:common.sha(ROOT/'tools'/n) for n in helpers},
        filesystem_binary_sha256=common.sha(OUT.with_name('global-archive-probe6-20261018')/'archive-fs'),hard_memory_gib=4,
        swap_bytes=0,core_bytes=0,reservation=RESERVE,outer_cpu_cap=OUTER,scope_cpu_cap=1500,
        previous_combined_scope_cpu_seconds=prior,new_controller_allowance_seconds=ALLOWANCE,
        original_sources_never_removed=True,never_modify_protected_desktop_runs=True,
        at_most_one_recovery=True,no_full_production_authorized=True)
    atomic_json(OUT/'plan.json',plan)
    atomic_json(OUT/'input-request.json',dict(source=str(BIG/'check'),
        source_sha256=expected[str(BIG/'check')][0],interface_pool_sha256=expected[str(BIG/'check')][1],
        sample_common_map=str(DONOR/'check'),no_new_wire_scan=True,no_native_solver=True))
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Seal full live text cache and validate exact read-only view/replay before any deletion; preserve all prior inline1500 actuals and physical12GiB cap')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,
        control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=4G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=310','--property=WorkingDirectory='+str(control),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,combined_reserved_scope_cpu_seconds=prior+RESERVE+ALLOWANCE)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
