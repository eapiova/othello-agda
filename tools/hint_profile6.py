#!/usr/bin/env python3
"""Bounded untrusted hint-depth pilots for sampled frontier positions.

Counts certificate occurrences and multiplies solve work by leaf occurrence
weights. No native result is imported as a proof. Concrete certificates are
emitted for independent safe Agda checks; this tool never runs Agda.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import bench6
import frontier6
import frontier_work6
import generate6
import hint_bench6
import ref
import solve6
from provenance import source_files, source_identity
from run_job import atomic_json


def graph_weights(row, direction, native):
    """Topological propagation, without copying a counter into every subtree."""
    graph = {}
    for item in native['states']:
        state = bench6.decode(('w' if item['turn'] == 'white' else 'b') + item['position'])
        if state in graph:
            raise ValueError('duplicate state')
        graph[state] = item
    root = bench6.decode(row['state'])
    children, postorder, visiting = {}, [], set()
    def visit(state):
        if state in visiting:
            raise ValueError('cycle in graph')
        if state in children:
            return
        if state not in graph:
            raise ValueError('missing graph child')
        visiting.add(state)
        item = graph[state]
        successors = () if item['leaf'] else ref.successors(state)
        own = state.turn == (ref.WHITE if direction == 'lower' else ref.BLACK)
        if successors and ref.placements(state) and own:
            index = item['selected_index']
            if not 0 <= index < len(successors):
                raise ValueError('invalid choice')
            successors = (successors[index],)
        children[state] = successors
        for child in successors:
            visit(child)
        visiting.remove(state)
        postorder.append(state)
    visit(root)
    if len(children) != len(graph):
        raise ValueError('unreachable graph state')
    weights = {state: 0 for state in graph}
    weights[root] = 1
    for state in reversed(postorder):
        for child in children[state]:
            weights[child] += weights[state]
    if sum(weights.values()) != native['tree_nodes_S']:
        raise ValueError('occurrence count differs from native S')
    return {state: weights[state] for state, item in graph.items() if item['leaf']}


def leaf_work(row, direction, native, *, max_leaves=1000, timeout=2,
              wall_budget=60, query=solve6.query):
    weights = graph_weights(row, direction, native)
    result = {'kind': 'exact occurrence-weighted mirror work only when every leaf completes',
              'distinct_leaves': len(weights), 'leaf_occurrences': sum(weights.values()),
              'records': [], 'complete': False, 'weighted_W': None,
              'max_leaves': max_leaves, 'wall_budget_seconds': wall_budget}
    terminal = {state for state in weights if not ref.successors(state)}
    result['terminal_leaf_occurrences'] = sum(weights[state] for state in terminal)
    result['solve_leaf_occurrences'] = sum(weight for state, weight in weights.items() if state not in terminal)
    if len(weights) - len(terminal) > max_leaves:
        result['stop_reason'] = 'distinct-leaf cap'
        return result
    started = time.monotonic()
    total = 0
    for state, weight in sorted(weights.items(), key=lambda item: generate6.encode_state(item[0])):
        remaining = wall_budget - (time.monotonic() - started)
        if remaining <= 0:
            result['stop_reason'] = 'leaf-work wall cap'
            break
        record = {'state': generate6.encode_state(state), 'occurrences': weight,
                  'W': None, 'status': 'pending'}
        if state in terminal:
            # Encoded L is checked by checkLocal; it does not call forcesB.
            record.update(status='complete', W=0, kind='terminal-certificate-leaf')
            result['records'].append(record)
            continue
        try:
            measured = query('mirror', state, direction=direction, threshold=row['value'],
                             fuel=80, timeout=min(timeout, remaining))
            if (measured.get('holds') is not True or measured.get('noTT') is not True
                    or measured.get('order') != 'row-major' or measured.get('fuel') != 80
                    or measured.get('direction') != direction
                    or measured.get('threshold') != row['value']
                    or type(measured.get('nodes')) is not int or measured['nodes'] <= 0):
                raise ValueError('mirror bound or semantics mismatch')
            record.update(status='complete', W=measured['nodes'], native_record=measured)
            total += weight * measured['nodes']
        except subprocess.TimeoutExpired as error:
            record.update(status='timeout', error=str(error))
        except Exception as error:
            record.update(status='failure', error=f'{type(error).__name__}: {error}')
        result['records'].append(record)
    result['wall_seconds'] = time.monotonic() - started
    result['completed_observed_weighted_W'] = total
    if len(result['records']) == len(weights) and all(r['status'] == 'complete' for r in result['records']):
        result.update(complete=True, weighted_W=total)
    return result


def freeze_case(case, encoded, output):
    """Create an independent proof root without inventing an exact raw W."""
    row, direction = case['row'], case['direction']
    label = f"hintpilot6-{row['id']}-c{case['frontier_discs']}-{direction}"
    root = output / label
    root.mkdir(parents=True, exist_ok=False)
    for name, data in source_files(bench6.ROOT):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    target = root / 'src/Tests/Bench6/Check.agda'
    proof = hint_bench6.proof_text(row, direction, encoded)
    target.write_text(proof)
    manifest = bench6.refresh_manifest(root)
    job = {'format': 'othello-hint-depth-pilot6-job-v1', 'label': label,
           'root': str(root), 'state': row['state'], 'state_id': row['id'],
           'threshold': row['value'], 'direction': direction, 'rules': 'fast',
           'search_kind': 'local-certificate', 'hint_tree_S': case['native']['tree_nodes_S'],
           'native_W': None, 'weighted_tail_W': case['leaf_work']['weighted_W'],
           'tail_work_complete': case['leaf_work']['complete'],
           'encoded_bytes': len(encoded), 'generated_proof': proof,
           'source_sha256': manifest['source_sha256'],
           'trust': 'untrusted generation; safe Agda acceptance pending'}
    atomic_json(root.with_name(label + '.job.json'), job)
    return {key: job[key] for key in ('label', 'root', 'source_sha256', 'hint_tree_S',
                                     'weighted_tail_W', 'tail_work_complete', 'encoded_bytes')}


def run(args):
    # Samples may come from another immutable desktop run. This is a read;
    # emitted native data and proof roots remain confined to our results/.
    input_path = Path(args.input).resolve(strict=True)
    output = frontier_work6.results_path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    raw = input_path.read_bytes()
    samples = json.loads(raw)
    if samples.get('format') not in ('frontier-work6-untrusted-v1',
                                   'canonical-frontier-work6-untrusted-v1'):
        raise ValueError('requires a recorded frontier sample')
    canonical = samples.get('format') == 'canonical-frontier-work6-untrusted-v1'
    chosen = samples.get('sampled_states', [])[:args.samples]
    if not chosen:
        raise ValueError('empty sample selection')
    grid = [int(value) for value in args.frontiers.split(',')]
    if not grid or len(set(grid)) != len(grid) or any(not 0 <= value <= 36 for value in grid):
        raise ValueError('invalid frontier grid')
    report = {'format': 'othello-hint-depth-profile6-v1',
              'sample_sha256': hashlib.sha256(raw).hexdigest(),
              'sample_seed': samples['seed'], 'sample_population_L': samples['population_L'],
              'sample_population_kind': samples.get('population_kind', 'distinct raw frontier states'),
              'selected_states': chosen, 'cases': [], 'config': vars(args).copy(),
              'source': source_identity(bench6.ROOT),
              'trust': 'untrusted local measurements; no global total or GO conclusion',
              'limitations': ['Only this selected subset of distinct frontier leaves.',
                              'Solve work is weighted by repeated leaves inside each local certificate.',
                              'Capped prefix or leaf work is never extrapolated as complete.']}
    report['config'] = {key: str(value) if isinstance(value, Path) else value
                        for key, value in report['config'].items()}
    if canonical:
        report['limitations'].append('Uniform canonical-class sample; raw frontier population multipliers are invalid.')
    destination = output / 'profile.json'
    atomic_json(destination, report)
    for index, item in enumerate(chosen):
        state = frontier_work6.scalar(item)
        row = {'id': f"{item['direction'][0]}{index:03d}", 'state': generate6.encode_state(state),
               'value': item['threshold'], 'empties': state.cells.count(0), 'split': 'held-out'}
        for frontier in grid:
            if frontier <= 36 - row['empties']:
                raise ValueError('hint frontier must follow the sampled position')
            case = {'row': row, 'direction': item['direction'], 'frontier_discs': frontier,
                    'status': 'pending', 'kernel_acceptance': 'unstarted'}
            try:
                native = frontier6.query(state, direction=item['direction'], threshold=item['threshold'],
                    frontier_discs=frontier, max_states=args.max_states, max_nodes=args.max_nodes,
                    max_cpu_seconds=args.prefix_cpu_seconds, tt_bits=20, small=4, deep_order=5,
                    max_memory_mb=256, emit_states=True, timeout=args.prefix_cpu_seconds + 10)
                native_path = output / f"native-{row['id']}-c{frontier}.json"
                atomic_json(native_path, native)
                case['native_path'] = str(native_path)
                case['native'] = {key: value for key, value in native.items() if key != 'states'}
                encoded, count = hint_bench6.certificate(row, item['direction'], native, args.max_bytes)
                case['encoded_bytes'] = len(encoded)
                case['leaf_work'] = leaf_work(row, item['direction'], native, max_leaves=args.max_leaves,
                    timeout=args.leaf_timeout, wall_budget=args.leaf_wall_seconds)
                case['status'] = 'complete' if case['leaf_work']['complete'] else 'leaf-work-capped'
                certificate_path = output / f"certificate-{row['id']}-c{frontier}.txt"
                certificate_path.write_text(encoded)
                case['encoded_sha256'] = hashlib.sha256(encoded.encode('ascii')).hexdigest()
                case['proof_job'] = (None if getattr(args, 'statistics_only', False)
                                     else freeze_case(case, encoded, output))
            except Exception as error:
                case.update(status='failure', error=f'{type(error).__name__}: {error}')
            report['cases'].append(case)
            atomic_json(destination, report)
            print(json.dumps({key: case[key] for key in ('row', 'frontier_discs', 'status')}, sort_keys=True), flush=True)
    return {'output': str(destination), 'cases': len(report['cases']),
            'complete_measurements': sum(c['status'] == 'complete' for c in report['cases'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=3)
    parser.add_argument('--frontiers', default='24,28,36')
    parser.add_argument('--max-states', type=int, default=100000)
    parser.add_argument('--max-nodes', type=int, default=10000000)
    parser.add_argument('--prefix-cpu-seconds', type=int, default=10)
    parser.add_argument('--max-bytes', type=int, default=1024*1024)
    parser.add_argument('--statistics-only', action='store_true',
                        help='record native profiles without copying a proof root per case')
    parser.add_argument('--max-leaves', type=int, default=1000)
    parser.add_argument('--leaf-timeout', type=float, default=2)
    parser.add_argument('--leaf-wall-seconds', type=float, default=60)
    args = parser.parse_args()
    if args.samples <= 0 or args.max_leaves <= 0 or args.leaf_timeout <= 0 or args.leaf_wall_seconds <= 0:
        parser.error('positive sample and leaf limits required')
    print(json.dumps(run(args), sort_keys=True))


if __name__ == '__main__':
    main()
