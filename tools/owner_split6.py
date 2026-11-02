#!/usr/bin/env python3
"""One bounded recovery: split only the failed root5 assembly into three.

All 27 accepted conditional certificates and six accepted assembly modules
are reused. Each original citation proof obligation and routing literal is
preserved. The old failed source and cache remain immutable. Caps do not rise.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import global_assembly6 as assembly
import lower_pilot6 as pilot
from memory_probe6 import rts_stats
from owner_audit6 import audit
import owner_lower6 as owner
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc

NAMESPACE = owner.PREFIX+'.Root5'
DIRECTORY = owner.DIRECTORY+'/Root5'


def split_sources(original):
    module = NAMESPACE+'.Assemble6'
    if original.count('module '+module+' where')!=1:
        raise ValueError('different failed module')
    matches=list(re.finditer(r'\nmodule P(\d+) where\n',original))
    if [int(m[1]) for m in matches]!=[24,25,26]:
        raise ValueError('requires the exact three unchecked bindings')
    prefix=original[:matches[0].start()]
    sources={}
    for offset,m in enumerate(matches):
        j=int(m[1]);end=matches[offset+1].start() if offset+1<len(matches) else len(original)
        body=original[m.start():end]
        own_prefix=prefix.replace('module '+module+' where',f'module {module}Split{offset} where',1)
        # Omit only imports unused by this exact obligation. No hint, state,
        # certificate or proof obligation is removed or changed.
        lines=[]
        for line in own_prefix.splitlines():
            imported=re.fullmatch(r'import (\S+) as (E\d+|I\d+)',line)
            if imported and not re.search(r'\b'+imported[2]+r'\.',body):
                continue
            lines.append(line)
        own_prefix='\n'.join(lines)+'\n'
        prior=[]
        for earlier in range(24,j):
            if re.search(r'\bP'+str(earlier)+r'\.',body):
                alias=f'S{earlier}'
                prior.append(f'import {module}Split{earlier-24} as {alias}\n')
                body=re.sub(r'\bP'+str(earlier)+r'\.',alias+f'.P{earlier}.',body)
        # Place new imports before the routesFor declaration.
        own_prefix=own_prefix.replace('\nroutesFor :','\n'+''.join(prior)+'\nroutesFor :',1)
        sources[f'{DIRECTORY}/Assemble6Split{offset}.agda']=own_prefix+body
    header=original.split('\n',1)[0]+'\n'+f'module {module} where\n\n'
    facade=header+''.join(f'import {module}Split{i} as S{i}\n' for i in range(3))
    facade+='\n'+''.join(f'module P{24+i} = S{i}.P{24+i}\n' for i in range(3))
    sources[f'{DIRECTORY}/Assemble6.agda']=facade
    return sources


def run(args):
    previous=args.previous.resolve()
    verified=audit(previous,args.expected_previous_sha256)
    old=json.loads((previous/'final.json').read_text())
    last=old['phases'][-1]
    if (verified['pilot_status']!='phase-failed' or old['completed_indices']!=[2,3] or
            last['label']!='root5-assembly6' or last['record']['exit_code']!=251 or
            last['record']['stop_reason'] or last['own_interfaces'] or
            old['nested_cpu_seconds']>=4000):
        raise ValueError('requires the unchanged root5 assembly heap failure; one recovery only')
    donor=Path(old['check_root']);identity=source_identity(donor);pool=assembly6.interfaces(donor)
    if assembly6.machine_identity(args.agda)!=old['machine']:
        raise ValueError('original desktop compiler changed')
    failed=f'{DIRECTORY}/Assemble6.agda'
    sources=split_sources((donor/failed).read_text())
    output,runs=args.output.resolve(),args.runs_root.resolve()
    required=sum((donor/n).stat().st_size for n in pool)+sum(len(t.encode()) for t in sources.values())+32*1024**2
    if output.exists() or runs not in output.parents or not pilot.disk_allowed(pilot.disk_usage(runs),required):
        raise ValueError('fresh root and unchanged storage headroom required')
    output.mkdir(parents=True);root=output/'check';root.mkdir()
    for name,_ in source_files(donor):
        if name!=failed:assembly.hardlink(donor/name,root/name)
    for name,text in sources.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    manifest=bench6.refresh_manifest(root,origin={k:identity[k] for k in ('revision','dirty')})
    for name,digest in pool.items():copy_interface(donor/name,root/name,digest)
    report=dict(format='othello-owner-lower6-split-v1',status='checking',accepted=False,
        created_utc=utc(),check_root=str(root),previous=str(previous),previous_audit=verified,
        previous_report_sha256=args.expected_previous_sha256,machine=old['machine'],
        source_sha256=manifest['source_sha256'],agda_source_sha256=source_identity(root)['agda_source_sha256'],
        borrowed_interfaces_sha256=digest_entries(pool),generated_source_hashes=pilot.source_hashes(sources),
        certificate_parts_rechecked=0,conditional_parts_reused=27,assembly_modules_reused=6,
        unchanged_old_sources=True,phases=[],completed_indices=[],checked_sample_lower_roots=5,
        nested_cpu_seconds=0.,original_training_nested_cpu_seconds=old['nested_cpu_seconds'],
        aggregate_training_nested_cpu_cap=4000,postulates=0,heldout_measured=False,
        initial_problem2_proved=False,production_authorized=False)
    atomic_json(output/'preflight.json',report)
    sequence=[(f'root5-split{i}',f'{DIRECTORY}/Assemble6Split{i}.agda',180) for i in range(3)]
    sequence += [('root5-facade',failed,30),('root5-check',f'{DIRECTORY}/Check.agda',180)]
    for label,target,cap in sequence:
        if old['nested_cpu_seconds']+report['nested_cpu_seconds']+cap+2>4000 or not pilot.disk_allowed(pilot.disk_usage(runs),16*1024**2):
            report['status']='resource-stop';break
        before=assembly6.interfaces(root);suffix=pilot.assert_cold(target,before,owner.DIRECTORY)
        record=run_job(label,[old['machine']['agda_path'],*assembly6.FLAGS,'--save-metas','-v','tc.decl:10',
            '-i','src',target,'+RTS','-M2500M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=cap,timeout=cap*2+30,
            rss_limit_gib=3,log_limit_mib=8,
            metadata=dict(machine=old['machine'],own_target_cold=True,certificate_parts_rechecked=0,
                borrowed_interfaces_sha256=digest_entries(before),timing_group='training-recovery'))
        after=assembly6.interfaces(root);changes=pilot.cache_changes(before,after)
        own={n:d for n,d in after.items() if n.endswith(suffix)}
        unexpected=[n for n in after if n not in before and n not in own]
        accepted=bool(record['accepted'] and len(own)==1 and not changes and not unexpected and
            record['source_unchanged'] and record['expected_source_matches'] and
            record['executable_sha256']==old['machine']['agda_sha256'])
        log=output/'records'/(label+'.log');log_sha=assembly6.sha(log);stats=rts_stats(log.read_text())
        packed=archive(log,log_sha) if accepted else None
        report['phases'].append(dict(label=label,target=target,kind='root' if label=='root5-check' else 'assembly',
            cpu_cap=cap,heap_mib=2500,rss_gib=3,accepted=accepted,record=record,
            record_sha256=assembly6.sha(output/'records'/(label+'.json')),
            cache_changes=changes,unexpected_interfaces=unexpected,own_interfaces=own,
            raw_log_sha256=log_sha,archived_log=packed,rts=stats))
        report['nested_cpu_seconds']+=record['cpu_seconds'];atomic_json(output/'running.json',report)
        if not accepted:report['status']='cache-mismatch' if changes or unexpected else 'phase-failed';break
    report['donor_unchanged']=source_identity(donor)==identity and assembly6.interfaces(donor)==pool
    report['generated_sources_unchanged']=all(assembly6.sha(root/n)==d for n,d in report['generated_source_hashes'].items())
    report['unchanged_old_sources']=all(assembly6.sha(root/n)==d for n,d in old['source_hashes'].items() if n!=failed)
    report['final_interfaces']=assembly6.interfaces(root);report['interfaces_sha256']=digest_entries(report['final_interfaces'])
    report['latest_disk']=pilot.disk_usage(runs)
    report['accepted']=bool(len(report['phases'])==5 and all(p['accepted'] for p in report['phases']) and
        report['donor_unchanged'] and report['generated_sources_unchanged'] and report['unchanged_old_sources'] and
        pilot.disk_allowed(report['latest_disk']))
    if report['accepted']:
        report.update(status='complete',completed_indices=[5],checked_sample_lower_roots=6)
    atomic_json(output/'final.json',report)
    print(json.dumps({k:report[k] for k in ('status','accepted','checked_sample_lower_roots','nested_cpu_seconds')}))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('previous','output','runs-root'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--expected-previous-sha256',required=True);p.add_argument('--agda',required=True)
    raise SystemExit(0 if run(p.parse_args())['accepted'] else 2)
