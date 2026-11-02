"""AI-assisted, explicitly approved single grouped-bridge measurement."""
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
import full_map_pilot6 as full_map
import new_row_bridge6 as bridge
from provenance import digest_entries, source_identity
from run_job import atomic_json, run_job, utc
from study6 import Ledger


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'results/grouped-bridge6-20261018-plan.json'
APPROVAL = ROOT / 'results/grouped-bridge6-20261018-authorization.json'
OUT = ROOT / 'results/grouped-bridge6-20261018'
CHECK = OUT / 'check'
LABEL = 'grouped-bridge6-20261018'
UNIT = 'othello6-grouped-bridge6-20261018.service'
GIB = 2**30
MIB = 2**20


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def approved():
    spec = json.loads(PLAN.read_text())
    consent = json.loads(APPROVAL.read_text())
    require(consent.get('approved') is True and consent.get('answer') == 'do il consenso',
            'explicit grouping-test consent required')
    require(consent['plan_sha256'] == sha(PLAN)
            and consent['worker_sha256'] == sha(__file__), 'reviewed plan or worker changed')
    require(spec['parts'] == [380, 17924] and spec['fresh_output'] == str(OUT),
            'reviewed two-part scope required')
    limits = spec['resource_proposal']
    require(limits['total_cpu_max_seconds_including_preparation_and_supervision'] == 240
            and limits['hard_memory_gib'] == 12 and limits['swap_bytes'] == 0
            and limits['ordinary_free_disk_floor_gib'] == 80
            and limits['new_artifact_max_mib'] == 64
            and limits['existing_study_artifact_cap_gib'] == 12
            and not limits['additional_budget_requested'], 'exact approved limits required')
    return spec, consent


def allocated(path):
    if not path.exists():
        return 0
    return int(subprocess.check_output(['du', '-s', '-B1', str(path)], text=True).split()[0])


def storage(reserve=0):
    new = allocated(OUT)
    used = allocated(full_map.BASE) + new
    free = shutil.disk_usage(ROOT).free
    require(new + reserve <= 64*MIB and used + reserve < 12*GIB
            and free - reserve >= 80*GIB, '80GiB disk floor or artifact cap reached')
    return dict(new_artifact_bytes=new, allocated_study_bytes=used, free_bytes=free,
                reserved_bytes=reserve, free_floor_bytes=80*GIB, checked_utc=utc())


def cgroup():
    groups = [line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
              if line.startswith('0::')]
    require(len(groups) == 1, 'one cgroup required')
    group = Path('/sys/fs/cgroup') / groups[0].lstrip('/')
    require((group/'memory.max').read_text().strip() == str(12*GIB)
            and (group/'memory.swap.max').read_text().strip() == '0',
            'hard12GiB/no-swap cgroup required')
    return group


def group_usage(group):
    values = dict(line.split() for line in (group/'cpu.stat').read_text().splitlines())
    return dict(cpu_seconds=int(values['usage_usec'])/1e6,
                memory_peak_bytes=int((group/'memory.peak').read_text()),
                swap_peak_bytes=int((group/'memory.swap.peak').read_text()))


@contextlib.contextmanager
def watched(group):
    stop = threading.Event()
    failures = []

    def watch():
        while not stop.wait(2):
            try:
                require(group_usage(group)['cpu_seconds'] < 210, '210CPU service stop reached')
                atomic_json(OUT/'storage.json', storage(4*MIB))
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
    require(not failures, 'resource watcher stopped the single experiment')


def prepare(spec):
    require(not OUT.exists() and not any(path.is_symlink() for path in (OUT, *OUT.parents)),
            'fresh output required; no automatic retry')
    storage(64*MIB)
    baseline = Path(spec['accepted_run'])
    files = {}
    for name, expected in spec['copied_bridge_sources'].items():
        source = baseline/name
        require(sha(source) == expected, 'accepted bridge source changed')
        relative = 'src/' + name.split('/src/', 1)[1]
        files[relative] = source.read_bytes()
    files['othello.agda-lib'] = (ROOT/'othello.agda-lib').read_bytes()
    target = 'src/' + spec['root_module'].replace('.', '/') + '.agda'
    files[target] = spec['root_source'].encode()
    CHECK.mkdir(parents=True)
    for name, raw in files.items():
        destination = CHECK/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    atomic_json(OUT/'prepared.json', dict(files={name: hashlib.sha256(raw).hexdigest()
                                               for name, raw in files.items()},
                                        source=source_identity(CHECK), prepared_utc=utc()))


