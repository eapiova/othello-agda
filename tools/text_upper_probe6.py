"""Full-state UPPER layout, exact prefix resolver and10000-owner heldout check."""
import contextlib
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import assembly6
import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity
from run_job import atomic_json,build_lock,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/othello-agda-desktop-artifacts-20261018/text-upper-probe6-20261018')
DONOR=OUT.with_name('full-upper-repair6-20261018')
CHECK=OUT/'check';UNIT='othello6-'+OUT.name+'.service'
RESERVE=460;OUTER=410;ALLOWANCE=20;CAP=192*2**20
previous.OUT=OUT;common.OUT=OUT;common.HARD_GIB=6;common.RESERVATION_CPU=RESERVE


def storage(frozen,reserve=0):
    own=batch.allocated(OUT);free=shutil.disk_usage(ROOT).free
    assert own+reserve<=CAP and frozen['prior_allocated_study_bytes']+own+reserve<12*2**30
    assert free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
    return dict(allocated_study_bytes=frozen['prior_allocated_study_bytes']+own,
        own_output_bytes=own,root_free_bytes=free,data_free_bytes=shutil.disk_usage(OUT).free,
        reserved_bytes=reserve,checked_utc=utc())


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text())
    assert all(common.sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    assert all(common.sha(ROOT/'src/Othello'/(n+'.agda'))==h for n,h in plan['core_source_sha256'].items())
    expected={Path(k):tuple(v) for k,v in plan['donors'].items()}
    frozen=json.loads((OUT/'storage-freeze.json').read_text());common.storage=lambda reserve=0:storage(frozen,reserve)
    phases={};source=None;emission=None
    with contextlib.ExitStack() as stack:
        for donor in expected:
            f=stack.enter_context((donor/'_build/.study6.lock').open('rb'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before=batch.donor_snapshot(expected);stack.enter_context(common.watched())
        fields=['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']
        result=run_job('prepare',previous.sandbox()+['/usr/bin/python3','-B',str(ROOT/'tools/text_upper_prepare6.py'),'core',str(OUT)],
            OUT/'records',root=OUT/'control',timeout=30,cpu_limit=2,rss_limit_gib=2.5,log_limit_mib=2,
            expected_source_sha256=plan['control_source']['source_sha256'])
        phases['prepare']={k:result[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
        if result['accepted']:
            emission=json.loads((OUT/'emission-core.json').read_text());source=emission['source']
            assert source_identity(CHECK)==source and not assembly6.interfaces(CHECK)
            stack.enter_context(build_lock(CHECK))
            targets=[('core','Othello/TextStateAssembly6',8),('data','Tests/TextUpperPacked6/Root',60),('load','Tests/TextUpperPacked6/Load',12),('compatible','Tests/TextUpperPacked6/Compatible',20),('training','Tests/TextUpperPacked6/Rows6',50),('heldout','Tests/TextUpperPacked6/Rows652',70),('assembly','Tests/TextUpperPacked6/Assembly',35)]
            for name,target,cap in targets:
                if name=='data':
                    core_pool=assembly6.interfaces(CHECK)
                    result=run_job('prepare-data',previous.sandbox()+['/usr/bin/python3','-B',str(ROOT/'tools/text_upper_prepare6.py'),'data',str(OUT)],
                        OUT/'records',root=OUT/'control',timeout=90,cpu_limit=20,rss_limit_gib=2.5,log_limit_mib=2,
                        expected_source_sha256=plan['control_source']['source_sha256'])
                    phases['prepare-data']={k:result[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
                    if not result['accepted']:break
                    emission=json.loads((OUT/'emission.json').read_text());source=emission['source']
                    assert source_identity(CHECK)==source and assembly6.interfaces(CHECK)==core_pool
                if name=='heldout':
                    assert not any(p.name in ['Body652.agdai','Rows652.agdai'] for p in CHECK.rglob('*.agdai'))
                    base=phases['load']['cpu_seconds'];train=phases['training']['cpu_seconds']
                    slope=max(0,train-base)/emission['cases']['6']['tokens']
                    forecast=dict(created_utc=utc(),full_map_states=6530011,owners_per_batch=10000,
                        measured_full_map_import_cpu_seconds=base,training_group=6,heldout_group=652,
                        training_cpu_seconds=train,training_tokens=emission['cases']['6']['tokens'],
                        cpu_per_token_after_import=slope,
                        predicted_heldout_cpu_seconds=base+slope*emission['cases']['652']['tokens'],
                        predicted_complete_upper_rows_cpu_seconds=654*base+slope*80755243,
                        fixed_preparation_data_and_compatibility_cpu_seconds=sum(phases[n]['cpu_seconds'] for n in ['prepare','prepare-data','data','compatible']),
                        accepted_error_limit_percent=30,
                        archive_storage_and_lower_full_map_still_require_validation=True,production_go=False)
                    forecast['full_body_generation_cost_not_yet_validated']=True
                    atomic_json(OUT/'forecast-freeze.json',forecast)
                    atomic_json(OUT/'heldout-freeze-pin.json',dict(created_utc=utc(),sha256=common.sha(OUT/'forecast-freeze.json')))
                storage(frozen,8*2**20)
                argv=previous.sandbox()+[batch.full_map.AGDA,'--no-libraries','-i','src']
                for donor in expected:argv+=['-i',str(donor/'src')]
                argv+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules',
                    'src/'+target+'.agda','+RTS','-M4500M','-s','-RTS']
                result=run_job(name,argv,OUT/'records',root=CHECK,timeout=300,cpu_limit=cap,rss_limit_gib=5.6,log_limit_mib=3,
                    expected_source_sha256=source['source_sha256'],
                    metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,upper_full_state_table=True,
                        tested_owners_only=20000,initial_bounds_proved=False))
                phases[name]={k:result[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
                if not result['accepted']:break
        intact=batch.donor_snapshot(expected)==before
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        p1=all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items())
        same=source is None or source_identity(CHECK)==source
        complete=len(phases)==9 and all(p['accepted'] for p in phases.values())
        validation=None
        if complete:
            forecast=json.loads((OUT/'forecast-freeze.json').read_text());actual=phases['heldout']['cpu_seconds']
            error=abs(forecast['predicted_heldout_cpu_seconds']-actual)/actual*100
            validation=dict(actual_heldout_cpu_seconds=actual,relative_error_percent=error,
                full_map10000_owner_component_gate_passed=error<=30,
                archive_storage_and_lower_full_map_still_require_validation=True,production_go=False)
            atomic_json(OUT/'forecast-validation.json',validation)
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),all_phases_accepted=complete,phases=phases,
            accepted_donors_unchanged=intact,p1_unchanged=p1,source_unchanged=same,
            full_state_table_rows=6530011,
            conditional_full_map_assembly_checked=phases.get('assembly',{}).get('accepted',False),
            upper_sparse_prefix_resolver_compatibility_closed=phases.get('compatible',{}).get('accepted',False),
            owned_full_map_groups=2 if complete else 0,remaining_full_map_groups=652,
            forecast_validation=validation,initial_bounds_proved=False,mathematical_objective_complete=False))
        assert complete and intact and p1 and same,'Full-state UPPER preparation incomplete; preserve all receipts'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=1100,cpu_limit=OUTER,rss_limit_gib=5.8,log_limit_mib=3,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists()
    assert common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    closed=json.loads((DONOR/'closure.json').read_text());assert closed['upper_prefix_resolver_compatibility_closed'] and not closed['accepted']
    prior=closed['combined_scope_cpu_seconds']
    extension=json.loads((ROOT/'results/full-state-scope-extension6-20261018.json').read_text())
    assert extension['new_cumulative_cap_cpu_seconds']==1500 and extension['all_prior_combined_scope_cpu_seconds']<prior
    assert prior+RESERVE+ALLOWANCE<=1500
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    externals={Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in extras|externals)
    assert used+CAP<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir();control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),legacy_snapshot=legacy,
        extra_roots=[str(p) for p in sorted(extras|externals)],prior_allocated_study_bytes=used,
        own_output_cap_bytes=CAP,retained_study_cap_gib=12,all_external_physical_bytes_counted=True))
    expected=json.loads((DONOR/'plan.json').read_text())['donors']
    expected[str(DONOR/'check')]=[closed['source_sha256'],closed['interface_pool_sha256']]
    helpers=['text_upper_probe6.py','text_upper_prepare6.py','packed_wire6.py']+list(json.loads((DONOR/'plan.json').read_text())['helper_sha256'])
    plan=dict(created_utc=utc(),control_source=source_identity(control),donors=expected,
        helper_sha256={n:common.sha(ROOT/'tools'/n) for n in set(helpers)},
        core_source_sha256={n:common.sha(ROOT/'src/Othello'/(n+'.agda')) for n in ['DirectPackedText6','TextStateMap6','TextStateAssembly6']},
        reservation=RESERVE,outer_cpu_cap=OUTER,scope_cpu_cap=1500,
        previous_combined_scope_cpu_seconds=prior,new_controller_allowance_seconds=ALLOWANCE,
        hard_memory_gib=6,swap_bytes=0,core_bytes=0,phase_cpu_caps=[2,8,20,60,12,20,50,70,35],
        full_state_rows=6530011,tested_groups=[6,652],tested_owner_rows=20000,
        full_row_coverage_proved=False,production_go=False,initial_bounds_proved=False)
    atomic_json(OUT/'plan.json',plan)
    atomic_json(OUT/'input-request.json',dict(wire=json.loads((ROOT/'results/upper-wire-current6-20261018.json').read_text()),training_group=6,heldout_group=652))
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Direct text-backed full UPPER map: same source strings/certificates, avoid cached packed vectors, exact resolver and10000-owner training/heldout, full conditional assembly; inline1500 preserves every old actual')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=6G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=1120','--property=WorkingDirectory='+str(control),
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
