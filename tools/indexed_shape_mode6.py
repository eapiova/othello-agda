#!/usr/bin/env python3
"""Measure explicit named shape arguments on two accepted indexed parts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil

import assembly6
from cache_resume6 import copy_interface
from indexed_family6 import PREFIX, WARNING, pinned
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def read_shape(text):
    definitions = {}
    for match in re.finditer(r'^shape(\d+) = B\.(?:leaf (\d+)|branch shape(\d+) shape(\d+))$', text, re.M):
        number = int(match[1])
        require(number not in definitions, 'duplicate named shape')
        definitions[number] = dict(number=number, size=int(match[2])) if match[2] is not None else \
            dict(number=number, child_numbers=(int(match[3]), int(match[4])))
    require(len(definitions)==533 and set(definitions)==set(range(533)) and 'shape = shape0\n' in text,
            'complete 267-leaf named baseline shape required')
    leaves=[]
    def build(number, path):
        node=definitions[number];node['path']=path;node['lo']=len(leaves)
        if 'size' in node:
            require(0<node['size']<=200, 'bounded real rows required')
            node['leaf']=len(leaves);leaves.append(node)
        else:
            left,right=node['child_numbers']
            require(left>number and right>number, 'cyclic/backward shape definitions')
            node['left']=build(left,path+'a');node['right']=build(right,path+'b')
        node['hi']=len(leaves)
        return node
    root=build(0,'')
    require(len(leaves)==267 and sum(n['size'] for n in leaves)==53217, 'wrong descendant shape')
    return root,leaves


def embedding(node, target, explicit=False):
    require(node['lo']<=target<node['hi'], 'row outside named subtree')
    if 'leaf' in node:
        return 'B.row'+(' {n = '+str(node['size'])+'}' if explicit else '')+' i'
    left=node['left'];right=node['right'];bit='left' if target<left['hi'] else 'right'
    args=(' {l = Shape.shape'+str(left['number'])+'} {r = Shape.shape'+str(right['number'])+'}') if explicit else ''
    return 'B.'+bit+args+' ('+embedding(node[bit],target,explicit)+')'


def view(node, deps, explicit=False):
    if not any(node['lo']<=d<node['hi'] for d in deps):
        return ('(View.absent {A = State six} {shape = Shape.shape'+str(node['number'])+'})') if explicit else 'View.absent'
    if 'leaf' in node:
        field='S'+str(node['leaf'])+'.states'
        if explicit:
            args=' {A = State six} {n = '+str(node['size'])+'}'
            return '(View.present'+args+' (View.allStates'+args+' '+field+'))'
        return '(View.present (View.allStates '+field+'))'
    args=(' {A = State six} {l = Shape.shape'+str(node['left']['number'])+'} {r = Shape.shape'+
          str(node['right']['number'])+'}') if explicit else ''
    return '(View.branches'+args+' '+view(node['left'],deps,explicit)+' '+view(node['right'],deps,explicit)+')'


def rewrite(original, number, root, leaves):
    n=leaves[number]['size']
    deps={int(x) for x in re.findall(r'^import Tests\.IndexedWire6\.StateData(\d+) as S\d+$',original,re.M)}
    require(number in deps and all(d<=number for d in deps), 'real own/earlier data imports required')
    old_embed='embed = λ i → '+embedding(root,number)+'\n'
    old_view='localView = '+view(root,deps)+'\n'
    changes=[(old_embed,'embed = λ i → '+embedding(root,number,True)+'\n'),
             (old_view,'localView = '+view(root,deps,True)+'\n'),
             ('Family.Lower.checkPart L embed','Family.Lower.checkPart {n = '+str(n)+'} L embed'),
             ('Family.Lower.linkPart L embed','Family.Lower.linkPart {n = '+str(n)+'} L embed')]
    text=original
    for before,after in changes:
        require(text.count(before)==1, 'known unchanged part form required')
        text=text.replace(before,after,1)
    restored=text
    for before,after in reversed(changes):restored=restored.replace(after,before,1)
    require(restored==original, 'change beyond explicit named arguments')
    return text


def run(args):
    current=Path.cwd();out=args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh private output required');out.mkdir(parents=True)
    old=args.baseline.resolve()/'results/indexed-family6/check'
    prior=pinned(old.parent/'report.json',args.expected_baseline_report_sha256)
    pool=pinned(old.parent/'interface-map.json',args.expected_baseline_map_sha256)
    old_source=source_identity(old);machine=assembly6.machine_identity(args.agda)
    require(prior['accepted'] and prior['checked_source']==old_source and assembly6.interfaces(old)==pool and
            digest_entries(pool)==prior['last_interface_pool_sha256'], 'unchanged accepted family baseline required')
    require(machine==prior['machine'] and machine['hostname']=='eapiova' and
            machine['agda_sha256']==args.expected_agda_sha256, 'same pinned desktop compiler required')
    require([p['target'] for p in prior['phases']]==['Family','Part60','Part120'] and
            all(p['record']['accepted'] and p['record']['source_unchanged'] and
                p['record']['executable_sha256']==machine['agda_sha256'] and '--save-metas' in p['record']['argv']
                for p in prior['phases']), 'baseline acceptance flags differ')
    baselines={p['target']:p for p in prior['phases'][1:]}
    borrowed={n:h for n,h in pool.items() if not re.search(r'/Part(?:60|120)\.agdai$',n)}
    require(len(pool)-len(borrowed)==2, 'exclude exactly the two own proof interfaces')
    report=dict(format='othello-indexed-shape-mode6-v1',accepted=False,status='preparing',created_utc=utc(),
                machine=machine,baseline_report_sha256=args.expected_baseline_report_sha256,
                baseline_map_sha256=args.expected_baseline_map_sha256,baselines=baselines,phases=[],kernel_cpu_seconds=0.,
                initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False,
                scope='same real row checks; only explicit named constructor/checker arguments change')
    def save():atomic_json(out/'report.json',report)
    def guard(extra=0):
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used+extra<10*2**30 and free-extra>=100*2**30, 'storage cap reached; baseline retained')
    estimated=sum(((old/name).stat().st_size+4095)//4096*4096 for name,_ in source_files(old))
    estimated+=sum((old/n).stat().st_blocks*512 for n in borrowed)
    guard(estimated+4*2**20)
    check=out/'check';check.mkdir()
    for name,_ in source_files(old):
        path=check/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/name,path)
    for name,h in borrowed.items():copy_interface(old/name,check/name,h)
    root,leaves=read_shape((check/'src/Tests/IndexedWire6/Shape.agda').read_text())
    for number in (60,120):
        path=check/('src/Tests/IndexedWire6/Part'+str(number)+'.agda')
        before=path.read_text();require(WARNING in before.splitlines()[0], 'preserve the local warning filter')
        path.write_text(rewrite(before,number,root,leaves))
    source=source_identity(check);report['checked_source']=source;report['borrowed_interfaces_sha256']=digest_entries(borrowed);save()
    for index,number in enumerate((60,120)):
        guard();target='Part'+str(number);before=assembly6.interfaces(check)
        suffix='/Tests/IndexedWire6/'+target+'.agdai'
        require(not any(n.endswith(suffix) for n in before), 'own proof target is warm')
        left=args.kernel_cpu_limit-report['kernel_cpu_seconds'];require(left>=1, 'nested allowance reached')
        r=run_job('target'+str(index),[args.agda,'--no-libraries','-i','src','--safe','--without-K','--cubical-compatible',
                  '--save-metas','src/Tests/IndexedWire6/'+target+'.agda','+RTS','-M1350M','-c','-s','-RTS'],
                  out/'records',root=check,expected_source_sha256=source['source_sha256'],timeout=220,
                  cpu_limit=min(100,left),rss_limit_gib=1.5,log_limit_mib=2,
                  metadata=dict(target=target,own_target_cold=True,child_proof_imports=False,
                                checker_instance_shared=True,explicit_named_shape_arguments=True))
        after=assembly6.interfaces(check)
        phase=dict(target=target,record=r,borrowed_interfaces_unchanged=all(after.get(n)==h for n,h in before.items()))
        report['phases'].append(phase);report['kernel_cpu_seconds']+=r['cpu_seconds']
        atomic_json(out/'interface-map.json',after);report['last_interface_pool_sha256']=digest_entries(after);save()
        require(phase['borrowed_interfaces_unchanged'] and r['accepted'], 'explicit named-shape target failed: '+target)
        names=[n for n in after if n.endswith(suffix)];require(len(names)==1, 'own proof interface missing')
        size=(check/names[0]).stat().st_size
        phase['interface']=dict(path=names[0],sha256=after[names[0]],bytes=size)
        phase['baseline_to_named_byte_ratio']=baselines[target]['interface']['bytes']/size
        save()
    require(source_identity(old)==old_source and assembly6.interfaces(old)==pool, 'accepted family baseline changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),baseline_sources_and_interfaces_unchanged=True);save()
    print(json.dumps(dict(accepted=True,kernel_cpu_seconds=report['kernel_cpu_seconds'],
                         byte_ratios=[p['baseline_to_named_byte_ratio'] for p in report['phases']])))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','output'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-baseline-report-sha256','expected-baseline-map-sha256'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--kernel-cpu-limit',type=float,default=180.)
    run(parser.parse_args())


if __name__=='__main__':main()
