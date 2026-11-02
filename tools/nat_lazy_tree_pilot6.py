#!/usr/bin/env python3
"""Cold-check uniform-lazy lower and upper hierarchies for a real late game.

This bounded pilot borrows only byte-identical generic core interfaces from a
completed desktop check. It never borrows generated parts or claims an initial
board theorem. Every newly generated proof is checked in a private build root.
"""
import argparse
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
import compact_shared6 as compact
from census_pilot6 import state
import generate6
from indexed_spike6 import BASE, IMAGE
from indexed_wire_pilot6 import skeleton
from indexed_wire_resume6 import pinned
from nat_descendant_resume6 import closed_worker
from nat_indexed_pilot6 import convert_wire
import nat_lazy_tree6 as lazy
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_identity
import ref
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def prepare(check):
    base = state(BASE[1:], 'black')
    passed = ref.successors(base)
    require(not ref.placements(base) and len(passed) == 1,
            'expected genuine forced pass')
    choices = ref.successors(passed[0])
    require(len(choices) == 2, 'expected both opponent replies')
    off = compact.pack_state(generate6.encode_state(choices[0]))
    lower = [compact.pack_state(BASE) * 2, compact.pack_state(IMAGE), compact.pack_state(IMAGE)]
    upper = [off + compact.pack_state(BASE), compact.pack_state(IMAGE), compact.pack_state(IMAGE)]
    sizes = [2, 1, 1]
    _, nodes, _ = skeleton(sizes)
    leaves = [n for n in nodes if 'leaf' in n]
    layouts = []
    for side, states, bodies in (
            ('lower', lower, ['PC1F1LKa00', 'R4a00', 'Kba00']),
            ('upper', upper, ['C0LPF2Ka00C0L', 'R4a01', 'Kba00'])):
        prefix = 'Tests.UniformLazyMini' + side.title()
        state_prefix = prefix + 'States'
        state_files = {}
        for j, n in enumerate(sizes):
            state_files.update(lazy.emit_state_text(check, state_prefix, j, n, states[j])['generated_sha256'])
        layout = lazy.generate(check, sizes=sizes,
            dependencies={0: [0], 1: [0, 1], 2: [1, 2]},
            body_texts=[convert_wire(text, leaves)[0] for text in bodies],
            root_packed=compact.pack_state(IMAGE), state_prefix=state_prefix,
            prefix=prefix, cut_depth=1, side=side)
        layout.update(prefix=prefix, state_data_sha256=state_files)
        layouts.append(layout)
    return layouts


