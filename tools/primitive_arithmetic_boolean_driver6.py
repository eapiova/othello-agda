"""Bounded Boolean screen only; no winning theorem or new proof coverage."""
import contextlib
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity, digest_entries
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = len(sys.argv) == 2 and sys.argv[1].endswith('-fixed')
if RECOVERY:
    sys.argv[1] = sys.argv[1][:-6]
OUT = ROOT/'results'/('primitive-arithmetic-boolean-probe6-20261018-fixed' if RECOVERY else 'primitive-arithmetic-boolean-probe6-20261018')
CHECK = OUT/'check'
UNIT = 'othello6-'+OUT.name+'.service'
TARGETS = ['Othello/PrimitiveArithmeticBoolean6',
           'Tests/PrimitiveArithmeticBooleanProbe6/Baseline',
           'Tests/PrimitiveArithmeticBooleanProbe6/Variant']
RESERVE = 55
OUTER = 40
common.OUT = OUT
common.HARD_GIB = 3
common.RESERVATION_CPU = RESERVE
EXTRA_PATTERNS = ['path-splice-probe6-20261018*', 'step-assembly-probe6-20261018*',
    'encoded-step-assembly-probe6-20261018*', 'query-layout6-20261018*',
    'reuse-query-layout6-20261018*', 'global-reuse-layout6-20261018*',
    'historical-query-layout6-20261018*', 'cross-bound*6-20261018*',
    'inline-scaling6-20261018*', 'inline-compact-scaling6-20261018*',
    'inline-boundary-scaling6-20261018*', 'degree-reuse-layout6-20261018*',
    'primitive-arithmetic-probe6-20261018*', 'primitive-arithmetic-boolean-probe6-20261018*']


def install_storage(frozen):
    def storage(reserve=0):
        own = batch.allocated(OUT)
        free = shutil.disk_usage(ROOT).free
        used = frozen['prior_allocated_study_bytes']+own
        assert own+reserve <= 16*2**20 and used+reserve < 12*2**30
        assert free-reserve >= 80*2**30
        return dict(allocated_study_bytes=used, new_artifact_bytes=own,
                    free_bytes=free, reserved_bytes=reserve, checked_utc=utc())
    common.storage = storage


def worker():
    batch.authorized()
    plan = json.loads((OUT/'plan.json').read_text())
    expected = {Path(k): tuple(v) for k, v in plan['donors'].items()}
    assert all(common.sha(ROOT/'tools'/n) == h for n, h in plan['helper_sha256'].items())
    install_storage(json.loads((OUT/'storage-freeze.json').read_text()))
    with contextlib.ExitStack() as stack:
        for donor in expected:
            f = stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stack.enter_context(build_lock(CHECK))
        stack.enter_context(common.watched())
        before = batch.donor_snapshot(expected)
        assert source_identity(CHECK) == plan['source'] and not assembly6.interfaces(CHECK)
        phases = {}
        for name in TARGETS:
            common.storage(8*2**20)
            argv = ['/usr/bin/bwrap', '--ro-bind', '/', '/', '--bind', str(CHECK), str(CHECK),
                '--proc', '/proc', '--dev-bind', '/dev', '/dev', '--tmpfs', '/tmp',
                '--die-with-parent', '--', batch.full_map.AGDA, '--no-libraries', '-i', 'src']
            for donor in expected:
                argv += ['-i', str(donor/'src')]
            argv += ['--safe', '--without-K', '--cubical-compatible', '--save-metas',
                '--profile=modules',
                'src/'+name+'.agda', '+RTS', '-M2G', '-s', '-RTS']
            r = run_job(name.replace('/', '-').lower(), argv, OUT/'records', root=CHECK,
                timeout=100, cpu_limit=15, rss_limit_gib=2.75, log_limit_mib=2,
                expected_source_sha256=plan['source']['source_sha256'],
                metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,
                              boolean_only=True, semantic_soundness_checked=False))
            phases[name] = {k: r[k] for k in ['accepted', 'exit_code', 'cpu_seconds',
                'wall_seconds', 'stop_reason', 'peak_rss_gib']}
            atomic_json(OUT/'phase-summary.json', phases)
            if not r['accepted']:
                break
        history = json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        intact = batch.donor_snapshot(expected) == before
        p1 = all(common.sha(ROOT/n) == h for n, h in history['p1_files'].items())
        same = source_identity(CHECK) == plan['source']
        complete = len(phases) == len(TARGETS) and all(p['accepted'] for p in phases.values())
        atomic_json(OUT/'report.json', dict(phases=phases, all_phases_accepted=complete,
            accepted_donors_unchanged=intact, p1_unchanged=p1, source_unchanged=same,
            boolean_only=True, semantic_soundness_checked=False,
            conditional_existing_rows=0, existing_repeated_boolean_rows=200 if complete else 0,
            new_distinct_rows=0, initial_bounds_proved=False,
            mathematical_objective_complete=False, finished_utc=utc()))
        assert intact and p1 and same and complete, 'Boolean screen failed; retain exact receipts'


