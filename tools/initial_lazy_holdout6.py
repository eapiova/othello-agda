#!/usr/bin/env python3
"""Check a prospectively frozen initial-layout holdout without rechecking training.

These are conditional part facts. Neither the forecast nor native data supplies
an Agda premise, a complete initial bound, or production authorization.
"""
import argparse
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
from indexed_wire_resume6 import pinned
from initial_lazy_forecast6 import AGDA, validate_training
from initial_lazy_samples6 import selection
from initial_training_resume6 import (
    argv, cold_target, target_interfaces, validate_cached_sources, validate_pool, validate_receipt,
)
from lazy_sample_parts6 import emit
from nat_descendant_resume6 import closed_worker
from native_layout_samples6 import decode_samples
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def forecast_rows(forecast, side, report_sha):
    require(forecast['format'] == 'othello-initial-lazy-forecast6-v1'
            and not forecast['heldout_measured_when_fitted']
            and not forecast['production_authorized']
            and not forecast['initial_problem2_proved']
            and not forecast['whole_workflow_validated']
            and forecast['training_inputs'][side + '_report'] == report_sha,
            'exact prospective training forecast required')
    rows = forecast['heldout_rows']
    require(len(rows) == 16 and len({(r['direction'], r['part']) for r in rows}) == 16
            and {(r['direction'], r['part']) for r in rows}
            == {(s, i) for s in ('lower', 'upper') for i in selection(s)['held_out']},
            'complete fixed holdout schedule required')
    chosen = [r for r in rows if r['direction'] == side]
    require([r['part'] for r in chosen] == selection(side)['held_out']
            and all(r['predicted_cpu_seconds'] > 0 for r in chosen),
            'changed holdout ordering or prediction')
    return chosen


def samples(decoded, side):
    plan = selection(side)
    require(decoded['complete']['selected'] == plan['selected']
            and [c['part'] for c in decoded['cases']] == plan['selected']
            and all(decoded['complete'][key] == plan['expected']['layout_' + key]
                    for key in ('parts', 'records', 'tokens')),
            'complete exact initial-layout samples required')
    needed = {j for c in decoded['cases'] for j in c['dependencies']}
    require(needed <= decoded['states'].keys(), 'missing demanded state chunk')
    chosen = dict(cases=decoded['cases'], states={j: decoded['states'][j] for j in sorted(needed)})
    rows = {c['part']: dict(part=c['part'], rows=c['rows'], tokens=c['tokens'],
        body_bytes=len(c['body_text']), dependencies=len(c['dependencies']),
        references=len(c['references'])) for c in decoded['cases']}
    return chosen, rows


def residual(rows, phases, prefix):
    expected = [prefix + '.Part' + str(r['part']) for r in rows]
    complete = [p['target'] for p in phases] == expected and all(
        p['record']['accepted'] and p['borrowed_interfaces_unchanged']
        and p['input_samples_unchanged'] for p in phases)
    predicted = sum(r['predicted_cpu_seconds'] for r in rows)
    measured = sum(p['record']['cpu_seconds'] for p in phases)
    error = abs(measured - predicted) / predicted
    return dict(complete=complete, predicted_cpu_seconds=predicted,
        measured_cpu_seconds=measured, relative_error=error,
        within_30_percent=complete and error <= .30)


