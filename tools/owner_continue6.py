#!/usr/bin/env python3
"""Prospectively predict, then check the fixed lower timing holdout.

Training and proof donors stay immutable. Each heldout target is cold in a
private cache; all imported Agda facts retain their exact hashes. No native
measurement is a proof premise. Run under one coordinator kernel reservation.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import global_assembly6 as assembly
import lower_pilot6 as pilot
from memory_probe6 import rts_stats
import owner_lower6 as owner
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, positive, run_job, utc
from warning_cost6 import solve


def nnls(rows, width):
    if not rows or any(len(r['x'])!=width or
            not math.isfinite(r['cpu_seconds']) or r['cpu_seconds']<0 or
            any(not math.isfinite(x) or x<0 for x in r['x']) for r in rows):
        raise ValueError('requires finite nonnegative measurements and fixed features')
    best = (sum(r['cpu_seconds']**2 for r in rows), [0.0]*width)
    for n in range(1,width+1):
        for active in itertools.combinations(range(width),n):
            a = [[sum(r['x'][i]*r['x'][j] for r in rows) for j in active] for i in active]
            b = [sum(r['x'][i]*r['cpu_seconds'] for r in rows) for i in active]
            fitted = solve(a,b)
            if fitted is None or any(not math.isfinite(v) or v < -1e-9 for v in fitted):
                continue
            coefficients = [0.0]*width
            for i,v in zip(active,fitted):
                coefficients[i] = max(0.0,v)
            error = sum((sum(c*x for c,x in zip(coefficients,r['x']))-r['cpu_seconds'])**2 for r in rows)
            if error < best[0]:
                best = (error,coefficients)
    return dict(coefficients=best[1],training_squared_error=best[0],training_phases=len(rows))


def prediction(preflight, training):
    if (training['format']!='othello-owner-lower6-training-v1' or
            training['status']!='complete' or not training['accepted'] or
            training['completed_indices']!=owner.TRAINING or training['heldout_measured'] or
            not training['donors_unchanged'] or not training['generated_sources_unchanged'] or
            training['generated_sha256']!=preflight['generated_sha256'] or
            training['rows']!=preflight['rows']):
        raise ValueError('complete unchanged training is required before timing any holdout')
    declared = [p for row in preflight['rows'] if row['index'] in owner.TRAINING for p in row['phases']]
    measured = training['phases']
    if ([p['label'] for p in measured]!=[p['label'] for p in declared] or
            any(not p['accepted'] or not p['record']['accepted'] or p['record']['stop_reason'] or
                p['x']!=d['x'] or p['kind']!=d['kind'] for p,d in zip(measured,declared))):
        raise ValueError('failed, partial or heldout timings cannot be training evidence')
    models = {}
    for kind,width in (('certificate',3),('assembly',3),('root',2)):
        rows = [dict(x=p['x'],cpu_seconds=p['record']['cpu_seconds']) for p in measured if p['kind']==kind]
        models[kind] = nnls(rows,width)
    predicted = []
    for row in preflight['rows']:
        if row['index'] not in owner.HELDOUT:
            continue
        for phase in row['phases']:
            fitted = models[phase['kind']]['coefficients']
            predicted.append(dict(phase,root_index=row['index'],
                                  predicted_cpu_seconds=sum(c*x for c,x in zip(fitted,phase['x']))))
    return dict(format='othello-owner-lower6-prospective-v1',created_utc=utc(),
        estimator='fixed nonnegative least squares, separate certificate/assembly/root models',
        feature_names=dict(certificate=['tokens/1000','literal citation states/1000','intercept'],
                           assembly=['literal citation states/1000','owner sources/100','intercept'],
                           root=['new parts/100','intercept']),
        training_indices=owner.TRAINING,heldout_indices=owner.HELDOUT,
        models=models,rows=predicted,heldout_measured_when_fitted=False,
        predicted_cpu_seconds=sum(p['predicted_cpu_seconds'] for p in predicted),
        gate_relative_error=.30,
        scope='new heldout certificate and citation assembly CPU after immutable checked-export reuse; outer driver overhead excluded',
        full_population_go=False,production_authorized=False)


def fit(args):
    preflight = json.loads(args.preflight.read_text())
    training = json.loads((args.previous/'final.json').read_text())
    report = prediction(preflight,training)
    report.update(preflight_sha256=assembly6.sha(args.preflight),
                  training_report_sha256=assembly6.sha(args.previous/'final.json'))
    atomic_json(args.output,report)
    print(json.dumps({k:report[k] for k in ('predicted_cpu_seconds','heldout_measured_when_fitted')}))


def residuals(predicted, phases):
    expected = {p['label']:p for p in predicted['rows']}
    if len(expected)!=len(predicted['rows']) or len({p['label'] for p in phases})!=len(phases):
        raise ValueError('duplicate forecast or measurement label')
    if any(p['label'] not in expected for p in phases):
        raise ValueError('measurement is outside the fixed holdout')
    complete = len(phases)==len(expected) and all(p['accepted'] for p in phases)
    actual = sum(p['record']['cpu_seconds'] for p in phases)
    estimate = predicted['predicted_cpu_seconds']
    error = ((actual-estimate)/estimate if complete and estimate>0 else None)
    return dict(complete=complete,measured_cpu_seconds=actual,predicted_cpu_seconds=estimate,
                relative_error=error,within_30_percent=bool(error is not None and abs(error)<=.30),
                failures_and_missing_checks_censored=True,production_authorized=False)


def run(args):
    previous = args.previous.resolve()
    if (assembly6.sha(previous/'final.json')!=args.expected_previous_sha256 or
            assembly6.sha(args.prediction)!=args.expected_prediction_sha256):
        raise ValueError('training or prospective forecast identity differs')
    training = json.loads((previous/'final.json').read_text())
    preflight = json.loads(args.preflight.read_text())
    forecast = json.loads(args.prediction.read_text())
    recomputed = prediction(preflight,training)
    for k in recomputed:
        if k!='created_utc' and forecast[k]!=recomputed[k]:
            raise ValueError('prospective model differs: '+k)
    if (forecast['training_report_sha256']!=args.expected_previous_sha256 or
            forecast['preflight_sha256']!=assembly6.sha(args.preflight)):
        raise ValueError('forecast provenance differs')
    donor = Path(training['check_root'])
    origin,pool = source_identity(donor),assembly6.interfaces(donor)
    machine = assembly6.machine_identity(args.agda)
    if (origin['source_sha256']!=training['source_sha256'] or pool!=training['final_interfaces'] or
            machine!=training['machine'] or not all(assembly6.sha(donor/name)==digest
            for name,digest in training['source_hashes'].items())):
        raise ValueError('training proof donor or compiler changed')
    output,runs = args.output.resolve(),args.runs_root.resolve()
    required = sum((donor/name).stat().st_size for name in pool)+32*1024**2
    if output.exists() or runs not in output.parents or not pilot.disk_allowed(pilot.disk_usage(runs),required):
        raise ValueError('fresh root and unchanged disk headroom required')
    output.mkdir(parents=True)
    root=output/'check';root.mkdir()
    for name,_ in source_files(donor):
        assembly.hardlink(donor/name,root/name)
    manifest = bench6.refresh_manifest(root,origin={k:origin[k] for k in ('revision','dirty')})
    for name,digest in pool.items():
        copy_interface(donor/name,root/name,digest)
    report=dict(format='othello-owner-lower6-heldout-v1',status='checking',accepted=False,
        created_utc=utc(),check_root=str(root),machine=machine,
        source_sha256=manifest['source_sha256'],agda_source_sha256=origin['agda_source_sha256'],
        previous=str(previous),previous_report_sha256=args.expected_previous_sha256,
        prediction_sha256=args.expected_prediction_sha256,preflight_sha256=assembly6.sha(args.preflight),
        generated_source_hashes=training['source_hashes'],borrowed_interfaces_sha256=digest_entries(pool),
        borrowed_interfaces=pool,phases=[],completed_indices=[],nested_cpu_seconds=0.0,
        nested_cpu_budget=args.kernel_cpu_budget,checked_sample_lower_roots=10,
        certificate_parts_rechecked=0,postulates=0,initial_problem2_proved=False,
        production_authorized=False,prospective_prediction=forecast)
    atomic_json(output/'running.json',report)
    for row in preflight['rows']:
        if row['index'] not in owner.HELDOUT:
            continue
        complete=True
        for phase in row['phases']:
            left=args.kernel_cpu_budget-report['nested_cpu_seconds']
            if left<10 or not pilot.disk_allowed(pilot.disk_usage(runs),16*1024**2):
                report['status']='cpu-stop' if left<10 else 'disk-stop';complete=False;break
            before=assembly6.interfaces(root)
            suffix=pilot.assert_cold(phase['target'],before,owner.DIRECTORY)
            cap=min(phase['cpu_cap'],left-2)
            record=run_job(phase['label'],[machine['agda_path'],*assembly6.FLAGS,'--save-metas',
                '-v','tc.decl:10','-i','src',phase['target'],'+RTS',f'-M{phase["heap_mib"]}M',
                '-c','-s','-RTS'],output/'records',root=root,
                expected_source_sha256=manifest['source_sha256'],cpu_limit=cap,timeout=cap*2+30,
                rss_limit_gib=phase['rss_gib'],log_limit_mib=8,
                metadata=dict(machine=machine,own_target_cold=True,timing_group='heldout',
                    checker_kind=phase['kind'],prospective_prediction_sha256=args.expected_prediction_sha256,
                    borrowed_interfaces_sha256=digest_entries(before),certificate_parts_rechecked=0))
            after=assembly6.interfaces(root);changes=pilot.cache_changes(before,after)
            own={name:d for name,d in after.items() if name.endswith(suffix)}
            unexpected=[name for name in after if name not in before and name not in own]
            accepted=bool(record['accepted'] and len(own)==1 and not changes and not unexpected and
                record['source_unchanged'] and record['expected_source_matches'] and
                record['executable_sha256']==machine['agda_sha256'])
            log=output/'records'/(phase['label']+'.log');log_sha=assembly6.sha(log)
            stats=rts_stats(log.read_text());packed=archive(log,log_sha) if accepted else None
            report['phases'].append(dict(phase,accepted=accepted,record=record,
                record_sha256=assembly6.sha(output/'records'/(phase['label']+'.json')),
                cache_changes=changes,unexpected_interfaces=unexpected,own_interfaces=own,
                raw_log_sha256=log_sha,archived_log=packed,rts=stats))
            report['nested_cpu_seconds']+=record['cpu_seconds']
            atomic_json(output/'running.json',report)
            if not accepted:
                report['status']='cache-mismatch' if changes or unexpected else 'phase-failed'
                complete=False;break
        if not complete:break
        report['completed_indices'].append(row['index']);report['checked_sample_lower_roots']+=1
        atomic_json(output/'running.json',report)
    report['donor_unchanged']=source_identity(donor)==origin and assembly6.interfaces(donor)==pool
    report['generated_sources_unchanged']=all(assembly6.sha(root/name)==digest
        for name,digest in training['source_hashes'].items())
    report['final_interfaces']=assembly6.interfaces(root)
    report['interfaces_sha256']=digest_entries(report['final_interfaces'])
    report['latest_disk']=pilot.disk_usage(runs)
    report['heldout_residual']=residuals(forecast,report['phases'])
    report['accepted']=bool(report['completed_indices']==owner.HELDOUT and report['donor_unchanged'] and
        report['generated_sources_unchanged'] and pilot.disk_allowed(report['latest_disk']))
    if report['accepted']:report['status']='complete'
    atomic_json(output/'final.json',report)
    print(json.dumps({k:report[k] for k in ('status','accepted','completed_indices',
        'checked_sample_lower_roots','nested_cpu_seconds','heldout_residual')}))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('predict','run'))
    for name in ('previous','preflight','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--prediction',type=Path)
    p.add_argument('--expected-previous-sha256')
    p.add_argument('--expected-prediction-sha256')
    p.add_argument('--runs-root',type=Path)
    p.add_argument('--agda')
    p.add_argument('--kernel-cpu-budget',type=positive)
    args=p.parse_args()
    if args.mode=='predict':fit(args)
    else:
        if any(getattr(args,k) is None for k in ('prediction','expected_previous_sha256',
            'expected_prediction_sha256','runs_root','agda','kernel_cpu_budget')):
            p.error('run requires a pinned prediction, previous report, runs root, Agda and CPU budget')
        raise SystemExit(0 if run(args)['accepted'] else 2)
