#!/usr/bin/env python3
"""Reconcile complete kernel pilots with the current per-frontier resource costs.

This statistical screen may reject a representation. It cannot authorize
production, prove the initial result or extrapolate global DAG sharing.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics

import assembly6
from owner_audit6 import audit
from owner_continue6 import residuals
from rewrite_holdout6 import HELDOUT, prediction
from run_job import atomic_json, utc


def component(data, coefficient, direction):
    cases = data['cases']
    n, population = len(cases), data['source_population']
    if (data['status'] != 'complete' or data['direction'] != direction or data['threshold'] != 4 or
            data['source_population_kind'] != 'canonical frontier full-state classes' or
            n < 2 or n != data['sample_size'] or population < n or
            not data['scalar_replay'] or len({c['state'] for c in cases}) != n or
            coefficient < 0 or not math.isfinite(coefficient)):
        raise ValueError('requires complete uncensored bound data with its declared population')
    tokens = [c['d4_layered_tokens'] for c in cases]
    encoded = [c['compact_bytes'] for c in cases]
    if any(type(x) is not int or x <= 0 for x in tokens+encoded):
        raise ValueError('invalid certificate work or encoded size')
    cpu = population*statistics.mean(tokens)*coefficient/1000/3600
    cpu_se = population*statistics.stdev(tokens)/math.sqrt(n)*coefficient/1000/3600
    size = population*statistics.mean(encoded)/2**30
    size_se = population*statistics.stdev(encoded)/math.sqrt(n)/2**30
    return dict(direction=direction, sample_size=n, population=population,
        source_sample_seed=data['source_sample_seed'], subsample_seed=data['subsample_seed'],
        coefficient_seconds_per_thousand_tokens=coefficient,
        nominal_token_cpu_hours=cpu, sampling_cpu_hours_se=cpu_se,
        nominal_compact_gib=size, sampling_compact_gib_se=size_se,
        observed_sample_global_token_gain=data['stats']['global_token_gain'],
        population_global_sharing_factor_applied=1.)


def evaluate(training, heldout, lower, upper, upper_cost, throughput):
    frozen = heldout['prospective_prediction']
    fitted = prediction(training)
    if any(frozen[k] != v for k, v in fitted.items() if k != 'created_utc'):
        raise ValueError('the heldout forecast was changed or refitted')
    if (heldout['status'] != 'complete' or not heldout['accepted'] or
            heldout['completed_indices'] != HELDOUT or heldout['checked_sample_lower_roots'] != 20 or
            not heldout['donor_unchanged'] or not heldout['generated_sources_unchanged'] or
            heldout['postulates'] != 0 or heldout['existing_conditional_parts_rechecked'] != 0):
        raise ValueError('requires the complete unchanged kernel holdout')
    checked_residual = residuals(frozen, heldout['phases'])
    if not checked_residual['complete'] or checked_residual != heldout['heldout_residual']:
        raise ValueError('partial, failed or mismatched holdout measurement')
    if (not upper_cost['aggregate_within_30_percent'] or upper_cost['heldout_measured_when_fitted'] or
            not throughput['accepted']):
        raise ValueError('upper or throughput pilot is not valid evidence')
    batches = [b for b in throughput['batches'] if b['slots'] == 8 and b['accepted']]
    if len(batches) != 1 or batches[0]['effective_slots'] <= 0:
        raise ValueError('requires the recorded controlled throughput measurement')
    parts = [component(lower, frozen['models']['certificate']['coefficients'][0], 'lower'),
             component(upper, upper_cost['coefficients'][0], 'upper')]
    cpu = sum(p['nominal_token_cpu_hours'] for p in parts)
    size = sum(p['nominal_compact_gib'] for p in parts)
    cpu_se = math.sqrt(sum(p['sampling_cpu_hours_se']**2 for p in parts))
    slots = batches[0]['effective_slots']
    wall = 1.25*cpu/slots
    failed = []
    if wall > 168:
        failed.append('168 desktop wall-hours, already exceeded by the nominal token component')
    if size > 10:
        failed.append('10 GiB artifacts, already exceeded by nominal compact certificate data')
    if not checked_residual['within_30_percent']:
        failed.append('complete lower holdout prediction within 30%')
    certificates = [p for p in heldout['phases'] if p['kind'] == 'certificate']
    bindings = [p for p in heldout['phases'] if p['kind'] != 'certificate']
    part_rss = max(p['record']['peak_rss_gib'] for p in certificates)
    assembly_rss = max(p['record']['peak_rss_gib'] for p in bindings)
    if part_rss > 1.5 or assembly_rss > 3:
        failed.append('unchanged kernel pilot memory caps')
    return dict(format='othello-workflow-resource-screen6-v1', created_utc=utc(),
        trust='native statistics plus audited kernel pilots; no initial-board theorem',
        recommendation='NO_GO_CURRENT_REPRESENTATION' if failed else 'NEEDS_FULL_WORKFLOW_PILOT',
        production_authorized=False, initial_problem2_proved=False, optimal_pair_proved=False,
        postulates=0, checked_sample_lower_roots=20, lower_holdout=checked_residual,
        lower_part_rss_gib=part_rss, lower_binding_rss_gib=assembly_rss,
        components=parts, nominal_token_cpu_hours=cpu, token_cpu_hours_sampling_se=cpu_se,
        nominal_token_wall_hours_with_margin=wall,
        token_wall_hours_plus_1_96se_and_margin=1.25*(cpu+1.96*cpu_se)/slots,
        nominal_compact_gib=size, effective_slots_reference=slots, failed_gates=failed,
        gates=dict(wall_hours=168, part_rss_gib=1.5, pilot_assembly_rss_gib=3,
            production_assembly_rss_gib=12, artifacts_gib=10, heldout_error=.30),
        excluded_work=['fixed part/import/export costs', 'owner/citation assembly',
            'whole root skeleton and optimal joint line', 'generation and transfer',
            'private checking roots, interfaces and logs', 'final verification and packaging'],
        limitations=['Projection describes the current per-frontier certificate design.',
            'Sampled sharing gains are not extrapolated to a population-wide DAG.',
            'Token coefficients omit other nonnegative fitted features, not a rigorous runtime lower bound.',
            'Sampling SE excludes cost-model, encoding, workflow and throughput uncertainty.',
            'The older medium-shard throughput is a reference, not a new full-workflow validation.',
            'A different full-population DAG remains unmeasured and cannot supply a production GO.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('training', 'heldout', 'lower', 'upper', 'upper-cost', 'throughput', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--expected-heldout-sha256', required=True)
    args = parser.parse_args()
    proof_audit = audit(args.heldout.resolve().parent, args.expected_heldout_sha256)
    paths = {key: getattr(args, key) for key in
        ('training', 'heldout', 'lower', 'upper', 'upper_cost', 'throughput')}
    result = evaluate(**{key: json.loads(path.read_text()) for key, path in paths.items()})
    result.update(proof_audit=proof_audit,
        input_sha256={key: assembly6.sha(path) for key, path in paths.items()})
    atomic_json(args.output, result)
    print(json.dumps({key: result[key] for key in ('recommendation', 'failed_gates',
        'nominal_token_wall_hours_with_margin', 'nominal_compact_gib')}))
