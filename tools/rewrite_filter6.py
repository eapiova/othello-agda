#!/usr/bin/env python3
"""Measure a module-local RewritesNothing filter on unchanged certificates.

Proof terms and compact data are preserved. Only the namespace and one local
warning option change. The two certificate checks must be performed afresh;
accepted generic proofs are copied on their original checking machine.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import global_assembly6 as assembly
import owner_cuts6 as cuts
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, positive, run_job, utc
from warning_tables6 import census_with_warnings

OLD='Tests.LowerPilot6.Group0'
PREFIX='Tests.RewriteFilter6'
DIRECTORY='src/Tests/RewriteFilter6'
WARNING='-WnoRewritesNothing'


def filtered_source(original, *, old=OLD, namespace=PREFIX, part=None):
    required=['--save-metas','--safe','--without-K','--cubical-compatible','-WnoUnsupportedIndexedMatch']
    option=re.search(r'^\{-# OPTIONS ([^\n]+) #-\}$',original,re.M)
    module=re.search(r'^module (\S+) where$',original,re.M)
    expected={f'{old}.Part{i}' for i in ((0,1) if part is None else (part,))}
    if (not option or any(x not in option[1].split() for x in required) or WARNING in original or
            original.count('accepted = refl {x = true}') != 1 or
            not module or module[1] not in expected):
        raise ValueError('requires an unchanged accepted pilot certificate')
    changed=original.replace(old,namespace)
    changed=changed.replace(option[0],option[0].replace(' #-}',' '+WARNING+' #-}'),1)
    if (changed.replace(' '+WARNING,'',1).replace(namespace,old) != original or
            re.findall(r'"([^"\n]*)"',changed) != re.findall(r'"([^"\n]*)"',original)):
        raise ValueError('change beyond the warning option and namespace')
    return changed


def run(args):
    previous=args.previous.resolve()
    old,donor,identity,pool,machine=cuts.verified_donor(previous,args.expected_previous_sha256,args.agda)
    sources={f'{DIRECTORY}/Part{i}.agda':filtered_source(
        (donor/f'src/{OLD.replace(".","/")}/Part{i}.agda').read_text()) for i in range(2)}
    generic={n:d for n,d in pool.items() if '/src/Tests/' not in n}
    if not generic or any('/src/Tests/' in n for n in generic):
        raise ValueError('generic cache selection differs')
    output,runs=args.output.resolve(),args.runs_root.resolve()
    needed=sum((donor/n).stat().st_size for n in generic)+sum(len(s.encode()) for s in sources.values())+16*1024**2
    if output.exists() or runs not in output.parents or not cuts.pilot.disk_allowed(cuts.pilot.disk_usage(runs),needed):
        raise ValueError('fresh private root and storage headroom required')
    output.mkdir(parents=True)
    root=output/'check';root.mkdir()
    for name,_ in source_files(donor):
        assembly.hardlink(donor/name,root/name)
    for name,text in sources.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    manifest=bench6.refresh_manifest(root,origin={k:identity[k] for k in ('revision','dirty')})
    for name,digest in generic.items():
        copy_interface(donor/name,root/name,digest)
    baseline={str(i):census_with_warnings(donor/f'_build/2.9.0/agda/src/{OLD.replace(".","/")}/Part{i}.agdai',
        pool[f'_build/2.9.0/agda/src/{OLD.replace(".","/")}/Part{i}.agdai']) for i in range(2)}
    report=dict(format='othello-rewrite-filter6-v1',status='checking',accepted=False,created_utc=utc(),
        previous=str(previous),previous_report_sha256=args.expected_previous_sha256,check_root=str(root),
        source_sha256=manifest['source_sha256'],agda_source_sha256=source_identity(root)['agda_source_sha256'],
        machine=machine,borrowed_interfaces=generic,borrowed_interfaces_sha256=digest_entries(generic),
        generated_source_hashes=cuts.pilot.source_hashes(sources),baseline=baseline,phases=[],
        nested_cpu_seconds=0.,nested_cpu_budget=args.kernel_cpu_budget,certificate_parts_rechecked=0,
        checked_sample_lower_roots=5,postulates=0,heldout_measured=False,initial_problem2_proved=False,
        production_authorized=False,warning_filter=WARNING,warning_filter_scope='new module OPTIONS only')
    atomic_json(output/'preflight.json',report)
    for i in range(2):
        label,target=f'Part{i}',f'{DIRECTORY}/Part{i}.agda'
        before=assembly6.interfaces(root)
        suffix=cuts.pilot.assert_cold(target,before,DIRECTORY)
        left=args.kernel_cpu_budget-report['nested_cpu_seconds']
        if left < 10 or not cuts.pilot.disk_allowed(cuts.pilot.disk_usage(runs),4*1024**2):
            report['status']='cpu-stop' if left < 10 else 'disk-stop';break
        cap=min(90,left-2)
        record=run_job(label,[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
            '+RTS','-M1350M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=cap,timeout=cap*2+30,
            rss_limit_gib=1.5,log_limit_mib=2,metadata=dict(machine=machine,own_target_cold=True,
                warning_filter=WARNING,warning_filter_scope='new module OPTIONS only',
                borrowed_interfaces_sha256=digest_entries(before)))
        after=assembly6.interfaces(root)
        changes=cuts.pilot.cache_changes(before,after)
        own={n:d for n,d in after.items() if n.endswith(suffix)}
        unexpected=[n for n in after if n not in before and n not in own]
        log=output/'records'/(label+'.log');raw=log.read_text();digest=assembly6.sha(log)
        footprint=census_with_warnings(root/next(iter(own)),next(iter(own.values()))) if len(own)==1 else None
        accepted=bool(record['accepted'] and len(own)==1 and not changes and not unexpected and
            record['source_unchanged'] and record['expected_source_matches'] and
            record['executable_sha256']==machine['agda_sha256'] and footprint['warnings']==0)
        packed=archive(log,digest) if accepted else None
        report['phases'].append(dict(label=label,target=target,expected_outcome_met=accepted,record=record,
            record_sha256=assembly6.sha(output/'records'/(label+'.json')),cache_changes=changes,
            unexpected_interfaces=unexpected,own_interfaces=own,raw_log_sha256=digest,
            archived_log=packed,rts=rts_stats(raw),interface=footprint))
        report['nested_cpu_seconds']+=record['cpu_seconds']
        report['certificate_parts_rechecked']+=int(accepted)
        atomic_json(output/'running.json',report)
        if not accepted:
            report['status']='phase-failed';break
    report.update(donor_unchanged=source_identity(donor)==identity and assembly6.interfaces(donor)==pool,
        generated_sources_unchanged=all(assembly6.sha(root/n)==d for n,d in report['generated_source_hashes'].items()),
        final_interfaces=assembly6.interfaces(root),latest_disk=cuts.pilot.disk_usage(runs))
    report['interfaces_sha256']=digest_entries(report['final_interfaces'])
    report['accepted']=bool(len(report['phases'])==2 and all(x['expected_outcome_met'] for x in report['phases']) and
        report['donor_unchanged'] and report['generated_sources_unchanged'] and cuts.pilot.disk_allowed(report['latest_disk']))
    if report['accepted']:report['status']='complete'
    atomic_json(output/'final.json',report)
    print({k:report[k] for k in ['status','accepted','nested_cpu_seconds','certificate_parts_rechecked']})
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['previous','output','runs-root']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-previous-sha256',required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--kernel-cpu-budget',type=positive,required=True)
    raise SystemExit(0 if run(p.parse_args())['accepted'] else 2)
