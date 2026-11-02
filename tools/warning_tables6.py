#!/usr/bin/env python3
"""Measure only Agda's IndexedMatch warning filter on unchanged certificates.

The filter concerns optional cubical transports. Ordinary safe equality proofs,
all certificate data, checker calls, rules and heap caps are preserved. Never
edit an interface or a core source to remove a warning.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface
import compact_shared6 as compact
import global_assembly6 as assembly
from interface_census6 import census_file,decompress,warning_fields
from memory_probe6 import rts_stats
from provenance import digest_entries,source_files,source_identity
from run_job import atomic_json,run_job

OLD='Tests.PackedTables6'
NEW='Tests.WarningTables6'
WARNING='-WnoUnsupportedIndexedMatch'


def warning_source(original):
    options='--save-metas --safe --without-K --cubical-compatible'
    if original.count(assembly.COMMON)!=1 or options not in original or WARNING in original:
        raise ValueError('different packed proof template')
    changed=original.replace(options,options+' '+WARNING,1).replace(OLD,NEW)
    if '/Part' in original or '  entries :' in original:
        before=original.split('  entries :',1)[1].split('  shape :',1)[0]
        after=changed.split('  entries :',1)[1].split('  shape :',1)[0]
        if before!=after or '  accepted = refl {x = true}' not in changed or '  shape = refl {x = states}' not in changed:
            raise ValueError('certificate or equality witness changed')
    return changed


def guarantee_source(part1):
    match=re.search(r'states = shardStates keyed6 \(fromMaybe \[\] \(decodeCompactEntries "([^"]+)"\)\)',part1)
    if not match or len(match[1])<14:raise ValueError('missing exported state list')
    state=compact.unpack_state(match[1][:13])
    text=assembly.assembly_source([state],{state:1},'upper')
    text=text.replace(assembly.PREFIX,OLD+'.Group0')
    text=text.replace('module '+OLD+'.Group0.Check where','module '+OLD+'.Guarantee where')
    text=text.replace('--safe ','--save-metas --safe ',1)
    return warning_source(text)


def census_with_warnings(path,digest):
    result=census_file(path,digest)
    result.update(warning_fields(decompress(path.read_bytes())))
    return result


def run(args):
    previous=args.previous.resolve()
    final=json.loads((previous/'packed.json').read_text())
    audit=json.loads((previous/'phase-records.json').read_text())
    donor=Path(final['resumed_from'])/'check';pool=audit['final_interfaces']
    identity=source_identity(donor);machine=assembly6.machine_identity(args.agda)
    if (final['status']!='collector-failed' or final['accepted'] or
            final['completed_groups']!=list(range(10)) or final['checked_sample_upper_roots']!=100 or
            identity['source_sha256']!=final['source_sha256'] or assembly6.interfaces(donor)!=pool or
            len(pool)!=305 or machine!=final['machine']):
        raise ValueError('requires the unchanged completed packed sample and original binary')
    originals={i:(donor/f'src/Tests/PackedTables6/Group0/Part{i}.agda').read_text() for i in (0,1)}
    sources={f'src/Tests/WarningTables6/Group0/Part{i}.agda':warning_source(text) for i,text in originals.items()}
    sources['src/Tests/WarningTables6/Guarantee.agda']=guarantee_source(originals[1])
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    root=output/'check';root.mkdir()
    for name,_ in source_files(donor):assembly.hardlink(donor/name,root/name)
    for name,text in sources.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    manifest=bench6.refresh_manifest(root,origin={k:identity[k] for k in ('revision','dirty')})
    generic={name:digest for name,digest in pool.items() if '/Tests/PackedTables6/' not in name}
    if len(generic)!=32:raise ValueError('wrong generic pool')
    for name,digest in generic.items():copy_interface(donor/name,root/name,digest)
    report=dict(format='othello-warning-tables6-v1',status='running',accepted=False,
        source_sha256=manifest['source_sha256'],machine=machine,phases=[],
        original_source_sha256=identity['source_sha256'],initial_problem2_proved=False,
        production_authorized=False,warning_filter=WARNING,
        generated_source_hashes={name:assembly6.sha(root/name) for name in sources},
        baseline={str(i):census_with_warnings(donor/f'_build/2.9.0/agda/src/Tests/PackedTables6/Group0/Part{i}.agdai',
            pool[f'_build/2.9.0/agda/src/Tests/PackedTables6/Group0/Part{i}.agdai']) for i in (0,1)})
    records={};spent=0.0
    for label,target in [('part0','src/Tests/WarningTables6/Group0/Part0.agda'),
                         ('part1','src/Tests/WarningTables6/Group0/Part1.agda'),
                         ('guarantee','src/Tests/WarningTables6/Guarantee.agda')]:
        before=assembly6.interfaces(root)
        suffix='/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'
        if any(name.endswith(suffix) for name in before):raise ValueError('own target not cold')
        # A command-line warning mode applies to dependencies too and changes
        # their interface compatibility. The new module's own OPTIONS pragma
        # filters only its repeated warnings; borrowed core caches stay fixed.
        record=run_job(label,[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
            '+RTS','-M1350M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=min(90,args.kernel_cpu_budget-spent),
            timeout=270,rss_limit_gib=1.5,log_limit_mib=2,
            metadata={'machine':machine,'own_target_cold':True,
                      'interface_isolation':'private copies, one serial cache',
                      'borrowed_interfaces_sha256':digest_entries(before)})
        spent+=record['cpu_seconds'];after=assembly6.interfaces(root)
        changes=[name for name,digest in before.items() if after.get(name)!=digest]
        metric=assembly.metrics(record)
        metric.update(label=label,target=target,exit_code=record['exit_code'],cache_changes=changes,
                      rts=rts_stats((output/'records'/f'{label}.log').read_text()))
        if changes:metric['accepted']=False
        if record['accepted'] and not changes:
            own=[name for name in after if name.endswith(suffix)]
            if len(own)!=1:raise ValueError('missing accepted interface')
            metric['interface']=census_with_warnings(root/own[0],after[own[0]])
        records[label]=record;report['phases'].append(metric);report['measured_kernel_cpu_seconds']=spent
        atomic_json(output/'warning.json',report);print(json.dumps(metric),flush=True)
        if not metric['accepted']:report['status']='phase-failed';break
    else:report['status']='complete';report['accepted']=True
    if source_identity(donor)!=identity or assembly6.interfaces(donor)!=pool:
        raise ValueError('original proof donor changed')
    report.update(donor_sources_unchanged=True,donor_interfaces_unchanged=True)
    atomic_json(output/'phase-records.json',dict(records=records,
        record_hashes={name:assembly6.sha(output/'records'/f'{name}.json') for name in records},
        log_hashes={name:assembly6.sha(output/'records'/f'{name}.log') for name in records},
        final_interfaces=assembly6.interfaces(root),generated_source_hashes=report['generated_source_hashes']))
    atomic_json(output/'warning.json',report)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--kernel-cpu-budget',type=float,default=150)
    run(p.parse_args())
