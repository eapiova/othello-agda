#!/usr/bin/env python3
"""AI-assisted real multi-shard kernel pilot; run inside a ledger reservation.

Each shard is cold except verified earlier interfaces. Export states are
separate from abstract certificate data, avoiding repeated decoder reduction.
No initial-board solution is claimed by this sampled-position experiment.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import shutil

import assembly6
import bench6
from generate6 import encode_state
from provenance import source_files, source_identity
from run_job import atomic_json, run_job
import shared6

HEADER = bench6.OPTIONS
COMMON = '''open import Prelude
open import Game.Core using (white; black; Guarantees)
open import Game.Shared
open import Game.Soundness using (checkSound)
open import Othello.Board using (State; six; initial)
open import Othello.Shared6 using (keyed6; key6; decodeSharedEntries)
open import Othello.Encode6 using (decodeState)
open import Tests.Bench6.Goals
import Othello.Fast6 as Fast

decode : _ → State six
decode text = fromMaybe (initial six) (decodeState text)

'''


def references(graph, state, text):
    """Locate actual citation states without re-enumerating legal moves."""
    refs = set()
    def visit(s, offset):
        token = text[offset]
        kind, children = graph[s]
        if token == 'K':
            refs.add(s)
            return offset + 1
        if token == 'L':
            if kind != 'leaf': raise ValueError('nonterminal leaf')
            return offset + 1
        if token == 'P':
            if kind != 'pass': raise ValueError('incorrect pass')
            return visit(children[0], offset + 1)
        end = text.index(';', offset)
        count = int(text[offset + 1:end])
        if token == 'S': return end + 1
        if token == 'C':
            if kind != ('choice', count): raise ValueError('wrong choice index')
            return visit(children[0], end + 1)
        if token != 'F' or kind != 'fork' or count != len(children):
            raise ValueError('wrong fork coverage')
        offset = end + 1
        for child in children: offset = visit(child, offset)
        return offset
    if visit(state, 0) != len(text): raise ValueError('trailing certificate tokens')
    return refs


def partition(entries, graph, count):
    if count < 2 or len(entries) < count: raise ValueError('too few entries for shard count')
    target = max(1, sum(sum(t.count(c) for c in 'LSPCFK') for _, t in entries) // count)
    entry_target = (len(entries) + count - 1) // count
    parts, owners, part, tokens = [], {}, [], 0
    for state, text in entries:
        refs = references(graph, state, text)
        if not refs <= owners.keys(): raise ValueError('self or forward citation')
        n = sum(text.count(c) for c in 'LSPCFK')
        if part and (tokens >= target or len(part) >= entry_target) and len(parts) < count - 1:
            parts.append(part); part, tokens = [], 0
        owners[state] = len(parts)
        part.append((state, text, refs)); tokens += n
    if part: parts.append(part)
    return parts, owners


def part_source(index, part, owners, direction):
    player = 'white' if direction == 'lower' else 'black'
    goal = f'({direction}Goal (pos 4))'
    dependencies = sorted({owners[r] for s, t, refs in part for r in refs if owners[r] != index})
    imports = ''.join(f'import Tests.SharedAssembly6.Part{j} as P{j}\n' for j in dependencies)
    selected = []
    for j in dependencies:
        cited = sorted({r for _, _, refs in part for r in refs if owners[r] == j}, key=encode_state)
        keys = ' ∷ '.join(f'key6 (decode "{encode_state(s)}")' for s in cited) + ' ∷ []'
        selected.append(f'selectExport ({keys}) P{j}.export')
    import_list = ' ∷ '.join(selected) + (' ∷ []' if dependencies else '[]')
    entries = [(s, text) for s, text, _ in part]
    # shardStates uses earlier-list entries on collision. Preserve that order.
    states = 'tip'
    for s, _ in reversed(entries):
        literal = encode_state(s)
        states = f'insertT (key6 (decode "{literal}")) (decode "{literal}") ({states})'
    text = HEADER + f'module Tests.SharedAssembly6.Part{index} where\n\n' + COMMON + imports
    text += f'''
imports : List (CheckedExport Fast.fastGame6 {player} {goal})
imports = {import_list}

states : Trie (State six)
states = {states}

abstract
  entries : List (SharedEntry (State six))
  entries = fromMaybe [] (decodeSharedEntries "{shared6.encode(entries)}")

  shape : shardStates keyed6 entries ≡ states
  shape = refl

  accepted : checkShard keyed6 Fast.fastGame6 {player} {goal} imports entries ≡ true
  accepted = refl

  sound : AllT (Proven Fast.fastGame6 {player} {goal}) states
  sound = subst (AllT (Proven Fast.fastGame6 {player} {goal})) shape
    (shard-sound keyed6 Fast.fastGame6 {player} {goal} imports entries accepted)

export : CheckedExport Fast.fastGame6 {player} {goal}
export = checkedExport states sound
'''
    return text, dependencies


def assembly_source(index, state, direction):
    player = 'white' if direction == 'lower' else 'black'
    goal = f'({direction}Goal (pos 4))'
    return HEADER + 'module Tests.SharedAssembly6.Check where\n\n' + COMMON + f'''
import Tests.SharedAssembly6.Part{index} as P

position : State six
position = decode "{encode_state(state)}"

accepted : knownIn keyed6 P.states position ≡ true
accepted = refl

guaranteed : Guarantees Fast.fastGame6 {player} {goal} position
guaranteed with knownIn-sound keyed6 Fast.fastGame6 {player} {goal}
  P.states position P.sound accepted
... | c , ok = checkSound Fast.fastGame6 {player} {goal} position c ok
'''


def run(args):
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    native = json.loads(args.native.read_text())
    state = bench6.decode(args.state)
    graph = shared6.graph_from_native(native, state, args.direction, 4)
    entries, stats = shared6.layered(graph, state)
    if not shared6.replay(entries, state, args.direction, 4): raise ValueError('scalar replay rejected')
    parts, owners = partition(entries, graph, args.shards)
    sources, deps = {}, {}
    for i, part in enumerate(parts):
        sources[f'src/Tests/SharedAssembly6/Part{i}.agda'], deps[i] = part_source(i, part, owners, args.direction)
        tokens = sum(sum(text.count(c) for c in 'LSPCFK') for _, text, _ in part)
        encoded_bytes = len(shared6.encode([(s,t) for s,t,_ in part]).encode())
        if tokens > args.max_tokens or encoded_bytes > args.max_encoded_bytes:
            raise ValueError(f'part {i} exceeds token/encoded-data sizing gate; increase shard count')
    sources['src/Tests/SharedAssembly6/Check.agda'] = assembly_source(owners[state], state, args.direction)
    machine = assembly6.machine_identity(args.agda)
    report = dict(format='othello-shared-assembly6-v1', machine=machine, stats=stats,
                  parts=[], dependency_graph=deps, accepted=False,
                  scope='real sampled-position certificate; no initial-board theorem',
                  direction=args.direction, state=args.state,
                  native_sha256=assembly6.sha(args.native),
                  requested_shards=args.shards, actual_shards=len(parts),
                  max_tokens=args.max_tokens, max_encoded_bytes=args.max_encoded_bytes)
    atomic_json(output / 'assembly.json', report)
    original = list(source_files(Path(__file__).resolve().parents[1]))
    completed = []

    def prepare(name):
        root = output / name; root.mkdir()
        for rel, data in original:
            path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        for rel, data in sources.items():
            path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(data)
        digest = bench6.refresh_manifest(root)['source_sha256']
        if assembly6.interfaces(root): raise ValueError('new root is not cold')
        for donor in completed:
            source_identity(donor)
            for rel, sha in assembly6.interfaces(donor).items():
                target = root / rel
                if target.exists():
                    if assembly6.sha(target) != sha: raise ValueError('conflicting dependency interfaces')
                    continue
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(donor / rel, target)
        return root, digest

    for i in range(len(parts)):
        root, digest = prepare(f'part{i}')
        record = run_job(f'shared-part{i}', [args.agda, *assembly6.FLAGS, '-i', 'src',
            f'src/Tests/SharedAssembly6/Part{i}.agda', '+RTS', '-M1200M', '-RTS'],
            output / 'records', root=root, expected_source_sha256=digest,
            cpu_limit=600, timeout=900, rss_limit_gib=1.5, log_limit_mib=2,
            metadata={'machine': machine, 'dependencies': deps[i], 'own_shard_cold': True})
        metrics = {k: record[k] for k in ['accepted','cpu_seconds','wall_seconds','peak_rss_gib','cache_state','stop_reason']}
        metrics.update(entries=len(parts[i]),
                       checked_tokens=sum(sum(t.count(c) for c in 'LSPCFK') for _,t,_ in parts[i]),
                       encoded_bytes=len(shared6.encode([(s,t) for s,t,_ in parts[i]]).encode()),
                       imported_states=len({r for _,_,refs in parts[i] for r in refs if owners[r] != i}))
        report['parts'].append(metrics)
        atomic_json(output / 'assembly.json', report)
        if not record['accepted']: return False
        completed.append(root)
    root, digest = prepare('assembly')
    record = run_job('shared-assembly', [args.agda, *assembly6.FLAGS, '-i', 'src',
        'src/Tests/SharedAssembly6/Check.agda', '+RTS', '-M1200M', '-RTS'],
        output / 'records', root=root, expected_source_sha256=digest,
        cpu_limit=180, timeout=300, rss_limit_gib=1.5, log_limit_mib=2,
        metadata={'machine': machine, 'accepted_dependency_interfaces': True})
    report['assembly'] = {k:record[k] for k in ['accepted','cpu_seconds','wall_seconds','peak_rss_gib','cache_state','stop_reason']}
    report['accepted'] = record['accepted']; atomic_json(output / 'assembly.json', report)
    return record['accepted']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--state', required=True)
    p.add_argument('--direction', choices=['lower','upper'], default='lower')
    p.add_argument('--shards', type=int, default=8)
    p.add_argument('--max-tokens', type=int, default=200000)
    p.add_argument('--max-encoded-bytes', type=int, default=1024*1024)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--agda', required=True)
    args = p.parse_args()
    if args.shards < 2 or args.max_tokens <= 0 or args.max_encoded_bytes <= 0:
        p.error('positive sizing gates and at least two shards required')
    return 0 if run(args) else 1


if __name__ == '__main__': raise SystemExit(main())