def run(args):
    current = Path.cwd().resolve()
    previous = args.previous.resolve()
    side = args.side
    folder = ('initial-lower-training-resume6' if side == 'lower' else 'initial-upper-training6')
    base = previous / 'results' / folder
    old = base / 'check'
    outer = source_identity(previous)
    receipt = pinned(previous / 'results' / (previous.name.removeprefix('six-') + '.json'),
                     args.expected_receipt_sha256)
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == 'eapiova' and machine['agda_sha256'] == AGDA
            == args.expected_agda_sha256, 'exact desktop compiler required')
    validate_receipt(receipt, outer, previous, machine['hostname'])
    service = closed_worker(receipt)
    prior = pinned(base / 'report.json', args.expected_report_sha256)
    pool = pinned(base / 'interface-map.json', args.expected_map_sha256)
    source_old = source_identity(old)
    require(prior['checked_source'] == source_old and prior['machine'] == machine
            and digest_entries(pool) == prior['last_interface_pool_sha256'],
            'accepted training source or machine changed')
    validate_pool(pool, assembly6.interfaces(old))
    forecast = pinned(args.forecast, args.expected_forecast_sha256)
    predictions = forecast_rows(forecast, side, args.expected_report_sha256)
    require(forecast['machine'] == machine
            and forecast['source_provenance'][side + '_report'] == source_old,
            'forecast source/machine differs from accepted training')
    sample_path = args.sample.absolute()
    require(not sample_path.is_symlink() and sample_path.is_file()
            and assembly6.sha(sample_path) == args.expected_sample_sha256,
            'exact immutable native sample required')
    chosen, rows = samples(decode_samples(sample_path), side)
    inherited = (forecast['lower_inherited_source']['source_sha256'] if side == 'lower' else None)
    training = validate_training(prior, side, dict(samples_sha256=args.expected_sample_sha256),
                                rows, source_old['source_sha256'], inherited)
    prefix = 'Tests.InitialLazyTraining' + side.title()
    for r in predictions:
        cold_target(pool, prefix + '.Part' + str(r['part']))
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts and previous not in out.parents,
            'fresh isolated holdout root required')
    out.mkdir(parents=True)
    report = dict(format='othello-initial-lazy-holdout6-v1', accepted=False, status='preparing',
        created_utc=utc(), side=side, machine=machine, donor_closed_service=service,
        donor_checked_source=source_old, donor_receipt_sha256=args.expected_receipt_sha256,
        donor_report_sha256=args.expected_report_sha256, donor_map_sha256=args.expected_map_sha256,
        prospective_forecast_sha256=args.expected_forecast_sha256, predictions=predictions,
        training_parts_rechecked=0, reused_training_parts=[m['part'] for m in training],
        phases=[], accepted_parts=0, kernel_cpu_seconds=0., input_samples_sha256=args.expected_sample_sha256,
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='eight independent initial-layout holdout checker facts and conditional links; no initial bound')

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used, free = allocated(current.parent), shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free,
                                          reserved_extra_bytes=extra, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'storage gate reached; accepted training preserved')

    core = [n for n, _ in source_files(current) if n.startswith('src/') or n == 'othello.agda-lib']
    estimate = sum((current / n).stat().st_blocks * 512 for n in core)
    estimate += sum((old / n).stat().st_blocks * 512 for n in pool)
    estimate += sum(len(c['text']) + 4096 for c in chosen['states'].values())
    estimate += sum(len(c['body_text']) + 512 * len(c['dependencies']) + 16384 for c in chosen['cases'])
    guard(estimate + 32 * 2**20)
    check = out / 'check'
    check.mkdir()
    for name in core:
        require((old / name).is_file() and assembly6.sha(old / name) == assembly6.sha(current / name),
                'main safe core changed from accepted training')
        destination = check / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current / name, destination)
    layout = emit(check, chosen, side=side, prefix=prefix)
    old_generated = prior['layouts'][0]['generated_sha256']
    require(all(assembly6.sha(old / n) == h == layout['generated_sha256'].get(n)
                for n, h in old_generated.items()), 'regenerated accepted training source differs')
    validate_cached_sources(old, check, pool)
    copied = set(old_generated) | {n.split('/agda/', 1)[1][:-1] for n in pool}
    for name in sorted(copied):
        shutil.copy2(old / name, check / name)
        require((old / name).stat().st_ino != (check / name).stat().st_ino
                or (old / name).stat().st_dev != (check / name).stat().st_dev, 'source copy is not private')
    for name, digest in pool.items():
        copy_interface(old / name, check / name, digest)
    source = source_identity(check)
    require(assembly6.interfaces(check) == pool, 'private cache copy differs')
    report.update(checked_source=source, layout=layout, last_interface_pool_sha256=digest_entries(pool))
    save()
    atomic_json(out / 'interface-map.json', pool)
    for index, prediction in enumerate(predictions):
        guard(11 * 2**20)
        require(assembly6.sha(sample_path) == args.expected_sample_sha256
                and assembly6.sha(args.forecast) == args.expected_forecast_sha256,
                'immutable sample or forecast changed')
        target = prefix + '.Part' + str(prediction['part'])
        before = assembly6.interfaces(check)
        cold_target(before, target)
        remaining = args.kernel_cpu_limit - report['kernel_cpu_seconds']
        require(remaining > 1, 'holdout CPU cap reached')
        record = run_job('target' + str(index), argv(machine, target), out / 'records', root=check,
            expected_source_sha256=source['source_sha256'], timeout=420, cpu_limit=min(120, remaining),
            rss_limit_gib=1.5, log_limit_mib=2, metadata=dict(target=target, own_target_cold=True,
                prospective_forecast_sha256=args.expected_forecast_sha256, initial_problem2_proved=False))
        after = assembly6.interfaces(check)
        unchanged = all(after.get(n) == h for n, h in before.items())
        sample_unchanged = assembly6.sha(sample_path) == args.expected_sample_sha256
        own = target_interfaces(after, target)
        phase = dict(target=target, record=record, borrowed_interfaces_unchanged=unchanged,
            input_samples_unchanged=sample_unchanged,
            own_interface={n: after[n] for n in own},
            checked_target_source_sha256=assembly6.sha(check / ('src/' + target.replace('.', '/') + '.agda')),
            interfaces_before_sha256=digest_entries(before), interfaces_after_sha256=digest_entries(after))
        report['phases'].append(phase)
        report['kernel_cpu_seconds'] += record['cpu_seconds']
        accepted = record['accepted'] and unchanged and sample_unchanged and len(own) == 1
        report['accepted_parts'] += int(accepted)
        report.update(status='checking' if accepted else 'target-rejected',
            last_interface_pool_sha256=digest_entries(after), heldout_residual=residual(predictions, report['phases'], prefix))
        atomic_json(out / 'interface-map.json', after)
        save()
        require(accepted, 'heldout target rejected; preserve failure: ' + target)
    require(source_identity(previous) == outer and source_identity(old) == source_old
            and assembly6.interfaces(old) == pool and source_identity(check) == source,
            'accepted donor or checked source changed')
    require(assembly6.sha(args.forecast) == args.expected_forecast_sha256
            and assembly6.sha(sample_path) == args.expected_sample_sha256, 'forecast or sample changed')
    report.update(accepted=True, status='complete', finished_utc=utc(), accepted_donor_unchanged=True,
        conditional_sample_links_checked=True)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output', 'sample', 'forecast'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--side', choices=('lower', 'upper'), required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-receipt-sha256',
                 'expected-report-sha256', 'expected-map-sha256',
                 'expected-sample-sha256', 'expected-forecast-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--kernel-cpu-limit', type=float, default=1000)
    args = parser.parse_args()
    require(0 < args.kernel_cpu_limit <= 1200, 'bounded new kernel budget required')
    run(args)


if __name__ == '__main__':
    main()
