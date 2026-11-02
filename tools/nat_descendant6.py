#!/usr/bin/env python3
"""Check the complete 53,217-row descendant with numeric, independent parts.

This is a bounded feasibility assembly, never the full initial 6x6 production
proof. It requires the generated two-bound mini hierarchy to have passed first.
"""
import argparse
from pathlib import Path
import re
import shutil

import assembly6
from cache_resume6 import copy_interface
from data_only_pilot6 import borrowed_sources
from indexed_wire_resume6 import closed, pinned
from indexed_shape_mode6 import read_shape
from nat_indexed_pilot6 import convert_wire
import nat_tree_assembly6 as tree
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def run(args):
    current=Path.cwd();pilot=args.pilot.resolve();pb=pilot/'results/nat-tree-pilot6';donor=pb/'check'
    plabel=pilot.name.removeprefix('six-')
    pa=pinned(pilot/'results'/(plabel+'.json'),args.expected_pilot_receipt_sha256)
    pr=pinned(pb/'report.json',args.expected_pilot_report_sha256)
    pp=pinned(pb/'interface-map.json',args.expected_pilot_map_sha256)
    machine=assembly6.machine_identity(args.agda);donor_source=source_identity(donor)
    require(pa['accepted'] and pa['source_unchanged'] and pa['expected_source_matches']
        and source_identity(pilot)['source_sha256']==pa['source_sha256'] and pr['accepted']
        and pr['late_original_lower_and_upper_checked'] and pr['checked_source']==donor_source
        and pr['machine']==machine and machine['hostname']=='eapiova'
        and machine['agda_sha256']==args.expected_agda_sha256 and assembly6.interfaces(donor)==pp
        and digest_entries(pp)==pr['last_interface_pool_sha256'],'accepted generated numeric mini hierarchy required')
    pstate=closed(pa)
    wire=args.wire.resolve();wb=wire/'results/indexed-slices-resume6';old=wb/'check';wlabel=wire.name.removeprefix('six-')
    wa=pinned(wire/'results'/(wlabel+'.json'),args.expected_wire_receipt_sha256)
    wr=pinned(wb/'report.json',args.expected_wire_report_sha256);wp=pinned(wb/'interface-map.json',args.expected_wire_map_sha256)
    old_source=source_identity(old)
    require(wa.get('finished_utc') and wa['source_unchanged'] and wa['expected_source_matches']
        and source_identity(wire)['source_sha256']==wa['source_sha256'] and wr['accepted_parts']==267
        and wr['checked_source']==old_source and wr['machine']==machine and assembly6.interfaces(old)==wp
        and digest_entries(wp)==wr['last_interface_pool_sha256'],'exact complete accepted descendant data required')
    wstate=closed(wa)
    core={n:h for n,h in pp.items() if (current/(n.split('/agda/',1)[1][:-1])).is_file()}
    core_names=borrowed_sources(core)
    require(all(assembly6.sha(current/n)==assembly6.sha(donor/n) for n in core_names),'checked core source changed')
    root,leaves=read_shape((old/'src/Tests/IndexedWire6/Shape.agda').read_text())
    sizes=[n['size'] for n in leaves];require(len(sizes)==267 and sum(sizes)==53217,'bounded complete descendant required')
    states={f'src/Tests/IndexedWire6/StateData{j}.agda' for j in range(267)}
    data={n:h for n,h in wp.items() if n.split('/agda/',1)[1][:-1] in states}
    require(borrowed_sources(data)==states,'every exact state interface required')
    body_texts=[];dependencies={};payload=[]
    for j in range(267):
        path=old/f'src/Tests/IndexedWire6/BodyData{j}.agda'
        text=re.search(r'^text = "([^"]*)"$',path.read_text(),re.M)[1]
        changed,refs=convert_wire(text,leaves)
        body_texts.append(changed);dependencies[j]={j}|{rank//200 for rank in refs}
        payload.append(dict(part=j,original_body_sha256=assembly6.sha(path),original_bytes=len(text),
            numeric_bytes=len(changed),references=len(refs)))
    original_root=(old/'src/Tests/IndexedTree6/Root.agda').read_text()
    packed=re.search(r'^position = fromMaybe \(initial six\) \(decodeCompactState "([^"]*)"\)$',original_root,re.M)[1]
    out=args.output.resolve();require(not out.exists() and 'results' in out.parts,'fresh private descendant run required');out.mkdir(parents=True)
    report=dict(format='othello-nat-descendant6-v1',accepted=False,status='preparing',created_utc=utc(),
        machine=machine,wire_source=old_source,pilot_source=donor_source,wire_closed_service=wstate,
        pilot_closed_service=pstate,wire_report_sha256=args.expected_wire_report_sha256,
        pilot_report_sha256=args.expected_pilot_report_sha256,phases=[],kernel_cpu_seconds=0.,accepted_parts=0,
        initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False,
        scope='complete existing lower 14-disc descendant, numeric IDs and symbolic hierarchy; initial production excluded',
        payload=payload,borrowed_part_proofs=0)
    def save():atomic_json(out/'report.json',report)
    def guard(extra=0):
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used+extra<10*2**30 and free-extra>=100*2**30,'storage gate reached; accepted checkpoints preserved')
    estimate=sum((donor/n).stat().st_blocks*512 for n in core)+sum((old/n).stat().st_blocks*512 for n in data)
    estimate+=sum((old/n).stat().st_blocks*512 for n in states)+48*2**20
    guard(estimate)
    check=out/'check';check.mkdir();shutil.copytree(current/'src',check/'src',copy_function=shutil.copy2)
    shutil.copy2(current/'othello.agda-lib',check/'othello.agda-lib')
    for name in core_names:shutil.copy2(donor/name,check/name)
    for name in sorted(states):
        dst=check/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/name,dst)
    for name,h in core.items():copy_interface(donor/name,check/name,h)
    for name,h in data.items():copy_interface(old/name,check/name,h)
    layout=tree.generate(check,sizes=sizes,dependencies=dependencies,body_texts=body_texts,
        root_packed=packed,state_prefix='Tests.IndexedWire6',prefix='Tests.NatDescendant6',cut_depth=4)
    source=source_identity(check);report.update(layout=layout,checked_source=source,borrowed_state_interfaces=len(data));save()
    for index,name in enumerate(layout['targets']):
        guard();target='Tests.NatDescendant6.'+name;before=assembly6.interfaces(check);suffix='/'+target.replace('.','/')+'.agdai'
        require(not any(n.endswith(suffix) for n in before),'own target unexpectedly warm')
        remaining=args.kernel_cpu_limit-report['kernel_cpu_seconds'];require(remaining>1,'nested CPU cap reached')
        assembly=name.startswith('Node') or name=='Root'
        rec=run_job('target'+str(index),[args.agda,'--no-libraries','-i','src','--safe','--without-K',
            '--cubical-compatible','--save-metas','src/'+target.replace('.','/')+'.agda',
            '+RTS','-M2600M' if assembly else '-M1350M','-c','-s','-RTS'],out/'records',root=check,
            expected_source_sha256=source['source_sha256'],timeout=420,cpu_limit=min(180 if assembly else 120,remaining),
            rss_limit_gib=3 if assembly else 1.5,log_limit_mib=2,
            metadata=dict(target=target,own_target_cold=True,part_proof_imports=assembly,initial_problem2_proved=False))
        after=assembly6.interfaces(check);unchanged=all(after.get(n)==h for n,h in before.items())
        phase=dict(target=target,record=rec,borrowed_interfaces_unchanged=unchanged)
        if rec['accepted'] and re.fullmatch('Part[0-9]+',name):report['accepted_parts']+=1
        report['phases'].append(phase);report['kernel_cpu_seconds']+=rec['cpu_seconds'];report['status']='checking'
        report['last_interface_pool_sha256']=digest_entries(after);atomic_json(out/'interface-map.json',after);save()
        require(rec['accepted'] and unchanged,'numeric descendant target or cache failed: '+target)
    require(source_identity(old)==old_source and assembly6.interfaces(old)==wp
        and source_identity(donor)==donor_source and assembly6.interfaces(donor)==pp,'accepted donor changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),descendant_original_lower_checked=True,
        accepted_donors_unchanged=True);save()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('pilot','wire','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-pilot-receipt-sha256','expected-pilot-report-sha256',
        'expected-pilot-map-sha256','expected-wire-receipt-sha256','expected-wire-report-sha256','expected-wire-map-sha256'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--kernel-cpu-limit',type=float,default=3200)
    run(p.parse_args())


if __name__=='__main__':main()
