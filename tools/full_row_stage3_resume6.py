"""AI-assisted bounded recovery with serialized resource-state writes.

Both historical controllers and plans remain byte-exact.  The production
checker is unchanged.  This controller serializes component_storage across
the worker and its watcher, preventing their same-PID JSON temporary-file
collision, and retains a full traceback for any subsequent batch failure.
"""
from __future__ import annotations

import functools
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import traceback

ROOT = Path('/home/eapiova/projects/othello-agda-main')
sys.path.insert(0, str(ROOT/'tools'))
import full_row_resume6 as previous
from provenance import source_identity
from run_job import atomic_json, utc
from study6 import Ledger

p = previous.production
OUT = p.OUT
RUN_ID = 'production-0003'
CONTROL = OUT/'control-production-0003'
PLAN = OUT/'resume-plan-production-0003.json'
AUTH = ROOT/'results/full-row-stage3-authorization6-20261019.json'
CONTROLLER = ROOT/'tools/full_row_stage3_resume6.py'
READ = previous.ORIGINAL_READ
RESERVE = 13500
OUTER_CPU = 13200
require, sha = p.require, p.sha
ORIGINAL_STORAGE = p.component_storage
ORIGINAL_BATCH = p.run_batch


def serialized(function):
    """Hold one process-local lock across the complete shared operation."""
    lock = threading.RLock()
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        with lock:
            return function(*args, **kwargs)
    return wrapped


