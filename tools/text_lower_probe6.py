"""Bounded full LOWER map/compatibility/composition and fresh row cost validation."""
import contextlib, fcntl, json, os, shutil, subprocess, sys, time
from pathlib import Path
import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
from provenance import source_identity
from run_job import atomic_json,build_lock,run_job,utc
from study6 import Ledger
from study_archive6 import verify_view

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT=BASE/'text-lower-probe6-20261018'; CHECK=OUT/'check'; VIEW=OUT/'upper-view'
DONOR=BASE/'text-parametric-assembly6-20261018'
UNIT='othello6-'+OUT.name+'.service'
RESERVE=400;OUTER=370;ALLOWANCE=20;CAP=192*2**20
previous.OUT=OUT;previous.CHECK=CHECK
common.OUT=OUT;common.HARD_GIB=6;common.RESERVATION_CPU=RESERVE


def storage(frozen,reserve=0):
    own=int(subprocess.check_output(['du','-s','-x','-B1',str(OUT)],text=True).split()[0])
    used=frozen['prior_allocated_study_bytes']+own
    assert own+reserve<=CAP and used+reserve<12*2**30
    free=shutil.disk_usage(ROOT).free
    assert free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
    return dict(allocated_study_bytes=used,own_output_bytes=own,root_free_bytes=free,
        reserved_bytes=reserve,virtual_archive_view_excluded_from_physical_allocation=True,checked_utc=utc())


