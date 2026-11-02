#!/usr/bin/env python3
"""AI-assisted, bounded untrusted statistics, no proof or GO.

Opening counts inspect native encoded states, not scalar successor topology.
Profile sharing counts apply only to the supplied sampled certificates.
No solver, mirror, Agda, desktop job, or population extrapolation is run here.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import sqlite3
import tempfile

import bench6
from generate6 import encode_state
import ref
from run_job import atomic_json
import shared6

TRUST = 'untrusted statistics, no proof or GO'
SEEDS = {'lower': 2026100604, 'upper': 2026100605}
MAX_INPUT = 512 * 1024 * 1024
MAX_STATES = 1500000
MAX_SAMPLES = 120
FIELDS = {'position', 'turn', 'direction', 'threshold', 'leaf', 'selected_index'}
INVERSES = (0, 3, 2, 1, 4, 5, 6, 7)


class DiskUnion:
    """Exact set cardinalities with bounded RAM; the database is temporary."""
    def __init__(self):
        self.directory = tempfile.TemporaryDirectory(prefix='othello-symmetry-union6-')
        self.connection = sqlite3.connect(str(Path(self.directory.name)/'sets.sqlite'))
        self.connection.execute('PRAGMA journal_mode=OFF')
        self.connection.execute('PRAGMA synchronous=OFF')
        self.connection.execute('PRAGMA cache_size=-16384')
        self.connection.execute('CREATE TABLE keys (kind INTEGER, key TEXT, PRIMARY KEY(kind,key)) WITHOUT ROWID')
        self.counts = defaultdict(int)

    def add(self, kind, keys):
        before = self.connection.total_changes
        with self.connection:
            self.connection.executemany('INSERT OR IGNORE INTO keys VALUES (?,?)',
                                        ((kind,key) for key in keys))
        self.counts[kind] += self.connection.total_changes-before
        return self.counts[kind]

    def close(self):
        self.connection.close()
        self.directory.cleanup()


def integer(value, name, low=0, high=(1 << 64) - 1):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('invalid ' + name)
    return value


def coordinate(tag, r, c):
    integer(tag, 'symmetry tag', 0, 7)
    integer(r, 'row', 0, 5)
    integer(c, 'column', 0, 5)
    return ((r, c), (c, 5-r), (5-r, 5-c), (5-c, r),
            (r, 5-c), (5-c, 5-r), (5-r, c), (c, r))[tag]


def _permutation(tag):
    result = [0] * 36
    for i in range(36):
        r, c = coordinate(tag, *divmod(i, 6))
        result[6*r+c] = i
    return tuple(result)


PERMUTATIONS = tuple(_permutation(tag) for tag in range(8))


def validate_key(key):
    if (type(key) is not str or len(key) != 37 or key[0] not in 'bw'
            or any(c not in '012' for c in key[1:])):
        raise ValueError('invalid full-state encoding')
    return key


def transform_key(key, tag):
    validate_key(key)
    integer(tag, 'symmetry tag', 0, 7)
    pos = key[1:]
    return key[0] + ''.join(pos[i] for i in PERMUTATIONS[tag])


def transform(state, tag):
    if (state.size != 6 or len(state.cells) != 36
            or state.turn not in (ref.BLACK, ref.WHITE)
            or any(type(c) is not int or c not in (0, 1, 2) for c in state.cells)):
        raise ValueError('invalid six-state')
    integer(tag, 'symmetry tag', 0, 7)
    return ref.State(6, tuple(state.cells[i] for i in PERMUTATIONS[tag]), state.turn)


def canonical_key(key):
    """Lexicographically least complete encode_state, lowest tag on ties."""
    validate_key(key)
    pos = key[1:]
    variants = (key[0] + ''.join(pos[i] for i in p) for p in PERMUTATIONS)
    return min((text, tag) for tag, text in enumerate(variants))


def canonical(state):
    key, tag = canonical_key(encode_state(transform(state, 0)))
    return bench6.decode(key), tag


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def _nonfinite(_):
    raise ValueError('nonfinite JSON')


DECODER = json.JSONDecoder(object_pairs_hook=unique_object, parse_constant=_nonfinite)


class Stream:
    """Incremental JSON reader; the states array is never materialized."""
    def __init__(self, path, max_bytes):
        if path.stat().st_size > max_bytes:
            raise ValueError('input byte cap exceeded')
        self.file = path.open('rb')
        self.buffer, self.index, self.bytes = '', 0, 0
        self.digest, self.max_bytes = hashlib.sha256(), max_bytes
        self.eof = False

    def refill(self):
        raw = self.file.read(65536)
        self.bytes += len(raw)
        if self.bytes > self.max_bytes:
            raise ValueError('input byte cap exceeded')
        self.digest.update(raw)
        # Native output is ASCII; rejecting non-ASCII also avoids split UTF-8.
        self.buffer = self.buffer[self.index:] + raw.decode('ascii')
        self.index = 0
        self.eof = not raw

    def peek(self):
        while True:
            while self.index < len(self.buffer) and self.buffer[self.index].isspace():
                self.index += 1
            if self.index < len(self.buffer):
                return self.buffer[self.index]
            if self.eof:
                return ''
            self.refill()

    def take(self, expected):
        if self.peek() != expected:
            raise ValueError('malformed JSON: expected ' + expected)
        self.index += 1

    def value(self):
        self.peek()
        while True:
            try:
                result, end = DECODER.raw_decode(self.buffer, self.index)
                # A primitive ending on a chunk boundary may be incomplete.
                if end == len(self.buffer) and not self.eof:
                    self.refill()
                    continue
                self.index = end
                return result
            except json.JSONDecodeError as error:
                if self.eof:
                    raise ValueError('malformed JSON') from error
                if len(self.buffer) - self.index > 2 * 1024 * 1024:
                    raise ValueError('oversized JSON record') from error
                self.refill()


def read_native(path, callback, *, max_bytes=MAX_INPUT, max_states=MAX_STATES):
    """Stream one native object; callback validates each encoded state."""
    integer(max_bytes, 'max_input_bytes', 1, 1024**3)
    integer(max_states, 'max_states', 1, 5000000)
    stream = Stream(Path(path), max_bytes)
    metadata, seen, count = {}, set(), 0
    try:
        stream.take('{')
        if stream.peek() == '}':
            raise ValueError('empty native object')
        while True:
            field = stream.value()
            if type(field) is not str or field in seen:
                raise ValueError('duplicate or invalid top-level key')
            seen.add(field)
            stream.take(':')
            if field == 'states':
                stream.take('[')
                if stream.peek() != ']':
                    while True:
                        count += 1
                        if count > max_states:
                            raise ValueError('state cap exceeded')
                        callback(stream.value())
                        if stream.peek() == ']':
                            break
                        stream.take(',')
                stream.take(']')
            else:
                metadata[field] = stream.value()
            if stream.peek() == '}':
                break
            stream.take(',')
        stream.take('}')
        if stream.peek():
            raise ValueError('trailing JSON data')
        if 'states' not in seen or count == 0:
            raise ValueError('missing or empty states')
        validate_metadata(metadata, count, max_states)
        return metadata, stream.digest.hexdigest()
    finally:
        stream.file.close()


def validate_metadata(meta, count, max_states):
    for field in ('complete', 'root_validated', 'root_holds'):
        if meta.get(field) is not True:
            raise ValueError('incomplete/unvalidated native: ' + field)
    if (meta.get('count_overflow') is not False or meta.get('oracle_aborted') is not False
            or meta.get('tree_count_kind') != 'exact'):
        raise ValueError('nonexact, overflowed or aborted native counts')
    if meta.get('direction') not in SEEDS:
        raise ValueError('invalid direction')
    integer(meta.get('threshold'), 'threshold', -36, 36)
    integer(meta.get('frontier_discs'), 'frontier_discs', 0, 36)
    if integer(meta.get('unique_dag_nodes'), 'unique_dag_nodes', 1, max_states) != count:
        raise ValueError('native state count mismatch')
    if integer(meta.get('tree_nodes_S'), 'tree_nodes_S', 1) < count:
        raise ValueError('tree count below distinct states')
    integer(meta.get('frontier_distinct_L'), 'frontier_distinct_L', 0, count)
    integer(meta.get('hint_occurrences_H'), 'hint_occurrences_H')


def item_key(item):
    if type(item) is not dict or set(item) != FIELDS:
        raise ValueError('malformed state fields')
    if item['turn'] not in ('black', 'white') or item['direction'] not in SEEDS:
        raise ValueError('invalid state turn/direction')
    integer(item['threshold'], 'state threshold', -36, 36)
    integer(item['selected_index'], 'selected_index', -1, 35)
    if type(item['leaf']) is not bool:
        raise ValueError('invalid leaf marker')
    if item['leaf'] and item['selected_index'] != -1:
        raise ValueError('leaf carries selection')
    pos = item['position']
    if type(pos) is not str:
        raise ValueError('invalid position')
    key = validate_key(('b' if item['turn'] == 'black' else 'w') + pos)
    if item['leaf'] and '0' not in pos:
        score = pos.count('2') - pos.count('1')
        if not (score >= item['threshold'] if item['direction'] == 'lower'
                else score <= item['threshold']):
            raise ValueError('full-board leaf bound fails')
    return key


def canonical_sample(keys, direction, threshold, samples):
    integer(samples, 'max_samples', 1, 100000)
    if direction not in SEEDS:
        raise ValueError('invalid direction')
    integer(threshold, 'threshold', -36, 36)
    selected = random.Random(SEEDS[direction]).sample(sorted(keys), min(samples, len(keys)))
    return [dict(position=key[1:], turn='black' if key[0] == 'b' else 'white',
                 direction=direction, threshold=threshold, leaf=True, selected_index=-1)
            for key in selected]


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(path, data)


def opening(args):
    report = {'format': 'othello-symmetry-opening6-v1', 'trust': TRUST,
              'status': 'pending', 'input_path': str(args.input.resolve()),
              'limitations': ['Native topology/reachability and symmetry claims are untrusted.',
                             'No successor recomputation, proof acceptance, or cost estimate.']}
    write(args.output, report)
    exact, classes, frontier_classes = set(), set(), set()
    bounds, frontier_counts, min_nonleaf, max_nonleaf = set(), defaultdict(int), 37, -1
    def consume(item):
        nonlocal min_nonleaf, max_nonleaf
        key = item_key(item)
        if key in exact:
            raise ValueError('duplicate full-state key')
        exact.add(key)
        representative, _ = canonical_key(key)
        classes.add(representative)
        bounds.add((item['direction'], item['threshold']))
        discs = 36 - key.count('0')
        if item['leaf']:
            frontier_classes.add(representative)
            frontier_counts[discs] += 1
        else:
            min_nonleaf = min(min_nonleaf, discs)
            max_nonleaf = max(max_nonleaf, discs)
        if len(exact) % 25000 == 0:
            report.update(status='counting', processed_states=len(exact),
                          observed_canonical_classes=len(classes))
            write(args.output, report)
    try:
        metadata, digest = read_native(args.input, consume, max_bytes=args.max_input_bytes,
                                       max_states=args.max_states)
        direction, threshold = metadata['direction'], metadata['threshold']
        if bounds != {(direction, threshold)}:
            raise ValueError('state bounds mismatch')
        if sum(frontier_counts.values()) != metadata['frontier_distinct_L']:
            raise ValueError('native frontier count mismatch')
        if max_nonleaf >= metadata['frontier_discs']:
            raise ValueError('nonleaf at/above frontier')
        # Below-cut terminal claims cannot be certified without rules replay.
        below = sum(n for discs, n in frontier_counts.items() if discs < metadata['frontier_discs'])
        report.update(status='complete', input_sha256=digest, graph_metadata=metadata,
                      exact_full_states=len(exact), canonical_full_state_classes=len(classes),
                      exact_frontier_full_states=sum(frontier_counts.values()),
                      canonical_frontier_full_state_classes=len(frontier_classes),
                      below_cut_native_terminal_claims_unchecked=below,
                      includes_frontier_leaves=True,
                      exact_to_canonical_ratio=len(exact)/len(classes))
        sample = {'format': 'canonical-frontier-work6-untrusted-v1', 'trust': TRUST,
                  'input_path': str(args.input.resolve()), 'input_sha256': digest,
                  'seed': SEEDS[direction], 'requested_samples': args.max_samples,
                  'population_L': len(frontier_classes),
                  'population_kind': 'canonical frontier full-state classes',
                  'raw_frontier_distinct_L': sum(frontier_counts.values()),
                  'sampling': 'uniform without replacement over sorted canonical class representatives',
                  'canonical_tag_order': ['identity', 'rotate90', 'rotate180', 'rotate270',
                                          'vertical', 'antiDiagonal', 'horizontal', 'diagonal'],
                  'sampled_states': canonical_sample(frontier_classes, direction, threshold, args.max_samples),
                  'records': [], 'sample_only': True,
                  'limitations': ['Canonical population differs from raw frontier leaf population.',
                                  'No raw-leaf or occurrence-weighted cost extrapolation is valid.',
                                  'Native frontier/terminal leaf markers are not independently proved.'],
                  'graph_metadata': metadata}
        if args.sample_output:
            write(args.sample_output, sample)
            report['sample_output'] = str(args.sample_output.resolve())
        report['sample_seed'] = sample['seed']
        report['selected_samples'] = len(sample['sampled_states'])
        write(args.output, report)
        return report
    except Exception as error:
        report.update(status='failure', error=f'{type(error).__name__}: {error}')
        write(args.output, report)
        raise


def read_json(path, max_bytes):
    path = Path(path)
    if path.stat().st_size > max_bytes:
        raise ValueError('input byte cap exceeded')
    with path.open('rb') as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError('input byte cap exceeded')
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=_nonfinite)


def certificate_stats(native, root, direction, threshold, max_states, max_tokens):
    """One exact scalar replay of each sampled native certificate graph."""
    states = native.get('states')
    if type(states) is not list:
        raise ValueError('missing native states')
    validate_metadata(native, len(states), max_states)
    keys = set()
    leaf_count = 0
    for item in states:
        key = item_key(item)
        if key in keys or (item['direction'], item['threshold']) != (direction, threshold):
            raise ValueError('duplicate state or mismatched bound')
        keys.add(key)
        leaf_count += item['leaf']
    if leaf_count != native['frontier_distinct_L']:
        raise ValueError('native frontier count mismatch')
    graph = shared6.graph_from_native(native, root, direction, threshold)
    if len(graph) != len(keys):
        raise ValueError('unreachable native states')
    tree_tokens = shared6.expanded_size(graph, root)
    if tree_tokens != native['tree_nodes_S']:
        raise ValueError('expanded/tree token count differs from native')
    if tree_tokens > max_tokens:
        raise ValueError('expanded token cap exceeded')
    entries, stats = shared6.layered(graph, root)
    # Decode tokens independently of shared6's counter (numbers are payloads).
    token_count = sum(sum(c in 'LCFPSK' for c in body) for _, body in entries)
    citation_count = sum(body.count('K') for _, body in entries)
    if token_count != stats['checked_tokens'] or citation_count != stats['citations']:
        raise ValueError('layered token accounting mismatch')
    if stats['expanded_tree_nodes'] != tree_tokens:
        raise ValueError('layered expanded accounting mismatch')
    canonical_keys = {canonical_key(key)[0] for key in keys}
    return dict(stats, tree_checked_tokens=tree_tokens,
                layered_encoded_bytes=len(shared6.encode(entries)),
                exact_full_states=len(keys), canonical_full_state_classes=len(canonical_keys),
                token_reduction=tree_tokens-stats['checked_tokens']), keys, canonical_keys


def profiles(args):
    source = args.input / 'profile.json' if args.input.is_dir() else args.input
    profile = read_json(source, args.max_input_bytes)
    cases = profile.get('cases')
    if type(cases) is not list or not cases:
        raise ValueError('missing profile cases')
    groups = defaultdict(list)
    seen_cases = set()
    for case in cases:
        if type(case) is not dict or case.get('status') not in ('complete', 'leaf-work-capped'):
            raise ValueError('incomplete profile case')
        row = case.get('row', {})
        direction = case.get('direction')
        if direction not in SEEDS:
            raise ValueError('invalid case direction')
        threshold = integer(row.get('value'), 'case threshold', -36, 36)
        frontier = integer(case.get('frontier_discs'), 'case frontier', 0, 36)
        if getattr(args, 'cuts', None) and frontier not in args.cuts:
            continue
        validate_key(row.get('state'))
        case_key = (direction, threshold, frontier, row['state'])
        if case_key in seen_cases:
            raise ValueError('duplicate profile case')
        seen_cases.add(case_key)
        groups[(direction, threshold, frontier)].append(case)
    report = {'format': 'othello-symmetry-sharing-profile6-v1', 'trust': TRUST,
              'sample_population_L': profile.get('sample_population_L'),
              'sample_population_kind': profile.get('sample_population_kind', 'distinct raw frontier states'),
              'selected_sample_count': len(profile.get('selected_states', [])),
              'sample_seed': profile.get('sample_seed'),
              'sample_sha256': profile.get('sample_sha256'),
              'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'status': 'pending', 'input_path': str(source.resolve()), 'groups': [],
              'scope': 'supplied sampled certificates only, grouped by direction/threshold/cut',
              'limitations': ['No population-global sharing or canonical reduction claim.',
                             'No solver/mirror reruns or proof acceptance.',
                             'Tree tokens count certificate nodes, not numeric payload characters.']}
    write(args.output, report)
    disk = DiskUnion() if getattr(args, 'disk_union', False) else None
    report['union_backend'] = 'temporary SQLite (removed on normal completion)' if disk else 'memory'
    try:
        for group_index, ((direction, threshold, frontier), group_cases) in enumerate(sorted(groups.items())):
            if len(group_cases) > args.max_samples:
                raise ValueError('profile sample cap exceeded')
            exact_union, canonical_union = set(), set()
            result = dict(direction=direction, threshold=threshold, frontier_discs=frontier,
                          cases=[], sum_per_certificate_exact_full_states=0,
                          sum_per_certificate_canonical_classes=0, sum_tree_checked_tokens=0,
                          sum_layered_checked_tokens=0)
            report['groups'].append(result)
            for case in group_cases:
                candidate = Path(case.get('native_path', ''))
                native_path = source.parent / candidate.name
                if not native_path.is_file():
                    native_path = candidate if candidate.is_absolute() else source.parent / candidate
                native = read_json(native_path, args.max_input_bytes)
                stats, keys, canonical_keys = certificate_stats(
                    native, bench6.decode(case['row']['state']), direction, threshold,
                    args.max_states, args.max_tree_tokens)
                if native['frontier_discs'] != frontier:
                    raise ValueError('case frontier mismatch')
                stats.update(id=case['row'].get('id'), state=case['row']['state'],
                             native_path=str(native_path.resolve()))
                result['cases'].append(stats)
                result['sum_per_certificate_exact_full_states'] += len(keys)
                result['sum_per_certificate_canonical_classes'] += len(canonical_keys)
                result['sum_tree_checked_tokens'] += stats['tree_checked_tokens']
                result['sum_layered_checked_tokens'] += stats['checked_tokens']
                if disk:
                    exact_count = disk.add(2*group_index, keys)
                    canonical_count = disk.add(2*group_index+1, canonical_keys)
                else:
                    exact_union.update(keys)
                    canonical_union.update(canonical_keys)
                    exact_count, canonical_count = len(exact_union), len(canonical_union)
                if exact_count > args.max_states or canonical_count > args.max_states:
                    raise ValueError('group union state cap exceeded')
                result.update(exact_union_full_states=exact_count,
                              canonical_union_full_state_classes=canonical_count)
                report['status'] = 'counting'
                write(args.output, report)
                del native, keys, canonical_keys
            result['sharing_between_certificates'] = result['sum_per_certificate_exact_full_states']-exact_count
            result['canonical_union_reduction'] = exact_count-canonical_count
            del exact_union, canonical_union
        report['status'] = 'complete'
        write(args.output, report)
        return report
    except Exception as error:
        report.update(status='failure', error=f'{type(error).__name__}: {error}')
        write(args.output, report)
        raise
    finally:
        if disk:
            disk.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('opening', 'profiles'):
        command = sub.add_parser(name)
        command.add_argument('--input', type=Path, required=True)
        command.add_argument('--output', type=Path, required=True)
        command.add_argument('--max-input-bytes', type=int, default=MAX_INPUT)
        command.add_argument('--max-states', type=int, default=MAX_STATES)
        command.add_argument('--max-samples', type=int, default=MAX_SAMPLES)
        if name == 'profiles':
            command.add_argument('--cuts', type=lambda s: {int(n) for n in s.split(',')},
                                 default=None, help='explicit measured cuts, e.g. 36')
            command.add_argument('--disk-union', action='store_true',
                                 help='count cross-certificate unions in temporary SQLite with bounded RAM')
        if name == 'opening':
            command.add_argument('--sample-output', type=Path)
        else:
            command.add_argument('--max-tree-tokens', type=int, default=10000000)
    args = parser.parse_args()
    try:
        integer(args.max_input_bytes, 'max_input_bytes', 1, 1024**3)
        integer(args.max_states, 'max_states', 1,
                10000000 if getattr(args, 'disk_union', False) else 5000000)
        integer(args.max_samples, 'max_samples', 1, 100000)
        paths = [args.input.resolve(), args.output.resolve()]
        if args.action == 'opening' and args.sample_output:
            paths.append(args.sample_output.resolve())
        if len(paths) != len(set(paths)):
            raise ValueError('input and output paths must differ')
        if args.action == 'profiles':
            integer(args.max_tree_tokens, 'max_tree_tokens', 1)
        result = opening(args) if args.action == 'opening' else profiles(args)
        print(json.dumps({'output': str(args.output.resolve()), 'status': result['status'], 'trust': TRUST}))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
