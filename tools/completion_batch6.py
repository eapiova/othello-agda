"""AI-assisted bounded continuation: new lower rows and common-map assembly."""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading

import assembly6
import canonical_multi_pilot6 as old
import canonical_state_pilot6 as canonical
import full_map_pilot6 as full_map
import new_row_bridge6 as bridge
from canonical_join6 import emit_join
from canonical_multi_prepare6 import prepare
from grouped_bridge_pilot6 import donor_snapshot
from provenance import digest_entries, source_identity
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger
from wire_part_samples6 import extract, selection


ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT/'results/completion6-continuation-authorization-20261018.json'
LABEL = 'completion-batch-lower-a6-20261018'
OUT = ROOT/'results'/LABEL
WORK = OUT/'work'
UNIT = 'othello6-' + LABEL + '.service'
PLAN = OUT/'plan.json'
BASELINE = ROOT/'results/canonical-multi6-20261018/collected/results/canonical-multi-pilot6/report.json'
ACCEPTED = full_map.BASE/'six-canonical-multi-20261018/results/canonical-multi-pilot6'
HELPERS = ['completion_batch6.py', 'grouped_bridge_pilot6.py', 'wire_part_samples6.py',
           'canonical_multi_prepare6.py', 'canonical_sample_parts6.py',
           'lazy_sample_parts6.py', 'new_row_bridge6.py', 'canonical_join6.py',
           'run_job.py', 'provenance.py', 'study6.py', 'assembly6.py']
GIB = 2**30
MIB = 2**20


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def authorized():
    auth = json.loads(AUTH.read_text())
    require(auth['approved'] and auth['formalization_and_necessary_tests_authorized']
            and not auth['additional_budget_authorized']
            and auth['ordinary_free_disk_floor_gib'] == 80
            and auth['hard_memory_gib'] == 12 and auth['swap_bytes'] == 0,
            'continuing user authorization and unchanged limits required')
    return auth


def allocated(path):
    return 0 if not path.exists() else int(subprocess.check_output(
        ['du', '-s', '-B1', str(path)], text=True).split()[0])


def storage(reserve=0):
    fresh = allocated(OUT)
    used = allocated(full_map.BASE) + allocated(ROOT/'results/grouped-bridge6-20261018') + fresh
    free = shutil.disk_usage(ROOT).free
    require(fresh + reserve <= 64*MIB and used + reserve < 12*GIB
            and free - reserve >= 80*GIB, 'ordinary disk floor or artifact cap reached')
    return dict(new_artifact_bytes=fresh, allocated_study_bytes=used, free_bytes=free,
                reserved_bytes=reserve, free_floor_bytes=80*GIB, checked_utc=utc())


def resources():
    groups = [line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
              if line.startswith('0::')]
    require(len(groups) == 1, 'one unified cgroup required')
    group = Path('/sys/fs/cgroup')/groups[0].lstrip('/')
    require((group/'memory.max').read_text().strip() == str(12*GIB)
            and (group/'memory.swap.max').read_text().strip() == '0',
            'hard12GiB/no-swap cgroup required')
    return group


def usage(group):
    cpu = dict(line.split() for line in (group/'cpu.stat').read_text().splitlines())
    return dict(cpu_seconds=int(cpu['usage_usec'])/1e6,
                memory_peak_bytes=int((group/'memory.peak').read_text()),
                swap_peak_bytes=int((group/'memory.swap.peak').read_text()))


@contextlib.contextmanager
def watched(group):
    stop = threading.Event()
    failures = []

    def watch():
        while not stop.wait(3):
            try:
                require(usage(group)['cpu_seconds'] < 650, '650CPU service stop reached')
                atomic_json(OUT/'storage.json', storage(8*MIB))
            except BaseException as error:
                failures.append(str(error))
                atomic_json(OUT/'resource-stop.json', dict(reason=str(error), finished_utc=utc()))
                os.kill(os.getpid(), signal.SIGTERM)
                return

    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        yield
    finally:
        stop.set()
        watcher.join()
    require(not failures, 'resource watcher stopped this batch')


