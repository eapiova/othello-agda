"""Stratified UPPER checks and heldout component forecast, never a full proof."""
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
OUT=Path('/mnt/data/othello-agda-desktop-artifacts-20261018/upper-kernel-probe6-20261018')
DONOR=OUT.with_name('range-upper-probe6-20261018')
WIRE=OUT.with_name('upper-wire-export6-20261018')
CHECK=OUT/'check';UNIT='othello6-'+OUT.name+'.service'
RESERVE=260;OUTER=230;ALLOWANCE=10;OUTPUT_CAP=96*2**20
previous.OUT=OUT;previous.CHECK=CHECK;common.OUT=OUT;common.HARD_GIB=4;common.RESERVATION_CPU=RESERVE


def storage(frozen,reserve=0):
    own=batch.allocated(OUT);free=shutil.disk_usage(ROOT).free
    assert own+reserve<=OUTPUT_CAP and frozen['prior_allocated_study_bytes']+own+reserve<12*2**30
    assert free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
    return dict(allocated_study_bytes=frozen['prior_allocated_study_bytes']+own,
        own_output_bytes=own,root_free_bytes=free,data_free_bytes=shutil.disk_usage(OUT).free,
        reserved_bytes=reserve,checked_utc=utc())


def freeze_forecast(selection,emission,phases):
    points=[(emission['cases'][str(p)]['tokens'],phases['part'+str(p)]['cpu_seconds']) for p in selection['training']]
    xbar=sum(x for x,y in points)/len(points);ybar=sum(y for x,y in points)/len(points)
    den=sum((x-xbar)**2 for x,y in points)
    slope=max(0,sum((x-xbar)*(y-ybar) for x,y in points)/den) if den else 0
    intercept=max(0,ybar-slope*xbar)
    predicted={str(p):intercept+slope*emission['cases'][str(p)]['tokens'] for p in selection['held_out']}
    return dict(created_utc=utc(),training_parts=selection['training'],held_out_parts=selection['held_out'],
        model='nonnegative affine CPU versus tokens at fixed200 owners/common sampled map',
        intercept=intercept,cpu_per_token=slope,predicted_held_out_cpu_seconds=predicted,
        predicted_held_out_total_cpu_seconds=sum(predicted.values()),
        accepted_component_error_limit_percent=30,full_workflow_forecast=False,production_go=False)


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text())
    assert all(common.sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    assert all(common.sha(ROOT/'src'/n)==h for n,h in plan['generic_source_sha256'].items())
    assert common.sha(ROOT/'certificates/six-line.json')==plan['line_source_sha256']
    expected={Path(k):tuple(v) for k,v in plan['donors'].items()}
    frozen=json.loads((OUT/'storage-freeze.json').read_text());common.storage=lambda reserve=0:storage(frozen,reserve)
    selection=plan['selection'];phases={};source=None;emission=None
    with contextlib.ExitStack() as stack:
        for donor in expected:
            f=stack.enter_context((donor/'_build/.study6.lock').open('rb'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before=batch.donor_snapshot(expected);stack.enter_context(common.watched())
        fields=['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']
        result=run_job('prepare',previous.sandbox()+['/usr/bin/python3','-B',str(ROOT/'tools/upper_kernel_prepare6.py'),str(OUT)],
            OUT/'records',root=OUT/'control',timeout=160,cpu_limit=60,rss_limit_gib=2.5,log_limit_mib=2,
            expected_source_sha256=plan['control_source']['source_sha256'])
        phases['prepare']={k:result[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
        if result['accepted']:
            emission=json.loads((OUT/'emission.json').read_text());source=emission['source']
            assert source_identity(CHECK)==source and not assembly6.interfaces(CHECK)
            stack.enter_context(build_lock(CHECK))
            targets=[('core','Othello/ConsecutiveUpperRange6',6),('prefix','Othello/PackedPrefixBounds6',6),
                ('data','Tests/UpperKernelSample6/Root',40)]
            targets += [('part'+str(p),'Tests/UpperKernelSample6/Part'+str(p),10) for p in selection['training']+selection['held_out']]
            targets += [('all','Tests/UpperKernelSample6/All',10)]
            targets += [('witnesses','Tests/UpperKernelSample6/PrefixWitnesses',10)]
            for name,target,cap in targets:
                if name=='part'+str(selection['held_out'][0]):
                    forecast=freeze_forecast(selection,emission,phases);atomic_json(OUT/'forecast-freeze.json',forecast)
                    atomic_json(OUT/'heldout-freeze-pin.json',dict(created_utc=utc(),sha256=common.sha(OUT/'forecast-freeze.json')))
                storage(frozen,8*2**20)
                argv=previous.sandbox()+[batch.full_map.AGDA,'--no-libraries','-i','src']
                for donor in expected:argv+=['-i',str(donor/'src')]
                argv+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules',
                    'src/'+target+'.agda','+RTS','-M2800M','-s','-RTS']
                result=run_job(name,argv,OUT/'records',root=CHECK,timeout=100,cpu_limit=cap,rss_limit_gib=3.6,log_limit_mib=2,
                    expected_source_sha256=source['source_sha256'],
                    metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,upper_new_policy=True,
                        one_common_encoded_map=True,partial_only=True,initial_bounds_proved=False))
                phases[name]={k:result[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
                if not result['accepted']:break
        intact=batch.donor_snapshot(expected)==before
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        p1=all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items())
        same=source is None or source_identity(CHECK)==source
        complete=len(phases)==14 and all(p['accepted'] for p in phases.values())
        forecast_validation=None
        if complete:
            forecast=json.loads((OUT/'forecast-freeze.json').read_text())
            actual=sum(phases['part'+str(p)]['cpu_seconds'] for p in selection['held_out'])
            error=abs(forecast['predicted_held_out_total_cpu_seconds']-actual)/actual*100
            forecast_validation=dict(actual_held_out_cpu_seconds=actual,relative_error_percent=error,
                component_gate_passed=error<=30,full_workflow_forecast_validated=False,production_go=False)
            atomic_json(OUT/'forecast-validation.json',forecast_validation)
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),all_phases_accepted=complete,phases=phases,
            accepted_donors_unchanged=intact,p1_unchanged=p1,source_unchanged=same,
            upper_owned_rows=emission['owned_rows'] if complete else 0,one_common_encoded_map=True,
            unowned_rows_remain=True,forecast_validation=forecast_validation,
            initial_bounds_proved=False,mathematical_objective_complete=False))
        assert complete and intact and p1 and same,'UPPER sample incomplete; retain all receipts'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=500,cpu_limit=OUTER,rss_limit_gib=3.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists()
    assert common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    closed=json.loads((DONOR/'closure.json').read_text());assert closed['accepted']
    prior=closed['combined_scope_cpu_seconds']
    extension=json.loads((ROOT/'results/upper-kernel-scope-extension6-20261018.json').read_text())
    assert extension['new_cumulative_cap_cpu_seconds']==900 and extension['all_prior_combined_scope_cpu_seconds']==prior
    assert prior+RESERVE+ALLOWANCE<=900
    wire=json.loads((WIRE/'wire-manifest.json').read_text());assert json.loads((WIRE/'closure.json').read_text())['accepted']
    selection=json.loads((ROOT/'results/upper-kernel-sample-selection6-20261018.json').read_text())
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    externals={Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in extras|externals)
    assert used+OUTPUT_CAP<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir();control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),legacy_snapshot=legacy,
        extra_roots=[str(p) for p in sorted(extras|externals)],prior_allocated_study_bytes=used,
        own_output_cap_bytes=OUTPUT_CAP,retained_study_cap_gib=12,external_physical_bytes_counted=True))
    expected=json.loads((DONOR/'plan.json').read_text())['donors']
    expected[str(DONOR/'check')]=[closed['source_sha256'],closed['interface_pool_sha256']]
    extra_donors=json.loads((OUT.with_name('splice-suffix21-probe6-20261018')/'plan.json').read_text())['donors']
    for key,value in extra_donors.items():
        if 'path-splice-probe6-20261018-fixed/check' in key:expected[key]=value
    helpers=['upper_kernel_probe6.py','upper_kernel_prepare6.py','directed_probe6.py','unicode_codec_probe6.py',
        'compact_shared6.py','ref.py','bench6.py','census_pilot6.py','symmetry_stats6.py']+list(json.loads((DONOR/'plan.json').read_text())['helper_sha256'])
    plan=dict(created_utc=utc(),control_source=source_identity(control),donors=expected,
        helper_sha256={n:common.sha(ROOT/'tools'/n) for n in set(helpers)},
        generic_source_sha256={n+'.agda':common.sha(ROOT/'src'/(n+'.agda')) for n in
            ['Othello/ConsecutiveUpperRange6','Othello/PackedPrefixBounds6']},
        line_source_sha256=common.sha(ROOT/'certificates/six-line.json'),
        selection=selection,reservation=RESERVE,outer_cpu_cap=OUTER,scope_cpu_cap=900,
        previous_combined_scope_cpu_seconds=prior,new_controller_allowance_seconds=ALLOWANCE,
        hard_memory_gib=4,swap_bytes=0,core_bytes=0,
        phase_cpu_caps=[60,6,6,40]+[10]*10,upper_new_policy=True,untrusted_wire_sha256=wire['sha256'],
        full_workflow_forecast_validated=False,production_go=False,initial_bounds_proved=False)
    atomic_json(OUT/'plan.json',plan);atomic_json(OUT/'input-request.json',dict(wire=wire,selection=selection))
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'UPPER stratified1600 owners on actual shared map, heldout forecast; inline family explicitly extended900, preserving every earlier actual/allowance')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=4G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=520','--property=WorkingDirectory='+str(control),
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
