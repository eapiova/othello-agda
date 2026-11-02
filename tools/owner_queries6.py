#!/usr/bin/env python3
"""Reuse the accepted list checker; check the stress imports eight at a time."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import assembly6
import owner_cuts6 as cuts
import owner_lists6 as lists
from provenance import digest_entries, source_identity
from run_job import positive

PREFIX = 'Tests.OwnerQueries6'
DIRECTORY = 'src/Tests/OwnerQueries6'


def generated(donor):
    return lists.generated(donor, namespace=PREFIX, generated_directory=DIRECTORY, batch_size=8, reuse_helpers=True)


def verified_prefix(args, original_pool, machine, sources):
    previous = args.prefix_donor.resolve()
    if assembly6.sha(previous/'final.json') != args.expected_prefix_sha256:
        raise ValueError('list-checker prefix report differs')
    report = json.loads((previous/'final.json').read_text())
    root = Path(report['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    original_sources, _, _ = lists.generated(Path(json.loads((Path(report['previous'])/'final.json').read_text())['check_root']))
    if (report['format'] != 'othello-owner-lists6-v1' or report['status'] != 'phase-failed' or report['accepted'] or
            [p['label'] for p in report['phases']] != ['Lookup', 'Fixtures', 'MissingOwner', 'Inputs', 'Chunk0'] or
            [p['expected_outcome_met'] for p in report['phases']] != [True, True, True, True, False] or
            report['phases'][-1]['record']['exit_code'] != 251 or report['phases'][-1]['record']['stop_reason'] or
            report['borrowed_interfaces'] != original_pool or report['machine'] != machine or
            report['previous_report_sha256'] != args.expected_previous_sha256 or
            not report['donor_unchanged'] or not report['generated_sources_unchanged'] or
            identity['source_sha256'] != report['source_sha256'] or
            identity['agda_source_sha256'] != report['agda_source_sha256'] or
            pool != report['final_interfaces'] or digest_entries(pool) != report['interfaces_sha256'] or
            report['generated_source_hashes'] != cuts.pilot.source_hashes(original_sources) or
            any(assembly6.sha(root/n) != d for n, d in report['generated_source_hashes'].items())):
        raise ValueError('accepted list checker, literal or original obligations changed')
    before = dict(original_pool)
    for phase in report['phases']:
        record = phase['record']
        receipt = previous/'records'/(phase['label']+'.json')
        if (assembly6.sha(receipt) != phase['record_sha256'] or json.loads(receipt.read_text()) != record or
                record['borrowed_interfaces_sha256'] != digest_entries(before) or
                phase['cache_changes'] or phase['unexpected_interfaces'] or
                not record['source_unchanged'] or not record['expected_source_matches'] or
                record['source_sha256'] != identity['source_sha256'] or not record['own_target_cold'] or
                record['executable_sha256'] != machine['agda_sha256'] or
                not all(f in record['argv'] for f in assembly6.FLAGS+['--save-metas', '-M2500M']) or
                record['rss_stop_threshold_gib'] != 3):
            raise ValueError('list-checker prefix receipt differs')
        if phase['archived_log']:
            packed = phase['archived_log']
            path = previous/'records'/packed['archive_name']
            if assembly6.sha(path) != packed['archive_sha256']:
                raise ValueError('list-checker prefix archive changed')
            raw = gzip.decompress(path.read_bytes())
        else:
            raw = (previous/'records'/(phase['label']+'.log')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != phase['raw_log_sha256'] or len(raw) != record['log_bytes']:
            raise ValueError('list-checker prefix log changed')
        if phase['negative_fixture']:
            if not lists.rejected_missing(record, raw.decode(), phase['own_interfaces']):
                raise ValueError('missing citation owner was not properly rejected')
        elif phase['expected_outcome_met']:
            if not record['accepted'] or len(phase['own_interfaces']) != 1:
                raise ValueError('generic prefix was not accepted by Agda')
        elif record['accepted'] or phase['own_interfaces']:
            raise ValueError('failed batch was incorrectly adopted')
        before.update(phase['own_interfaces'])
    if before != pool or len(pool) != len(original_pool)+3:
        raise ValueError('unrecorded list-checker prefix interface')
    return dict(previous=str(previous), report_sha256=args.expected_prefix_sha256, root=str(root),
        identity=identity, interfaces=pool, interfaces_sha256=digest_entries(pool),
        original_phases=report['phases'], skip_phases=0, missing_owner_rejection_audited=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'prefix-donor', 'output', 'runs-root'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-previous-sha256', required=True)
    parser.add_argument('--expected-prefix-sha256', required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(parser.parse_args(), generator=generated, directory=DIRECTORY,
        report_format='othello-owner-queries6-v1', negative_guard=lists.rejected_missing,
        prefix_validator=verified_prefix)['accepted'] else 2)