def expected_donors():
    report = json.loads(BASELINE.read_text())
    require(report['accepted'], 'accepted common-map baseline required')
    phases = {phase['label']: phase for phase in report['phases']}
    expected = {bridge.FULL: (bridge.FULL_SOURCE_SHA, bridge.FULL_POOL_SHA),
                bridge.ALIGNED: (bridge.ALIGNED_SOURCE, bridge.ALIGNED_POOL),
                full_map.DONOR: (full_map.DONOR_SOURCE_SHA, full_map.DONOR_POOL_SHA)}
    units = []
    for part in old.PARTS:
        for side, label in [('rows', 'rows-'), ('bridge', 'bridge-')]:
            phase = phases[label + str(part)]
            expected[ACCEPTED/'prepared/parts'/str(part)/side] = (
                phase['record']['source_sha256'], phase['interface_pool_sha256'])
        units.append(dict(part=part, rows=200, row_prefix=old.PREFIX+'.Rows'+str(part),
                          bridge_prefix=old.PREFIX+'.Bridge'+str(part)))
    prior = json.loads((old.CANONICAL/'report.json').read_text())
    require(prior['accepted'], 'accepted canonical Part34176 required')
    expected[old.PRIOR_ROW] = (prior['row_record']['source_sha256'], prior['row_interface_pool_sha256'])
    expected[old.PRIOR_BRIDGE] = (prior['bridge_record']['source_sha256'], prior['bridge_interface_pool_sha256'])
    units.append(dict(part=34176, rows=200, row_prefix=canonical.ROW_PREFIX,
                      bridge_prefix=canonical.BRIDGE_PREFIX))
    return expected, units


def pinned_plan():
    plan = json.loads(PLAN.read_text())
    require(plan['authorization_sha256'] == sha(AUTH)
            and all(sha(ROOT/'tools'/name) == pin for name, pin in plan['helper_sha256'].items()),
            'authorized worker or helper source changed')
    return plan


