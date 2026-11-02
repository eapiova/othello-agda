#!/usr/bin/env python3
"""Check direct sample linkage with private copies of accepted named interfaces.

This bounded assembly experiment never checks complete initial coverage or
authorizes production. The accepted named donor and original row proofs remain
unchanged, and every new claim is checked by safe Agda.
"""
import argparse
from pathlib import Path
import re
import shutil
import tempfile

import assembly6
from cache_resume6 import copy_interface
from indexed_wire_resume6 import pinned
from initial_global_direct6 import emit
from initial_shards_resume6 import argv
from initial_training_resume6 import cold_target, target_interfaces, validate_pool, validate_receipt
from native_layout_samples6 import decode_samples
from nat_descendant_resume6 import closed_worker
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, build_lock, run_job, utc
from wire_workflow6 import require
from closed_pilot_policy6 import same_compiler_after_reboot


def run(args):
    current, previous = Path.cwd().resolve(), args.previous.resolve()
    closed = getattr(args, 'closed_lookup_80g_20261015', False)
    narrow = getattr(args, 'narrow_routes_80g_20261015', False)
    module_only = getattr(args, 'module_imports_80g_20261016', False)
    limited = closed or narrow or module_only
    require(sum((closed, narrow, module_only)) <= 1, 'one candidate per approved test')
    if limited:
        require((args.side == 'lower' or module_only) and not args.private_imports and args.cpu_limit <= 230
                and args.output.as_posix() == 'results/initial-' + args.side + '-global-' + ('module6' if module_only else 'narrow6' if narrow else 'closed6'),
                'one-off closed linkage pilot only')
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == 'eapiova' and machine['agda_sha256'] == args.expected_agda_sha256,
            'exact desktop compiler required')
    outer = source_identity(previous)
    receipt = pinned(previous / 'results' / (previous.name.removeprefix('six-') + '.json'),
                     args.expected_receipt_sha256)
    validate_receipt(receipt, outer, previous, machine['hostname'])
    service = closed_worker(receipt)
    base = previous / 'results' / ('initial-' + args.side + '-global-named6')
    old = base / 'check'
    prior = pinned(base / 'report.json', args.expected_report_sha256)
    pool = pinned(base / 'interface-map.json', args.expected_map_sha256)
    source_old = source_identity(old)
    layout = prior['layout']
    same_machine = (same_compiler_after_reboot(prior['machine'], machine) if limited
                    else prior['machine'] == machine)
    require(prior['accepted'] and prior['status'] == 'complete' and same_machine
            and prior['checked_source'] == source_old and prior['sample_parts_rechecked'] == 0
            and prior['global_lookup_alignment_checked'] and prior['global_self_alignment_measured']
            and not prior['initial_problem2_proved'] and not prior['production_authorized']
            and layout['format'] == 'othello-initial-global-named6-v1' and layout['side'] == args.side,
            'exact completed same-side named donor required')
    validate_pool(pool, assembly6.interfaces(old))
    require(digest_entries(pool) == prior['last_interface_pool_sha256'], 'named donor pool differs')
    targets = [layout['prefix'] + '.' + n for n in layout['targets']]
    phases = prior.get('inherited_accepted_phases', []) + prior['phases']
    require([p['target'] for p in phases] == targets, 'complete ordered named acceptance required')
    for phase in phases:
        rec = phase['record']
        require(rec['accepted'] and rec['exit_code'] == 0 and rec['stop_reason'] is None
                and rec['source_unchanged'] and rec['expected_source_matches'] and rec['own_target_cold']
                and rec['source_sha256'] == rec['expected_source_sha256'] == source_old['source_sha256']
                and rec['executable_sha256'] == machine['agda_sha256']
                and rec['machine'] == machine['hostname'] and rec['argv'] == argv(machine, phase['target'])
                and phase['borrowed_interfaces_unchanged']
                and len(target_interfaces(pool, phase['target'])) == 1,
                'named donor target provenance differs')
    require(not args.sample.is_symlink() and assembly6.sha(args.sample) == args.expected_sample_sha256
            and prior['input_samples_sha256'] == args.expected_sample_sha256,
            'exact original sample required')
    sample = decode_samples(args.sample)
    out = args.output.resolve()
    require(not out.exists() and current in out.parents and 'results' in out.parts,
            'fresh private direct pilot required')
    out.mkdir(parents=True)
    report = dict(format='othello-initial-direct-pilot6-v1', accepted=False, status='preparing',
        created_utc=utc(), side=args.side, machine=machine, donor_closed_service=service,
        donor_receipt_sha256=args.expected_receipt_sha256, donor_report_sha256=args.expected_report_sha256,
        donor_map_sha256=args.expected_map_sha256, donor_checked_source=source_old,
        input_samples_sha256=args.expected_sample_sha256, reused_named_targets=len(targets),
        accepted_targets_rechecked=0, sample_parts_rechecked=0, phases=[], assembly_cpu_seconds=0.,
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='direct function linkage and CLOSED sample partial coverage only')
    if limited:
        report['accepted_donor_machine'] = prior['machine']
        report['same_compiler_after_reboot_verified'] = True
        report['user_approved_resource_exception'] = dict(date='2026-10-16' if module_only else '2026-10-15',
            free_disk_gib=80, total_outer_cpu_seconds_max=300, hard_cgroup_memory_gib=3,
            study_artifacts_gib_max=10, scope='this ' + args.side + ' ' + ('module-import' if module_only else 'narrow-import' if narrow else 'closed-linkage') + ' pilot only')
    prediction = args.predicted_seconds
    require((prediction is None) == (args.forecast_sha256 is None), 'complete forecast pins required')
    if prediction is not None:
        require(args.side == 'upper' and prediction > 0
                and re.fullmatch(r'[0-9a-f]{64}', args.forecast_sha256),
                'bounded prospective upper forecast required')
        report['assembly_forecast'] = dict(predicted_nested_cpu_seconds=prediction,
            forecast_sha256=args.forecast_sha256, heldout_measured_before_launch=False,
            whole_workflow_validated=False)

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used, free = allocated(current.parent), shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free,
                                          reserved_extra_bytes=extra, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= (80 if limited else 100) * 2**30,
                'direct pilot storage guard reached; accepted donor preserved')

    files = [n for n, _ in source_files(old)]
    staged_pool = dict(pool)
    if limited:
        # These coverage modules are verified above, but the new candidate
        # imports only named data/maps/routes and the original row facts.
        stem = '/src/' + layout['prefix'].replace('.', '/') + '/'
        omitted = [n for n in pool if stem in n and
                   re.fullmatch(r'(?:Part\d+|Root)\.agdai', Path(n).name)]
        require(len(omitted) == 17, 'expected unused named coverage interfaces')
        staged_pool = {n: h for n, h in pool.items() if n not in omitted}
        report['unused_named_coverage_interfaces_not_staged'] = omitted
    if narrow:
        from closed_pilot_allocation6 import recover
        report['closed_allocation'] = recover(current, previous, out / 'allocation.json')
    guard(sum((old / n).stat().st_blocks * 512 for n in
              (files if module_only else files + list(staged_pool))) + 16 * 2**20)
    check = out / 'check'
    check.mkdir()
    if module_only:
        # Validate donors and generate in disposable private source storage.
        # Accepted interfaces stay at their original paths behind a read-only
        # mount; no active cache inode is shared with a writable path.
        with tempfile.TemporaryDirectory(prefix='module-source-', dir=out) as tmp:
            stage = Path(tmp)
            for n in files:
                p = stage / n; p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old / n, p)
            generated = emit(stage, side=args.side, sample=sample,
                sample_prefix=layout['sample_prefix'], named_layout=layout,
                module_imports_only=True, prefix='Tests.InitialGlobalModule' + args.side.title())
            for n in generated['generated_sha256']:
                p = check / n; p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(stage / n, p)
            libraries = [n for n in files if n.endswith('.agda-lib')]
            require(len(libraries) == 1, 'one private project library expected')
            shutil.copy2(old / libraries[0], check / libraries[0])
        report.update(dependency_mode='existing immutable source/interfaces, bwrap read-only root',
                      dependency_root=str(old), copied_dependency_interfaces=0)
        staged_pool = {}
    else:
        for n in files:
            destination = check / n
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old / n, destination)
        for n, digest in staged_pool.items():
            copy_interface(old / n, check / n, digest)
        require(source_identity(check) == source_old and assembly6.interfaces(check) == staged_pool,
                'private named copy differs')
    if module_only:
        pass
    elif narrow:
        from initial_global_narrow6 import emit as emit_narrow
        generated = emit_narrow(check, side=args.side, sample=sample,
            sample_prefix=layout['sample_prefix'], named_layout=layout,
            prefix='Tests.InitialGlobalNarrowLower')
    elif closed:
        from initial_global_closed6 import emit as emit_closed
        generated = emit_closed(check, side=args.side, sample=sample,
            sample_prefix=layout['sample_prefix'], named_layout=layout,
            prefix='Tests.InitialGlobalClosedLower')
    else:
        generated = emit(check, side=args.side, sample=sample, sample_prefix=layout['sample_prefix'],
                         named_layout=layout, private_imports=args.private_imports,
                         prefix=('Tests.InitialGlobalPrivate' if args.private_imports else
                                 'Tests.InitialGlobalDirect') + args.side.title())
    source = source_identity(check)
    report.update(layout=generated, checked_source=source, last_interface_pool_sha256=digest_entries(staged_pool))
    atomic_json(out / 'interface-map.json', staged_pool)
    save()
    for name in generated['targets']:
        guard(8 * 2**20)
        target = generated['prefix'] + '.' + name
        before = assembly6.interfaces(check)
        cold_target(before, target)
        remaining = args.cpu_limit - report['assembly_cpu_seconds']
        require(remaining > 1, 'direct pilot CPU cap reached')
        checker_command = argv(machine, target)
        if module_only:
            from readonly_dependencies6 import command
            checker_command = command(machine, target, check, old)
        rec = run_job('target' + str(len(report['phases'])), checker_command, out / 'records',
            root=check, expected_source_sha256=source['source_sha256'], timeout=420,
            cpu_limit=min(60, remaining), rss_limit_gib=2.5 if limited else 3, log_limit_mib=2,
            metadata=dict(target=target, own_target_cold=True, initial_problem2_proved=False,
                          checker_binary_sha256=machine['agda_sha256']))
        after = assembly6.interfaces(check)
        unchanged = all(after.get(n) == h for n, h in before.items())
        if module_only:
            unchanged = unchanged and assembly6.interfaces(old) == pool
        report['phases'].append(dict(target=target, record=rec, borrowed_interfaces_unchanged=unchanged))
        report['assembly_cpu_seconds'] += rec['cpu_seconds']
        report.update(status='checking' if rec['accepted'] and unchanged else 'target-rejected',
                      last_interface_pool_sha256=digest_entries(after))
        atomic_json(out / 'interface-map.json', after)
        save()
        require(rec['accepted'] and unchanged, 'direct linkage rejected: ' + target)
    require(source_identity(previous) == outer and source_identity(old) == source_old
            and assembly6.interfaces(old) == pool and source_identity(check) == source
            and assembly6.sha(args.sample) == args.expected_sample_sha256,
            'donor, source or original sample changed')
    report.update(accepted=True, status='complete', finished_utc=utc(), accepted_donor_unchanged=True,
                  global_lookup_alignment_checked=True, global_self_alignment_measured=True)
    if prediction is not None:
        error = abs(report['assembly_cpu_seconds'] - prediction) / prediction
        report['assembly_forecast_residual'] = dict(complete=True,
            predicted_nested_cpu_seconds=prediction, measured_nested_cpu_seconds=report['assembly_cpu_seconds'],
            relative_error=error, within_30_percent=error <= .30, whole_workflow_validated=False)
    save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output', 'sample'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--side', choices=('lower', 'upper'), required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-receipt-sha256',
                 'expected-report-sha256', 'expected-map-sha256', 'expected-sample-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--cpu-limit', type=float, default=180)
    parser.add_argument('--predicted-seconds', type=float)
    parser.add_argument('--forecast-sha256')
    parser.add_argument('--private-imports', action='store_true')
    parser.add_argument('--closed-lookup-80g-20261015', action='store_true')
    parser.add_argument('--narrow-routes-80g-20261015', action='store_true')
    parser.add_argument('--module-imports-80g-20261016', action='store_true')
    args = parser.parse_args()
    require(0 < args.cpu_limit <= 400, 'bounded direct linkage budget required')
    if args.module_imports_80g_20261016:
        donor = args.previous / 'results' / ('initial-' + args.side + '-global-named6') / 'check'
        with build_lock(donor):
            run(args)
    else:
        run(args)
