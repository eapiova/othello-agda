#!/usr/bin/env python3
"""Bounded sharing experiments. Native statistics never establish a theorem.

AI-assisted. Run expensive actions inside a reserved run_job/remote6 envelope.
The A/B uses a frozen, previously checked core to avoid concurrent source edits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

import bench6
from provenance import source_files, source_identity
from run_job import atomic_json, run_job
import shared6

CS = 0.0010171599998201899
LOWER_CASES = [
    ('l000', 'b002002000222222222022111001110001000', 43.289418),
    ('l001', 'b022222021122021112021110001000000000', 26.121601),
    ('l002', 'b202220220200222110221201001100001000', 16.882786),
]


def terminal_projection(profile):
    cases = [c for c in profile['cases'] if c['frontier_discs'] == 36]
    if not cases or len(cases) != len(profile['selected_states']):
        raise ValueError('terminal sample is missing cases')
    if any(c['status'] != 'complete' or not c['native']['complete'] for c in cases):
        raise ValueError('censored terminal sample; no uncensored projection available')
    nodes = [c['native']['tree_nodes_S'] for c in cases]
    population = profile['sample_population_L']
    mean = statistics.mean(nodes)
    se = statistics.stdev(nodes) / math.sqrt(len(nodes)) if len(nodes) > 1 else None
    return {
        'format': 'othello-terminal-projection6-v2',
        'trust': 'statistical measurement only; not a proof or GO decision',
        'sample_seed': profile['sample_seed'], 'sample_size': len(cases),
        'population_distinct_leaves': population,
        'population_kind': profile.get('sample_population_kind', 'distinct raw frontier states'),
        'coefficient_cpu_seconds_per_node': CS,
        'coefficient_source': 'unchanged upper fit, validated on lower fixtures',
        'full_terminal_samples_S': sum(nodes), 'largest_sample_S': max(nodes),
        'nominal_variable_cpu_hours': population * mean * CS / 3600,
        'nominal_variable_cpu_hours_standard_error':
            None if se is None else population * se * CS / 3600,
        'nominal_encoded_GiB': population * statistics.mean(
            c['encoded_bytes'] for c in cases) / 2**30,
        'censored_other_cuts': [
            {'id': c['row']['id'], 'cut': c['frontier_discs'], 'status': c['status']}
            for c in profile['cases'] if c['status'] != 'complete'],
        'exclusions': ['sharing', 'cold imports', 'skeleton', 'assembly',
                       'generation', 'parallel throughput', 'verification'],
    }


def ab(args):
    source_identity(args.source_root)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'format': 'othello-shared-ab6-v2', 'cases': [],
              'baseline_scope': 'three cold LocalCertificate lower checks',
              'scope': 'sampled certificates only; no initial-board theorem'}
    atomic_json(output / 'ab.json', report)
    for ident, state_text, baseline in LOWER_CASES:
        native = json.loads((args.input / f'native-{ident}-c36.json').read_text())
        state = bench6.decode(state_text)
        graph = shared6.graph_from_native(native, state, 'lower', 4)
        for mode, indegree in [('shared', 2), ('tree', 10**9)]:
            entries, stats = shared6.layered(graph, state, indegree)
            if stats['expanded_tree_nodes'] != native['tree_nodes_S']:
                raise ValueError('expanded node count differs from native input')
            if not shared6.replay(entries, state, 'lower', 4):
                raise ValueError('independent replay rejected fixture')
            label = f'shared6-{ident}-c36-lower-{mode}'
            root = output / label
            root.mkdir()
            for name, data in source_files(args.source_root):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            path = root / 'src/Tests/Bench6/SharedCheck.agda'
            path.write_text(shared6.agda_text(state_text, 'lower', 4,
                                             shared6.encode(entries)))
            manifest = bench6.refresh_manifest(root)
            record = run_job(label, [args.agda, '--no-libraries', '--safe',
                '--without-K', '--cubical-compatible', '-i', 'src',
                'src/Tests/Bench6/SharedCheck.agda', '+RTS', '-M1200M', '-RTS'],
                output / 'records', root=root, expected_source_sha256=manifest['source_sha256'],
                cpu_limit=160, timeout=240, rss_limit_gib=1.5, log_limit_mib=2)
            case = dict(stats, label=label, mode=mode, id=ident,
                        source_sha256=manifest['source_sha256'],
                        native_sha256=hashlib.sha256(json.dumps(native, sort_keys=True).encode()).hexdigest(),
                        accepted=record['accepted'], cpu_seconds=record['cpu_seconds'],
                        peak_rss_gib=record['peak_rss_gib'], stop_reason=record['stop_reason'],
                        speedup_against_original_tree=baseline / record['cpu_seconds'])
            report['cases'].append(case)
            atomic_json(output / 'ab.json', report)
    report['all_accepted'] = all(c['accepted'] for c in report['cases'])
    report['paired_speedups'] = {
        ident: next(c['cpu_seconds'] for c in report['cases'] if c['id'] == ident and c['mode'] == 'tree') /
               next(c['cpu_seconds'] for c in report['cases'] if c['id'] == ident and c['mode'] == 'shared')
        for ident, _, _ in LOWER_CASES}
    atomic_json(output / 'ab.json', report)
    return report['all_accepted']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    proj = sub.add_parser('projection')
    proj.add_argument('profile', type=Path)
    proj.add_argument('output', type=Path)
    pilot = sub.add_parser('ab')
    pilot.add_argument('--source-root', type=Path, required=True)
    pilot.add_argument('--input', type=Path, required=True)
    pilot.add_argument('--output', type=Path, required=True)
    pilot.add_argument('--agda', required=True)
    args = parser.parse_args()
    if args.action == 'projection':
        raw = args.profile.read_bytes()
        result = terminal_projection(json.loads(raw))
        result['source_report_sha256'] = hashlib.sha256(raw).hexdigest()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(args.output, result)
        print(json.dumps(result))
        return 0
    return 0 if ab(args) else 1


if __name__ == '__main__':
    raise SystemExit(main())
