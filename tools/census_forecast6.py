#!/usr/bin/env python3
"""Prospective timing model for the fixed eight-root pilot; no production GO."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from owner_continue6 import nnls
from run_job import atomic_json, utc

FORMAT = 'othello-census-pilot6-v1'
FEATURES = dict(part=['tokens/1000', 'entries/150', 'imported citation states/1000', 'intercept'],
                assembly=['transitive entries/1000', 'intercept'])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def features(target):
    names = ('tokens', 'entries', 'imported_citations') if target['kind']=='part' else ('transitive_entries',)
    values = [target[n] for n in names]
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError('invalid frozen features')
    if target['kind']=='part':
        return [values[0]/1000, values[1]/150, values[2]/1000, 1.]
    return [values[0]/1000, 1.]


def prediction(plan, training, plan_hash, training_hash):
    if (plan.get('format') != FORMAT or training.get('format') != FORMAT or
            training.get('phase') != 'training' or not training.get('accepted') or
            training.get('status') != 'complete' or training.get('plan_sha256') != plan_hash or
            not training.get('donor_unchanged') or not training.get('generated_sources_unchanged')):
        raise ValueError('requires accepted immutable training for the frozen plan')
    declared = [t for t in plan['targets'] if t['root_index'] < 4]
    phases = training['phases']
    if (len(phases) != len(declared) or any(p['target'] != t or not p['record']['accepted'] or
            p['record'].get('stop_reason') or p['changed_imports'] or
            not p['record'].get('own_target_cold') or not p['record'].get('source_unchanged') or
            not p['record'].get('expected_source_matches') or
            p['record']['source_sha256'] != training['source_sha256'] or
            p['record']['executable_sha256'] != training['machine']['agda_sha256']
            for p,t in zip(phases, declared))):
        raise ValueError('failed, partial or heldout phases cannot fit training')
    models = {}
    for kind, names in FEATURES.items():
        rows = [dict(x=features(p['target']), cpu_seconds=p['record']['cpu_seconds'])
                for p in phases if p['target']['kind']==kind]
        models[kind] = nnls(rows, len(names))
    predictions, rows = {str(i):0. for i in range(4,8)}, []
    for t in plan['targets']:
        if t['root_index'] < 4: continue
        estimate = sum(c*x for c,x in zip(models[t['kind']]['coefficients'], features(t)))
        if not math.isfinite(estimate) or estimate <= 0:
            raise ValueError('training did not produce a positive phase prediction')
        predictions[str(t['root_index'])] += estimate
        rows.append(dict(target=t, predicted_cpu_seconds=estimate))
    return dict(format='othello-census-pilot6-forecast-v1', created_utc=utc(),
        training_report_sha256=training_hash, plan_sha256=plan_hash,
        root_predictions_cpu_seconds=predictions, rows=rows, models=models,
        feature_names=FEATURES, heldout_measured_when_fitted=False,
        predicted_cpu_seconds=sum(predictions.values()), gate_relative_error=.30,
        scope='conditional descendant roots; nested checker CPU excludes driver/setup; no global assembly extrapolation',
        production_authorized=False, initial_problem2_proved=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True); p.add_argument('--training',type=Path,required=True)
    p.add_argument('--expected-plan-sha256',required=True); p.add_argument('--expected-training-sha256',required=True)
    p.add_argument('--output',type=Path,required=True); args=p.parse_args()
    if sha(args.plan)!=args.expected_plan_sha256 or sha(args.training)!=args.expected_training_sha256:
        raise ValueError('pinned plan or training report changed')
    report=prediction(json.loads(args.plan.read_text()),json.loads(args.training.read_text()),
                      args.expected_plan_sha256,args.expected_training_sha256)
    args.output.parent.mkdir(parents=True,exist_ok=True); atomic_json(args.output,report)
    print(json.dumps(dict(predicted_cpu_seconds=report['predicted_cpu_seconds'],heldout_measured=False)))


if __name__=='__main__': main()