def expected_donors(spec):
    baseline = json.loads((ROOT/spec['baseline_receipt']).read_text())
    phases = {phase['label']: phase for phase in baseline['phases']}
    expected = {}
    for part in spec['parts']:
        phase = phases['rows-' + str(part)]
        path = Path(spec['accepted_run'])/'prepared/parts'/str(part)/'rows'
        expected[path] = (phase['record']['source_sha256'], phase['interface_pool_sha256'])
    expected[bridge.FULL] = (bridge.FULL_SOURCE_SHA, bridge.FULL_POOL_SHA)
    expected[bridge.ALIGNED] = (bridge.ALIGNED_SOURCE, bridge.ALIGNED_POOL)
    expected[full_map.DONOR] = (full_map.DONOR_SOURCE_SHA, full_map.DONOR_POOL_SHA)
    require(set(map(str, expected)) == set(spec['read_only_dependency_roots']),
            'exact accepted dependency roots required')
    return expected


def donor_snapshot(expected):
    snapshot = {}
    for path, (source_sha, pool_sha) in expected.items():
        identity = source_identity(path)
        pool = assembly6.interfaces(path)
        require(identity['source_sha256'] == source_sha and digest_entries(pool) == pool_sha,
                'accepted same-machine source or interface pool changed: ' + str(path))
        snapshot[str(path)] = dict(source=identity, interface_count=len(pool),
                                   interface_pool_sha256=digest_entries(pool))
    return snapshot


def worker():
    spec, consent = approved()
    group = cgroup()
    report = dict(format='othello-grouped-bridge6-report-v1', accepted=False,
                  created_utc=utc(), approval=consent, plan_sha256=sha(PLAN),
                  root_is_import_only=True, new_distinct_game_rows=0,
                  initial_problem2_proved=False, optimal_initial_pair_proved=False,
                  production_authorized=False, controlled_speedup_claim=False)
    atomic_json(OUT/'report.json', report)
    expected = expected_donors(spec)
    with contextlib.ExitStack() as stack, watched(group):
        for donor in sorted(expected):
            lock = stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = donor_snapshot(expected)
        require(sha(spec['checker_binary']) == spec['checker_binary_sha256'],
                'pinned Agda binary changed')
        require(not assembly6.interfaces(CHECK), 'owned target must start cold')
        source = source_identity(CHECK)
        source_pin = json.loads((OUT/'prepared.json').read_text())['source']
        require(source == source_pin, 'prepared source changed')
        history = json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        p1 = history['p1_files']
        require(all(sha(ROOT/name) == expected_sha for name, expected_sha in p1.items()),
                'P1 source changed')
        require(sha(ROOT/spec['accepted_checkpoint']) == spec['accepted_checkpoint_sha256'],
                'accepted checkpoint changed')
        argv = ['/usr/bin/bwrap', '--ro-bind', '/', '/', '--bind', str(CHECK), str(CHECK),
                '--proc', '/proc', '--dev-bind', '/dev', '/dev', '--tmpfs', '/tmp',
                '--die-with-parent', '--', spec['checker_binary'], '--no-libraries', '-i', 'src']
        for donor in spec['read_only_dependency_roots']:
            argv += ['-i', str(Path(donor)/'src')]
        argv += spec['agda_flags'][1:] + ['src/' + spec['root_module'].replace('.', '/') + '.agda']
        argv += spec['rts_flags']
        record = run_job('grouped-agda', argv, OUT/'records', root=CHECK,
                         timeout=480, cpu_limit=140, rss_limit_gib=11.5, log_limit_mib=4,
                         expected_source_sha256=source['source_sha256'],
                         metadata=dict(checker_binary_sha256=spec['checker_binary_sha256'],
                                       own_target_cold=True, native_search_allowed=False,
                                       production_authorized=False))
        checked = re.findall(r'(?m)^\s*Checking (\S+) \(', (OUT/'records/grouped-agda.log').read_text())
        modules = {name.split('/src/', 1)[1][:-5].replace('/', '.')
                   for name in spec['copied_bridge_sources']} | {spec['root_module']}
        pool = assembly6.interfaces(CHECK)
        after = donor_snapshot(expected)
        intact = before == after and all(sha(ROOT/name) == expected_sha for name, expected_sha in p1.items())
        intact = intact and sha(ROOT/spec['accepted_checkpoint']) == spec['accepted_checkpoint_sha256']
        accepted = bool(record['accepted'] and intact and set(checked) == modules
                        and len(checked) == len(modules) == len(pool) == 8)
        report.update(accepted=accepted, record=record, donor_snapshots=after,
                      accepted_donors_and_p1_unchanged=intact, checked_modules=checked,
                      expected_modules=sorted(modules), new_interfaces=len(pool),
                      interface_pool_sha256=digest_entries(pool), storage=storage(),
                      baseline_serial_cpu_seconds=spec['baseline_serial_bridge_cpu_seconds']['sum'],
                      historical_cpu_difference_seconds=spec['baseline_serial_bridge_cpu_seconds']['sum']-record['cpu_seconds'],
                      cgroup=group_usage(group), finished_utc=utc())
        atomic_json(OUT/'report.json', report)
        require(accepted, 'single grouping measurement failed; no retry authorized')


