#!/usr/bin/env python3
"""Audit a completed root-local pilot without evaluating any Agda term again."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import assembly6
import lower_pilot6 as pilot
from provenance import digest_entries, source_identity
from run_job import atomic_json, utc


def audit(previous):
    previous = previous.resolve()
    report = json.loads((previous/'final.json').read_text())
    proof_audit = json.loads((previous/'phase-records.json').read_text())
    guard = json.loads((previous/'old-prefix-guard.json').read_text())
    if (report['status'] == 'running' or report['layout']['root_index'] != 4 or
            len(report['roots']) != 1 or report['heldout_groups'] or
            not report['layout']['original_heldout_kernel_unmeasured'] or
            not guard['unchanged'] or report['initial_problem2_proved'] or report['production_authorized']):
        raise ValueError('not a completed bounded training stress pilot')
    root = Path(report['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    if (identity['source_sha256'] != report['source_sha256'] or
            identity['agda_source_sha256'] != report['agda_source_sha256'] or
            pool != proof_audit['final_interfaces'] or
            digest_entries(pool) != proof_audit['final_interfaces_sha256'] or
            assembly6.sha(previous/'final.json') != proof_audit['final_sha256'] or
            assembly6.sha(previous/'lower.json') != proof_audit['lower_sha256']):
        raise ValueError('source, interfaces or result changed')
    donor = Path(report['donor'])
    if (source_identity(donor)['source_sha256'] != report['donor_source_sha256'] or
            digest_entries(assembly6.interfaces(donor)) != report['donor_interfaces_sha256'] or
            assembly6.sha(Path(report['machine']['agda_path'])) != report['machine']['agda_sha256']):
        raise ValueError('original proof donor or compiler changed')
    for name, digest in report['generated_source_hashes'].items():
        source = (root/name).read_text()
        if (assembly6.sha(root/name) != digest or
                '--safe --without-K --cubical-compatible' not in source or
                source.count(pilot.WARNING) != 1):
            raise ValueError('generated source or safe options changed')
    checked, raw_bytes, packed_bytes = [], 0, 0
    for phase in report['phases']:
        label = phase['label']
        record = proof_audit['records'][label]
        path = previous/'records'/(label+'.json')
        if (assembly6.sha(path) != proof_audit['record_hashes'][label] or
                json.loads(path.read_text()) != record or
                not record['source_unchanged'] or not record['expected_source_matches'] or
                not record['own_target_cold'] or record['source_sha256'] != report['source_sha256'] or
                record['executable_sha256'] != report['machine']['agda_sha256'] or
                record['rss_stop_threshold_gib'] != phase['rss_limit_gib'] or
                record['argv'][-4] != f"-M{phase['heap_mib']}M" or
                any(pilot.WARNING in arg for arg in record['argv']) or
                not all(flag in record['argv'] for flag in ('--safe', '--without-K', '--cubical-compatible', '--save-metas')) or
                phase['cache_changes'] or phase['unexpected_interfaces'] or phase['proof_issues']):
            raise ValueError('phase evidence changed: '+label)
        if phase['accepted']:
            row = proof_audit['log_archives'][label]
            log = previous/'records'/row['archive_name']
            if assembly6.sha(log) != row['archive_sha256']:
                raise ValueError('archived log changed')
            raw = gzip.decompress(log.read_bytes())
            raw_bytes += len(raw)
            packed_bytes += log.stat().st_size
            if (hashlib.sha256(raw).hexdigest() != row['original_sha256'] or
                    row['original_sha256'] != proof_audit['log_hashes'][label] or
                    len(raw) != row['original_bytes'] or not record['accepted'] or
                    len(phase['own_interfaces']) != 1 or
                    any(pool.get(name) != digest for name, digest in phase['own_interfaces'].items())):
                raise ValueError('accepted evidence not exactly recoverable')
        else:
            log = previous/'records'/(label+'.log')
            raw = log.read_bytes()
            if hashlib.sha256(raw).hexdigest() != proof_audit['log_hashes'][label]:
                raise ValueError('failure log changed')
        if phase['negative_fixture']:
            if not pilot.negative_rejected(record, [], [], raw.decode()):
                raise ValueError('negative fixture did not reject the false Boolean')
        elif '-part' in label:
            checked.append(phase)
    accepted_parts = [phase for phase in checked if phase['accepted']]
    if [phase['label'] for phase in accepted_parts] != [f'group0-part{i}' for i in range(len(accepted_parts))]:
        raise ValueError('accepted prefix has a gap')
    if report['accepted'] and (len(accepted_parts) != report['groups'][0]['parts'] or
            report['accepted_roots'] != report['roots'] or not report['exact_accepted_root_coverage'] or
            report['phases'][-1]['label'] != 'all-lower'):
        raise ValueError('complete result lacks exact coverage')
    return dict(format='othello-lower-local-audit6-v1', status='complete', created_utc=utc(),
        previous=str(previous), accepted=report['accepted'], pilot_status=report['status'],
        report_sha256=proof_audit['final_sha256'], phase_audit_sha256=assembly6.sha(previous/'phase-records.json'),
        old_prefix_guard_sha256=assembly6.sha(previous/'old-prefix-guard.json'),
        source_sha256=identity['source_sha256'], agda_source_sha256=identity['agda_source_sha256'],
        interfaces_sha256=digest_entries(pool), interfaces=len(pool),
        root=report['roots'][0], root_index=report['layout']['root_index'],
        accepted_parts=len(accepted_parts), attempted_parts=len(checked), phases=len(report['phases']),
        checked_lower_roots=report['checked_sample_lower_roots'],
        nested_kernel_cpu_seconds=report['measured_kernel_cpu_seconds'],
        maximum_part_rss_gib=max([phase['peak_rss_gib'] for phase in checked] or [0]),
        accepted_logs_exactly_recovered=True, accepted_raw_log_bytes=raw_bytes, accepted_gzip_bytes=packed_bytes,
        original_donor_unchanged=True, old_accepted_prefix_unchanged=True,
        source_hashes=report['generated_source_hashes'],
        heldout_unmeasured=True, initial_problem2_proved=False, production_authorized=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = audit(args.previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, result)
    print(json.dumps({key: result[key] for key in ('status', 'pilot_status', 'accepted_parts',
        'checked_lower_roots', 'maximum_part_rss_gib', 'accepted_logs_exactly_recovered')}))
