#!/usr/bin/env python3
"""Extend the fixed lower pilot using checked exports as citation boundaries.

No accepted certificate is repeated. New certificate modules check literal
imports independently; small assembly modules discharge every import through
the previously checked owner-directed coverage theorem. Generated Agda lives
only in frozen results roots. This is a feasibility pilot, never production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import compact_shared6 as compact
import direct_citations6 as direct
import global_assembly6 as assembly
import independent_lower6 as independent
from lower_local_plan6 import closure
import lower_pilot6 as pilot
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, positive, run_job, utc

PREFIX = 'Tests.OwnerLower6'
DIRECTORY = 'src/Tests/OwnerLower6'
TRAINING = [2, 3, 5, 6, 7, 8, 9]
HELDOUT = list(range(10, 20))
ASSEMBLY_PARTS = 4


def missing_closure(entries, root, known):
    by_state = {e['state']: e for e in entries}
    seen, todo = set(), [root]
    while todo:
        state = todo.pop()
        if state in known or state in seen:
            continue
        seen.add(state)
        todo.extend(by_state[state]['references'])
    return [e for e in entries if e['state'] in seen]


def partition_missing(entries, known):
    # Preserve the original topological order and every certificate byte.
    parts, pending, count, owners = [], [], 0, {s: -1 for s in known}
    for entry in entries:
        if not set(entry['references']) <= owners.keys() or entry['state'] in owners:
            raise ValueError('unproved, forward or duplicate citation')
        size = assembly.tokens(entry['certificate'])
        if size > 32000:
            raise ValueError('entry exceeds the unchanged token cap')
        if pending and (count+size > 32000 or len(pending) >= 150):
            parts.append(pending)
            pending, count = [], 0
        owners[entry['state']] = len(parts)
        pending.append(entry)
        count += size
    if pending:
        parts.append(pending)
    return parts, owners


def external_states(part, owners, index):
    return sorted({s for e in part for s in e['references'] if owners[s] != index})


def owner_expression(state, owners, known, index, chunk, aliases):
    owner = owners[state]
    if owner == -1:
        module, fact = known[state]
        return aliases[module]+'.'+fact
    if owner >= index:
        raise ValueError('forward owner in assembly')
    if owner//ASSEMBLY_PARTS == chunk:
        return f'P{owner}.export'
    module = f'{PREFIX}.Root{aliases["root_index"]}.Assemble{owner//ASSEMBLY_PARTS}'
    return aliases[module]+f'.P{owner}.export'


def assembly_source(index, chunk, parts, owners, known):
    start = chunk*ASSEMBLY_PARTS
    end = min(len(parts), start+ASSEMBLY_PARTS)
    namespace = f'{PREFIX}.Root{index}'
    used = sorted({s for j in range(start, end) for s in external_states(parts[j], owners, j)})
    modules = set()
    for state in used:
        owner = owners[state]
        if owner == -1:
            modules.add(known[state][0])
        elif owner//ASSEMBLY_PARTS < chunk:
            modules.add(namespace+f'.Assemble{owner//ASSEMBLY_PARTS}')
    aliases = {module: f'E{i}' for i, module in enumerate(sorted(modules))}
    aliases['root_index'] = index
    text = pilot.local_options(assembly.HEADER+f'module {namespace}.Assemble{chunk} where\n\n')
    text += assembly.COMMON
    text += f'open import {direct.PREFIX}.Coverage using (coveredBy; coveredBy-sound)\n'
    text += ''.join(f'import {m} as {aliases[m]}\n' for m in sorted(modules))
    text += ''.join(f'import {namespace}.Part{j} as I{j}\n' for j in range(start, end))
    text += '''
routesFor : ℕ → String → Trie ℕ → Trie ℕ
routesFor owner wire tail = add (fromMaybe [] (decodeCompactEntries wire)) tail
  where
  add : List (SharedEntry (State six)) → Trie ℕ → Trie ℕ
  add [] tail = tail
  add (e ∷ es) tail = insertT (key6 (entryState e)) owner (add es tail)
'''
    cited, owner_count = 0, 0
    for j in range(start, end):
        groups = {}
        external = external_states(parts[j], owners, j)
        for state in external:
            expr = owner_expression(state, owners, known, j, chunk, aliases)
            groups.setdefault(expr, []).append(state)
        ordered = sorted(groups)
        sources = ' ∷ '.join(ordered)+' ∷ []' if ordered else '[]'
        hints = 'tip'
        for k, expr in reversed(list(enumerate(ordered))):
            hints = f'routesFor {k} "{independent.state_wire(groups[expr])}" ({hints})'
        text += f'''
module P{j} where
  sources : List (CheckedExport Fast.fastGame6 white (lowerGoal 4))
  sources = {sources}

  hints : Trie ℕ
  hints = {hints}

  states : Trie (State six)
  states = I{j}.states

  abstract
    coverage : coveredBy keyed6 sources hints I{j}.imports ≡ true
    coverage = refl {{x = true}}

    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = I{j}.sound
      (coveredBy-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
        sources hints I{j}.imports coverage)

  export : CheckedExport Fast.fastGame6 white (lowerGoal 4)
  export = checkedExport states sound
'''
        cited += len(external)
        owner_count += len(ordered)
    return text, dict(kind='assembly', chunk=chunk, parts=list(range(start, end)),
                     citations=cited, owners=owner_count,
                     x=[cited/1000, owner_count/100, 1.0])


def layout(plan, index, known):
    root = plan['roots'][index]
    entries = missing_closure(plan['entries'], root, known)
    parts, owners = partition_missing(entries, known)
    if root not in owners:
        raise ValueError('pilot root has no certificate or checked owner')
    prefix, directory = f'{PREFIX}.Root{index}', f'{DIRECTORY}/Root{index}'
    sources, phases = {}, []
    for j, part in enumerate(parts):
        text = independent.part_source(j, part, owners)
        # Reuse the accepted generic Checker, including its exact module name.
        text = text.replace(f'module {independent.PREFIX}.Part{j} where',
                            f'module {prefix}.Part{j} where', 1)
        sources[f'{directory}/Part{j}.agda'] = text
        tokens = sum(assembly.tokens(e['certificate']) for e in part)
        cites = len(external_states(part, owners, j))
        phases.append(dict(label=f'root{index}-part{j}', target=f'{directory}/Part{j}.agda',
            kind='certificate', part=j, entries=len(part), tokens=tokens, citations=cites,
            x=[tokens/1000, cites/1000, 1.0], heap_mib=1350, rss_gib=1.5, cpu_cap=120))
    for chunk in range((len(parts)+ASSEMBLY_PARTS-1)//ASSEMBLY_PARTS):
        text, row = assembly_source(index, chunk, parts, owners, known)
        target = f'{directory}/Assemble{chunk}.agda'
        sources[target] = text
        phases.append(dict(row, label=f'root{index}-assembly{chunk}', target=target,
                          heap_mib=2500, rss_gib=3, cpu_cap=180))
    owner = owners[root]
    text = pilot.local_options(assembly.HEADER+f'module {prefix}.Check where\n\n')+assembly.COMMON
    if owner >= 0:
        text += f'import {prefix}.Assemble{owner//ASSEMBLY_PARTS} as A\n'
        owner_prefix = f'A.P{owner}'
    else:
        module, fact = known[root]
        text += f'import {module} as A\n'
        owner_prefix = 'A'+('.'+fact.removesuffix('.export') if fact!='export' else '')
    # The original full-state membership and fast-to-Rules transfer are kept.
    dummy_owner = max(0, owner)
    tail = independent.collector_source(root, [[{}]]*(dummy_owner+1), {root: dummy_owner}, dummy_owner+1)
    tail = '\nposition :'+tail.split('\nposition :', 1)[1]
    text += tail.replace(f'P{dummy_owner}.', owner_prefix+'.')
    target = f'{directory}/Check.agda'
    sources[target] = text
    phases.append(dict(label=f'root{index}-check', target=target, kind='root',
                      x=[len(parts)/100, 1.0], heap_mib=2500, rss_gib=3, cpu_cap=180))
    return dict(index=index, state=root, entries=len(entries), parts=len(parts),
        original_entries=len(closure(plan['entries'], [root])),
        sources=sources, phases=phases, tokens=sum(p['tokens'] for p in phases if p['kind']=='certificate'),
        citations=sum(p['citations'] for p in phases if p['kind']=='certificate'),
        new_known={entry['state']:(prefix+f'.Assemble{owners[entry["state"]]//ASSEMBLY_PARTS}',
                                 f'P{owners[entry["state"]]}.export') for entry in entries})


def donors(args, plan):
    prefix, complete = args.prefix.resolve(), args.complete.resolve()
    first = json.loads((prefix/'final.json').read_text())
    original_audit = json.loads((prefix/'phase-records.json').read_text())
    last = json.loads((complete/'final.json').read_text())
    if (first['status'] != 'part-failed' or first['last_attempted_check']['label'] != 'group0-part122' or
            original_audit['final_sha256'] != assembly6.sha(prefix/'final.json') or
            original_audit['lower_sha256'] != assembly6.sha(prefix/'lower.json') or
            not last['accepted'] or last['status'] != 'complete' or
            assembly6.sha(complete/'final.json') !=
            'e0daff978453825c97e4b6f66315857fedb2662727880795b2b225e94b38c085' or
            any(not p['expected_outcome_met'] for p in last['phases'])):
        raise ValueError('requires the audited 122-part prefix and completed l015 donor')
    roots = [prefix/'check', Path(last['check_root'])]
    identities = [source_identity(root) for root in roots]
    pools = [assembly6.interfaces(root) for root in roots]
    if (identities[0]['source_sha256'] != first['source_sha256'] or
            pools[0] != original_audit['final_interfaces'] or len(pools[0]) != 154 or
            identities[1]['source_sha256'] != last['source_sha256'] or
            pools[1] != last['final_interfaces'] or len(pools[1]) != 154 or
            assembly6.machine_identity(args.agda) != last['machine'] or first['machine'] != last['machine']):
        raise ValueError('donor source, interfaces or compiler changed')
    known = {}
    parts, owners = assembly.partition(closure(plan['entries'], plan['roots'][:10]), 32000, 150)
    for j, part in enumerate(parts[:122]):
        text, _, _ = assembly.part_source(j, part, owners, 'lower')
        expected = pilot.packed_part(text.replace(assembly.PREFIX, pilot.PREFIX+'.Group0'))
        if (roots[0]/f'{pilot.DIRECTORY}/Group0/Part{j}.agda').read_text() != expected:
            raise ValueError('earlier accepted prefix certificate source differs')
        for entry in part:
            known[entry['state']] = (pilot.PREFIX+f'.Group0.Part{j}', 'export')
    parts, owners = assembly.partition(closure(plan['entries'], [plan['roots'][4]]), 32000, 150)
    if len(parts) != 118:
        raise ValueError('different completed stress layout')
    for j, part in enumerate(parts):
        if j < 114:
            text, _, _ = assembly.part_source(j, part, owners, 'lower')
            expected = pilot.packed_part(text.replace(assembly.PREFIX, independent.OLD))
            name = 'src/'+independent.OLD.replace('.', '/')+f'/Part{j}.agda'
            descriptor = (independent.OLD+f'.Part{j}', 'export')
        else:
            expected = independent.part_source(j, part, owners)
            name = independent.DIRECTORY+f'/Part{j}.agda'
            descriptor = (direct.PREFIX+'.Root', f'P{j}.export')
        if (roots[1]/name).read_text() != expected:
            raise ValueError('completed stress certificate source differs')
        for entry in part:
            known.setdefault(entry['state'], descriptor)
    pool, holders = {}, {}
    for root, imported in zip(roots, pools):
        for name, digest in imported.items():
            if name.endswith('/Game/SharedExport.agdai'):
                continue  # Unused historical interface; never restored or adopted.
            if name in pool and pool[name] != digest:
                raise ValueError('accepted donor interfaces conflict')
            pool[name] = digest
            holders.setdefault(name, root/name)
    return dict(roots=roots, identities=identities, pools=pools, pool=pool, holders=holders,
                known=known, machine=last['machine'])


def prepare(args):
    if assembly6.sha(args.plan) != direct.EXPECTED_PLAN:
        raise ValueError('different predeclared fixed sample')
    plan = json.loads(args.plan.read_text())
    pilot.validate_plan(plan)
    donor = donors(args, plan)
    known = dict(donor['known'])
    rows = []
    for i in TRAINING+HELDOUT:
        row = layout(plan, i, known)
        rows.append(row)
        known.update(row['new_known'])
    source_hashes = {name: digest for row in rows for name, digest in
                     pilot.source_hashes(row['sources']).items()}
    report = dict(format='othello-owner-lower6-preflight-v1', status='complete', created_utc=utc(),
        plan_sha256=direct.EXPECTED_PLAN, roots=plan['roots'],
        training_indices=TRAINING, heldout_indices=HELDOUT,
        heldout_declared_before_checks=True, known_entries=len(donor['known']),
        known_owners_sha256=digest_entries({s:'|'.join(d) for s,d in donor['known'].items()}),
        donors=[dict(root=str(root), identity=identity, interfaces_sha256=digest_entries(pool))
                for root,identity,pool in zip(donor['roots'],donor['identities'],donor['pools'])],
        machine=donor['machine'], generated_sha256=digest_entries(source_hashes),
        generated_source_bytes=sum(len(text.encode()) for row in rows for text in row['sources'].values()),
        rows=[{k:v for k,v in row.items() if k not in ('sources','new_known')} for row in rows],
        borrowed_interfaces=len(donor['pool']), borrowed_interfaces_sha256=digest_entries(donor['pool']),
        source_hashes=source_hashes, certificate_parts_rechecked=0,
        assembly_parts_per_module=ASSEMBLY_PARTS, zero_postulates=True,
        initial_problem2_proved=False, production_authorized=False)
    return donor, rows, report


def preflight(args):
    _, _, report = prepare(args)
    atomic_json(args.output, report)
    print(json.dumps({k:report[k] for k in ('status','known_entries','generated_source_bytes',
                                         'generated_sha256','borrowed_interfaces')}))


def run(args):
    donor, rows, preflight = prepare(args)
    if assembly6.sha(args.preflight) != args.expected_preflight_sha256:
        raise ValueError('preflight receipt differs')
    recorded = json.loads(args.preflight.read_text())
    for key in ('generated_sha256','known_owners_sha256','borrowed_interfaces_sha256',
                'source_hashes','rows','machine','donors'):
        if recorded[key] != preflight[key]:
            raise ValueError('layout or donor differs from the declared preflight: '+key)
    # Timing holdout cannot be invoked through the training driver.
    selected = [row for row in rows if row['index'] in TRAINING]
    runs, output = args.runs_root.resolve(), args.output.resolve()
    if output.exists() or runs not in output.parents:
        raise ValueError('requires a fresh frozen results directory')
    required = sum(p.stat().st_size for p in donor['holders'].values())+preflight['generated_source_bytes']+32*1024**2
    if not pilot.disk_allowed(pilot.disk_usage(runs), max(required, 100*1024**2)):
        raise ValueError('insufficient unchanged study disk headroom')
    output.mkdir(parents=True)
    root = output/'check'
    root.mkdir()
    # All overlapping original sources must agree. Future, unchecked files are
    # preserved but cannot be imported by any new pilot module.
    for old in donor['roots']:
        for name, _ in source_files(old):
            dest = root/name
            if dest.exists():
                if name.endswith(('.agda','.agda-lib')) and assembly6.sha(dest) != assembly6.sha(old/name):
                    raise ValueError('donor proof sources conflict')
                continue
            assembly.hardlink(old/name, dest)
    for row in rows:
        for name,text in row['sources'].items():
            dest = root/name
            if dest.exists():
                raise ValueError('fresh target already exists')
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(text)
    manifest = bench6.refresh_manifest(root,origin={k:donor['identities'][1][k] for k in ('revision','dirty')})
    for name,digest in donor['pool'].items():
        copy_interface(donor['holders'][name],root/name,digest)
    report = dict(preflight, format='othello-owner-lower6-training-v1', status='checking', accepted=False,
        check_root=str(root), source_sha256=manifest['source_sha256'],
        agda_source_sha256=source_identity(root)['agda_source_sha256'],
        preflight_sha256=args.expected_preflight_sha256, completed_indices=[], phases=[],
        nested_cpu_seconds=0.0, nested_cpu_budget=args.kernel_cpu_budget,
        heldout_measured=False, prior_checked_lower_roots=3, checked_sample_lower_roots=3)
    atomic_json(output/'running.json',report)
    for row in selected:
        complete = True
        for phase in row['phases']:
            left = args.kernel_cpu_budget-report['nested_cpu_seconds']
            if left < 10 or not pilot.disk_allowed(pilot.disk_usage(runs), 16*1024**2):
                report['status'] = 'cpu-stop' if left < 10 else 'disk-stop'
                complete = False
                break
            before = assembly6.interfaces(root)
            suffix = pilot.assert_cold(phase['target'],before,DIRECTORY)
            cap = min(phase['cpu_cap'],left-2)
            record = run_job(phase['label'],[donor['machine']['agda_path'],*assembly6.FLAGS,
                '--save-metas','-v','tc.decl:10','-i','src',phase['target'],
                '+RTS',f'-M{phase["heap_mib"]}M','-c','-s','-RTS'],output/'records',root=root,
                expected_source_sha256=manifest['source_sha256'],cpu_limit=cap,timeout=cap*2+30,
                rss_limit_gib=phase['rss_gib'],log_limit_mib=8,
                metadata=dict(machine=donor['machine'],own_target_cold=True,
                    borrowed_interfaces_sha256=digest_entries(before),certificate_parts_rechecked=0,
                    timing_group='training',checker_kind=phase['kind']))
            after = assembly6.interfaces(root)
            changes = pilot.cache_changes(before,after)
            own = {name:d for name,d in after.items() if name.endswith(suffix)}
            unexpected = [name for name in after if name not in before and name not in own]
            accepted = bool(record['accepted'] and len(own)==1 and not changes and not unexpected and
                record['source_unchanged'] and record['expected_source_matches'] and
                record['executable_sha256']==donor['machine']['agda_sha256'])
            log = output/'records'/(phase['label']+'.log')
            log_sha = assembly6.sha(log)
            stats = rts_stats(log.read_text())
            packed = archive(log,log_sha) if accepted else None
            report['phases'].append(dict(phase,accepted=accepted,record=record,
                record_sha256=assembly6.sha(output/'records'/(phase['label']+'.json')),
                cache_changes=changes,unexpected_interfaces=unexpected,own_interfaces=own,
                raw_log_sha256=log_sha,archived_log=packed,rts=stats))
            report['nested_cpu_seconds'] += record['cpu_seconds']
            atomic_json(output/'running.json',report)
            if not accepted:
                report['status'] = 'cache-mismatch' if changes or unexpected else 'phase-failed'
                complete = False
                break
        if not complete:
            break
        report['completed_indices'].append(row['index'])
        report['checked_sample_lower_roots'] += 1
        atomic_json(output/'running.json',report)
    report['donors_unchanged'] = all(source_identity(old)==identity and assembly6.interfaces(old)==pool
        for old,identity,pool in zip(donor['roots'],donor['identities'],donor['pools']))
    report['generated_sources_unchanged'] = all(assembly6.sha(root/name)==digest
                                              for name,digest in preflight['source_hashes'].items())
    report['final_interfaces'] = assembly6.interfaces(root)
    report['interfaces_sha256'] = digest_entries(report['final_interfaces'])
    report['latest_disk'] = pilot.disk_usage(runs)
    report['accepted'] = bool(report['completed_indices']==TRAINING and report['donors_unchanged'] and
        report['generated_sources_unchanged'] and pilot.disk_allowed(report['latest_disk']))
    if report['accepted']:
        report['status'] = 'complete'
    atomic_json(output/'final.json',report)
    print(json.dumps({k:report[k] for k in ('status','accepted','completed_indices',
                                         'checked_sample_lower_roots','nested_cpu_seconds')}))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('preflight','train'))
    for name in ('plan','prefix','complete','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--preflight',type=Path)
    p.add_argument('--expected-preflight-sha256')
    p.add_argument('--runs-root',type=Path)
    p.add_argument('--kernel-cpu-budget',type=positive)
    args = p.parse_args()
    if args.mode=='preflight':
        preflight(args)
    else:
        if any(getattr(args,k) is None for k in ('preflight','expected_preflight_sha256','runs_root','kernel_cpu_budget')):
            p.error('train requires a pinned preflight, runs root and nested CPU budget')
        raise SystemExit(0 if run(args)['accepted'] else 2)
