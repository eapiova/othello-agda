#!/usr/bin/env python3
"""Conservative gate for the measured per-leaf shared-certificate design.

AI-assisted. This is statistical evidence, never a proof. Cross-leaf savings
observed in a small sample are not extrapolated to a population-wide DAG.
The measured components can reject production; passing them alone cannot
authorize production without the full skeleton and workflow pilot.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

from run_job import atomic_json
from shared_study6 import CS

COLD_SECONDS = 8.851230


def model(training):
    if not training.get('accepted') or not all(p['accepted'] for p in training['parts']):
        raise ValueError('cost calibration requires accepted kernel parts')
    stats = training['stats']
    cpu = sum(p['cpu_seconds'] for p in training['parts'])
    per_entry = max(0, (cpu-COLD_SECONDS-CS*stats['checked_tokens'])/stats['entries'])
    return dict(cold_seconds=COLD_SECONDS, seconds_per_token=CS,
                seconds_per_export_entry=per_entry,
                calibration_cpu_seconds=cpu,
                calibration_tokens=stats['checked_tokens'],
                calibration_entries=stats['entries'],
                limitation='entry coefficient combines state export, shape and import overhead')


def heldout_result(pilot, cost):
    if not pilot.get('accepted') or not pilot.get('assembly', {}).get('accepted'):
        return dict(accepted=False, prediction_gate=False)
    stats = pilot['stats']
    expected = (cost['cold_seconds']+cost['seconds_per_token']*stats['checked_tokens']+
                cost['seconds_per_export_entry']*stats['entries'])
    actual = sum(p['cpu_seconds'] for p in pilot['parts'])
    relative = abs(actual-expected)/expected
    return dict(accepted=True, entries=stats['entries'], checked_tokens=stats['checked_tokens'],
                predicted_cpu_seconds=expected, actual_cpu_seconds=actual,
                relative_prediction_error=relative, prediction_gate=relative <= .30,
                max_part_rss_gib=max(p['peak_rss_gib'] for p in pilot['parts']),
                assembly_cpu_seconds=pilot['assembly']['cpu_seconds'],
                assembly_rss_gib=pilot['assembly']['peak_rss_gib'])


def sample(report, direction, cost):
    if report.get('status') != 'complete':
        raise ValueError('incomplete or censored sharing sample')
    groups = [g for g in report['groups'] if g['direction']==direction and
              g['threshold']==4 and g['frontier_discs']==36]
    if len(groups) != 1:
        raise ValueError('wrong bound or ambiguous sample')
    group=groups[0]; cases=group['cases']; n=len(cases)
    if n < 2 or n != report.get('selected_sample_count'):
        raise ValueError('sample count disagrees with the selected population sample')
    if len({c['state'] for c in cases}) != n:
        raise ValueError('duplicate sampled state')
    prefix_discs = 20 if direction == 'lower' else 22
    for c in cases:
        state = c['state']
        if len(state) != 37 or state[0] not in 'bw' or set(state[1:])-set('012'):
            raise ValueError('invalid sampled state')
        occupied = 36-state.count('0')
        if occupied != prefix_discs and not (occupied < prefix_discs and
                c['unique_nodes']==1 and c['tree_checked_tokens']==1):
            raise ValueError('sample belongs to a different opening frontier')
    population=report['sample_population_L']
    if type(population) is not int or population < n:
        raise ValueError('invalid population')
    kind=report.get('sample_population_kind')
    if kind not in ['canonical frontier full-state classes','distinct raw frontier states']:
        raise ValueError('population kind is required; raw and canonical samples cannot be mixed')
    seconds=[cost['seconds_per_token']*c['checked_tokens']+
             cost['seconds_per_export_entry']*c['entries'] for c in cases]
    token_total=population*statistics.mean(c['checked_tokens'] for c in cases)
    encoded_total=population*statistics.mean(c['layered_encoded_bytes'] for c in cases)
    parts=max(math.ceil(token_total/200000),math.ceil(encoded_total/2**20))
    return dict(direction=direction,opening_frontier_discs=prefix_discs,
                population=population,population_kind=kind,
                sample_size=n,seed=report['sample_seed'],
                nominal_variable_cpu_hours=population*statistics.mean(seconds)/3600,
                nominal_variable_cpu_hours_se=population*statistics.stdev(seconds)/math.sqrt(n)/3600,
                nominal_encoded_gib=encoded_total/2**30,
                nominal_encoded_gib_se=population*statistics.stdev(
                    c['layered_encoded_bytes'] for c in cases)/math.sqrt(n)/2**30,
                nominal_checked_tokens=token_total,estimated_minimum_parts=parts,
                nominal_cold_cpu_hours=parts*cost['cold_seconds']/3600,
                observed_tree_tokens=group['sum_tree_checked_tokens'],
                observed_layered_tokens=group['sum_layered_checked_tokens'],
                observed_cross_certificate_reused_states=group['sharing_between_certificates'],
                observed_canonical_union_reduction=group['canonical_union_reduction'])


def report(lower, upper, training, heldout, throughput):
    if not throughput.get('accepted'):
        raise ValueError('throughput requires accepted kernel batches')
    batches=[b for b in throughput['batches'] if b['slots']==8 and b['accepted']]
    if len(batches)!=1 or batches[0]['effective_slots']<=0:
        raise ValueError('missing controlled eight-slot measurement')
    slots=batches[0]['effective_slots'];cost=model(training)
    samples=[sample(lower,'lower',cost),sample(upper,'upper',cost)]
    if samples[0]['population_kind'] != samples[1]['population_kind']:
        raise ValueError('lower and upper populations use different sampling units')
    variable=sum(s['nominal_variable_cpu_hours'] for s in samples)
    cold=sum(s['nominal_cold_cpu_hours'] for s in samples)
    se=math.sqrt(sum(s['nominal_variable_cpu_hours_se']**2 for s in samples))
    encoded=sum(s['nominal_encoded_gib'] for s in samples)
    wall=1.25*(variable+cold)/slots
    conservative=1.25*(variable+cold+1.96*se)/slots
    failed=[]
    if conservative>168:failed.append('168 desktop wall-hours')
    if encoded>10:failed.append('10 GiB artifact limit, even before interfaces and work roots')
    pilot=heldout_result(heldout,cost)
    if not pilot['prediction_gate']:failed.append('held-out prediction within 30%')
    if pilot.get('max_part_rss_gib',math.inf)>1.5:failed.append('1.5 GiB per kernel part')
    return dict(format='othello-sharing-production-gate6-v1',
                recommendation='NO_GO_CURRENT_REPRESENTATION' if failed else 'NEEDS_FULL_WORKFLOW_PILOT',
                trust='statistical projection and recorded kernel pilots; no initial-board proof',
                production_authorized=False,failed_gates=failed,cost_model=cost,heldout=pilot,
                samples=samples,effective_desktop_slots=slots,
                nominal_component_cpu_hours=variable+cold,
                variable_cpu_hours_standard_error=se,
                nominal_component_wall_hours_with_margin=wall,
                component_wall_hours_plus_1_96se_and_margin=conservative,
                nominal_encoded_gib=encoded,
                gates=dict(wall_hours=168,part_rss_gib=1.5,root_assembly_rss_gib=12,
                           artifacts_gib=10,heldout_error=.30),
                unmeasured=['full skeleton and root lookup footprint','generation and transfer',
                            'full import/dependency scheduling','optimal joint 16–20 strategy line',
                            'final verification and packaging'],
                limitations=['Per-leaf certificate design; a global DAG may behave differently.',
                             'Sample union overlap is not a population-wide reduction factor.',
                             'Nominal encoded data excludes transparent exports, interfaces and work roots.',
                             'SE covers sampling only, not cost-model or throughput uncertainty.',
                             'Eight-slot throughput used a medium shard, not a full production workload.',
                             'Even a passing component estimate cannot authorize production.'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['lower','upper','training','heldout','throughput','output']:
        p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args(); inputs={k:json.loads(getattr(args,k).read_text())
                                for k in ['lower','upper','training','heldout','throughput']}
    result=report(**inputs)
    result['input_sha256']={k:hashlib.sha256(getattr(args,k).read_bytes()).hexdigest() for k in inputs}
    args.output.parent.mkdir(parents=True,exist_ok=True);atomic_json(args.output,result)
    print(json.dumps({k:result[k] for k in ['recommendation','failed_gates',
                     'nominal_component_wall_hours_with_margin','nominal_encoded_gib']}))


if __name__=='__main__':main()
