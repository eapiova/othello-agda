#!/usr/bin/env python3
"""Untrusted generator for layered (citation-sharing) 6x6 certificates.

AI-assisted. Output is checked by Agda (Game.Shared.acceptShared); the Python
replay below is only an early rejection gate, never evidence. Entries are
emitted children-first so every citation 'K' refers to an earlier entry.
"""
from __future__ import annotations
import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path
import bench6
import ref
from generate6 import encode_state
from run_job import atomic_json

FUEL = 80


def score_ok(state, direction, threshold):
    score = ref.score(state)
    return score >= threshold if direction == 'lower' else score <= threshold


def forcing_player(direction):
    return ref.WHITE if direction == 'lower' else ref.BLACK


def graph_from_native(native, root, direction, threshold):
    """Validated choice map from a native frontier graph (as hint_bench6 does)."""
    for field in ('complete', 'root_validated', 'root_holds'):
        if native.get(field) is not True:
            raise ValueError('incomplete or unvalidated native graph: ' + field)
    if native.get('direction') != direction or native.get('threshold') != threshold:
        raise ValueError('native root bound mismatch')
    frontier = native['frontier_discs']
    nodes = {}
    for item in native['states']:
        state = bench6.decode(('w' if item['turn'] == 'white' else 'b') + item['position'])
        if state in nodes or item.get('direction') != direction or item.get('threshold') != threshold:
            raise ValueError('duplicate state or mismatched bound')
        nodes[state] = item
    if root not in nodes:
        raise ValueError('root absent from native graph')
    choice = {}
    def leaf_kind(state, children):
        if not children:
            if not score_ok(state, direction, threshold):
                raise ValueError('terminal does not satisfy bound')
            return 'leaf'
        if 36 - state.cells.count(0) >= frontier:
            return 'solve'
        return None
    seen = set()
    stack = [root]
    while stack:
        state = stack.pop()
        if state in seen:
            continue
        seen.add(state)
        item = nodes.get(state)
        if item is None:
            raise ValueError('missing required child')
        children = ref.successors(state)
        kind = leaf_kind(state, children)
        if (kind is not None) != item['leaf']:
            raise ValueError('incorrect frontier/terminal leaf')
        if kind is not None:
            choice[state] = (kind, [])
            continue
        if not ref.placements(state):
            choice[state] = ('pass', [children[0]])
        elif state.turn == forcing_player(direction):
            index = item['selected_index']
            if not 0 <= index < len(children):
                raise ValueError('choice index out of range')
            choice[state] = (('choice', index), [children[index]])
        else:
            choice[state] = ('fork', list(children))
        stack.extend(choice[state][1])
    return choice


def graph_from_search(root, direction, threshold, max_states=200000):
    """Exact small-position AND/OR search with memo; for laptop fixtures only."""
    target = forcing_player(direction)
    memo = {}
    def holds(state):
        if state in memo:
            return memo[state][0]
        if len(memo) > max_states:
            raise ValueError('search state cap exceeded')
        children = ref.successors(state)
        if not children:
            memo[state] = (score_ok(state, direction, threshold), ('leaf', []))
        elif not ref.placements(state):
            memo[state] = (holds(children[0]), ('pass', [children[0]]))
        elif state.turn == target:
            memo[state] = (False, None)
            for index, child in enumerate(children):
                if holds(child):
                    memo[state] = (True, (('choice', index), [child]))
                    break
        else:
            memo[state] = (all(holds(child) for child in children), ('fork', list(children)))
        return memo[state][0]
    if not holds(root):
        raise ValueError('bound does not hold at root')
    choice = {}
    stack = [root]
    while stack:
        state = stack.pop()
        if state in choice:
            continue
        choice[state] = memo[state][1]
        stack.extend(choice[state][1])
    return choice


def layered(choice, root, min_indegree=2):
    """Choose shared internal nodes and emit entries children-first."""
    indegree = {}
    for kind, children in choice.values():
        for child in children:
            indegree[child] = indegree.get(child, 0) + 1
    shared = {s for s, k in indegree.items()
              if k >= min_indegree and choice[s][0] not in ('leaf', 'solve')}
    entries, emitted = [], set()
    stats = {'tokens': 0, 'citations': 0}
    sys.setrecursionlimit(10000)
    def body(state, top):
        if state in shared and not top:
            ensure(state)
            stats['citations'] += 1
            stats['tokens'] += 1
            return 'K'
        kind, children = choice[state]
        stats['tokens'] += 1
        if kind == 'leaf':
            return 'L'
        if kind == 'solve':
            return f'S{FUEL};'
        if kind == 'pass':
            return 'P' + body(children[0], False)
        if kind == 'fork':
            return f'F{len(children)};' + ''.join(body(c, False) for c in children)
        return f'C{kind[1]};' + body(children[0], False)
    def ensure(state):
        if state in emitted:
            return
        text = body(state, True)
        emitted.add(state)
        entries.append((state, text))
    ensure(root)
    tree = expanded_size(choice, root)
    return entries, {'unique_nodes': len(choice), 'shared_entries': len(shared),
                     'entries': len(entries), 'checked_tokens': stats['tokens'],
                     'citations': stats['citations'], 'expanded_tree_nodes': tree}