def worker():
    authorized()
    plan = pinned_plan()
    group = resources()
    report = dict(format='othello-completion-batch6-report-v1', accepted=False,
                  created_utc=utc(), phase='preflight', selection=plan['selection'],
                  initial_problem2_proved=False, optimal_initial_pair_proved=False,
                  production_authorized=False, whole_workflow_validated=False)
    atomic_json(OUT/'report.json', report)
    expected, units = expected_donors()
    with contextlib.ExitStack() as stack, watched(group):
        for donor in sorted(expected):
            lock = stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = donor_snapshot(expected)
        require(sha(full_map.AGDA) == full_map.AGDA_SHA, 'pinned safe checker changed')
        require(sha(bridge.FULL/'results/full-state-map6.json') == canonical.FULL_MANIFEST_SHA,
                'complete canonical state manifest changed')
        history = json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        require(all(sha(ROOT/name) == pin for name, pin in history['p1_files'].items()), 'P1 changed')
        report.update(phase='extracting-new-rows')
        atomic_json(OUT/'report.json', report)
        sample = extract(full_map.NATIVE_EXPORT/'initial-lower.wire',
                         expected_sha256=plan['wire_sha256'], expected_rows=6873047,
                         selected=plan['selection']['selected'])
        atomic_json(OUT/'sample.json', sample)
        layout = prepare(OUT/'sample.json', bridge.FULL/'results/full-state-map6.json',
                         parts=plan['selection']['selected'], output=WORK/'prepared',
                         prefix='Tests.CompletionBatchLowerA6', expected_sample_sha256=sha(OUT/'sample.json'),
                         expected_full_sha256=canonical.FULL_MANIFEST_SHA)
        roots = []
        modules = set()
        for entry in layout['layouts']:
            part = entry['part']
            for side in ('row', 'bridge'):
                path = WORK/'prepared'/entry[side+'_root']
                roots.append(path)
                for relative in entry[side+'_layout']['generated_sha256']:
                    if relative.endswith('.agda'):
                        modules.add(relative[4:-5].replace('/', '.'))
            units.append(dict(part=part, rows=entry['rows'],
                              row_prefix=entry['row_layout']['prefix'],
                              bridge_prefix=entry['bridge_layout']['prefix']))
        joint = emit_join(WORK/'semantic-joint', json.loads((bridge.FULL/'results/full-state-map6.json').read_text()),
                          units, prefix='Tests.CompletionBatchLowerACombined6')
        joint_root = WORK/'semantic-joint'
        roots.append(joint_root)
        modules.add(joint['root_module'])
        for path in roots:
            stack.enter_context(build_lock(path))
        sources = {str(path): source_identity(path) for path in roots}
        require(all(not assembly6.interfaces(path) for path in roots), 'owned caches must start cold')
        report.update(phase='checking-new-rows-and-common-map-join', layout=layout,
                      joint_layout=joint, expected_modules=sorted(modules),
                      new_wire_epoch_rows=layout['selected_rows'], joint_owned_rows=joint['owned_rows'])
        atomic_json(OUT/'report.json', report)
        argv = ['/usr/bin/bwrap', '--ro-bind', '/', '/', '--bind', str(WORK), str(WORK),
                '--proc', '/proc', '--dev-bind', '/dev', '/dev', '--tmpfs', '/tmp',
                '--die-with-parent', '--', full_map.AGDA, '--no-libraries', '-i', 'src']
        for path in roots[:-1] + list(expected):
            argv += ['-i', str(path/'src')]
        argv += ['--safe', '--without-K', '--cubical-compatible', '--save-metas',
                 '--profile=modules', 'src/'+joint['root_module'].replace('.', '/')+'.agda',
                 '+RTS', '-M10G', '-c', '-s', '-RTS']
        record = run_job('batch-agda', argv, OUT/'records', root=joint_root, timeout=1500,
                         cpu_limit=500, rss_limit_gib=11.5, log_limit_mib=8,
                         expected_source_sha256=sources[str(joint_root)]['source_sha256'],
                         metadata=dict(checker_binary_sha256=full_map.AGDA_SHA,
                                       own_targets_cold=True, native_search_allowed=False,
                                       production_authorized=False))
        checked = re.findall(r'(?m)^\s*Checking (\S+) \(', (OUT/'records/batch-agda.log').read_text())
        pools = {str(path): assembly6.interfaces(path) for path in roots}
        new_intact = all(source_identity(path) == sources[str(path)] for path in roots)
        donors_intact = donor_snapshot(expected) == before
        p1_intact = all(sha(ROOT/name) == pin for name, pin in history['p1_files'].items())
        accepted = bool(record['accepted'] and new_intact and donors_intact and p1_intact
                        and set(checked) == modules and len(checked) == len(modules)
                        and sum(map(len, pools.values())) == len(modules))
        atomic_json(OUT/'interfaces.json', pools)
        report.update(accepted=accepted, phase='complete' if accepted else 'not-accepted',
                      record=record, checked_modules=checked, new_sources_unchanged=new_intact,
                      accepted_donors_unchanged=donors_intact, p1_unchanged=p1_intact,
                      donor_snapshots=before, new_interface_count=sum(map(len, pools.values())),
                      storage=storage(), cgroup=usage(group), finished_utc=utc())
        atomic_json(OUT/'report.json', report)
        require(accepted, 'batch did not pass; retain exact partial receipts before choosing next work')


