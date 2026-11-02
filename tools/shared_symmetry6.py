#!/usr/bin/env python3
"""AI-assisted untrusted D4 layered generator; only Agda acceptance is evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from functools import lru_cache
import bench6
import ref
import shared6
import symmetry_stats6 as sym
from generate6 import encode_state


def normalize(graph):
    """Fold complete states, transporting the selected successor, never its index."""
    result = {}
    for state, (kind, children) in graph.items():
        representative, tag = sym.canonical(state)
        moved = [sym.transform(c, tag) for c in children]
        if isinstance(kind, tuple):
            kind = ('choice', ref.successors(representative).index(moved[0]))
        elif kind == 'fork':
            ordered = list(ref.successors(representative))
            if set(moved) != set(ordered) or len(moved) != len(ordered):
                raise ValueError('missing opponent branch')
            moved = ordered
        result.setdefault(representative, (kind, moved))
    return result


def validate_graph(graph, root, direction, threshold):
    target = shared6.forcing_player(direction)
    active, seen = set(), set()
    def visit(state):
        if state in active:
            raise ValueError('cycle')
        if state in seen:
            return
        active.add(state)
        kind, children = graph[state]
        actual = list(ref.successors(state))
        if kind == 'leaf':
            if actual or children or not shared6.score_ok(state, direction, threshold):
                raise ValueError('bad leaf')
        elif kind == 'solve':
            if children:
                raise ValueError('bad solve')
        elif kind == 'pass':
            if ref.placements(state) or not actual or children != actual:
                raise ValueError('bad pass')
        elif kind == 'fork':
            if state.turn == target or not ref.placements(state) or children != actual:
                raise ValueError('missing opponent branch')
        elif isinstance(kind, tuple) and kind[0] == 'choice':
            i = kind[1]
            if (state.turn != target or not ref.placements(state) or type(i) is not int
                    or not 0 <= i < len(actual) or children != [actual[i]]):
                raise ValueError('bad choice')
        else:
            raise ValueError('bad node')
        for child in children:
            visit(sym.canonical(child)[0] if child not in graph else child)
        active.remove(state)
        seen.add(state)
    visit(root)
    return seen


def graph_from_native(native, root, direction, threshold):
    if direction not in ('lower', 'upper') or type(threshold) is not int or not -36 <= threshold <= 36:
        raise ValueError('invalid bound')
    states = native.get('states')
    if type(states) is not list:
        raise ValueError('missing states')
    keys = set()
    for item in states:
        key = sym.item_key(item)
        if key in keys:
            raise ValueError('duplicate state')
        keys.add(key)
    raw = shared6.graph_from_native(native, root, direction, threshold)
    if len(raw) != len(keys):
        raise ValueError('unreachable states')
    validate_graph(raw, root, direction, threshold)
    if 'tree_nodes_S' in native and shared6.expanded_size(raw, root) != native['tree_nodes_S']:
        raise ValueError('tree token mismatch')
    graph = normalize(raw)
    validate_graph(graph, sym.canonical(root)[0], direction, threshold)
    return graph


def layered(graph, root):
    canonical_root, root_tag = sym.canonical(root)
    indegree = {}
    for _, children in graph.values():
        for child in children:
            representative = sym.canonical(child)[0]
            indegree[representative] = indegree.get(representative, 0) + 1
    split = {s for s, n in indegree.items() if n >= 2} | {canonical_root}
    entries, known, active = [], set(), set()
    def body(actual, top=False):
        representative, tag = sym.canonical(actual)
        if representative in known:
            return f'R{tag};'
        if representative in split and not top:
            ensure(representative)
            return f'R{tag};'
        if representative in active and not top:
            raise ValueError('cycle')
        kind, canonical_children = graph[representative]
        if kind == 'leaf':
            return 'L'
        if kind == 'solve':
            return f'S{shared6.FUEL};'
        actual_children = ref.successors(actual)
        if kind == 'pass':
            return 'P' + body(actual_children[0])
        if kind == 'fork':
            return f'F{len(actual_children)};' + ''.join(body(c) for c in actual_children)
        chosen = sym.transform(canonical_children[0], sym.INVERSES[tag])
        index = actual_children.index(chosen)
        return f'C{index};' + body(chosen)
    def ensure(state):
        if state in known:
            return
        if state in active:
            raise ValueError('cycle')
        active.add(state)
        text = body(state, True)
        active.remove(state)
        entries.append((state, text))
        known.add(state)
    ensure(canonical_root)
    if root != canonical_root:
        entries.append((root, f'R{root_tag};'))
    stats = dict(canonical_classes=len(graph), entries=len(entries),
                 checked_tokens=sum(sum(c in 'LCFPSKR' for c in t) for _, t in entries),
                 citations=sum(t.count('R') for _, t in entries),
                 nonidentity_citations=sum(t.count(f'R{i};') for _, t in entries for i in range(1,8)))
    return entries, stats


def replay(entries, root, direction, threshold):
    """Scalar rules/parser replay: each reference must find an earlier exact state."""
    known = set()
    target = shared6.forcing_player(direction)
    @lru_cache(None)
    def solve(state, fuel):
        if not fuel:
            return False
        children = ref.successors(state)
        if not children:
            return shared6.score_ok(state, direction, threshold)
        values = [solve(c, fuel-1) for c in children]
        return any(values) if state.turn == target else all(values)
    def parse(text, offset, state):
        token = text[offset]
        offset += 1
        if token == 'K':
            return state in known, offset
        children = ref.successors(state)
        if token == 'L':
            return not children and shared6.score_ok(state, direction, threshold), offset
        if token == 'P':
            if ref.placements(state) or len(children) != 1 or not ref.placements(children[0]):
                return False, offset
            return parse(text, offset, children[0])
        end = text.index(';', offset)
        digits = text[offset:end]
        if not digits or not digits.isascii() or not digits.isdecimal():
            return False, end+1
        n, offset = int(digits), end+1
        if n > 128:
            return False, offset
        if token == 'R':
            return n < 8 and sym.transform(state, n) in known, offset
        if token == 'S':
            return solve(state, n), offset
        if token == 'C':
            if state.turn != target or not ref.placements(state) or n >= len(children):
                return False, offset
            return parse(text, offset, children[n])
        if token == 'F':
            if state.turn == target or not ref.placements(state) or n != len(children):
                return False, offset
            for child in children:
                ok, offset = parse(text, offset, child)
                if not ok:
                    return False, offset
            return True, offset
        return False, offset
    try:
        for state, text in entries:
            ok, end = parse(text, 0, state)
            if not ok or end != len(text):
                return False
            known.add(state)
        return root in known
    except (ValueError, IndexError, RecursionError):
        return False


def build(native, root, direction, threshold):
    graph = graph_from_native(native, root, direction, threshold)
    entries, stats = layered(graph, root)
    if not replay(entries, root, direction, threshold):
        raise ValueError('independent replay rejected')
    encoded = shared6.encode(entries)
    stats.update(encoded_bytes=len(encoded), direction=direction, threshold=threshold,
                 trust='untrusted generator; Agda acceptance required')
    return encoded, stats


def fixture_text(state, certificates):
    text = bench6.OPTIONS + '''-- AI-assisted untrusted fixture; acceptance checked by the safe kernel.
module Tests.GeneratedSharedSymmetry6 where
open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (white; black; Guarantees)
open import Game.Shared using (SharedEntry; acceptSharedBy; acceptSharedBy-sound)
open import Othello.Board using (State; six; initial)
open import Othello.Encode6 using (decodeState)
open import Othello.Shared6 using (keyed6; decodeSharedEntries)
open import Othello.SharedSymmetry6 using (lowerTransport6; upperTransport6)
open import Othello.Statements using (lowerGoal; upperGoal)
import Othello.Fast6 as Fast

'''
    text += f'position : State six\nposition = fromMaybe (initial six) (decodeState "{encode_state(state)}")\n\n'
    for direction, encoded in certificates.items():
        player = 'white' if direction == 'lower' else 'black'
        prefix = f'{direction}'
        args = f'keyed6 Fast.fastGame6 {player} ({direction}Goal 4) {direction}Transport6 {prefix}Entries position'
        text += f'''{prefix}Encoded : String
{prefix}Encoded = "{encoded}"
{prefix}Entries : List (SharedEntry (State six))
{prefix}Entries = fromMaybe [] (decodeSharedEntries {prefix}Encoded)
{prefix}Decoded : decodeSharedEntries {prefix}Encoded ≡ just {prefix}Entries
{prefix}Decoded = refl
{prefix}Accepted : acceptSharedBy {args} ≡ true
{prefix}Accepted = refl
{prefix}Guaranteed : Guarantees Fast.fastGame6 {player} ({direction}Goal 4) position
{prefix}Guaranteed = acceptSharedBy-sound {args} {prefix}Accepted

'''
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--state', required=True)
    parser.add_argument('--direction', choices=('lower', 'upper'), required=True)
    parser.add_argument('--threshold', type=int, required=True)
    args = parser.parse_args()
    encoded, stats = build(json.loads(args.native.read_text()), bench6.decode(args.state), args.direction, args.threshold)
    print(json.dumps(dict(stats, encoded=encoded)))

if __name__ == '__main__':
    main()
