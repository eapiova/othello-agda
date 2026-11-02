#!/usr/bin/env python3
"""Locate and export true extreme initial parts in two native passes per bound.

Only selected rows and their demanded state chunks are retained. All native
results remain untrusted and require safe Agda checking before any proof claim.
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import assembly6
import canonical_census6 as census
from indexed_wire_resume6 import pinned
from initial_lazy_samples6 import EXPECTED
from nat_descendant_resume6 import closed_worker
import native_layout_extrema6 as extrema
from owner_cache_dedup6 import allocated
from provenance import source_identity
from run_job import atomic_json, utc
from wire_workflow6 import require


def run(args):
    current = Path.cwd().resolve()
    previous = args.fixtures_root.resolve()
    actual = pinned(previous / 'results' / (previous.name.removeprefix('six-') + '.json'),
                    args.expected_receipt_sha256)
    require(actual['accepted'] and actual['exit_code'] == 0 and actual['source_unchanged']
            and actual['expected_source_matches'] and actual['stop_reason'] is None
            and source_identity(previous)['source_sha256'] == actual['source_sha256'],
            'accepted unchanged extrema fixtures required')
    service = closed_worker(actual)
    base = previous / 'results/native-extrema-fixtures6'
    tests = pinned(base / 'report.json', args.expected_report_sha256)
    require(tests['accepted'] and tests['first_maximum_indices_checked']
            and tests['fixture_cases'] == 30 and len(tests['native_negative_fixtures']) == 4
            and len(tests['extrema_comparisons']) == 16 and tests['exact_partition_counters']
            and tests['exact_numeric_bodies_and_state_chunks'], 'complete matching extrema validation required')
    build = base / 'sample-pinned'
    built, binary = extrema.checked_build(build)
    require(assembly6.sha(build / 'build.json') == tests['builds']['sample-pinned']['build_sha256']
            and built['line_sha256'] == assembly6.sha(current / 'certificates/six-line.json')
            and built['pins'], 'exact validated line-pinned extrema binary required')
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh native results required')
    out.mkdir(parents=True)
    source = source_identity(current)
    report = dict(format='othello-initial-extrema-samples6-v1', accepted=False, status='preparing',
        source=source, created_utc=utc(), fixture_closed_service=service,
        fixture_receipt_sha256=args.expected_receipt_sha256,
        fixture_report_sha256=args.expected_report_sha256, phases=[],
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='native extrema identification and selected certificates; no kernel premise')

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra):
        used, free = allocated(current.parent), shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free,
                                          reserved_extra_bytes=extra, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'extrema artifact/free-disk gate reached')

    guard(34 * 2**20)
    matching = out / 'matching-tests.json'
    atomic_json(matching, dict(accepted=True, build_sha256=assembly6.sha(build / 'build.json'),
        fixture_report_sha256=args.expected_report_sha256, proof_premise=False))
    for side in ('lower', 'upper'):
        first_counts = None
        selected = [0]
        for mode in ('locate', 'extract'):
            guard(17 * 2**20)
            partial = out / (side + '-' + mode + '.jsonl.partial')
            target = out / (side + '-' + mode + '.jsonl')
            native_report = out / (side + '-' + mode + '-native.json')
            options = extrema.sample.layout.native_options(SimpleNamespace(counts_only=True,
                layout_limit_mib=512, max_entries=200, max_tokens=32000, max_records=200000000,
                inline_limit=256, record_limit=1048576, body_fuel=80))
            options += ['--sample-parts', ','.join(map(str, selected)), '--sample-output', str(partial),
                '--sample-record-cap', '8000000', '--sample-output-limit-mib', '16']
            executed = []

            def native(command, **kwargs):
                command = [command[0], 'layout', *command[2:], *options]
                executed.extend(command)
                return subprocess.run(command, **kwargs)

            report['status'] = side + '-' + mode
            save()
            native_args = SimpleNamespace(build=build, tests=matching, donor=args.native_donor.resolve(),
                output=native_report, max_states=70000000, direction=side, native_cpu=args.native_cpu)
            with contextlib.redirect_stdout(io.StringIO()):
                census.run(native_args, build_validator=extrema.checked_build, execute_native=native)
            data = json.loads(native_report.read_text())
            counts = data['counts']
            phase = dict(direction=side, mode=mode, selected=selected, accepted=False,
                native_report_sha256=assembly6.sha(native_report), command=executed)
            report['phases'].append(phase)
            save()
            require(data['native_complete'] and data['donor_unchanged'] and data['table_unchanged']
                    and counts['wire_complete'] and counts['layout_complete'] and not counts['layout_censored']
                    and all(counts.get(k) == v for k, v in EXPECTED[side].items()),
                    'censored or changed initial layout; partial artifacts retained')
            decoded = extrema.decode_samples(partial)
            require(decoded['complete']['selected'] == selected, 'requested sample selection changed')
            if mode == 'locate':
                first_counts = counts
                selected_next = extrema.extrema(counts)
                phase['next_selected'] = selected_next
            else:
                require(all(counts[k] == v for k, v in first_counts.items()
                            if k.startswith('layout_') and k not in ('layout_peak_bytes', 'layout_total_peak_bytes')),
                        'second pass differs from located partition or extrema')
                require(selected == extrema.extrema(counts), 'extraction missed actual extreme part IDs')
                summary = dict(direction=side, selected=selected, complete=decoded['complete'],
                    samples_sha256=assembly6.sha(partial), sample_bytes=partial.stat().st_size,
                    state_chunks=len(decoded['states']),
                    cases=[dict(part=c['part'], rows=c['rows'], tokens=c['tokens'],
                        body_bytes=len(c['body_text']), dependencies=len(c['dependencies']),
                        references=len(c['references'])) for c in decoded['cases']],
                    native_counts=counts, initial_problem2_proved=False, production_authorized=False,
                    kernel_checks_pending=True)
                atomic_json(out / (side + '-summary.json'), summary)
                phase['summary_sha256'] = assembly6.sha(out / (side + '-summary.json'))
            phase.update(accepted=True, sample_sha256=assembly6.sha(partial), sample_path=str(target))
            partial.rename(target)
            save()
            if mode == 'locate':
                selected = selected_next
    require(source_identity(current) == source and source_identity(previous)['source_sha256'] == actual['source_sha256']
            and extrema.checked_build(build)[0] == built, 'fixture/compiler/frozen source changed')
    report.update(accepted=True, status='complete-untrusted-extrema-samples', finished_utc=utc())
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('fixtures-root', 'native-donor', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('expected-receipt-sha256', 'expected-report-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--native-cpu', type=int, default=1000)
    args = parser.parse_args()
    require(60 <= args.native_cpu <= 2100, 'bounded native phase CPU cap required')
    run(args)


if __name__ == '__main__':
    main()