def sandbox():
    args=previous.sandbox()
    if os.path.ismount(VIEW):args=args[:-1]+['--ro-bind',str(VIEW),str(VIEW),'--']
    return args


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text())
    assert all(common.sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    cache=plan['upper_cache'];archive=Path(cache['archive']);fs=Path(cache['filesystem_binary'])
    assert common.sha(archive)==cache['archive_sha256'] and common.sha(fs)==plan['filesystem_binary_sha256']
    frozen=json.loads((OUT/'storage-freeze.json').read_text());common.storage=lambda reserve=0:storage(frozen,reserve)
    phases={};source=None;failure=None;fuse=None;cleanup=None;intact=False;view_before=None
    fields=['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']
    with contextlib.ExitStack() as stack:
        expected={Path(k):tuple(v) for k,v in plan['donors'].items() if k!=cache['original_source']}
        for donor in expected:
            lock=stack.enter_context((donor/'_build/.study6.lock').open('rb'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        archive_lock=stack.enter_context(archive.open('rb'));fcntl.flock(archive_lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
        stack.enter_context(common.watched())
        before=batch.donor_snapshot(expected)
        try:
            VIEW.mkdir();log=stack.enter_context((OUT/'filesystem.log').open('wb'))
            fuse=subprocess.Popen([str(fs),str(archive),str(VIEW)],stdout=log,stderr=subprocess.STDOUT)
            start=time.monotonic()
            while not os.path.ismount(VIEW):
                assert fuse.poll() is None and time.monotonic()-start<10
                time.sleep(.05)
            view_before=verify_view(VIEW,cache['manifest']);atomic_json(OUT/'upper-view-verification.json',view_before)
            expected[VIEW]=(cache['source_sha256'],cache['interface_pool_sha256'])
            prepared=run_job('prepare',sandbox()+['/usr/bin/python3','-B',str(ROOT/'tools/text_lower_prepare6.py'),str(OUT)],
                OUT/'records',root=OUT/'control',timeout=200,cpu_limit=70,rss_limit_gib=2.5,log_limit_mib=2,
                expected_source_sha256=plan['control_source']['source_sha256'])
            phases['prepare']={k:prepared[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
            assert prepared['accepted'],'LOWER preparation incomplete'
            emission=json.loads((OUT/'emission.json').read_text());source=emission['source']
            assert source_identity(CHECK)==source and not assembly6.interfaces(CHECK)
            stack.enter_context(build_lock(CHECK))
            targets=[('data','Root',50),('load','Load',15),('compatible','Compatible',25),
                ('assembly','Assembly',40),('joint','Joint',35),('training','Rows6',50),
                ('heldout','Rows686',100),('samples','Samples',15)]
            for label,target,cap in targets:
                if label=='heldout':
                    assert not any(p.name in ['Body686.agdai','Rows686.agdai'] for p in CHECK.rglob('*.agdai'))
                    # New model: fit the token slope to BOTH old UPPER cases, then
                    # calibrate the fixed offset with LOWER training. The new LOWER
                    # heldout is untouched and the original failed gate is retained.
                    upper=json.loads((BASE/'text-upper-probe6-20261018-fixed/phase-summary.json').read_text())
                    meta=json.loads((BASE/'text-upper-probe6-20261018-fixed/emission.json').read_text())['cases']
                    slope=(upper['heldout']['cpu_seconds']-upper['training']['cpu_seconds'])/(meta['652']['tokens']-meta['6']['tokens'])
                    offset=phases['training']['cpu_seconds']-slope*emission['cases']['6']['tokens']
                    forecast=dict(created_utc=utc(),model='old-UPPER-two-point token slope plus new-LOWER-training offset',
                        prior_upper_failed_forecast_retained=True,cpu_per_token=slope,calibrated_offset_cpu_seconds=offset,
                        training_group=6,heldout_group=686,training_tokens=emission['cases']['6']['tokens'],
                        heldout_tokens=emission['cases']['686']['tokens'],
                        predicted_heldout_cpu_seconds=offset+slope*emission['cases']['686']['tokens'],
                        accepted_error_limit_percent=30,archive_and_full_body_generation_still_require_validation=True,
                        full_row_coverage_proved=False,production_go=False)
                    atomic_json(OUT/'forecast-freeze.json',forecast)
                    atomic_json(OUT/'heldout-freeze-pin.json',dict(created_utc=utc(),sha256=common.sha(OUT/'forecast-freeze.json')))
                common.storage(8*2**20)
                args=sandbox()+[batch.full_map.AGDA,'--no-libraries','-i','src']
                for donor in expected:args+=['-i',str(donor/'src')]
                args+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules',
                    'src/Tests/TextLowerPacked6/'+target+'.agda','+RTS','-M4500M','-s','-RTS']
                result=run_job(label,args,OUT/'records',root=CHECK,timeout=250,cpu_limit=cap,rss_limit_gib=5.6,
                    log_limit_mib=3,expected_source_sha256=source['source_sha256'],
                    metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,full_lower_state_map_rows=6873047,
                        upper_archive_view_read_only=True,initial_bounds_proved=False,unowned_rows_remain=True))
                phases[label]={k:result[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
                assert result['accepted'],'LOWER phase incomplete: '+label
                if label=='heldout':
                    predicted=forecast['predicted_heldout_cpu_seconds'];actual=result['cpu_seconds']
                    error=100*abs(predicted-actual)/actual
                    atomic_json(OUT/'forecast-validation.json',dict(actual_heldout_cpu_seconds=actual,
                        relative_error_percent=error,component_gate_passed=error<=30,
                        archive_and_full_body_generation_still_require_validation=True,production_go=False))
            assert verify_view(VIEW,cache['manifest'])==view_before
        except BaseException as error:failure=repr(error)
        finally:
            unmount=None
            if os.path.ismount(VIEW):unmount=subprocess.run(['/usr/bin/fusermount3','-u',str(VIEW)],capture_output=True,text=True,timeout=8)
            if fuse is not None:
                try:fuse.wait(timeout=5)
                except subprocess.TimeoutExpired:fuse.terminate();fuse.wait(timeout=5)
            cleanup=dict(unmounted=not os.path.ismount(VIEW),fuse_exit=None if fuse is None else fuse.returncode,
                unmount_exit=None if unmount is None else unmount.returncode)
            atomic_json(OUT/'view-cleanup.json',cleanup)
        expected.pop(VIEW,None);intact=batch.donor_snapshot(expected)==before
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        p1=all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items())
        same=source is None or source_identity(CHECK)==source
        complete=len(phases)==9 and all(r['accepted'] for r in phases.values()) and failure is None and cleanup['unmounted']
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),phases=phases,all_phases_accepted=complete,failure=failure,
            accepted_donors_unchanged=intact,p1_unchanged=p1,source_unchanged=same,upper_view=cleanup,
            lower_full_state_map_rows=6873047,lower_prefix_resolver_compatibility_closed=phases.get('compatible',{}).get('accepted',False),
            conditional_lower_assembly_checked=phases.get('assembly',{}).get('accepted',False),
            conditional_same_pair_problem2_bridge_checked=phases.get('joint',{}).get('accepted',False),
            owned_rows_on_new_lower_map=20000 if phases.get('heldout',{}).get('accepted',False) else (10000 if phases.get('training',{}).get('accepted',False) else 0),
            full_row_coverage_proved=False,production_go=False,initial_bounds_proved=False,mathematical_objective_complete=False))
        assert complete and intact and p1 and same,'LOWER full-map probe incomplete; retain every receipt'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=1100,cpu_limit=OUTER,rss_limit_gib=5.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists()
    assert common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running','--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior=json.loads((BASE/'study-log-archive6-20261018/closure.json').read_text())['combined_scope_cpu_seconds']
    extension=json.loads((ROOT/'results/full-text-lower-scope-extension6-20261018.json').read_text())
    assert extension['new_cumulative_cap_cpu_seconds']==2000 and prior+RESERVE+ALLOWANCE<=2000
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths=extras|{Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+CAP<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    closed=json.loads((DONOR/'closure.json').read_text());assert closed['accepted']
    cache=json.loads((ROOT/'results/text-upper-cache-current6-20261018.json').read_text());assert cache['plaintext_retirement_complete']
    expected=json.loads((DONOR/'plan.json').read_text())['donors'];expected[str(DONOR/'check')]=[closed['source_sha256'],closed['interface_pool_sha256']]
    assert expected[cache['original_source']]==[cache['source_sha256'],cache['interface_pool_sha256']]
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),legacy_snapshot=legacy,
        prior_allocated_study_bytes=used,extra_roots=[str(p) for p in sorted(paths)],
        own_output_cap_bytes=CAP,retained_study_cap_gib=12,root_free_floor_gib=80,
        external_physical_bytes_counted=True,virtual_view_not_double_counted=True))
    helpers=set(['text_lower_probe6.py','text_lower_prepare6.py','study_archive6.py','study_archive_fs6.c','wire_part_samples6.py']+list(json.loads((DONOR/'plan.json').read_text())['helper_sha256']))
    plan=dict(created_utc=utc(),control_source=source_identity(OUT/'control'),donors=expected,upper_cache=cache,
        helper_sha256={n:common.sha(ROOT/'tools'/n) for n in helpers},
        filesystem_binary_sha256=common.sha(Path(cache['filesystem_binary'])),hard_memory_gib=6,swap_bytes=0,core_bytes=0,
        reservation=RESERVE,outer_cpu_cap=OUTER,scope_cpu_cap=2000,previous_combined_scope_cpu_seconds=prior,
        new_controller_allowance_seconds=ALLOWANCE,phase_cpu_caps=[70,50,15,25,40,35,50,100,15],
        existing_raw_lower_wire_read_only=True,no_new_solver_runs=True,conditional_proofs_only=True,
        full_row_coverage_proved=False,production_go=False,mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    wire=Path('/home/eapiova/projects/othello-agda/runs/six-full-map-lower-native-20261016/results/full-map-pilot6/initial-lower.wire')
    from wire_part_samples6 import _fingerprint
    atomic_json(OUT/'input-request.json',dict(wire=str(wire),wire_sha256='d6b4786ebafc86c5f1513d8e300366b9baf3ff06879defa8e2cb19998dc3a762',
        wire_rows=6873047,wire_bytes=498606513,wire_fingerprint=list(_fingerprint(wire.stat()))))
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Full direct-text LOWER map, exact prefix compatibility, symbolic688-field assembly, SAME-pair conditional bridge and fresh10000-owner training/heldout; all prior inline2000 charges preserved')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=6G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=1130','--property=WorkingDirectory='+str(OUT/'control'),
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
