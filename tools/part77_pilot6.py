#!/usr/bin/env python3
"""AI-assisted, bounded recovery of one failed sampled proof part.

Reuse only the verified 77-part prefix on its original machine/binary. Compare
isolating the dominant entry with literal, checked import tables. No accepted
source/interface is changed, no resource cap grows, and no production starts.
Run inside one coordinator-ledger reservation; nested records are not charged
again. Generated sources stay in this experiment's frozen results roots.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
import global_assembly6 as assembly
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job


def state_trie(states):
    result = 'tip'
    for state in reversed(states):
        literal = assembly.compact.pack_state(state)
        result = f'insertState (decode "{literal}") ({result})'
    return result


def split_sources(part, owners, direction):
    if not part or any(owners[e['state']] != 77 for e in part):
        raise ValueError('requires exactly the original Part77 entries')
    pivot = max(range(len(part)), key=lambda i: assembly.tokens(part[i]['certificate']))
    if pivot == 0:
        raise ValueError('the dominant entry has no preceding prefix to isolate')
    prefix, tail = part[:pivot], part[pivot:]
    text, _, _ = assembly.part_source(77, prefix, owners, direction, suffix='Prefix')
    new_owners = dict(owners)
    new_owners.update((e['state'], 78) for e in tail)
    last, _, _ = assembly.part_source(78, tail, new_owners, direction, suffix='Tail')
    last = last.replace('module Tests.GlobalPilot6.Part78Tail where',
                        'module Tests.GlobalPilot6.Part77Tail where', 1)
    last = last.replace('import Tests.GlobalPilot6.Part77 as P77',
                        'import Tests.GlobalPilot6.Part77Prefix as P77', 1)
    player = 'white' if direction == 'lower' else 'black'
    goal = f'({direction}Goal 4)'
    merged = assembly.HEADER + 'module Tests.GlobalPilot6.Part77Split where\n\n' + assembly.COMMON
    merged += f'''import Tests.GlobalPilot6.Part77Prefix as A
import Tests.GlobalPilot6.Part77Tail as B

states : Trie (State six)
states = mergeT A.states B.states

abstract
  sound : AllT (Proven Fast.fastGame6 {player} {goal}) states
  sound = merge-all A.states B.states A.sound B.sound

export : CheckedExport Fast.fastGame6 {player} {goal}
export = checkedExport states sound
'''
    return {'Part77Prefix': text, 'Part77Tail': last, 'Part77Split': merged}, pivot


def thin_sources(part, owners, direction, *, index=77):
    # Materialize exactly the cited external states, and prove each table from
    # its accepted owner. Missing/colliding states still fail in safe Agda.
    if not part or any(owners[e['state']] != index for e in part):
        raise ValueError('literal import part does not match its recorded owners')
    original, dependencies, _ = assembly.part_source(index, part, owners, direction, suffix='Thin')
    player = 'white' if direction == 'lower' else 'black'
    goal = f'({direction}Goal 4)'
    tables = assembly.HEADER + f'module Tests.GlobalPilot6.Part{index}ThinImports where\n\n'
    tables += assembly.COMMON
    tables += 'open import Game.SharedExport using (covered; covered-sound)\n'
    tables += ''.join(f'import {assembly.PREFIX}.Part{j} as P{j}\n' for j in dependencies)
    tables += '\ninsertState : State six → Trie (State six) → Trie (State six)\n'
    tables += 'insertState s = insertT (key6 s) s\n'
    for j in dependencies:
        cited = sorted({r for e in part for r in e['references'] if owners[r] == j})
        tables += f'''
states{j} : Trie (State six)
states{j} = {state_trie(cited)}

abstract
  covered{j} : covered keyed6 P{j}.states states{j} ≡ true
  covered{j} = refl

  sound{j} : AllT (Proven Fast.fastGame6 {player} {goal}) states{j}
  sound{j} = covered-sound keyed6 Fast.fastGame6 {player} {goal}
    P{j}.states states{j} P{j}.sound covered{j}

export{j} : CheckedExport Fast.fastGame6 {player} {goal}
export{j} = checkedExport states{j} sound{j}
'''
    exports = ' ∷ '.join(f'export{j}' for j in dependencies) + ' ∷ []' if dependencies else '[]'
    tables += f'\nexports : List (CheckedExport Fast.fastGame6 {player} {goal})\nexports = {exports}\n'
    changed, count = re.subn(r'^import Tests\.GlobalPilot6\.Part\d+ as P\d+\n', '',
                            original, flags=re.MULTILINE)
    if count != len(dependencies):
        raise ValueError('unexpected generated import declarations')
    changed = changed.replace('\nimports :',
                              f'\nimport Tests.GlobalPilot6.Part{index}ThinImports as Thin\n\nimports :', 1)
    changed, count = re.subn(r'^imports = [^\n]*$', 'imports = Thin.exports', changed,
                            count=1, flags=re.MULTILINE)
    if count != 1 or 'accepted = refl' not in changed or 'shardBy-sound' not in changed:
        raise ValueError('lost certificate checking or soundness obligations')
    return {f'Part{index}ThinImports': tables, f'Part{index}Thin': changed}


def validate_prefix(report):
    parts = report.get('parts', [])
    if (report.get('format') != 'othello-memory-repair6-v1' or
            report.get('status') != 'part-failed' or report.get('accepted') or
            not report.get('compacting_gc') or not report.get('preserved_sources_unchanged') or
            not report.get('preserved_interfaces_unchanged') or len(parts) != 78 or
            any(p.get('index') != i or p.get('accepted') != (i < 77)
                for i, p in enumerate(parts))):
        raise ValueError('requires the verified, contiguous 77-part prefix and Part77 failure')


def replace_link(path, text):
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run(args):
    previous = args.previous.resolve()
    old = json.loads((previous / 'repair.json').read_text())
    validate_prefix(old)
    machine = assembly6.machine_identity(args.agda)
    if machine != old['machine']:
        raise ValueError('different machine, boot or Agda binary')
    base, donor = previous / 'source', previous / 'repaired-part77'
    origin = source_identity(base)
    failed = json.loads((previous / 'records/repaired-part77.json').read_text())
    initial = assembly6.interfaces(donor)
    if (origin['source_sha256'] != old['source_sha256'] or
            source_identity(donor)['source_sha256'] != origin['source_sha256'] or
            failed['accepted'] or not failed['source_unchanged'] or
            failed['executable_sha256'] != machine['agda_sha256'] or
            digest_entries(initial) != failed['borrowed_interfaces_sha256'] or
            any(p.endswith('/Part77.agdai') for p in initial)):
        raise ValueError('source, failed record or borrowed interfaces changed')
    for i in range(77):
        if sum(p.endswith(f'/Part{i}.agdai') for p in initial) != 1:
            raise ValueError('missing or ambiguous accepted part interface')
    for i in range(39, 77):
        record = json.loads((previous / 'records' / f'repaired-part{i}.json').read_text())
        if (not record['accepted'] or not record['source_unchanged'] or
                record['source_sha256'] != origin['source_sha256'] or
                record['executable_sha256'] != machine['agda_sha256']):
            raise ValueError('new accepted prefix record disagrees')
    if assembly6.sha(args.plan) != old['plan_sha256']:
        raise ValueError('different graph plan')
    plan = json.loads(args.plan.read_text())
    assembly.validate_plan(plan)
    parts, owners = assembly.partition(plan['entries'], 32000, 300)
    if len(parts) != old['part_count']:
        raise ValueError('different partition')
    original, dependencies, _ = assembly.part_source(77, parts[77], owners, plan['direction'])
    if (base / 'src/Tests/GlobalPilot6/Part77.agda').read_text() != original:
        raise ValueError('Part77 differs from the measured template')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = output / 'source'
    source.mkdir()
    for name, _ in source_files(base):
        assembly.hardlink(base / name, source / name)
    extension = Path(__file__).resolve().parents[1] / 'src/Game/SharedExport.agda'
    if (source / 'src/Game/SharedExport.agda').exists():
        raise ValueError('old source unexpectedly contains the coverage extension')
    (source / 'src/Game/SharedExport.agda').write_bytes(extension.read_bytes())
    sources, pivot = split_sources(parts[77], owners, plan['direction'])
    sources.update(thin_sources(parts[77], owners, plan['direction']))
    sources['Part77Dependencies'] = (assembly.HEADER +
        'module Tests.GlobalPilot6.Part77Dependencies where\n\n' + assembly.COMMON +
        ''.join(f'import {assembly.PREFIX}.Part{j} as P{j}\n' for j in dependencies))
    for name, text in sources.items():
        path = source / f'src/Tests/GlobalPilot6/{name}.agda'
        if path.exists():
            raise ValueError('experiment would overwrite an existing generated module')
        path.write_text(text)
    manifest = bench6.refresh_manifest(source, origin={k: origin[k] for k in ['revision', 'dirty']})
    files = [name for name, _ in source_files(source)]
    interfaces, donors = dict(initial), {name: donor / name for name in initial}
    accepted_source_replacements = {}
    spent = 0.0
    result = dict(format='othello-part77-pilot6-v1', status='checking', machine=machine,
                  plan_sha256=old['plan_sha256'], original_source_sha256=origin['source_sha256'],
                  source_sha256=manifest['source_sha256'],
                  agda_source_sha256=source_identity(source)['agda_source_sha256'],
                  original_accepted_parts=77, original_checked_sample_upper_roots=57,
                  dominant_entry_index=pivot, prefix_entries=pivot,
                  tail_entries=len(parts[77]) - pivot,
                  part_heap_mib=1350, part_rss_limit_gib=1.5,
                  compacting_gc=True, phases=[], chosen_variant=None,
                  new_checked_roots=[], measured_kernel_cpu_seconds=0,
                  initial_problem2_proved=False, production_authorized=False,
                  scope='one completion-selected sampled upper part; no population forecast')

    def check(name, *, replacement=None, assembly_check=False):
        nonlocal spent
        remaining = args.kernel_cpu_budget - spent
        if remaining < 10:
            result['status'] = 'budget-stopped'
            return False
        root = output / name
        root.mkdir()
        for path in files:
            assembly.hardlink(source / path, root / path)
        # A checked adapter must keep its matching source in every downstream
        # root; never pair the adapter interface with the old failed body.
        for path, (checked_source, digest) in accepted_source_replacements.items():
            if assembly6.sha(checked_source) != digest:
                raise ValueError('checked adapter source changed')
            if (root / path).exists():
                (root / path).unlink()
            # Preserve the checked source's timestamp as well as bytes. A new
            # write would invalidate the borrowed interface in its importer.
            assembly.hardlink(checked_source, root / path)
        target = f'src/Tests/GlobalPilot6/{name}.agda'
        if replacement is not None:
            replace_link(root / target, replacement)
        current = bench6.refresh_manifest(root, origin={k: origin[k] for k in ['revision', 'dirty']})
        for path, digest in interfaces.items():
            if assembly6.sha(donors[path]) != digest:
                raise ValueError('accepted interface donor changed')
            assembly.hardlink(donors[path], root / path)
        before = assembly6.interfaces(root)
        if any(p.endswith(f'/{name}.agdai') for p in before):
            raise ValueError('own target is not cold')
        if assembly6.machine_identity(args.agda) != machine:
            raise ValueError('machine or binary changed')
        heap, rss = (2500, 3) if assembly_check else (1350, 1.5)
        record = run_job(name, [args.agda, *assembly6.FLAGS, '-i', 'src', target,
                               '+RTS', f'-M{heap}M', '-c', '-s', '-RTS'],
                         output / 'records', root=root,
                         expected_source_sha256=current['source_sha256'],
                         cpu_limit=min(120, remaining), timeout=240, rss_limit_gib=rss,
                         log_limit_mib=2, metadata={'machine': machine, 'own_target_cold': True,
                             'borrowed_interfaces_sha256': digest_entries(before)})
        spent += record['cpu_seconds']
        after = assembly6.interfaces(root)
        if any(after.get(path) != digest for path, digest in before.items()):
            raise ValueError('borrowed accepted interface changed')
        if record['accepted']:
            if replacement is not None:
                accepted_source_replacements[target] = (root / target, assembly6.sha(root / target))
            for path, digest in after.items():
                if path in interfaces and interfaces[path] != digest:
                    raise ValueError('conflicting accepted interfaces')
                interfaces[path] = digest
                donors.setdefault(path, root / path)
        metric = assembly.metrics(record)
        metric.update(name=name, heap_mib=heap, rss_limit_gib=rss,
                      exit_code=record['exit_code'],
                      rts=rts_stats((output / 'records' / f'{name}.log').read_text()))
        result['phases'].append(metric)
        result['measured_kernel_cpu_seconds'] = spent
        atomic_json(output / 'pilot.json', result)
        print(json.dumps(metric), flush=True)
        return record['accepted']

    atomic_json(output / 'pilot.json', result)
    if check('Part77Dependencies'):
        split_ok = (check('Part77Prefix') and check('Part77Tail') and check('Part77Split'))
        if split_ok:
            result['chosen_variant'] = 'split'
        elif check('Part77ThinImports') and check('Part77Thin'):
            result['chosen_variant'] = 'literal-imports'
        if result['chosen_variant']:
            selected = 'Part77Split' if split_ok else 'Part77Thin'
            adapter = assembly.HEADER + 'module Tests.GlobalPilot6.Part77 where\n\n'
            adapter += f'open import Tests.GlobalPilot6.{selected} public using (states; sound; export)\n'
            if check('Part77', replacement=adapter):
                # One downstream compatibility check, not a production continuation.
                count = 78
                if check('Part78'):
                    count = 79
                roots = [s for s in plan['roots'] if 77 <= owners[s] < count]
                if roots:
                    text = assembly.assembly_source(roots, owners, plan['direction']).replace(
                        'module Tests.GlobalPilot6.Check where',
                        'module Tests.GlobalPilot6.CheckNew where', 1)
                    if check('CheckNew', replacement=text, assembly_check=True):
                        result['new_checked_roots'] = roots
                result['accepted_original_parts'] = count
                result['status'] = 'partial-part-recovered'
            else:
                result['status'] = 'adapter-failed'
        else:
            result['status'] = 'both-variants-failed'
    else:
        result['status'] = 'dependency-load-failed'
    if (source_identity(base)['source_sha256'] != origin['source_sha256'] or
            assembly6.interfaces(donor) != initial):
        raise ValueError('preserved source or interfaces changed')
    result.update(preserved_sources_unchanged=True, preserved_interfaces_unchanged=True)
    atomic_json(output / 'pilot.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'chosen_variant',
          'measured_kernel_cpu_seconds', 'new_checked_roots')}), flush=True)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--agda', required=True)
    p.add_argument('--kernel-cpu-budget', type=float, default=800)
    args = p.parse_args()
    if not 0 < args.kernel_cpu_budget <= 800:
        p.error('bounded pilot kernel budget must be at most 800 CPU seconds')
    run(args)


if __name__ == '__main__':
    main()
