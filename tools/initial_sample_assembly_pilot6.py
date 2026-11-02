#!/usr/bin/env python3
"""Measure conditional assembly of accepted initial-layout samples, with private caches."""
import argparse
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
from indexed_wire_resume6 import pinned
from initial_lazy_samples6 import selection
from initial_sample_assembly6 import emit
from initial_training_resume6 import cold_target, validate_pool, validate_receipt
from nat_descendant_resume6 import closed_worker
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def run(args):
    current, previous = Path.cwd().resolve(), args.previous.resolve()
    side = args.side
    base = previous / 'results' / ('initial-' + side + '-holdout6')
    old = base / 'check'
    actual = pinned(previous / 'results' / (previous.name.removeprefix('six-') + '.json'),
                    args.expected_receipt_sha256)
    outer = source_identity(previous)
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == 'eapiova' and machine['agda_sha256'] == args.expected_agda_sha256,
            'exact desktop compiler required')
    validate_receipt(actual, outer, previous, machine['hostname'])
    service = closed_worker(actual)
    prior = pinned(base / 'report.json', args.expected_report_sha256)
    pool = pinned(base / 'interface-map.json', args.expected_map_sha256)
    donor_pool = pool
    source_old = source_identity(old)
    require(prior['accepted'] and prior['status'] == 'complete' and prior['accepted_parts'] == 8
            and prior['accepted_donor_unchanged'] and prior['training_parts_rechecked'] == 0
            and prior['heldout_residual']['complete'] and prior['heldout_residual']['within_30_percent']
            and prior['checked_source'] == source_old and prior['machine'] == machine
            and not prior['initial_problem2_proved'] and not prior['production_authorized'],
            'exact completed conditional holdout donor required')
    validate_pool(pool, assembly6.interfaces(old))
    require(digest_entries(pool) == prior['last_interface_pool_sha256'], 'donor pool hash differs')
    layout = prior['layout']
    parts = [c['part'] for c in layout['cases']]
    sizes = [c['rows'] for c in layout['cases']]
    require(parts == selection(side)['selected'] and layout['side'] == side,
            'all16 accepted same-side sample parts required')
    for name, h in layout['generated_sha256'].items():
        require(assembly6.sha(old / name) == h, 'accepted generated source changed')
    for part in parts:
        target = layout['prefix'] + '.Part' + str(part)
        require(sum(n.endswith('/src/' + target.replace('.', '/') + '.agdai') for n in pool) == 1,
                'accepted sample proof interface missing')
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts and previous not in out.parents,
            'fresh private pilot required')
    out.mkdir(parents=True)
    report = dict(format='othello-initial-sample-assembly-pilot6-v1', accepted=False, status='preparing',
        created_utc=utc(), side=side, machine=machine, donor_closed_service=service,
        donor_checked_source=source_old, donor_receipt_sha256=args.expected_receipt_sha256,
        donor_report_sha256=args.expected_report_sha256, donor_map_sha256=args.expected_map_sha256,
        reused_sample_parts=parts, sample_parts_rechecked=0, phases=[], assembly_cpu_seconds=0.,
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        global_self_alignment_measured=False, initial_root_measured=False,
        scope='conditional assembly and import costs of4/8/16 real initial sample parts')
    named_mode = getattr(args, 'global_named', False)
    sharded_mode = getattr(args, 'global_shards', False) or named_mode
    global_mode = getattr(args, 'global_alignment', False) or sharded_mode
    if global_mode:
        require(args.sample is not None and args.expected_sample_sha256 is not None
                and not args.sample.is_symlink()
                and assembly6.sha(args.sample) == args.expected_sample_sha256,
                'exact immutable original samples required for global alignment')
        report.update(format='othello-initial-global-alignment-pilot6-v1',
            input_samples_sha256=args.expected_sample_sha256,
            scope='global lookup alignment and closed sample partial coverage; no complete initial bound')
    prediction = getattr(args, 'assembly_predicted_seconds', None)
    if prediction is not None:
        import re
        require(sharded_mode and side == 'upper' and prediction > 0
                and re.fullmatch(r'[0-9a-f]{64}', args.assembly_forecast_sha256 or ''),
                'exact prospective upper alignment forecast required')
        report['assembly_forecast'] = dict(predicted_nested_cpu_seconds=prediction,
            forecast_sha256=args.assembly_forecast_sha256, observed_before_check=False,
            whole_workflow_validated=False, production_authorized=False)

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used, free = allocated(current.parent), shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free,
                                          reserved_extra_bytes=extra, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'assembly storage gate reached; donor preserved')

    files = [(n, p) for n, _ in assembly6.source_files(old) for p in [old / n]]
    estimate = sum(p.stat().st_blocks * 512 for _, p in files)
    estimate += sum((old / n).stat().st_blocks * 512 for n in pool) + 16 * 2**20
    guard(estimate + (32 * 2**20 if global_mode else 0))
    check = out / 'check'
    check.mkdir()
    for name, path in files:
        destination = check / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    for name, h in pool.items():
        copy_interface(old / name, check / name, h)
    if global_mode:
        if named_mode:
            from initial_global_named6 import emit as emit_alignment
        elif sharded_mode:
            from initial_global_shards6 import emit as emit_alignment
        else:
            from initial_global_alignment6 import emit as emit_alignment
        from native_layout_samples6 import decode_samples
        decoded = decode_samples(args.sample)
        require(decoded['complete']['selected'] == parts, 'original complete sample selection differs')
        generated = emit_alignment(check, side=side, sample=decoded, sample_prefix=layout['prefix'],
            prefix=('Tests.InitialGlobalNamed' if named_mode else
                    'Tests.InitialGlobalShards' if sharded_mode else 'Tests.InitialGlobalAlignment')
                   + side.title())
    else:
        generated = emit(check, side=side, sample_prefix=layout['prefix'], parts=parts, sizes=sizes,
                         prefix='Tests.InitialSampleAssembly' + side.title())
    inherited = []
    reuse = getattr(args, 'reuse_stage', None)
    if reuse:
        require(global_mode and not sharded_mode, 'original global stage reuse only')
        reuse = reuse.resolve()
        receipt = pinned(reuse / 'results' / (reuse.name.removeprefix('six-') + '.json'),
                         args.expected_stage_receipt_sha256)
        validate_receipt(receipt, source_identity(reuse), reuse, machine['hostname'])
        closed_worker(receipt)
        stage_base = reuse / 'results' / ('initial-' + side + '-global-alignment6')
        stage_prior = pinned(stage_base / 'report.json', args.expected_stage_report_sha256)
        stage_pool = pinned(stage_base / 'interface-map.json', args.expected_stage_map_sha256)
        stage_old = stage_base / 'check'
        require(stage_prior['accepted'] and stage_prior['status'] == 'complete'
                and stage_prior['machine'] == machine
                and stage_prior['checked_source'] == source_identity(stage_old)
                and stage_prior['selected_targets'] == ['Stage4']
                and stage_prior['input_samples_sha256'] == args.expected_sample_sha256
                and stage_prior['layout']['generated_sha256'] == generated['generated_sha256']
                and len(stage_prior['phases']) == 1,
                'exact completed first global stage required')
        validate_pool(stage_pool, assembly6.interfaces(stage_old))
        require(digest_entries(stage_pool) == stage_prior['last_interface_pool_sha256'],
                'stage donor pool changed')
        phase = stage_prior['phases'][0]
        rec = phase['record']
        require(rec['accepted'] and rec['source_unchanged'] and rec['expected_source_matches']
                and rec['source_sha256'] == stage_prior['checked_source']['source_sha256']
                and rec['executable_sha256'] == machine['agda_sha256']
                and rec['own_target_cold'] and phase['borrowed_interfaces_unchanged'],
                'first global stage acceptance differs')
        for name, h in stage_pool.items():
            source_name = name.split('/agda/', 1)[1][:-1]
            require(assembly6.sha(stage_old / source_name) == assembly6.sha(check / source_name),
                    'cached stage source differs')
            shutil.copy2(stage_old / source_name, check / source_name)
            destination = check / name
            if destination.exists():
                require(assembly6.sha(destination) == h, 'existing private cache differs')
            else:
                copy_interface(stage_old / name, destination, h)
        pool = stage_pool
        inherited = stage_prior['phases']
        report.update(inherited_accepted_phases=inherited,
            inherited_checked_source=stage_prior['checked_source'],
            inherited_stage_report_sha256=args.expected_stage_report_sha256,
            inherited_stage_receipt_sha256=args.expected_stage_receipt_sha256)
    source = source_identity(check)
    require(assembly6.interfaces(check) == pool, 'private cache differs')
    report.update(layout=generated, checked_source=source, last_interface_pool_sha256=digest_entries(pool))
    atomic_json(out / 'interface-map.json', pool)
    save()
    targets = generated['targets'] if sharded_mode else generated['targets'][:getattr(args, 'stages', 3)]
    if inherited:
        targets = targets[1:]
    report['selected_targets'] = targets
    for index, target in enumerate(targets):
        guard(8 * 2**20)
        module = generated['prefix'] + '.' + target
        before = assembly6.interfaces(check)
        cold_target(before, module)
        remaining = args.assembly_cpu_limit - report['assembly_cpu_seconds']
        require(remaining > 1, 'assembly CPU cap reached')
        rec = run_job('target' + str(index), [args.agda, '--no-libraries', '-i', 'src', '--safe',
            '--without-K', '--cubical-compatible', '--save-metas',
            'src/' + module.replace('.', '/') + '.agda', '+RTS', '-M2700M', '-c', '-s', '-RTS'],
            out / 'records', root=check, expected_source_sha256=source['source_sha256'],
            timeout=420, cpu_limit=min(getattr(args, 'target_cpu_limit', 180), remaining), rss_limit_gib=3, log_limit_mib=2,
            metadata=dict(target=module, own_target_cold=True, conditional_assembly=True,
                          initial_problem2_proved=False))
        after = assembly6.interfaces(check)
        unchanged = all(after.get(n) == h for n, h in before.items())
        report['phases'].append(dict(target=module, record=rec, borrowed_interfaces_unchanged=unchanged,
                                    parts=(generated['owned_parts'] if sharded_mode else
                                           next(s.get('owned_parts', s['parts']) for s in generated['stages']
                                                if s['target'] == target))))
        report['assembly_cpu_seconds'] += rec['cpu_seconds']
        report.update(status='checking' if rec['accepted'] and unchanged else 'target-rejected',
                      last_interface_pool_sha256=digest_entries(after))
        atomic_json(out / 'interface-map.json', after)
        save()
        require(rec['accepted'] and unchanged, 'conditional assembly rejected: ' + module)
    require(source_identity(previous) == outer and source_identity(old) == source_old
            and assembly6.interfaces(old) == donor_pool and source_identity(check) == source,
            'donor or new source changed')
    if global_mode:
        require(assembly6.sha(args.sample) == args.expected_sample_sha256, 'original sample changed')
    report.update(accepted=True, status='complete', finished_utc=utc(), accepted_donor_unchanged=True,
                  global_lookup_alignment_checked=global_mode, global_self_alignment_measured=global_mode)
    if prediction is not None:
        error = abs(report['assembly_cpu_seconds'] - prediction) / prediction
        report['assembly_forecast_residual'] = dict(complete=True,
            predicted_nested_cpu_seconds=prediction, measured_nested_cpu_seconds=report['assembly_cpu_seconds'],
            relative_error=error, within_30_percent=error <= .30, whole_workflow_validated=False)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--side', choices=('lower', 'upper'), required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-receipt-sha256',
                 'expected-report-sha256', 'expected-map-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--assembly-cpu-limit', type=float, default=600)
    parser.add_argument('--stages', type=int, choices=(1, 2, 3), default=3)
    parser.add_argument('--target-cpu-limit', type=float, default=180)
    parser.add_argument('--global-alignment', action='store_true')
    parser.add_argument('--global-shards', action='store_true')
    parser.add_argument('--global-named', action='store_true')
    parser.add_argument('--sample', type=Path)
    parser.add_argument('--expected-sample-sha256')
    parser.add_argument('--reuse-stage', type=Path)
    parser.add_argument('--expected-stage-receipt-sha256')
    parser.add_argument('--expected-stage-report-sha256')
    parser.add_argument('--expected-stage-map-sha256')
    parser.add_argument('--assembly-predicted-seconds', type=float)
    parser.add_argument('--assembly-forecast-sha256')
    args = parser.parse_args()
    require(0 < args.assembly_cpu_limit <= 900, 'bounded assembly budget required')
    require(0 < args.target_cpu_limit <= 180, 'bounded per-target CPU budget required')
    run(args)


if __name__ == '__main__':
    main()
