#!/usr/bin/env python3
"""AI-assisted single bounded retry of an unchanged global-proof pilot.

Reuse only a verified accepted prefix and the recorded, unchanged interfaces
borrowed by the failed part. Proof sources are hard-linked from the original
frozen source root, never regenerated or changed. Only the heap allowance grows;
the per-part RSS guard stays 1.5 GiB. Run under one outer coordinator reservation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time

import assembly6
import bench6
from global_assembly6 import hardlink,metrics
from provenance import digest_entries,source_files,source_identity
from run_job import atomic_json,run_job


def resume(args):
    start=time.monotonic();previous=args.previous.resolve();output=args.output.resolve()
    report=json.loads((previous/'assembly.json').read_text())
    if report['status']!='part-failed' or report['accepted']:
        raise ValueError('requires one failed-part pilot, not a completed assembly')
    machine=assembly6.machine_identity(args.agda)
    if machine!=report['machine']:raise ValueError('different machine, boot or Agda binary')
    parts=report['parts'];accepted=[p for p in parts if p['accepted']]
    if len(accepted)!=len(parts)-1 or parts[-1]['index']!=len(accepted):
        raise ValueError('prefix is not contiguous and ends in one failure')
    base=previous/'source';identity=source_identity(base)
    if identity['source_sha256']!=report['source_sha256']:
        raise ValueError('original generated source changed')
    for i in range(len(accepted)):
        record=json.loads((previous/'records'/f'global-part{i}.json').read_text())
        root=previous/f'global-part{i}'
        if (not record['accepted'] or not record['source_unchanged'] or
            record['source_sha256']!=identity['source_sha256'] or
            record['executable_sha256']!=machine['agda_sha256'] or
            source_identity(root)['source_sha256']!=identity['source_sha256']):
            raise ValueError('accepted prefix record or source identity disagrees')
    failed_index=len(accepted)
    failed=json.loads((previous/'records'/f'global-part{failed_index}.json').read_text())
    if failed['accepted'] or failed['executable_sha256']!=machine['agda_sha256']:
        raise ValueError('missing original failed-part record')
    donor_root=previous/f'global-part{failed_index}'
    if source_identity(donor_root)['source_sha256']!=identity['source_sha256']:
        raise ValueError('failed-part source changed')
    interfaces=assembly6.interfaces(donor_root)
    if digest_entries(interfaces)!=failed['borrowed_interfaces_sha256']:
        raise ValueError('borrowed accepted interface hashes changed')
    if any(rel.endswith(f'/Part{failed_index}.agdai') for rel in interfaces):
        raise ValueError('failed target unexpectedly has an accepted interface')
    donors={rel:donor_root/rel for rel in interfaces}
    output.mkdir(parents=True,exist_ok=False)
    report['parts']=accepted
    report.update(status='resuming',accepted=False,ab=[],resumed_from=str(previous),
                  original_failure_record_sha256=assembly6.sha(previous/'records'/f'global-part{failed_index}.json'),
                  original_accepted_parts=len(accepted),retry_heap_mib=args.heap_mib,
                  retry_rss_limit_gib=1.5)
    original_cpu=sum(p['cpu_seconds'] for p in accepted)
    retry_cpu=0.0;files=[n for n,_ in source_files(base)]
    atomic_json(output/'assembly.json',report)

    def check(label,target,limit,rss,heap,metadata):
        nonlocal retry_cpu
        remaining=args.kernel_cpu_budget-retry_cpu
        if remaining<10:raise ValueError('retry kernel budget exhausted')
        root=output/label;root.mkdir()
        for name in files:hardlink(base/name,root/name)
        bench6.refresh_manifest(root,origin={k:identity[k] for k in ['revision','dirty']})
        if source_identity(root)['source_sha256']!=identity['source_sha256']:
            raise ValueError('resumed source is not byte-identical')
        for rel,digest in interfaces.items():
            if assembly6.sha(donors[rel])!=digest:raise ValueError('accepted donor changed')
            hardlink(donors[rel],root/rel)
        before=assembly6.interfaces(root)
        if any(p.endswith('/'+target.rsplit('/',1)[-1].replace('.agda','.agdai')) for p in before):
            raise ValueError('resumed own target is not cold')
        record=run_job(label,[args.agda,*assembly6.FLAGS,'-i','src',target,
                             '+RTS',f'-M{heap}M','-RTS'],output/'records',root=root,
                       expected_source_sha256=identity['source_sha256'],
                       cpu_limit=min(limit,remaining),timeout=max(120,limit*2),
                       rss_limit_gib=rss,log_limit_mib=2,
                       metadata={'machine':machine,'own_target_cold':True,
                                 'borrowed_interfaces_sha256':digest_entries(before),**metadata})
        retry_cpu+=record['cpu_seconds'];after=assembly6.interfaces(root)
        for rel,digest in before.items():
            if after.get(rel)!=digest:raise ValueError('resumed dependency interface mutated')
        if record['accepted']:
            for rel,digest in after.items():
                if rel in interfaces and interfaces[rel]!=digest:raise ValueError('interface conflict')
                interfaces[rel]=digest;donors.setdefault(rel,root/rel)
        return metrics(record)

    # Source metadata, sizes and imports are recovered from the plan, while all
    # actual proof modules stay byte-identical to the original frozen source.
    import global_assembly6 as assembly
    plan=json.loads(args.plan.read_text())
    if assembly6.sha(args.plan)!=report['plan_sha256']:raise ValueError('different graph plan')
    assembly.validate_plan(plan)
    all_parts,owners=assembly.partition(plan['entries'],report['max_tokens'],report['max_entries'])
    if len(all_parts)!=report['part_count']:raise ValueError('different partition')
    for i in range(failed_index,len(all_parts)):
        part=all_parts[i]
        metric=check(f'global-part{i}',f'src/Tests/GlobalPilot6/Part{i}.agda',120,1.5,args.heap_mib,
                     {'dependencies':report['dependency_graph'][str(i)]})
        metric.update(index=i,entries=len(part),checked_tokens=sum(assembly.tokens(e['certificate']) for e in part),
                      compact_bytes=len(assembly.compact.encode((e['state'],e['certificate']) for e in part).encode()),
                      imported_states=len({r for e in part for r in e['references'] if owners[r]!=i}))
        report['parts'].append(metric)
        report.update(retry_kernel_cpu_seconds=retry_cpu,measured_kernel_cpu_seconds=original_cpu+retry_cpu)
        atomic_json(output/'assembly.json',report)
        print(json.dumps({'part':i,'parts':len(all_parts),**metric}),flush=True)
        if not metric['accepted']:
            report['status']='retry-part-failed';atomic_json(output/'assembly.json',report);return False
    compare=report['comparison_part']
    for variant,suffix in [('compact','CompactAB'),('legacy','LegacyAB')]:
        metric=check(f'global-ab-{variant}',f'src/Tests/GlobalPilot6/Part{compare}{suffix}.agda',
                     120,1.5,args.heap_mib,{'paired_graph_part':compare,'variant':variant})
        metric.update(variant=variant);report['ab'].append(metric)
        atomic_json(output/'assembly.json',report)
        if not metric['accepted']:
            report['status']='retry-ab-failed';atomic_json(output/'assembly.json',report);return False
    record=check('global-all-roots','src/Tests/GlobalPilot6/Check.agda',180,3,2500,
                 {'root_guarantees':len(plan['roots'])})
    report.update(assembly=record,accepted=record['accepted'],
                  status='complete' if record['accepted'] else 'retry-assembly-failed',
                  retry_kernel_cpu_seconds=retry_cpu,measured_kernel_cpu_seconds=original_cpu+retry_cpu,
                  accepted_interface_sha256=digest_entries(interfaces),
                  borrowed_interface_count=len(interfaces),retry_wall_seconds=time.monotonic()-start)
    atomic_json(output/'assembly.json',report)
    print(json.dumps({'status':report['status'],'checked_roots':len(plan['roots']) if report['accepted'] else 0,
                      'retry_cpu_seconds':retry_cpu}),flush=True)
    return report['accepted']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--heap-mib',type=int,default=1350)
    p.add_argument('--kernel-cpu-budget',type=float,default=3900)
    args=p.parse_args()
    if not 1200<args.heap_mib<=1350:p.error('one bounded heap retry up to 1350 MiB')
    return 0 if resume(args) else 1


if __name__=='__main__':raise SystemExit(main())
