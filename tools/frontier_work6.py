#!/usr/bin/env python3
"""Bounded, untrusted DISTINCT frontier-leaf work sampling (never proof input).

This estimates the sum of no-TT row-major mirror calls over distinct leaves,
not occurrence-weighted work in an expanded proof tree. Graph topology and
native count correctness are not independently established. No GO verdict.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time

import ref
import solve6

MAX_BYTES = 128 * 1024 * 1024
MAX_STATES = 500000
STATE_FIELDS = {'position', 'turn', 'direction', 'threshold', 'leaf', 'selected_index'}
LIMITATIONS = [
    'Untrusted native graph; topology/reachability, S/H and kernel acceptance not checked.',
    'Uniform sampling without replacement over DISTINCT full-state leaves only.',
    'Estimated distinct-leaf sum is not occurrence-weighted expanded proof-tree work.',
    'Native mirror measures literal no-TT row-major calls, not Agda kernel CPU or acceptance.',
    'Small samples may miss rare expensive leaves; censoring prevents a total estimate.',
]


def integer(value, name, low=0, high=(1 << 64)-1):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('invalid ' + name)
    return value


def results_path(path):
    path = Path(path).resolve()
    if not path.is_relative_to((solve6.ROOT / 'results').resolve()):
        raise ValueError('input/output must be under results/')
    return path


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key: ' + key)
        obj[key] = value
    return obj


def read_graph(path, *, max_bytes=MAX_BYTES, max_states=MAX_STATES):
    """Bound the file before decoding; never construct an expanded certificate."""
    integer(max_bytes, 'max_bytes', 1, 1024 * 1024 * 1024)
    integer(max_states, 'max_states', 1, 5000000)
    path = results_path(path)
    if path.stat().st_size > max_bytes:
        raise ValueError('graph exceeds input byte cap')
    with path.open('rb') as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError('graph exceeds input byte cap')
    graph = json.loads(raw, object_pairs_hook=unique_object,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    leaves = validate_graph(graph, max_states=max_states)
    # Retain all exact source/build/request/counter metadata, without graph expansion.
    metadata = {key: value for key, value in graph.items() if key != 'states'}
    return leaves, metadata, hashlib.sha256(raw).hexdigest()


def validate_graph(graph, *, max_states=MAX_STATES):
    if type(graph) is not dict:
        raise ValueError('graph must be an object')
    for field in ('complete', 'root_validated', 'root_holds'):
        if graph.get(field) is not True:
            raise ValueError('incomplete/unvalidated graph: ' + field)
    if graph.get('count_overflow') is not False or graph.get('tree_count_kind') != 'exact':
        raise ValueError('overflowed or nonexact native counts')
    if graph.get('oracle_aborted') is not False:
        raise ValueError('aborted or unspecified oracle')
    direction = graph.get('direction')
    if direction not in ('lower', 'upper'):
        raise ValueError('invalid direction')
    threshold = integer(graph.get('threshold'), 'threshold', -36, 36)
    frontier = integer(graph.get('frontier_discs'), 'frontier_discs', 0, 36)
    states = graph.get('states')
    if type(states) is not list or not 1 <= len(states) <= max_states:
        raise ValueError('missing, empty or oversized states')
    n = integer(graph.get('unique_dag_nodes'), 'unique_dag_nodes', 1, max_states)
    population = integer(graph.get('frontier_distinct_L'), 'frontier_distinct_L', 1, n)
    if n != len(states):
        raise ValueError('DAG state count mismatch')
    if integer(graph.get('tree_nodes_S'), 'tree_nodes_S', 1) < n:
        raise ValueError('tree count smaller than DAG')
    integer(graph.get('hint_occurrences_H'), 'hint_occurrences_H')
    for name in ('cpu_seconds', 'cumulative_cpu_seconds'):
        if name in graph:
            value = graph[name]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('invalid ' + name)
    seen, leaves = set(), []
    for item in states:
        if type(item) is not dict or set(item) != STATE_FIELDS:
            raise ValueError('malformed state fields')
        pos = item['position']
        if type(pos) is not str or len(pos) != 36 or any(c not in '012' for c in pos):
            raise ValueError('invalid 6x6 position')
        if item['turn'] not in ('black', 'white'):
            raise ValueError('invalid turn')
        if item['direction'] != direction or type(item['threshold']) is not int or item['threshold'] != threshold:
            raise ValueError('mismatched state bound')
        key = (pos, item['turn'], direction, threshold)
        if key in seen:
            raise ValueError('duplicate full-state key (including leaf)')
        seen.add(key)
        if type(item['leaf']) is not bool:
            raise ValueError('invalid leaf marker')
        selected = integer(item['selected_index'], 'selected_index', -1, 35)
        discs = 36 - pos.count('0')
        if item['leaf']:
            if selected != -1:
                raise ValueError('leaf carries selected index')
            if discs < frontier:
                state = scalar(item)
                if ref.successors(state):
                    raise ValueError('nonterminal leaf below frontier')
                score = ref.score(state)
                if not (score >= threshold if direction == 'lower' else score <= threshold):
                    raise ValueError('terminal leaf bound fails')
            if discs == 36:
                score = pos.count('2') - pos.count('1')
                if not (score >= threshold if direction == 'lower' else score <= threshold):
                    raise ValueError('terminal leaf bound fails')
            leaves.append(dict(item))
        elif discs >= frontier:
            raise ValueError('nonleaf at/above frontier')
        else:
            state = scalar(item)
            children = ref.successors(state)
            if not children:
                raise ValueError('terminal marked nonleaf')
            placements = ref.placements(state)
            own = item['turn'] == ('white' if direction == 'lower' else 'black')
            if placements and own:
                if not 0 <= selected < len(children):
                    raise ValueError('invalid forcing-node selected index')
            elif selected != -1:
                raise ValueError('pass/opponent node carries selected index')
    if len(leaves) != population:
        raise ValueError('distinct leaf count mismatch')
    return sorted(leaves, key=lambda x: (x['position'], x['turn']))


def scalar(item):
    return ref.State(6, tuple(map(int, item['position'])),
                     ref.BLACK if item['turn'] == 'black' else ref.WHITE)


def select(leaves, samples, seed):
    integer(samples, 'samples', 1, MAX_STATES)
    integer(seed, 'seed', 0, (1 << 64)-1)
    return random.Random(seed).sample(leaves, min(samples, len(leaves)))


def atomic_json(path, value):
    path = results_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.tmp-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def provenance():
    files = [Path(__file__), solve6.ROOT / 'tools/solve6.py', solve6.ROOT / 'tools/ref.py',
             solve6.SOURCE, solve6.VENDOR, solve6.LICENSE]
    record = {'source_sha256': {str(p.relative_to(solve6.ROOT)): solve6.sha256(p) for p in files}}
    build = solve6.BUILD / 'build.json'
    if build.exists():
        record['build_metadata'] = json.loads(build.read_text())
    return record


def measure(item, timeout):
    started = time.monotonic()
    record = {'state': item, 'timeout_seconds': timeout, 'fuel': 80,
              'status': 'pending', 'censored': True, 'W': None}
    try:
        native = solve6.query('mirror', scalar(item), direction=item['direction'],
                              threshold=item['threshold'], fuel=80, timeout=timeout)
        record['native_record'] = native
        if (native.get('holds') is not True or native.get('noTT') is not True
                or native.get('order') != 'row-major' or native.get('fuel') != 80
                or native.get('direction') != item['direction']
                or type(native.get('threshold')) is not int or native['threshold'] != item['threshold']):
            raise ValueError('mirror did not confirm requested literal no-TT bound')
        work = integer(native.get('nodes'), 'mirror nodes', 1)
        cpu = native.get('cpu_seconds')
        if type(cpu) not in (int, float) or not math.isfinite(cpu) or cpu < 0:
            raise ValueError('invalid mirror CPU time')
        record.update(status='complete', censored=False, W=work)
    except subprocess.TimeoutExpired as error:
        record.update(status='timeout', error=str(error))
    except Exception as error:
        record.update(status='failure', error=f'{type(error).__name__}: {error}')
    record['wall_seconds'] = time.monotonic() - started
    record['provenance'] = provenance()
    return record


def estimates(records, population, selected_count):
    done = [r['W'] for r in records if r['status'] == 'complete']
    result = {'kind': 'statistical sample summary, never exact total W',
              'completed_samples': len(done), 'selected_samples': selected_count,
              'uncensored': len(done) == selected_count,
              'completed_sample_sum_W': sum(done),
              'sample_sum_scope': 'observed completed samples only; omitted censored costs are unknown',
              'recommendation': 'none; sampling does not establish GO or kernel acceptance'}
    if len(done) == selected_count and done:
        mean = statistics.mean(done)
        result.update(statistical_sample_mean_W=mean,
                      statistical_estimated_distinct_leaf_total_W=population * mean)
        if len(done) > 1:
            se = statistics.stdev(done) / math.sqrt(len(done)) * math.sqrt(
                (population-len(done))/(population-1)) if population > 1 else 0
            result['statistical_estimated_total_standard_error_W'] = population * se
    return result


def run(input_path, output_path, *, samples=20, seed=0, timeout=10, sample_only=False,
        max_bytes=MAX_BYTES, max_states=MAX_STATES):
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be finite and positive')
    output_path = results_path(output_path)
    if output_path == results_path(input_path):
        raise ValueError('output must differ from graph input')
    leaves, metadata, digest = read_graph(input_path, max_bytes=max_bytes, max_states=max_states)
    chosen = select(leaves, samples, seed)
    identity = {'input_sha256': digest, 'seed': seed, 'requested_samples': samples,
                'timeout_seconds': timeout, 'population_L': len(leaves), 'sampled_states': chosen,
                'input_limits': {'max_bytes': max_bytes, 'max_states': max_states}}
    report = {'format': 'frontier-work6-untrusted-v1', **identity,
              'input_path': str(results_path(input_path)), 'graph_metadata': metadata,
              'limitations': LIMITATIONS, 'records': [], 'sampler_provenance': provenance()}
    if output_path.exists():
        previous = json.loads(output_path.read_text(), object_pairs_hook=unique_object)
        if previous.get('format') != report['format'] or any(previous.get(k) != v for k, v in identity.items()):
            raise ValueError('resume input or sampling configuration mismatch')
        if previous.get('sampler_provenance', {}).get('source_sha256') != report['sampler_provenance']['source_sha256']:
            raise ValueError('resume source mismatch')
        records = previous.get('records')
        if type(records) is not list or len(records) > len(chosen):
            raise ValueError('invalid resume records')
        for index, record in enumerate(records):
            if record.get('state') != chosen[index] or record.get('status') not in ('complete', 'timeout', 'failure'):
                raise ValueError('invalid resume state/status')
            if record['status'] == 'complete':
                integer(record.get('W'), 'resumed W', 1)
                if record.get('censored') is not False:
                    raise ValueError('completed resume record censored')
            elif record.get('W') is not None or record.get('censored') is not True:
                raise ValueError('failed resume record has completed work')
        report['records'] = records
    report['sample_only'] = sample_only
    report['summary'] = estimates(report['records'], len(leaves), len(chosen))
    atomic_json(output_path, report)
    if not sample_only:
        for item in chosen[len(report['records']):]:
            report['records'].append(measure(item, timeout))
            report['summary'] = estimates(report['records'], len(leaves), len(chosen))
            atomic_json(output_path, report)
    return {'output': str(output_path), 'population_L': len(leaves), 'selected_samples': len(chosen),
            'sample_only': sample_only, **report['summary']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--timeout', type=float, default=10)
    parser.add_argument('--sample-only', action='store_true')
    parser.add_argument('--max-input-bytes', type=int, default=MAX_BYTES)
    parser.add_argument('--max-states', type=int, default=MAX_STATES)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.input, args.output, samples=args.samples, seed=args.seed,
                             timeout=args.timeout, sample_only=args.sample_only,
                             max_bytes=args.max_input_bytes, max_states=args.max_states), sort_keys=True))
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
