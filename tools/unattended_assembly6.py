#!/usr/bin/env python3
"""Detached, capped assembly diagnosis and a fresh saved-meta grouping pilot.

No AI session, ledger mutation, production, or trusted source edit runs here.
The coordinator reserves the complete queue before submitting it. Checkpoints
and all kernel failures are written after each phase inside results/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
from closed_roots6 import closure_entries, collector_source
from cache_resume6 import copy_interface
import global_assembly6 as assembly
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job


def grouped_sources(plan, size=10):
    if size != 10 or len(plan['roots']) != 100 or plan['direction'] != 'upper':
        raise ValueError('requires the original 100-root upper pilot in groups of ten')
    sources, groups, witnesses = {}, [], {}
    for index, offset in enumerate(range(0, 100, size)):
        roots = plan['roots'][offset:offset+size]
        entries = closure_entries(plan, roots)
        parts, owners = assembly.partition(entries, 32000, 150)
        prefix = f'Tests.Unattended6.Group{index}'
        for j, part in enumerate(parts):
            text, _, _ = assembly.part_source(j, part, owners, 'upper')
            text = text.replace(assembly.PREFIX, prefix)
            text = text.replace('--safe ', '--save-metas --safe ', 1)
            sources[f'src/Tests/Unattended6/Group{index}/Part{j}.agda'] = text
        text = assembly.assembly_source(roots, owners, 'upper').replace(assembly.PREFIX, prefix)
        # Keep each position transparent, but hide each completed evidence term.
        text = re.sub(r'(\naccepted\d+ :.*?)(?=\nposition\d+ :|\Z)',
                      lambda m: '\nabstract\n' + '\n'.join(
                          '  '+line if line else '' for line in m[1].lstrip('\n').splitlines())+'\n',
                      text, flags=re.S)
        text = text.replace('--safe ', '--save-metas --safe ', 1)
        sources[f'src/Tests/Unattended6/Group{index}/Check.agda'] = text
        groups.append(dict(index=index, roots=roots, parts=len(parts), entries=len(entries)))
        for j, state in enumerate(roots):
            witnesses[state] = (prefix+'.Check', f'guarantee{j}')
    text = collector_source(plan['roots'], witnesses)
    text = text.replace('Tests.ClosedPilot6.All100', 'Tests.Unattended6.All100')
    text = text.replace('--safe ', '--save-metas --safe ', 1)
    sources['src/Tests/Unattended6/All100.agda'] = text
    return sources, groups


def import_probes(original):
    declarations = re.findall(r'^import (Tests\.[\w.]+) as (R\d+)$', original, re.M)
    old = [p for p in declarations if '.GlobalPilot6.' in p[0]]
    new = [p for p in declarations if '.ClosedPilot6.Root' in p[0]]
    if len(old) != 3 or len(new) != 34:
        raise ValueError('requires the original failed 66+34 collector imports')
    first57 = [p for p in old if p[0].endswith('.CheckSubset')]
    sets = [('Core', []), ('Old57', first57), ('Old66', old),
            ('New8', new[:8]), ('New34', new), ('All100', declarations)]
    return {f'src/Tests/Unattended6/Imports{name}.agda':
            assembly.HEADER + f'module Tests.Unattended6.Imports{name} where\n\n' +
            'open import Prelude\n' + ''.join(f'import {module} as {alias}\n' for module, alias in imports)
            for name, imports in sets}


def run(args):
    previous = args.previous.resolve()
    old = json.loads((previous/'closed.json').read_text())
    failed = json.loads((previous/'records/all100.json').read_text())
    donor = previous/'all100'
    origin = source_identity(donor)
    pool = assembly6.interfaces(donor)
    machine = assembly6.machine_identity(args.agda)
    if (old['status'] != 'collector-failed' or old['checked_sample_upper_roots'] != 100 or
            not old['preserved_sources_unchanged'] or not old['preserved_interfaces_unchanged'] or
            machine != old['machine'] or machine != failed['machine'] or
            origin['source_sha256'] != failed['source_sha256'] or
            digest_entries(pool) != failed['borrowed_interfaces_sha256'] or
            not failed['source_unchanged'] or not failed['expected_source_matches'] or failed['accepted']):
        raise ValueError('completed sample or compiler provenance differs')
    plan = json.loads(args.plan.read_text())
    if assembly6.sha(args.plan) != old['plan_sha256']:
        raise ValueError('different original sample graph')
    sources, groups = grouped_sources(plan)
    sources.update(import_probes((donor/'src/Tests/ClosedPilot6/All100.agda').read_text()))
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    base = output/'source'; base.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor/name, base/name)
    for name, text in sources.items():
        path = base/name
        if path.exists(): raise ValueError('new namespace would overwrite a source')
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
    bench6.refresh_manifest(base, origin={k: origin[k] for k in ['revision', 'dirty']})
    # Saved-meta mode changes compatibility of the generic caches too. Start
    # this mode cold; the first successful part supplies its checked core cache.
    interfaces, holders = {}, {}
    report = dict(format='othello-unattended-assembly6-v1', status='running',
        accepted=False, initial_problem2_proved=False, production_authorized=False,
        source_sha256=source_identity(base)['source_sha256'], machine=machine,
        plan_sha256=old['plan_sha256'], groups=groups, phases=[], completed_groups=[],
        checked_regrouped_upper_roots=0, measured_kernel_cpu_seconds=0,
        scope='import diagnosis and saved-solved-meta representation of the same 100 upper-only sampled bounds')

    def check(label, target, probe=False, collect=False):
        left = args.kernel_cpu_budget-report['measured_kernel_cpu_seconds']
        if left < 15: return None
        root=output/label; root.mkdir()
        for name,_ in source_files(base): assembly.hardlink(base/name,root/name)
        current=bench6.refresh_manifest(root,origin={k:origin[k] for k in ['revision','dirty']})
        borrowed, donors = (pool, {p:donor/p for p in pool}) if probe else (interfaces, holders)
        for p,d in borrowed.items():
            if assembly6.sha(donors[p])!=d: raise ValueError('accepted interface changed')
            copy_interface(donors[p],root/p,d)
        before=assembly6.interfaces(root)
        suffix='/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'
        if any(p.endswith(suffix) for p in before): raise ValueError('target is not cold')
        heap,rss,cap = (2500,3,120) if probe or collect else (1350,1.5,90)
        flags=[] if probe else ['--save-metas']
        if assembly6.machine_identity(args.agda)!=machine: raise ValueError('compiler changed')
        record=run_job(label,[args.agda,*assembly6.FLAGS,*flags,'-i','src',target,
                        '+RTS',f'-M{heap}M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=current['source_sha256'],cpu_limit=min(cap,left),
            timeout=cap*3,rss_limit_gib=rss,log_limit_mib=2,
            metadata={'machine':machine,'own_target_cold':True,'borrowed_interfaces_sha256':digest_entries(before)})
        report['measured_kernel_cpu_seconds']+=record['cpu_seconds']
        after=assembly6.interfaces(root)
        if any(after.get(p)!=d for p,d in before.items()): raise ValueError('borrowed interface changed')
        if not probe and record['accepted']:
            for p,d in after.items():
                if p in interfaces and interfaces[p]!=d: raise ValueError('interface mismatch')
                interfaces[p]=d; holders.setdefault(p,root/p)
        metric=assembly.metrics(record)
        metric.update(label=label,target=target,heap_mib=heap,rss_limit_gib=rss,
            saved_metas=not probe,exit_code=record['exit_code'],
            rts=rts_stats((output/'records'/f'{label}.log').read_text()))
        report['phases'].append(metric)
        atomic_json(output/'checkpoint.json',report); print(json.dumps(metric),flush=True)
        return metric

    atomic_json(output/'checkpoint.json',report)
    for name in ['Core','Old57','Old66','New8','New34','All100']:
        result=check('imports-'+name,f'src/Tests/Unattended6/Imports{name}.agda',probe=True)
        if not result or (not result['accepted'] and name=='Core'):
            report['status']='imports-blocked'; break
    else:
        for group in groups:
            i=group['index'];prefix=f'src/Tests/Unattended6/Group{i}'
            for j in range(group['parts']):
                result=check(f'group{i}-part{j}',f'{prefix}/Part{j}.agda')
                if not result or not result['accepted']:
                    report['status']='part-failed' if result else 'budget-stopped'; break
            else:
                result=check(f'group{i}-bounds',f'{prefix}/Check.agda')
                if result and result['accepted']:
                    report['completed_groups'].append(i)
                    report['checked_regrouped_upper_roots']+=len(group['roots'])
                    atomic_json(output/'checkpoint.json',report)
                    continue
                report['status']='group-assembly-failed' if result else 'budget-stopped'
            break
        else:
            result=check('regrouped-all100','src/Tests/Unattended6/All100.agda',collect=True)
            report['accepted']=bool(result and result['accepted'])
            report['status']='complete' if report['accepted'] else 'collector-failed'
    if source_identity(donor)['source_sha256']!=origin['source_sha256'] or assembly6.interfaces(donor)!=pool:
        raise ValueError('original checked sample changed')
    report.update(preserved_sources_unchanged=True,preserved_interfaces_unchanged=True)
    atomic_json(output/'checkpoint.json',report);atomic_json(output/'final.json',report)
    print(json.dumps({'status':report['status'],'accepted':report['accepted'],
                      'checked_roots':report['checked_regrouped_upper_roots']}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--kernel-cpu-budget',type=float,default=2400)
    run(p.parse_args())


if __name__=='__main__':main()
