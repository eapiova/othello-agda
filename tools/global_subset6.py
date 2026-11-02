#!/usr/bin/env python3
"""AI-assisted assembly of roots fully covered by a failed pilot's accepted prefix.

This first subset check is not a retry of failed parts. Its completion-selected
roots are biased and cannot supply a population performance estimate.
"""
import argparse
import json
from pathlib import Path

import assembly6
import bench6
import global_assembly6 as assembly
from provenance import digest_entries,source_files,source_identity
from run_job import atomic_json,run_job


def run(args):
    previous=args.previous.resolve()
    report=json.loads((previous/('repair.json' if args.repaired else 'assembly.json')).read_text())
    expected='part-failed' if args.repaired else 'retry-part-failed'
    if report['status']!=expected:raise ValueError('requires a finished failed-part pilot')
    if args.repaired and (not report.get('preserved_sources_unchanged') or
                          not report.get('preserved_interfaces_unchanged') or
                          not report.get('compacting_gc')):
        raise ValueError('repaired prefix lacks unchanged-source or collector provenance')
    machine=assembly6.machine_identity(args.agda)
    if machine!=report['machine']:raise ValueError('different machine, boot or binary')
    accepted=[p for p in report['parts'] if p['accepted']]
    count=len(accepted)
    if len(report['parts'])!=count+1 or report['parts'][-1]['index']!=count:
        raise ValueError('not a contiguous accepted prefix')
    prefix='repaired-part' if args.repaired else 'global-part'
    failed=json.loads((previous/'records'/f'{prefix}{count}.json').read_text())
    donor=previous/f'{prefix}{count}'
    base=previous/'source' if args.repaired else Path(report['resumed_from'])/'source'
    identity=source_identity(base)
    if (identity['source_sha256']!=report['source_sha256'] or
        source_identity(donor)['source_sha256']!=identity['source_sha256'] or
        failed['executable_sha256']!=machine['agda_sha256']):
        raise ValueError('source or binary disagrees with the retry')
    interfaces=assembly6.interfaces(donor)
    if digest_entries(interfaces)!=failed['borrowed_interfaces_sha256']:
        raise ValueError('accepted borrowed interfaces changed')
    plan=json.loads(args.plan.read_text());assembly.validate_plan(plan)
    if assembly6.sha(args.plan)!=report['plan_sha256']:raise ValueError('different plan')
    if args.repaired:
        # The repair preserved the original 32k-token / 300-entry partition.
        token_cap,entry_cap=32000,300
    else:
        token_cap,entry_cap=report['max_tokens'],report['max_entries']
    partition,owners=assembly.partition(plan['entries'],token_cap,entry_cap)
    if len(partition)!=report['part_count']:raise ValueError('different partition')
    roots=[s for s in plan['roots'] if owners[s]<count]
    if not roots:raise ValueError('no completed root to assemble')
    output=args.output.resolve();root=output/'check';root.mkdir(parents=True,exist_ok=False)
    for name,_ in source_files(base):assembly.hardlink(base/name,root/name)
    source=assembly.assembly_source(roots,owners,plan['direction']).replace(
        'module Tests.GlobalPilot6.Check where','module Tests.GlobalPilot6.CheckSubset where',1)
    target='src/Tests/GlobalPilot6/CheckSubset.agda';(root/target).write_text(source)
    manifest=bench6.refresh_manifest(root,origin={k:identity[k] for k in ['revision','dirty']})
    for rel,digest in interfaces.items():
        if assembly6.sha(donor/rel)!=digest:raise ValueError('donor mutated')
        assembly.hardlink(donor/rel,root/rel)
    record=run_job('global-completed-subset',[args.agda,*assembly6.FLAGS,'-i','src',target,
                                           '+RTS','-M2500M',*(['-c'] if args.repaired else []),
                                           '-s','-RTS'],output/'records',root=root,
                   expected_source_sha256=manifest['source_sha256'],cpu_limit=120,timeout=240,
                   rss_limit_gib=3,log_limit_mib=2,
                   metadata={'machine':machine,'borrowed_interfaces_sha256':digest_entries(interfaces),
                             'own_target_cold':True,'completion_selected_root_count':len(roots)})
    after=assembly6.interfaces(root)
    if any(after.get(rel)!=digest for rel,digest in interfaces.items()):
        raise ValueError('accepted dependency interface mutated')
    result=dict(format='othello-global-subset6-v1',accepted=record['accepted'],
                checked_root_guarantees=len(roots) if record['accepted'] else 0,
                roots=roots,direction=plan['direction'],threshold=4,
                plan_sha256=report['plan_sha256'],accepted_prefix_parts=count,
                repaired_prefix=args.repaired,compacting_gc=args.repaired,
                assembly=assembly.metrics(record),
                selection='completion-selected prefix; biased, not a performance sample',
                scope='sampled-position guarantees under original Othello rules; no initial-board theorem')
    atomic_json(output/'subset.json',result)
    print(json.dumps(result))
    return record['accepted']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--repaired',action='store_true')
    args=p.parse_args()
    return 0 if run(args) else 1


if __name__=='__main__':raise SystemExit(main())
