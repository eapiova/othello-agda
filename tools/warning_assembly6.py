#!/usr/bin/env python3
"""Cold same-100-root assembly with a local cubical-warning output filter.

No core or certificate changes. Proof imports use unchanged same-binary private
cache copies. A false terminal upper certificate must be rejected first.
"""
from __future__ import annotations
import argparse
import hashlib
import gzip
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
from explicit_exports6 import pack_tables
import global_assembly6 as assembly
from memory_probe6 import rts_stats
from packed_assembly6 import generated_sources as packed_sources
from provenance import digest_entries,source_files,source_identity
from run_job import atomic_json,run_job
from warning_tables6 import census_with_warnings,warning_source,OLD,NEW,WARNING
from warning_cost6 import predict

GIB=1024**3


def negative_rejected(record,changes,own,text):
    if (record['accepted'] or record['exit_code'] in (None,0) or record['stop_reason'] or changes or own):
        return False
    diagnostic=text.split('error: [UnequalTerms]',1)[-1]
    terms=re.search(r'\b(true|false)\s+and\s+(true|false)\s+are not equal at type Bool',diagnostic)
    return bool('error: [UnequalTerms]' in text and terms and terms[1]!=terms[2] and
                'refl {x = true}' in diagnostic and
                'checkShardBy keyed6 Fast.fastGame6 black (upperGoal 4)' in diagnostic)


def generated_sources(plan):
    packed,groups,_=packed_sources(plan)
    sources={name.replace('/PackedTables6/','/WarningTables6/'):warning_source(text)
             for name,text in packed.items()}
    for name,text in sources.items():
        original=packed[name.replace('/WarningTables6/','/PackedTables6/')]
        if text.replace(' '+WARNING,'',1).replace(NEW,OLD)!=original:
            raise ValueError('change beyond the local warning pragma and namespace')
    return sources,groups,packed


def negative_source():
    # A terminal all-White board refutes Black's claimed upper bound +4.
    state='w'+'2'*36
    text,_,_=assembly.part_source(0,[dict(state=state,certificate='L',references=[])],{state:0},'upper')
    text=pack_tables(text.replace(assembly.PREFIX,OLD+'.Negative'))
    text=text.replace('module '+OLD+'.Negative.Part0 where','module '+OLD+'.Negative where')
    text=text.replace('--safe ','--save-metas --safe ',1)
    text=text.replace('  shape = refl\n','  shape = refl {x = states}\n')
    text=text.replace('  accepted = refl\n','  accepted = refl {x = true}\n')
    return warning_source(text)


