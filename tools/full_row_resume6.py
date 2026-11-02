"""Bounded second-stage resume of the unchanged safe row checker.

AI-assisted recovery controller.  The original controller, plan, forecast and
failed outer receipt remain immutable.  Only the effective storage envelopes,
finite stage caps and JSON whitespace of the mutable progress index change.
No accepted batch is submitted again.  This is not a Problem2 checker.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import resource
import shutil
import subprocess
import sys

ROOT = Path('/home/eapiova/projects/othello-agda-main')
sys.path.insert(0, str(ROOT/'tools'))
import full_row_production6 as production
from provenance import source_identity
from run_job import atomic_json, run_job, utc
from study6 import Ledger

OUT = production.OUT
CONTROL = OUT/'control-production-0002'
ORIGINAL_PLAN = OUT/'plan.json'
PLAN = OUT/'resume-plan-production-0002.json'
RUN_ID = 'production-0002'
CONTROLLER = ROOT/'tools/full_row_resume6.py'
AUTH = ROOT/'results/full-row-resume-authorization6-20261019.json'
ORIGINAL_READ = production.read_json
ORIGINAL_VALIDATE = production.validate_plan
ORIGINAL_DURABLE = production.durable_json
require = production.require
sha = production.sha


def read_json(path):
    # The reused worker's single hard-coded active-plan read is redirected;
    # the historical original plan is neither edited nor replaced.
    return ORIGINAL_READ(PLAN if Path(path) == ORIGINAL_PLAN else path)


def compact_durable(path, data):
    if Path(path) != production.PROGRESS:
        return ORIGINAL_DURABLE(path, data)
    raw = (json.dumps(data, separators=(',', ':'))+'\n').encode()
    require(json.loads(raw) == data, 'compact progress serialization changed data')
    production.records.atomic_bytes(Path(path), raw, mode=0o600)


def expected_effective_plan(original, resume, authorization):
    result = copy.deepcopy(original)
    result['authorization_path'] = str(AUTH)
    result['authorization_sha256'] = sha(AUTH)
    result['authorization'] = authorization
    result['run'] = {'run_id': RUN_ID,
        'reservation_cpu_seconds': authorization['reservation_cpu_seconds'],
        'outer_cpu_cap_seconds': authorization['outer_cpu_cap_seconds']}
    result['forecast']['storage'].update(resume['storage_overrides'])
    result['resume'] = resume
    return result


def validate_plan(plan):
    resume = plan['resume']
    require(resume['original_plan_sha256'] == sha(ORIGINAL_PLAN)
            and resume['controller_sha256'] == sha(CONTROLLER),
            'original plan or recovery controller changed')
    original = ORIGINAL_READ(ORIGINAL_PLAN)
    auth = ORIGINAL_READ(AUTH)
    require(plan == expected_effective_plan(original, resume, auth),
            'effective plan differs outside the explicit resume overrides')
    require(resume['original_failed_report_sha256'] == sha(OUT/'report-production-0001.json')
            and resume['original_outer_record_sha256'] == sha(OUT/'outer-records/production-0001.json')
            and resume['reconciliation_sha256'] == sha(resume['reconciliation']),
            'failed stage evidence or its reconciliation changed')
    require(resume['history_sha256'] == sha(resume['history']),
            'pre-resume mutable metadata snapshot changed')
    require(resume['preaccepted_batches'] == 484
            and resume['remaining_batches'] == 183
            and resume['remaining_groups'] == {'upper': 0, 'lower': 366},
            'reviewed recovery scope changed')
    progress = ORIGINAL_READ(production.PROGRESS)
    accepted_prefix = progress['accepted_batches'][:484]
    prefix_pin = hashlib.sha256(json.dumps(accepted_prefix, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()
    require(prefix_pin == resume['accepted_prefix_sha256'],
            'previously accepted proof records changed')
    ORIGINAL_VALIDATE(plan)


def install():
    production.read_json = read_json
    production.validate_plan = validate_plan
    production.durable_json = compact_durable


def annotate_report():
    report_path = OUT/('report-'+RUN_ID+'.json')
    if not report_path.exists():
        return
    report = ORIGINAL_READ(report_path)
    require(report['run_id'] == RUN_ID, 'resume terminal report id changed')
    report.update(effective_plan=str(PLAN), effective_plan_sha256=sha(PLAN),
        original_plan=str(ORIGINAL_PLAN), original_plan_sha256=sha(ORIGINAL_PLAN),
        resumed_after_failed_run='production-0001',
        original_failed_stage_reconciliation=str(
            ROOT/'results/full-row-production-reconciliation6-20261019.json'))
    atomic_json(report_path, report)
    atomic_json(OUT/'report.json', report)


def worker():
    install()
    try:
        production.worker(RUN_ID)
    finally:
        annotate_report()


def supervise():
    job = ORIGINAL_READ(OUT/('job-'+RUN_ID+'.json'))
    require(job['effective_plan_sha256'] == sha(PLAN)
            and job['controller_sha256'] == sha(CONTROLLER),
            'dispatched plan or controller changed')
    result = run_job(RUN_ID, ['/usr/bin/python3', '-B', str(CONTROLLER), 'worker'],
        OUT/'outer-records', root=CONTROL,
        timeout=job['outer_wall_limit_seconds'], cpu_limit=job['outer_cpu_cap_seconds'],
        rss_limit_gib=11.7, log_limit_mib=.5,
        reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'],
        metadata={'manual_ledger_finish_required': True,
            'full_row_production_run_id': RUN_ID,
            'effective_plan_sha256': job['effective_plan_sha256']})
    usage = resource.getrusage(resource.RUSAGE_SELF)
    atomic_json(OUT/('supervisor-cpu-'+RUN_ID+'.json'), {
        'finished_utc': utc(), 'self_cpu_seconds': usage.ru_utime+usage.ru_stime,
        'whole_service_cpu_requires_terminal_systemd_CPUUsageNSec': True,
        'nested_receipts_must_not_be_charged_again': True})
    return 0 if result['accepted'] else 1


def launch():
    require(not (OUT/('job-'+RUN_ID+'.json')).exists(), 'resume was already dispatched')
    auth = ORIGINAL_READ(AUTH)
    require(auth['approved'] is True and auth['resume'] is True
            and auth['total_cpu_seconds'] == 172800
            and auth['output'] == str(OUT)
            and auth['reservation_cpu_seconds'] == 16000
            and auth['outer_cpu_cap_seconds'] == 15700
            and auth['child_cpu_limit_seconds'] == production.CHILD_CPU
            and auth['child_wall_limit_seconds'] == production.CHILD_WALL
            and auth['runtime_max_seconds'] == production.RUNTIME_MAX
            and auth['hard_memory_gib'] == 12 and auth['swap_bytes'] == 0
            and auth['ordinary_free_disk_floor_gib'] == 80,
            'explicit unchanged-limit finite recovery authorization differs')
    require(auth['ledger_sha256_before_reservation'] == sha(production.LEDGER_FILE),
            'ledger changed after the applied recovery authorization')
    production.batch.authorized()
    require(not production.common.disjoint_checkers(), 'another Othello checker is active')
    services = subprocess.check_output(['systemctl', '--user', 'list-units',
        '--state=activating,running', '--type=service', '--no-legend', '--plain',
        'othello*'], text=True)
    require(not services.strip(), 'an Othello service is active')
    state = ORIGINAL_READ(production.LEDGER_FILE)
    summary = Ledger.summary(state)
    require(summary['total_cpu_seconds'] == 172800 and not summary['outstanding']
            and summary['categories']['kernel']['available_cpu_seconds'] >= 16000,
            'unchanged ledger cannot cover this finite recovery')
    plan = ORIGINAL_READ(PLAN)
    validate_plan(plan)
    require(not production.TRANSACTION.exists()
            and not ORIGINAL_READ(production.PROGRESS)['pending_record_batches'],
            'reviewed clean post-batch recovery state changed')
    pre = plan['resume']['row_archives_before']
    require(all(sha(production.ROW_ZIP[s]) == pre[s] for s in production.SIDES)
            and sha(production.RECORD_ZIP) == plan['resume']['records_archive_before_sha256']
            and sha(production.LINEAGE) == plan['resume']['lineage_before_sha256'],
            'accepted payload archives changed before dispatch')
    production.component_storage(plan, reserve=4*production.MIB)
    CONTROL.mkdir()
    shutil.copy2(CONTROLLER, CONTROL/'resume-controller.py')
    identity = source_identity(CONTROL)
    reservation = Ledger(production.LEDGER_FILE).reserve('kernel', 16000, RUN_ID)
    unit = 'othello6-'+OUT.name+'-'+RUN_ID+'.service'
    job = {'format': 'othello-full-row-production-job-v1', 'created_utc': utc(),
        'action': 'reviewed-resume', 'run_id': RUN_ID, 'reservation': reservation,
        'outer_cpu_cap_seconds': 15700, 'outer_wall_limit_seconds': production.RUNTIME_MAX-30,
        'control_source': identity, 'unit': unit, 'manual_ledger_finish_required': True,
        'effective_plan': str(PLAN), 'effective_plan_sha256': sha(PLAN),
        'controller_sha256': sha(CONTROLLER)}
    ORIGINAL_DURABLE(OUT/('job-'+RUN_ID+'.json'), job)
    argv = ['systemd-run', '--user', '--no-block', '--unit='+unit,
        '--property=MemoryMax=12G', '--property=MemorySwapMax=0', '--property=LimitCORE=0',
        '--property=CPUAccounting=yes', '--property=CPUQuota=100%',
        '--property=TasksMax=128', '--property=KillMode=control-group',
        '--property=RuntimeMaxSec='+str(production.RUNTIME_MAX),
        '--property=WorkingDirectory='+str(CONTROL),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3', '-B', str(CONTROLLER), 'supervise']
    done = subprocess.run(argv, capture_output=True, text=True)
    atomic_json(OUT/('dispatch-'+RUN_ID+'.json'), {'argv': argv,
        'exit_code': done.returncode, 'stdout': done.stdout, 'stderr': done.stderr})
    require(done.returncode == 0, 'dispatch failed; preserve and reconcile the reservation')
    print(json.dumps({'unit': unit, 'reservation': reservation,
        'remaining_batches': 183, 'Problem2_checked': False}))


def main():
    require(len(sys.argv) == 2, 'exactly one action required')
    if sys.argv[1] == 'worker':
        worker(); return 0
    if sys.argv[1] == 'supervise':
        return supervise()
    require(sys.argv[1] == 'launch', 'action must be launch, worker, or supervise')
    launch(); return 0


if __name__ == '__main__':
    raise SystemExit(main())
