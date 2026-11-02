#!/usr/bin/env python3
"""Check generated numeric hierarchies for both bounds of a real late position."""
import argparse
from pathlib import Path
import shutil

import assembly6
import compact_shared6 as compact
import generate6
import ref
from census_pilot6 import state
from cache_resume6 import copy_interface
from data_only_pilot6 import borrowed_sources
from indexed_spike6 import BASE, IMAGE
from indexed_wire_resume6 import closed, pinned
from indexed_wire_pilot6 import skeleton
from nat_indexed_pilot6 import convert_wire, HEADER
import nat_tree_assembly6 as tree
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def prepare(check):
    base=state(BASE[1:],'black');passed=ref.successors(base)
    require(not ref.placements(base) and len(passed)==1,'expected genuine forced pass')
    choices=ref.successors(passed[0]);require(len(choices)==2,'expected both opponent replies')
    off=compact.pack_state(generate6.encode_state(choices[0]))
    lowstates=[compact.pack_state(BASE)*2,compact.pack_state(IMAGE),compact.pack_state(IMAGE)]
    upstates=[off+compact.pack_state(BASE),compact.pack_state(IMAGE),compact.pack_state(IMAGE)]
    layouts=[];sizes=[2,1,1];_,nodes,_=skeleton(sizes)
    leaves=[n for n in nodes if 'leaf' in n]
    for side,states,bodies in [
        ('lower',lowstates,['PC1F1LKa00','R4a00','Kba00']),
        ('upper',upstates,['C0LPF2Ka00C0L','R4a01','Kba00'])]:
        label=side.title();prefix='Tests.NatTreeMini'+label;state_prefix=prefix+'States'
        for j,n in enumerate(sizes):
            path=check/('src/'+state_prefix.replace('.','/')+'/StateData'+str(j)+'.agda')
            require(not path.exists(),'refusing state data overwrite');path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(HEADER+'module '+state_prefix+'.StateData'+str(j)+' where\n\n'+tree.DATA+
                f'\ntext : String\ntext = "{states[j]}"\nstates : B.Vec (State six) {n}\nstates = D.states {n} text\n')
        numeric=[convert_wire(text,leaves)[0] for text in bodies]
        layouts.append(tree.generate(check,sizes=sizes,dependencies={0:[0],1:[0,1],2:[1,2]},
            body_texts=numeric,root_packed=compact.pack_state(IMAGE),state_prefix=state_prefix,
            prefix=prefix,cut_depth=1,side=side))
    return layouts


def run(args):
    current=Path.cwd();previous=args.previous.resolve();base=previous/'results/nat-assembly-spike6';old=base/'check'
    label=previous.name.removeprefix('six-')
    actual=pinned(previous/'results'/(label+'.json'),args.expected_receipt_sha256)
    require(actual['accepted'] and actual['source_unchanged'] and actual['expected_source_matches']
        and source_identity(previous)['source_sha256']==actual['source_sha256'],'accepted unchanged donor required')
    state_observed=closed(actual);prior=pinned(base/'report.json',args.expected_report_sha256)
    pool=pinned(base/'interface-map.json',args.expected_map_sha256);old_source=source_identity(old)
    machine=assembly6.machine_identity(args.agda)
    require(prior['accepted'] and prior['updated_everything6_checked'] and prior['late_original_lower_checked']
        and prior['checked_source']==old_source and prior['machine']==machine and machine['hostname']=='eapiova'
        and machine['agda_sha256']==args.expected_agda_sha256 and assembly6.interfaces(old)==pool
        and digest_entries(pool)==prior['last_interface_pool_sha256'],'exact checked numeric assembly donor required')
    names=borrowed_sources(pool)
    require(all((current/n).exists() and assembly6.sha(current/n)==assembly6.sha(old/n) for n in names),
        'current borrowed core differs from donor')
    out=args.output.resolve();require(not out.exists() and 'results' in out.parts,'fresh isolated pilot required');out.mkdir(parents=True)
    report=dict(format='othello-nat-tree-pilot6-v1',accepted=False,status='preparing',created_utc=utc(),
        machine=machine,donor_closed_service=state_observed,donor_source=old_source,
        donor_report_sha256=args.expected_report_sha256,phases=[],kernel_cpu_seconds=0.,
        initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False,
        scope='generated hierarchical lower and upper bounds from a late forced-pass position; no initial theorem')
    def save():atomic_json(out/'report.json',report)
    def guard(extra=0):
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used+extra<10*2**30 and free-extra>=100*2**30,'storage gate reached; donor preserved')
    guard(sum((old/n).stat().st_blocks*512 for n in pool)+8*2**20)
    check=out/'check';check.mkdir();shutil.copytree(current/'src',check/'src',copy_function=shutil.copy2)
    shutil.copy2(current/'othello.agda-lib',check/'othello.agda-lib')
    for name in names:shutil.copy2(old/name,check/name)
    for name,h in pool.items():copy_interface(old/name,check/name,h)
    layouts=prepare(check);source=source_identity(check);report.update(layouts=layouts,checked_source=source);save()
    targets=[('Tests.NatTreeMini'+layout['side'].title()+'.'+name) for layout in layouts for name in layout['targets']]
    for index,target in enumerate(targets):
        guard();before=assembly6.interfaces(check);suffix='/'+target.replace('.','/')+'.agdai'
        require(not any(n.endswith(suffix) for n in before),'own target unexpectedly warm')
        remaining=args.kernel_cpu_limit-report['kernel_cpu_seconds'];require(remaining>1,'nested CPU cap reached')
        rec=run_job('target'+str(index),[args.agda,'--no-libraries','-i','src','--safe','--without-K',
            '--cubical-compatible','--save-metas','src/'+target.replace('.','/')+'.agda',
            '+RTS','-M1350M','-c','-s','-RTS'],out/'records',root=check,expected_source_sha256=source['source_sha256'],
            timeout=240,cpu_limit=min(90,remaining),rss_limit_gib=1.5,log_limit_mib=2,
            metadata=dict(target=target,own_target_cold=True,initial_problem2_proved=False))
        after=assembly6.interfaces(check);unchanged=all(after.get(n)==h for n,h in before.items())
        report['phases'].append(dict(target=target,record=rec,borrowed_interfaces_unchanged=unchanged))
        report['kernel_cpu_seconds']+=rec['cpu_seconds'];report['status']='checking'
        report['last_interface_pool_sha256']=digest_entries(after);atomic_json(out/'interface-map.json',after);save()
        require(rec['accepted'] and unchanged,'generated hierarchy or borrowed cache failed: '+target)
    require(source_identity(old)==old_source and assembly6.interfaces(old)==pool,'accepted donor changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),late_original_lower_and_upper_checked=True,
        accepted_donor_unchanged=True);save()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-receipt-sha256','expected-report-sha256','expected-map-sha256'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--kernel-cpu-limit',type=float,default=500)
    run(p.parse_args())


if __name__=='__main__':main()