def run(args, *, prepare_layouts=prepare, whole_late_root=True, prepare_extra_bytes=0):
    current = Path.cwd().resolve()
    previous = args.previous.resolve()
    label = previous.name.removeprefix('six-')
    actual = pinned(previous / 'results' / (label + '.json'), args.expected_receipt_sha256)
    require(actual['accepted'] and actual['exit_code'] == 0 and actual['stop_reason'] is None
            and actual['source_unchanged'] and actual['expected_source_matches']
            and source_identity(previous)['source_sha256'] == actual['source_sha256'],
            'accepted unchanged donor required')
    service = closed_worker(actual)
    base = previous / 'results/nat-lazy-finish6'
    prior = pinned(base / 'report.json', args.expected_report_sha256)
    pool = pinned(base / 'interface-map.json', args.expected_map_sha256)
    old = base / 'check'
    old_source = source_identity(old)
    machine = assembly6.machine_identity(args.agda)
    require(prior['accepted'] and prior['root_checked'] and prior['accepted_parts'] == 267
            and prior['descendant_original_lower_checked']
            and prior['checked_source'] == old_source and prior['machine'] == machine
            and machine['hostname'] == 'eapiova'
            and machine['agda_sha256'] == args.expected_agda_sha256
            and assembly6.interfaces(old) == pool
            and digest_entries(pool) == prior['last_interface_pool_sha256'],
            'exact completed desktop donor required')
    borrowed = {}
    source_names = set()
    for name, digest in pool.items():
        require(name.startswith('_build/') and '/agda/' in name and name.endswith('.agdai'),
                'unsupported generic interface location')
        source = name.split('/agda/', 1)[1][:-1]
        if source == 'src/Prelude.agda' or source.startswith(('src/Game/', 'src/Othello/')):
            require((current / source).is_file()
                    and assembly6.sha(current / source) == assembly6.sha(old / source),
                    'current generic source differs from accepted donor')
            borrowed[name] = digest
            source_names.add(source)
    require('src/Othello/LazyIndexed6.agda' in source_names, 'accepted lazy core missing')
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh isolated pilot required')
    out.mkdir(parents=True)
    report = dict(format='othello-nat-lazy-tree-pilot6-v1', accepted=False, status='preparing',
        created_utc=utc(), machine=machine, donor_closed_service=service, donor_source=old_source,
        donor_receipt_sha256=args.expected_receipt_sha256, donor_report_sha256=args.expected_report_sha256,
        donor_map_sha256=args.expected_map_sha256, borrowed_generic_interfaces=len(borrowed),
        phases=[], kernel_cpu_seconds=0., initial_problem2_proved=False,
        optimal_initial_pair_proved=False, production_authorized=False,
        scope=('uniform-lazy lower and upper original-rule bounds for a late forced-pass position'
               if whole_late_root else 'independent lazy part acceptances and conditional links at high numeric IDs'))

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used = allocated(current.parent)
        free = shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free, checked_utc=utc())
        save()
        extra += getattr(args, 'other_reserved_artifact_mib', 0) * 2**20
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'storage gate reached; accepted donor preserved')

    guard(sum((old / n).stat().st_blocks * 512 for n in borrowed) + 8 * 2**20 + prepare_extra_bytes)
    check = out / 'check'
    check.mkdir()
    shutil.copytree(current / 'src', check / 'src', copy_function=shutil.copy2)
    shutil.copy2(current / 'othello.agda-lib', check / 'othello.agda-lib')
    for name in source_names:
        shutil.copy2(old / name, check / name)
    for name, digest in borrowed.items():
        copy_interface(old / name, check / name, digest)
    layouts = prepare_layouts(check)
    source = source_identity(check)
    report.update(layouts=layouts, checked_source=source)
    save()
    targets = [layout['prefix'] + '.' + name for layout in layouts for name in layout['targets']]
    for index, target in enumerate(targets):
        guard()
        before = assembly6.interfaces(check)
        suffix = '/' + target.replace('.', '/') + '.agdai'
        require(not any(n.endswith(suffix) for n in before), 'own target unexpectedly warm')
        remaining = args.kernel_cpu_limit - report['kernel_cpu_seconds']
        require(remaining > 1, 'nested CPU cap reached')
        record = run_job('target' + str(index), [args.agda, '--no-libraries', '-i', 'src', '--safe',
            '--without-K', '--cubical-compatible', '--save-metas',
            'src/' + target.replace('.', '/') + '.agda', '+RTS', '-M1350M', '-c', '-s', '-RTS'],
            out / 'records', root=check, expected_source_sha256=source['source_sha256'],
            timeout=180, cpu_limit=min(60, remaining), rss_limit_gib=1.5, log_limit_mib=2,
            metadata=dict(target=target, own_target_cold=True, initial_problem2_proved=False))
        after = assembly6.interfaces(check)
        unchanged = all(after.get(n) == digest for n, digest in before.items())
        report['phases'].append(dict(target=target, record=record, borrowed_interfaces_unchanged=unchanged))
        report['kernel_cpu_seconds'] += record['cpu_seconds']
        report['status'] = 'checking'
        report['last_interface_pool_sha256'] = digest_entries(after)
        atomic_json(out / 'interface-map.json', after)
        save()
        require(record['accepted'] and unchanged, 'uniform lazy hierarchy failed: ' + target)
    require(source_identity(old) == old_source and assembly6.interfaces(old) == pool,
            'accepted donor changed')
    report.update(accepted=True, status='complete', finished_utc=utc(),
        late_original_lower_and_upper_checked=whole_late_root,
        conditional_sample_links_checked=not whole_late_root, accepted_donor_unchanged=True)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-receipt-sha256',
                 'expected-report-sha256', 'expected-map-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--kernel-cpu-limit', type=float, default=180)
    parser.add_argument('--high-rank-parts', action='store_true',
        help='check independent real-game part fixtures at initial-layout-sized numeric IDs')
    parser.add_argument('--initial-sample', type=Path)
    parser.add_argument('--expected-initial-sample-sha256')
    parser.add_argument('--sample-direction', choices=('lower', 'upper'))
    parser.add_argument('--training-parts', type=int, choices=range(1, 9), default=2)
    parser.add_argument('--other-reserved-artifact-mib', type=int, choices=range(0, 33), default=0)
    args = parser.parse_args()
    if args.initial_sample:
        from initial_lazy_samples6 import selection
        from lazy_sample_parts6 import emit
        from native_layout_samples6 import decode_samples
        require(not args.high_rank_parts and args.sample_direction and args.expected_initial_sample_sha256,
                'initial sample direction/hash required, without fixture mode')
        data_path = args.initial_sample.resolve()
        require(not args.initial_sample.is_symlink() and data_path.is_file() and 'results' in data_path.parts
                and assembly6.sha(data_path) == args.expected_initial_sample_sha256,
                'exact immutable sample data required')
        decoded = decode_samples(data_path)
        plan = selection(args.sample_direction)
        require(decoded['complete']['selected'] == plan['selected']
                and decoded['complete']['parts'] == plan['expected']['layout_parts'],
                'fixed initial sample selection differs')
        selected = plan['training'][:args.training_parts]
        cases = [c for c in decoded['cases'] if c['part'] in selected]
        require([c['part'] for c in cases] == selected, 'training sample missing')
        needed = {d for c in cases for d in c['dependencies']}
        chosen = dict(cases=cases, states={j: decoded['states'][j] for j in needed})
        # Conservative source estimate is additional to private core/cache and
        # interface-growth headroom, including the other live native output.
        extra = sum(len(c['text']) + 1024 for c in chosen['states'].values())
        extra += sum(len(c['body_text']) + len(c['dependencies']) * 512 + 16384 for c in cases)

        def initial_parts(check):
            result = emit(check, chosen, side=args.sample_direction,
                prefix='Tests.InitialLazyTraining' + args.sample_direction.title())
            result.update(input_samples=str(data_path), input_samples_sha256=args.expected_initial_sample_sha256,
                selected_training=selected, held_out_checked=False)
            return [result]

        run(args, prepare_layouts=initial_parts, whole_late_root=False, prepare_extra_bytes=extra)
        require(assembly6.sha(data_path) == args.expected_initial_sample_sha256, 'sample bytes changed')
    elif args.high_rank_parts:
        from lazy_sample_parts6 import emit
        from test_lazy_sample_parts6 import fixture

        def high_rank(check):
            return [emit(check, fixture(side), side=side,
                         prefix='Tests.LazyHighRank' + side.title()) for side in ('lower', 'upper')]

        run(args, prepare_layouts=high_rank, whole_late_root=False)
    else:
        run(args)


if __name__ == '__main__':
    main()
