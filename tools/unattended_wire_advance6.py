#!/usr/bin/env python3
"""Continue a completed wire pilot with two earlier line roots on the desktop.

The coordinator reserves the whole envelope before launch. This bounded study
does not authorize production, edit a ledger or introduce a proof premise.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import assembly6
import census_pilot6 as census
import census_wire6 as exporter
from owner_cache_dedup6 import allocated
from provenance import source_identity
from run_job import atomic_json, utc
from unattended_wire6 import closed_record
import wire_pilot6 as wire
import wire_cuts6 as cuts


def predecessor(record, report, source_hash, report_hash, expected_report_hash):
    closed_record(record, source_hash)
    if (report_hash != expected_report_hash or report.get('status') != 'complete-pilot' or
            report.get('accepted') is not True or report.get('initial_problem2_proved') is not False or
            [p.get('label') for p in report.get('phases', [])] !=
            ['upper-heldout', 'lower-ply16', 'upper-ply16', 'lower-ply14', 'upper-ply14'] or
            not all(p.get('accepted') is True for p in report['phases'])):
        raise ValueError('exact completed safe pilot required before advancing')


def accepted_advance(record, report, source_hash, report_hash, expected_report_hash):
    closed_record(record, source_hash)
    if (report_hash != expected_report_hash or
            report.get('format') != 'othello-unattended-wire-advance6-v1' or
            report.get('status') != 'complete-earlier-roots' or report.get('accepted') is not True or
            report.get('line_ply') != 12 or report.get('initial_problem2_proved') is not False or
            report.get('production_authorized') is not False or
            [p.get('label') for p in report.get('phases', [])] != ['lower-ply12', 'upper-ply12'] or
            not all(p.get('accepted') is True for p in report['phases'])):
        raise ValueError('both exact accepted ply12 bounds required before the cut pilot')


def run(args):
    output = args.output.resolve()
    if output.exists() or 'results' not in output.parts:
        raise ValueError('fresh isolated results output required')
    output.mkdir(parents=True)
    previous = args.predecessor_root.resolve()
    machine = assembly6.machine_identity(args.agda)
    if machine['hostname'] != args.expected_hostname or machine['agda_sha256'] != args.expected_agda_sha256:
        raise ValueError('exact original desktop/compiler required')
    report = dict(format='othello-unattended-wire-advance6-v1', status='validating-predecessor',
        accepted=False, created_utc=utc(), machine=machine, phases=[], kernel_cpu_seconds=0.,
        kernel_cpu_budget=args.kernel_cpu_budget, line_ply=args.ply,
        initial_problem2_proved=False, production_authorized=False,
        laptop_required_during_execution=False)
    def save(): atomic_json(output/'report.json', report)
    def guard(target=None):
        used = allocated(previous.parent)
        free = shutil.disk_usage(previous.parent).free
        if used >= 10*1024**3 or free < 100*1024**3:
            raise ValueError('desktop storage gate reached; accepted checkpoints preserved')
        report['last_storage_gate'] = dict(allocated_runs_bytes=used, free_bytes=free, checked_utc=utc())
        save()
    save(); guard()
    receipt = previous/'results/wire-unattended-fixed-20261008.json'
    final = previous/'results/unattended-wire6/report.json'
    predecessor(json.loads(receipt.read_text()), json.loads(final.read_text()),
        args.expected_predecessor_source_sha256, assembly6.sha(final), args.expected_predecessor_report_sha256)
    if source_identity(previous)['source_sha256'] != args.expected_predecessor_source_sha256:
        raise ValueError('frozen predecessor source changed')
    bounded = getattr(args, 'inline_limit', None) is not None
    export = cuts if bounded else exporter
    if bounded:
        advance = args.accepted_advance_root.resolve()
        final_advance = advance/'results/wire-advance6/report.json'
        accepted_advance(json.loads((advance/'results/wire-advance-reuse-ply12-20261008.json').read_text()),
            json.loads(final_advance.read_text()), args.expected_advance_source_sha256,
            assembly6.sha(final_advance), args.expected_advance_report_sha256)
        if source_identity(advance)['source_sha256'] != args.expected_advance_source_sha256:
            raise ValueError('accepted advance source changed')
        validation = args.cuts_validation_root.resolve()
        closed_record(json.loads((validation/'results/wire-cuts-validation-20261009.json').read_text()),
            args.expected_cuts_source_sha256)
        if source_identity(validation)['source_sha256'] != args.expected_cuts_source_sha256:
            raise ValueError('cut validation source changed')
        validation_report = validation/'results/wire-cuts6/report.json'
        validated = json.loads(validation_report.read_text())
        if (assembly6.sha(validation_report) != args.expected_cuts_report_sha256 or
                validated.get('accepted') is not True or
                validated.get('pinned_build_sha256') != assembly6.sha(args.native_build/'build.json') or
                validated.get('receipts', {}).get('pinned', {}).get('sha256') != assembly6.sha(args.native_tests)):
            raise ValueError('exact accepted exporter fixtures required')
        report['accepted_advance_report_sha256'] = assembly6.sha(final_advance)
        report['cut_validation_report_sha256'] = assembly6.sha(validation_report)
        report['inline_limit'] = args.inline_limit
    reuse = args.reuse_native_root.resolve() if args.reuse_native_root else None
    if reuse:
        if (not args.expected_reuse_source_sha256 or reuse.parent != previous.parent or
                source_identity(reuse)['source_sha256'] != args.expected_reuse_source_sha256):
            raise ValueError('unchanged same-desktop native-data snapshot required')
        report['reused_native_root'] = str(reuse)
    line = json.loads(Path('certificates/six-line.json').read_text())
    build, _ = export.checked_build(args.native_build)
    if build.get('line_sha256') != assembly6.sha(Path('certificates/six-line.json')) or not build.get('pins'):
        raise ValueError('matching line-pinned native build required')
    report['predecessor_report_sha256'] = assembly6.sha(final)
    report['predecessor_receipt_sha256'] = assembly6.sha(receipt)
    for direction in ('lower', 'upper'):
        label = direction+'-ply'+str(args.ply)
        report['status'] = 'preparing-'+label; save(); guard()
        native_report, data = output/(label+'-native.json'), output/(label+'.wire')
        saved = reuse/'results/wire-advance6'/(label+'-native.json') if reuse else None
        if saved and saved.is_file():
            existing = json.loads(saved.read_text())
            saved_wire = saved.with_name(label+'.wire')
            if (existing.get('wire_complete') is not True or existing.get('native_complete') is not True or
                    existing.get('root_key') != line['states'][args.ply] or
                    existing.get('request', {}).get('direction') != direction or
                    assembly6.sha(saved_wire) != existing.get('wire_output_sha256')):
                raise ValueError('complete matching immutable native artifact required')
            shutil.copy2(saved, native_report); shutil.copy2(saved_wire, data)
            complete = True
        else:
            native = argparse.Namespace(build=args.native_build, tests=args.native_tests,
                donor=args.native_donor, output=native_report, root_key=line['states'][args.ply],
                direction=direction, wire_output=data, wire_limit_mib=8 if bounded else 4,
                max_states=1000000 if bounded else 500000, native_cpu=180)
            if bounded: native.inline_limit = args.inline_limit
            complete = export.run(native)
        phase = dict(label=label, native_complete=complete, native_report=str(native_report),
            native_report_sha256=assembly6.sha(native_report), accepted=False)
        report['phases'].append(phase); save()
        if not complete:
            report['status'] = 'native-censored'; save(); return False
        prepared = output/(label+'-prepared')
        wire.emit(argparse.Namespace(wire=data, report=native_report, output=prepared,
            max_tokens=32000 if bounded else 200000, max_entries=200,
            max_records=100000 if bounded else 50000,
            max_source_bytes=1048576, max_total_source_bytes=8388608 if bounded else 4194304))
        guard()
        report['status'] = 'checking-'+label; save()
        remaining = args.kernel_cpu_budget-report['kernel_cpu_seconds']
        if remaining < 100:
            report['status'] = 'internal-cpu-stop'; save(); return False
        check = argparse.Namespace(prepared=prepared, donor=args.donor, output=output/(label+'-checked'),
            expected_plan_sha256=assembly6.sha(prepared/'plan.json'), agda=args.agda,
            expected_hostname=args.expected_hostname, expected_agda_sha256=args.expected_agda_sha256,
            expected_donor_source_sha256=args.expected_donor_source_sha256,
            expected_generic_interfaces_sha256=args.expected_generic_interfaces_sha256,
            phase='training', training_report=None, forecast=None, expected_forecast_sha256=None,
            kernel_cpu_budget=min(2400., remaining-64), part_cpu_limit=240., assembly_cpu_limit=240.)
        accepted = census.check(check, required_roots=1, expected_format=wire.FORMAT, preflight=guard)
        checked = json.loads((check.output/'report.json').read_text())
        report['kernel_cpu_seconds'] += checked['cpu_seconds']
        phase.update(accepted=accepted, plan_sha256=check.expected_plan_sha256,
            kernel_report=str(check.output/'report.json'),
            kernel_report_sha256=assembly6.sha(check.output/'report.json'),
            kernel_cpu_seconds=checked['cpu_seconds'], checked_targets=len(checked['phases']),
            peak_rss_gib=max((p['record']['peak_rss_gib'] for p in checked['phases']), default=0.))
        save()
        if not accepted:
            report['status'] = 'kernel-check-failed'; save(); return False
        guard()
    report.update(status='complete-earlier-roots', accepted=True, finished_utc=utc()); save()
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('predecessor-root', 'native-build', 'native-tests', 'native-donor', 'donor', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    for name in ('agda', 'expected-hostname', 'expected-agda-sha256', 'expected-predecessor-source-sha256',
                 'expected-predecessor-report-sha256', 'expected-donor-source-sha256',
                 'expected-generic-interfaces-sha256'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--ply', type=int, choices=(10, 12), default=12)
    parser.add_argument('--inline-limit', type=int)
    parser.add_argument('--accepted-advance-root', type=Path)
    parser.add_argument('--cuts-validation-root', type=Path)
    for name in ('expected-advance-source-sha256', 'expected-advance-report-sha256',
                 'expected-cuts-source-sha256', 'expected-cuts-report-sha256'):
        parser.add_argument('--'+name)
    parser.add_argument('--reuse-native-root', type=Path)
    parser.add_argument('--expected-reuse-source-sha256')
    parser.add_argument('--kernel-cpu-budget', type=float, default=4900.)
    args = parser.parse_args()
    if not 180 <= args.kernel_cpu_budget <= 4900: parser.error('invalid reserved queue cap')
    if args.inline_limit is not None:
        if not 1 <= args.inline_limit <= 256: parser.error('invalid cut pilot inline cap')
        if args.ply != 10 or args.reuse_native_root: parser.error('cut pilot is a fresh earlier root')
        if not all((args.accepted_advance_root, args.cuts_validation_root,
                    args.expected_advance_source_sha256, args.expected_advance_report_sha256,
                    args.expected_cuts_source_sha256, args.expected_cuts_report_sha256)):
            parser.error('cut pilot requires exact accepted advance and exporter validation')
    elif args.ply != 12:
        parser.error('earlier roots require the validated bounded-inline exporter')
    try: return 0 if run(args) else 1
    except Exception as error:
        path = args.output.resolve()/'report.json'
        if path.is_file():
            report = json.loads(path.read_text())
            report.update(status='driver-failed', accepted=False, error_type=type(error).__name__,
                error=str(error), finished_utc=utc()); atomic_json(path, report)
        raise


if __name__ == '__main__': raise SystemExit(main())
