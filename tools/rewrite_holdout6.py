#!/usr/bin/env python3
"""Predict the fixed lower holdout, then check it using immutable training.

No censored training or holdout measurements enter the fit. Native statistics
are never proof premises. Every heldout Agda target is cold in a private cache.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import global_assembly6 as assembly
import lower_pilot6 as pilot
from memory_probe6 import rts_stats
from owner_audit6 import audit
from owner_continue6 import nnls, residuals
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, positive, run_job, utc
from rewrite_dedup6 import closed

TRAINING = [6, 7, 8, 9]
HELDOUT = list(range(10, 20))
DIRECTORY = 'src/Tests/RewriteTraining6'


def prediction(training):
    if (training['format'] != 'othello-rewrite-training6-v1' or training['status'] != 'complete' or
            not training['accepted'] or training['completed_indices'] != TRAINING or
            training['training_indices'] != TRAINING or training['heldout_indices'] != HELDOUT or
            training['checked_sample_lower_roots'] != 10 or training['heldout_measured'] or
            not training['donor_unchanged'] or not training['original_donor_unchanged'] or
            not training['generated_sources_unchanged']):
        raise ValueError('requires complete unchanged uncensored training before any holdout')
    declared = training['repairs']+[dict(p, root_index=row['index']) for row in training['rows']
        if row['index'] in TRAINING for p in row['phases']]
    if (len(declared) != len(training['phases']) or
            any(not p['accepted'] or not p['record']['accepted'] or p['record']['stop_reason'] or
                any(p[k] != v for k, v in d.items()) for p, d in zip(training['phases'], declared))):
        raise ValueError('failed, partial or undeclared training cannot fit a gate model')
    models = {}
    for kind, width in (('certificate', 3), ('assembly', 3), ('root', 2)):
        models[kind] = nnls([dict(x=p['x'], cpu_seconds=p['record']['cpu_seconds'])
            for p in training['phases'] if p['kind'] == kind], width)
    rows = [dict(p, root_index=row['index'], predicted_cpu_seconds=sum(c*x for c, x in
        zip(models[p['kind']]['coefficients'], p['x']))) for row in training['rows']
        if row['index'] in HELDOUT for p in row['phases']]
    return dict(format='othello-rewrite-holdout6-prediction-v1', created_utc=utc(),
        estimator='fixed nonnegative least squares; separate certificate, assembly and root models',
        feature_names=dict(certificate=['tokens/1000', 'literal citations/1000', 'intercept'],
            assembly=['literal citations/1000', 'owner sources/100', 'intercept'],
            root=['new parts/100', 'intercept']),
        training_indices=TRAINING, heldout_indices=HELDOUT, models=models, rows=rows,
        heldout_measured_when_fitted=False, predicted_cpu_seconds=sum(p['predicted_cpu_seconds'] for p in rows),
        gate_relative_error=.30, training_layout_sha256=training['layout_sha256'],
        rebind_training_cpu_seconds=sum(p['record']['cpu_seconds'] for p in training['phases'] if p['kind'] == 'rebind'),
        scope='new fixed heldout certificate, binding and root CPU; setup and driver overhead excluded',
        full_population_go=False, production_authorized=False)


def verified_training(args):
    previous = args.previous.resolve()
    proof_audit = audit(previous, args.expected_previous_sha256)
    training = json.loads((previous/'final.json').read_text())
    forecast = prediction(training)
    root = Path(training['check_root'])
    machine = assembly6.machine_identity(args.agda)
    if machine != training['machine']:
        raise ValueError('requires the original compiler on the original checking machine')
    return previous, training, root, source_identity(root), assembly6.interfaces(root), forecast, machine, proof_audit


def fit(args):
    _, _, _, _, _, forecast, _, proof_audit = verified_training(args)
    forecast.update(training_report_sha256=args.expected_previous_sha256, proof_audit=proof_audit)
    atomic_json(args.output, forecast)
    print(json.dumps({k: forecast[k] for k in ('predicted_cpu_seconds', 'heldout_measured_when_fitted')}))


def resume_prefix(training, forecast, report):
    """Require an accepted proper prefix of the original, unrevised holdout."""
    declared = [dict(p, root_index=row['index']) for row in training['rows']
        if row['index'] in HELDOUT for p in row['phases']]
    phases = report['phases']
    if (report['format'] != 'othello-rewrite-heldout6-v1' or report['accepted'] or
            report['status'] not in ('disk-stop', 'cpu-stop') or not phases or
            len(phases) >= len(declared) or not report['heldout_measured'] or
            not report['donor_unchanged'] or not report['generated_sources_unchanged'] or
            report['prospective_prediction'] != forecast or
            any(not p['accepted'] or not p['record']['accepted'] or p['record']['stop_reason'] or
                any(p.get(k) != v for k, v in d.items()) for p, d in zip(phases, declared))):
        raise ValueError('requires an unchanged accepted prefix of the original fixed holdout')
    completed = [row['index'] for row in training['rows'] if row['index'] in HELDOUT and
        all(p['label'] in {q['label'] for q in phases} for p in row['phases'])]
    if (report['completed_indices'] != completed or report['checked_sample_lower_roots'] != 10+len(completed) or
            abs(report['nested_cpu_seconds']-sum(p['record']['cpu_seconds'] for p in phases)) > 1e-6 or
            report['heldout_residual']['relative_error'] is not None or
            report['existing_conditional_parts_rechecked'] != 0):
        raise ValueError('resume completion or timing accounting differs')
    return len(phases)


def run(args):
    previous, training, donor, identity, pool, predicted, machine, proof_audit = verified_training(args)
    if not args.prediction or assembly6.sha(args.prediction) != args.expected_prediction_sha256:
        raise ValueError('requires a pinned forecast before any holdout check')
    forecast = json.loads(args.prediction.read_text())
    if (forecast['training_report_sha256'] != args.expected_previous_sha256 or
            any(forecast[k] != v for k, v in predicted.items() if k != 'created_utc')):
        raise ValueError('prospective forecast differs from the complete training')
    training_pool = dict(pool)
    resumed = None
    if args.resume is not None:
        if not args.expected_resume_sha256:
            raise ValueError('resume requires a pinned final report')
        resume_audit = audit(args.resume.resolve(), args.expected_resume_sha256)
        resumed = json.loads((args.resume/'final.json').read_text())
        resume_prefix(training, forecast, resumed)
        outer = args.resume.resolve().parents[1]
        closed(outer.name.removeprefix('six-'))
        receipt = json.loads((outer/'results'/(outer.name.removeprefix('six-')+'.json')).read_text())
        if (not receipt.get('finished_utc') or not receipt['source_unchanged'] or
                not receipt['expected_source_matches'] or resumed['machine'] != machine or
                resumed['previous_report_sha256'] != args.expected_previous_sha256 or
                resumed['prediction_sha256'] != args.expected_prediction_sha256 or
                resumed['borrowed_interfaces'] != training_pool):
            raise ValueError('resume receipt, compiler or original proof pool differs')
        donor = Path(resumed['check_root'])
        identity, pool = source_identity(donor), assembly6.interfaces(donor)
    output, runs = args.output.resolve(), args.runs_root.resolve()
    required = sum((donor/name).stat().st_size for name in pool)+32*1024**2
    if output.exists() or runs not in output.parents or not pilot.disk_allowed(pilot.disk_usage(runs), required):
        raise ValueError('fresh private root and unchanged storage headroom required')
    output.mkdir(parents=True); root = output/'check'; root.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor/name, root/name)
    for name, digest in pool.items():
        copy_interface(donor/name, root/name, digest)
    manifest = bench6.refresh_manifest(root, origin={k: identity[k] for k in ('revision', 'dirty')})
    report = dict(format='othello-rewrite-heldout6-v1', status='checking', accepted=False,
        created_utc=utc(), previous=str(previous), previous_report_sha256=args.expected_previous_sha256,
        prediction_sha256=args.expected_prediction_sha256, check_root=str(root), machine=machine,
        source_sha256=manifest['source_sha256'], agda_source_sha256=identity['agda_source_sha256'],
        generated_source_hashes=training['generated_source_hashes'], borrowed_interfaces=training_pool,
        borrowed_interfaces_sha256=digest_entries(training_pool), training_audit=proof_audit,
        prospective_prediction=forecast, phases=[], completed_indices=[],
        nested_cpu_seconds=0., nested_cpu_budget=args.kernel_cpu_budget, checked_sample_lower_roots=10,
        heldout_measured=False,
        existing_conditional_parts_rechecked=0, new_certificate_parts_checked=0, postulates=0,
        initial_problem2_proved=False, production_authorized=False)
    if resumed is not None:
        (output/'records').mkdir()
        for phase in resumed['phases']:
            for name in (phase['label']+'.json', phase['archived_log']['archive_name']):
                shutil.copy2(args.resume/'records'/name, output/'records'/name)
        report.update(phases=resumed['phases'].copy(), completed_indices=resumed['completed_indices'].copy(),
            nested_cpu_seconds=resumed['nested_cpu_seconds'],
            checked_sample_lower_roots=resumed['checked_sample_lower_roots'], heldout_measured=True,
            new_certificate_parts_checked=resumed['new_certificate_parts_checked'],
            resumed_from=str(args.resume.resolve()), resumed_report_sha256=args.expected_resume_sha256,
            resume_audit=resume_audit, reused_holdout_phases=len(resumed['phases']),
            resume_initial_interfaces=pool, resume_initial_interfaces_sha256=digest_entries(pool),
            new_nested_cpu_seconds=0.)
    atomic_json(output/'preflight.json', report)
    reused_labels = {p['label'] for p in report['phases']}
    for row in training['rows']:
        if row['index'] not in HELDOUT:
            continue
        complete = True
        for phase in row['phases']:
            if phase['label'] in reused_labels:
                continue
            left = args.kernel_cpu_budget-report['nested_cpu_seconds']
            if left < 10 or not pilot.disk_allowed(pilot.disk_usage(runs), 16*1024**2):
                report['status'] = 'cpu-stop' if left < 10 else 'disk-stop'; complete = False; break
            before = assembly6.interfaces(root)
            suffix = pilot.assert_cold(phase['target'], before, DIRECTORY)
            cap = min(phase['cpu_cap'], left-2)
            record = run_job(phase['label'], [machine['agda_path'], *assembly6.FLAGS, '--save-metas',
                '-v', 'tc.decl:10', '-i', 'src', phase['target'], '+RTS', f'-M{phase["heap_mib"]}M', '-c', '-s', '-RTS'],
                output/'records', root=root, expected_source_sha256=manifest['source_sha256'],
                cpu_limit=cap, timeout=cap*2+30, rss_limit_gib=phase['rss_gib'], log_limit_mib=8,
                metadata=dict(machine=machine, own_target_cold=True, timing_group='heldout',
                    prospective_prediction_sha256=args.expected_prediction_sha256,
                    borrowed_interfaces_sha256=digest_entries(before), existing_conditional_parts_rechecked=0))
            after = assembly6.interfaces(root)
            changes = pilot.cache_changes(before, after)
            own = {name: digest for name, digest in after.items() if name.endswith(suffix)}
            unexpected = [name for name in after if name not in before and name not in own]
            accepted = bool(record['accepted'] and len(own) == 1 and not changes and not unexpected and
                record['source_unchanged'] and record['expected_source_matches'] and
                record['executable_sha256'] == machine['agda_sha256'])
            log = output/'records'/(phase['label']+'.log')
            raw = log.read_text(); digest = assembly6.sha(log)
            packed = archive(log, digest) if accepted else None
            report['phases'].append(dict(phase, root_index=row['index'], accepted=accepted, record=record,
                record_sha256=assembly6.sha(output/'records'/(phase['label']+'.json')),
                cache_changes=changes, unexpected_interfaces=unexpected, own_interfaces=own,
                raw_log_sha256=digest, archived_log=packed, rts=rts_stats(raw),
                declaration_tail=[] if accepted else raw.splitlines()[-30:]))
            report['nested_cpu_seconds'] += record['cpu_seconds']
            if resumed is not None:
                report['new_nested_cpu_seconds'] += record['cpu_seconds']
            report['heldout_measured'] = True
            if accepted and phase['kind'] == 'certificate':
                report['new_certificate_parts_checked'] += 1
            atomic_json(output/'running.json', report)
            if not accepted:
                report['status'] = 'cache-mismatch' if changes or unexpected else 'phase-failed'; complete = False; break
        if not complete:
            break
        if row['index'] not in report['completed_indices']:
            report['completed_indices'].append(row['index']); report['checked_sample_lower_roots'] += 1
        atomic_json(output/'running.json', report)
    report.update(donor_unchanged=source_identity(donor) == identity and assembly6.interfaces(donor) == pool,
        generated_sources_unchanged=all(assembly6.sha(root/name) == digest for name, digest in report['generated_source_hashes'].items()),
        final_interfaces=assembly6.interfaces(root), latest_disk=pilot.disk_usage(runs))
    report['interfaces_sha256'] = digest_entries(report['final_interfaces'])
    report['heldout_residual'] = residuals(forecast, report['phases'])
    report['accepted'] = bool(report['completed_indices'] == HELDOUT and report['donor_unchanged'] and
        report['generated_sources_unchanged'] and pilot.disk_allowed(report['latest_disk']))
    if report['accepted']:
        report['status'] = 'complete'
    atomic_json(output/'final.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'accepted', 'checked_sample_lower_roots',
        'nested_cpu_seconds', 'heldout_residual')}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('predict', 'run'))
    for name in ('previous', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    for name in ('expected-previous-sha256', 'agda'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--prediction', type=Path)
    parser.add_argument('--expected-prediction-sha256')
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--expected-resume-sha256')
    parser.add_argument('--runs-root', type=Path)
    parser.add_argument('--kernel-cpu-budget', type=positive)
    arguments = parser.parse_args()
    if arguments.mode == 'predict':
        fit(arguments)
    else:
        if any(getattr(arguments, k) is None for k in
                ('prediction', 'expected_prediction_sha256', 'runs_root', 'kernel_cpu_budget')):
            parser.error('run requires a pinned prediction, runs root and CPU budget')
        raise SystemExit(0 if run(arguments)['accepted'] else 2)
