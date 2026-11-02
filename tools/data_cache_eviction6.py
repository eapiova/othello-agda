"""Replay a cached row proof after omitting its data-only interface, without writing caches."""
import contextlib,fcntl,json,os,shutil,subprocess,sys,time
from pathlib import Path
import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
from provenance import source_identity,digest_entries
from run_job import atomic_json,build_lock,run_job,utc
from study6 import Ledger
from study_archive6 import verify_view

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT=BASE/'data-cache-eviction6-20261018';CHECK=OUT/'check'
PRIOR=BASE/'text-upper-holdout6-20261018';UNIT='othello6-'+OUT.name+'.service'
RESERVE=110;OUTER=90;ALLOWANCE=10
previous.OUT=OUT;previous.CHECK=CHECK
common.OUT=OUT;common.HARD_GIB=6;common.RESERVATION_CPU=RESERVE


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text())
    assert all(common.sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    frozen=json.loads((OUT/'storage-freeze.json').read_text())
    def storage(reserve=0):
        own=int(subprocess.check_output(['du','-s','-x','-B1',str(OUT)],text=True).split()[0])
        assert own+reserve<=16*2**20 and frozen['prior_allocated_study_bytes']+own+reserve<12*2**30
        assert shutil.disk_usage(ROOT).free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
        return dict(checked_utc=utc(),allocated_study_bytes=frozen['prior_allocated_study_bytes']+own,
            own_output_bytes=own,root_free_bytes=shutil.disk_usage(ROOT).free,virtual_views_not_double_counted=True)
    common.storage=storage
    expected={Path(k):tuple(v) for k,v in plan['donors'].items()}
    processes=[];views={};failure=None;phase=None;cleanup=[]
    with contextlib.ExitStack() as stack:
        for donor in expected:
            lock=stack.enter_context((donor/'_build/.study6.lock').open('rb'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stack.enter_context(build_lock(CHECK));stack.enter_context(common.watched())
        before=batch.donor_snapshot(expected)
        identity=source_identity(CHECK);assert identity==plan['source'] and assembly6.interfaces(CHECK)==plan['retained_proof_interfaces']
        fs=Path(plan['filesystem_binary']);assert common.sha(fs)==plan['filesystem_binary_sha256']
        try:
            actual=dict(expected)
            for label,cache in plan['caches'].items():
                archive=Path(cache['archive']);assert common.sha(archive)==cache['archive_sha256']
                view=OUT/(label+'-view');view.mkdir()
                log=stack.enter_context((OUT/(label+'-filesystem.log')).open('wb'))
                process=subprocess.Popen([str(fs),str(archive),str(view)],stdout=log,stderr=subprocess.STDOUT)
                processes.append((view,process));start=time.monotonic()
                while not os.path.ismount(view):
                    assert process.poll() is None and time.monotonic()-start<10
                    time.sleep(.05)
                views[label]=verify_view(view,cache['manifest'])
                actual[view]=(cache['source_sha256'],cache['interface_pool_sha256'])
            args=previous.sandbox()[:-1]
            for view,_ in processes:args+=['--ro-bind',str(view),str(view)]
            args+=['--',batch.full_map.AGDA,'--no-libraries','-i','src']
            for donor in actual:args+=['-i',str(donor/'src')]
            args+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules','--no-write-interfaces',
                'src/Tests/DataCacheEviction6.agda','+RTS','-M4500M','-s','-RTS']
            result=run_job('archive-cache-replay',args,OUT/'records',root=CHECK,timeout=100,cpu_limit=20,
                rss_limit_gib=5.6,log_limit_mib=2,expected_source_sha256=identity['source_sha256'],
                metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,archive_view_read_only=True,
                    data_only_interface_missing_before_check=True,proof_interface_retained=True,additional_game_row_checks=0,
                    mathematical_objective_complete=False))
            phase={k:result[k] for k in ['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']}
            assert result['accepted'],'No-write cached proof replay incomplete'
            assert assembly6.interfaces(CHECK)==plan['retained_proof_interfaces']
            log=(OUT/'records/archive-cache-replay.log').read_text()
            assert 'Checking Tests.TextUpperHoldout6.Rows500' not in log,'Proof was rechecked instead of reused'
            assert not any(q.name=='Body500.agdai' for q in CHECK.rglob('*.agdai'))
            for label,cache in plan['caches'].items():
                assert verify_view(OUT/(label+'-view'),cache['manifest'])==views[label]
        except BaseException as error:failure=repr(error)
        finally:
            for view,process in reversed(processes):
                unmount=None
                if os.path.ismount(view):unmount=subprocess.run(['/usr/bin/fusermount3','-u',str(view)],capture_output=True,text=True,timeout=8)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
                cleanup.append(dict(view=str(view),unmounted=not os.path.ismount(view),fuse_exit=process.returncode,
                    unmount_exit=None if unmount is None else unmount.returncode))
            atomic_json(OUT/'view-cleanup.json',cleanup)
        intact=batch.donor_snapshot(expected)==before
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        p1=all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items())
        complete=failure is None and phase is not None and phase['accepted'] and all(x['unmounted'] for x in cleanup)
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=complete,phase=phase,views=views,
            failure=failure,cleanup=cleanup,accepted_donors_unchanged=intact,p1_unchanged=p1,
            source_unchanged=source_identity(CHECK)==identity,additional_game_row_checks=0,data_interface_missing_and_not_written=True,proof_interface_unchanged=True,proof_reused_without_boolean_rerun=complete,
            mathematical_objective_complete=False))
        assert complete and intact and p1 and source_identity(CHECK)==identity,'Data-only cache replay incomplete; retain every receipt'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=250,cpu_limit=OUTER,rss_limit_gib=5.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and not common.disjoint_checkers()
    assert common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    accepted=json.loads((PRIOR/'closure.json').read_text());assert accepted['accepted']
    prior=accepted['combined_scope_cpu_seconds'];assert prior+RESERVE+ALLOWANCE<=2000
    caches={'upper':json.loads((ROOT/'results/text-upper-cache-current6-20261018.json').read_text())}
    oldplan=json.loads((PRIOR/'plan.json').read_text())
    expected={k:v for k,v in oldplan['donors'].items() if k!=caches['upper']['original_source']}
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths=extras|{Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+16*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    shutil.copytree(PRIOR/'check/src',CHECK/'src');shutil.copy2(ROOT/'othello.agda-lib',CHECK/'othello.agda-lib')
    wrapper=CHECK/'src/Tests/DataCacheEviction6.agda'
    wrapper.write_text('''{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted storage test: same cached proof, data-only cache omitted.
module Tests.DataCacheEviction6 where
import Tests.TextUpperHoldout6.Rows500
''')
    original_pool=assembly6.interfaces(PRIOR/'check')
    proof_names=[n for n in original_pool if n.endswith('/Rows500.agdai')];assert len(proof_names)==1
    target=CHECK/proof_names[0];target.parent.mkdir(parents=True);shutil.copy2(PRIOR/'check'/proof_names[0],target)
    retained=assembly6.interfaces(CHECK);assert retained=={proof_names[0]:original_pool[proof_names[0]]}

    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),prior_allocated_study_bytes=used,
        own_output_cap_mib=16,retained_study_cap_gib=12,root_free_floor_gib=80,physical_archives_counted=True))
    helpers=set(['data_cache_eviction6.py','study_archive6.py','study_archive_fs6.c']+list(oldplan['helper_sha256']))
    plan=dict(created_utc=utc(),source=source_identity(CHECK),control_source=source_identity(OUT/'control'),
        helper_sha256={n:common.sha(ROOT/'tools'/n) for n in helpers},donors=expected,caches=caches,retained_proof_interfaces=retained,
        filesystem_binary=caches['upper']['filesystem_binary'],filesystem_binary_sha256=oldplan['filesystem_binary_sha256'],
        source_proof_checkpoint=str(PRIOR),data_only_cache_eviction_probe=True,previous_combined_scope_cpu_seconds=prior,
        scope_cpu_cap=2000,reservation=RESERVE,outer_cpu_cap=OUTER,new_controller_allowance_seconds=ALLOWANCE,
        hard_memory_gib=6,heap_mib=4500,swap_bytes=0,core_bytes=0,additional_game_row_checks=0,
        mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Verify no-write interface mode reuses an accepted row proof while reconstructing only its missing String data; original sources/caches untouched and inline2000 consumption retained')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=6G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=280','--property=WorkingDirectory='+str(OUT/'control'),
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
