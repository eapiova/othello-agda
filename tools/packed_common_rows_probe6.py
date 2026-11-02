"""Bounded assembly of sampled row Steps on one fully instantiated packed map."""
import contextlib
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys

SYMBOLIC = len(sys.argv)==2 and sys.argv[1].endswith('-symbolic')
WIDE = SYMBOLIC or (len(sys.argv)==2 and sys.argv[1].endswith('-wide'))
RECOVERY = WIDE or (len(sys.argv)==2 and sys.argv[1].endswith('-fixed'))
SUFFIX = '-symbolic' if SYMBOLIC else '-wide' if WIDE else '-fixed' if RECOVERY else ''
if RECOVERY:sys.argv[1]=sys.argv[1][:-len(SUFFIX)]

import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
from provenance import source_identity
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger

ROOT = Path(__file__).resolve().parents[1]
PRIOR = Path('/mnt/data/othello-agda-desktop-artifacts-20261018/packed-common-rows-probe6-20261018')
OUT = PRIOR.with_name(PRIOR.name+SUFFIX) if RECOVERY else PRIOR
DONOR = OUT.with_name('big-rows-probe6-20261018-fixed')
CHECK = OUT/'check'
UNIT = 'othello6-'+OUT.name+'.service'
RESERVE = 140 if SYMBOLIC else 100
OUTER = 120 if SYMBOLIC else 80
HARD = 4 if WIDE else 2
ALLOWANCE = 10 if SYMBOLIC else 5 if WIDE else 10
previous.OUT = OUT
previous.CHECK = CHECK
common.OUT = OUT
common.HARD_GIB = HARD
common.RESERVATION_CPU = RESERVE


