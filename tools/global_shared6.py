#!/usr/bin/env python3
"""AI-assisted multi-root D4 proof graph pilot; all output is untrusted.

Merge compatible native certificates, emit child-first shared entries, and
replay every root with independent scalar rules. No population extrapolation
or initial-board theorem follows from this sampled graph.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

import bench6
from generate6 import encode_state
import ref
from run_job import atomic_json
import shared6
import shared_symmetry6 as single
import symmetry_stats6 as symmetry


def select_cases(profile, count, seed, direction):
    if profile.get('sample_population_kind') != 'canonical frontier full-state classes':
        raise ValueError('requires the recorded canonical frontier sample')
    source_cases = profile.get('cases', [])
    cases = [c for c in source_cases if c.get('direction') == direction and
             c.get('frontier_discs') == 36]
    if not 2 <= count <= len(cases):
        raise ValueError('invalid sampled root count')
    if any(c.get('status') != 'complete' or c.get('row', {}).get('value') != 4
           for c in cases):
        raise ValueError('incomplete or wrong-bound sample')
    keys = [c['row']['state'] for c in cases]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate sampled root')
    for key in keys:
        symmetry.validate_key(key)
        if symmetry.canonical_key(key)[0] != key:
            raise ValueError('root is not the recorded canonical representative')
    # Random subsampling preserves the sampling unit; taking the first sorted
    # 100 rows would introduce a lexicographic selection bias.
    chosen = random.Random(seed).sample(cases, count)
    return sorted(chosen, key=lambda c: c['row']['state'])


@lru_cache(maxsize=200000)
def canonical(state):
    return symmetry.canonical(state)


def reachable(graph, roots):
    seen, active = set(), set()
    def visit(s):
        if s in active:
            raise ValueError('cycle in merged graph')
        if s in seen:
            return
        if s not in graph:
            raise ValueError('missing merged child')
        active.add(s)
        for child in graph[s][1]:
            visit(canonical(child)[0])
        active.remove(s)
        seen.add(s)
    for root in roots:
        visit(canonical(root)[0])
    return seen


def layered_many(graph, roots, forced_splits=()):
    """Emit a single acyclic graph. Terminal goals stay inline, except roots."""
    roots = list(roots)
    canonical_roots = {canonical(s)[0] for s in roots}
    used = reachable(graph, roots)
    indegree = Counter(canonical(c)[0] for s in used for c in graph[s][1])
    split = {s for s, degree in indegree.items() if degree >= 2 and
             graph[s][0] not in ('leaf', 'solve')} | canonical_roots
    forced_splits = set(forced_splits)
    if not forced_splits <= used:
        raise ValueError('forced split is outside the complete graph')
    split.update(s for s in forced_splits if graph[s][0] not in ('leaf', 'solve'))
    entries, citations, known, active = [], {}, set(), set()

    def body(actual, refs, top=False):
        representative, tag = canonical(actual)
        if representative in known or (representative in split and not top):
            ensure(representative)
            refs.add(representative)
            return 'K' if tag == 0 else f'R{tag};'
        if representative in active and not top:
            raise ValueError('cyclic citation')
        kind, canonical_children = graph[representative]
        if kind == 'leaf':
            return 'L'
        if kind == 'solve':
            return f'S{shared6.FUEL};'
        actual_children = ref.successors(actual)
        if kind == 'pass':
            if len(actual_children) != 1 or ref.placements(actual):
                raise ValueError('incorrect merged pass')
            return 'P' + body(actual_children[0], refs)
        if kind == 'fork':
            return f'F{len(actual_children)};' + ''.join(body(c, refs) for c in actual_children)
        chosen = symmetry.transform(canonical_children[0], symmetry.INVERSES[tag])
        try:
            index = actual_children.index(chosen)
        except ValueError as error:
            raise ValueError('transported choice is not legal') from error
        return f'C{index};' + body(chosen, refs)

    def ensure(state):
        if state in known:
            return
        if state in active:
            raise ValueError('cyclic exported state')
        active.add(state)
        refs = set()
        text = body(state, refs, True)
        active.remove(state)
        if not refs <= known:
            raise ValueError('forward or missing citation')
        citations[state] = refs
        entries.append((state, text))
        known.add(state)

    for root in roots:
        representative, tag = canonical(root)
        ensure(representative)
        if root != representative and root not in known:
            entries.append((root, f'R{tag};'))
            citations[root] = {representative}
            known.add(root)
    stats = dict(roots=len(roots), union_canonical_states=len(graph),
                 reachable_canonical_states=len(used), entries=len(entries),
                 checked_tokens=sum(sum(c in 'LCFPSKR' for c in t) for _, t in entries),
                 citations=sum(t.count('K')+t.count('R') for _, t in entries),
                 nonidentity_citations=sum(t.count('R') for _, t in entries))
    return entries, citations, stats


def replay_many(entries, roots, direction, threshold):
    """One scalar replay of all entries, followed by all requested root lookups."""
    if direction not in ('lower', 'upper'):
        return False
    known = set()
    target = shared6.forcing_player(direction)
    @lru_cache(maxsize=50000)
    def solve(state, fuel):
        if not fuel:
            return False
        children = ref.successors(state)
        if not children:
            return shared6.score_ok(state, direction, threshold)
        results = (solve(c, fuel-1) for c in children)
        return any(results) if state.turn == target else all(results)
    def parse(text, offset, state):
        token = text[offset]
        offset += 1
        if token == 'K':
            return state in known, offset
        if token == 'R':
            end = text.index(';', offset)
            raw = text[offset:end]
            if not raw or not raw.isascii() or not raw.isdecimal():
                return False, end+1
            tag = int(raw)
            return tag < 8 and symmetry.transform(state, tag) in known, end+1
        children = ref.successors(state)
        if token == 'L':
            return not children and shared6.score_ok(state, direction, threshold), offset
        if token == 'P':
            if ref.placements(state) or len(children) != 1:
                return False, offset
            return parse(text, offset, children[0])
        end = text.index(';', offset)
        raw = text[offset:end]
        if not raw or not raw.isascii() or not raw.isdecimal():
            return False, end+1
        number, offset = int(raw), end+1
        if number > 128:
            return False, offset
        if token == 'S':
            return solve(state, number), offset
        if token == 'C':
            if state.turn != target or not ref.placements(state) or number >= len(children):
                return False, offset
            return parse(text, offset, children[number])
        if token == 'F':
            if state.turn == target or not ref.placements(state) or number != len(children):
                return False, offset
            for child in children:
                ok, offset = parse(text, offset, child)
                if not ok:
                    return False, offset
            return True, offset
        return False, offset
    try:
        for state, text in entries:
            if state in known:
                return False
            ok, end = parse(text, 0, state)
            if not ok or end != len(text):
                return False
            known.add(state)
        return bool(roots) and all(s in known for s in roots)
    except (ValueError, IndexError, RecursionError):
        return False


def encode_plan(entries, references, roots, direction):
    return dict(format='othello-global-shared6-plan-v1', direction=direction, threshold=4,
                roots=[encode_state(s) for s in roots],
                entries=[{'state':encode_state(s), 'certificate':text,
                          'references':sorted(encode_state(t) for t in references[s])}
                         for s,text in entries],
                trust='untrusted input; safe Agda checks required')


def run(args):
    import compact_shared6 as compact
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    raw = args.profile.read_bytes()
    profile = json.loads(raw)
    chosen = select_cases(profile, args.samples, args.seed, args.direction)
    baseline = json.loads(args.baseline.read_text()) if args.baseline else None
    baseline_cases = {}
    if baseline:
        if baseline.get('status') != 'complete':
            raise ValueError('incomplete baseline')
        for group in baseline['groups']:
            if group['direction'] == args.direction and group['threshold'] == 4 and group['frontier_discs'] == 36:
                baseline_cases = {case['state']:case for case in group['cases']}
    report = dict(format='othello-global-shared6-result-v1', status='building',
                  direction=args.direction, threshold=4, sample_size=len(chosen),
                  subsample_seed=args.seed, source_sample_seed=profile.get('sample_seed'),
                  source_population=profile.get('sample_population_L'),
                  source_population_kind=profile.get('sample_population_kind'),
                  profile_sha256=hashlib.sha256(raw).hexdigest(), cases=[],
                  limitations=['sample union savings are not full-population DAG savings',
                               'native generation and scalar replay are untrusted',
                               'no initial-board proof or production authorization'])
    atomic_json(output/'report.json',report)
    graph, roots, individual_tokens, individual_bytes = {}, [], 0, 0
    for case in chosen:
        root = bench6.decode(case['row']['state'])
        path = Path(case['native_path'])
        if not path.is_absolute():
            path = args.profile.parent/path
        if path.stat().st_size > args.max_input_bytes:
            raise ValueError('native input byte limit')
        native = json.loads(path.read_text())
        normalized = single.graph_from_native(native, root, args.direction, 4)
        for state,node in normalized.items():
            graph.setdefault(state,node)
        if len(graph) > args.max_states:
            raise ValueError('global state cap')
        # A separate per-root D4 baseline isolates global reuse from encoding.
        entries, _, stats = layered_many(normalized, [root])
        compact_bytes = len(compact.encode(entries).encode())
        individual_tokens += stats['checked_tokens']
        individual_bytes += compact_bytes
        old = baseline_cases.get(case['row']['state'], {})
        report['cases'].append(dict(state=case['row']['state'], id=case['row'].get('id'),
            native_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            canonical_classes=len(normalized), d4_layered_tokens=stats['checked_tokens'],
            compact_bytes=compact_bytes,
            exact_layered_tokens=old.get('checked_tokens'),
            exact_layered_bytes=old.get('layered_encoded_bytes')))
        roots.append(root)
        report['union_canonical_states']=len(graph)
        atomic_json(output/'report.json',report)
        del normalized,native,entries
    entries, refs, stats = layered_many(graph, roots)
    if not replay_many(entries, roots, args.direction, 4):
        raise ValueError('independent scalar replay rejected multi-root graph')
    compact_wire = compact.encode(entries)
    exact_tokens = [c['exact_layered_tokens'] for c in report['cases']]
    exact_bytes = [c['exact_layered_bytes'] for c in report['cases']]
    stats.update(per_root_d4_tokens=individual_tokens, per_root_compact_bytes=individual_bytes,
                 global_compact_bytes=len(compact_wire.encode()),
                 global_legacy_bytes=len(shared6.encode(entries).encode()),
                 global_token_gain=individual_tokens/stats['checked_tokens'],
                 global_compact_byte_gain=individual_bytes/len(compact_wire.encode()),
                 exact_baseline_tokens=sum(exact_tokens) if all(v is not None for v in exact_tokens) else None,
                 exact_baseline_bytes=sum(exact_bytes) if all(v is not None for v in exact_bytes) else None)
    plan=encode_plan(entries,refs,roots,args.direction)
    atomic_json(output/'plan.json',plan)
    (output/'compact.txt').write_text(compact_wire)
    report.update(status='complete', scalar_replay=True, stats=stats,
                  plan_sha256=hashlib.sha256((output/'plan.json').read_bytes()).hexdigest())
    atomic_json(output/'report.json',report)
    print(json.dumps({'status':report['status'],'stats':stats}))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--baseline',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--direction',choices=('lower','upper'),default='upper')
    p.add_argument('--samples',type=int,default=100)
    p.add_argument('--seed',type=int,default=2026100606)
    p.add_argument('--max-states',type=int,default=1500000)
    p.add_argument('--max-input-bytes',type=int,default=536870912)
    args=p.parse_args()
    if args.samples < 2 or args.max_states < 1:
        p.error('positive state cap and at least two roots required')
    run(args)


if __name__=='__main__':main()
