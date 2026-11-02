#!/usr/bin/env python3
"""Adopt a stopped serial private cache and check only its remaining targets.

Every pre-existing source and interface must retain its hash. The continuation
only adds cold target interfaces to the same private cache; it never copies a
writable cache inode or rechecks accepted parts. Log receipts remain separate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

import assembly6
from memory_probe6 import rts_stats
from provenance import digest_entries,source_identity
from run_job import atomic_json,run_job

GIB=1024**3


def run(args):
    previous=args.previous.resolve();root=previous/'check'
    old=json.loads((previous/'packed.json').read_text())
    audit=json.loads((previous/'phase-records.json').read_text())
    identity=source_identity(root);initial=assembly6.interfaces(root)
    machine=assembly6.machine_identity(args.agda)
    if (old['status']!='artifact-budget-stopped' or old['accepted'] or
            old['completed_groups']!=list(range(6)) or old['checked_sample_upper_roots']!=60 or
            not all(phase['accepted'] for phase in old['phases']) or
            identity['source_sha256']!=old['source_sha256'] or
            initial!=audit['final_interfaces'] or len(initial)!=205 or machine!=old['machine'] or
            not old['donor_sources_unchanged'] or not old['donor_interfaces_unchanged']):
        raise ValueError('requires the unchanged accepted six-group packed checkpoint')
    for phase in old['phases']:
        receipt=audit['records'][phase['label']]
        if (not receipt['accepted'] or not receipt['own_target_cold'] or
                receipt['source_sha256']!=identity['source_sha256'] or
                receipt['executable_sha256']!=machine['agda_sha256'] or
                not receipt['source_unchanged'] or not receipt['expected_source_matches'] or
                phase['cache_changes']):raise ValueError('invalid accepted prefix')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    report=dict(old)
    report.update(status='running',resumed_from=str(previous),
                  reused_checked_parts=167,reused_completed_groups=list(range(6)),
                  measured_new_kernel_cpu_seconds=0,
                  initial_prefix_interfaces_sha256=digest_entries(initial))
    report['completed_groups']=list(old['completed_groups'])
    report['phases']=list(old['phases'])
    spent=0.0
    runs=Path(__file__).resolve().parents[1].parent

    def usage():
        allocated=int(subprocess.check_output(['du','-s','-B1',str(runs)],text=True).split()[0])
        return dict(runs_bytes=allocated,free_bytes=shutil.disk_usage(runs).free)

    starting=usage();report['continuation_initial_disk']=starting
    if starting['runs_bytes']+48*1024**2>=10*GIB:
        raise ValueError('remaining queue lacks artifact headroom')

    def save():atomic_json(output/'packed.json',report)

    def check(label,target,collector=False):
        nonlocal spent
        left=args.kernel_cpu_budget-spent
        if left<15:return None
        before=assembly6.interfaces(root)
        suffix='/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'
        if any(name.endswith(suffix) for name in before):raise ValueError('own target is not cold')
        if assembly6.machine_identity(args.agda)!=machine:raise ValueError('compiler changed')
        heap,rss,cap=(2500,3,180) if collector else (1350,1.5,90)
        record=run_job(label,[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
            '+RTS',f'-M{heap}M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=identity['source_sha256'],cpu_limit=min(cap,left),
            timeout=cap*3,rss_limit_gib=rss,log_limit_mib=2,
            metadata={'machine':machine,'own_target_cold':True,
                      'borrowed_interfaces_sha256':digest_entries(before),
                      'interface_isolation':'private inode copies; one serial cache'})
        spent+=record['cpu_seconds'];after=assembly6.interfaces(root)
        changes=[name for name,digest in before.items() if after.get(name)!=digest]
        metric={
            key:record[key] for key in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib',
                                       'cache_state','stop_reason','source_sha256','agda_source_sha256')}
        metric.update(label=label,target=target,exit_code=record['exit_code'],heap_mib=heap,
                      rss_limit_gib=rss,cache_changes=changes,
                      rts=rts_stats((output/'records'/f'{label}.log').read_text()))
        if changes:metric['accepted']=False;metric['rejection']='prior-cache-hash-changed'
        report['phases'].append(metric)
        report['measured_new_kernel_cpu_seconds']=spent
        report['measured_kernel_cpu_seconds']=old['measured_kernel_cpu_seconds']+spent
        save();print(json.dumps(metric),flush=True);return metric

    def disk_ok():
        current=usage();report['latest_disk']=current
        return (current['runs_bytes']<10*GIB and current['free_bytes']>=100*GIB and
                current['runs_bytes']-starting['runs_bytes']<=48*1024**2)

    save()
    for group in report['groups'][6:]:
        i=group['index'];prefix=f'src/Tests/PackedTables6/Group{i}'
        if not disk_ok():report['status']='artifact-budget-stopped';break
        for j in range(group['parts']):
            result=check(f'group{i}-part{j}',f'{prefix}/Part{j}.agda')
            if not result or not result['accepted']:
                report['status']='part-failed' if result else 'cpu-budget-stopped';break
        else:
            result=check(f'group{i}-bounds',f'{prefix}/Check.agda')
            if result and result['accepted']:
                report['completed_groups'].append(i);report['checked_sample_upper_roots']+=10
                save();continue
            report['status']='group-failed' if result else 'cpu-budget-stopped'
        break
    else:
        if disk_ok():
            result=check('packed-all100','src/Tests/PackedTables6/All100.agda',True)
            report['accepted']=bool(result and result['accepted'])
            report['status']='complete' if report['accepted'] else 'collector-failed'
        else:report['status']='artifact-budget-stopped'
    if source_identity(root)!=identity:raise ValueError('checkpoint sources changed')
    current=assembly6.interfaces(root)
    if any(current.get(name)!=digest for name,digest in initial.items()):
        raise ValueError('a pre-existing accepted interface changed')
    report.update(prefix_sources_unchanged=True,prefix_interface_hashes_unchanged=True,
                  final_disk=usage())
    records=dict(audit['records']);hashes=dict(audit['record_hashes']);logs=dict(audit['log_hashes'])
    for phase in report['phases'][len(old['phases']):]:
        name=phase['label'];records[name]=json.loads((output/'records'/f'{name}.json').read_text())
        hashes[name]=assembly6.sha(output/'records'/f'{name}.json')
        logs[name]=assembly6.sha(output/'records'/f'{name}.log')
    atomic_json(output/'phase-records.json',dict(records=records,record_hashes=hashes,
        log_hashes=logs,final_interfaces=current,generated_source_hashes=old['generated_source_hashes']))
    save();print(json.dumps({key:report[key] for key in ('status','accepted','checked_sample_upper_roots',
        'measured_kernel_cpu_seconds','measured_new_kernel_cpu_seconds')}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--agda',required=True)
    parser.add_argument('--kernel-cpu-budget',type=float,default=1000)
    run(parser.parse_args())


if __name__=='__main__':main()
