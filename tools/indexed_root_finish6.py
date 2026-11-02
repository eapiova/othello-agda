#!/usr/bin/env python3
"""Check only the two missing roots of the complete accepted indexed prefix."""
import argparse
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
from indexed_wire_resume6 import closed, pinned
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def run(args):
    current=Path.cwd();previous=args.previous.resolve();base=previous/'results/indexed-slices-resume6'
    old=base/'check';label=previous.name.removeprefix('six-')
    actual=pinned(previous/'results'/(label+'.json'),args.expected_receipt_sha256)
    require(actual.get('finished_utc') and not actual['accepted'] and actual['source_unchanged'] and
        actual['expected_source_matches'] and source_identity(previous)['source_sha256']==actual['source_sha256'],
        'terminal unchanged previous run required')
    state=closed(actual)
    prior=pinned(base/'report.json',args.expected_report_sha256)
    pool=pinned(base/'interface-map.json',args.expected_map_sha256)
    machine=assembly6.machine_identity(args.agda);old_source=source_identity(old)
    require(prior['machine']==machine and machine['hostname']=='eapiova' and
        machine['agda_sha256']==args.expected_agda_sha256 and old_source==prior['checked_source'] and
        assembly6.interfaces(old)==pool and digest_entries(pool)==prior['last_interface_pool_sha256'],
        'same compiler and exact accepted source/cache map required')
    targets=prior['targets'][len(prior['phases']):]
    require(prior['accepted_parts']==267 and not prior['accepted'] and len(prior['phases'])==230 and
        targets==['Tests.IndexedTree6.Node0','Tests.IndexedTree6.Root'] and
        all(p['record']['accepted'] and p['borrowed_interfaces_unchanged'] and p['record']['source_unchanged'] and
            p['record']['expected_source_matches'] and p['record']['executable_sha256']==machine['agda_sha256']
            for p in prior['phases']), 'all parts and 30 checked nodes required')
    for target in targets:
        require(not any(n.endswith('/'+target.replace('.','/')+'.agdai') for n in pool), 'remaining target is warm')
    out=args.output.resolve();require(not out.exists() and 'results' in out.parts,'fresh results root required');out.mkdir(parents=True)
    report=dict(format='othello-indexed-root-finish6-v1',accepted=False,status='preparing',created_utc=utc(),
        machine=machine,previous_closed_service=state,reused_indexed_parts=267,reused_hierarchy_nodes=30,
        previous_receipt_sha256=args.expected_receipt_sha256,previous_report_sha256=args.expected_report_sha256,
        previous_map_sha256=args.expected_map_sha256,phases=[],kernel_cpu_seconds=0.,
        initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False)
    def save():atomic_json(out/'report.json',report)
    def guard(extra=0):
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used+extra<10*2**30 and free-extra>=100*2**30,'storage gate reached; every acceptance preserved')
    estimate=sum((old/n).stat().st_blocks*512 for n,_ in source_files(old))+sum((old/n).stat().st_blocks*512 for n in pool)
    guard(estimate+16*2**20)
    check=out/'check';check.mkdir()
    for name,_ in source_files(old):
        p=check/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/name,p)
    for name,h in pool.items():copy_interface(old/name,check/name,h)
    require(source_identity(check)==old_source and assembly6.interfaces(check)==pool,'private clone differs')
    source=source_identity(check);report['checked_source']=source;save();borrowed=dict(pool)
    for index,target in enumerate(targets):
        guard()
        rec=run_job('target'+str(index),[args.agda,'--no-libraries','-i','src','--safe','--without-K',
            '--cubical-compatible','--save-metas','src/'+target.replace('.','/')+'.agda',
            '+RTS','-M2600M','-c','-s','-RTS'],out/'records',root=check,expected_source_sha256=source['source_sha256'],
            timeout=420,cpu_limit=180,rss_limit_gib=3,log_limit_mib=2,
            metadata=dict(target=target,own_target_cold=True,accepted_prefix_rechecked=False))
        after=assembly6.interfaces(check);unchanged=all(after.get(n)==h for n,h in borrowed.items())
        report['phases'].append(dict(target=target,record=rec,borrowed_interfaces_unchanged=unchanged))
        report['kernel_cpu_seconds']+=rec['cpu_seconds'];report['last_interface_pool_sha256']=digest_entries(after)
        report['status']='checking-final-roots';atomic_json(out/'interface-map.json',after);save()
        require(rec['accepted'] and unchanged,'final root or borrowed cache failed: '+target);borrowed=after
    guard();require(source_identity(old)==old_source and assembly6.interfaces(old)==pool,'accepted donor changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),descendant_original_lower_checked=True,
        original_accepted_sources_and_interfaces_unchanged=True);save()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-receipt-sha256','expected-report-sha256','expected-map-sha256'):
        p.add_argument('--'+name,required=True)
    run(p.parse_args())


if __name__=='__main__':main()
