#!/usr/bin/env python3
"""Check hierarchical linking and an explicit late 16--20 strategy play."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
import indexed_spike6 as spike
import indexed_tree_assembly6 as tree
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def run(args):
    current=Path.cwd();out=args.output.resolve();previous=args.previous.resolve();donor=args.donor.resolve()
    require(not out.exists() and 'results' in out.parts,'fresh frozen output required');out.mkdir(parents=True)
    machine=assembly6.machine_identity(args.agda)
    require(machine['hostname']=='eapiova' and machine['agda_sha256']==args.expected_agda_sha256,'pinned desktop compiler required')
    previous_source=source_identity(previous)
    require(previous_source['source_sha256']==args.expected_previous_source_sha256,'accepted spike source changed')
    report_path=previous/'results/indexed-spike6/report.json'
    require(assembly6.sha(report_path)==args.expected_previous_report_sha256,'accepted spike report changed')
    old=json.loads(report_path.read_text());old_check=previous/'results/indexed-spike6/check'
    require(old['accepted'] and old['status']=='complete' and len(old['phases'])==7
            and all(p['record']['accepted'] for p in old['phases']),'complete accepted real spike required')
    require(source_identity(old_check)==old['checked_source'],'accepted spike checked source differs')
    previous_pool=assembly6.interfaces(old_check)
    donor_source=source_identity(donor);donor_pool=assembly6.interfaces(donor)
    require(donor_source['source_sha256']==args.expected_donor_source_sha256,'generic source donor differs')
    generic={n:h for n,h in donor_pool.items() if '/src/Tests/' not in n}
    require(len(generic)==31 and digest_entries(generic)==args.expected_generic_interfaces_sha256,'generic interface donor differs')
    report=dict(format='othello-indexed-tree-pilot6-v1',status='preparing',accepted=False,phases=[],
        created_utc=utc(),machine=machine,kernel_cpu_seconds=0.,initial_problem2_proved=False,
        optimal_initial_pair_proved=False,production_authorized=False,late_joint_16_20_checked=False,
        previous_report_sha256=args.expected_previous_report_sha256,scope='real late-position hierarchy and checked joint play')
    def save():atomic_json(out/'report.json',report)
    def guard():
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used<10*2**30 and free>=100*2**30,'storage gate reached; checked prefix retained')
    save();guard();check=out/'check';check.mkdir()
    shutil.copytree(current/'src',check/'src',copy_function=shutil.copy2)
    shutil.copy2(current/'othello.agda-lib',check/'othello.agda-lib')
    for name in json.loads((donor/'SNAPSHOT.json').read_text())['files']:
        if name.endswith('.agda') and any(n.endswith('/'+name.removeprefix('src/').removesuffix('.agda')+'.agdai') for n in generic):
            require((current/name).read_bytes()==(donor/name).read_bytes(),'generic source differs')
            shutil.copystat(donor/name,check/name)
    # Copy the exact previously checked fixtures; the new BalancedView API
    # deliberately gets checked again, so no historical Part cache is borrowed.
    for name,digest in old['prepared']['generated_sha256'].items():
        require(assembly6.sha(old_check/name)==digest,'accepted generated fixture changed')
        dest=check/name;require(not dest.exists(),'fixture name collides with core source')
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old_check/name,dest)
    layouts=[];targets=[]
    for side in ('lower','upper'):
        prefix='Tests.IndexedTree'+side.capitalize()+'6'
        layouts.append(tree.generate(check,sizes=[2,1,1],dependencies={0:[0],1:[0],2:[1]},
            root_packed=spike.compact.pack_state(spike.IMAGE),
            base_prefix=spike.PREFIX,prefix=prefix,cut_depth=1,state_field=side,body_field=side,
            linked_field=side+'Linked',side=side))
        targets.extend(prefix+'.'+name for name in layouts[-1]['targets'])
    spines=(old_check/'src/Tests/IndexedSpike6/Spines.agda').read_text()
    spines=spines.replace('module Tests.IndexedSpike6.Spines where','module Tests.IndexedTreePlay6 where')
    spines=spines.replace('import Tests.IndexedSpike6.Assemble as A','import Tests.IndexedTreeUpper6.Root as A')
    spines=spines.replace('Bk.plug A.offUpper','Bk.plug offUpper')
    spines=spines.replace('module W =', '''abstract
  offUpper : Proven Fast.fastGame6 black (upperGoal 4) (B.lookupVec S0.upper B.fzero)
  offUpper = A.provenAt (B.left (B.row B.fzero))

module W =''')
    path=check/'src/Tests/IndexedTreePlay6.agda';path.write_text(spines)
    targets+=['Tests.IndexedTreePlay6','Everything6']
    for name,digest in generic.items():copy_interface(donor/name,check/name,digest)
    source=source_identity(check);report.update(checked_source=source,layouts=layouts,
        targets=targets,generated_play_sha256=assembly6.sha(path));save()
    for j,target in enumerate(targets):
        guard();require(report['kernel_cpu_seconds']<args.kernel_cpu_limit,'kernel allowance reached')
        own='src/'+target.replace('.','/')+'.agda'
        require(not any(n.endswith('/'+own.removeprefix('src/').removesuffix('.agda')+'.agdai')
                        for n in assembly6.interfaces(check)),'own target unexpectedly warm')
        record=run_job('target'+str(j),[args.agda,'--no-libraries','-i','src','--safe','--without-K',
            '--cubical-compatible','--save-metas',own,'+RTS','-M1350M','-c','-s','-RTS'],
            out/'records',root=check,expected_source_sha256=source['source_sha256'],
            timeout=180,cpu_limit=min(90,args.kernel_cpu_limit-report['kernel_cpu_seconds']),
            rss_limit_gib=1.5,log_limit_mib=2,metadata=dict(target=target,
                cache_policy='own hierarchy target cold; compatible same-machine generic and prior checked data reused'))
        report['phases'].append(dict(target=target,record=record));report['kernel_cpu_seconds']+=record['cpu_seconds']
        report.update(status='checking-hierarchy',last_interface_pool_sha256=digest_entries(assembly6.interfaces(check)))
        atomic_json(out/'interface-map.json',assembly6.interfaces(check));save()
        require(record['accepted'],'hierarchical target failed: '+target)
    require(source_identity(previous)==previous_source and assembly6.interfaces(old_check)==previous_pool
        and source_identity(donor)==donor_source and assembly6.interfaces(donor)==donor_pool,'accepted donors changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),late_joint_16_20_checked=True,
        original_rule_lower_and_upper_checked=True,historical_sources_and_interfaces_unchanged=True)
    save();print(json.dumps(dict(accepted=True,kernel_cpu_seconds=report['kernel_cpu_seconds'],initial_problem2_proved=False)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','donor','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-previous-source-sha256','expected-previous-report-sha256',
                 'expected-donor-source-sha256','expected-generic-interfaces-sha256'):p.add_argument('--'+name,required=True)
    p.add_argument('--kernel-cpu-limit',type=float,default=200.)
    run(p.parse_args())


if __name__=='__main__':main()