def supervise():
    job = json.loads((OUT/'job.json').read_text())
    r = run_job(OUT.name, ['/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'worker-fixed' if RECOVERY else 'worker'],
        OUT/'records', root=OUT/'control', timeout=360, cpu_limit=OUTER,
        rss_limit_gib=2.9, log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if r['accepted'] else 1


def launch():
    batch.authorized()
    assert not OUT.exists() and common.sha(batch.full_map.AGDA) == batch.full_map.AGDA_SHA
    assert not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl', '--user', 'list-units',
        '--state=activating,running', '--type=service', '--no-legend', '--plain', 'othello*'], text=True).strip()
    prior = ROOT/'results/primitive-arithmetic-probe6-20261018-fixed'
    closed = json.loads((prior/'closure.json').read_text())
    assert not closed['accepted'] and closed['accepted_partial_interfaces'] == 1
    scope_prior = closed['combined_scope_cpu_seconds']
    if RECOVERY:
        failed = json.loads((ROOT/'results/primitive-arithmetic-boolean-probe6-20261018/closure.json').read_text())
        assert not failed['accepted']
        scope_prior = failed['combined_scope_cpu_seconds']
    allowance_seconds = 0 if RECOVERY else 10
    assert scope_prior+RESERVE+allowance_seconds <= 200
    legacy = common.storage(0)
    extras = {p for pattern in EXTRA_PATTERNS for p in (ROOT/'results').glob(pattern) if p != OUT}
    extra_bytes = sum(batch.allocated(p) for p in extras)
    frozen = dict(created_utc=utc(), legacy_snapshot=legacy,
        extra_roots=[str(p) for p in sorted(extras)], extra_allocated_bytes=extra_bytes,
        prior_allocated_study_bytes=legacy['allocated_study_bytes']+extra_bytes,
        own_output_cap_bytes=16*2**20, free_disk_floor_gib=80)
    assert frozen['prior_allocated_study_bytes']+16*2**20 < 12*2**30
    assert shutil.disk_usage(ROOT).free-16*2**20 >= 80*2**30
    from primitive_arithmetic_boolean_probe6 import emit
    emit(CHECK)
    atomic_json(OUT/'storage-freeze.json', frozen)
    expected = json.loads((prior/'plan.json').read_text())['donors']
    for name in ['inline-entries-probe6-20261018']:
        donor = ROOT/'results'/name
        meta = json.loads((donor/'closure.json').read_text())
        assert meta['accepted']
        # Include its already checked length/Unicode dependency pools too.
        expected.update(json.loads((donor/'plan.json').read_text())['donors'])
        expected[str(donor/'check')] = [meta['source_sha256'], meta['interface_pool_sha256']]
    partial_interfaces = assembly6.interfaces(prior/'check')
    state_receipt = json.loads((prior/'records/othello-primitivearithmeticstate6.json').read_text())
    assert state_receipt['accepted'] and len(partial_interfaces) == 1
    assert source_identity(prior/'check') == json.loads((prior/'plan.json').read_text())['source']
    expected[str(prior/'check')] = [source_identity(prior/'check')['source_sha256'], digest_entries(partial_interfaces)]
    helpers = ['primitive_arithmetic_boolean_driver6.py', 'primitive_arithmetic_boolean_probe6.py',
        'citation_diagnostic6.py', 'completion_batch6.py', 'run_job.py', 'study6.py', 'provenance.py', 'assembly6.py']
    atomic_json(OUT/'plan.json', dict(created_utc=utc(), source=source_identity(CHECK), donors=expected,
        helper_sha256={n: common.sha(ROOT/'tools'/n) for n in helpers}, hard_memory_gib=3,
        swap_bytes=0, core_bytes=0, reservation=RESERVE, scope_cpu_cap=200,
        phase_cpu_cap=15, outer_cpu_cap=OUTER, boolean_only=True,
        semantic_soundness_checked=False, accepted_partial_state_receipt=str(prior/'records/othello-primitivearithmeticstate6.json'),
        unaccepted_game_and_rows_not_imported=True, previous_combined_scope_cpu_seconds=scope_prior))
    control = OUT/'control'
    control.mkdir()
    shutil.copy2(Path(__file__), control/'worker.py')
    ledger = Ledger(ROOT/'results/study6-ledger.json')
    assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance = (dict(reused_from='results/primitive-arithmetic-boolean-probe6-20261018/job.json', additional_withholding_seconds=0)
        if RECOVERY else ledger.withhold('assembly', 10, 'Boolean-only arithmetic screen preparation/controller/closure within original200 arithmetic scope; no added budget.'))
    reservation = ledger.reserve('kernel', RESERVE, OUT.name)
    atomic_json(OUT/'job.json', dict(reservation=reservation, control_allowance=allowance,
        control_source=source_identity(control), unit=UNIT))
    argv = ['systemd-run', '--user', '--no-block', '--unit='+UNIT,
        '--property=MemoryMax=3G', '--property=MemorySwapMax=0', '--property=LimitCORE=0',
        '--property=CPUQuota=100%', '--property=TasksMax=128', '--property=KillMode=control-group',
        '--property=RuntimeMaxSec=400', '--property=WorkingDirectory='+str(control),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'supervise-fixed' if RECOVERY else 'supervise']
    done = subprocess.run(argv, capture_output=True, text=True)
    atomic_json(OUT/'dispatch.json', dict(argv=argv, exit_code=done.returncode,
        stdout=done.stdout, stderr=done.stderr))
    assert done.returncode == 0
    print(json.dumps(dict(unit=UNIT, reservation=reservation,
        scope_reserved_envelope=scope_prior+RESERVE+allowance_seconds)))


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ['launch', 'worker', 'supervise']
    if sys.argv[1] == 'launch':
        launch()
    elif sys.argv[1] == 'worker':
        worker()
    else:
        raise SystemExit(supervise())
