#!/usr/bin/env python3
"""AI-assisted phase isolation of the preserved global pilot's heap failures.

Run under one outer coordinator reservation. Original sources and accepted
interfaces are verified and never modified. Each generated target is cold in
its own root; dependencies reuse only same-machine, same-binary interfaces.
No initial-board claim or production forecast follows from these diagnostics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
import compact_shared6 as compact
import global_assembly6 as assembly
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job


PREFIX = 'Tests.MemoryProbe6'


def module_source(name, body):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*', name):
        raise ValueError('invalid diagnostic module name')
    return assembly.HEADER + f'module {PREFIX}.{name} where\n\n' + body


def part_phases(source, expected_index):
    """Cut only at named declaration boundaries, leaving earlier proofs intact."""
    marker = f'module Tests.GlobalPilot6.Part{expected_index} where\n\n'
    if marker not in source:
        raise ValueError('source is a different part')
    body = source.split(marker, 1)[1]
    boundaries = ['imports :', 'states :', 'abstract\n  entries :',
                  '  shape :', '  accepted :', '  sound :']
    offsets = [body.index(x) for x in boundaries]
    if offsets != sorted(offsets):
        raise ValueError('unexpected declaration layout')
    # States alone measures its literal construction, excluding imports values
    # and certificate data, while retaining exactly the dependency imports.
    states = body[:offsets[0]] + body[offsets[1]:offsets[2]]
    return {
        'dependencies': body[:offsets[0]],
        'imports': body[:offsets[1]],
        'states': states,
        'decode': body[:offsets[3]],
        'shape': body[:offsets[4]],
        'check': body[:offsets[5]],
        'sound': body,
    }


def root_source(roots, owners, direction, stage):
    """Use projections rather than concrete with-abstraction for Proven pairs."""
    if direction not in ('lower', 'upper') or stage not in (
            'imports', 'known', 'proven', 'fast', 'rules'):
        raise ValueError('invalid root diagnostic stage or bound')
    if not roots or len(set(roots)) != len(roots) or not set(roots) <= owners.keys():
        raise ValueError('missing, duplicate or unowned root')
    player = 'white' if direction == 'lower' else 'black'
    goal = f'({direction}Goal 4)'
    body = assembly.COMMON
    for j in sorted({owners[s] for s in roots}):
        body += f'import Tests.GlobalPilot6.Part{j} as P{j}\n'
    if stage == 'imports':
        return body
    for i, state in enumerate(roots):
        j = owners[state]
        body += f'''
position{i} : State six
position{i} = decode "{compact.pack_state(state)}"

accepted{i} : knownIn keyed6 P{j}.states position{i} ≡ true
accepted{i} = refl
'''
        if stage == 'known':
            continue
        body += f'''
proven{i} : Proven Fast.fastGame6 {player} {goal} position{i}
proven{i} = knownIn-sound keyed6 Fast.fastGame6 {player} {goal}
  P{j}.states position{i} P{j}.sound accepted{i}
'''
        if stage == 'proven':
            continue
        body += f'''
fastGuarantee{i} : Guarantees Fast.fastGame6 {player} {goal} position{i}
fastGuarantee{i} = checkSound Fast.fastGame6 {player} {goal} position{i}
  (proj₁ proven{i}) (proj₂ proven{i})
'''
        if stage == 'fast':
            continue
        body += f'''
guarantee{i} : Guarantees (Rules.game six) {player} {goal} position{i}
guarantee{i} = guarantees-transfer Fast.fastGame6 (Rules.game six)
  fastAgreement fastGuarantee{i}
'''
    return body


def rts_stats(log):
    result = {}
    for key, label in [('allocated_bytes', 'bytes allocated in the heap'),
                       ('copied_bytes', 'bytes copied during GC'),
                       ('maximum_residency_bytes', 'bytes maximum residency')]:
        match = re.search(r'([\d,]+)\s+' + label, log)
        if match:
            result[key] = int(match.group(1).replace(',', ''))
    match = re.search(r'(\d+)\s+(MiB|MB) total memory in use', log)
    if match:
        result['total_memory_in_use'] = int(match.group(1))
        result['total_memory_unit'] = match.group(2)
    return result


def run(args):
    previous = args.previous.resolve()
    old = json.loads((previous / 'assembly.json').read_text())
    machine = assembly6.machine_identity(args.agda)
    if old['status'] != 'retry-part-failed' or old['accepted'] or machine != old['machine']:
        raise ValueError('requires the unchanged failed retry on the same machine/binary')
    accepted = [p for p in old['parts'] if p['accepted']]
    count = len(accepted)
    if count != 39 or len(old['parts']) != count + 1 or old['parts'][-1]['index'] != count:
        raise ValueError('requires the recorded 39-part accepted prefix')
    base = Path(old['resumed_from']) / 'source'
    donor = previous / f'global-part{count}'
    identity = source_identity(base)
    failed = json.loads((previous / 'records' / f'global-part{count}.json').read_text())
    borrowed = assembly6.interfaces(donor)
    if (identity['source_sha256'] != old['source_sha256'] or
            source_identity(donor)['source_sha256'] != identity['source_sha256'] or
            failed['executable_sha256'] != machine['agda_sha256'] or
            digest_entries(borrowed) != failed['borrowed_interfaces_sha256'] or
            any(rel.endswith('/Part39.agdai') for rel in borrowed)):
        raise ValueError('source, compiler or accepted interfaces changed')
    if assembly6.sha(args.plan) != old['plan_sha256']:
        raise ValueError('different graph plan')
    plan = json.loads(args.plan.read_text())
    assembly.validate_plan(plan)
    _, owners = assembly.partition(plan['entries'], old['max_tokens'], old['max_entries'])
    roots = [s for s in plan['roots'] if owners[s] < count]
    if len(roots) != 28:
        raise ValueError('different covered-root subset')
    part = base / 'src/Tests/GlobalPilot6/Part39.agda'
    part_text = part.read_text()
    if args.drop_decoder_equality:
        from memory_repair6 import remove_unused_equality
        part_text = remove_unused_equality(part_text)
    phases = part_phases(part_text, 39)

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = output / 'source'
    source.mkdir()
    for name, _ in source_files(base):
        assembly.hardlink(base / name, source / name)
    jobs = []

    def add(name, body, heap=1350, rss=1.5, requires=None, scope='diagnostic'):
        path = f'src/Tests/MemoryProbe6/{name}.agda'
        destination = source / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(module_source(name, body))
        jobs.append(dict(name=name, target=path, heap_mib=heap,
                         rss_limit_gib=rss, requires=requires, scope=scope))

    add('Core', assembly.COMMON)
    for n in [10, 33, 39]:
        body = assembly.COMMON + ''.join(
            f'import Tests.GlobalPilot6.Part{j} as P{j}\n' for j in range(n))
        add(f'Prefix{n}', body)
    add('Part39Dependencies', phases['dependencies'])
    for phase in ['imports', 'states', 'decode', 'shape', 'check', 'sound']:
        add('Part39' + phase.title(), phases[phase], requires='Part39Dependencies')
    for prefix, selected in [('Single', roots[:1]), ('Subset', roots)]:
        for stage in ['imports', 'known', 'proven', 'fast', 'rules']:
            name = prefix + stage.title()
            previous_stage = None if stage == 'imports' else prefix + {
                'known': 'Imports', 'proven': 'Known', 'fast': 'Proven', 'rules': 'Fast'}[stage]
            add(name, root_source(selected, owners, plan['direction'], stage),
                heap=2500, rss=3, requires=previous_stage,
                scope='completion-selected subset; no population cost forecast')
    manifest = bench6.refresh_manifest(source, origin={k: identity[k] for k in ['revision', 'dirty']})
    files = [n for n, _ in source_files(source)]
    if args.phases:
        requested = set(args.phases)
        names = {job['name'] for job in jobs}
        if not requested <= names:
            raise ValueError('unknown diagnostic phase')
        for job in jobs:
            if job['name'] in requested and job['requires'] and job['requires'] not in requested:
                raise ValueError('requested phase omits its prerequisite')
        jobs = [job for job in jobs if job['name'] in requested]
    result = dict(format='othello-memory-probe6-v1', status='running',
                  machine=machine, plan_sha256=old['plan_sha256'],
                  original_source_sha256=identity['source_sha256'],
                  original_agda_source_sha256=identity['agda_source_sha256'],
                  diagnostic_source_sha256=manifest['source_sha256'],
                  diagnostic_agda_source_sha256=source_identity(source)['agda_source_sha256'],
                  borrowed_interfaces_sha256=digest_entries(borrowed),
                  phases=[], checked_subset_root_guarantees=0,
                  decoder_equality_removed=args.drop_decoder_equality,
                  requested_phases=args.phases,
                  cpu_budget=args.kernel_cpu_budget, measured_kernel_cpu_seconds=0,
                  scope='phase diagnostics and completion-selected upper sample; no initial-board theorem')
    passed = {}
    spent = 0.0
    for job in jobs:
        name = job['name']
        if job['requires'] and not passed.get(job['requires'], False):
            result['phases'].append({**job, 'status': 'skipped',
                                     'reason': 'prerequisite did not accept'})
            continue
        remaining = args.kernel_cpu_budget - spent
        if remaining < 10:
            result['phases'].append({**job, 'status': 'skipped', 'reason': 'internal CPU budget'})
            continue
        root = output / name
        root.mkdir()
        for relative in files:
            assembly.hardlink(source / relative, root / relative)
        bench6.refresh_manifest(root, origin={k: identity[k] for k in ['revision', 'dirty']})
        for relative, digest in borrowed.items():
            if assembly6.sha(donor / relative) != digest:
                raise ValueError('donor interface mutated')
            assembly.hardlink(donor / relative, root / relative)
        if assembly6.machine_identity(args.agda) != machine:
            raise ValueError('machine or compiler changed')
        record = run_job('memory-' + name, [args.agda, *assembly6.FLAGS, '-i', 'src',
                         job['target'], '+RTS', f'-M{job["heap_mib"]}M', '-s', '-RTS'],
                         output / 'records', root=root,
                         expected_source_sha256=manifest['source_sha256'],
                         cpu_limit=min(90, remaining), timeout=180,
                         rss_limit_gib=job['rss_limit_gib'], log_limit_mib=2,
                         metadata={'machine': machine, 'own_target_cold': True,
                                   'borrowed_interfaces_sha256': digest_entries(borrowed),
                                   'diagnostic_phase': name})
        spent += record['cpu_seconds']
        after = assembly6.interfaces(root)
        if any(after.get(relative) != digest for relative, digest in borrowed.items()):
            raise ValueError('borrowed interface mutated')
        log = (output / 'records' / ('memory-' + name + '.log')).read_text()
        phase = {**job, **assembly.metrics(record), 'status': 'accepted' if record['accepted'] else 'failed',
                 'exit_code': record['exit_code'], 'rts': rts_stats(log),
                 'heap_exhausted': 'Heap exhausted' in log}
        passed[name] = record['accepted']
        result['phases'].append(phase)
        result['measured_kernel_cpu_seconds'] = spent
        if name == 'SubsetRules' and record['accepted']:
            result['checked_subset_root_guarantees'] = len(roots)
        atomic_json(output / 'diagnostic.json', result)
        print(json.dumps({k: phase[k] for k in ['name', 'accepted', 'cpu_seconds',
                                               'peak_rss_gib', 'heap_exhausted', 'rts']}), flush=True)
    if (source_identity(base)['source_sha256'] != identity['source_sha256'] or
            assembly6.interfaces(donor) != borrowed):
        raise ValueError('preserved source/interfaces changed')
    result.update(status='complete', preserved_source_unchanged=True,
                  preserved_interfaces_unchanged=True)
    atomic_json(output / 'diagnostic.json', result)
    print(json.dumps({'status': result['status'], 'cpu_seconds': spent,
                      'checked_subset_root_guarantees': result['checked_subset_root_guarantees']}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--kernel-cpu-budget', type=float, default=1400)
    parser.add_argument('--drop-decoder-equality', action='store_true')
    parser.add_argument('--phases', nargs='+')
    args = parser.parse_args()
    if not 0 < args.kernel_cpu_budget <= 1400:
        parser.error('internal CPU budget must be at most 1400 seconds')
    run(args)


if __name__ == '__main__':
    main()
