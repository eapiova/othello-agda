#!/usr/bin/env python3
"""Resume the saved-meta sample using isolated, verified interface copies.

The first part was accepted before the old harness stopped on rewritten
dependency hashes. Reuse that accepted cache in its original compiler mode;
never hard-link writable Agda interfaces or alter historical proof sources.
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
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job


def copy_interface(source, destination, expected):
    if assembly6.sha(source) != expected:
        raise ValueError('interface donor changed')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError('refusing to overwrite a cache file')
    shutil.copy2(source, destination)
    if (assembly6.sha(destination) != expected or
            source.stat().st_ino == destination.stat().st_ino and
            source.stat().st_dev == destination.stat().st_dev):
        raise ValueError('interface copy is not isolated and identical')


def selected_interfaces(pool, group=None):
    if group is None:
        return dict(pool)
    return {p:d for p,d in pool.items()
            if '/Tests/Unattended6/' not in p or f'/Group{group}/' in p}


def run(args):
    previous=args.previous.resolve()
    old=json.loads((previous/'checkpoint.json').read_text())
    seed=previous/'group0-part0'
    first=json.loads((previous/'records/group0-part0.json').read_text())
    machine=assembly6.machine_identity(args.agda)
    identity=source_identity(seed)
    initial=assembly6.interfaces(seed)
    if (old['format']!='othello-unattended-assembly6-v1' or old['completed_groups'] or
            len(old['phases'])!=6 or machine!=old['machine'] or machine!=first['machine'] or
            not first['accepted'] or not first['source_unchanged'] or not first['expected_source_matches'] or
            not first['own_target_cold'] or '--save-metas' not in first['argv'] or
            identity['source_sha256']!=first['source_sha256'] or
            identity['source_sha256']!=old['source_sha256'] or
            first['executable_sha256']!=machine['agda_sha256']):
        raise ValueError('requires the unchanged accepted saved-meta first part')
    if sum(p.endswith('/Tests/Unattended6/Group0/Part0.agdai') for p in initial)!=1:
        raise ValueError('missing or ambiguous accepted first part interface')
    plan=json.loads(args.plan.read_text())
    assembly.validate_plan(plan)
    if assembly6.sha(args.plan)!=old['plan_sha256'] or plan['direction']!='upper' or len(plan['roots'])!=100:
        raise ValueError('different original sample')
    if [s for g in old['groups'] for s in g['roots']]!=plan['roots']:
        raise ValueError('grouped roots do not match the exact original order')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    base=output/'source';base.mkdir()
    for name,_ in source_files(seed):assembly.hardlink(seed/name,base/name)
    bench6.refresh_manifest(base,origin={k:identity[k] for k in ['revision','dirty']})
    interfaces=dict(initial);holders={p:seed/p for p in initial};workspaces={}
    report=dict(format='othello-cache-resume6-v1',status='running',accepted=False,
        machine=machine,source_sha256=identity['source_sha256'],plan_sha256=old['plan_sha256'],
        groups=old['groups'],completed_groups=[],checked_regrouped_upper_roots=0,
        phases=[],measured_kernel_cpu_seconds=0,reused_first_part=first,
        interface_policy='private copies, same compiler and saved-meta mode; before/after hashes',
        initial_problem2_proved=False,production_authorized=False)

    def save():atomic_json(output/'resume.json',report)

    def check(label,target,group=None):
        left=args.kernel_cpu_budget-report['measured_kernel_cpu_seconds']
        if left<15:return None
        # One privately owned cache per group, used sequentially. Every own
        # target is still cold; copies are made once to avoid quadratic disk use.
        key='collector' if group is None else f'group{group}'
        if key not in workspaces:
            root=output/key;root.mkdir()
            for name,_ in source_files(base):assembly.hardlink(base/name,root/name)
            borrowed=selected_interfaces(interfaces,group)
            for p,d in borrowed.items():copy_interface(holders[p],root/p,d)
            workspaces[key]=root
        root=workspaces[key]
        manifest=bench6.refresh_manifest(root,origin={k:identity[k] for k in ['revision','dirty']})
        before=assembly6.interfaces(root)
        suffix='/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'
        if any(p.endswith(suffix) for p in before):raise ValueError('own target is not cold')
        heap,rss,cap=(2500,3,180) if group is None else (1350,1.5,90)
        if assembly6.machine_identity(args.agda)!=machine:raise ValueError('compiler changed')
        record=run_job(label,[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
            '+RTS',f'-M{heap}M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=min(cap,left),
            timeout=cap*3,rss_limit_gib=rss,log_limit_mib=2,
            metadata={'machine':machine,'own_target_cold':True,
                      'borrowed_interfaces_sha256':digest_entries(before),
                      'interface_isolation':'private inode copies'})
        report['measured_kernel_cpu_seconds']+=record['cpu_seconds']
        after=assembly6.interfaces(root)
        changes=[dict(path=p,before=d,after=after.get(p)) for p,d in before.items() if after.get(p)!=d]
        metric=assembly.metrics(record)
        metric.update(label=label,target=target,heap_mib=heap,rss_limit_gib=rss,
                      cache_changes=changes,exit_code=record['exit_code'],
                      rts=rts_stats((output/'records'/f'{label}.log').read_text()))
        if changes:
            metric['accepted']=False;metric['rejection']='borrowed-cache-hashes-changed'
        if metric['accepted']:
            for p,d in after.items():
                if p in interfaces and interfaces[p]!=d:raise ValueError('cache conflict')
                interfaces[p]=d;holders.setdefault(p,root/p)
        report['phases'].append(metric);save();print(json.dumps(metric),flush=True)
        return metric

    save()
    for g in old['groups']:
        i=g['index'];prefix=f'src/Tests/Unattended6/Group{i}'
        for j in range(g['parts']):
            if i==0 and j==0:continue
            result=check(f'group{i}-part{j}',f'{prefix}/Part{j}.agda',i)
            if not result or not result['accepted']:
                report['status']='part-failed' if result else 'budget-stopped';break
        else:
            result=check(f'group{i}-bounds',f'{prefix}/Check.agda',i)
            if result and result['accepted']:
                report['completed_groups'].append(i)
                report['checked_regrouped_upper_roots']+=len(g['roots']);save();continue
            report['status']='group-assembly-failed' if result else 'budget-stopped'
        break
    else:
        result=check('regrouped-all100','src/Tests/Unattended6/All100.agda')
        report['accepted']=bool(result and result['accepted'])
        report['status']='complete' if report['accepted'] else 'collector-failed'
    if source_identity(seed)['source_sha256']!=identity['source_sha256'] or assembly6.interfaces(seed)!=initial:
        raise ValueError('saved-meta seed changed')
    report.update(seed_sources_unchanged=True,seed_interfaces_unchanged=True)
    save();atomic_json(output/'final.json',report)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--kernel-cpu-budget',type=float,default=2400)
    run(p.parse_args())


if __name__=='__main__':main()
