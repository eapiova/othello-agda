"""Final bounded safe Agda check of the prepared 6x6 Problem2 theorem.

AI-assisted controller.  Launch requires a parent-supplied finite stage
authorization, an accepted and manually reconciled full-row production run,
and a registered output root.  The outer study6 reservation is deliberately
left for manual reconciliation from its terminal run_job record.

This controller never rebuilds Boolean Rows proofs.  It mounts the complete
Rows interface archives read-only, checks both AllParts modules, Result, and a
small Problem2 wrapper with --no-write-interfaces, then audits the exact 4,128
selected sources.  It has no automatic retry or resume action.
"""
from __future__ import annotations

import contextlib
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import sys
import threading
import traceback
import time
import zipfile

ROOT = Path('/home/eapiova/projects/othello-agda-main')
if str(ROOT/'tools') not in sys.path:
    sys.path.append(str(ROOT/'tools'))

from compression import zstd

import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
import problem2_source_audit6 as source_audit
from provenance import digest_entries, source_identity
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger
from study_archive6 import verify_view

BASE = Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
PRODUCTION = BASE/'full-row-production6-20261018'
OUT = BASE/'final-problem2-compacting6-20261019'
PREVIOUS_FINAL = BASE/'final-problem2-recovery6-20261019'
FIRST_FINAL = BASE/'final-problem2-check6-20261018'
CONTROL = OUT/'control'
CHECK = OUT/'check'
PROOF = OUT/'proof'
RECORDS = OUT/'records'
OUTER_RECORDS = OUT/'outer-records'
PRIVATE = BASE/'private-core-package6-20261018'
PRIVATE_MANIFEST = PRIVATE/'manifest.json'
PRODUCTION_PLAN = PRODUCTION/'plan.json'
COMPLETE_ROWS = PRODUCTION/'complete-row-cache-manifest.json'
LINEAGE = PRODUCTION/'row-interface-payload-lineage.json.zst'
REGISTRY_FILE = ROOT/'results/study6-external-artifacts-20261018.json'
LEDGER_FILE = ROOT/'results/study6-ledger.json'
SIDES = ('upper', 'lower')
PREFIX = {'upper': 'Tests.CompleteUpperRows6', 'lower': 'Tests.CompleteLowerRows6'}
EXPECTED_ROWS = {'upper': 651, 'lower': 686}
EXPECTED_SCHEDULED = {'upper': 649, 'lower': 684}
ORIGINAL_OWNED = {'upper': {6, 500, 652}, 'lower': {6, 686}}
PILOTS = {100, 300}
GIB = 2**30
MIB = 2**20
MAX_RESERVATION_CPU = 2500
MAX_OUTER_CPU = 2400
MAX_CHILD_CPU = 2200
MAX_WALL = 7200
STOP_RESERVE = 4*MIB
HARD_GIB = 12
ASSEMBLY_ALLOWANCE = 10
WRAPPER_RELATIVE = 'src/Tests/FinalProblem2Check6.agda'
WRAPPER_MODULE = 'Tests.FinalProblem2Check6'
WRAPPER = '''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted final safe checker wrapper.
module Tests.FinalProblem2Check6 where
open import Othello.Statements using (Problem2)
import Tests.CompleteUpperRows6.Result as Result

initial6x6 : Problem2
initial6x6 = Result.initial6x6
'''
FLAGS = ['--no-libraries', '--safe', '--without-K', '--cubical-compatible',
         '--save-metas', '--no-write-interfaces', '--profile=modules']
HELPERS = ['final_problem2_compacting6.py', 'problem2_source_audit6.py', 'assembly6.py',
           'citation_diagnostic6.py', 'completion_batch6.py',
           'grouped_bridge_pilot6.py', 'provenance.py', 'run_job.py',
           'study6.py', 'study_archive6.py', 'study_row_archive_fs6.c']

# Reproduce the canonical pre-production census, then add the frozen/current
# external registry roots with du -x.  FUSE view contents are never charged as
# retained physical bytes.
common.OUT, common.HARD_GIB, common.RESERVATION_CPU = OUT, HARD_GIB, 0


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(MIB), b''):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def allocated(path):
    path = Path(path)
    return 0 if not path.exists() else int(subprocess.check_output(
        ['du', '-s', '-x', '-B1', str(path)], text=True).split()[0])


def helper_hashes(base=ROOT/'tools'):
    return {name: sha(Path(base)/name) for name in HELPERS}


def verified_row_view(config):
    manifest_path = Path(config['manifest'])
    closure_path = Path(config['closure'])
    rec_path = Path(config['reconciliation'])
    require(sha(manifest_path) == config['manifest_sha256']
            and sha(closure_path) == config['closure_sha256']
            and sha(rec_path) == config['reconciliation_sha256'],
            'row-view diagnostic evidence changed')
    manifest, closure, rec = map(read_json, (manifest_path, closure_path, rec_path))
    require(closure['accepted'] and not closure['Agda_dispatched']
            and closure['original_archives_unchanged']
            and rec['status'] == 'reconciled' and rec['all_two_views_unmounted'],
            'accepted, reconciled row-view metadata diagnostic is required')
    require(config['binary'] == manifest['binary'] == closure['binary']
            and sha(config['binary']) == config['binary_sha256'] == closure['binary_sha256']
            and sha(manifest['source']) == manifest['source_sha256'] == closure['source_sha256']
            and Path(manifest['source']) == ROOT/'tools/study_row_archive_fs6.c'
            and manifest['metadata'] == config['metadata']
            and Path(manifest['lineage']) == LINEAGE
            and sha(LINEAGE) == manifest['lineage_sha256'],
            'row-view source, binary, metadata, or lineage changed')
    state = read_json(LEDGER_FILE)
    require(state['finished'].get(rec['reservation_id']) == rec['finished']
            and rec['whole_service_cpu_seconds_exact'] <= rec['total_stage_accounted_cpu_seconds']
                <= rec['stage_envelope_cpu_seconds'], 'row-view diagnostic accounting differs')
    residual = dict(rec.get('residual_withholding') or {})
    if residual:
        identifier = residual.pop('withholding_id')
        require(state.get('withheld', {}).get(identifier) == residual,
                'row-view diagnostic residual charge missing')
    lineage = json.loads(zstd.decompress(LINEAGE.read_bytes()))
    for side in SIDES:
        item = config['metadata'][side]
        require(Path(item['archive']) == PRODUCTION/(side+'-row-interfaces.zip')
                and sha(item['archive']) == item['archive_sha256']
                and sha(item['path']) == item['sha256'], 'immutable row inputs changed')
        actual = {}
        for line in Path(item['path']).read_text().splitlines():
            name, mode, ns = line.split('\t')
            require(name not in actual, 'row metadata duplicates a member')
            actual[name] = (int(mode), int(ns))
        expected = {key.split('/', 1)[1]: (entry['mode'], entry['mtime_ns'])
            for key, entry in lineage.items() if key.startswith(side+'/')}
        require(actual == expected and len(actual) == EXPECTED_ROWS[side]
                and item['entries'] == len(actual),
                'row-view metadata differs from accepted exact lineage')
    return config