def worker():
    batch.authorized()
    plan=json.loads((OUT/'plan.json').read_text())
    assert all(common.sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    assert common.sha(ROOT/'src/Othello/PackedVectors6.agda')==plan['generic_source_sha256']
    assert common.sha(ROOT/'src/Game/NatMapCheck.agda')==plan['map_check_source_sha256']
    assert common.sha(ROOT/'src/Othello/PackedRowPartial6.agda')==plan['partial_source_sha256']
    expected={Path(k):tuple(v) for k,v in plan['donors'].items()}
    previous.install_storage(json.loads((OUT/'storage-freeze.json').read_text()))
    with contextlib.ExitStack() as stack:
        for donor in expected:
            f=stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stack.enter_context(common.watched())
        before=batch.donor_snapshot(expected)
        prepared=run_job('prepare',previous.sandbox()+['/usr/bin/python3','-B',
            str(ROOT/'tools/packed_common_rows6.py'),str(OUT)],OUT/'records',root=OUT/'control',
            timeout=50,cpu_limit=10,rss_limit_gib=1.8,log_limit_mib=2,
            expected_source_sha256=plan['control_source']['source_sha256'])
        fields=['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']
        phases={'prepare':{k:prepared[k] for k in fields}}
        atomic_json(OUT/'phase-summary.json',phases)
        if prepared['accepted']:
            source=json.loads((OUT/'emission.json').read_text())['source']
            assert source_identity(CHECK)==source and not assembly6.interfaces(CHECK)
            stack.enter_context(build_lock(CHECK))
            for target in ['Othello/PackedVectors6','Othello/PackedRowPartial6','Tests/PackedCommonRows6/Closed']:
                common.storage(8*2**20)
                argv=previous.sandbox()+[batch.full_map.AGDA,'--no-libraries','-i','src']
                for donor in expected:argv+=['-i',str(donor/'src')]
                argv+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules',
                    'src/'+target+'.agda','+RTS','-M2800M' if WIDE else '-M1400M','-s','-RTS']
                result=run_job(target.replace('/','-').lower(),argv,OUT/'records',root=CHECK,
                    timeout=130,cpu_limit=70 if SYMBOLIC else 50,rss_limit_gib=3.6 if WIDE else 1.8,log_limit_mib=2,
                    expected_source_sha256=source['source_sha256'],
                    metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,
                        partial_only=True,unowned_citation_obligations_remain=True))
                phases[target]={k:result[k] for k in fields}
                atomic_json(OUT/'phase-summary.json',phases)
                if not result['accepted']:break
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        intact=batch.donor_snapshot(expected)==before
        p1=all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items())
        same=not prepared['accepted'] or source_identity(CHECK)==source
        complete=len(phases)==4 and all(r['accepted'] for r in phases.values())
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),phases=phases,
            all_phases_accepted=complete,accepted_donors_unchanged=intact,p1_unchanged=p1,
            source_unchanged=same,owned_sampled_rows_on_one_encoded_map=3000 if complete else 0,
            ownership_and_citation_compatibility_discharged=complete,
            unowned_citation_obligations_remain=True,
            not_added_to_old2600_map=True,old2600_map_preserved=True,
            initial_bounds_proved=False,mathematical_objective_complete=False))
        assert intact and p1 and same and complete,'Common packed partial incomplete; preserve receipts'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'+SUFFIX],
        OUT/'records',root=OUT/'control',timeout=250,cpu_limit=OUTER,rss_limit_gib=3.8 if WIDE else 1.9,
        log_limit_mib=2,reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized()
    assert not OUT.exists() and common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA
    assert not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    closed=json.loads((DONOR/'closure.json').read_text())
    assert closed['accepted'] and closed['heldout_component_gate_passed']
    scope_prior=closed['combined_scope_cpu_seconds']
    if RECOVERY:
        failed_root=PRIOR.with_name(PRIOR.name+('-wide' if SYMBOLIC else '-fixed')) if WIDE else PRIOR
        failed=json.loads((failed_root/'closure.json').read_text())
        assert not failed['accepted'] and not failed.get('closed_partial_checked',False)
        scope_prior=failed['combined_scope_cpu_seconds']
    assert scope_prior+RESERVE+ALLOWANCE<=600
    cap=json.loads((ROOT/'results/inline-calibration-cap-extension6-20261018.json').read_text())
    assert cap['new_cumulative_cap_cpu_seconds']==600
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    externals={Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    prior_bytes=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in extras|externals)
    assert prior_bytes+64*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir()
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),legacy_snapshot=legacy,
        extra_roots=[str(p) for p in sorted(extras|externals)],prior_allocated_study_bytes=prior_bytes,
        own_output_cap_bytes=64*2**20,retained_study_cap_gib=12,root_free_floor_gib=80,
        external_physical_bytes_counted=True))
    atomic_json(OUT/'input-request.json',dict(created_utc=utc(),sample=str(DONOR/'sample.json'),
        sample_sha256=common.sha(DONOR/'sample.json'),same_three1000_row_bundles=True,
        no_new_wire_scan=True,no_native_solver=True))
    expected=json.loads((DONOR/'plan.json').read_text())['donors']
    expected[str(DONOR/'check')]=[closed['source_sha256'],closed['interface_pool_sha256']]
    helpers=['packed_common_rows_probe6.py','packed_common_rows6.py']+list(json.loads((DONOR/'plan.json').read_text())['helper_sha256'])
    control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    plan=dict(created_utc=utc(),control_source=source_identity(control),donors=expected,
        helper_sha256={n:common.sha(ROOT/'tools'/n) for n in helpers},
        generic_source_sha256=common.sha(ROOT/'src/Othello/PackedVectors6.agda'),
        map_check_source_sha256=common.sha(ROOT/'src/Game/NatMapCheck.agda'),
        partial_source_sha256=common.sha(ROOT/'src/Othello/PackedRowPartial6.agda'),
        hard_memory_gib=HARD,swap_bytes=0,core_bytes=0,reservation=RESERVE,
        scope_cpu_cap=600,previous_combined_scope_cpu_seconds=scope_prior,
        new_controller_allowance_seconds=ALLOWANCE,outer_cpu_cap=OUTER,phase_cpu_cap=70 if SYMBOLIC else 50,
        no_same_wrapper_retry=True,architecture_variant='symbolic-partial-boundary' if SYMBOLIC else 'explicit-ownership',
        recovery_attempt=0 if SYMBOLIC else 2 if WIDE else 1 if RECOVERY else 0,
        no_additional_recovery_scheduled=True,original_attempt=str(failed_root) if RECOVERY else None,
        purpose='Discharge ownership and sparse citation-map compatibility for1000-row encoded Steps; one common packed Partial over3000 sampled rows. Preserve old2600 map, no full-production GO.')
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json')
    assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'One common encoded-map partial assembly inside original inline600 scope; preserve every prior actual and storage safeguard')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,
        control_source=plan['control_source'],unit=UNIT))
    argv=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax='+str(HARD)+'G',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%',
        '--property=TasksMax=128','--property=KillMode=control-group','--property=RuntimeMaxSec=280',
        '--property=WorkingDirectory='+str(control),'--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),'/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise'+SUFFIX]
    done=subprocess.run(argv,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=argv,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr))
    assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,combined_reserved_scope_cpu_seconds=scope_prior+RESERVE+ALLOWANCE)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
