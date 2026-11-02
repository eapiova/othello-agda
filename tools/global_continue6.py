#!/usr/bin/env python3
"""AI-assisted capped continuation of the existing 100-root upper pilot.

Begin at the verified Part78/CheckNew checkpoint. Each later part gets one
normal check and, only after a resource failure, one literal-import recovery.
No accepted source/interface is mutated; no gate is raised; no production or
initial-board theorem is claimed. Run inside one outer study-ledger reservation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import assembly6
import bench6
import global_assembly6 as assembly
from memory_probe6 import rts_stats
from part77_pilot6 import replace_link, thin_sources
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job


def initial_checkpoint(previous, agda):
    report = json.loads((previous / 'pilot.json').read_text())
    phases = {p['name']: p for p in report.get('phases', [])}
    if (report.get('format') != 'othello-part77-pilot6-v1' or
            report.get('status') != 'partial-part-recovered' or
            report.get('chosen_variant') != 'literal-imports' or
            report.get('accepted_original_parts') != 79 or
            len(report.get('new_checked_roots', [])) != 2 or
            not report.get('preserved_sources_unchanged') or
            not report.get('preserved_interfaces_unchanged') or
            any(not phases.get(name, {}).get('accepted')
                for name in ('Part77ThinImports', 'Part77Thin', 'Part77', 'Part78', 'CheckNew'))):
        raise ValueError('requires the verified 79-part literal-import checkpoint')
    donor = previous / 'CheckNew'
    record = json.loads((previous / 'records/CheckNew.json').read_text())
    identity = source_identity(donor)
    machine = assembly6.machine_identity(agda)
    if (machine != report['machine'] or not record['accepted'] or
            not record['source_unchanged'] or not record['expected_source_matches'] or
            identity['source_sha256'] != record['source_sha256'] or
            identity['source_sha256'] != phases['CheckNew']['source_sha256'] or
            record['executable_sha256'] != machine['agda_sha256']):
        raise ValueError('checkpoint machine, source or compiler disagrees')
    interfaces = assembly6.interfaces(donor)
    own = [p for p in interfaces if p.endswith('/CheckNew.agdai')]
    if len(own) != 1 or digest_entries({p: d for p, d in interfaces.items() if p != own[0]}) != record['borrowed_interfaces_sha256']:
        raise ValueError('checkpoint interfaces disagree with the accepted record')
    for i in range(79):
        if sum(p.endswith(f'/Part{i}.agdai') for p in interfaces) != 1:
            raise ValueError('missing or ambiguous accepted original part')
    if any(p.endswith('/Part79.agdai') for p in interfaces):
        raise ValueError('next target is not cold')
    for name in ('Part77', 'Part78'):
        accepted = json.loads((previous / 'records' / f'{name}.json').read_text())
        target = f'src/Tests/GlobalPilot6/{name}.agda'
        if (not accepted['accepted'] or not accepted['source_unchanged'] or
                source_identity(previous / name)['source_sha256'] != accepted['source_sha256'] or
                assembly6.sha(previous / name / target) != assembly6.sha(donor / target)):
            raise ValueError('adapter/downstream source no longer matches its acceptance')
    return report, donor, identity, interfaces, machine


def resource_failure(metric):
    # A malformed certificate, type error or provenance error gets no retry.
    return not metric['accepted'] and (metric['heap_exhausted'] or
        metric['stop_reason'] in ('rss-threshold', 'cpu-limit', 'timeout'))


def run(args):
    previous = args.previous.resolve()
    old, donor, origin, initial, machine = initial_checkpoint(previous, args.agda)
    if assembly6.sha(args.plan) != old['plan_sha256']:
        raise ValueError('different graph plan')
    plan = json.loads(args.plan.read_text())
    assembly.validate_plan(plan)
    parts, owners = assembly.partition(plan['entries'], 32000, 300)
    if len(parts) != 125 or len(plan['roots']) != 100 or plan['direction'] != 'upper':
        raise ValueError('different pilot scope or partition')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    base = output / 'source'
    base.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor / name, base / name)
    frozen = bench6.refresh_manifest(base, origin={k: origin[k] for k in ['revision', 'dirty']})
    interfaces = dict(initial)
    donors = {name: donor / name for name in initial}
    source_overrides = {}
    extra_sources = {}
    spent = 0.0
    checkpoint = donor
    result = dict(format='othello-global-continue6-v1', status='checking', accepted=False,
                  machine=machine, original_checkpoint=str(donor),
                  original_source_sha256=origin['source_sha256'], plan_sha256=old['plan_sha256'],
                  direction='upper', threshold=4, part_count=125, planned_roots=100,
                  reused_original_parts=79, accepted_original_parts=79,
                  original_checked_sample_upper_roots=59, phases=[], parts=[], assembly=None,
                  new_checked_roots=[], measured_kernel_cpu_seconds=0, resource_failures=[],
                  part_heap_mib=1350, part_rss_limit_gib=1.5, compacting_gc=True,
                  initial_problem2_proved=False, production_authorized=False,
                  scope='100 sampled upper frontier roots only; no population forecast')

    def check(label, name, *, replacement=None, assembly_check=False):
        nonlocal spent, checkpoint
        remaining = args.kernel_cpu_budget - spent
        if remaining < 10:
            return None
        # Nested work remains subject to the frozen launch's disk gates.
        if shutil.disk_usage(output).free < 100 * 1024**3:
            result['status'] = 'disk-gate-stopped'
            return None
        root = output / label
        root.mkdir()
        for path, _ in source_files(base):
            assembly.hardlink(base / path, root / path)
        for path, (checked_source, digest) in {**extra_sources, **source_overrides}.items():
            if assembly6.sha(checked_source) != digest:
                raise ValueError('accepted/generated source changed')
            if (root / path).exists():
                (root / path).unlink()
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
            raise ValueError('machine or compiler changed')
        heap, rss, cpu = (2500, 3, 180) if assembly_check else (1350, 1.5, 120)
        record = run_job(label, [args.agda, *assembly6.FLAGS, '-i', 'src', target,
                                '+RTS', f'-M{heap}M', '-c', '-s', '-RTS'],
                         output / 'records', root=root,
                         expected_source_sha256=current['source_sha256'],
                         cpu_limit=min(cpu, remaining), timeout=max(240, cpu*2),
                         rss_limit_gib=rss, log_limit_mib=2,
                         metadata={'machine': machine, 'own_target_cold': True,
                                   'borrowed_interfaces_sha256': digest_entries(before)})
        spent += record['cpu_seconds']
        after = assembly6.interfaces(root)
        if any(after.get(path) != digest for path, digest in before.items()):
            raise ValueError('borrowed interface mutated')
        if record['accepted']:
            if replacement is not None:
                source_overrides[target] = (root / target, assembly6.sha(root / target))
            for path, digest in after.items():
                if path in interfaces and interfaces[path] != digest:
                    raise ValueError('conflicting accepted interface')
                interfaces[path] = digest
                donors.setdefault(path, root / path)
            checkpoint = root
        log = (output / 'records' / f'{label}.log').read_text()
        metric = assembly.metrics(record)
        metric.update(label=label, name=name, heap_mib=heap, rss_limit_gib=rss,
                      exit_code=record['exit_code'], heap_exhausted='Heap exhausted' in log,
                      rts=rts_stats(log))
        result['phases'].append(metric)
        result['measured_kernel_cpu_seconds'] = spent
        atomic_json(output / 'continuation.json', result)
        print(json.dumps(metric), flush=True)
        return metric

    atomic_json(output / 'continuation.json', result)
    for i in range(79, len(parts)):
        normal = check(f'normal-part{i}', f'Part{i}')
        if normal is None:
            if result['status'] != 'disk-gate-stopped':
                result['status'] = 'budget-stopped'
            break
        selected = normal
        variant = 'normal'
        if resource_failure(normal):
            result['resource_failures'].append(i)
            generated = thin_sources(parts[i], owners, plan['direction'], index=i)
            for name, text in generated.items():
                path = output / 'generated' / f'{name}.agda'
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.exists():
                    raise ValueError('one recovery attempt per part')
                path.write_text(text)
                relative = f'src/Tests/GlobalPilot6/{name}.agda'
                if relative in extra_sources or (base / relative).exists():
                    raise ValueError('new template would overwrite existing module')
                extra_sources[relative] = (path, assembly6.sha(path))
            imports = check(f'literal-imports{i}', f'Part{i}ThinImports')
            thin = check(f'literal-part{i}', f'Part{i}Thin') if imports and imports['accepted'] else None
            if thin and thin['accepted']:
                adapter = assembly.HEADER + f'module Tests.GlobalPilot6.Part{i} where\n\n'
                adapter += f'open import Tests.GlobalPilot6.Part{i}Thin public using (states; sound; export)\n'
                selected = check(f'adapter-part{i}', f'Part{i}', replacement=adapter)
                variant = 'literal-imports'
            else:
                selected = thin or imports
        if not selected or not selected['accepted']:
            result['status'] = 'part-failed' if selected is not None else 'budget-stopped'
            result['failed_original_part'] = i
            break
        result['parts'].append(dict(index=i, entries=len(parts[i]), variant=variant,
                                    checked_tokens=sum(assembly.tokens(e['certificate']) for e in parts[i]),
                                    acceptance=selected))
        result['accepted_original_parts'] = i + 1
        atomic_json(output / 'continuation.json', result)
    else:
        full = check('all100-roots', 'CheckAll100',
                     replacement=assembly.assembly_source(plan['roots'], owners, plan['direction']).replace(
                         'module Tests.GlobalPilot6.Check where',
                         'module Tests.GlobalPilot6.CheckAll100 where', 1), assembly_check=True)
        result['assembly'] = full
        result['accepted'] = bool(full and full['accepted'])
        result['status'] = 'complete' if result['accepted'] else 'assembly-failed'
        if result['accepted']:
            result['checked_root_guarantees'] = 100
    if not result['accepted']:
        # Salvage only newly completed sampled roots; do not recheck the 59
        # previously accepted root guarantees or retry a failed full assembly.
        roots = [s for s in plan['roots'] if 79 <= owners[s] < result['accepted_original_parts']]
        if roots and result['assembly'] is None:
            subset = check('new-covered-roots', 'CheckContinueNew',
                           replacement=assembly.assembly_source(roots, owners, plan['direction']).replace(
                               'module Tests.GlobalPilot6.Check where',
                               'module Tests.GlobalPilot6.CheckContinueNew where', 1), assembly_check=True)
            result['subset_assembly'] = subset
            if subset and subset['accepted']:
                result['new_checked_roots'] = roots
    result.update(final_checkpoint=str(checkpoint),
                  final_checkpoint_source_sha256=source_identity(checkpoint)['source_sha256'],
                  final_checkpoint_agda_source_sha256=source_identity(checkpoint)['agda_source_sha256'],
                  final_checkpoint_interfaces_sha256=digest_entries(assembly6.interfaces(checkpoint)))
    if (source_identity(donor)['source_sha256'] != origin['source_sha256'] or
            assembly6.interfaces(donor) != initial or
            source_identity(base)['source_sha256'] != frozen['source_sha256']):
        raise ValueError('preserved checkpoint source or interfaces changed')
    result.update(preserved_sources_unchanged=True, preserved_interfaces_unchanged=True)
    atomic_json(output / 'continuation.json', result)
    print(json.dumps({k: result.get(k) for k in ('status', 'accepted_original_parts',
        'checked_root_guarantees', 'new_checked_roots', 'measured_kernel_cpu_seconds')}), flush=True)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--agda', required=True)
    p.add_argument('--kernel-cpu-budget', type=float, default=3200)
    args = p.parse_args()
    if not 0 < args.kernel_cpu_budget <= 3200:
        p.error('bounded pilot kernel CPU budget must be at most 3200 seconds')
    run(args)


if __name__ == '__main__':
    main()
