#!/usr/bin/env python3
"""Read-only verification of a stopped lower prefix and its recoverable logs."""
import argparse
import gzip
import json
from pathlib import Path

import assembly6
from closed_roots6 import closure_entries
import global_assembly6 as assembly
from provenance import digest_entries, source_identity
from run_job import atomic_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    previous = args.previous.resolve()
    report = json.loads((previous/'final.json').read_text())
    audit = json.loads((previous/'phase-records.json').read_text())
    if (report['status'] != 'part-failed' or report['last_attempted_check']['label'] != 'group0-part122' or
            len(report['phases']) != 124 or report['checked_sample_lower_roots'] != 0 or
            audit['final_sha256'] != assembly6.sha(previous/'final.json') or
            audit['lower_sha256'] != assembly6.sha(previous/'lower.json') or
            source_identity(previous/'check')['source_sha256'] != report['source_sha256'] or
            assembly6.interfaces(previous/'check') != audit['final_interfaces']):
        raise ValueError('different stopped prefix')
    donor = Path(report['donor'])
    if (source_identity(donor)['source_sha256'] != report['donor_source_sha256'] or
            digest_entries(assembly6.interfaces(donor)) != report['donor_interfaces_sha256']):
        raise ValueError('upper donor changed')
    raw_bytes = compressed_bytes = 0
    for label, row in audit['log_archives'].items():
        path = previous/'records'/row['archive_name']
        if assembly6.sha(path) != row['archive_sha256']:
            raise ValueError('accepted compressed log changed')
        import hashlib
        raw = gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest() != row['original_sha256'] or len(raw) != row['original_bytes']:
            raise ValueError('accepted log no longer exactly recoverable')
        raw_bytes += len(raw)
        compressed_bytes += path.stat().st_size
    for label in ('negative-terminal-lower', 'group0-part122'):
        if assembly6.sha(previous/'records'/(label+'.log')) != audit['log_hashes'][label]:
            raise ValueError('raw negative/failure log changed')
    for name, digest in report['generated_source_hashes'].items():
        if assembly6.sha(previous/'check'/name) != digest:
            raise ValueError('generated source changed')
    if assembly6.sha(args.plan) != report['plan_sha256']:
        raise ValueError('factored sample changed')
    plan = json.loads(args.plan.read_text())
    parts, owners = assembly.partition(closure_entries(plan, report['groups'][0]['roots']), 32000, 150)
    covered = [dict(state=state, part=owners[state], group=0) for state in report['groups'][0]['roots']
               if owners[state] < 122]
    result = dict(format='othello-lower-verify6-v1', status='complete',
        previous=str(previous), previous_report_sha256=assembly6.sha(previous/'final.json'),
        previous_audit_sha256=assembly6.sha(previous/'phase-records.json'),
        source_sha256=report['source_sha256'], agda_source_sha256=report['agda_source_sha256'],
        interfaces_sha256=digest_entries(audit['final_interfaces']),
        accepted_log_archives=len(audit['log_archives']), exact_logs_recovered=True,
        raw_log_bytes=raw_bytes, compressed_log_bytes=compressed_bytes,
        donor_unchanged=True, generated_sources_unchanged=True,
        source_covered_roots=covered, roots_have_exported_facts_only=True,
        original_root_guarantees_checked=0, source_hashes=report['generated_source_hashes'],
        initial_problem2_proved=False, production_authorized=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, result)
    print(json.dumps({key: result[key] for key in ('status', 'accepted_log_archives',
        'exact_logs_recovered', 'source_covered_roots', 'interfaces_sha256')}))


if __name__ == '__main__':
    main()