def expanded_size(choice, root):
    memo = {}
    def size(state):
        if state not in memo:
            memo[state] = 1 + sum(size(c) for c in choice[state][1])
        return memo[state]
    sys.setrecursionlimit(10000)
    return size(root)


def replay(entries, root, direction, threshold):
    """Independent re-implementation of acceptShared over the scalar rules."""
    target = forcing_player(direction)
    known = set()
    def parse(text, i, state):
        token = text[i]
        children = ref.successors(state)
        if token == 'K':
            return state in known, i + 1
        if token == 'L':
            return (not children) and score_ok(state, direction, threshold), i + 1
        if token == 'S':
            j = text.index(';', i)
            raise ValueError('solve leaves are not replayed here')
        if token == 'P':
            ok = len(children) == 1 and not ref.placements(state) and bool(ref.placements(children[0]))
            inner, j = parse(text, i + 1, children[0]) if children else (False, i + 1)
            return ok and inner, j
        j = text.index(';', i)
        n = int(text[i + 1:j])
        if token == 'C':
            ok = bool(children) and state.turn == target and n < len(children)
            inner, k = parse(text, j + 1, children[n]) if ok else (False, j + 1)
            return ok and inner, k
        if token == 'F':
            ok = bool(children) and state.turn != target and n == len(children)
            k, all_ok = j + 1, ok
            for child in children[:n]:
                inner, k = parse(text, k, child)
                all_ok = all_ok and inner
            return all_ok, k
        raise ValueError('bad token')
    for state, text in entries:
        ok, end = parse(text, 0, state)
        if not ok or end != len(text):
            return False
        known.add(state)
    return root in known


def encode(entries):
    return ''.join(encode_state(s) + text for s, text in entries)


AGDA = '''-- Untrusted generated layered certificate; Agda decodes and checks it.
module Tests.Bench6.SharedCheck where

open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (white; black; Guarantees)
open import Game.Shared using (SharedEntry; acceptShared; acceptShared-sound)
open import Othello.Board using (State; six; initial)
open import Othello.Encode6 using (decodeState)
open import Othello.Shared6 using (keyed6; decodeSharedEntries)
open import Tests.Bench6.Goals
import Othello.Fast6 as Fast

position : State six
position = fromMaybe (initial six) (decodeState "{state}")

decoded-position : decodeState "{state}" ≡ just position
decoded-position = refl

encoded : String
encoded = "{encoded}"

entries : List (SharedEntry (State six))
entries = fromMaybe [] (decodeSharedEntries encoded)

decoded-entries : decodeSharedEntries encoded ≡ just entries
decoded-entries = refl

accepted : acceptShared keyed6 Fast.fastGame6 {player} ({direction}Goal ({threshold})) entries position ≡ true
accepted = refl

guaranteed : Guarantees Fast.fastGame6 {player} ({direction}Goal ({threshold})) position
guaranteed = acceptShared-sound keyed6 Fast.fastGame6 {player} ({direction}Goal ({threshold})) entries position accepted
'''


def agda_text(state, direction, threshold, encoded):
    # The OPTIONS pragma contains braces, so it is prepended after formatting.
    return bench6.OPTIONS + AGDA.format(state=state, encoded=encoded,
                       player='white' if direction == 'lower' else 'black',
                       direction=direction,
                       threshold=f"{'pos' if threshold >= 0 else 'neg'} {abs(threshold)}")


def build(args):
    root = bench6.decode(args.state)
    if args.native:
        choice = graph_from_native(json.loads(Path(args.native).read_text()), root,
                                   args.direction, args.threshold)
    else:
        choice = graph_from_search(root, args.direction, args.threshold)
    entries, stats = layered(choice, root, args.min_indegree)
    if args.min_indegree > 10**8:
        stats['mode'] = 'tree'
    if not replay(entries, root, args.direction, args.threshold):
        raise ValueError('independent replay rejected the layered certificate')
    encoded = encode(entries)
    stats.update(encoded_bytes=len(encoded), state=args.state, direction=args.direction,
                 threshold=args.threshold, trust='untrusted generator; Agda acceptance required')
    return encoded, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', required=True, help='b/w followed by 36 cells')
    parser.add_argument('--direction', choices=('lower', 'upper'), required=True)
    parser.add_argument('--threshold', type=int, required=True)
    parser.add_argument('--native', help='native frontier graph JSON; default: exact search')
    parser.add_argument('--min-indegree', type=int, default=2,
                        help='share nodes with at least this many parents')
    parser.add_argument('--agda', help='write a Tests.Bench6.SharedCheck module here')
    parser.add_argument('--stats', help='write statistics JSON here')
    args = parser.parse_args()
    encoded, stats = build(args)
    if args.agda:
        Path(args.agda).write_text(agda_text(args.state, args.direction, args.threshold, encoded))
    if args.stats:
        atomic_json(Path(args.stats), stats)
    print(json.dumps(stats))


if __name__ == '__main__':
    main()
