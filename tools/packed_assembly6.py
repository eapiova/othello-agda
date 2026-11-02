#!/usr/bin/env python3
"""Recheck the original upper sample with compact routing and export tables.

One serial private cache avoids duplicating proof interfaces per group and
collector. Only same-binary verified generic interfaces are reused. Every new
part, group theorem and final collector is cold; stop on the first failure.
This bounded experiment makes no initial-board or production claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

import assembly6
import bench6
from cache_resume6 import copy_interface
from explicit_exports6 import pack_tables
import global_assembly6 as assembly
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job
from unattended_assembly6 import grouped_sources

OLD = 'Tests.Unattended6'
NEW = 'Tests.PackedTables6'
GIB = 1024**3


def generated_sources(plan):
    originals,groups = grouped_sources(plan)
    changed = {}
    for name,text in originals.items():
        if '/Part' in name:
            packed = pack_tables(text)
            # Keep the explicit equality witness measured in the A/B pilot.
            packed = packed.replace('  shape = refl\n','  shape = refl {x = states}\n')
            packed = packed.replace('  accepted = refl\n','  accepted = refl {x = true}\n')
            before = text.split('  entries :',1)[1].split('  shape :',1)[0]
            after = packed.split('  entries :',1)[1].split('  shape :',1)[0]
            if before != after or '  shape :' not in packed or '  accepted :' not in packed:
                raise ValueError('certificate data or proof obligation changed')
        else:
            packed = text
        changed[name.replace('/Unattended6/','/PackedTables6/')] = packed.replace(OLD,NEW)
    if len(changed) != 274 or sum(group['parts'] for group in groups) != 263:
        raise ValueError('different original grouped sample')
    return changed,groups,originals


def run(args):
    started = time.monotonic()
    previous = args.previous.resolve()
    donor = previous/'collector'
    audit = json.loads((previous/'phase-records.json').read_text())
    final = json.loads((previous/'final.json').read_text())
    machine = assembly6.machine_identity(args.agda)
    identity = source_identity(donor)
    pool = audit['collector_interfaces']
    if (assembly6.sha(previous/'final.json') != audit['final_sha256'] or
            final['status'] != 'collector-failed' or final['accepted'] or
            final['completed_groups'] != list(range(10)) or
            final['checked_regrouped_upper_roots'] != 100 or machine != final['machine'] or
            identity['source_sha256'] != final['source_sha256'] or assembly6.interfaces(donor) != pool):
        raise ValueError('requires the completed sample and unchanged original donor')
    plan = json.loads(args.plan.read_text());assembly.validate_plan(plan)
    if assembly6.sha(args.plan) != final['plan_sha256']:
        raise ValueError('different original graph plan')
    sources,groups,originals = generated_sources(plan)
    for name,text in originals.items():
        if (donor/name).read_text() != text:
            raise ValueError('original sample regeneration differs')
    output = args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    root = output/'check';root.mkdir()
    for name,_ in source_files(donor):assembly.hardlink(donor/name,root/name)
    for name,text in sources.items():
        destination = root/name
        if destination.exists():raise ValueError('new source namespace already exists')
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(text)
    manifest = bench6.refresh_manifest(root,origin={k:identity[k] for k in ('revision','dirty')})
    generic = {name:digest for name,digest in pool.items() if '/Tests/Unattended6/' not in name}
    if len(generic) != 32:raise ValueError('different verified generic interface pool')
    for name,digest in generic.items():copy_interface(donor/name,root/name,digest)
    report = dict(format='othello-packed-assembly6-v1',status='running',accepted=False,
        machine=machine,source_sha256=manifest['source_sha256'],
        agda_source_sha256=source_identity(root)['agda_source_sha256'],
        original_source_sha256=identity['source_sha256'],plan_sha256=final['plan_sha256'],
        groups=groups,completed_groups=[],checked_sample_upper_roots=0,phases=[],
        measured_kernel_cpu_seconds=0,heldout_groups=[9],training_groups=list(range(9)),
        heldout_declared_before_checks=True,
        interface_policy='one serial private cache; same binary and saved-meta mode; hashes before/after',
        generated_source_hashes={name:assembly6.sha(root/name) for name in sources},
        scope='the same 100 original upper-bound sample roots; encoded routes and exported states',
        initial_problem2_proved=False,production_authorized=False,
        maximum_runs_bytes=10*GIB,phases_artifact_growth_limit_mib=64)
    runs = Path(__file__).resolve().parents[1].parent

    def usage():
        allocated = int(subprocess.check_output(['du','-s','-B1',str(runs)],text=True).split()[0])
        return dict(runs_bytes=allocated,free_bytes=shutil.disk_usage(runs).free)

    initial_disk = usage();report['initial_disk'] = initial_disk
    if initial_disk['runs_bytes']+64*1024**2 >= 10*GIB:
        raise ValueError('insufficient artifact headroom for the bounded queue')

    def save():atomic_json(output/'packed.json',report)

    def check(label,target,collector=False):
        left = args.kernel_cpu_budget-report['measured_kernel_cpu_seconds']
        if left < 15:return None
        before = assembly6.interfaces(root)
        suffix = '/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'
        if any(name.endswith(suffix) for name in before):raise ValueError('own target is not cold')
        if assembly6.machine_identity(args.agda) != machine:raise ValueError('compiler changed')
        heap,rss,cap = (2500,3,180) if collector else (1350,1.5,90)
        record = run_job(label,[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
            '+RTS',f'-M{heap}M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=min(cap,left),
            timeout=cap*3,rss_limit_gib=rss,log_limit_mib=2,
            metadata={'machine':machine,'own_target_cold':True,
                      'borrowed_interfaces_sha256':digest_entries(before),
                      'interface_isolation':'private inode copies; one serial cache'})
        report['measured_kernel_cpu_seconds'] += record['cpu_seconds']
        after = assembly6.interfaces(root)
        changes = [name for name,digest in before.items() if after.get(name) != digest]
        metric = assembly.metrics(record)
        metric.update(label=label,target=target,exit_code=record['exit_code'],
                      heap_mib=heap,rss_limit_gib=rss,cache_changes=changes,
                      rts=rts_stats((output/'records'/f'{label}.log').read_text()))
        if changes:metric['accepted']=False;metric['rejection']='borrowed-cache-changed'
        report['phases'].append(metric);save();print(json.dumps(metric),flush=True)
        return metric

    def disk_ok():
        current = usage();report['latest_disk'] = current
        return (current['runs_bytes'] < 10*GIB and
                current['runs_bytes']-initial_disk['runs_bytes'] <= 64*1024**2 and
                current['free_bytes'] >= 100*GIB)

    save()
    for group in groups:
        i = group['index'];prefix=f'src/Tests/PackedTables6/Group{i}'
        if not disk_ok():report['status']='artifact-budget-stopped';break
        for j in range(group['parts']):
            result = check(f'group{i}-part{j}',f'{prefix}/Part{j}.agda')
            if not result or not result['accepted']:
                report['status']='part-failed' if result else 'cpu-budget-stopped';break
        else:
            result=check(f'group{i}-bounds',f'{prefix}/Check.agda')
            if result and result['accepted']:
                report['completed_groups'].append(i)
                report['checked_sample_upper_roots'] += len(group['roots']);save();continue
            report['status']='group-failed' if result else 'cpu-budget-stopped'
        break
    else:
        if disk_ok():
            result=check('packed-all100','src/Tests/PackedTables6/All100.agda',True)
            report['accepted']=bool(result and result['accepted'])
            report['status']='complete' if report['accepted'] else 'collector-failed'
        else:report['status']='artifact-budget-stopped'
    if source_identity(donor) != identity or assembly6.interfaces(donor) != pool:
        raise ValueError('original checked donor changed')
    report.update(donor_sources_unchanged=True,donor_interfaces_unchanged=True,
                  wall_seconds=time.monotonic()-started,final_disk=usage())
    records = {phase['label']:json.loads((output/'records'/f"{phase['label']}.json").read_text())
               for phase in report['phases']}
    atomic_json(output/'phase-records.json',dict(records=records,
        record_hashes={name:assembly6.sha(output/'records'/f'{name}.json') for name in records},
        log_hashes={name:assembly6.sha(output/'records'/f'{name}.log') for name in records},
        final_interfaces=assembly6.interfaces(root),
        generated_source_hashes=report['generated_source_hashes']))
    save()
    print(json.dumps({key:report[key] for key in ('status','accepted','checked_sample_upper_roots',
                                               'measured_kernel_cpu_seconds')}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--agda',required=True)
    parser.add_argument('--kernel-cpu-budget',type=float,default=2400)
    run(parser.parse_args())


if __name__=='__main__':main()
