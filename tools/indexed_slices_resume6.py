#!/usr/bin/env python3
"""Continue the authenticated sliced prefix, then check its complete hierarchy."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
from indexed_slices6 import generate
from indexed_wire_resume6 import closed, pinned
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def run(args):
    current=Path.cwd();previous=args.previous.resolve();base=previous/'results/indexed-slices6'
    out=args.output.resolve();require(not out.exists() and 'results' in out.parts,'fresh results root required');out.mkdir(parents=True)
    label=previous.name.removeprefix('six-')
    receipt=pinned(previous/'results'/(label+'.json'),args.expected_previous_receipt_sha256)
    outer_source=source_identity(previous)
    require(receipt['accepted'] and receipt.get('finished_utc') and receipt['source_unchanged'] and
        receipt['expected_source_matches'] and outer_source['source_sha256']==receipt['source_sha256'],
        'accepted unchanged terminal slice pilot required')
    service=closed(receipt)
    prior=pinned(base/'report.json',args.expected_previous_report_sha256)
    pool=pinned(base/'interface-map.json',args.expected_previous_map_sha256)
    old=base/'check';old_source=source_identity(old);machine=assembly6.machine_identity(args.agda)
    require(machine==prior['machine'] and machine['hostname']=='eapiova' and
        machine['agda_sha256']==args.expected_agda_sha256 and old_source==prior['checked_source'] and
        assembly6.interfaces(old)==pool and digest_entries(pool)==prior['last_interface_pool_sha256'],
        'same machine/compiler and exact terminal source/cache map required')
    expected=['Slice232q'+str(i) for i in range(4)]+['Part232']
    require(prior['accepted'] and prior['original_data_and_accepted_prefix_unchanged'] and
        [p['target'] for p in prior['phases']]==expected and prior['reused_indexed_parts']==232 and
        all(p['record']['accepted'] and p['borrowed_interfaces_unchanged'] and
            p['record']['source_unchanged'] and p['record']['expected_source_matches'] and
            p['record']['root']==str(old) and p['record']['executable_sha256']==machine['agda_sha256'] and
            p['record']['peak_rss_gib']<=1.5 for p in prior['phases']), 'complete accepted split required')
    for part in range(267):
        present=any(n.endswith('/Tests/IndexedWire6/Part'+str(part)+'.agdai') for n in pool)
        require(present==(part<233),'exact 233-part accepted proof prefix required')
    report=dict(format='othello-indexed-slices-resume6-v1',accepted=False,status='preparing',created_utc=utc(),
        machine=machine,previous_closed_service=service,previous_receipt_sha256=args.expected_previous_receipt_sha256,
        previous_report_sha256=args.expected_previous_report_sha256,previous_map_sha256=args.expected_previous_map_sha256,
        reused_indexed_parts=233,phases=[],kernel_cpu_seconds=0.,initial_problem2_proved=False,
        optimal_initial_pair_proved=False,production_authorized=False,
        scope='remaining exact descendant rows, original-ID recombination and full original-rule hierarchy')
    def save():atomic_json(out/'report.json',report)
    def guard(extra=0):
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used+extra<10*2**30 and free-extra>=100*2**30,'storage gate reached; all accepted targets preserved')
    estimate=sum((old/n).stat().st_blocks*512 for n,_ in source_files(old))+sum((old/n).stat().st_blocks*512 for n in pool)
    guard(estimate+40*2**20)
    check=out/'check';check.mkdir()
    for name,_ in source_files(old):
        path=check/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/name,path)
    for name,h in pool.items():copy_interface(old/name,check/name,h)
    require(source_identity(check)==old_source and assembly6.interfaces(check)==pool,'private source/cache copy differs')
    layouts=[];targets=[]
    for part in range(233,266):
        layout=generate(check,part);layouts.append(layout)
        targets.extend('Tests.IndexedWire6.'+t for t in layout['targets'])
    targets.append('Tests.IndexedWire6.Part266')
    # These hierarchy sources were frozen before the original 232-part run.
    main_report=pinned(args.main_prefix/'results/indexed-wire-resume6/report.json',
        '83f573687b162e1cafb786b1f5fadde067b5d19a2545fc85102edb5f99d184fe')
    hierarchy=main_report['layout'];require(hierarchy['rows']==53217 and hierarchy['parts']==267 and
        hierarchy['proof_nodes']==31 and hierarchy['targets'][-1]=='Root','complete original hierarchy required')
    for relative,h in hierarchy['generated_sha256'].items():
        require(assembly6.sha(check/relative)==h,'prepared hierarchy source differs')
    targets.extend('Tests.IndexedTree6.'+t for t in hierarchy['targets'])
    core='src/Everything6.agda';require(not any(n.endswith('/Everything6.agdai') for n in pool),'new Everything6 target must be cold')
    shutil.copy2(current/core,check/core);targets.insert(0,'Everything6')
    source=source_identity(check);report.update(checked_source=source,layouts=layouts,targets=targets,
        hierarchy_layout=hierarchy,private_cache_and_source_bytes=estimate,accepted_parts=233);save()
    borrowed=dict(pool)
    for index,target in enumerate(targets):
        guard();left=args.kernel_cpu_limit-report['kernel_cpu_seconds'];require(left>=1,'nested CPU cap reached')
        hierarchy_target=target.startswith('Tests.IndexedTree6.')
        rss=3. if hierarchy_target else 1.5;heap='-M2600M' if hierarchy_target else '-M1350M'
        own='src/'+target.replace('.','/')+'.agda';suffix='/'+own.removeprefix('src/').removesuffix('.agda')+'.agdai'
        require(not any(n.endswith(suffix) for n in assembly6.interfaces(check)), 'own target unexpectedly warm')
        rec=run_job('target'+str(index),[args.agda,'--no-libraries','-i','src','--safe','--without-K',
            '--cubical-compatible','--save-metas',own,'+RTS',heap,'-c','-s','-RTS'],out/'records',root=check,
            expected_source_sha256=source['source_sha256'],timeout=420,cpu_limit=min(180,left),rss_limit_gib=rss,
            log_limit_mib=2,metadata=dict(target=target,own_target_cold=True,original_ids_preserved=True))
        after=assembly6.interfaces(check);unchanged=all(after.get(n)==h for n,h in borrowed.items())
        report['phases'].append(dict(target=target,record=rec,borrowed_interfaces_unchanged=unchanged))
        report['kernel_cpu_seconds']+=rec['cpu_seconds']
        report['accepted_parts']=233+sum(p['record']['accepted'] and p['target'].startswith('Tests.IndexedWire6.Part') for p in report['phases'])
        report.update(status='checking-hierarchy' if hierarchy_target else 'checking-remaining-slices',last_interface_pool_sha256=digest_entries(after))
        atomic_json(out/'interface-map.json',after);save()
        require(rec['accepted'] and unchanged, 'target or borrowed cache failed: '+target)
        borrowed=after
    guard()
    require(source_identity(previous)==outer_source and source_identity(old)==old_source and assembly6.interfaces(old)==pool,
        'terminal accepted donor changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),descendant_original_lower_checked=True,
        original_data_and_accepted_prefix_unchanged=True,extended_everything6_checked=True);save()
    print(json.dumps(dict(accepted=True,kernel_cpu_seconds=report['kernel_cpu_seconds'],accepted_parts=report['accepted_parts'],
        initial_problem2_proved=False,optimal_initial_pair_proved=False)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','main-prefix','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-previous-receipt-sha256','expected-previous-report-sha256','expected-previous-map-sha256'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--kernel-cpu-limit',type=float,default=4500.)
    run(p.parse_args())


if __name__=='__main__':main()