def supervise():
    authorized()
    pinned_plan()
    group = resources()
    job = json.loads((OUT/'job.json').read_text())
    require(not (OUT/'records'/(LABEL+'.json')).exists(), 'existing job receipt; never restart')
    control = OUT/'control'
    record = run_job(LABEL, ['/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'worker'],
                     OUT/'records', root=control, timeout=1740, cpu_limit=600,
                     rss_limit_gib=11.75, log_limit_mib=4,
                     reservation_id=job['reservation']['reservation_id'],
                     expected_source_sha256=job['control_source']['source_sha256'],
                     metadata=dict(continuation_authorization_sha256=sha(AUTH),
                                   scope='new lower certificate rows and common-map assembly',
                                   native_search_allowed=False, production_authorized=False))
    atomic_json(OUT/'service-accounting.json', usage(group))
    print(json.dumps(dict(accepted=record['accepted'], cpu_seconds=record['cpu_seconds'],
                          exit_code=record['exit_code'])), flush=True)
    return 0 if record['accepted'] else 1


def launch():
    authorized()
    require(not OUT.exists() and not any(path.is_symlink() for path in (OUT, *OUT.parents)),
            'fresh continuation output required')
    active = subprocess.check_output(['systemctl', '--user', 'list-units', '--state=activating,running',
                                      '--type=service', '--no-legend', '--plain', 'othello*'], text=True)
    require(not active.strip(), 'another Othello service active')
    processes = subprocess.check_output(['ps', '-eo', 'comm='], text=True).splitlines()
    require(not any(name.strip().lower() == 'agda' for name in processes), 'Agda already active')
    storage(64*MIB)
    old_plan = json.loads((ROOT/'results/wire-new-lower6-20261016/plan.json').read_text())
    excluded = sorted(set(old_plan['selection']['excluded'] + old_plan['selection']['selected']))
    selected = selection(34366, excluded, seed=2026101801, count=8)
    expected_donors()
    plan = dict(format='othello-completion-batch6-plan-v1', created_utc=utc(),
                authorization_sha256=sha(AUTH), selection=selected,
                helper_sha256={name: sha(ROOT/'tools'/name) for name in HELPERS},
                wire_sha256=old_plan['wire_sha256'], scope_cpu_max_seconds=750,
                kernel_reservation_seconds=700, assembly_control_allowance_seconds=50,
                legacy_full_map_pilot_remaining_unchanged=160.51004700000658,
                scope='new certificate-row verification; not a restart of the closed lower state-map pilot',
                hard_memory_gib=12, swap_bytes=0, free_disk_floor_gib=80,
                artifact_cap_gib=12, new_artifact_max_mib=64,
                initial_problem2_proved=False, optimal_initial_pair_proved=False,
                production_authorized=False)
    ledger = Ledger(ROOT/'results/study6-ledger.json')
    summary = Ledger.summary(json.loads(ledger.path.read_text()))
    require(summary['coordinator_host'] == 'eapiova' and not summary['outstanding'],
            'canonical ledger must have no outstanding work')
    require(summary['categories']['kernel']['available_cpu_seconds'] >= 700
            and summary['categories']['assembly']['available_cpu_seconds'] >= 50,
            'existing category balances insufficient')
    control = OUT/'control'
    control.mkdir(parents=True)
    shutil.copy2(Path(__file__), control/'worker.py')
    atomic_json(PLAN, plan)
    allowance = ledger.withhold('assembly', 50,
        'Continuing completion6 authorization18Oct: conservative preparation/final audit and outer-supervisor allowance for new lower certificate batch; no new grant or legacy full-map pilot reset.')
    reservation = ledger.reserve('kernel', 700, LABEL)
    args = ['systemd-run', '--user', '--no-block', '--unit='+UNIT,
            '--property=MemoryMax=12G', '--property=MemorySwapMax=0', '--property=CPUQuota=100%',
            '--property=TasksMax=256', '--property=KillMode=control-group',
            '--property=RuntimeMaxSec=1800', '--property=TimeoutStopSec=10',
            '--property=WorkingDirectory='+str(control),
            '--property=StandardOutput=append:'+str(OUT/'service.log'),
            '--property=StandardError=append:'+str(OUT/'service.log'),
            '/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'supervise']
    job = dict(format='othello-completion-batch6-job-v1', label=LABEL, unit=UNIT,
               reservation=reservation, control_allowance=allowance, control_source=source_identity(control),
               state='dispatching', plan_sha256=sha(PLAN), systemd_command=args, created_utc=utc())
    atomic_json(OUT/'job.json', job)
    response = subprocess.run(args, capture_output=True, text=True)
    job.update(state='submitted' if response.returncode == 0 else 'dispatch-failed',
               dispatch_exit_code=response.returncode, dispatch_stdout=response.stdout,
               dispatch_stderr=response.stderr, submitted_utc=utc())
    atomic_json(OUT/'job.json', job)
    print(json.dumps(dict(unit=UNIT, state=job['state'], selection=selected,
                          reservation=reservation, control_allowance=allowance)), flush=True)
    require(response.returncode == 0, 'dispatch failed; retain reservation until reconciled')


if __name__ == '__main__':
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    require(len(sys.argv) == 2 and sys.argv[1] in ('launch', 'supervise', 'worker'),
            'explicit launch, supervise or worker required')
    if sys.argv[1] == 'launch':
        launch()
    elif sys.argv[1] == 'supervise':
        raise SystemExit(supervise())
    else:
        worker()
