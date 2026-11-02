#!/usr/bin/env python3
"""Measure default interface serialization on two accepted indexed parts.

This rechecks unchanged part/dependency sources with --no-save-metas in a fresh
private cache. The baseline is accepted same-machine data, never a proof premise.
The comparison concerns interface bytes; cache conditions differ for CPU timing.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil

import assembly6
from cache_resume6 import copy_interface
import data_only_pilot6 as data_only
import indexed_wire_pilot6 as pilot
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def run(args):
    current=Path.cwd();out=args.output.resolve();old=args.baseline.resolve()
    require(not out.exists() and 'results' in out.parts,'fresh mode output required');out.mkdir(parents=True)
    machine=assembly6.machine_identity(args.agda)
    require(machine['hostname']=='eapiova' and machine['agda_sha256']==args.expected_agda_sha256,'pinned compiler required')
    old_check=old/'results/indexed-wire6/check';old_source=source_identity(old_check)
    require(old_source['source_sha256']==args.expected_baseline_check_source_sha256,'baseline source differs')
    for _ in range(3):
        baseline=json.loads((old/'results/indexed-wire6/report.json').read_text())
        pool=json.loads((old/'results/indexed-wire6/interface-map.json').read_text())
        if digest_entries(pool)==baseline['last_interface_pool_sha256']:break
    else:raise ValueError('baseline atomic report/map differ; inspect the same job later')
    require(baseline['machine']['agda_sha256']==machine['agda_sha256'] and baseline['machine']['hostname']==machine['hostname'],
            'baseline is another machine/compiler')
    baselines={}
    for part in args.parts:
        target='Part'+str(part)
        matches=[p for p in baseline['phases'] if p['target']==target]
        require(len(matches)==1 and matches[0]['record']['accepted'],'part lacks an accepted baseline')
        record=matches[0]['record']
        require(record['source_unchanged'] and record['expected_source_matches'] and
            record['executable_sha256']==machine['agda_sha256'] and '--save-metas' in record['argv'] and
            record['source_sha256']==old_source['source_sha256'],'baseline acceptance identity differs')
        suffix='/'+pilot.PREFIX.replace('.','/')+'/'+target+'.agdai'
        names=[n for n in pool if n.endswith(suffix)];require(len(names)==1,'own interface missing')
        path=old_check/names[0];require(assembly6.sha(path)==pool[names[0]],'baseline own interface changed')
        baselines[target]=dict(record=record,interface_path=names[0],sha256=pool[names[0]],bytes=path.stat().st_size)
    report=dict(format='othello-indexed-cache-mode6-v1',accepted=False,status='preparing',created_utc=utc(),
        machine=machine,baselines=baselines,phases=[],kernel_cpu_seconds=0.,
        cache_mode='--save-metas' if args.local_warning_filter else '--no-save-metas',
        local_warning_filter='-WnoUnsupportedIndexedMatch' if args.local_warning_filter else None,
        initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False,
        scope='interface-byte comparison; dependency warmth differs from baseline for CPU timing')
    def save():atomic_json(out/'report.json',report)
    def guard():
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used<10*2**30 and free>=100*2**30,'storage gate reached; preserve all receipts')
    save();guard();check=out/'check';check.mkdir()
    shutil.copytree(current/'src',check/'src',copy_function=shutil.copy2)
    shutil.copy2(current/'othello.agda-lib',check/'othello.agda-lib')
    wire=args.wire_root/'results/wire-advance6/lower-ply10.wire'
    require(assembly6.sha(wire)==args.expected_wire_sha256,'historical wire changed')
    layout=pilot.generate(check,wire)
    require(layout['generated_sha256']==baseline['prepared']['generated_sha256'],'experiment changes generated parts')
    # Everything6 gained an unrelated import; the checked Part dependencies
    # are otherwise byte-identical to the original accepted source snapshot.
    for path in (old_check/'src').rglob('*.agda'):
        name=path.relative_to(old_check)
        if str(name)=='src/Everything6.agda':continue
        require((check/name).read_bytes()==path.read_bytes(),'a checked dependency source differs: '+str(name))
    borrowed={}
    if args.local_warning_filter:
        # Keep compiler flags and dependency caches exactly as in the accepted
        # baseline. Only the selected modules' optional warning output changes.
        borrowed={n:h for n,h in pool.items() if not re.search(r'/Part[0-9]+\.agdai$',n)}
        for name in data_only.borrowed_sources(borrowed):
            require((old_check/name).read_bytes()==(check/name).read_bytes(),'borrowed dependency source differs')
            shutil.copystat(old_check/name,check/name)
        for name,h in borrowed.items():copy_interface(old_check/name,check/name,h)
        for part in args.parts:
            path=check/('src/'+pilot.PREFIX.replace('.','/')+'/Part'+str(part)+'.agda')
            before=path.read_text()
            require(before.startswith('{-# OPTIONS --safe --without-K --cubical-compatible #-}'),'unexpected part pragma')
            after=before.replace('--cubical-compatible #-}', '--cubical-compatible -WnoUnsupportedIndexedMatch #-}',1)
            path.write_text(after)
            require(after.replace(' -WnoUnsupportedIndexedMatch','',1)==before,'change beyond local warning filter')
    source=source_identity(check);report['checked_source']=source;save()
    for j,part in enumerate(args.parts):
        guard();target='Part'+str(part)
        require(not any(n.endswith('/'+target+'.agdai') for n in assembly6.interfaces(check)),'own target is warm')
        record=run_job('target'+str(j),[args.agda,'--no-libraries','-i','src','--safe','--without-K',
            '--cubical-compatible',report['cache_mode'],'src/'+pilot.PREFIX.replace('.','/')+'/'+target+'.agda',
            '+RTS','-M1350M','-c','-s','-RTS'],out/'records',root=check,expected_source_sha256=source['source_sha256'],
            timeout=210,cpu_limit=min(100,args.kernel_cpu_limit-report['kernel_cpu_seconds']),rss_limit_gib=1.5,
            log_limit_mib=2,metadata=dict(target=target,cache_policy=
                'saved-meta data/generic interfaces copied privately; only local warning filter changes' if args.local_warning_filter
                else 'fresh normal-mode cache; own target cold; no baseline interfaces copied'))
        report['phases'].append(dict(target=target,record=record));report['kernel_cpu_seconds']+=record['cpu_seconds']
        pool_after=assembly6.interfaces(check);atomic_json(out/'interface-map.json',pool_after)
        report['last_interface_pool_sha256']=digest_entries(pool_after);save()
        require(all(pool_after.get(n)==h for n,h in borrowed.items()),'borrowed dependency interface changed')
        require(record['accepted'],'normal-mode target failed: '+target)
        name=baselines[target]['interface_path'];path=check/name
        require(name in pool_after and path.is_file(),'normal-mode own interface missing')
        report['phases'][-1]['interface_comparison']=dict(saved_bytes=baselines[target]['bytes'],
            normal_bytes=path.stat().st_size,normal_sha256=pool_after[name],
            saved_to_normal_byte_ratio=baselines[target]['bytes']/path.stat().st_size)
        save()
    require(source_identity(old_check)==old_source,'baseline sources changed')
    require(all(assembly6.sha(old_check/b['interface_path'])==b['sha256'] for b in baselines.values()),'baseline interfaces changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),baseline_sources_and_selected_interfaces_unchanged=True)
    save();print(json.dumps(dict(accepted=True,kernel_cpu_seconds=report['kernel_cpu_seconds'],
        byte_ratios=[p['interface_comparison']['saved_to_normal_byte_ratio'] for p in report['phases']])))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','wire-root','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-baseline-check-source-sha256','expected-wire-sha256'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--parts',type=int,nargs='+',default=[60,120])
    p.add_argument('--kernel-cpu-limit',type=float,default=180.)
    p.add_argument('--local-warning-filter',action='store_true',
        help='measure only the selected source modules optional cubical warning filter; preserve saved-meta compiler flags')
    args=p.parse_args();require(len(args.parts)==2 and len(set(args.parts))==2,'exactly two distinct measurement targets required')
    run(args)


if __name__=='__main__':main()