def run(args):
    started=time.monotonic();previous=args.previous.resolve()
    final=json.loads((previous/'packed.json').read_text())
    audit=json.loads((previous/'phase-records.json').read_text())
    donor=Path(final['resumed_from'])/'check';pool=audit['final_interfaces']
    identity=source_identity(donor);machine=assembly6.machine_identity(args.agda)
    pilot=json.loads((args.pilot/'warning.json').read_text())
    if (final['status']!='collector-failed' or final['accepted'] or final['completed_groups']!=list(range(10)) or
            final['checked_sample_upper_roots']!=100 or identity['source_sha256']!=final['source_sha256'] or
            assembly6.interfaces(donor)!=pool or len(pool)!=305 or machine!=final['machine'] or
            not pilot['accepted'] or pilot['status']!='complete' or pilot['machine']!=machine or
            pilot['original_source_sha256']!=identity['source_sha256'] or
            any(not p['accepted'] or p['cache_changes'] or p['interface']['unsupported_indexed_match_warnings']
                for p in pilot['phases']) or
            any(pilot['phases'][i]['interface']['nodes']>=.35*pilot['baseline'][str(i)]['nodes'] for i in (0,1))):
        raise ValueError('requires unchanged completed sample and successful local-filter pilot')
    plan=json.loads(args.plan.read_text());assembly.validate_plan(plan)
    if assembly6.sha(args.plan)!=final['plan_sha256']:raise ValueError('different original sample plan')
    sources,groups,packed=generated_sources(plan)
    for name,text in packed.items():
        if (donor/name).read_text()!=text:raise ValueError('old packed source regeneration differs')
    sources['src/Tests/WarningTables6/Negative.agda']=negative_source()
    generated_hashes={name:hashlib.sha256(text.encode()).hexdigest() for name,text in sources.items()}
    if digest_entries(generated_hashes)!=args.expected_generated_sha256:
        raise ValueError('generated sources differ from the recorded laptop preflight')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    generic={name:digest for name,digest in pool.items() if '/Tests/PackedTables6/' not in name}
    if len(generic)!=32:raise ValueError('wrong generic pool')
    reused=None
    if args.resume:
        old=json.loads((args.resume/'assembly.json').read_text())
        old_audit=json.loads((args.resume/'phase-records.json').read_text())
        root=Path(old.get('check_root',args.resume.resolve()/'check'));manifest=json.loads((root/'SNAPSHOT.json').read_text())
        current=source_identity(root)
        stopped=old['status']=='artifact-budget-stopped' and old['completed_groups']==list(range(5))
        negative_only=old['status']=='negative-fixture-failed' and len(old['phases'])==1
        before=assembly6.interfaces(root)
        if (not (negative_only or stopped) or old['accepted'] or
                old['machine']!=machine or current['source_sha256']!=old['source_sha256'] or
                before!=old_audit['final_interfaces'] or
                any(before.get(n)!=h for n,h in generic.items()) or
                old['generated_source_hashes']!=generated_hashes):
            raise ValueError('requires an unchanged negative-only or five-group checkpoint')
        for name,digest in generated_hashes.items():
            if assembly6.sha(root/name)!=digest:raise ValueError('prepared proof source changed')
        record=old_audit['records']['negative-terminal-upper']
        negative_directory=(Path(old['resumed_from']) if stopped else args.resume)
        log=negative_directory/'records/negative-terminal-upper.log'
        if (assembly6.sha(log)!=old_audit['log_hashes']['negative-terminal-upper'] or
                assembly6.sha(negative_directory/'records/negative-terminal-upper.json')!=old_audit['record_hashes']['negative-terminal-upper'] or
                record['executable_sha256']!=machine['agda_sha256'] or not record['source_unchanged'] or
                not record['expected_source_matches'] or not record['own_target_cold'] or
                not negative_rejected(record,old['phases'][0]['cache_changes'],[],log.read_text())):
            raise ValueError('old negative fixture did not reject the actual false Boolean')
        reused=dict(phase=dict(old['phases'][0],expected_outcome_met=True),record=record,
                    record_sha256=old_audit['record_hashes']['negative-terminal-upper'],
                    log_sha256=old_audit['log_hashes']['negative-terminal-upper'],old=old,audit=old_audit)
        if stopped:
            expected=['negative-terminal-upper']
            for group in groups[:5]:
                expected += [f'group{group["index"]}-part{j}' for j in range(group['parts'])]
                expected.append(f'group{group["index"]}-bounds')
            if [p['label'] for p in old['phases']]!=expected or len(before)!=165:
                raise ValueError('different accepted prefix or cache size')
            for phase in old['phases'][1:]:
                rec=old_audit['records'][phase['label']]
                if (not phase['accepted'] or not rec['accepted'] or phase['cache_changes'] or
                        not rec['own_target_cold'] or not rec['source_unchanged'] or
                        not rec['expected_source_matches'] or rec['source_sha256']!=current['source_sha256'] or
                        rec['executable_sha256']!=machine['agda_sha256'] or
                        phase['interface']['unsupported_indexed_match_warnings'] or
                        assembly6.sha(args.resume/'records'/f"{phase['label']}.json")!=old_audit['record_hashes'][phase['label']]):
                    raise ValueError('an accepted prefix check differs')
            # Only recoverable log bytes change; every source/interface remains.
            archives={}
            if args.prefix_archives:
                receipt=json.loads(args.prefix_archives.read_text())
                if (not receipt['sources_unchanged'] or not receipt['interfaces_unchanged'] or
                        receipt['source_sha256']!=current['source_sha256'] or
                        receipt['interfaces_sha256']!=digest_entries(before)):
                    raise ValueError('external archive provenance differs')
                archives=receipt['records']
                if set(archives)!={p['label'] for p in old['phases'][1:]}:
                    raise ValueError('different archived prefix labels')
                for label,row in archives.items():
                    path=args.resume/'records'/row['archive_name']
                    if (row['original_name']!=label+'.log' or row['original_sha256']!=old_audit['log_hashes'][label] or
                            assembly6.sha(path)!=row['archive_sha256'] or
                            hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()!=row['original_sha256']):
                        raise ValueError('archived prefix does not recover the original log')
            else:
                for phase in old['phases'][1:]:
                    label=phase['label'];path=args.resume/'records'/f'{label}.log'
                    archives[label]=archive(path,old_audit['log_hashes'][label])
                    archives[label]['directory']=str(path.parent.resolve())
            atomic_json(output/'prefix-log-archives.json',archives)
            if assembly6.interfaces(root)!=before or source_identity(root)!=current:
                raise ValueError('prefix cache/source changed during archival')
    else:
        root=output/'check';root.mkdir()
        for name,_ in source_files(donor):assembly.hardlink(donor/name,root/name)
        for name,text in sources.items():
            path=root/name
            if path.exists():raise ValueError('new namespace already exists')
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        manifest=bench6.refresh_manifest(root,origin={k:identity[k] for k in ('revision','dirty')})
        for name,digest in generic.items():copy_interface(donor/name,root/name,digest)
    report=dict(format='othello-warning-assembly6-v1',status='running',accepted=False,
        machine=machine,source_sha256=manifest['source_sha256'],
        agda_source_sha256=source_identity(root)['agda_source_sha256'],
        original_source_sha256=identity['source_sha256'],plan_sha256=final['plan_sha256'],
        pilot_report_sha256=assembly6.sha(args.pilot/'warning.json'),groups=groups,
        completed_groups=[],checked_sample_upper_roots=0,phases=[],measured_kernel_cpu_seconds=0,
        heldout_groups=[9],training_groups=list(range(9)),heldout_declared_before_checks=True,
        interface_policy='one serial private cache; own targets cold; unchanged hashes before/after',
        warning_filter=WARNING,warning_filter_scope='new generated modules OPTIONS only; absent from command line',
        generated_source_hashes={name:assembly6.sha(root/name) for name in sources},
        scope='same 100 original upper-bound sample roots and unchanged certificate obligations',
        initial_problem2_proved=False,production_authorized=False,maximum_runs_bytes=10*GIB,
        phases_artifact_growth_limit_mib=32,check_root=str(root),
        resumed_from=str(args.resume.resolve()) if args.resume else None,
        measured_new_kernel_cpu_seconds=0)
    runs=Path(__file__).resolve().parents[1].parent
    def usage():
        return dict(runs_bytes=int(subprocess.check_output(['du','-s','-B1',str(runs)],text=True).split()[0]),
                    free_bytes=shutil.disk_usage(runs).free)
    starting=usage();report['initial_disk']=starting
    required=(12 if reused and stopped else 24)*1024**2
    if starting['runs_bytes']+required>=10*GIB:
        raise ValueError('insufficient headroom for remaining interfaces and compressed logs')
    records={};logs={};hashes={}
    if reused:
        report['phases']=list(reused['old']['phases'])
        report['phases'][0]=reused['phase']
        report['completed_groups']=list(reused['old']['completed_groups'])
        report['checked_sample_upper_roots']=reused['old']['checked_sample_upper_roots']
        report['measured_kernel_cpu_seconds']=reused['old']['measured_kernel_cpu_seconds']
        report['reused_negative_fixture']=True
        report['reused_checked_parts']=sum('-part' in p['label'] for p in report['phases'])
        records=dict(reused['audit']['records']);logs=dict(reused['audit']['log_hashes'])
        hashes=dict(reused['audit']['record_hashes'])
        if stopped:report['prefix_log_archives_sha256']=assembly6.sha(output/'prefix-log-archives.json')
    def save():atomic_json(output/'assembly.json',report)
    def disk_ok():
        current=usage();report['latest_disk']=current
        return (current['runs_bytes']<10*GIB and current['free_bytes']>=100*GIB and
                current['runs_bytes']-starting['runs_bytes']<=32*1024**2)
    def check(label,target,collector=False,negative=False):
        left=args.kernel_cpu_budget-report['measured_new_kernel_cpu_seconds']
        if left<15:return None
        before=assembly6.interfaces(root)
        suffix='/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'
        if any(name.endswith(suffix) for name in before):raise ValueError('own target not cold')
        if assembly6.machine_identity(args.agda)!=machine:raise ValueError('compiler changed')
        heap,rss,cap=(2500,3,180) if collector else (1350,1.5,90)
        record=run_job(label,[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
            '+RTS',f'-M{heap}M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=min(cap,left),timeout=cap*3,
            rss_limit_gib=rss,log_limit_mib=2,metadata={'machine':machine,'own_target_cold':True,
                'borrowed_interfaces_sha256':digest_entries(before),
                'interface_isolation':'private inode copies; one serial cache',
                'negative_certificate_fixture':negative})
        report['measured_kernel_cpu_seconds']+=record['cpu_seconds']
        report['measured_new_kernel_cpu_seconds']+=record['cpu_seconds']
        after=assembly6.interfaces(root);changes=[n for n,h in before.items() if after.get(n)!=h]
        log=output/'records'/f'{label}.log';text=log.read_text()
        metric=assembly.metrics(record)
        metric.update(label=label,target=target,exit_code=record['exit_code'],heap_mib=heap,
            rss_limit_gib=rss,cache_changes=changes,rts=rts_stats(text),negative_fixture=negative)
        if changes:metric['accepted']=False;metric['rejection']='prior-cache-hash-changed'
        own=[n for n in after if n.endswith(suffix)]
        if negative:
            metric['expected_outcome_met']=negative_rejected(record,changes,own,text)
        else:
            if metric['accepted']:
                if len(own)!=1:raise ValueError('missing accepted interface')
                metric['interface']=census_with_warnings(root/own[0],after[own[0]])
                if metric['interface']['unsupported_indexed_match_warnings']:
                    raise ValueError('local warning filter not applied')
            metric['expected_outcome_met']=metric['accepted']
        records[label]=record;logs[label]=assembly6.sha(log)
        hashes[label]=assembly6.sha(output/'records'/f'{label}.json')
        if metric['accepted']:
            metric['archived_log']=archive(log,logs[label])
        report['phases'].append(metric);save();print(json.dumps(metric),flush=True)
        return metric
    save()
    result=reused['phase'] if reused else check('negative-terminal-upper','src/Tests/WarningTables6/Negative.agda',negative=True)
    if not result or not result['expected_outcome_met']:report['status']='negative-fixture-failed'
    else:
        for group in groups[len(report['completed_groups']):]:
            i=group['index'];prefix=f'src/Tests/WarningTables6/Group{i}'
            if not disk_ok():report['status']='artifact-budget-stopped';break
            if i==9:
                prediction=predict(plan,report)
                atomic_json(output/'upper-prediction.json',prediction)
                report['upper_prediction_sha256']=assembly6.sha(output/'upper-prediction.json');save()
            for j in range(group['parts']):
                result=check(f'group{i}-part{j}',f'{prefix}/Part{j}.agda')
                if not result or not result['expected_outcome_met']:
                    report['status']='part-failed' if result else 'cpu-budget-stopped';break
            else:
                result=check(f'group{i}-bounds',f'{prefix}/Check.agda')
                if result and result['expected_outcome_met']:
                    report['completed_groups'].append(i);report['checked_sample_upper_roots']+=10;save();continue
                report['status']='group-failed' if result else 'cpu-budget-stopped'
            break
        else:
            if disk_ok():
                result=check('warning-all100','src/Tests/WarningTables6/All100.agda',collector=True)
                report['accepted']=bool(result and result['expected_outcome_met'])
                report['status']='complete' if report['accepted'] else 'collector-failed'
            else:report['status']='artifact-budget-stopped'
    if source_identity(donor)!=identity or assembly6.interfaces(donor)!=pool:
        raise ValueError('original checked donor changed')
    all_interfaces=assembly6.interfaces(root)
    totals={}
    for name,digest in all_interfaces.items():
        row=census_with_warnings(root/name,digest)
        for key in ('compressed_bytes','payload_bytes','nodes','node_words','node_array_bytes',
                    'saved_meta_bindings','signature_definitions','string_characters','lazy_text_bytes',
                    'strict_text_bytes','warnings','unsupported_indexed_match_warnings'):
            totals[key]=totals.get(key,0)+row[key]
    report.update(donor_sources_unchanged=True,donor_interfaces_unchanged=True,
        wall_seconds=time.monotonic()-started,final_disk=usage(),interface_pool_totals=totals,
        interfaces=len(all_interfaces))
    atomic_json(output/'phase-records.json',dict(records=records,
        record_hashes=hashes,
        log_hashes=logs,final_interfaces=all_interfaces,generated_source_hashes=report['generated_source_hashes']))
    save();print(json.dumps({key:report[key] for key in ('status','accepted','checked_sample_upper_roots',
        'measured_kernel_cpu_seconds','interfaces')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--pilot',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--expected-generated-sha256',required=True)
    p.add_argument('--resume',type=Path)
    p.add_argument('--prefix-archives',type=Path)
    p.add_argument('--kernel-cpu-budget',type=float,default=1600)
    run(p.parse_args())
