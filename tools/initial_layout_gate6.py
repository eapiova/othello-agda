#!/usr/bin/env python3
"""Screen full initial native layout costs using an earlier audited model.

Native layout counters and cost projections provide no proof premise. The
earlier model is retrospective, correlated and measured on smaller wire roots.
This diagnostic can reject the current dependency design; it never grants GO.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import assembly6
from run_job import atomic_json, utc
from wire_workflow6 import FEATURES, require

FORMAT = 'othello-initial-layout-gate6-v1'
FIELDS = ('layout_tokens', 'layout_records', 'layout_imported_citations_sum',
          'layout_transitive_entries_sum', 'layout_parts')


def counter(data, key, minimum=0):
    value = data.get(key)
    require(type(value) is int and minimum <= value <= 2**64-1, 'invalid layout ' + key)
    return value


def component(native, direction, model):
    require(native.get('format') == 'othello-wire-layout6-run-v1' and
        native.get('status') == 'complete-untrusted-layout' and
        native.get('root_key') == 'initial' and native.get('counts_only') is True and
        native.get('native_complete') is True and native.get('layout_complete') is True and
        native.get('layout_counts_censored') is False and native.get('exit_code') == 0 and
        native.get('donor_unchanged') is True and native.get('table_unchanged') is True and
        native.get('incomplete_count_extrapolated') is False and
        native.get('initial_problem2_proved') is False and
        native.get('optimal_pair_proved') is False and native.get('production_authorized') is False,
        'complete untrusted initial layout required')
    request, build, c = native.get('request', {}), native.get('build', {}), native.get('counts', {})
    require(request.get('position') == 'initial' and request.get('turn') == 'black' and
        request.get('direction') == direction and request.get('threshold') == 4 and
        request.get('frontier-discs') == 36 and c.get('direction') == direction and
        c.get('threshold') == 4 and c.get('frontier_discs') == 36 and
        build.get('pins') and build.get('line_sha256') and
        build.get('solver_rules_tt_bytes_unchanged') is True,
        'wrong board, bound, line pins or native build scope')
    require(all(c.get(k) is True for k in ('complete', 'root_validated', 'root_holds',
        'wire_complete', 'layout_complete', 'layout_counts_only')) and
        all(c.get(k) is False for k in ('count_overflow', 'oracle_aborted', 'layout_censored')),
        'censored or incomplete native layout')
    values = [counter(c, k, 1) for k in FIELDS]
    records, parts = c['layout_records'], c['layout_parts']
    cap = counter(c, 'layout_max_entries', 1)
    require(cap <= 200 and parts >= (records+cap-1)//cap and
        c.get('wire_records') == records and c.get('wire_tokens') == c['layout_tokens'] and
        c.get('wire_bytes') == c.get('layout_source_wire_bytes'), 'layout count identity differs')
    transitive_parts = counter(c, 'layout_transitive_parts_sum')
    direct = counter(c, 'layout_direct_dependencies_sum')
    require(direct <= transitive_parts <= parts*(parts-1)//2 and
        direct <= c['layout_imported_citations_sum'] and
        c['layout_transitive_entries_sum'] <= records*(parts-1) and
        counter(c, 'layout_assembly_transitive_parts', 1) <= parts and
        counter(c, 'layout_assembly_transitive_entries', 1) <= records and
        counter(c, 'layout_peak_bytes') <= counter(c, 'layout_limit_bytes', 1) <= 512*2**20,
        'invalid dependency closure or layout memory counters')
    coefficients = model.get('coefficients')
    require(model.get('feature_names') == FEATURES and
        type(coefficients) is list and len(coefficients) == 5 and
        all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in coefficients),
        'invalid earlier model')
    costs = [v*k/1000 if j < 4 else v*k for j,(v,k) in enumerate(zip(coefficients,values))]
    return dict(direction=direction, full_line_pinned_counts=True, agda_accepted=False,
        entries=records, tokens=c['layout_tokens'], parts=parts,
        imported_citations=c['layout_imported_citations_sum'],
        direct_dependencies=direct, transitive_entries=c['layout_transitive_entries_sum'],
        transitive_parts=transitive_parts,
        fraction_of_complete_prefix_closure=transitive_parts/(parts*(parts-1)/2) if parts>1 else 0.,
        nominal_feature_cpu_hours={name:cost/3600 for name,cost in zip(FEATURES,costs)},
        nominal_part_cpu_hours=sum(costs)/3600,
        compact_bytes=counter(c, 'layout_compact_bytes', 1),
        wire_bytes_if_emitted=counter(c, 'layout_source_wire_bytes', 1),
        assembly_transitive_entries=c['layout_assembly_transitive_entries'],
        direct_data_only_scenario_entry_upper_count=direct*cap,
        direct_data_only_scenario_is_unimplemented=True,
        whole_assembly_cpu_hours=None, whole_assembly_peak_rss_gib=None)


def evaluate(calibration, natives, driver):
    require(calibration.get('format') == 'othello-wire-workflow6-v1' and
        calibration.get('accepted_pilot_audit') is True and
        calibration.get('production_authorized') is False,
        'earlier audited calibration required')
    require(driver.get('format') == 'othello-unattended-layout6-v1' and
        driver.get('initial_problem2_proved') is False and
        driver.get('optimal_pair_proved') is False and
        driver.get('production_authorized') is False,
        'native measurement driver with no proof or production claim required')
    require(natives and set(natives) <= {'lower','upper'}, 'missing layout direction')
    parts = []
    phase_list = driver.get('phases', [])
    require(type(phase_list) is list and all(type(p) is dict for p in phase_list),
        'invalid driver phase list')
    phases = {p.get('label'):p for p in phase_list}
    require(len(phases) == len(phase_list), 'duplicate driver phase')
    for direction, native in natives.items():
        phase = phases.get('initial-'+direction, {})
        record = phase.get('record', {})
        require(phase.get('accepted') is True and phase.get('layout_complete') is True and
            record.get('accepted') is True and record.get('exit_code') == 0 and
            record.get('stop_reason') is None and record.get('counts_only') is True and
            record.get('proof_premise') is False and record.get('source_unchanged') is True and
            record.get('expected_source_matches') is True,
            'accepted matching native measurement required')
        require(native.get('build', {}).get('line_sha256') == calibration.get('line_sha256'),
            'different optimal-line input')
        parts.append(component(native, direction, calibration['models'][direction]))
    nominal = sum(p['nominal_part_cpu_hours'] for p in parts)
    # A generous hardware-only ceiling, not a measured throughput or schedule.
    optimistic = 1.25*nominal/16
    failed = ['168-hour gate exceeded even at 16 ideal slots in the earlier model'] if optimistic>168 else []
    return dict(format=FORMAT, created_utc=utc(),
        recommendation='NO_GO_CURRENT_WIRE_DEPENDENCIES' if failed else 'NEEDS_INDEPENDENT_FULL_WORKFLOW_PILOT',
        failed_gates=failed, production_authorized=False, initial_problem2_proved=False,
        optimal_pair_proved=False, data_supplies_agda_premise=False,
        components=parts, directions_measured=sorted(natives),
        full_both_bounds_measured=set(natives)=={'lower','upper'},
        nominal_measured_direction_part_cpu_hours=nominal,
        optimistic_nominal_wall_hours_16_slots_with_margin=optimistic,
        hypothetical_parallel_slots=16, production_wall_gate_hours=168,
        part_rss_gate_gib=1.5, production_assembly_rss_gate_gib=12.,
        actual_parallel_schedule_validated=False, whole_assembly_memory_validated=False,
        limits_changed=False, missing_initial_theorem=True,
        excluded_work=['initial assemblies', 'optimal joint play', 'generic cold checks',
            'generation, sources/interfaces/logs, transfer, final verification and packaging'],
        limitations=['Earlier coefficients are retrospective and correlated, not a rigorous runtime bound.',
            'The old model was not validated for millions of imports or this inline-cut design.',
            'The 16-slot value is optimistic; dependency order may forbid that concurrency.',
            'Direct-data-only counts describe a proposed design, not a measured saving or soundness proof.',
            'Compact payload bytes exclude complete source, interface and artifact allocation.'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--calibration', type=Path, required=True)
    p.add_argument('--expected-calibration-sha256', required=True)
    p.add_argument('--driver', type=Path, required=True)
    p.add_argument('--expected-driver-sha256', required=True)
    p.add_argument('--lower', type=Path)
    p.add_argument('--expected-lower-sha256')
    p.add_argument('--upper', type=Path)
    p.add_argument('--expected-upper-sha256')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    paths = {'calibration':args.calibration, 'driver':args.driver}
    for name in ('lower','upper'):
        value = getattr(args,name)
        if value is not None:
            paths[name] = value
    inputs = {}
    for name,path in paths.items():
        expected = getattr(args,'expected_'+name+'_sha256')
        require(expected is not None and assembly6.sha(path)==expected, 'unpinned '+name+' input')
        inputs[name] = json.loads(path.read_text())
    for direction in ('lower','upper'):
        if direction in inputs:
            phase = next(p for p in inputs['driver']['phases'] if p.get('label')=='initial-'+direction)
            require(phase.get('report_sha256') == assembly6.sha(paths[direction]), 'native/driver digest differs')
    report = evaluate(inputs['calibration'], {d:inputs[d] for d in ('lower','upper') if d in inputs}, inputs['driver'])
    report['input_sha256'] = {name:assembly6.sha(path) for name,path in paths.items()}
    atomic_json(args.output,report)
    print(json.dumps({k:report[k] for k in ('recommendation','directions_measured',
        'nominal_measured_direction_part_cpu_hours','optimistic_nominal_wall_hours_16_slots_with_margin')}))


if __name__ == '__main__':
    main()
