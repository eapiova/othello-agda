"""1000-row grouping under a recorded extension of the original inline scope."""
import contextlib
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys

# Parse before importing the older driver, whose import consumes a -fixed suffix.
RECOVERY = len(sys.argv) == 2 and sys.argv[1].endswith('-fixed')
if RECOVERY:
    sys.argv[1] = sys.argv[1][:-6]

import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
from contiguous_explicit_driver6 import EXTRA_PATTERNS
from provenance import source_identity
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger

ROOT = Path(__file__).resolve().parents[1]
PRIOR = Path('/mnt/data/othello-agda-desktop-artifacts-20261018/big-rows-probe6-20261018')
OUT = PRIOR.with_name(PRIOR.name+'-fixed') if RECOVERY else PRIOR
CHECK = OUT/'check'
UNIT = 'othello6-'+OUT.name+'.service'
RESERVE = 180 if RECOVERY else 250
OUTER = 160 if RECOVERY else 230
PREPARE = 10 if RECOVERY else 65
ALLOWANCE = 5 if RECOVERY else 10
common.OUT = OUT
common.HARD_GIB = 2
common.RESERVATION_CPU = RESERVE


def install_storage(frozen):
    def storage(reserve=0):
        own = batch.allocated(OUT)
        free = shutil.disk_usage(ROOT).free
        used = frozen['prior_allocated_study_bytes']+own
        assert own+reserve <= 64*2**20 and used+reserve < 12*2**30
        assert free-2**20 >= 80*2**30
        assert shutil.disk_usage(OUT).free-reserve >= 80*2**30
        return dict(allocated_study_bytes=used, own_output_bytes=own,
            root_free_bytes=free, root_metadata_reserve_bytes=2**20,
            data_free_bytes=shutil.disk_usage(OUT).free, reserved_bytes=reserve, checked_utc=utc())
    common.storage = storage


def sandbox():
    return ['/usr/bin/bwrap', '--ro-bind', '/', '/', '--bind', str(OUT), str(OUT),
        '--proc', '/proc', '--dev-bind', '/dev', '/dev', '--tmpfs', '/tmp', '--die-with-parent', '--']


def worker():
    batch.authorized()
    plan = json.loads((OUT/'plan.json').read_text())
    assert all(common.sha(ROOT/'tools'/n) == h for n,h in plan['helper_sha256'].items())
    expected = {Path(k): tuple(v) for k,v in plan['donors'].items()}
    install_storage(json.loads((OUT/'storage-freeze.json').read_text()))
    with contextlib.ExitStack() as stack:
        for donor in expected:
            f = stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stack.enter_context(common.watched())
        before = batch.donor_snapshot(expected)
        phases = {}
        args = sandbox()+['/usr/bin/python3', '-B', str(ROOT/'tools/big_rows_prepare6.py'), str(OUT)]
        prepared = run_job('prepare', args, OUT/'records', root=OUT/'control', timeout=200,
            cpu_limit=PREPARE, rss_limit_gib=1.8, log_limit_mib=2,
            expected_source_sha256=plan['control_source']['source_sha256'])
        phases['prepare'] = {k:prepared[k] for k in ['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']}
        atomic_json(OUT/'phase-summary.json', phases)
        if prepared['accepted']:
            source = json.loads((OUT/'emission.json').read_text())['source']
            assert source_identity(CHECK) == source and not assembly6.interfaces(CHECK)
            stack.enter_context(build_lock(CHECK))
            for phase in ['Training','Holdout']:
                common.storage(8*2**20)
                argv = sandbox()+[batch.full_map.AGDA,'--no-libraries','-i','src']
                for donor in expected:
                    argv += ['-i',str(donor/'src')]
                argv += ['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules',
                    'src/Tests/BigRowsScaling6/'+phase+'.agda','+RTS','-M1400M','-s','-RTS']
                result = run_job('tests-bigrowsscaling6-'+phase.lower(), argv, OUT/'records',root=CHECK,
                    timeout=160,cpu_limit=70,rss_limit_gib=1.8,log_limit_mib=2,
                    expected_source_sha256=source['source_sha256'],
                    metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,conditional_theorem_only=True))
                phases[phase] = {k:result[k] for k in ['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']}
                atomic_json(OUT/'phase-summary.json',phases)
                if not result['accepted']:
                    break
                from big_rows_scaling6 import summarize
                summarize(OUT,phase.lower())
                if phase=='Training':
                    atomic_json(OUT/'holdout-freeze-pin.json',dict(created_utc=utc(),sha256=common.sha(OUT/'forecast-freeze.json')))
        history = json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        intact = batch.donor_snapshot(expected)==before
        p1 = all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items())
        same = not prepared['accepted'] or source_identity(CHECK)==source
        complete = len(phases)==3 and all(p['accepted'] for p in phases.values())
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),all_phases_accepted=complete,
            phases=phases,accepted_donors_unchanged=intact,p1_unchanged=p1,source_unchanged=same,
            conditional_rows=3000 if complete else 0,new_distinct_common_map_rows=0,
            initial_bounds_proved=False,mathematical_objective_complete=False))
        assert intact and p1 and same and complete,'Larger grouping incomplete; retain every receipt'


