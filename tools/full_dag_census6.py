#!/usr/bin/env python3
"""Bounded census of the initial lower certificate DAG, with no state dump.

This native measurement never supplies an Agda proof premise. Partial counts
remain censored; an incomplete DAG cannot authorize production. The original
binary and TT snapshot are used read-only with source/config/checksum guards.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from provenance import source_identity
from rewrite_dedup6 import closed
from run_job import atomic_json, utc
import solve6

LABEL = 'native-lower20-resume-20261006'
EXPECTED_TT = '7886f35fc835b64ad458e7ccb91475200bf44e4065e8d707d1a6ebcee61497d8'


def run(args):
    donor = args.donor.resolve()
    if donor.name != 'six-'+LABEL:
        raise ValueError('requires the original closed lower TT donor')
    closed(LABEL)
    identity = source_identity(donor)
    receipt = donor/'results'/(LABEL+'.json')
    record = json.loads(receipt.read_text())
    table = donor/'results/native6/warm-2.tt'
    sidecar = Path(str(table)+'.json')
    metadata = json.loads(sidecar.read_text())
    binary = donor/'results/native6/solve6'
    source = donor/'tools/native6/solve6.c'
    config = dict(tt_bits=25, small=4, deep_order=5)
    if (not record['accepted'] or not record['finished_utc'] or not record['source_unchanged'] or
            not record['expected_source_matches'] or identity['source_sha256'] != record['source_sha256'] or
            metadata['format'] != 'native6-tt-v1' or metadata['config'] != config or
            metadata['cache_sha256'] != EXPECTED_TT or solve6.sha256(table) != EXPECTED_TT or
            metadata['cache_bytes'] != table.stat().st_size or
            metadata['build']['binary_sha256'] != solve6.sha256(binary) or
            metadata['build']['source_sha256'] != solve6.sha256(source) or
            solve6.sha256(source) != solve6.sha256(solve6.SOURCE)):
        raise ValueError('native source, binary, closed receipt or full-key TT provenance differs')
    guards = {str(receipt): solve6.sha256(receipt), str(sidecar): solve6.sha256(sidecar),
              str(binary): solve6.sha256(binary), str(source): solve6.sha256(source)}
    options = {'position': 'initial', 'turn': 'black', 'direction': 'lower',
        'threshold': 4, 'frontier-discs': 36, 'max-states': 100000000,
        'max-nodes': 1000000000000, 'max-memory-mb': 8192, 'max-cpu-seconds': 750,
        'tt-bits': 25, 'small': 4, 'deep-order': 5, 'emit-states': 0, 'load-tt': str(table)}
    argv = [str(binary), 'frontier']
    for name, value in options.items():
        argv += ['--'+name, str(value)]
    report = dict(format='othello-full-dag-census6-v1', status='running', created_utc=utc(),
        trust='untrusted native measurement; no proof premise', donor_source=identity,
        table_sha256=EXPECTED_TT, table_bytes=table.stat().st_size, guards=guards,
        command=argv, request=options, initial_problem2_proved=False,
        optimal_pair_proved=False, production_authorized=False, states_emitted=False)
    atomic_json(args.output, report)
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=900)
    report.update(exit_code=completed.returncode, stderr=completed.stderr, raw_stdout=completed.stdout)
    if len(completed.stdout) > 1024**2:
        raise ValueError('counts-only census unexpectedly emits large data')
    counts = json.loads(completed.stdout)
    if (not isinstance(counts, dict) or 'states' in counts or counts['direction'] != 'lower' or
            counts['threshold'] != 4 or counts['frontier_discs'] != 36 or
            counts['unique_dag_nodes'] > 100000000 or counts['tt_bits'] != 25):
        raise ValueError('native census differs from the bounded counts-only request')
    if (source_identity(donor) != identity or
            any(solve6.sha256(Path(name)) != digest for name, digest in guards.items()) or
            solve6.sha256(table) != EXPECTED_TT):
        raise ValueError('original closed donor or TT bytes changed')
    complete = bool(completed.returncode == 0 and counts['complete'] and counts['root_validated'] and
                    counts['root_holds'] and not counts['oracle_aborted'] and not counts['count_overflow'])
    report.update(status='complete-native-census' if complete else 'censored-native-census',
        finished_utc=utc(), native_complete=complete, counts=counts,
        donor_unchanged=True, table_unchanged=True,
        partial_counts_are_lower_bounds=not complete,
        incomplete_count_extrapolated=False, initial_problem2_proved=False,
        production_authorized=False)
    atomic_json(args.output, report)
    print(json.dumps({key: report[key] for key in ('status', 'native_complete',
        'partial_counts_are_lower_bounds', 'production_authorized')}))
    print(json.dumps(counts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args())
