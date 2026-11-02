#!/usr/bin/env python3
"""Extract fixed initial-layout samples without retaining the native graph.

This is a bounded feasibility job, not production. Exact accepted native
fixtures and the immutable old TT are authenticated. Every selected row still
needs safe Agda checking and eventual initial-board assembly.
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import random
import shutil
from types import SimpleNamespace

import assembly6
import canonical_census6 as census
from indexed_wire_resume6 import pinned
from nat_descendant_resume6 import closed_worker
import native_layout_samples6 as sample
from owner_cache_dedup6 import allocated
from provenance import source_identity
from run_job import atomic_json, utc
from wire_workflow6 import require
import wire_layout6 as layout


EXPECTED = {
    'lower': dict(layout_parts=34366, layout_records=6873047, layout_tokens=88689949,
        layout_compact_bytes=250608935, unique_dag_nodes=67468513),
    'upper': dict(layout_parts=34932, layout_records=6986325, layout_tokens=87903624,
        layout_compact_bytes=250691484, unique_dag_nodes=66936456),
}


def selection(side):
    """Fixed stratified discovery sample, including first and initial root part."""
    require(side in EXPECTED, 'lower or upper required')
    count = EXPECTED[side]['layout_parts']
    rng = random.Random(2026101201 + (side == 'upper'))
    selected = [0]
    for k in range(14):
        lo = 1 + k * (count - 2) // 14
        hi = 1 + (k + 1) * (count - 2) // 14
        selected.append(rng.randrange(lo, hi))
    selected.append(count - 1)
    require(len(set(selected)) == 16 and selected == sorted(selected), 'sample partition invalid')
    return dict(selected=selected, training=selected[::2], held_out=selected[1::2],
        seed=2026101201 + (side == 'upper'), expected=EXPECTED[side],
        cost_forecast_frozen=False, held_out_kernel_checks_started=False)


def run(args):
    current = Path.cwd().resolve()
    previous = args.fixtures_root.resolve()
    label = previous.name.removeprefix('six-')
    actual = pinned(previous / 'results' / (label + '.json'), args.expected_receipt_sha256)
    require(actual['accepted'] and actual['exit_code'] == 0 and actual['stop_reason'] is None
            and actual['source_unchanged'] and actual['expected_source_matches']
            and actual['source_sha256'] == source_identity(previous)['source_sha256'],
            'accepted unchanged native fixtures required')
    service = closed_worker(actual)
    base = previous / 'results/native-layout-sample-fixtures6'
    tests = pinned(base / 'report.json', args.expected_report_sha256)
    require(tests['accepted'] and tests['fixture_cases'] == 30
            and len(tests['native_negative_fixtures']) == 4
            and tests['exact_partition_counters'] and tests['exact_numeric_bodies_and_state_chunks']
            and not tests['initial_problem2_proved'] and not tests['production_authorized'],
            'matching complete sampler/scalar validation required')
    build = base / 'sample-pinned'
    built, binary = sample.checked_build(build)
    require(assembly6.sha(build / 'build.json') == tests['builds']['sample-pinned']['build_sha256']
            and built['pins'] and built['line_sha256'] == assembly6.sha(current / 'certificates/six-line.json'),
            'validated exact pinned sampler required')
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh isolated output required')
    out.mkdir(parents=True)
    source = source_identity(current)
    report = dict(format='othello-initial-lazy-samples6-v1', accepted=False, status='preparing',
        created_utc=utc(), source=source, fixture_closed_service=service,
        fixture_receipt_sha256=args.expected_receipt_sha256, fixture_report_sha256=args.expected_report_sha256,
        pinned_build_sha256=assembly6.sha(build / 'build.json'), phases=[],
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='fixed real initial-layout native samples; no Agda premise or complete proof',
        native_cpu_cap_per_bound=args.native_cpu, sample_output_cap_per_bound_mib=16)

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used = allocated(current.parent)
        free = shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'storage gate reached; no graph or accepted proof deleted')

    plan = {side: selection(side) for side in ('lower', 'upper')}
    atomic_json(out / 'plan.json', dict(format='othello-initial-lazy-sample-selection6-v1',
        created_utc=utc(), sides=plan, initial_problem2_proved=False, production_authorized=False))
    guard(34 * 2**20)
    matching_tests = out / 'matching-native-tests.json'
    atomic_json(matching_tests, dict(accepted=True, build_sha256=assembly6.sha(build / 'build.json'),
        native_fixture_report_sha256=args.expected_report_sha256, fixture_cases=30,
        native_negative_fixtures=4, proof_premise=False))
    for direction in ('lower', 'upper'):
        guard(17 * 2**20)
        target = out / (direction + '.samples.jsonl')
        partial = target.with_name(target.name + '.partial')
        native_report = out / (direction + '-native.json')
        options = layout.native_options(SimpleNamespace(counts_only=True, layout_limit_mib=512,
            max_entries=200, max_tokens=32000, max_records=200000000, inline_limit=256,
            record_limit=1048576, body_fuel=80))
        options += ['--sample-parts', ','.join(map(str, plan[direction]['selected'])),
            '--sample-output', str(partial), '--sample-record-cap', '8000000',
            '--sample-output-limit-mib', '16']
        executed = []

        def native(command, **kwargs):
            import subprocess
            command = [command[0], 'layout', *command[2:], *options]
            executed.extend(command)
            return subprocess.run(command, **kwargs)

        report['status'] = 'sampling-' + direction
        save()
        args_native = SimpleNamespace(build=build, tests=matching_tests, donor=args.native_donor.resolve(),
            output=native_report, max_states=70000000, direction=direction, native_cpu=args.native_cpu)
        with contextlib.redirect_stdout(io.StringIO()):
            census.run(args_native, build_validator=sample.checked_build, execute_native=native)
        data = json.loads(native_report.read_text())
        counts = data['counts']
        complete = bool(data['native_complete'] and data['donor_unchanged'] and data['table_unchanged']
            and counts.get('layout_complete') and not counts.get('layout_censored')
            and counts.get('wire_complete') and partial.is_file())
        report['phases'].append(dict(direction=direction, accepted=False, native_report_sha256=assembly6.sha(native_report),
            command=executed, complete=complete, partial_path=str(partial)))
        save()
        require(complete, 'native initial sample stopped; partial evidence retained')
        require(all(counts.get(k) == v for k, v in EXPECTED[direction].items()),
                'new native partition differs from the complete prior pinned layout')
        decoded = sample.decode_samples(partial)
        require(decoded['complete']['selected'] == plan[direction]['selected'], 'sample selection changed')
        summary = dict(direction=direction, source_sha256=source['source_sha256'],
            samples_sha256=assembly6.sha(partial), sample_bytes=partial.stat().st_size,
            state_chunks=len(decoded['states']), state_rows=sum(c['rows'] for c in decoded['states'].values()),
            cases=[dict(part=c['part'], rows=c['rows'], tokens=c['tokens'], body_bytes=len(c['body_text']),
                dependencies=len(c['dependencies']), references=len(c['references'])) for c in decoded['cases']],
            complete=decoded['complete'], native_complete=True, independent_kernel_checks_pending=True,
            initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False)
        atomic_json(out / (direction + '-summary.json'), summary)
        partial.rename(target)
        report['phases'][-1].update(accepted=True, sample_path=str(target),
            sample_sha256=summary['samples_sha256'], summary_sha256=assembly6.sha(out / (direction + '-summary.json')))
        save()
    require(source_identity(current) == source, 'frozen coordinator source changed')
    require(source_identity(previous)['source_sha256'] == actual['source_sha256']
            and sample.checked_build(build)[0] == built, 'accepted fixtures or binary changed')
    report.update(accepted=True, status='complete-untrusted-initial-samples', finished_utc=utc(),
        fixture_source_unchanged=True, checked_rows_or_initial_proof=False)
    save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('fixtures-root', 'native-donor', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('expected-receipt-sha256', 'expected-report-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--native-cpu', type=int, choices=range(60, 2101), default=2100)
    run(parser.parse_args())