def supervise():
    job = json.loads((OUT/'job.json').read_text())
    result = run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker-fixed' if RECOVERY else 'worker'],
        OUT/'records',root=OUT/'control',timeout=500,cpu_limit=OUTER,rss_limit_gib=1.9,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized()
    assert not OUT.exists() and common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA
    assert not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    cap=json.loads((ROOT/'results/inline-calibration-cap-extension6-20261018.json').read_text())
    assert cap['approved_under_user_authorization'] and cap['new_cumulative_cap_cpu_seconds']==600
    scope_prior=cap['all_prior_combined_scope_cpu_seconds']
    if RECOVERY:
        failed=json.loads((PRIOR/'closure.json').read_text())
        assert not failed['accepted'] and not failed['checker_started'] and cap['max_recovery_attempts']==1
        scope_prior=failed['combined_scope_cpu_seconds']
    assert scope_prior+RESERVE+ALLOWANCE<=600
    legacy=common.storage(0)
    patterns=EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    externals={Path(item['path']) for item in registry['roots'] if Path(item['path'])!=OUT}
    prior_bytes=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in extras|externals)
    assert prior_bytes+64*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir()
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),legacy_snapshot=legacy,
        extra_roots=[str(p) for p in sorted(extras|externals)],prior_allocated_study_bytes=prior_bytes,
        own_output_cap_bytes=64*2**20,retained_study_cap_gib=12,root_free_floor_gib=80,
        external_physical_bytes_counted=True))
    from big_rows_scaling6 import BUNDLES
    request=dict(created_utc=utc(),
        wire='/home/eapiova/projects/othello-agda/runs/six-full-map-lower-native-20261016/results/full-map-pilot6/initial-lower.wire',
        wire_sha256='d6b4786ebafc86c5f1513d8e300366b9baf3ff06879defa8e2cb19998dc3a762',
        wire_rows=6873047,selected_parts=sorted(p for parts in BUNDLES.values() for p in parts),
        bundles=BUNDLES,selection_frozen_before_extraction=True)
    if RECOVERY:
        request.update(reused_verified_sample=str(PRIOR/'sample.json'),
            reused_sample_sha256=failed['sample_sha256'],
            original_input_request_sha256=common.sha(PRIOR/'input-request.json'),
            original_attempt_closure=str(PRIOR/'closure.json'),additional_wire_scans=0)
    atomic_json(OUT/'input-request.json',request)
    donor=Path('/mnt/data/othello-agda-desktop-artifacts-20261018/text-map-holdout6-20261018-fixed')
    expected=json.loads((donor/'plan.json').read_text())['donors']
    meta=json.loads((donor/'closure.json').read_text());assert meta['accepted']
    expected[str(donor/'check')]=[meta['source_sha256'],meta['interface_pool_sha256']]
    helpers=['big_rows_probe6.py','big_rows_prepare6.py','big_rows_scaling6.py','wire_part_samples6.py',
        'full_state_map6.py','native_layout_samples6.py','wire_workflow6.py','text_map_scaling6.py',
        'shared_inline_scaling6.py','directed_probe6.py','unicode_codec_probe6.py','compact_shared6.py',
        'sparse_citation_pilot6.py','bench6.py','ref.py','directed_scaling6.py','inline_scaling6.py',
        'contiguous_explicit_driver6.py','citation_diagnostic6.py','completion_batch6.py',
        'run_job.py','study6.py','provenance.py','assembly6.py']
    control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    plan=dict(created_utc=utc(),control_source=source_identity(control),donors=expected,
        helper_sha256={n:common.sha(ROOT/'tools'/n) for n in helpers},hard_memory_gib=2,
        swap_bytes=0,core_bytes=0,reservation=RESERVE,scope_cpu_cap=600,prepare_cpu_cap=PREPARE,
        phase_cpu_cap=70,outer_cpu_cap=OUTER,total_hard_memory_gib=2,
        prior_scope_cap_extension='results/inline-calibration-cap-extension6-20261018.json',
        previous_combined_scope_cpu_seconds=scope_prior,new_controller_allowance_seconds=ALLOWANCE,
        recovery_attempt=1 if RECOVERY else 0,original_attempt=str(PRIOR) if RECOVERY else None,
        all_prior_actuals_and_withholdings_preserved=True)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Larger1000-row grouping recovery inside explicitly extended cumulative inline600 scope; no total grant, preserve every previous actual')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,
        control_source=plan['control_source'],unit=UNIT))
    argv=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=2G',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%',
        '--property=TasksMax=128','--property=KillMode=control-group','--property=RuntimeMaxSec=540',
        '--property=WorkingDirectory='+str(control),'--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),'/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise-fixed' if RECOVERY else 'supervise']
    done=subprocess.run(argv,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=argv,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr))
    assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,combined_reserved_scope_cpu_seconds=scope_prior+RESERVE+ALLOWANCE)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