def prior_failed_final(evidence):
    require(Path(evidence['reconciliation']) == ROOT/'results/final-problem2-reconciliation6-20261019.json'
            and sha(evidence['reconciliation']) == evidence['reconciliation_sha256'],
            'prior failed final reconciliation changed')
    rec = read_json(evidence['reconciliation']); state = read_json(LEDGER_FILE)
    outer = FIRST_FINAL/'outer-records/final-problem2-outer.json'
    report = FIRST_FINAL/'report.json'
    require(rec['status'] == 'reconciled' and rec['Agda_dispatched'] is False
            and rec['source_graph_audit_run'] is False and rec['all_six_views_unmounted']
            and rec['outer_record_sha256'] == sha(outer)
            and rec['run_report_sha256'] == sha(report)
            and state['finished'].get(rec['reservation_id']) == rec['finished']
            and read_json(outer)['accepted'] is False
            and read_json(report)['accepted'] is False
            and not (FIRST_FINAL/'records/final-problem2-check6.json').exists()
            and rec['whole_service_cpu_seconds_exact'] <= rec['total_stage_accounted_cpu_seconds']
                <= rec['stage_envelope_cpu_seconds'],
            'prior failed final stage must remain preserved and fully reconciled')
    residual = dict(rec.get('residual_withholding') or {})
    if residual:
        identifier = residual.pop('withholding_id')
        require(state.get('withheld', {}).get(identifier) == residual,
                'prior failed final residual charge missing')
    return evidence


def prior_heap_failure(evidence):
    rec_path = ROOT/'results/final-problem2-recovery-reconciliation6-20261019.json'
    require(Path(evidence['reconciliation']) == rec_path
            and sha(rec_path) == evidence['reconciliation_sha256'],
            'prior heap-failure reconciliation changed')
    rec = read_json(rec_path); state = read_json(LEDGER_FILE)
    outer = PREVIOUS_FINAL/'outer-records/final-problem2-outer.json'
    report = PREVIOUS_FINAL/'report.json'
    child = PREVIOUS_FINAL/'records/final-problem2-check6.json'
    log = PREVIOUS_FINAL/'records/final-problem2-check6.log'
    require(rec['status'] == 'reconciled' and rec['all_six_views_unmounted']
            and rec['Agda_dispatched'] and rec['source_graph_audit_passed']
            and state['finished'].get(rec['reservation_id']) == rec['finished']
            and rec['outer_record_sha256'] == sha(outer)
            and rec['run_report_sha256'] == sha(report)
            and rec['child_record_sha256'] == sha(child)
            and rec['child_log_sha256'] == sha(log)
            and read_json(child)['exit_code'] == 251
            and 'Heap exhausted' in log.read_text()
            and rec['whole_service_cpu_seconds_exact'] <= rec['total_stage_accounted_cpu_seconds']
                <= rec['stage_envelope_cpu_seconds'],
            'preserved, reconciled heap-failure evidence is required')
    residual = dict(rec.get('residual_withholding') or {})
    if residual:
        identifier = residual.pop('withholding_id')
        require(state.get('withheld', {}).get(identifier) == residual,
                'prior heap-failure residual charge missing')
    old_plan = read_json(PREVIOUS_FINAL/'plan.json')
    require(sha(ROOT/'tools/final_problem2_resume6.py')
                == old_plan['helper_sha256']['final_problem2_resume6.py'],
            'prior controller source must remain immutable')
    return evidence


def authorization(path):
    path = Path(path).resolve(strict=True)
    raw = read_json(path)
    require(raw.get('approved') is True
            and raw.get('final_problem2_check_authorized') is True,
            'explicit final Problem2 stage authorization is required')
    require(raw.get('output') == str(OUT) and raw.get('total_cpu_seconds') == 172800,
            'authorization output or unchanged total differs')
    reserve = raw.get('reservation_cpu_seconds')
    outer = raw.get('outer_cpu_cap_seconds')
    child = raw.get('child_cpu_limit_seconds')
    wall = raw.get('wall_limit_seconds')
    cap = raw.get('own_output_cap_bytes')
    numbers = (reserve, outer, child, wall, cap)
    require(all(isinstance(value, (int, float)) and value > 0 for value in numbers),
            'authorization caps must be finite positive numbers')
    require(child <= MAX_CHILD_CPU and child+100 <= outer <= MAX_OUTER_CPU
            and outer+100 <= reserve <= MAX_RESERVATION_CPU,
            'authorized CPU caps exceed or do not nest within 2200/2400/2500')
    require(180 <= wall <= MAX_WALL, 'authorized wall cap exceeds 7200 seconds')
    require(type(cap) is int and cap <= 4*MIB,
            'authorized own-output cap must be an integer no larger than 4MiB')
    require(raw.get('parent_assembly_allowance_cpu_seconds') == ASSEMBLY_ALLOWANCE,
            'the separate parent assembly allowance must be exactly 10 CPU seconds')
    require(raw.get('hard_memory_gib') == HARD_GIB and raw.get('swap_bytes') == 0
            and raw.get('core_bytes') == 0
            and raw.get('ordinary_free_disk_floor_gib') == 80,
            'memory, swap, core, or ordinary disk safeguards differ')
    require(raw.get('manual_ledger_finish_required') is True,
            'authorization must preserve manual outer ledger reconciliation')
    verified_row_view(raw['row_view'])
    prior_failed_final(raw['prior_failed_final'])
    prior_heap_failure(raw['prior_heap_failure'])
    return path, raw


def schedule_groups(plan):
    return {side: {group for entry in plan['forecast']['side'][side]['batches']
                   for group in entry['groups']} for side in SIDES}


def reconciled_production_stage(state, run_id, expected_accepted, reconciliation):
    """Identify an actual terminal receipt and its complete CPU accounting."""
    report_path = PRODUCTION/('report-'+run_id+'.json')
    outer_path = PRODUCTION/'outer-records'/(run_id+'.json')
    job_path = PRODUCTION/('job-'+run_id+'.json')
    report, outer, job = map(read_json, (report_path, outer_path, job_path))
    identifier = job['reservation']['reservation_id']
    require(report.get('run_id') == run_id
            and report.get('accepted') is expected_accepted
            and outer.get('accepted') is expected_accepted
            and outer.get('full_row_production_run_id') == run_id
            and outer.get('reservation_id') == identifier,
            'terminal production stage differs from its actual receipt')
    require(identifier not in state['reservations'] and identifier in state['finished'],
            'a production stage reservation remains unreconciled')
    finished = state['finished'][identifier]
    require(finished.get('accepted') is expected_accepted
            and finished.get('record_sha256') == sha(outer_path)
            and Path(finished['record']).resolve() == outer_path.resolve(),
            'production stage ledger finish does not match its terminal receipt')
    reconciliation = Path(reconciliation)
    record = read_json(reconciliation)
    require(record['status'] == 'reconciled'
            and record['reservation_id'] == identifier
            and record['outer_record_sha256'] == sha(outer_path)
            and record['run_report_sha256'] == sha(report_path)
            and record['finished'] == finished
            and record['nested_child_records_charged_separately'] is False
            and record['all_four_views_unmounted'] is True,
            'complete whole-service production accounting is required')
    require(record['whole_service_cpu_seconds_exact']
                <= record['total_stage_accounted_cpu_seconds']
                <= job['reservation']['reserved_cpu_seconds'],
            'whole-service accounting exceeds its finite stage reservation')
    residual = dict(record.get('residual_withholding') or {})
    if residual:
        withholding_id = residual.pop('withholding_id')
        require(state.get('withheld', {}).get(withholding_id) == residual,
                'whole-service CPU residual is absent from the authoritative ledger')
    else:
        require(record['positive_residual_seconds'] <= 0,
                'positive whole-service CPU residual was not accounted')
    require(len(report['view_cleanup']) == 4 and all(
        entry['unmounted'] and entry['exit_code'] == 0 for entry in report['view_cleanup']),
        'a production stage did not cleanly close all archive views')
    return {'run_id': run_id, 'accepted': expected_accepted,
        'reservation_id': identifier, 'outer_record': str(outer_path),
        'outer_record_sha256': sha(outer_path),
        'run_report': str(report_path), 'run_report_sha256': sha(report_path),
        'reconciliation': str(reconciliation),
        'reconciliation_sha256': sha(reconciliation),
        'whole_service_cpu_seconds': record['whole_service_cpu_seconds_exact']}