def validate_plan(plan):
    resume = plan['resume']
    require(sha(previous.ORIGINAL_PLAN) == resume['original_plan_sha256']
            and sha(CONTROLLER) == resume['controller_sha256'],
            'original plan or third-stage controller changed')
    require(all(sha(ROOT/'tools'/name) == pin for name, pin in resume['helper_sha256'].items()),
            'historical resume helper changed')
    require(sha(resume['previous_effective_plan']) == resume['previous_effective_plan_sha256']
            and sha(resume['history']) == resume['history_sha256'],
            'prior effective plan or closed metadata snapshot changed')
    auth = READ(AUTH)
    expected = previous.expected_effective_plan(READ(previous.ORIGINAL_PLAN), resume, auth)
    require(plan == expected, 'effective plan differs outside explicit stage overrides')
    require(resume['preaccepted_batches'] == 516
            and resume['remaining_batches'] == 151
            and resume['remaining_groups'] == {'upper': 0, 'lower': 302},
            'reviewed third-stage scope changed')
    prior = resume['prior_stages']
    require([item['run_id'] for item in prior] == ['production-0001', 'production-0002'],
            'both earlier failed stages must remain in the proof/accounting lineage')
    state = READ(p.LEDGER_FILE)
    for item in prior:
        require(all(sha(item[key]) == item[key+'_sha256']
                    for key in ('report', 'outer_record', 'reconciliation')),
                'prior stage receipt changed')
        rec = READ(item['reconciliation'])
        identifier = rec['reservation_id']
        require(rec['status'] == 'reconciled'
                and identifier not in state['reservations']
                and state['finished'][identifier] == rec['finished'],
                'prior stage accounting is not closed exactly once')
    progress = READ(p.PROGRESS)
    prefix = progress['accepted_batches'][:516]
    require(hashlib.sha256(json.dumps(prefix, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest() == resume['accepted_prefix_sha256'],
        'accepted proof prefix changed')
    previous.ORIGINAL_VALIDATE(plan)


def capture_batch(*args, **kwargs):
    try:
        return ORIGINAL_BATCH(*args, **kwargs)
    except BaseException as error:
        atomic_json(OUT/('batch-exception-'+RUN_ID+'.json'), {
            'recorded_utc': utc(), 'exception': repr(error),
            'filename': getattr(error, 'filename', None),
            'traceback': traceback.format_exc(), 'Problem2_checked': False})
        raise


def annotate_report():
    path = OUT/('report-'+RUN_ID+'.json')
    if not path.exists():
        return
    report = READ(path); plan = READ(PLAN)
    require(report['run_id'] == RUN_ID, 'third-stage terminal report id differs')
    report.update(effective_plan=str(PLAN), effective_plan_sha256=sha(PLAN),
        original_plan=str(previous.ORIGINAL_PLAN),
        original_plan_sha256=sha(previous.ORIGINAL_PLAN),
        resumed_after_failed_run='production-0002',
        prior_stages=plan['resume']['prior_stages'],
        terminal_reconciliation=plan['resume']['terminal_reconciliation_path'],
        serialized_resource_state_writes=True)
    atomic_json(path, report); atomic_json(OUT/'report.json', report)


def install():
    previous.production.read_json = previous.read_json
    previous.production.validate_plan = validate_plan
    previous.production.durable_json = previous.compact_durable
    previous.production.component_storage = serialized(ORIGINAL_STORAGE)
    previous.production.run_batch = capture_batch


def configure():
    # Reuse only the already-reviewed worker/supervisor scaffolding. The old
    # module's source and its historical control directory remain unchanged.
    for name, value in {'RUN_ID': RUN_ID, 'CONTROL': CONTROL, 'PLAN': PLAN,
            'AUTH': AUTH, 'CONTROLLER': CONTROLLER}.items():
        setattr(previous, name, value)
    previous.validate_plan = validate_plan
    previous.install = install
    previous.annotate_report = annotate_report


def launch():
    configure()
    require(not (OUT/('job-'+RUN_ID+'.json')).exists() and not CONTROL.exists(),
            'third-stage dispatch or source root already exists')
    auth = READ(AUTH)
    require(auth['approved'] is True and auth['resume'] is True
            and auth['total_cpu_seconds'] == 172800 and auth['output'] == str(OUT)
            and auth['reservation_cpu_seconds'] == RESERVE
            and auth['outer_cpu_cap_seconds'] == OUTER_CPU
            and auth['child_cpu_limit_seconds'] == 160
            and auth['child_wall_limit_seconds'] == 400
            and auth['runtime_max_seconds'] == p.RUNTIME_MAX
            and auth['hard_memory_gib'] == 12 and auth['swap_bytes'] == 0
            and auth['core_bytes'] == 0 and auth['ordinary_free_disk_floor_gib'] == 80,
            'finite third-stage authorization or unchanged safeguards differ')
    require(sha(p.LEDGER_FILE) == auth['ledger_sha256_before_reservation'],
            'ledger changed after authorization was frozen')
    p.batch.authorized()
    require(not p.common.disjoint_checkers(), 'another Othello checker is active')
    services = subprocess.check_output(['systemctl', '--user', 'list-units',
        '--state=activating,running', '--type=service', '--no-legend', '--plain',
        'othello*'], text=True)
    require(not services.strip(), 'an Othello service is active')
    summary = Ledger.summary(READ(p.LEDGER_FILE))
    require(summary['total_cpu_seconds'] == 172800 and not summary['outstanding']
            and summary['categories']['kernel']['available_cpu_seconds'] >= RESERVE,
            'remaining kernel budget cannot cover the finite third stage')
    plan = READ(PLAN); validate_plan(plan)
    require(not p.TRANSACTION.exists() and not READ(p.PROGRESS)['pending_record_batches'],
            'clean closed-batch recovery state differs')
    resume = plan['resume']
    require(all(sha(p.ROW_ZIP[s]) == resume['row_archives_before'][s] for s in p.SIDES)
            and sha(p.RECORD_ZIP) == resume['records_archive_before_sha256']
            and sha(p.LINEAGE) == resume['lineage_before_sha256'],
            'accepted proof archives changed before dispatch')
    ORIGINAL_STORAGE(plan, reserve=4*p.MIB)
    CONTROL.mkdir(); shutil.copy2(CONTROLLER, CONTROL/'controller.py')
    shutil.copy2(ROOT/'tools/full_row_resume6.py', CONTROL/'historical-resume-helper.py')
    identity = source_identity(CONTROL)
    reservation = Ledger(p.LEDGER_FILE).reserve('kernel', RESERVE, RUN_ID)
    unit = 'othello6-'+OUT.name+'-'+RUN_ID+'.service'
    job = {'format': 'othello-full-row-production-job-v1', 'created_utc': utc(),
        'action': 'serialized-resource-state-resume', 'run_id': RUN_ID,
        'reservation': reservation, 'outer_cpu_cap_seconds': OUTER_CPU,
        'outer_wall_limit_seconds': p.RUNTIME_MAX-30, 'control_source': identity,
        'unit': unit, 'manual_ledger_finish_required': True,
        'effective_plan': str(PLAN), 'effective_plan_sha256': sha(PLAN),
        'controller_sha256': sha(CONTROLLER)}
    previous.ORIGINAL_DURABLE(OUT/('job-'+RUN_ID+'.json'), job)
    argv = ['systemd-run', '--user', '--no-block', '--unit='+unit,
        '--property=MemoryMax=12G', '--property=MemorySwapMax=0', '--property=LimitCORE=0',
        '--property=CPUAccounting=yes', '--property=CPUQuota=100%', '--property=TasksMax=128',
        '--property=KillMode=control-group', '--property=RuntimeMaxSec='+str(p.RUNTIME_MAX),
        '--property=WorkingDirectory='+str(CONTROL),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3', '-B', str(CONTROLLER), 'supervise']
    done = subprocess.run(argv, capture_output=True, text=True)
    atomic_json(OUT/('dispatch-'+RUN_ID+'.json'), {'argv': argv,
        'exit_code': done.returncode, 'stdout': done.stdout, 'stderr': done.stderr})
    require(done.returncode == 0, 'third-stage dispatch failed; reservation remains outstanding')
    print(json.dumps({'unit': unit, 'reservation': reservation,
        'remaining_batches': 151, 'Problem2_checked': False}))


def main():
    require(len(sys.argv) == 2, 'exactly one action required')
    configure()
    if sys.argv[1] == 'worker':
        previous.worker(); return 0
    if sys.argv[1] == 'supervise':
        return previous.supervise()
    require(sys.argv[1] == 'launch', 'action must be launch, worker, or supervise')
    launch(); return 0


if __name__ == '__main__':
    raise SystemExit(main())
