"""Retarget accepted rows to actual map chunks and check UPPER terminal fixture."""
import contextlib
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
from provenance import source_identity
from run_job import atomic_json,build_lock,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/othello-agda-desktop-artifacts-20261018/range-upper-probe6-20261018')
DONOR=OUT.with_name('consecutive-global-probe6-20261018')
CHECK=OUT/'check';UNIT='othello6-'+OUT.name+'.service'
RESERVE=65;OUTER=45;ALLOWANCE=5
previous.OUT=OUT;previous.CHECK=CHECK
common.OUT=OUT;common.HARD_GIB=4;common.RESERVATION_CPU=RESERVE


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text())
    assert all(common.sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    assert all(common.sha(ROOT/'src'/n)==h for n,h in plan['generic_source_sha256'].items())
    expected={Path(k):tuple(v) for k,v in plan['donors'].items()}
    previous.install_storage(json.loads((OUT/'storage-freeze.json').read_text()))
    with contextlib.ExitStack() as stack:
        for donor in expected:
            f=stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stack.enter_context(common.watched())
        before=batch.donor_snapshot(expected)
        fields=['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']
        prepared=run_job('prepare',previous.sandbox()+['/usr/bin/python3','-B',str(ROOT/'tools/range_upper_prepare6.py'),str(OUT)],
            OUT/'records',root=OUT/'control',timeout=20,cpu_limit=3,rss_limit_gib=1.5,log_limit_mib=2,
            expected_source_sha256=plan['control_source']['source_sha256'])
        phases={'prepare':{k:prepared[k] for k in fields}};atomic_json(OUT/'phase-summary.json',phases)
        source=None
        if prepared['accepted']:
            source=json.loads((OUT/'emission.json').read_text())['source']
            assert source_identity(CHECK)==source and not assembly6.interfaces(CHECK)
            stack.enter_context(build_lock(CHECK))
            for target,cap in [('Game/StepRangeAssembly',10),('Othello/ConsecutiveRange6',6),('Othello/ConsecutivePackedUpper6',10),('Tests/RangeUpper6/Retarget',10),('Tests/RangeUpper6/Upper',5)]:
                common.storage(8*2**20)
                args=previous.sandbox()+[batch.full_map.AGDA,'--no-libraries','-i','src']
                for donor in expected:args+=['-i',str(donor/'src')]
                args+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules',
                    'src/'+target+'.agda','+RTS','-M2800M','-s','-RTS']
                result=run_job(target.replace('/','-').lower(),args,OUT/'records',root=CHECK,
                    timeout=110,cpu_limit=cap,rss_limit_gib=3.6,log_limit_mib=2,
                    expected_source_sha256=source['source_sha256'],
                    metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,
                        reuse_exact_accepted10000_rows=True,additional_wire_scans=0,
                        partial_only=True,initial_bounds_proved=False))
                phases[target]={k:result[k] for k in fields};atomic_json(OUT/'phase-summary.json',phases)
                if not result['accepted']:break
        intact=batch.donor_snapshot(expected)==before
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        p1=all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items())
        same=source is None or source_identity(CHECK)==source
        complete=len(phases)==6 and all(r['accepted'] for r in phases.values())
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),phases=phases,all_phases_accepted=complete,
            accepted_donors_unchanged=intact,p1_unchanged=p1,source_unchanged=same,
            owned_sampled_rows_on_one_encoded_map=10000 if complete else 0,
            additional_wire_scans=0,new_native_solver_runs=0,actual_state_chunk_retarget=True,upper_terminal_fixture=True,
            unowned_state_rows_remain=True,separate_from_old3000_and2600_maps=True,
            full_workflow_forecast_validated=False,production_go=False,
            initial_bounds_proved=False,mathematical_objective_complete=False))
        assert complete and intact and p1 and same,'Sequential10000 recovery incomplete; preserve every receipt'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=220,cpu_limit=OUTER,rss_limit_gib=3.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists()
    assert common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    closed=json.loads((DONOR/'closure.json').read_text())
    assert closed['accepted'] and closed['owned_sampled_rows_on_one_encoded_map']==10000
    prior=closed['combined_scope_cpu_seconds'];assert prior+RESERVE+ALLOWANCE<=600
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    externals={Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in extras|externals)
    assert used+64*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir();control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),legacy_snapshot=legacy,
        extra_roots=[str(p) for p in sorted(extras|externals)],prior_allocated_study_bytes=used,
        own_output_cap_bytes=64*2**20,retained_study_cap_gib=12,root_free_floor_gib=80,
        external_physical_bytes_counted=True))
    expected=json.loads((DONOR/'plan.json').read_text())['donors']
    expected[str(DONOR/'check')]=[closed['source_sha256'],closed['interface_pool_sha256']]
    helpers=['range_upper_probe6.py','range_upper_prepare6.py']+list(json.loads((DONOR/'plan.json').read_text())['helper_sha256'])
    plan=dict(created_utc=utc(),control_source=source_identity(control),donors=expected,
        helper_sha256={n:common.sha(ROOT/'tools'/n) for n in helpers},
        generic_source_sha256={n+'.agda':common.sha(ROOT/'src'/(n+'.agda')) for n in ['Game/StepRangeAssembly','Othello/ConsecutiveRange6','Othello/ConsecutivePackedUpper6']},hard_memory_gib=4,
        swap_bytes=0,core_bytes=0,reservation=RESERVE,outer_cpu_cap=OUTER,scope_cpu_cap=600,
        previous_combined_scope_cpu_seconds=prior,new_controller_allowance_seconds=ALLOWANCE,
        same_exact_state_and_body_data=True,retarget_only_no_certificate_rerun=True,original_attempt=str(DONOR),
        actual_state_chunk_retarget=True,upper_terminal_fixture=True,additional_wire_scans=0,
        owned_rows=10000,phase_cpu_caps=[3,10,6,10,10,5],single_recovery=False,no_full_production_authorized=True)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Retarget exact accepted10000-row sample to actual50 state chunks and check UPPER core/terminal fixture; original inline600 cumulative cap preserves every old actual')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,
        control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=4G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=250','--property=WorkingDirectory='+str(control),
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
