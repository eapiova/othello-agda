#!/usr/bin/env python3
"""Reuse an authenticated terminal indexed prefix, then link it hierarchically."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess

import assembly6
from cache_resume6 import copy_interface
import compact_shared6 as compact
import data_only_pilot6 as data_only
import indexed_tree_assembly6 as tree
import indexed_wire_pilot6 as pilot
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def pinned(path, digest):
    require(assembly6.sha(path)==digest,'pinned artifact changed: '+str(path))
    return json.loads(path.read_text())


def closed(receipt):
    unit=receipt['remote_unit']
    require(unit=='othello6-'+receipt['label']+'.service','previous unit label differs')
    result=subprocess.run(['systemctl','--user','show',unit,'-p','LoadState','-p','ActiveState',
        '-p','SubState','-p','MainPID','-p','ControlPID','-p','ExecMainStatus'],capture_output=True,text=True,timeout=15)
    state=dict(l.split('=',1) for l in result.stdout.splitlines() if '=' in l)
    require(result.returncode in (0,1) and state.get('LoadState') in ('loaded','not-found') and
        state.get('ActiveState') in ('inactive','failed') and state.get('SubState') in ('dead','failed') and
        state.get('MainPID')==state.get('ControlPID')=='0','previous service is still live or unobservable')
    if state['LoadState']=='loaded':
        require(state.get('ExecMainStatus')==str(receipt['exit_code']),'closed unit exit status differs')
    return state


def run(args):
    current=Path.cwd();out=args.output.resolve();previous=args.previous.resolve()
    require(not out.exists() and 'results' in out.parts,'fresh isolated resume output required');out.mkdir(parents=True)
    machine=assembly6.machine_identity(args.agda)
    require(machine['hostname']=='eapiova' and machine['agda_sha256']==args.expected_agda_sha256,'pinned desktop compiler required')
    receipt_path=previous/'results'/(previous.name.removeprefix('six-')+'.json')
    receipt=pinned(receipt_path,args.expected_previous_receipt_sha256)
    require(receipt['machine']==machine['hostname'] and receipt['root']==str(previous) and receipt.get('finished_utc') and
        receipt['source_unchanged'] and receipt['expected_source_matches'] and receipt['source_sha256']==args.expected_previous_source_sha256,
        'previous outer receipt/source is not terminal and unchanged')
    service=closed(receipt);outer_source=source_identity(previous)
    require(outer_source['source_sha256']==args.expected_previous_source_sha256,'previous outer source changed')
    old=previous/'results/indexed-wire6/check';report_path=previous/'results/indexed-wire6/report.json'
    prior=pinned(report_path,args.expected_previous_report_sha256)
    map_path=previous/'results/indexed-wire6/interface-map.json'
    pool=pinned(map_path,args.expected_previous_map_sha256)
    old_source=source_identity(old)
    require(prior['format']=='othello-indexed-wire-pilot6-v1' and not prior['initial_problem2_proved'] and
        not prior['production_authorized'] and prior['checked_source']==old_source and
        old_source['source_sha256']==args.expected_check_source_sha256 and
        prior['machine']['agda_sha256']==machine['agda_sha256'] and prior['machine']['hostname']==machine['hostname'],
        'previous indexed proof identity differs')
    require(assembly6.interfaces(old)==pool and digest_entries(pool)==prior['last_interface_pool_sha256'],'previous cache map changed')
    reused=[]
    for phase in prior['phases']:
        r=phase['record']
        if not r['accepted']:break
        if phase['target']=='Assemble':break
        require(phase['target']=='Part'+str(len(reused)) and r['target']==phase['target'] and
            r['root']==str(old) and r['machine']==machine['hostname'] and r['executable_sha256']==machine['agda_sha256'] and
            r['source_sha256']==r['expected_source_sha256']==old_source['source_sha256'] and
            r['source_unchanged'] and r['expected_source_matches'] and r['exit_code']==0 and r['stop_reason'] is None and
            phase['borrowed_generic_interfaces_unchanged'] and not r['child_proof_imports'],
            'non-consecutive or unauthenticated accepted prefix')
        expected=[args.agda,'--no-libraries','-i','src','--safe','--without-K','--cubical-compatible','--save-metas',
            'src/'+pilot.PREFIX.replace('.','/')+'/'+phase['target']+'.agda','+RTS','-M1350M','-c','-s','-RTS']
        require(r['argv']==expected and r['peak_rss_gib']<=1.5,'previous proof flags or RSS differ')
        suffix='/'+pilot.PREFIX.replace('.','/')+'/'+phase['target']+'.agdai'
        require(sum(n.endswith(suffix) for n in pool)==1,'accepted own interface missing')
        reused.append(phase)
    require(0<len(reused)<=267 and len(reused)==prior['accepted_parts'],'prefix count differs')
    # A failed own proof is never adopted. Data-only interfaces can remain, but
    # every still-needed Part must be cold in both original and copied caches.
    for part in range(len(reused),267):
        suffix='/'+pilot.PREFIX.replace('.','/')+'/Part'+str(part)+'.agdai'
        require(not any(n.endswith(suffix) for n in pool),'unaccepted own proof interface found')
    report=dict(format='othello-indexed-wire-resume6-v1',accepted=False,status='preparing',created_utc=utc(),
        machine=machine,reused_phases=reused,reused_parts=len(reused),reused_kernel_cpu_seconds=sum(p['record']['cpu_seconds'] for p in reused),
        phases=[],kernel_cpu_seconds=0.,initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False,
        previous_receipt_sha256=args.expected_previous_receipt_sha256,previous_report_sha256=args.expected_previous_report_sha256,
        previous_map_sha256=args.expected_previous_map_sha256,closed_previous_service=service,
        interface_policy='same desktop/compiler and saved-meta flags; private copy2 with exact source mtimes; accepted parts reused once')
    def save():atomic_json(out/'report.json',report)
    def guard():
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used<10*2**30 and free>=100*2**30,'storage gate reached; preserved prefix remains usable')
    save();guard()
    copied_bytes=sum(((old/n).stat().st_size+4095)//4096*4096 for n,_ in source_files(old))
    copied_bytes+=sum((old/n).stat().st_blocks*512 for n in pool)
    require(allocated(current.parent)+copied_bytes+40*2**20<10*2**30,'private cache/source staging would exceed the storage cap')
    check=out/'check';check.mkdir()
    for name,_ in source_files(old):
        p=check/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/name,p)
    for name,digest in pool.items():copy_interface(old/name,check/name,digest)
    require(source_identity(check)['source_sha256']==old_source['source_sha256'] and assembly6.interfaces(check)==pool,'private copy differs')
    helper='src/Game/BalancedDemand.agda';require(not (check/helper).exists(),'new helper already exists in old source')
    shutil.copy2(current/helper,check/helper)
    if args.local_warning_filter:
        for part in range(len(reused),267):
            path=check/('src/'+pilot.PREFIX.replace('.','/')+'/Part'+str(part)+'.agda')
            before=path.read_text()
            require(before.startswith('{-# OPTIONS --safe --without-K --cubical-compatible #-}'),'unexpected resumed part pragma')
            after=before.replace('--cubical-compatible #-}', '--cubical-compatible -WnoUnsupportedIndexedMatch #-}',1)
            require(after.replace(' -WnoUnsupportedIndexedMatch','',1)==before,'change beyond optional warning output')
            path.write_text(after)
    wire=args.wire_root/'results/wire-advance6/lower-ply10.wire'
    require(assembly6.sha(wire)==args.expected_wire_sha256,'wire changed')
    parts,owners=data_only.read_partition(wire)
    require(len(parts)==267 and sum(map(len,parts))==53217,'wrong complete descendant')
    dependencies={j:{j}|{owners[r] for e in p for r in e['references']} for j,p in enumerate(parts)}
    layout=tree.generate(check,sizes=list(map(len,parts)),dependencies=dependencies,
        root_packed=compact.pack_state(parts[-1][-1]['state']),cut_depth=4,
        local_warning_filter=args.local_warning_filter)
    require(layout['generated_bytes']<=32*2**20,'hierarchy source cap reached')
    source=source_identity(check)
    targets=[pilot.PREFIX+'.Part'+str(i) for i in range(len(reused),267)]
    targets+=['Tests.IndexedTree6.'+t for t in layout['targets']]
    report.update(checked_source=source,layout=layout,targets=targets,private_cache_bytes=copied_bytes);save()
    borrowed=dict(pool)
    for j,target in enumerate(targets):
        guard();left=args.kernel_cpu_limit-report['kernel_cpu_seconds']
        require(left>=1,'nested kernel allowance reached; accepted prefix preserved')
        part=target.startswith(pilot.PREFIX+'.Part')
        rss=1.5 if part else 3.;heap='-M1350M' if part else '-M2600M'
        own='src/'+target.replace('.','/')+'.agda';suffix='/'+own.removeprefix('src/').removesuffix('.agda')+'.agdai'
        require(not any(n.endswith(suffix) for n in assembly6.interfaces(check)),'own resumed target unexpectedly warm')
        record=run_job('target'+str(j),[args.agda,'--no-libraries','-i','src','--safe','--without-K',
            '--cubical-compatible','--save-metas',own,'+RTS',heap,'-c','-s','-RTS'],out/'records',root=check,
            expected_source_sha256=source['source_sha256'],timeout=420,cpu_limit=min(180,left),rss_limit_gib=rss,
            log_limit_mib=2,metadata=dict(target=target,own_target_cold=True,
                cache_policy='authenticated same-machine prefix copied privately; only remaining own targets checked'))
        report['phases'].append(dict(target=target,record=record));report['kernel_cpu_seconds']+=record['cpu_seconds']
        after=assembly6.interfaces(check)
        unchanged=all(after.get(n)==h for n,h in borrowed.items())
        report['phases'][-1]['borrowed_interfaces_unchanged']=unchanged
        report.update(status='checking-remaining-parts' if part else 'checking-hierarchy',
            last_interface_pool_sha256=digest_entries(after),accepted_parts=len(reused)+sum(p['record']['accepted'] and p['target'].startswith(pilot.PREFIX+'.Part') for p in report['phases']))
        atomic_json(out/'interface-map.json',after);save()
        require(record['accepted'] and unchanged,'resumed target/cache failed: '+target)
        borrowed=after
    require(source_identity(old)==old_source and assembly6.interfaces(old)==pool and source_identity(previous)==outer_source,
        'original accepted source/cache changed')
    report.update(status='complete',accepted=True,finished_utc=utc(),descendant_original_lower_checked=True,
        previous_sources_and_interfaces_unchanged=True);save()
    print(json.dumps(dict(accepted=True,reused_parts=len(reused),new_kernel_cpu_seconds=report['kernel_cpu_seconds'],initial_problem2_proved=False)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','wire-root','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-previous-receipt-sha256','expected-previous-source-sha256',
        'expected-previous-report-sha256','expected-previous-map-sha256','expected-check-source-sha256','expected-wire-sha256'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--kernel-cpu-limit',type=float,default=4500.)
    p.add_argument('--local-warning-filter',action='store_true',help='filter optional cubical warnings in remaining cold parts and new linking modules only')
    run(p.parse_args())


if __name__=='__main__':main()
