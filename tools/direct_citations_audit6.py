#!/usr/bin/env python3
"""Read-only verification of direct citation assembly and its exact cache donor."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

import assembly6
from independent_lower_audit6 import audit as audit_independent
from lower_pilot6 import WARNING, cache_changes
from provenance import digest_entries, source_identity
from run_job import atomic_json, utc


def audit(previous):
    final_path = previous/'final.json'
    result = json.loads(final_path.read_text())
    if result['status'] == 'running' or result['certificate_parts_rechecked'] or result['postulates']:
        raise ValueError('incomplete run or different proof boundary')
    if result['initial_problem2_proved'] or result['production_authorized'] or not result['heldout_unmeasured']:
        raise ValueError('unsupported scope claim')
    root = Path(result['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    if (identity['source_sha256'] != result['source_sha256'] or
            identity['agda_source_sha256'] != result['agda_source_sha256'] or
            pool != result['final_interfaces'] or digest_entries(pool) != result['interfaces_sha256']):
        raise ValueError('checked source or interface changed')
    donor = Path(result['previous'])
    audit_independent(donor)
    old = json.loads((donor/'final.json').read_text())
    donor_pool = assembly6.interfaces(Path(old['check_root']))
    if (assembly6.sha(donor/'final.json') != result['previous_report_sha256'] or
            digest_entries(donor_pool) != result['donor_interfaces_sha256'] or
            source_identity(Path(old['check_root']))['source_sha256'] != result['donor_source_sha256'] or
            cache_changes(result['borrowed_interfaces'], pool) or
            assembly6.sha(Path(result['machine']['agda_path'])) != result['machine']['agda_sha256']):
        raise ValueError('original donor, borrowed cache or binary differs')
    for name, expected in result['source_hashes'].items():
        text = (root/name).read_text()
        if (assembly6.sha(root/name) != expected or
                '--safe --without-K --cubical-compatible' not in text or text.count(WARNING) != 1 or
                any(word in text for word in ('postulate', 'TERMINATING', 'NO_POSITIVITY', '{!'))):
            raise ValueError('safe generated source changed')
    helper = result['reused_helper']
    if helper:
        first = Path(helper['previous'])
        first_report = json.loads((first/'final.json').read_text())
        if (assembly6.sha(first/'final.json') != helper['report_sha256'] or
                source_identity(Path(first_report['check_root']))['source_sha256'] != helper['source_sha256'] or
                assembly6.interfaces(Path(first_report['check_root'])) != helper['original_interfaces'] or
                first_report['phases'][0] != helper['original_phase'] or
                pool[helper['name']] != helper['sha256']):
            raise ValueError('checked helper donor changed')
        phases = [(first, helper['original_phase'])]
    else:
        phases = []
    phases += [(previous, phase) for phase in result['phases']]
    cpu = 0.0
    archives = 0
    for directory, phase in phases:
        label, record = phase['label'], phase['record']
        path = directory/'records'/(label+'.json')
        if (assembly6.sha(path) != phase['record_sha256'] or json.loads(path.read_text()) != record or
                not record['source_unchanged'] or not record['expected_source_matches'] or
                record['executable_sha256'] != result['machine']['agda_sha256'] or
                not all(flag in record['argv'] for flag in ('--safe', '--without-K', '--cubical-compatible', '--save-metas')) or
                any(WARNING in flag for flag in record['argv']) or
                record['argv'][-4] != '-M2500M' or record['rss_stop_threshold_gib'] != 3 or
                not record['own_target_cold'] or phase['cache_changes'] or phase['unexpected_interfaces']):
            raise ValueError('phase provenance differs: '+label)
        if phase['archived_log']:
            row = phase['archived_log']
            path = directory/'records'/row['archive_name']
            if assembly6.sha(path) != row['archive_sha256']:
                raise ValueError('archived log changed')
            raw = gzip.decompress(path.read_bytes())
            if len(raw) != row['original_bytes'] or hashlib.sha256(raw).hexdigest() != row['original_sha256']:
                raise ValueError('log does not recover exactly')
            archives += 1
        else:
            raw = (directory/'records'/(label+'.log')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != phase['raw_log_sha256']:
            raise ValueError('raw phase log changed')
        if phase['negative_fixture']:
            text = raw.decode()
            if (record['accepted'] or record['stop_reason'] or phase['own_interfaces'] or
                    re.findall(r'error: \[([^]]+)\]', text) != ['UnequalTerms'] or
                    not re.search(r'\b(true\s+and\s+false|false\s+and\s+true)\s+are not equal at type Bool', text)):
                raise ValueError('wrong-owner fixture did not reject the intended false claim')
        if not phase['negative_fixture'] and record['accepted']:
            if any(pool.get(name) != value for name, value in phase['own_interfaces'].items()):
                raise ValueError('accepted phase interface changed')
        if directory == previous:
            cpu += record['cpu_seconds']
    if abs(cpu-result['nested_cpu_seconds']) > 1e-6:
        raise ValueError('nested CPU total differs')
    expected = ['Fixtures', 'WrongOwner', 'Imports', 'Root'] if helper else ['Coverage', 'Fixtures', 'WrongOwner', 'Imports', 'Root']
    complete = bool([phase['label'] for phase in result['phases']] == expected and
                    all(phase['expected_outcome_met'] for phase in result['phases']))
    if result['accepted'] and (not complete or result['checked_lower_roots'] != 1):
        raise ValueError('root claim lacks a checked obligation')
    return dict(format='othello-direct-citations6-audit-v1', status='complete', created_utc=utc(),
        accepted=result['accepted'], pilot_status=result['status'], checked_lower_roots=result['checked_lower_roots'],
        report_sha256=assembly6.sha(final_path), source_sha256=identity['source_sha256'],
        agda_source_sha256=identity['agda_source_sha256'], interfaces=len(pool),
        interfaces_sha256=digest_entries(pool), certificate_parts_rechecked=0,
        accepted_logs_exactly_recovered=archives, donor_unchanged=True, helper_donor_unchanged=True,
        nested_cpu_seconds=cpu, phases=[dict(label=p['label'], accepted=p['record']['accepted'],
        cpu_seconds=p['record']['cpu_seconds'], wall_seconds=p['record']['wall_seconds'],
        peak_rss_gib=p['record']['peak_rss_gib'], stop_reason=p['record']['stop_reason']) for p in result['phases']],
        postulates=0, initial_problem2_proved=False, production_authorized=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = audit(args.previous.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, result)
    print(json.dumps(result))
