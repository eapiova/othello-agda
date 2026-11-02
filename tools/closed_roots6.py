#!/usr/bin/env python3
"""AI-assisted root-local reassembly of the remaining sampled upper bounds.

Keep accepted old bounds; close each remaining root over the SAME graph's
citations, then repartition that closure without importing unrelated roots.
Soundness stays in safe Agda. No certificate branch is pruned or rewritten.
Generated groups have distinct namespaces and use the original resource caps.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import assembly6
import bench6
import global_assembly6 as assembly
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job


def closure_entries(plan, roots):
    assembly.validate_plan(plan)
    if not roots or len(set(roots)) != len(roots) or not set(roots) <= set(plan['roots']):
        raise ValueError('requires distinct roots from the original plan')
    entries = {e['state']: e for e in plan['entries']}
    seen, todo = set(), list(roots)
    while todo:
        state = todo.pop()
        if state not in seen:
            seen.add(state)
            todo.extend(entries[state]['references'])
    # Original topological order and every certificate byte are preserved.
    return [e for e in plan['entries'] if e['state'] in seen]


def root_sources(plan, root, index):
    entries = closure_entries(plan, [root])
    parts, owners = assembly.partition(entries, 32000, 150)
    namespace = f'Tests.ClosedPilot6.Root{index}'
    sources = {}
    for i, part in enumerate(parts):
        text, _, _ = assembly.part_source(i, part, owners, plan['direction'])
        sources[f'src/Tests/ClosedPilot6/Root{index}/Part{i}.agda'] = text.replace(assembly.PREFIX, namespace)
    text = assembly.assembly_source([root], owners, plan['direction']).replace(assembly.PREFIX, namespace)
    before, after = text.split('\naccepted0 :', 1)
    # Position remains transparent; the completed guarantee is opaque to the
    # final collector. Its proof is still elaborated and checked here.
    text = before + '\nabstract\n' + '\n'.join('  '+line if line else ''
        for line in ('accepted0 :' + after).splitlines()) + '\n'
    sources[f'src/Tests/ClosedPilot6/Root{index}/Check.agda'] = text
    return sources, parts


def collector_source(roots, witnesses):
    if len(set(roots)) != len(roots) or set(roots) != set(witnesses):
        raise ValueError('collector needs exactly one witness for every original root')
    aliases = sorted({module for module, _ in witnesses.values()})
    names = {module: f'R{i}' for i, module in enumerate(aliases)}
    text = assembly.HEADER + 'module Tests.ClosedPilot6.All100 where\n\n' + assembly.COMMON
    text += ''.join(f'import {module} as {names[module]}\n' for module in aliases)
    text += '''
AllUpper : List String → Set
AllUpper [] = ⊤
AllUpper (code ∷ codes) =
  Guarantees (Rules.game six) black (upperGoal 4) (decode code) × AllUpper codes

rootCodes : List String
rootCodes = '''
    text += ' ∷ '.join(f'"{assembly.compact.pack_state(s)}"' for s in roots) + ' ∷ []\n'
    text += '\nabstract\n  allUpper : AllUpper rootCodes\n  allUpper = '
    body = 'tt'
    for state in reversed(roots):
        module, fact = witnesses[state]
        body = f'{names[module]}.{fact} , ({body})'
    return text + body + '\n'


def run(args):
    previous = args.previous.resolve()
    old = json.loads((previous / 'continuation.json').read_text())
    if (old.get('status') != 'part-failed' or old.get('accepted_original_parts') != 84 or
            len(old.get('new_checked_roots', [])) != 7 or
            not old.get('preserved_sources_unchanged') or not old.get('preserved_interfaces_unchanged')):
        raise ValueError('requires the verified 84-part/66-root checkpoint')
    donor = Path(old['final_checkpoint'])
    origin = source_identity(donor)
    machine = assembly6.machine_identity(args.agda)
    pool = assembly6.interfaces(donor)
    if (machine != old['machine'] or origin['source_sha256'] != old['final_checkpoint_source_sha256'] or
            digest_entries(pool) != old['final_checkpoint_interfaces_sha256']):
        raise ValueError('checkpoint source, interfaces or machine changed')
    if assembly6.sha(args.plan) != old['plan_sha256']:
        raise ValueError('different original graph')
    plan = json.loads(args.plan.read_text())
    original_parts, owners = assembly.partition(plan['entries'], 32000, 300)
    if len(original_parts) != 125 or len(plan['roots']) != 100 or plan['direction'] != 'upper':
        raise ValueError('different pilot scope')
    remaining = [s for s in plan['roots'] if owners[s] >= 84]
    if len(remaining) != 34:
        raise ValueError('not the expected remaining roots')
    accepted_module_roots = [previous / 'new-covered-roots', args.first57.resolve(), args.next2.resolve()]
    prior = []
    for module_root, record in [(accepted_module_roots[0], previous/'records/new-covered-roots.json'),
            (accepted_module_roots[1], args.first57_record.resolve()),
            (accepted_module_roots[2], args.next2_record.resolve())]:
        measurement = json.loads(record.read_text())
        identity = source_identity(module_root)
        if (not measurement['accepted'] or not measurement['source_unchanged'] or
                not measurement['expected_source_matches'] or
                identity['source_sha256'] != measurement['source_sha256'] or
                measurement['executable_sha256'] != machine['agda_sha256']):
            raise ValueError('an earlier root assembly lacks unchanged acceptance')
        prior.append((module_root, identity, assembly6.interfaces(module_root)))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    base = output/'source'
    base.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor/name, base/name)
    sources, root_plans = {}, []
    for i, state in enumerate(remaining):
        generated, parts = root_sources(plan, state, i)
        sources.update(generated)
        root_plans.append(dict(index=i,state=state,parts=len(parts),entries=sum(len(p) for p in parts),
                               tokens=sum(assembly.tokens(e['certificate']) for p in parts for e in p)))
    # All earlier assembly sources and interfaces must match where they overlap.
    for module_root, _, imported in prior:
        for name, _ in source_files(module_root):
            if not name.endswith('.agda'):
                continue
            source = module_root/name
            dest = base/name
            # Old unchecked future parts can differ. Only files with accepted
            # interfaces are relevant; their exact source must agree.
            suffix = '/' + name.removeprefix('src/').removesuffix('.agda') + '.agdai'
            if not any(p.endswith(suffix) for p in imported):
                continue
            if dest.exists():
                if assembly6.sha(dest) != assembly6.sha(source):
                    raise ValueError('accepted source mismatch across earlier assemblies')
            else:
                assembly.hardlink(source, dest)
        for name, digest in imported.items():
            if name in pool and pool[name] != digest:
                raise ValueError('earlier accepted interface conflict')
    witnesses = {}
    first57 = json.loads(args.first57_summary.read_text())['roots']
    next2 = json.loads(args.next2_summary.read_text())['new_checked_roots']
    for states, module in [(first57,'Tests.GlobalPilot6.CheckSubset'),
            (next2,'Tests.GlobalPilot6.CheckNew'),
            (old['new_checked_roots'],'Tests.GlobalPilot6.CheckContinueNew')]:
        for i, state in enumerate(states):
            if state in witnesses:
                raise ValueError('duplicate earlier sampled root')
            witnesses[state] = (module, f'guarantee{i}')
    if len(witnesses) != 66 or set(witnesses) & set(remaining) or set(witnesses)|set(remaining) != set(plan['roots']):
        raise ValueError('earlier and new roots do not cover the exact original sample')
    all_witnesses = {**witnesses, **{s:(f'Tests.ClosedPilot6.Root{i}.Check','guarantee0')
                                   for i,s in enumerate(remaining)}}
    sources['src/Tests/ClosedPilot6/All100.agda'] = collector_source(plan['roots'], all_witnesses)
    for name, text in sources.items():
        path = base/name
        if path.exists():
            raise ValueError('new root namespace would overwrite an existing source')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text)
    manifest = bench6.refresh_manifest(base,origin={k:origin[k] for k in ['revision','dirty']})
    # Root-local checks borrow only generic interfaces; unrelated sampled proof
    # modules are imported only by the final collector.
    generic = {p:d for p,d in pool.items() if '/Tests/GlobalPilot6/' not in p}
    interfaces, donors = dict(generic), {p:donor/p for p in generic}
    global_interfaces, global_donors = dict(pool), {p:donor/p for p in pool}
    for module_root,_,imported in prior:
        for p,d in imported.items():
            if p in global_interfaces and global_interfaces[p]!=d:
                raise ValueError('global collection interface mismatch')
            global_interfaces[p]=d
            global_donors.setdefault(p,module_root/p)
    spent = 0.0
    report = dict(format='othello-closed-roots6-v1',status='checking',accepted=False,
                  machine=machine,plan_sha256=old['plan_sha256'],root_plans=root_plans,
                  source_sha256=manifest['source_sha256'],
                  agda_source_sha256=source_identity(base)['agda_source_sha256'],
                  reused_checked_roots=66,new_checked_roots=[],phases=[],assembly=None,
                  measured_kernel_cpu_seconds=0,initial_problem2_proved=False,
                  scope='same 100 upper-only sampled roots, reclosed over exact original graph; no forecast')

    def check(label,target,collect=False):
        nonlocal spent
        remaining_cpu=args.kernel_cpu_budget-spent
        if remaining_cpu<10:return None
        root=output/label;root.mkdir()
        for name,_ in source_files(base):assembly.hardlink(base/name,root/name)
        current=bench6.refresh_manifest(root,origin={k:origin[k] for k in ['revision','dirty']})
        borrowed=global_interfaces if collect else interfaces
        holders=global_donors if collect else donors
        for name,digest in borrowed.items():
            if assembly6.sha(holders[name])!=digest:raise ValueError('interface donor mutated')
            assembly.hardlink(holders[name],root/name)
        before=assembly6.interfaces(root)
        if any(p.endswith('/'+Path(target).stem+'.agdai') and
               p.endswith('/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai')
               for p in before):raise ValueError('own target is not cold')
        heap,rss,cpu=(2500,3,180) if collect else (1350,1.5,120)
        if assembly6.machine_identity(args.agda)!=machine:raise ValueError('compiler or machine changed')
        record=run_job(label,[args.agda,*assembly6.FLAGS,'-i','src',target,
                             '+RTS',f'-M{heap}M','-c','-s','-RTS'],output/'records',root=root,
                       expected_source_sha256=current['source_sha256'],
                       cpu_limit=min(cpu,remaining_cpu),timeout=max(240,cpu*2),
                       rss_limit_gib=rss,log_limit_mib=2,
                       metadata={'machine':machine,'own_target_cold':True,
                                 'borrowed_interfaces_sha256':digest_entries(before)})
        spent+=record['cpu_seconds'];after=assembly6.interfaces(root)
        if any(after.get(p)!=d for p,d in before.items()):raise ValueError('borrowed interface changed')
        if record['accepted']:
            for p,d in after.items():
                if p in interfaces and interfaces[p]!=d:raise ValueError('interface conflict')
                interfaces[p]=d;donors.setdefault(p,root/p)
                if p in global_interfaces and global_interfaces[p]!=d:raise ValueError('global interface conflict')
                global_interfaces[p]=d;global_donors.setdefault(p,root/p)
        metric=assembly.metrics(record);metric.update(label=label,target=target,
            heap_mib=heap,rss_limit_gib=rss,exit_code=record['exit_code'],
            rts=rts_stats((output/'records'/f'{label}.log').read_text()))
        report['phases'].append(metric);report['measured_kernel_cpu_seconds']=spent
        atomic_json(output/'closed.json',report);print(json.dumps(metric),flush=True)
        return metric

    atomic_json(output/'closed.json',report)
    for item in root_plans:
        i=item['index'];prefix=f'src/Tests/ClosedPilot6/Root{i}'
        for j in range(item['parts']):
            result=check(f'root{i}-part{j}',f'{prefix}/Part{j}.agda')
            if not result or not result['accepted']:
                report['status']='part-failed';break
        else:
            result=check(f'root{i}-bound',f'{prefix}/Check.agda')
            if result and result['accepted']:
                report['new_checked_roots'].append(item['state']);continue
            report['status']='root-assembly-failed'
        break
    else:
        report['assembly']=check('all100', 'src/Tests/ClosedPilot6/All100.agda',collect=True)
        report['accepted']=bool(report['assembly'] and report['assembly']['accepted'])
        report['status']='complete' if report['accepted'] else 'collector-failed'
    report['checked_sample_upper_roots']=66+len(report['new_checked_roots'])
    if source_identity(donor)['source_sha256']!=origin['source_sha256'] or assembly6.interfaces(donor)!=pool:
        raise ValueError('original continuation donor changed')
    for module_root,identity,imported in prior:
        if source_identity(module_root)['source_sha256']!=identity['source_sha256'] or assembly6.interfaces(module_root)!=imported:
            raise ValueError('earlier accepted root package changed')
    report.update(preserved_sources_unchanged=True,preserved_interfaces_unchanged=True)
    atomic_json(output/'closed.json',report)
    print(json.dumps({k:report[k] for k in ('status','checked_sample_upper_roots','measured_kernel_cpu_seconds')}))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','plan','output','first57','first57-record','first57-summary',
                 'next2','next2-record','next2-summary'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--kernel-cpu-budget',type=float,default=2300)
    args=p.parse_args()
    if not 0<args.kernel_cpu_budget<=2300:p.error('root-local budget must be at most 2300 CPU seconds')
    run(args)


if __name__=='__main__':main()
