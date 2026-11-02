#!/usr/bin/env python3
"""AI-assisted bounded pilot continuation after two measured elaboration fixes.

Earlier 39 checked parts stay byte-identical. Only the unused decoder equality
in unchecked parts is removed; checker acceptance and export-shape proofs stay.
Root assembly uses the projection form accepted by the diagnostic. No core
source, old interface or resource gate is changed. This remains a sample pilot.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
import global_assembly6 as assembly
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job


def remove_unused_equality(source):
    changed, count = re.subn(r'^  decoded :[^\n]*\n  decoded = refl\n\n',
                            '', source, count=1, flags=re.MULTILINE)
    if count != 1 or '  shape :' not in changed or '  accepted :' not in changed:
        raise ValueError('unexpected decoder equality or missing proof obligations')
    return changed


def run(args):
    previous = args.previous.resolve()
    old = json.loads((previous / 'assembly.json').read_text())
    machine = assembly6.machine_identity(args.agda)
    if old['status'] != 'retry-part-failed' or old['accepted'] or machine != old['machine']:
        raise ValueError('requires the unchanged failed retry on the same machine/binary')
    accepted = [p for p in old['parts'] if p['accepted']]
    first = len(accepted)
    if first != 39 or len(old['parts']) != first + 1 or old['parts'][-1]['index'] != first:
        raise ValueError('requires the recorded 39-part accepted prefix')
    base = Path(old['resumed_from']) / 'source'
    donor = previous / f'global-part{first}'
    identity = source_identity(base)
    failed = json.loads((previous / 'records' / f'global-part{first}.json').read_text())
    borrowed = assembly6.interfaces(donor)
    if (identity['source_sha256'] != old['source_sha256'] or
            source_identity(donor)['source_sha256'] != identity['source_sha256'] or
            failed['executable_sha256'] != machine['agda_sha256'] or
            digest_entries(borrowed) != failed['borrowed_interfaces_sha256'] or
            any(rel.endswith('/Part39.agdai') for rel in borrowed)):
        raise ValueError('source, compiler or accepted interfaces changed')
    # Validate every earlier acceptance and source, not just the donor hashes.
    for i in range(first):
        directory = previous if i >= old['original_accepted_parts'] else Path(old['resumed_from'])
        record = json.loads((directory / 'records' / f'global-part{i}.json').read_text())
        if (not record['accepted'] or not record['source_unchanged'] or
                record['source_sha256'] != identity['source_sha256'] or
                record['executable_sha256'] != machine['agda_sha256']):
            raise ValueError('invalid earlier acceptance')
    if assembly6.sha(args.plan) != old['plan_sha256']:
        raise ValueError('different graph plan')
    plan = json.loads(args.plan.read_text())
    assembly.validate_plan(plan)
    parts, owners = assembly.partition(plan['entries'], old['max_tokens'], old['max_entries'])
    if len(parts) != old['part_count']:
        raise ValueError('different partition')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = output / 'source'
    source.mkdir()
    for name, _ in source_files(base):
        assembly.hardlink(base / name, source / name)
    if args.boolean_exports:
        extension = Path(__file__).resolve().parents[1] / 'src/Game/SharedExport.agda'
        path = source / 'src/Game/SharedExport.agda'
        if path.exists():
            raise ValueError('old source unexpectedly contains the new export extension')
        path.write_bytes(extension.read_bytes())
    for i in range(first, len(parts)):
        path = source / f'src/Tests/GlobalPilot6/Part{i}.agda'
        changed = remove_unused_equality(path.read_text())
        expected, _, _ = assembly.part_source(i, parts[i], owners, plan['direction'], export_mode='equality')
        if changed != expected:
            raise ValueError('unchecked part change exceeds the measured template fix')
        if args.boolean_exports:
            changed, _, _ = assembly.part_source(i, parts[i], owners, plan['direction'], export_mode='coverage')
        path.unlink()  # Break the immutable old-source hard link before writing.
        path.write_text(changed)
    check_path = source / 'src/Tests/GlobalPilot6/Check.agda'
    check_path.unlink()
    check_path.write_text(assembly.assembly_source(plan['roots'], owners, plan['direction']))
    for i in range(first):
        name = f'src/Tests/GlobalPilot6/Part{i}.agda'
        if assembly6.sha(source / name) != assembly6.sha(base / name):
            raise ValueError('checked prefix source changed')
    manifest = bench6.refresh_manifest(source, origin={k: identity[k] for k in ['revision', 'dirty']})
    files = [name for name, _ in source_files(source)]
    donors = {relative: donor / relative for relative in borrowed}
    interfaces = dict(borrowed)
    result = dict(format='othello-memory-repair6-v1', status='checking', accepted=False,
                  machine=machine, direction=plan['direction'], threshold=4,
                  plan_sha256=old['plan_sha256'], original_source_sha256=identity['source_sha256'],
                  source_sha256=manifest['source_sha256'],
                  agda_source_sha256=source_identity(source)['agda_source_sha256'],
                  reused_accepted_parts=first, part_count=len(parts), parts=list(accepted),
                  new_part_records=[], assembly=None, checked_root_guarantees=0,
                  fixes=['unused decoder equality removed from unchecked parts',
                         'concrete with-abstraction replaced by Proven projections'],
                  boolean_export_coverage=args.boolean_exports,
                  compacting_gc=args.compact_gc,
                  measured_new_cpu_seconds=0,
                  scope='100 sampled upper canonical frontier positions; no initial-board theorem')
    spent = 0.0

    def check(label, target, limit, rss, heap):
        nonlocal spent
        remaining = args.kernel_cpu_budget - spent
        if remaining < 10:
            return None
        root = output / label
        root.mkdir()
        for name in files:
            assembly.hardlink(source / name, root / name)
        bench6.refresh_manifest(root, origin={k: identity[k] for k in ['revision', 'dirty']})
        for relative, digest in interfaces.items():
            if assembly6.sha(donors[relative]) != digest:
                raise ValueError('accepted donor interface mutated')
            assembly.hardlink(donors[relative], root / relative)
        before = assembly6.interfaces(root)
        if any(p.endswith('/' + Path(target).stem + '.agdai') for p in before):
            raise ValueError('own target is not cold')
        if assembly6.machine_identity(args.agda) != machine:
            raise ValueError('machine or binary changed')
        record = run_job(label, [args.agda, *assembly6.FLAGS, '-i', 'src', target,
                         '+RTS', f'-M{heap}M', *(['-c'] if args.compact_gc else []),
                         '-s', '-RTS'], output / 'records', root=root,
                         expected_source_sha256=manifest['source_sha256'],
                         cpu_limit=min(limit, remaining), timeout=240,
                         rss_limit_gib=rss, log_limit_mib=2,
                         metadata={'machine': machine, 'own_target_cold': True,
                                   'borrowed_interfaces_sha256': digest_entries(before)})
        spent += record['cpu_seconds']
        after = assembly6.interfaces(root)
        if any(after.get(relative) != digest for relative, digest in before.items()):
            raise ValueError('borrowed interface mutated')
        if record['accepted']:
            for relative, digest in after.items():
                if relative in interfaces and interfaces[relative] != digest:
                    raise ValueError('conflicting accepted interface')
                interfaces[relative] = digest
                donors.setdefault(relative, root / relative)
        result['measured_new_cpu_seconds'] = spent
        return record

    atomic_json(output / 'repair.json', result)
    for i in range(first, len(parts)):
        record = check(f'repaired-part{i}', f'src/Tests/GlobalPilot6/Part{i}.agda', 120, 1.5, 1350)
        if record is None:
            result['status'] = 'budget-stopped'
            break
        metric = assembly.metrics(record)
        metric.update(index=i, entries=len(parts[i]),
                      checked_tokens=sum(assembly.tokens(e['certificate']) for e in parts[i]),
                      exit_code=record['exit_code'])
        result['parts'].append(metric)
        result['new_part_records'].append(metric)
        print(json.dumps({'part': i, **metric}), flush=True)
        atomic_json(output / 'repair.json', result)
        if not record['accepted']:
            result['status'] = 'part-failed'
            break
    else:
        record = check('repaired-all-roots', 'src/Tests/GlobalPilot6/Check.agda', 180, 3, 2500)
        if record is None:
            result['status'] = 'assembly-budget-stopped'
        else:
            result['assembly'] = assembly.metrics(record)
            result['accepted'] = record['accepted']
            result['checked_root_guarantees'] = len(plan['roots']) if record['accepted'] else 0
            result['status'] = 'complete' if record['accepted'] else 'assembly-failed'
    if (source_identity(base)['source_sha256'] != identity['source_sha256'] or
            assembly6.interfaces(donor) != borrowed):
        raise ValueError('preserved sources or interfaces changed')
    result.update(preserved_sources_unchanged=True, preserved_interfaces_unchanged=True,
                  accepted_parts=sum(p['accepted'] for p in result['parts']))
    atomic_json(output / 'repair.json', result)
    print(json.dumps({key: result[key] for key in ['status', 'accepted_parts',
                                                  'checked_root_guarantees', 'measured_new_cpu_seconds']}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--kernel-cpu-budget', type=float, default=1100)
    parser.add_argument('--boolean-exports', action='store_true')
    parser.add_argument('--compact-gc', action='store_true')
    args = parser.parse_args()
    if not 0 < args.kernel_cpu_budget <= 1100:
        parser.error('repair pilot CPU budget must be at most 1100 seconds')
    run(args)


if __name__ == '__main__':
    main()