def supervise():
    spec, consent = approved()
    cgroup()
    job = json.loads((OUT/'job.json').read_text())
    require(not (OUT/'records'/ (LABEL+'.json')).exists(), 'outer receipt already exists')
    prepared = json.loads((OUT/'prepared.json').read_text())
    record = run_job(LABEL, ['/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'worker'],
                     OUT/'records', root=CHECK, timeout=560, cpu_limit=190,
                     rss_limit_gib=11.75, log_limit_mib=4,
                     reservation_id=job['reservation']['reservation_id'],
                     expected_source_sha256=prepared['source']['source_sha256'],
                     metadata=dict(scope_approval=consent, grouped_bridge_only=True,
                                   native_search_allowed=False, production_authorized=False))
    atomic_json(OUT/'service-accounting.json', group_usage(cgroup()))
    print(json.dumps(dict(accepted=record['accepted'], cpu_seconds=record['cpu_seconds'],
                          exit_code=record['exit_code'])), flush=True)
    return 0 if record['accepted'] else 1


def launch():
    spec, consent = approved()
    require(not OUT.exists(), 'existing run must never be restarted')
    active = subprocess.check_output(['systemctl', '--user', 'list-units', '--state=activating,running',
                                      '--type=service', '--no-legend', '--plain', 'othello*'], text=True)
    require(not active.strip(), 'another Othello service is active')
    processes = subprocess.check_output(['ps', '-eo', 'comm='], text=True).splitlines()
    require(not any(name.strip().lower() == 'agda' for name in processes), 'Agda already active')
    ledger = Ledger(ROOT/'results/study6-ledger.json')
    status = Ledger.summary(json.loads(ledger.path.read_text()))
    require(status['coordinator_host'] == 'eapiova' and not status['outstanding'],
            'canonical ledger must have no outstanding jobs')
    stage_used = status['charged_cpu_seconds'] - 90524.756808 + status['withheld_cpu_seconds'] - 324
    require(0 <= stage_used and stage_used + 240 < 3600, 'existing full-map stage budget exhausted')
    prepare(spec)
    control = ledger.withhold('assembly', 20,
        'Approved grouped bridge18Oct: conservative unmeasured preparation and outer supervisor allowance; within240CPU scope, not measured kernel CPU and not a budget grant.')
    reservation = ledger.reserve('kernel', 220, LABEL)
    args = ['systemd-run', '--user', '--no-block', '--unit=' + UNIT,
            '--property=MemoryMax=12G', '--property=MemorySwapMax=0',
            '--property=CPUQuota=100%', '--property=TasksMax=256',
            '--property=KillMode=control-group', '--property=RuntimeMaxSec=600',
            '--property=TimeoutStopSec=10', '--property=Environment=PYTHONDONTWRITEBYTECODE=1',
            '--property=Environment=GIT_OPTIONAL_LOCKS=0', '--property=WorkingDirectory=' + str(CHECK),
            '--property=StandardOutput=append:' + str(OUT/'service.log'),
            '--property=StandardError=append:' + str(OUT/'service.log'),
            '/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'supervise']
    job = dict(format='othello-grouped-bridge6-job-v1', unit=UNIT, label=LABEL,
               reservation=reservation, control_allowance=control, approval=consent,
               created_utc=utc(), state='dispatching', systemd_command=args)
    atomic_json(OUT/'job.json', job)
    result = subprocess.run(args, capture_output=True, text=True)
    job.update(state='submitted' if result.returncode == 0 else 'dispatch-failed',
               dispatch_exit_code=result.returncode, dispatch_stdout=result.stdout,
               dispatch_stderr=result.stderr, submitted_utc=utc())
    atomic_json(OUT/'job.json', job)
    print(json.dumps(job), flush=True)
    require(result.returncode == 0, 'dispatch failed; do not retry or release without evidence')


if __name__ == '__main__':
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    require(len(sys.argv) == 2 and sys.argv[1] in ('launch', 'supervise', 'worker'),
            'explicit launch, supervise or worker command required')
    if sys.argv[1] == 'launch':
        launch()
    elif sys.argv[1] == 'supervise':
        raise SystemExit(supervise())
    else:
        worker()
