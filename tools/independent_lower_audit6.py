#!/usr/bin/env python3
"""Read-only audit of the independent-check/real-citation recovery pilot."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import assembly6
from independent_lower6 import negative_ok
from lower_pilot6 import WARNING
from provenance import digest_entries, source_identity
from run_job import atomic_json, utc


def audit(previous):
    old = json.loads((previous/'final.json').read_text())
    proof = json.loads((previous/'phase-records.json').read_text())
    root = Path(old['check_root'])
    pool = assembly6.interfaces(root)
    identity = source_identity(root)
    if (old['status'] == 'running' or old['prefix_parts_reused'] != 114 or not old['heldout_unmeasured'] or
            old['initial_problem2_proved'] or old['production_authorized'] or
            old['postulates'] != 0 or not old['conditional_part_premises_explicit'] or
            assembly6.sha(previous/'final.json') != proof['final_sha256'] or
            assembly6.sha(previous/'independent.json') != proof['independent_sha256'] or
            pool != proof['final_interfaces'] or digest_entries(pool) != proof['final_interfaces_sha256'] or
            identity['source_sha256'] != old['source_sha256'] or
            identity['agda_source_sha256'] != old['agda_source_sha256'] or
            not old['donor_unchanged'] or not old['generated_source_unchanged']):
        raise ValueError('result is incomplete or its source/cache/proof boundary changed')
    donor = Path(old['donor'])
    if (source_identity(donor)['source_sha256'] != old['donor_source_sha256'] or
            digest_entries(assembly6.interfaces(donor)) != old['donor_interfaces_sha256'] or
            assembly6.sha(Path(old['machine']['agda_path'])) != old['machine']['agda_sha256']):
        raise ValueError('original source, accepted prefix or compiler changed')
    for name, expected in old['source_hashes'].items():
        text = (root/name).read_text()
        if (assembly6.sha(root/name) != expected or
                '--safe --without-K --cubical-compatible' not in text or
                any(word in text for word in ('postulate', 'TERMINATING', 'NO_POSITIVITY', '{!')) or
                text.count(WARNING) != 1):
            raise ValueError('new safe proof source changed')
    parts, raw_bytes, gzip_bytes = [], 0, 0
    for phase in old['phases']:
        label = phase['label']
        record = proof['records'][label]
        record_path = previous/'records'/(label+'.json')
        if (assembly6.sha(record_path) != proof['record_hashes'][label] or json.loads(record_path.read_text()) != record or
                not record['source_unchanged'] or not record['expected_source_matches'] or not record['own_target_cold'] or
                record['source_sha256'] != old['source_sha256'] or
                record['executable_sha256'] != old['machine']['agda_sha256'] or
                not all(flag in record['argv'] for flag in ('--safe', '--without-K', '--cubical-compatible', '--save-metas')) or
                any(WARNING in flag for flag in record['argv']) or
                phase['cache_changes'] or phase['unexpected_interfaces']):
            raise ValueError('phase proof receipt changed: '+label)
        heap, rss = (2500, 3) if phase['root_assembly'] else (1350, 1.5)
        if record['argv'][-4] != f'-M{heap}M' or record['rss_stop_threshold_gib'] != rss:
            raise ValueError('resource classification differs from the predeclared caps')
        if phase['accepted']:
            row = proof['log_archives'][label]
            path = previous/'records'/row['archive_name']
            if assembly6.sha(path) != row['archive_sha256']:
                raise ValueError('archive changed')
            raw = gzip.decompress(path.read_bytes())
            gzip_bytes += path.stat().st_size
            raw_bytes += len(raw)
            if (not record['accepted'] or len(raw) != row['original_bytes'] or
                    hashlib.sha256(raw).hexdigest() != row['original_sha256'] or
                    row['original_sha256'] != proof['log_hashes'][label] or
                    len(phase['own_interfaces']) != 1 or
                    any(pool.get(name) != expected for name, expected in phase['own_interfaces'].items())):
                raise ValueError('accepted evidence is not exactly recoverable')
        else:
            path = previous/'records'/(label+'.log')
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != proof['log_hashes'][label]:
                raise ValueError('negative/failure log changed')
        if phase['negative_fixture'] and not negative_ok(record, raw.decode(), [], []):
            raise ValueError('negative did not reject the intended false Bool')
        if label.startswith('conditional-part'):
            parts.append(phase)
    if old['accepted']:
        expected = ['checker', 'FalseTerminal', 'MissingCitation']
        expected += [f'conditional-part{index}' for index in (114, 115, 116, 117)]
        expected += ['root-assembly']
        if ([phase['label'] for phase in old['phases']] != expected or
                old['conditional_parts'] != [114, 115, 116, 117] or old['checked_lower_roots'] != 1 or
                not old['phases'][-1]['accepted'] or
                any(not phase['expected_outcome_met'] for phase in old['phases'])):
            raise ValueError('claimed bound lacks a checked obligation')
    return dict(format='othello-independent-lower6-audit-v1', status='complete', created_utc=utc(),
        accepted=old['accepted'], pilot_status=old['status'], previous=str(previous.resolve()),
        report_sha256=proof['final_sha256'], phase_audit_sha256=assembly6.sha(previous/'phase-records.json'),
        source_sha256=identity['source_sha256'], agda_source_sha256=identity['agda_source_sha256'],
        interfaces=len(pool), interfaces_sha256=digest_entries(pool),
        source_hashes=old['source_hashes'], root=old['root'], checked_lower_roots=old['checked_lower_roots'],
        reused_prefix_parts=114, conditional_parts=old['conditional_parts'],
        original_prefix_unchanged=True, compiler_unchanged=True, exact_accepted_logs_recovered=True,
        accepted_raw_log_bytes=raw_bytes, accepted_gzip_bytes=gzip_bytes,
        nested_kernel_cpu_seconds=old['measured_kernel_cpu_seconds'],
        maximum_conditional_part_rss_gib=max([phase['peak_rss_gib'] for phase in parts] or [0]),
        root_assembly=next((phase for phase in old['phases'] if phase['root_assembly']), None),
        negatives_rejected=sum(phase['negative_fixture'] and phase['expected_outcome_met'] for phase in old['phases']),
        postulates=0, heldout_unmeasured=True, initial_problem2_proved=False, production_authorized=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    args = p.parse_args()
    result = audit(args.previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, result)
    print(json.dumps({key: result[key] for key in ('status', 'pilot_status', 'checked_lower_roots',
        'conditional_parts', 'maximum_conditional_part_rss_gib', 'exact_accepted_logs_recovered')}))