def production_terminal(state):
    original_plan = read_json(PRODUCTION_PLAN)
    report = read_json(PRODUCTION/'report.json')
    require(report.get('accepted') is True
            and report.get('full_remaining_row_coverage_checked') is True
            and report.get('Problem2_checked') is False
            and report.get('result_or_allparts_checked') is False,
            'accepted full-row production report with an unproved Problem2 is required')
    run_id = report.get('run_id')
    require(re.fullmatch(r'production-\d{4}', str(run_id)) is not None,
            'production report has an invalid terminal run id')
    run_report = PRODUCTION/('report-'+run_id+'.json')
    require(run_report.is_file() and read_json(run_report) == report,
            'current production report is not the actual accepted terminal report')
    plan_path = Path(report.get('effective_plan', PRODUCTION_PLAN))
    prior_stages = []
    if plan_path.resolve() != PRODUCTION_PLAN.resolve():
        run_number = int(run_id.rsplit('-', 1)[1])
        require(run_number >= 2
                and plan_path.resolve() == (PRODUCTION/('resume-plan-'+run_id+'.json')).resolve()
                and report['effective_plan_sha256'] == sha(plan_path)
                and report['original_plan_sha256'] == sha(PRODUCTION_PLAN),
                'accepted recovery must identify its immutable effective and original plans')
        plan = read_json(plan_path)
        resume = plan['resume']
        require(resume['original_plan_sha256'] == sha(PRODUCTION_PLAN)
                and resume['controller_sha256'] == sha(resume['controller'])
                and resume['history_sha256'] == sha(resume['history']),
                'recovery evidence changed after dispatch')
        expected = copy.deepcopy(original_plan)
        for key in ('authorization_path', 'authorization_sha256', 'authorization', 'run'):
            expected[key] = plan[key]
        expected['forecast']['storage'].update(resume['storage_overrides'])
        expected['resume'] = resume
        require(plan == expected
                and sha(plan['authorization_path']) == plan['authorization_sha256']
                and read_json(plan['authorization_path']) == plan['authorization'],
                'recovery changed frozen mathematical inputs or lacks its applied authorization')
        if run_number == 2:
            require(resume['original_failed_report_sha256'] == sha(PRODUCTION/'report-production-0001.json')
                    and resume['original_outer_record_sha256'] == sha(PRODUCTION/'outer-records/production-0001.json')
                    and resume['reconciliation_sha256'] == sha(resume['reconciliation']),
                    'first recovery prior-stage evidence changed')
            prior_stages = [reconciled_production_stage(state, 'production-0001', False,
                resume['reconciliation'])]
            current_reconciliation = ROOT/'results/full-row-resume-reconciliation6-20261019.json'
        else:
            prior = resume['prior_stages']
            require([item['run_id'] for item in prior] == [
                f'production-{number:04d}' for number in range(1, run_number)],
                'recovery must retain every earlier production stage in order')
            require(Path(resume['previous_effective_plan']).resolve() == (
                    PRODUCTION/(f'resume-plan-production-{run_number-1:04d}.json')).resolve()
                    and sha(resume['previous_effective_plan']) == resume['previous_effective_plan_sha256']
                    and all(sha(ROOT/'tools'/name) == pin
                        for name, pin in resume['helper_sha256'].items()),
                    'previous recovery plan or preserved helper changed')
            for item in prior:
                require(Path(item['report']).resolve() == (
                            PRODUCTION/('report-'+item['run_id']+'.json')).resolve()
                        and Path(item['outer_record']).resolve() == (
                            PRODUCTION/'outer-records'/(item['run_id']+'.json')).resolve()
                        and all(sha(item[key]) == item[key+'_sha256']
                            for key in ('report', 'outer_record', 'reconciliation')),
                        'a prior recovery receipt changed')
                prior_stages.append(reconciled_production_stage(state,
                    item['run_id'], False, item['reconciliation']))
            current_reconciliation = Path(resume['terminal_reconciliation_path'])
            require(current_reconciliation.parent.resolve() == (ROOT/'results').resolve(),
                    'current recovery reconciliation must be canonical local evidence')
        current_stage = reconciled_production_stage(state, run_id, True,
            current_reconciliation)
    else:
        plan = original_plan
        current_stage = None
    outer_path = PRODUCTION/'outer-records'/(run_id+'.json')
    job_path = PRODUCTION/('job-'+run_id+'.json')
    require(outer_path.is_file() and job_path.is_file(),
            'accepted production lacks its terminal outer record or job')
    outer, job = read_json(outer_path), read_json(job_path)
    if prior_stages:
        require(job['effective_plan_sha256'] == sha(plan_path)
                and job['controller_sha256'] == plan['resume']['controller_sha256'],
                'accepted outer job does not pin the executed recovery plan and controller')
    reservation = job['reservation']
    identifier = reservation['reservation_id']
    require(outer.get('accepted') is True and outer.get('reservation_id') == identifier
            and outer.get('full_row_production_run_id') == run_id,
            'production terminal outer record is not accepted or does not match its reservation')
    require(identifier not in state['reservations'] and identifier in state['finished'],
            'production outer reservation has not been reconciled exactly once')
    finished = state['finished'][identifier]
    require(finished.get('accepted') is True
            and finished.get('record_sha256') == sha(outer_path)
            and Path(finished.get('record', '')).resolve() == outer_path.resolve(),
            'ledger production finish does not identify the accepted outer record')
    manifest_path = Path(report['complete_row_cache_manifest'])
    require(manifest_path.resolve() == COMPLETE_ROWS.resolve() and manifest_path.is_file(),
            'production report does not identify the canonical complete-row manifest')
    return {'plan': plan, 'report': report, 'run_id': run_id,
            'effective_plan_path': str(plan_path), 'effective_plan_sha256': sha(plan_path),
            'original_plan_sha256': sha(PRODUCTION_PLAN),
            'prior_reconciled_stages': prior_stages, 'current_reconciled_stage': current_stage,
            'run_report': str(run_report), 'run_report_sha256': sha(run_report),
            'outer_record': str(outer_path), 'outer_record_sha256': sha(outer_path),
            'complete_manifest_sha256': sha(COMPLETE_ROWS),
            'reservation_id': identifier}


