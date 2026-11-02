"""Finish the never-started text-map holdout in the same inline200 scope, never new coverage."""
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
from contiguous_explicit_driver6 import EXTRA_PATTERNS
from provenance import source_identity
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/mnt/data/othello-agda-desktop-artifacts-20261018/text-map-holdout6-20261018')
CHECK = OUT/'check'
UNIT = 'othello6-'+OUT.name+'.service'
TARGETS = ['Tests/TextMapHoldoutOnly6/Holdout']
RESERVE = 15
OUTER = 10
common.OUT = OUT
common.HARD_GIB = 3
common.RESERVATION_CPU = RESERVE+17


def install_storage(frozen):
    def storage(reserve=0):
        own = batch.allocated(OUT)
        free = shutil.disk_usage(ROOT).free
        used = frozen['prior_allocated_study_bytes']+own
        assert own+reserve <= 12*2**20 and used+reserve < 12*2**30
        assert free-2**20 >= 80*2**30
        assert shutil.disk_usage(OUT).free-reserve >= 80*2**30
        return dict(allocated_study_bytes=used, new_artifact_bytes=own,
                    root_free_bytes=free, data_free_bytes=shutil.disk_usage(OUT).free, root_metadata_reserve_bytes=2**20, reserved_bytes=reserve, checked_utc=utc())
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
                '--profile=modules', 'src/'+name+'.agda', '+RTS', '-M2G', '-s', '-RTS']
            r = run_job(name.replace('/', '-').lower(), argv, OUT/'records', root=CHECK,
                timeout=120, cpu_limit=12, rss_limit_gib=2.75, log_limit_mib=2,
                expected_source_sha256=plan['source']['source_sha256'],
                metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,
                              conditional_theorem_only=True))
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
            conditional_existing_rows=600 if complete else 0,
            new_distinct_rows=0, initial_bounds_proved=False,
            mathematical_objective_complete=False, finished_utc=utc()))
        assert intact and p1 and same and complete, 'Shared-instance comparison incomplete; retain receipts'


def supervise():
    job = json.loads((OUT/'job.json').read_text())
    r = run_job(OUT.name, ['/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'worker'],
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
    prior = ROOT/'results/text-map-scaling6-20261018-fixed'
    closed = json.loads((prior/'closure.json').read_text())
    assert closed['accepted_partial_semantic_phases']
    scope_prior = closed['combined_scope_cpu_seconds']
    assert scope_prior+RESERVE <= 200
    # Snapshot the same study inventory plus every subsequent retained probe.
    legacy = common.storage(0)
    patterns = EXTRA_PATTERNS+['global-upper-layout6-20261018*', 'step-existing-partial6-20261018*',
                               'citation-diagnostic6-20261018*', 'shared-inline-scaling6-20261018*', 'text-map-scaling6-20261018*']
    extras = {p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    extra_bytes = sum(batch.allocated(p) for p in extras)
    frozen = dict(created_utc=utc(), legacy_snapshot=legacy,
        extra_roots=[str(p) for p in sorted(extras)], extra_allocated_bytes=extra_bytes,
        prior_allocated_study_bytes=legacy['allocated_study_bytes']+extra_bytes,
        own_output_cap_bytes=12*2**20, retained_study_cap_gib=12, free_disk_floor_gib=80,
        external_output_physical_path=str(OUT), external_own_bytes_included=True,
        external_registry='results/study6-external-artifacts-20261018.json', root_metadata_reserve_bytes=2**20)
    assert frozen['prior_allocated_study_bytes']+12*2**20 < 12*2**30
    assert shutil.disk_usage(ROOT).free-2**20 >= 80*2**30
    assert shutil.disk_usage(OUT.parent).free-12*2**20 >= 80*2**30
    from text_map_holdout6 import emit
    emit(CHECK)
    shutil.copy2(ROOT/'othello.agda-lib', CHECK/'othello.agda-lib')
    atomic_json(OUT/'storage-freeze.json', frozen)
    donor = ROOT/'results/shared-inline-scaling6-20261018'
    expected = json.loads((donor/'plan.json').read_text())['donors']
    meta = json.loads((donor/'closure.json').read_text())
    assert meta['accepted']
    expected[str(donor/'check')] = [meta['source_sha256'], meta['interface_pool_sha256']]
    partial = ROOT/'results/text-map-scaling6-20261018-fixed'
    meta = json.loads((partial/'closure.json').read_text())
    expected[str(partial/'check')] = [meta['source_sha256'], meta['interface_pool_sha256']]
    helpers = ['text_map_holdout_probe6.py', 'text_map_holdout6.py', 'text_map_scaling6.py', 'shared_inline_scaling6.py',
        'inline_boundary_scaling6.py', 'inline_scaling6.py', 'inline_compact_scaling6.py',
        'directed_scaling6.py', 'contiguous_explicit_driver6.py', 'citation_diagnostic6.py',
        'completion_batch6.py', 'run_job.py', 'study6.py', 'provenance.py', 'assembly6.py']
    atomic_json(OUT/'plan.json', dict(created_utc=utc(), source=source_identity(CHECK), donors=expected,
        helper_sha256={n: common.sha(ROOT/'tools'/n) for n in helpers}, hard_memory_gib=3,
        swap_bytes=0, core_bytes=0, reservation=RESERVE, scope_cpu_cap=200,
        phase_cpu_cap=12, outer_cpu_cap=OUTER, service_cpu_guard_seconds=RESERVE-3,
        total_hard_memory_gib=3, conditional_theorem_only=True,
        prior_scope_closure=str(prior/'closure.json'), previous_combined_scope_cpu_seconds=scope_prior,
        new_controller_allowance_seconds=0))
    control = OUT/'control'
    control.mkdir()
    shutil.copy2(Path(__file__), control/'worker.py')
    ledger = Ledger(ROOT/'results/study6-ledger.json')
    assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance = dict(reused_from='results/text-map-scaling6-20261018/job.json', additional_withholding_seconds=0)
    reservation = ledger.reserve('kernel', RESERVE, OUT.name)
    atomic_json(OUT/'job.json', dict(reservation=reservation, control_allowance=allowance,
        control_source=source_identity(control), unit=UNIT))
    argv = ['systemd-run', '--user', '--no-block', '--unit='+UNIT,
        '--property=MemoryMax=3G', '--property=MemorySwapMax=0', '--property=LimitCORE=0',
        '--property=CPUQuota=100%', '--property=TasksMax=128', '--property=KillMode=control-group',
        '--property=RuntimeMaxSec=400', '--property=WorkingDirectory='+str(control),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'supervise']
    done = subprocess.run(argv, capture_output=True, text=True)
    atomic_json(OUT/'dispatch.json', dict(argv=argv, exit_code=done.returncode,
        stdout=done.stdout, stderr=done.stderr))
    assert done.returncode == 0
    print(json.dumps(dict(unit=UNIT, reservation=reservation,
                         combined_reserved_scope_cpu_seconds=scope_prior+RESERVE)))


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ['launch', 'worker', 'supervise']
    if sys.argv[1] == 'launch':
        launch()
    elif sys.argv[1] == 'worker':
        worker()
    else:
        raise SystemExit(supervise())
