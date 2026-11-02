#!/usr/bin/env python3
"""Check numeric map assembly and the extended safe project on the desktop."""
import argparse
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
from data_only_pilot6 import borrowed_sources
from indexed_wire_resume6 import closed, pinned
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def run(args):
    current=Path.cwd();previous=args.previous.resolve();base=previous/'results/nat-indexed-pilot6';old=base/'check'
    label=previous.name.removeprefix('six-')
    actual=pinned(previous/'results'/(label+'.json'),args.expected_receipt_sha256)
    require(actual['accepted'] and actual['source_unchanged'] and actual['expected_source_matches']
        and source_identity(previous)['source_sha256']==actual['source_sha256'],'accepted unchanged donor required')
    state=closed(actual);prior=pinned(base/'report.json',args.expected_report_sha256)
    pool=pinned(base/'interface-map.json',args.expected_map_sha256);old_source=source_identity(old)
    machine=assembly6.machine_identity(args.agda)
    require(prior['accepted'] and prior['checked_source']==old_source and prior['machine']==machine
        and machine['agda_sha256']==args.expected_agda_sha256 and machine['hostname']=='eapiova'
        and assembly6.interfaces(old)==pool and digest_entries(pool)==prior['last_interface_pool_sha256'],
        'exact numeric prototype donor/compiler required')
    # The top-level aggregate and numeric decoder have changed. Numeric tests
    # depend on the decoder and must also be checked cold in the new root.
    excluded={'src/Everything6.agda','src/Othello/NatIndexed6.agda'}
    borrowed={n:h for n,h in pool.items() if '/Tests/' not in n and
        n.split('/agda/',1)[1][:-1] not in excluded}
    names=borrowed_sources(borrowed)
    require(all((current/n).exists() and assembly6.sha(current/n)==assembly6.sha(old/n) for n in names),
        'borrowed generic source differs from current source')
    out=args.output.resolve();require(not out.exists() and 'results' in out.parts,'fresh isolated spike required');out.mkdir(parents=True)
    report=dict(format='othello-nat-assembly-spike6-v1',accepted=False,status='preparing',created_utc=utc(),
        machine=machine,donor_closed_service=state,donor_source=old_source,donor_report_sha256=args.expected_report_sha256,
        phases=[],kernel_cpu_seconds=0.,initial_problem2_proved=False,optimal_initial_pair_proved=False,
        production_authorized=False,scope='two-part original-rule late-position lower theorem; extended safe Everything6',
        interface_policy='private same-machine/compiler/flags copies; exact generic source bytes and mtimes')
    def save():atomic_json(out/'report.json',report)
    def guard(extra=0):
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used+extra<10*2**30 and free-extra>=100*2**30,'storage gate reached; donor preserved')
    guard(sum((old/n).stat().st_blocks*512 for n in borrowed)+8*2**20)
    check=out/'check';check.mkdir();shutil.copytree(current/'src',check/'src',copy_function=shutil.copy2)
    shutil.copy2(current/'othello.agda-lib',check/'othello.agda-lib')
    for name in names:shutil.copy2(old/name,check/name)
    for name,h in borrowed.items():copy_interface(old/name,check/name,h)
    source=source_identity(check);report['checked_source']=source;report['borrowed_interfaces']=len(borrowed);save()
    for index,(target,rss,heap,limit) in enumerate([
        ('Tests.NatAssembly6',1.5,1350,90),('Everything6',3,2600,270)]):
        guard();before=assembly6.interfaces(check);suffix='/'+target.replace('.','/')+'.agdai'
        require(not any(n.endswith(suffix) for n in before),'own target unexpectedly warm')
        rec=run_job('target'+str(index),[args.agda,'--no-libraries','-i','src','--safe','--without-K',
            '--cubical-compatible','--save-metas','src/'+target.replace('.','/')+'.agda',
            '+RTS','-M'+str(heap)+'M','-c','-s','-RTS'],out/'records',root=check,expected_source_sha256=source['source_sha256'],
            timeout=600,cpu_limit=limit,rss_limit_gib=rss,log_limit_mib=2,
            metadata=dict(target=target,own_target_cold=True,part_proof_imports=False,borrowed_generic_data=True))
        after=assembly6.interfaces(check);unchanged=all(after.get(n)==h for n,h in before.items())
        report['phases'].append(dict(target=target,record=rec,borrowed_interfaces_unchanged=unchanged))
        report['kernel_cpu_seconds']+=rec['cpu_seconds'];report['status']='checking'
        report['last_interface_pool_sha256']=digest_entries(after);atomic_json(out/'interface-map.json',after);save()
        require(rec['accepted'] and unchanged,'assembly fixture or borrowed cache failed: '+target)
    require(source_identity(old)==old_source and assembly6.interfaces(old)==pool,'accepted donor changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),late_original_lower_checked=True,
        updated_everything6_checked=True,accepted_donor_unchanged=True);save()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-receipt-sha256','expected-report-sha256','expected-map-sha256'):
        p.add_argument('--'+name,required=True)
    run(p.parse_args())


if __name__=='__main__':main()
