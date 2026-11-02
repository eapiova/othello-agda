#!/usr/bin/env python3
"""Cold-check original-rank slices of true initial-layout extrema, in a private cache.

Native samples provide data only. This finite pilot checks every selected slice
with safe Agda and records conditional links; it never assembles an initial bound.
"""
import argparse
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
from indexed_wire_resume6 import pinned
from initial_training_resume6 import cold_target, target_interfaces, validate_pool, validate_receipt
from lazy_sample_slices6 import emit
from nat_descendant_resume6 import closed_worker
from native_layout_samples6 import decode_samples
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def core_pool(pool, core):
    """Reuse only interfaces whose exact source is in the unchanged main core."""
    result = {}
    for name, digest in pool.items():
        source = name.split('/agda/', 1)[1][:-1]
        if source in core:
            result[name] = digest
    require(bool(result), 'accepted core interfaces required')
    return result


def run(args):
    current, previous, native = Path.cwd().resolve(), args.previous.resolve(), args.native_root.resolve()
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == 'eapiova' and machine['agda_sha256'] == args.expected_agda_sha256,
            'exact same desktop compiler required')
    donor_outer = source_identity(previous)
    actual = pinned(previous / 'results' / (previous.name.removeprefix('six-') + '.json'),
                    args.expected_receipt_sha256)
    validate_receipt(actual, donor_outer, previous, machine['hostname'])
    donor_service = closed_worker(actual)
    donor_base = previous / 'results/initial-lower-holdout6'
    old = donor_base / 'check'
    prior = pinned(donor_base / 'report.json', args.expected_report_sha256)
    donor_pool = pinned(donor_base / 'interface-map.json', args.expected_map_sha256)
    donor_source = source_identity(old)
    require(prior['accepted'] and prior['status'] == 'complete' and prior['machine'] == machine
            and prior['checked_source'] == donor_source and prior['accepted_donor_unchanged'],
            'completed unchanged accepted core donor required')
    validate_pool(donor_pool, assembly6.interfaces(old))
    require(digest_entries(donor_pool) == prior['last_interface_pool_sha256'], 'donor pool hash differs')
    native_outer = source_identity(native)
    native_receipt = pinned(native / 'results' / (native.name.removeprefix('six-') + '.json'),
                            args.expected_native_receipt_sha256)
    validate_receipt(native_receipt, native_outer, native, machine['hostname'])
    native_service = closed_worker(native_receipt)
    native_base = native / 'results/initial-extrema-samples6'
    native_report = pinned(native_base / 'report.json', args.expected_native_report_sha256)
    require(native_report['accepted'] and native_report['status'] == 'complete-untrusted-extrema-samples'
            and len(native_report['phases']) == 4 and all(p['accepted'] for p in native_report['phases'])
            and not native_report['initial_problem2_proved'], 'complete uncensored native extrema data required')
    samples = []
    for side in (('lower', 'upper') if args.side == 'both' else (args.side,)):
        phase = next(p for p in native_report['phases'] if p['direction'] == side and p['mode'] == 'extract')
        summary = pinned(native_base / (side + '-summary.json'), phase['summary_sha256'])
        path = native_base / (side + '-extract.jsonl')
        require(not path.is_symlink() and assembly6.sha(path) == summary['samples_sha256']
                == phase['sample_sha256'], 'exact immutable extrema sample required')
        decoded = decode_samples(path)
        require(decoded['complete']['selected'] == phase['selected'] == summary['selected']
                and 1 <= len(decoded['cases']) <= 3 and summary['kernel_checks_pending'],
                'selected actual extrema IDs differ')
        samples.append((side, path, summary, decoded))
    core = {n for n, _ in source_files(current) if n.startswith('src/') or n == 'othello.agda-lib'}
    pool = core_pool(donor_pool, core)
    for name in core:
        require((old / name).is_file() and assembly6.sha(old / name) == assembly6.sha(current / name),
                'main safe core differs from accepted donor')
    out = args.output.resolve()
    require(not out.exists() and current in out.parents and 'results' in out.parts,
            'fresh private pilot required')
    out.mkdir(parents=True)
    report = dict(format='othello-extrema-slices-pilot6-v1', accepted=False, status='preparing',
        created_utc=utc(), machine=machine, donor_closed_service=donor_service,
        native_closed_service=native_service, donor_receipt_sha256=args.expected_receipt_sha256,
        donor_report_sha256=args.expected_report_sha256, donor_map_sha256=args.expected_map_sha256,
        native_receipt_sha256=args.expected_native_receipt_sha256,
        native_report_sha256=args.expected_native_report_sha256, donor_checked_source=donor_source,
        layouts=[], phases=[], kernel_cpu_seconds=0., accepted_slices=0,
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='actual extrema split into <=50-row original-rank checker facts and conditional links')

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used, free = allocated(current.parent), shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free,
                                          reserved_extra_bytes=extra, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'extrema slice storage gate reached; donors preserved')

    estimate = sum((old / n).stat().st_blocks * 512 for n in core)
    estimate += sum((old / n).stat().st_blocks * 512 for n in pool)
    # Text sources and tiny state interfaces dominate; reserve their full
    # per-chunk allocation plus conservative space for checker interfaces.
    estimate += sum(len(d['states']) * 16 * 1024 + p.stat().st_size for _, p, _, d in samples)
    guard(estimate + 24 * 2**20)
    check = out / 'check'
    check.mkdir()
    for name in sorted(core):
        target = check / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old / name, target)
    for name, digest in pool.items():
        copy_interface(old / name, check / name, digest)
    for side, path, summary, _ in samples:
        layout = emit(check, path, side=side, prefix='Tests.InitialExtremaSlices' + side.title(),
                      rows_per_slice=args.rows_per_slice)
        layout['summary'] = summary
        report['layouts'].append(layout)
    source = source_identity(check)
    require(assembly6.interfaces(check) == pool, 'private core cache differs')
    report.update(checked_source=source, last_interface_pool_sha256=digest_entries(pool))
    atomic_json(out / 'interface-map.json', pool)
    save()
    for layout in report['layouts']:
        for name in layout['targets']:
            guard(8 * 2**20)
            target = layout['prefix'] + '.' + name
            before = assembly6.interfaces(check)
            cold_target(before, target)
            remaining = args.kernel_cpu_limit - report['kernel_cpu_seconds']
            require(remaining > 1, 'extrema kernel CPU cap reached')
            record = run_job('target' + str(len(report['phases'])),
                [args.agda, '--no-libraries', '-i', 'src', '--safe', '--without-K',
                 '--cubical-compatible', '--save-metas', 'src/' + target.replace('.', '/') + '.agda',
                 '+RTS', '-M1350M', '-c', '-s', '-RTS'], out / 'records', root=check,
                expected_source_sha256=source['source_sha256'], timeout=420,
                cpu_limit=min(120, remaining), rss_limit_gib=1.5, log_limit_mib=2,
                metadata=dict(target=target, own_target_cold=True, original_global_ids_preserved=True,
                              native_claim_is_premise=False, initial_problem2_proved=False))
            after = assembly6.interfaces(check)
            unchanged = all(after.get(n) == h for n, h in before.items())
            own = target_interfaces(after, target)
            input_unchanged = all(assembly6.sha(p) == s['samples_sha256'] for _, p, s, _ in samples)
            phase = dict(target=target, record=record, borrowed_interfaces_unchanged=unchanged,
                input_samples_unchanged=input_unchanged, own_interface={n: after[n] for n in own},
                interfaces_before_sha256=digest_entries(before), interfaces_after_sha256=digest_entries(after))
            report['phases'].append(phase)
            report['kernel_cpu_seconds'] += record['cpu_seconds']
            accepted = record['accepted'] and unchanged and input_unchanged and len(own) == 1
            report['accepted_slices'] += int(accepted and name.startswith('Slice'))
            report.update(status='checking' if accepted else 'target-rejected',
                          last_interface_pool_sha256=digest_entries(after))
            atomic_json(out / 'interface-map.json', after)
            save()
            require(accepted, 'extrema target rejected; preserve failure: ' + target)
    require(source_identity(previous) == donor_outer and source_identity(old) == donor_source
            and assembly6.interfaces(old) == donor_pool and source_identity(native) == native_outer
            and source_identity(check) == source, 'accepted donor or checked source changed')
    report.update(accepted=True, status='complete', finished_utc=utc(), accepted_donor_unchanged=True,
                  conditional_slice_links_checked=True)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'native-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-receipt-sha256', 'expected-report-sha256',
                 'expected-map-sha256', 'expected-native-receipt-sha256', 'expected-native-report-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--side', choices=('lower', 'upper', 'both'), default='both')
    parser.add_argument('--rows-per-slice', type=int, default=50)
    parser.add_argument('--kernel-cpu-limit', type=float, default=600)
    args = parser.parse_args()
    require(1 <= args.rows_per_slice <= 50 and 0 < args.kernel_cpu_limit <= 1200,
            'bounded slice and CPU budget required')
    run(args)


if __name__ == '__main__':
    main()
