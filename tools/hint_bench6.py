#!/usr/bin/env python3
"""Untrusted complete-DAG hints for independent cold Agda local checks.

These fixtures measure certificate checking (S), separately from solve-only W.
Native truth claims are not evidence: each frozen root contains decoder and
checkLocal refl obligations. No Agda process is launched by this generator.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import bench6
import frontier6
import generate6
import ref
from run_job import atomic_json


def certificate(row, direction, native, max_bytes=1024*1024):
    """Validate every reachable full-state key and reconstruct row-major hints."""
    if direction not in ('lower', 'upper'):
        raise ValueError('invalid direction')
    value = row['value']
    if type(value) is not int or not -36 <= value <= 36:
        raise ValueError('invalid signed threshold')
    for field in ('complete', 'root_validated', 'root_holds'):
        if native.get(field) is not True:
            raise ValueError('incomplete or unvalidated native graph: ' + field)
    if native.get('count_overflow') or native.get('tree_count_kind') != 'exact':
        raise ValueError('native tree count is not exact')
    if native.get('direction') != direction or native.get('threshold') != value:
        raise ValueError('native root bound mismatch')
    frontier = native.get('frontier_discs')
    if type(frontier) is not int or not 0 <= frontier <= 36:
        raise ValueError('invalid frontier')
    graph = {}
    for item in native.get('states', []):
        if item.get('turn') not in ('black', 'white'):
            raise ValueError('invalid turn')
        state = bench6.decode(('w' if item['turn'] == 'white' else 'b') + item['position'])
        key = (state, item.get('direction'), item.get('threshold'))
        if key in graph or key[1:] != (direction, value):
            raise ValueError('duplicate state or mismatched bound')
        if type(item.get('leaf')) is not bool or type(item.get('selected_index')) is not int:
            raise ValueError('invalid leaf or index')
        graph[key] = item
    if native.get('unique_dag_nodes') != len(graph):
        raise ValueError('native DAG count mismatch')
    memo, visiting = {}, set()
    def visit(state):
        key = (state, direction, value)
        if key in visiting:
            raise ValueError('cycle in native graph')
        if key in memo:
            return memo[key]
        if key not in graph:
            raise ValueError('missing required child')
        visiting.add(key)
        item = graph[key]
        children = ref.successors(state)
        expected_leaf = not children or 36-state.cells.count(0) >= frontier
        if item['leaf'] != expected_leaf:
            raise ValueError('incorrect frontier/terminal leaf')
        count = 1
        if item['leaf']:
            if item['selected_index'] != -1:
                raise ValueError('leaf carries choice')
            if not children:
                holds = ref.score(state) >= value if direction == 'lower' else ref.score(state) <= value
                if not holds:
                    raise ValueError('terminal does not satisfy bound')
                node, size = {'kind': 'leaf'}, 1
            else:
                node, size = {'kind': 'solve', 'fuel': 80}, 4
        else:
            own = state.turn == (ref.WHITE if direction == 'lower' else ref.BLACK)
            if not ref.placements(state):
                if len(children) != 1 or item['selected_index'] != -1:
                    raise ValueError('invalid compulsory pass')
                child, n, b = visit(children[0])
                node, count, size = {'kind': 'pass', 'child': child}, 1+n, 1+b
            elif own:
                index = item['selected_index']
                if not 0 <= index < len(children):
                    raise ValueError('choice index out of row-major range')
                child, n, b = visit(children[index])
                node = {'kind': 'choice', 'index': index, 'child': child}
                count, size = 1+n, len(f'C{index};')+b
            else:
                if item['selected_index'] != -1:
                    raise ValueError('opponent carries choice')
                parts = [visit(child) for child in children]
                node = {'kind': 'fork', 'children': [part[0] for part in parts]}
                count = 1+sum(part[1] for part in parts)
                size = len(f'F{len(children)};')+sum(part[2] for part in parts)
        if size > max_bytes:
            raise ValueError('encoded certificate exceeds byte cap')
        visiting.remove(key)
        memo[key] = node, count, size
        return memo[key]
    node, count, size = visit(bench6.decode(row['state']))
    if len(memo) != len(graph):
        raise ValueError('unreachable native states')
    if count != native.get('tree_nodes_S'):
        raise ValueError('expanded tree count differs from native S')
    encoded = generate6.encode_local(node)
    if len(encoded.encode('ascii')) != size:
        raise ValueError('encoding byte count mismatch')
    return encoded, count


def proof_text(row, direction, encoded):
    player = 'white' if direction == 'lower' else 'black'
    threshold = f"{'pos' if row['value'] >= 0 else 'neg'} {abs(row['value'])}"
    return bench6.OPTIONS + f'''-- Untrusted generated hints; independent safe decoder and local checker facts.
module Tests.Bench6.Check where

open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (white; black)
open import Game.Composite using (LocalCertificate; localLeaf; checkLocal)
open import Othello.Board using (State; six; initial)
open import Othello.Encode6 using (decodeState; decodeLocal)
open import Tests.Bench6.Goals
import Othello.Fast6 as Fast

position : State six
position = fromMaybe (initial six) (decodeState "{row['state']}")

decoded-position : decodeState "{row['state']}" ≡ just position
decoded-position = refl

encoded : String
encoded = "{encoded}"

certificate : LocalCertificate
certificate = fromMaybe localLeaf (decodeLocal encoded)

decoded-certificate : decodeLocal encoded ≡ just certificate
decoded-certificate = refl

accepted : checkLocal Fast.fastGame6 {player} ({direction}Goal ({threshold})) position certificate ≡ true
accepted = refl
'''


def emit(row, direction, native, output, max_bytes):
    encoded, count = certificate(row, direction, native, max_bytes)
    job = bench6.freeze(row, 'fast', direction, output)
    old = Path(job['root'])
    label = f"hints6-{row['id']}-fast-{direction}"
    root = old.with_name(label)
    if root.exists():
        raise ValueError('fixture already exists: ' + str(root))
    old.rename(root)
    old.with_name(job['label'] + '.job.json').unlink()
    (root/'src/Tests/Bench6/Check.agda').write_text(proof_text(row, direction, encoded))
    manifest = bench6.refresh_manifest(root)
    job.update(format='othello-local-hint-bench6-job-v1', label=label, root=str(root),
               search_kind='local-certificate', hint_tree_S=count,
               encoded_bytes=len(encoded), encoded_sha256=hashlib.sha256(encoded.encode('ascii')).hexdigest(),
               source_sha256=manifest['source_sha256'], native_measurement=native,
               trust='untrusted generator; Agda acceptance pending')
    atomic_json(root.with_name(label+'.job.json'), job)
    return job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=bench6.ROOT/'results/bench6/dataset.json')
    parser.add_argument('--output', type=Path, default=bench6.ROOT/'results/hint-bench6')
    parser.add_argument('--ids', default='e08s07,e10s15,e12s06')
    parser.add_argument('--max-bytes', type=int, default=1024*1024)
    parser.add_argument('--max-nodes', type=int, default=2000000)
    parser.add_argument('--tt-bits', type=int, choices=(18,20), default=18)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to((bench6.ROOT/'results').resolve()):
        parser.error('--output must be under results/')
    rows = {row['id']:row for row in json.loads(args.dataset.read_text())['states']}
    for identifier in args.ids.split(','):
        row = rows[identifier]
        for direction in ('lower','upper'):
            native = frontier6.query(bench6.decode(row['state']), direction=direction,
                threshold=row['value'], frontier_discs=36, emit_states=True,
                max_states=100000, max_nodes=args.max_nodes, max_cpu_seconds=5,
                tt_bits=args.tt_bits, timeout=15)
            try:
                job = emit(row, direction, native, args.output, args.max_bytes)
            except ValueError as error:
                args.output.mkdir(parents=True, exist_ok=True)
                atomic_json(args.output/f'hints6-{identifier}-{direction}.rejected.json',
                            {'id':identifier, 'direction':direction, 'error':str(error), 'native':native})
                raise
            print(json.dumps({key:job[key] for key in ('label','hint_tree_S','native_W','encoded_bytes','source_sha256','root')}), flush=True)


if __name__ == '__main__':
    main()
