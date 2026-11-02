#!/usr/bin/env python3
"""Untrusted eight-root C-canonical certificate pilot; no initial-board claim.

emit validates every native row against scalar rules and freezes four training
and four heldout roots before measurement. check reuses only same-machine
generic interfaces, checks new shards cold, and preserves accepted prefixes.
Heldout checking requires a prospectively pinned parent-authored forecast.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import re
import shutil

import assembly6
import bench6
from cache_resume6 import copy_interface
import global_assembly6 as assembly
import global_shared6 as shared
from generate6 import encode_state
from provenance import digest_entries, source_files, source_identity
import ref
from run_job import atomic_json, run_job
import shared6
import shared_symmetry6 as single
import symmetry_stats6 as symmetry

FORMAT = 'othello-census-pilot6-v1'
PREFIX = 'Tests.CensusPilot6'
HEADER = ('{-# OPTIONS --save-metas --safe --without-K --cubical-compatible '
          '-WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n')


def state(position, turn):
    if (type(position) is not str or len(position) != 36 or
            any(c not in '012' for c in position) or turn not in ('black', 'white')):
        raise ValueError('invalid absolute position or turn')
    return ref.State(6, tuple(map(int, position)), ref.BLACK if turn == 'black' else ref.WHITE)


@lru_cache(maxsize=200000)
def ccanonical(s):
    """Native padded mover-relative (P,O) minimum, independent of string order."""
    def key(cells):
        p = sum(1 << ((i // 6 + 1) * 8 + i % 6 + 1)
                for i, c in enumerate(cells) if c == s.turn)
        o = sum(1 << ((i // 6 + 1) * 8 + i % 6 + 1)
                for i, c in enumerate(cells) if c not in (0, s.turn))
        return p, o
    images = []
    for t in range(8):
        cells = [0] * 36
        for r in range(6):
            for c in range(6):
                y, x = (c, r) if t & 4 else (r, c)
                if t & 2: y = 5 - y
                if t & 1: x = 5 - x
                cells[y * 6 + x] = s.cells[r * 6 + c]
        images.append(tuple(cells))
    return ref.State(6, min(images, key=key), s.turn)


def validate_sample(sample):
    """Require exact complete forcing graph, including honest expanded counters."""
    direction = sample.get('direction')
    if direction not in ('lower', 'upper') or type(sample.get('threshold')) is not int or sample['threshold'] != 4:
        raise ValueError('wrong direction or bound')
    if any(sample.get(k) is not True for k in ('complete', 'root_validated', 'root_holds')):
        raise ValueError('incomplete or invalid root')
    if type(sample.get('frontier_discs')) is not int or sample['frontier_discs'] != 36:
        raise ValueError('requires terminal frontier')
    root = state(sample.get('root_position'), sample.get('root_turn'))
    rows = sample.get('states')
    if type(rows) is not list or not rows:
        raise ValueError('missing rows')
    graph = {}
    target = shared6.forcing_player(direction)
    for row in rows:
        s = state(row.get('position'), row.get('turn'))
        if s != ccanonical(s): raise ValueError('row is not C canonical')
        if s in graph: raise ValueError('duplicate row')
        if row.get('direction') != direction or type(row.get('threshold')) is not int or row['threshold'] != 4:
            raise ValueError('row direction or threshold mismatch')
        if type(row.get('leaf')) is not bool: raise ValueError('invalid leaf flag')
        children = list(ref.successors(s))
        if row['leaf']:
            if children or not shared6.score_ok(s, direction, 4): raise ValueError('wrong terminal bound')
            kind, chosen = 'leaf', []
        elif not children:
            raise ValueError('terminal marked nonleaf')
        elif not ref.placements(s):
            kind, chosen = 'pass', children
        elif s.turn != target:
            kind, chosen = 'fork', children
        else:
            i = row.get('selected_index')
            if type(i) is not int or not 0 <= i < len(children): raise ValueError('invalid selected index')
            kind, chosen = ('choice', i), [children[i]]
        graph[s] = kind, chosen
    seen, active, sizes = set(), set(), {}
    def visit(s):
        s = ccanonical(s)
        if s in active: raise ValueError('cycle')
        if s in seen: return sizes[s]
        if s not in graph: raise ValueError('missing opponent reply or selected child row')
        active.add(s)
        sizes[s] = 1 + sum(visit(c) for c in graph[s][1])
        active.remove(s); seen.add(s)
        return sizes[s]
    tree = visit(root)
    if seen != set(graph): raise ValueError('unreachable row')
    for name, count in (('unique_dag_nodes', len(graph)), ('tree_nodes_S', tree)):
        if type(sample.get(name)) is not int or sample[name] != count:
            raise ValueError('dishonest ' + name)
    normalized = single.normalize(graph)
    visited = single.validate_graph(normalized, symmetry.canonical(root)[0], direction, 4)
    if visited != set(normalized): raise ValueError('unreachable normalized graph')
    return root, normalized


def prepare_samples(payload, seed):
    samples = payload.get('samples')
    if type(samples) is not list or len(samples) < 8: raise ValueError('requires at least eight samples')
    keys = [(s.get('direction'), ccanonical(state(s.get('root_position'), s.get('root_turn')))) for s in samples]
    if len(set(keys)) != len(keys): raise ValueError('duplicate sample root')
    # Sampling is fixed before validation/generation/timing; no selection by cost.
    picked = random.Random(seed).sample(range(len(samples)), 8)
    return [(i, samples[i]) for i in picked]


def private_source(text):
    """Hide helper imports so warnings and reduction do not leak through exports."""
    head, body = text.split(' where\n', 1)
    body = body.lstrip('\n')
    marker = '\nimports :' if '\nimports :' in body else '\nposition0 :'
    helper, public = body.split(marker, 1)
    result = HEADER + 'module ' + head.split('\nmodule ', 1)[1] + ' where\n\n'
    result += 'private\n' + ''.join('  ' + line + '\n' if line else '\n' for line in helper.splitlines())
    result += marker + public
    result = result.replace('accepted = refl\n', 'accepted = refl {x = true}\n')
    # The proof fields are already abstract. Keep the record constructor
    # transparent: a later shard must compute exportStates during checking.
    return result


def root_sources(graph, root, direction, index, max_tokens, max_entries, forced_splits=()):
    entries, refs, stats = shared.layered_many(graph, [root], forced_splits)
    if not shared.replay_many(entries, [root], direction, 4): raise ValueError('independent replay failed')
    plan = dict(format='othello-global-shared6-plan-v1', direction=direction, threshold=4,
                roots=[encode_state(root)], entries=[dict(state=encode_state(s), certificate=t,
                    references=sorted(encode_state(r) for r in refs[s])) for s, t in entries])
    assembly.validate_plan(plan)
    parts, owners = assembly.partition(plan['entries'], max_tokens, max_entries)
    namespace = PREFIX + f'.Root{index}'
    sources, targets, ancestors = {}, [], []
    for j, part in enumerate(parts):
        text, deps, wire_bytes = assembly.part_source(j, part, owners, direction)
        text = private_source(text.replace(assembly.PREFIX, namespace))
        closure = set(deps)
        for dependency in deps:
            closure.update(ancestors[dependency])
        ancestors.append(closure)
        cited = {r for entry in part for r in entry['references'] if owners[r] != j}
        path = 'src/' + namespace.replace('.', '/') + f'/Part{j}.agda'
        sources[path] = text
        targets.append(dict(path=path, kind='part', root_index=index, part=j,
            entries=len(part), tokens=sum(assembly.tokens(e['certificate']) for e in part),
            compact_bytes=wire_bytes, dependencies=deps, source_bytes=len(text.encode()),
            imported_citations=len(cited), transitive_parts=len(closure),
            transitive_entries=sum(len(parts[k]) for k in closure)))
    path = 'src/' + namespace.replace('.', '/') + '/Check.agda'
    sources[path] = private_source(assembly.assembly_source(plan['roots'], owners, direction).replace(assembly.PREFIX, namespace))
    owner = owners[encode_state(root)]
    assembly_parts = ancestors[owner] | {owner}
    targets.append(dict(path=path, kind='assembly', root_index=index,
        source_bytes=len(sources[path].encode()), transitive_parts=len(assembly_parts),
        transitive_entries=sum(len(parts[k]) for k in assembly_parts)))
    return sources, targets, stats


def emit(args):
    output = args.output.resolve()
    if output.exists() or 'results' not in output.parts: raise ValueError('fresh isolated results root required')
    raw = args.samples.read_bytes()
    chosen = prepare_samples(json.loads(raw), args.seed)
    sources, roots, targets = {}, [], []
    for index, (source_index, sample) in enumerate(chosen):
        root, graph = validate_sample(sample)
        degrees = [r.get('global_indegree') for r in sample['states']]
        if any(type(d) is not int or d < 0 for d in degrees):
            raise ValueError('pilot requires full-graph citation counts')
        forced = {symmetry.canonical(state(r['position'],r['turn']))[0]
                  for r in sample['states'] if r['global_indegree'] >= 2 and not r['leaf']}
        emitted, jobs, stats = root_sources(graph, root, sample['direction'], index, args.max_tokens, args.max_entries, forced)
        if any(len(t.encode()) > args.max_source_bytes for t in emitted.values()): raise ValueError('source size cap')
        sources.update(emitted); targets.extend(jobs)
        roots.append(dict(index=index, source_index=source_index, phase='training' if index < 4 else 'heldout',
                          key=encode_state(root), direction=sample['direction'], native_nodes=len(graph),
                          native_tree_nodes=sample['tree_nodes_S'], full_graph_forced_splits=len(forced), **stats))
    output.mkdir(parents=True)
    for name, text in sources.items():
        p = output / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
    report = dict(format=FORMAT, accepted=False, status='emitted-unchecked', seed=args.seed,
        samples_sha256=hashlib.sha256(raw).hexdigest(), roots=roots, targets=targets,
        generated_hashes={n: hashlib.sha256(t.encode()).hexdigest() for n,t in sources.items()},
        max_tokens=args.max_tokens, max_entries=args.max_entries,
        scope='eight conditional sampled roots; no INITIAL6 theorem or population forecast',
        production_authorized=False, initial_theorem_proved=False)
    atomic_json(output / 'plan.json', report)
    print(json.dumps(dict(status=report['status'], roots=8, targets=len(targets))))


def check(args, *, required_roots=8, expected_format=FORMAT, preflight=None):
    prepared, donor, output = args.prepared.resolve(), args.donor.resolve(), args.output.resolve()
    plan = json.loads((prepared / 'plan.json').read_text())
    if plan.get('format') != expected_format or len(plan['roots']) != required_roots: raise ValueError('wrong prepared plan')
    if assembly6.sha(prepared / 'plan.json') != args.expected_plan_sha256: raise ValueError('plan changed')
    for name, digest in plan['generated_hashes'].items():
        if assembly6.sha(prepared / name) != digest: raise ValueError('generated source changed')
    machine = assembly6.machine_identity(args.agda)
    if machine['hostname'] != args.expected_hostname or machine['agda_sha256'] != args.expected_agda_sha256:
        raise ValueError('requires exact original machine and Agda binary')
    identity, pool = source_identity(donor), assembly6.interfaces(donor)
    generic = {n:d for n,d in pool.items() if '/src/Tests/' not in n}
    if (identity['source_sha256'] != args.expected_donor_source_sha256 or
            digest_entries(generic) != args.expected_generic_interfaces_sha256 or not generic):
        raise ValueError('donor source/cache identity mismatch')
    forecast = None
    if args.phase == 'heldout':
        if not args.forecast or not args.expected_forecast_sha256: raise ValueError('heldout needs pinned prospective forecast')
        if assembly6.sha(args.forecast) != args.expected_forecast_sha256: raise ValueError('forecast changed')
        forecast = json.loads(args.forecast.read_text())
        training = args.training_report
        if not training: raise ValueError('heldout needs accepted training report')
        train = json.loads(training.read_text())
        if (train.get('phase') != 'training' or not train.get('accepted') or
                train.get('plan_sha256') != args.expected_plan_sha256 or
                forecast.get('training_report_sha256') != assembly6.sha(training) or
                forecast.get('plan_sha256') != args.expected_plan_sha256 or
                set(forecast.get('root_predictions_cpu_seconds', {})) != {'4','5','6','7'} or
                any(type(v) not in (int,float) or not 0 < v < 1e12 for v in forecast['root_predictions_cpu_seconds'].values())):
            raise ValueError('forecast must pin complete training and all four unseen roots')
    if output.exists() or 'results' not in output.parts or donor in output.parents or prepared in output.parents:
        raise ValueError('new isolated results output required')
    output.mkdir(parents=True); root = output / 'check'; root.mkdir()
    for name, raw in source_files(donor):
        if name.startswith('src/Tests/') or not name.endswith(('.agda', '.agda-lib')): continue
        p = root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
    for name in plan['generated_hashes']:
        p = root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes((prepared / name).read_bytes())
    manifest = bench6.refresh_manifest(root, origin={k:identity[k] for k in ('revision','dirty')})
    for name, digest in generic.items(): copy_interface(donor / name, root / name, digest)
    selected = [t for t in plan['targets'] if (t['root_index'] < 4) == (args.phase == 'training')]
    report = dict(format=expected_format, phase=args.phase, status='checking', accepted=False,
        check_root=str(root), plan_sha256=args.expected_plan_sha256, machine=machine,
        borrowed_interfaces_sha256=digest_entries(generic), donor_source=identity,
        source_sha256=manifest['source_sha256'], phases=[], cpu_seconds=0.,
        cpu_budget=args.kernel_cpu_budget, forecast_sha256=args.expected_forecast_sha256,
        root_predictions_cpu_seconds=forecast['root_predictions_cpu_seconds'] if forecast else None,
        production_authorized=False, initial_theorem_proved=False)
    atomic_json(output / 'report.json', report)
    for t in selected:
        if preflight is not None:preflight(t)
        left = args.kernel_cpu_budget - report['cpu_seconds']
        if left < 3: report['status'] = 'cpu-stop'; break
        before = assembly6.interfaces(root)
        suffix = '/' + t['path'].removeprefix('src/').removesuffix('.agda') + '.agdai'
        if any(n.endswith(suffix) for n in before): raise ValueError('target is not cold')
        assembly_job = t['kind'] == 'assembly'
        heap, rss = (2500, 3.) if assembly_job else (1350, 1.5)
        cap = min(left - 1, args.assembly_cpu_limit if assembly_job else args.part_cpu_limit)
        label = f"root{t['root_index']}-" + ('assembly' if assembly_job else f"part{t['part']}")
        record = run_job(label, [machine['agda_path'], *assembly6.FLAGS, '--save-metas',
            '-i', 'src', t['path'], '+RTS', f'-M{heap}M', '-c', '-s', '-RTS'], output / 'records',
            root=root, expected_source_sha256=manifest['source_sha256'], cpu_limit=cap,
            timeout=cap*2+30, rss_limit_gib=rss, log_limit_mib=2,
            metadata=dict(machine=machine, own_target_cold=True,
                borrowed_interfaces_sha256=digest_entries(before), **t))
        report['cpu_seconds'] += record['cpu_seconds']
        after = assembly6.interfaces(root)
        changed = {n for n,d in before.items() if after.get(n) != d}
        report['phases'].append(dict(target=t, record=record, changed_imports=sorted(changed)))
        report['status'] = 'checking' if record['accepted'] and not changed else 'check-failed'
        atomic_json(output / 'report.json', report)
        print(json.dumps(dict(label=label, accepted=record['accepted'], cpu_seconds=record['cpu_seconds'])), flush=True)
        if report['status'] != 'checking': break
    report['donor_unchanged'] = source_identity(donor) == identity and assembly6.interfaces(donor) == pool
    report['generated_sources_unchanged'] = all(assembly6.sha(prepared / n) == d for n,d in plan['generated_hashes'].items())
    report['accepted'] = (len(report['phases']) == len(selected) and report['status'] == 'checking' and
                          report['donor_unchanged'] and report['generated_sources_unchanged'])
    if report['accepted']: report['status'] = 'complete'
    report['final_interfaces_sha256'] = digest_entries(assembly6.interfaces(root))
    atomic_json(output / 'report.json', report)
    return report['accepted']


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    e = sub.add_parser('emit'); e.add_argument('--samples', type=Path, required=True); e.add_argument('--output', type=Path, required=True)
    e.add_argument('--seed', type=int, default=2026100807); e.add_argument('--max-tokens', type=int, default=32000)
    e.add_argument('--max-entries', type=int, default=150); e.add_argument('--max-source-bytes', type=int, default=1048576)
    c = sub.add_parser('check')
    for name in ('prepared','donor','output','forecast','training-report'): c.add_argument('--'+name, type=Path, required=name in ('prepared','donor','output'))
    for name in ('agda','expected-plan-sha256','expected-hostname','expected-agda-sha256','expected-donor-source-sha256','expected-generic-interfaces-sha256'):
        c.add_argument('--'+name, required=True)
    c.add_argument('--expected-forecast-sha256'); c.add_argument('--phase', choices=('training','heldout'), required=True)
    c.add_argument('--kernel-cpu-budget', type=float, default=1200); c.add_argument('--part-cpu-limit', type=float, default=120)
    c.add_argument('--assembly-cpu-limit', type=float, default=180)
    args = p.parse_args()
    caps = (args.max_tokens,args.max_entries,args.max_source_bytes) if args.command == 'emit' else (args.kernel_cpu_budget,args.part_cpu_limit,args.assembly_cpu_limit)
    if any(not 0 < v < 1e12 for v in caps): p.error('caps must be finite and positive')
    if args.command == 'emit': emit(args); return 0
    return 0 if check(args) else 1


if __name__ == '__main__': raise SystemExit(main())
