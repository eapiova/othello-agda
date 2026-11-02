#!/usr/bin/env python3
"""Supervised, resumable native/scalar checks; no results are Agda evidence.

Run this CLI through study6 local-run/remote supervision. Default work includes
native initial perft 0..10, independent scalar perft 0..7, all 1000 seeded late
positions, 90 kernel values and White-forcing mirrors, and principal-line states.
--limit caps position jobs across phases; --empties filters position jobs.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import resource
import time
import traceback
import ref
import solve6

ROOT = Path(__file__).resolve().parents[1]


def scalar_mirror(state, direction, threshold, fuel=80):
    """Independent literal forces model, with all recursive calls counted."""
    nodes = 0
    forcing = ref.WHITE if direction == 'lower' else ref.BLACK
    def visit(s, remaining):
        nonlocal nodes
        nodes += 1
        if remaining == 0:
            return False
        children = ref.successors(s)
        if not children:
            return ref.score(s) >= threshold if direction == 'lower' else ref.score(s) <= threshold
        # A compulsory pass is the same singleton recursion under either fold.
        if s.turn == forcing:
            return any(visit(child, remaining - 1) for child in children)
        return all(visit(child, remaining - 1) for child in children)
    return visit(state, fuel), nodes


def decode(key):
    if len(key) != 37 or key[0] not in 'bw':
        raise ValueError('invalid encoded state')
    state = ref.State(6, tuple(map(int, key[1:])), ref.BLACK if key[0] == 'b' else ref.WHITE)
    solve6.position012(state)
    return state


def cpu():
    return sum(r.ru_utime + r.ru_stime for r in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))


def save(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w') as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
    tmp.replace(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase', choices=('all', 'perft', 'late', 'kernel', 'line'), default='all')
    p.add_argument('--limit', type=int)
    p.add_argument('--empties', type=int, default=36)
    p.add_argument('--max-depth', type=int, default=10)
    p.add_argument('--checkpoint', type=Path, default=solve6.BUILD / 'validation-checkpoint.json')
    p.add_argument('--output', type=Path, default=solve6.BUILD / 'validation.json')
    p.add_argument('--timeout', type=float, default=3600)
    p.add_argument('--deep-order', type=int, default=13)
    p.add_argument('--fuel', type=int, default=80)
    args = p.parse_args()
    if not 0 <= args.max_depth <= 10 or not 0 <= args.empties <= 36 or (args.limit is not None and args.limit < 0):
        p.error('depth must be 0..10, empties 0..36, limit nonnegative')
    config = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}
    record = {'format': 'othello-native6-validation-v1', 'config': config, 'results': [], 'failures': [],
              'trust': 'untrusted differential evidence; no Agda claims'}
    if args.checkpoint.exists():
        previous = json.loads(args.checkpoint.read_text())
        if previous.get('config') != config:
            p.error('checkpoint configuration differs; choose a new checkpoint')
        record = previous
    completed = {item['id'] for item in record['results']}
    started, before = time.monotonic(), cpu()
    def flush():
        record['cpu_seconds_this_invocation'] = cpu() - before
        record['wall_seconds_this_invocation'] = time.monotonic() - started
        record['ok'] = not record['failures']
        save(args.checkpoint, record)
        save(args.output, record)
    def run(identifier, action):
        if identifier in completed:
            return
        try:
            item = {'id': identifier, **action(), 'ok': True}
        except Exception as exc:
            item = {'id': identifier, 'ok': False, 'error': str(exc), 'traceback': traceback.format_exc()}
            record['failures'].append(item)
        record['results'].append(item)
        completed.add(identifier)
        flush()  # Every position survives later cancellation or failure.
    def native(command, state, **kwargs):
        return solve6.query(command, state, timeout=args.timeout, deep_order=args.deep_order, **kwargs)
    if args.phase in ('all', 'perft'):
        for depth in range(args.max_depth + 1):
            def check(depth=depth):
                result = native('perft', ref.initial(6), depth=depth)
                output = {'native': result, 'scalar_checked': depth <= 7}
                if depth <= 7:
                    output['scalar_count'] = ref.perft(ref.initial(6), depth)
                    assert result['count'] == output['scalar_count'], output
                return output
            run(f'perft:{depth}', check)
    jobs = []
    samples = json.loads((ROOT / 'certificates/six-samples.json').read_text())
    if args.phase in ('all', 'late'):
        jobs.extend((f'late:{i}', key, False) for i, key in enumerate(samples['late']))
    if args.phase in ('all', 'kernel'):
        jobs.extend((f'kernel:{empty}:{i}', key, True) for empty, keys in samples['kernel'].items() for i, key in enumerate(keys))
    if args.phase in ('all', 'line'):
        line = json.loads((ROOT / 'certificates/six-line.json').read_text())
        jobs.extend((f'line:{i}', key, False) for i, key in enumerate(line['states']))
    selected = [(identifier, key, mirror) for identifier, key, mirror in jobs if key.count('0') <= args.empties]
    if args.limit is not None:
        selected = selected[:args.limit]
    for identifier, key, mirror in selected:
        def check(key=key, mirror=mirror):
            state = decode(key)
            ref.value.cache_clear()
            try:
                expected = ref.value(state)
                result = native('solve', state)
                output = {'state': key, 'empties': state.cells.count(0), 'scalar_value': expected, 'native': result, 'bounds': []}
                assert result['value'] == expected, output
                for threshold in (expected - 1, expected, expected + 1):
                    if -36 <= threshold <= 36:
                        for direction in ('lower', 'upper'):
                            bound = native('bounds', state, direction=direction, threshold=threshold)
                            output['bounds'].append(bound)
                            assert bound['holds'] == (expected >= threshold if direction == 'lower' else expected <= threshold), output
                if mirror:
                    output['mirrorW'] = native('mirror', state, direction='lower', threshold=expected, fuel=args.fuel)
                    assert output['mirrorW']['holds'], output
                return output
            finally:
                ref.value.cache_clear()
        run(identifier, check)
    record['selected_positions'] = len(selected)
    record['completed_selected_positions'] = sum(identifier in completed for identifier, _, _ in selected)
    record['build'] = json.loads((solve6.BUILD / 'build.json').read_text()) if (solve6.BUILD / 'build.json').exists() else None
    flush()
    print(json.dumps({'ok': record['ok'], 'results': len(record['results']), 'failures': len(record['failures']), 'cpu_seconds': record['cpu_seconds_this_invocation']}))
    raise SystemExit(0 if record['ok'] else 1)

if __name__ == '__main__':
    main()