def row_inventory(side, production_plan, complete):
    item = complete['row_archives'][side]
    path = Path(item['path'])
    require(path.resolve() == (PRODUCTION/(side+'-row-interfaces.zip')).resolve()
            and sha(path) == item['sha256'], side+' complete row archive changed')
    lineage = json.loads(zstd.decompress(LINEAGE.read_bytes()))
    inventory, groups = {}, set()
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) == EXPECTED_ROWS[side]
                and archive.testzip() is None, side+' row archive inventory is invalid')
        for name in names:
            match = re.fullmatch(r'Rows(\d+)\.agdai', name)
            require(match is not None, side+' row archive is not flat Rows-only')
            group = int(match.group(1)); raw = archive.read(name)
            key = side+'/'+name; entry = lineage.get(key)
            pin = hashlib.sha256(raw).hexdigest()
            require(entry is not None and pin == entry['new_sha256']
                    and raw[:24].hex() == entry['header_hex']
                    and raw[24:28] == bytes.fromhex('28b52ffd'),
                    side+' row frame lacks exact lineage')
            payload = zstd.decompress(raw[24:])
            require(hashlib.sha256(payload).hexdigest() == entry['decoded_payload_sha256'],
                    side+' decoded row payload differs from lineage')
            require(entry['seeded_accepted_pilot'] is (group in PILOTS),
                    side+' pilot/scheduled row lineage classification differs')
            inventory[name] = pin; groups.add(group)
    digest = hashlib.sha256(json.dumps(inventory,
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    require(item['member_count'] == len(inventory)
            and item['member_inventory_sha256'] == digest,
            side+' row archive differs from complete manifest inventory')
    scheduled = schedule_groups(production_plan)[side]
    universe = set(range(654 if side == 'upper' else 688))
    require(len(scheduled) == EXPECTED_SCHEDULED[side]
            and groups == scheduled | PILOTS
            and groups | ORIGINAL_OWNED[side] == universe
            and groups.isdisjoint(ORIGINAL_OWNED[side])
            and set(complete['checked_remaining_groups'][side]) == scheduled
            and set(complete['seeded_accepted_pilot_groups'][side]) == PILOTS,
            side+' row archive does not equal scheduled checks plus two accepted pilots')
    source_manifest = read_json(production_plan['packages'][side+'-sources']['manifest'])
    require({int(group) for group in source_manifest['cases']} == groups,
            side+' prepared source cases differ from the completed row interfaces')
    allparts = source_manifest['entries']['AllParts.agda']
    with zipfile.ZipFile(production_plan['packages'][side+'-sources']['archive']) as archive:
        raw = archive.read('AllParts.agda')
    require(len(raw) == allparts['size']
            and hashlib.sha256(raw).hexdigest() == allparts['sha256'],
            side+' AllParts source entry differs')
    imported = {int(group) for group in re.findall(
        rb'^import Tests\.Complete(?:Upper|Lower)Rows6\.Rows(\d+) as P\d+$', raw, re.M)}
    require(imported == groups and ORIGINAL_OWNED[side].isdisjoint(imported),
            side+' AllParts source does not preserve original donor-owned namespaces')
    return {'path': str(path), 'sha256': item['sha256'], 'member_count': len(inventory),
            'member_inventory_sha256': digest, 'groups_sha256': hashlib.sha256(
                json.dumps(sorted(groups), separators=(',', ':')).encode()).hexdigest(),
            'scheduled_checked': len(scheduled), 'accepted_pilots': sorted(PILOTS),
            'original_donor_owned': sorted(ORIGINAL_OWNED[side]),
            'allparts_source': dict(allparts)}


def complete_row_evidence(production_plan):
    complete = read_json(COMPLETE_ROWS)
    require(complete.get('remaining_rows_sources_safely_checked') is True
            and complete.get('result_or_allparts_checked') is False
            and complete.get('Problem2_checked') is False,
            'complete row cache evidence must retain the Problem2 boundary')
    require(sha(LINEAGE) == complete['lineage_sha256'], 'row lineage archive changed')
    lineage = json.loads(zstd.decompress(LINEAGE.read_bytes()))
    require(len(lineage) == 1337, 'complete row lineage must have exactly 1,337 entries')
    rows = {side: row_inventory(side, production_plan, complete) for side in SIDES}
    require(sum(item['member_count'] for item in rows.values()) == 1337,
            'complete row cache must contain exactly 1,337 row frames')
    upper_manifest = read_json(production_plan['packages']['upper-sources']['manifest'])
    result_entry = upper_manifest['entries']['Result.agda']
    with zipfile.ZipFile(production_plan['packages']['upper-sources']['archive']) as archive:
        result_raw = archive.read('Result.agda')
    require(len(result_raw) == result_entry['size']
            and hashlib.sha256(result_raw).hexdigest() == result_entry['sha256']
            and b'import Tests.CompleteUpperRows6.AllParts as Upper' in result_raw
            and b'import Tests.CompleteLowerRows6.AllParts as Lower' in result_raw
            and b'initial6x6 : Problem2' in result_raw,
            'Result source entry does not state the expected two-bound Problem2 theorem')
    return {'manifest': str(COMPLETE_ROWS), 'manifest_sha256': sha(COMPLETE_ROWS),
            'lineage': str(LINEAGE), 'lineage_sha256': sha(LINEAGE),
            'rows': rows, 'result_source': dict(result_entry)}


def validate_private_package(production_plan):
    manifest = read_json(PRIVATE_MANIFEST)
    require(manifest['package_source_integrity_verified'] is True
            and manifest['package_build_not_yet_checked'] is True
            and manifest['complete_initial_theorem_not_yet_checked'] is True
            and manifest['selected_module_count'] == 4128,
            'private selected-source package boundary differs')
    require(sha(manifest['core_archive']) == manifest['core_archive_sha256']
            and sha(manifest['source_graph']) == manifest['source_graph_sha256'],
            'private core or selected source graph changed')
    references = manifest['large_archive_references']
    for name, package in production_plan['packages'].items():
        require(name in references
                and Path(references[name]['archive']).resolve() == Path(package['archive']).resolve()
                and references[name]['archive_sha256'] == package['archive_sha256'],
                'private selected-source package does not reference production '+name)
    return {'manifest': str(PRIVATE_MANIFEST), 'manifest_sha256': sha(PRIVATE_MANIFEST),
            'core_archive_sha256': manifest['core_archive_sha256'],
            'source_graph_sha256': manifest['source_graph_sha256'],
            'source_graph_decoded_sha256': manifest['source_graph_decoded_sha256'],
            'selected_modules': 4128,
            'package_build_checked': False,
            'package_referenced_not_duplicated': True}


def registered_paths():
    registry = read_json(REGISTRY_FILE)
    return {Path(entry['path']) for entry in registry['roots']}


def physical_census(production_plan):
    # citation_diagnostic6's historical census uses plain du for its own OUT.
    # Point that slot at an absent sentinel and add this stage separately with
    # du -x so mounted archive contents can never be counted as physical bytes.
    common.OUT = OUT/'__physical-du-x-sentinel__'
    legacy = common.storage(0)
    extras = {Path(path) for path in production_plan['census_paths']} | registered_paths()
    extras.discard(OUT)
    return (legacy['allocated_study_bytes'] + allocated(OUT)
            + sum(allocated(path) for path in extras)), extras


def storage(plan, reserve=STOP_RESERVE):
    total, paths = physical_census(read_json(PRODUCTION_PLAN))
    own = allocated(OUT)
    cap = int(plan['authorization']['own_output_cap_bytes'])
    private_remaining = int(read_json(PRODUCTION_PLAN)['private_core_remaining_allowance_bytes'])
    projected = total-own+cap+private_remaining
    root_free = shutil.disk_usage(ROOT).free
    data_free = shutil.disk_usage(BASE).free
    require(own <= cap and projected < HARD_GIB*GIB,
            'final output cap or fresh retained physical projection reached')
    require(root_free-reserve >= 80*GIB and data_free-reserve >= 80*GIB,
            'ordinary 80GiB free-disk floor reached')
    result = {'checked_utc': utc(), 'allocated_study_bytes': total,
        'own_output_bytes': own, 'own_output_cap_bytes': cap,
        'private_packaging_remaining_allowance_bytes': private_remaining,
        'full_projection_bytes': projected, 'hard_retained_cap_bytes': HARD_GIB*GIB,
        'root_free_bytes': root_free, 'data_free_bytes': data_free,
        'stop_reserve_bytes': reserve, 'census_path_count': len(paths),
        'virtual_readonly_fuse_bytes_excluded_via_du_x': True}
    atomic_json(OUT/'storage.json', result)
    return result


def no_active_work():
    done = subprocess.run(['systemctl', '--user', 'list-units',
        '--state=activating,running', '--type=service', '--no-legend', '--plain',
        'othello*'], capture_output=True, text=True)
    require(done.returncode == 0 and not done.stdout.strip(),
            'an Othello service is active')
    peers = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal():
            continue
        try:
            if proc.joinpath('comm').read_text().strip().lower() != 'agda':
                continue
            argv = proc.joinpath('cmdline').read_bytes().decode(errors='replace').split('\0')[:-1]
            cwd = proc.joinpath('cwd').resolve()
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if str(ROOT) in str(cwd) or str(BASE) in str(cwd) or any(
                str(ROOT) in arg or str(BASE) in arg or '/othello-agda/runs/' in arg for arg in argv):
            peers.append({'pid': int(proc.name), 'cwd': str(cwd), 'argv': argv})
    require(not peers, 'an Othello Agda checker is active')
    known_views = [PRODUCTION/name for name in
        ('upper-cache', 'lower-cache', 'upper-proof/src/Tests/CompleteUpperRows6',
         'lower-proof/src/Tests/CompleteLowerRows6')]
    require(not any(os.path.ismount(path) for path in known_views),
            'a production archive view remains mounted')


def resources():
    groups = [line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
              if line.startswith('0::')]
    require(len(groups) == 1, 'one unified cgroup required')
    group = Path('/sys/fs/cgroup')/groups[0].lstrip('/')
    require((group/'memory.max').read_text().strip() == str(HARD_GIB*GIB)
            and (group/'memory.swap.max').read_text().strip() == '0',
            'hard 12GiB/no-swap cgroup required')
    return group


def cgroup_cpu(group):
    values = dict(line.split() for line in (group/'cpu.stat').read_text().splitlines())
    return int(values['usage_usec'])/1e6


@contextlib.contextmanager
def watched(plan, group):
    stop = threading.Event(); failures = []
    cutoff = plan['authorization']['outer_cpu_cap_seconds']-50

    def watch():
        while not stop.wait(3):
            try:
                require(cgroup_cpu(group) < cutoff, 'final service CPU cleanup guard reached')
                storage(plan)
                available = next(int(line.split()[1])*1024 for line in
                    Path('/proc/meminfo').read_text().splitlines()
                    if line.startswith('MemAvailable:'))
                require(available >= 2*GIB, 'host memory headroom guard reached')
            except BaseException as error:
                failures.append(repr(error))
                atomic_json(OUT/'resource-stop.json', {'reason': repr(error), 'finished_utc': utc()})
                os.kill(os.getpid(), signal.SIGTERM)
                return
    thread = threading.Thread(target=watch, daemon=True); thread.start()
    try:
        yield
    finally:
        stop.set(); thread.join()
    require(not failures, 'resource watcher stopped final checking')


def validate_plan(plan, *, worker=False):
    require(plan['format'] == 'othello-final-problem2-check6-plan-v1'
            and sha(plan['authorization_path']) == plan['authorization_sha256'],
            'final plan or authorization changed')
    verified_row_view(plan['row_view'])
    prior_failed_final(plan['prior_failed_final'])
    prior_heap_failure(plan['prior_heap_failure'])
    base = CONTROL if worker else ROOT/'tools'
    require(helper_hashes(base) == plan['helper_sha256'],
            'final controller helper set changed')
    require(sha(plan['production_plan']) == plan['production_plan_sha256']
            and sha(PRODUCTION_PLAN) == plan['original_production_plan_sha256']
            and sha(COMPLETE_ROWS) == plan['complete_rows']['manifest_sha256']
            and sha(PRIVATE_MANIFEST) == plan['private_package']['manifest_sha256'],
            'production or selected-source evidence changed')
    require(sha(plan['agda']) == plan['agda_sha256']
            and sha(plan['filesystem_binary']) == plan['filesystem_binary_sha256'],
            'checker or archive filesystem binary changed')
    require(len(plan['p1_files']) == 23
            and all(sha(ROOT/name) == pin for name, pin in plan['p1_files'].items()),
            'tagged P1 changed')
    require(source_identity(CHECK) == plan['wrapper_source_identity'],
            'final wrapper source identity changed')


def mount_archive(fs, archive, view, log_path, stack, processes):
    archive = Path(archive); view = Path(view)
    lock = stack.enter_context(archive.open('rb'))
    fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
    require(view.is_dir() and not any(view.iterdir()), 'archive mountpoint must start empty')
    log = stack.enter_context(Path(log_path).open('wb'))
    args = [str(fs), str(archive), str(view)]
    config = read_json(OUT/'plan.json')['row_view']
    for side in SIDES:
        item = config['metadata'][side]
        if archive.resolve() == Path(item['archive']).resolve():
            args = [config['binary'], str(archive), item['path'], str(view)]
    process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
    processes.append((view, process))
    started = time.monotonic()
    while not os.path.ismount(view):
        require(process.poll() is None and time.monotonic()-started < 10,
                'archive view did not mount: '+str(view))
        time.sleep(.05)


def verify_row_view(side, path, row_evidence):
    path = Path(path); lineage = json.loads(zstd.decompress(LINEAGE.read_bytes()))
    names = sorted(item.name for item in path.iterdir())
    require(len(names) == len(set(names)) == EXPECTED_ROWS[side],
            side+' mounted row view inventory differs')
    inventory = {}
    for name in names:
        match = re.fullmatch(r'Rows(\d+)\.agdai', name)
        require(match is not None, side+' mounted row view is not flat Rows-only')
        raw = (path/name).read_bytes(); key = side+'/'+name
        info = (path/name).stat()
        require((info.st_mode & 0o7777) == lineage[key]['mode']
                and info.st_mtime_ns == lineage[key]['mtime_ns'],
                side+' mounted row metadata differs from accepted lineage')
        require(hashlib.sha256(raw).hexdigest() == lineage[key]['new_sha256']
                and raw[:24].hex() == lineage[key]['header_hex']
                and hashlib.sha256(zstd.decompress(raw[24:])).hexdigest()
                    == lineage[key]['decoded_payload_sha256'],
                side+' mounted row frame differs from exact lineage')
        inventory[name] = lineage[key]['new_sha256']
    digest = hashlib.sha256(json.dumps(inventory,
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    require(digest == row_evidence['member_inventory_sha256'],
            side+' mounted row inventory digest differs')
    return {'entries_verified': len(names), 'member_inventory_sha256': digest,
            'header_bytes_verified': 24, 'decoded_payloads_verified': len(names),
            'body_interfaces_intentionally_absent': not any(
                item.name.startswith('Body') for item in path.iterdir())}


def archive_hashes(plan):
    paths = {name: Path(package['archive']) for name, package in
             plan['production_packages'].items()}
    paths.update({side+'-rows': Path(plan['complete_rows']['rows'][side]['path'])
                  for side in SIDES})
    paths.update({'row-lineage': LINEAGE,
                  'private-core': Path(read_json(PRIVATE_MANIFEST)['core_archive']),
                  'source-graph': Path(read_json(PRIVATE_MANIFEST)['source_graph'])})
    return {name: {'path': str(path), 'sha256': sha(path)} for name, path in paths.items()}


def cleanup_views(processes):
    cleanup = []
    for view, process in reversed(processes):
        if os.path.ismount(view):
            subprocess.run(['/usr/bin/fusermount3', '-u', str(view)],
                           capture_output=True, timeout=8)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)
        cleanup.append({'view': str(view), 'unmounted': not os.path.ismount(view),
                        'exit_code': process.returncode})
    return cleanup


def sandbox(readonly):
    argv = ['/usr/bin/bwrap', '--ro-bind', '/', '/', '--bind', str(OUT), str(OUT),
        '--proc', '/proc', '--dev-bind', '/dev', '/dev', '--tmpfs', '/tmp',
        '--die-with-parent']
    for path in readonly:
        argv += ['--ro-bind', str(path), str(path)]
    return argv+['--']


def worker():
    plan = read_json(OUT/'plan.json'); validate_plan(plan, worker=True)
    group = resources(); job = read_json(OUT/'job.json')
    ledger_state = read_json(LEDGER_FILE)
    production_terminal(ledger_state)
    identifier = job['reservation']['reservation_id']
    require(set(ledger_state['reservations']) == {identifier}
            and ledger_state['reservations'][identifier] == job['reservation'],
            'the final outer reservation must be the only outstanding reservation')
    donors = {Path(path): tuple(pins) for path, pins in plan['donors'].items()}
    require(len(donors) == 68, 'exactly 68 frozen core donor roots are required')
    failure = None; child = None; source_report = None
    beginning = None; ending = None; cleanup = []; processes = []
    previous_term = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    with contextlib.ExitStack() as stack:
        try:
            for donor in donors:  # insertion order is the accepted include order
                lock = stack.enter_context((donor/'_build/.study6.lock').open('rb'))
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            stack.enter_context(build_lock(PROOF))
            stack.enter_context(build_lock(CHECK))
            validate_plan(plan, worker=True)
            donor_before = batch.donor_snapshot(donors)
            require(donor_before == plan['donor_beginning'], 'donor snapshot changed before final check')
            require(not assembly6.interfaces(CHECK) and not assembly6.interfaces(PROOF),
                    'new final roots must start without interfaces')
            target_if = CHECK/'_build/2.9.0/agda/src/Tests/FinalProblem2Check6.agdai'
            require(not target_if.exists(), 'a prior final wrapper interface is forbidden')
            fs = Path(plan['filesystem_binary'])
            views = {}
            for side in SIDES:
                source_view = PROOF/'src'/Path(*PREFIX[side].split('.'))
                row_view = PROOF/'_build/2.9.0/agda/src'/Path(*PREFIX[side].split('.'))
                source_view.mkdir(parents=True); row_view.mkdir(parents=True)
                package = plan['production_packages'][side+'-sources']
                mount_archive(fs, package['archive'], source_view,
                    OUT/(side+'-sources-filesystem.log'), stack, processes)
                mount_archive(fs, plan['complete_rows']['rows'][side]['path'], row_view,
                    OUT/(side+'-rows-filesystem.log'), stack, processes)
                views[side+'-sources'] = source_view; views[side+'-rows'] = row_view
            for side in SIDES:
                cache_view = OUT/'views'/(side+'-cache'); cache_view.mkdir(parents=True)
                package = plan['production_packages'][side+'-cache']
                mount_archive(fs, package['archive'], cache_view,
                    OUT/(side+'-cache-filesystem.log'), stack, processes)
                views[side+'-cache'] = cache_view
            beginning = {}
            for side in SIDES:
                package = plan['production_packages'][side+'-sources']
                beginning[side+'-sources'] = verify_view(
                    views[side+'-sources'], package['manifest'])
                package = plan['production_packages'][side+'-cache']
                beginning[side+'-cache'] = verify_view(
                    views[side+'-cache'], package['manifest'])
                beginning[side+'-rows'] = verify_row_view(side, views[side+'-rows'],
                    plan['complete_rows']['rows'][side])
            beginning['archive_hashes'] = archive_hashes(plan)
            atomic_json(OUT/'input-snapshots-begin.json', beginning)
            proof_before = assembly6.interfaces(PROOF)
            require(len(proof_before) == 1337
                    and all('/Rows' in path and not '/Body' in path for path in proof_before),
                    'proof root must expose exactly 1,337 cached Rows interfaces and no Body interfaces')
            # Establish the exact source boundary before spending the final
            # checker budget. End snapshots below prove those bytes stay fixed.
            with watched(plan, group):
                source_report = source_audit.audit(PRIVATE_MANIFEST, ROOT, plan['p1_files'])
            require(source_report['source_audit_passed'] is True
                    and source_report['selected_modules'] == 4128
                    and source_report['source_postulates_found'] == 0,
                    'selected Problem2 source audit was not accepted')
            atomic_json(OUT/'source-audit.json', source_report)
            command = sandbox([*donors, *views.values()]) + [
                plan['agda'], '--no-libraries', '-i', 'src']
            for donor in donors:
                command += ['-i', str(donor/'src')]
            command += ['-i', str(PROOF/'src')]
            for side in SIDES:
                command += ['-i', str(views[side+'-cache']/'src')]
            command += FLAGS[1:] + [WRAPPER_RELATIVE, '+RTS', '-M9000M', '-c', '-s', '-RTS']
            with watched(plan, group):
                child = run_job('final-problem2-check6', command, RECORDS, root=CHECK,
                    timeout=plan['child_wall_limit_seconds'],
                    cpu_limit=plan['authorization']['child_cpu_limit_seconds'],
                    rss_limit_gib=11.4, log_limit_mib=2,
                    expected_source_sha256=plan['wrapper_source_identity']['source_sha256'],
                    locked=True, metadata={
                        'checker_binary_path': plan['agda'],
                        'checker_binary_sha256': plan['agda_sha256'],
                        'checker_flags': FLAGS+['+RTS', '-M9000M', '-c', '-s', '-RTS'],
                        'wrapper_source_identity': plan['wrapper_source_identity'],
                        'actual_theorem_source_entries': plan['theorem_source_entries'],
                        'proof_cache_before': proof_before,
                        'row_cache_evidence': plan['complete_rows'],
                        'p1_files': plan['p1_files'],
                        'private_selected_source_package': plan['private_package'],
                        'no_write_interfaces_policy': True,
                        'body_interfaces_intentionally_absent': True,
                        'known_full_layout_peak_gib': 4.9145,
                        'final_theorem_memory_was_unknown_before_this_check': True,
                        'nested_record_not_separately_reserved': True})
            require(child['accepted'], 'final safe Agda child was not accepted; no retry')
            log = (RECORDS/'final-problem2-check6.log').read_text(errors='replace')
            required = [PREFIX['upper']+'.AllParts', PREFIX['lower']+'.AllParts',
                        PREFIX['upper']+'.Result', WRAPPER_MODULE]
            require(all('Checking '+module in log for module in required),
                    'accepted log does not show both AllParts, Result, and wrapper checks')
            repeated = re.findall(r'Checking Tests\.Complete(?:Upper|Lower)Rows6\.Rows\d+', log)
            require(not repeated, 'final check repeated a Boolean Rows proof')
            # Body modules contain regenerable String data. Their interfaces
            # were deliberately evicted after accepted row checks; rebuilding
            # them with --no-write-interfaces is part of the validated policy.
            rebuilt_data = re.findall(r'Checking Tests\.Complete(?:Upper|Lower)Rows6\.Body\d+', log)
            atomic_json(OUT/'cached-row-replay.json', {
                'Boolean_Rows_rechecked': repeated,
                'data_only_Body_modules_reconstructed': rebuilt_data,
                'Body_reconstruction_is_not_new_game_row_evidence': True})
            proof_after = assembly6.interfaces(PROOF)
            require(proof_after == proof_before and not assembly6.interfaces(CHECK)
                    and not target_if.exists(),
                    '--no-write-interfaces changed the final or cached interface pools')
            ending = {}
            for side in SIDES:
                package = plan['production_packages'][side+'-sources']
                ending[side+'-sources'] = verify_view(
                    views[side+'-sources'], package['manifest'])
                package = plan['production_packages'][side+'-cache']
                ending[side+'-cache'] = verify_view(
                    views[side+'-cache'], package['manifest'])
                ending[side+'-rows'] = verify_row_view(side, views[side+'-rows'],
                    plan['complete_rows']['rows'][side])
            ending['archive_hashes'] = archive_hashes(plan)
            require(ending == beginning, 'source, dataset, or row-cache inputs changed')
            require(batch.donor_snapshot(donors) == donor_before,
                    'a donor source or interface pool changed during final checking')
            validate_plan(plan, worker=True)
            atomic_json(OUT/'input-snapshots-end.json', ending)
        except BaseException as error:
            failure = repr(error)
            atomic_json(OUT/'worker-exception.json', {'recorded_utc': utc(),
                'exception': failure, 'traceback': traceback.format_exc()})
        finally:
            cleanup = cleanup_views(processes)
            atomic_json(OUT/'view-cleanup.json', cleanup)
    try:
        final_storage = storage(plan, reserve=0)
    except BaseException as error:
        final_storage = None
        failure = (failure+'; ' if failure else '')+'final storage: '+repr(error)
    accepted = (failure is None and final_storage is not None
        and child is not None and child.get('accepted') is True
        and source_report is not None and source_report.get('source_audit_passed') is True
        and beginning is not None and ending == beginning
        and len(cleanup) == 6
        and all(item['unmounted'] and item['exit_code'] == 0 for item in cleanup))
    report = {'format': 'othello-final-problem2-check6-report-v1',
        'finished_utc': utc(), 'accepted': accepted, 'failure': failure,
        'child_record': str(RECORDS/'final-problem2-check6.json'),
        'child_record_sha256': (sha(RECORDS/'final-problem2-check6.json')
                                if (RECORDS/'final-problem2-check6.json').exists() else None),
        'source_audit': str(OUT/'source-audit.json') if source_report is not None else None,
        'view_cleanup': cleanup, 'final_storage': final_storage,
        'Problem2_checked': accepted,
        'both_actual_AllParts_checked': accepted,
        'Result_initial6x6_checked': accepted,
        'same_optimal_pair_black16_white20': accepted,
        'white_minus_black_raw_score': 4 if accepted else None,
        'tagged_P1_preserved': accepted, 'source_postulates': 0 if accepted else None,
        'no_Boolean_Rows_rechecked': accepted,
        'no_interfaces_written': accepted,
        'private_source_package_independently_rebuilt': False,
        'private_source_package_referenced_not_duplicated': True,
        'mathematical_objective_complete': False,
        'remaining_project_work': ('parent proof-boundary review, documentation and private package closure'),
        'manual_ledger_finish_required_from_outer_record': True}
    atomic_json(OUT/'report.json', report)
    signal.signal(signal.SIGTERM, previous_term)
    require(accepted, 'final Problem2 checking failed; evidence retained and no retry authorized')


def supervise():
    plan = read_json(OUT/'plan.json'); validate_plan(plan, worker=True)
    job = read_json(OUT/'job.json')
    result = run_job('final-problem2-outer',
        ['/usr/bin/python3', '-B', str(CONTROL/'final_problem2_compacting6.py'), 'worker'],
        OUTER_RECORDS, root=CONTROL,
        timeout=plan['outer_wall_limit_seconds'],
        cpu_limit=plan['authorization']['outer_cpu_cap_seconds'],
        rss_limit_gib=11.7, log_limit_mib=.25,
        reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'],
        metadata={'manual_ledger_finish_required': True,
                  'final_problem2_check': True,
                  'child_cpu_limit_seconds': plan['authorization']['child_cpu_limit_seconds'],
                  'parent_assembly_allowance_not_reserved_here': ASSEMBLY_ALLOWANCE})
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # wait4 intentionally describes the reaped child tree. Keep that receipt
    # exact and separately expose the supervisor's own CPU for reconciliation.
    atomic_json(OUT/'supervisor-cpu.json', {
        'recorded_utc': utc(), 'self_user_seconds': usage.ru_utime,
        'self_system_seconds': usage.ru_stime,
        'self_cpu_seconds': usage.ru_utime+usage.ru_stime,
        'outer_wait4_cpu_seconds': result['cpu_seconds'],
        'whole_cgroup_cpu_snapshot_seconds': cgroup_cpu(resources()),
        'terminal_meter_or_conservative_exit_allowance_required': True,
        'reconciliation': 'Finish the outer wait4 record once, then account '
            'for positive whole-service-minus-wait4 CPU inside this same '
            'kernel stage envelope. Do not alter the rusage fields or charge '
            'nested checker records again.',
        'ledger_write_performed': False})
    return 0 if result['accepted'] else 1


def freeze_plan(auth_path, auth, terminal):
    production_plan = terminal['plan']
    require(len(production_plan['donors']) == 68 and len(production_plan['p1_files']) == 23,
            'production plan donor or P1 cardinality differs')
    complete = complete_row_evidence(production_plan)
    private = validate_private_package(production_plan)
    packages = production_plan['packages']
    for package in packages.values():
        require(sha(package['archive']) == package['archive_sha256']
                and sha(package['manifest']) == package['manifest_sha256'],
                'production source/data package changed')
    require(sha(production_plan['agda']) == production_plan['agda_sha256']
            and sha(production_plan['filesystem_binary']) == production_plan['filesystem_binary_sha256'],
            'production checker or archive filesystem binary changed')
    donors = {Path(path): tuple(pins) for path, pins in production_plan['donors'].items()}
    with contextlib.ExitStack() as stack:
        for donor in donors:
            lock = stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        donor_beginning = batch.donor_snapshot(donors)
    require(donor_beginning == production_plan['donor_beginning'],
            'donor snapshot changed after row production')
    wrapper_identity = source_identity(CHECK)
    upper_manifest = read_json(packages['upper-sources']['manifest'])
    lower_manifest = read_json(packages['lower-sources']['manifest'])
    theorem_entries = {
        PREFIX['upper']+'.AllParts': upper_manifest['entries']['AllParts.agda'],
        PREFIX['lower']+'.AllParts': lower_manifest['entries']['AllParts.agda'],
        PREFIX['upper']+'.Result': upper_manifest['entries']['Result.agda']}
    return {'format': 'othello-final-problem2-check6-plan-v1', 'created_utc': utc(),
        'authorization_path': str(auth_path), 'authorization_sha256': sha(auth_path),
        'authorization': auth, 'row_view': verified_row_view(auth['row_view']),
        'prior_failed_final': prior_failed_final(auth['prior_failed_final']),
        'prior_heap_failure': prior_heap_failure(auth['prior_heap_failure']),
        'production_plan': terminal['effective_plan_path'],
        'production_plan_sha256': terminal['effective_plan_sha256'],
        'original_production_plan_sha256': sha(PRODUCTION_PLAN),
        'production_terminal': {key: value for key, value in terminal.items() if key != 'plan'},
        'complete_rows': complete, 'private_package': private,
        'production_packages': packages, 'donors': production_plan['donors'],
        'donor_beginning': donor_beginning, 'p1_files': production_plan['p1_files'],
        'agda': production_plan['agda'], 'agda_sha256': production_plan['agda_sha256'],
        'filesystem_binary': production_plan['filesystem_binary'],
        'filesystem_binary_sha256': production_plan['filesystem_binary_sha256'],
        'agda_lib_sha256': production_plan['agda_lib_sha256'],
        'helper_sha256': helper_hashes(), 'wrapper_source_identity': wrapper_identity,
        'theorem_source_entries': theorem_entries,
        'include_order': ['wrapper-src', *map(str, donors), 'proof-src',
                          'upper-cache-src', 'lower-cache-src'],
        'flags': FLAGS+['+RTS', '-M9000M', '-c', '-s', '-RTS'],
        'child_wall_limit_seconds': auth['wall_limit_seconds']-120,
        'outer_wall_limit_seconds': auth['wall_limit_seconds']-20,
        'service_wall_limit_seconds': auth['wall_limit_seconds'],
        'manual_ledger_finish_required': True,
        'no_automatic_retry_or_resume': True,
        'full_layout_peak_gib': 4.9145,
        'final_theorem_memory_unknown_before_check': True}


def launch(auth_file):
    auth_path, auth = authorization(auth_file)
    require(not OUT.exists(), 'final output already exists; automatic retry is forbidden')
    require(OUT in registered_paths(), 'parent must register the final output before launch')
    no_active_work()
    ledger = Ledger(LEDGER_FILE); state = read_json(LEDGER_FILE)
    summary = Ledger.summary(state)
    require(summary['total_cpu_seconds'] == 172800 and not summary['outstanding'],
            'ledger total or outstanding reservation differs')
    terminal = production_terminal(state)
    require(summary['categories']['kernel']['available_cpu_seconds']
                >= auth['reservation_cpu_seconds'],
            'actual kernel availability cannot cover the final reservation')
    require(summary['categories']['assembly']['available_cpu_seconds'] >= ASSEMBLY_ALLOWANCE,
            'actual assembly availability cannot preserve the separate parent allowance')
    OUT.mkdir(); CONTROL.mkdir(); CHECK.mkdir(); PROOF.mkdir(); RECORDS.mkdir(); OUTER_RECORDS.mkdir()
    (OUT/'views').mkdir()
    shutil.copy2(ROOT/'othello.agda-lib', CHECK/'othello.agda-lib')
    shutil.copy2(ROOT/'othello.agda-lib', PROOF/'othello.agda-lib')
    target = CHECK/WRAPPER_RELATIVE; target.parent.mkdir(parents=True); target.write_text(WRAPPER)
    for name in HELPERS:
        shutil.copy2(ROOT/'tools'/name, CONTROL/name)
    plan = freeze_plan(auth_path, auth, terminal)
    require(sha(CHECK/'othello.agda-lib') == plan['agda_lib_sha256']
            and sha(PROOF/'othello.agda-lib') == plan['agda_lib_sha256'],
            'new proof-root Agda library file differs')
    atomic_json(OUT/'plan.json', plan)
    storage(plan)
    reservation = ledger.reserve('kernel', auth['reservation_cpu_seconds'],
                                 'final-problem2-outer')
    unit = 'othello6-final-problem2-compacting6-20261019.service'
    control_source = source_identity(CONTROL)
    job = {'format': 'othello-final-problem2-check6-job-v1', 'created_utc': utc(),
        'reservation': reservation, 'unit': unit, 'control_source': control_source,
        'outer_cpu_cap_seconds': auth['outer_cpu_cap_seconds'],
        'child_cpu_limit_seconds': auth['child_cpu_limit_seconds'],
        'service_wall_limit_seconds': auth['wall_limit_seconds'],
        'manual_ledger_finish_required': True}
    atomic_json(OUT/'job.json', job)
    args = ['systemd-run', '--user', '--no-block', '--unit='+unit,
        '--property=MemoryMax=12G', '--property=MemorySwapMax=0', '--property=LimitCORE=0',
        '--property=CPUQuota=100%', '--property=TasksMax=128',
        '--property=KillMode=control-group',
        '--property=RuntimeMaxSec='+str(auth['wall_limit_seconds']),
        '--property=WorkingDirectory='+str(CONTROL),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3', '-B', str(CONTROL/'final_problem2_compacting6.py'), 'supervise']
    done = subprocess.run(args, capture_output=True, text=True)
    atomic_json(OUT/'dispatch.json', {'argv': args, 'exit_code': done.returncode,
        'stdout': done.stdout, 'stderr': done.stderr})
    require(done.returncode == 0, 'systemd dispatch failed; reservation remains outstanding')
    print(json.dumps({'unit': unit, 'reservation': reservation,
        'manual_finish_record': str(OUTER_RECORDS/'final-problem2-outer.json')}, indent=2))


def main():
    require(len(sys.argv) >= 2, 'action required')
    if sys.argv[1] == 'launch':
        require(len(sys.argv) == 3, 'launch requires AUTHORIZATION.json')
        launch(Path(sys.argv[2])); return 0
    if sys.argv[1] == 'worker':
        require(len(sys.argv) == 2, 'worker takes no arguments')
        worker(); return 0
    if sys.argv[1] == 'supervise':
        require(len(sys.argv) == 2, 'supervise takes no arguments')
        return supervise()
    raise ValueError('action must be launch, worker, or supervise')


if __name__ == '__main__':
    raise SystemExit(main())
