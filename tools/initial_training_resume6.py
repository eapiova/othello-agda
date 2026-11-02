#!/usr/bin/env python3
"""Reuse the exact accepted lower training pair and cold-check six remaining parts.

Every result is an independent checker fact with a conditional link. This job
never assembles or claims an initial-board theorem or checks held-out samples.
"""
import argparse
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
from indexed_wire_resume6 import pinned
from initial_lazy_samples6 import selection
from lazy_sample_parts6 import emit
from nat_descendant_resume6 import closed_worker
from native_layout_samples6 import decode_samples
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require

PREFIX = 'Tests.InitialLazyTrainingLower'
PRIOR_PARTS = [0, 4599]
TRAINING = [0, 4599, 9756, 12421, 17673, 23621, 28426, 33690]


def argv(machine, target):
    return [machine['agda_path'], '--no-libraries', '-i', 'src', '--safe',
            '--without-K', '--cubical-compatible', '--save-metas',
            'src/' + target.replace('.', '/') + '.agda', '+RTS', '-M1350M', '-c', '-s', '-RTS']


def validate_receipt(receipt, source, previous, hostname):
    require(receipt.get('finished_utc') and receipt['accepted'] and receipt['exit_code'] == 0
            and receipt['stop_reason'] is None and receipt['source_unchanged']
            and receipt['expected_source_matches']
            and receipt['source_sha256'] == receipt['expected_source_sha256'] == source['source_sha256']
            and receipt['root'] == str(previous) and receipt['machine'] == hostname,
            'terminal accepted unchanged predecessor receipt required')


def chosen_training(decoded):
    plan = selection('lower')
    require(plan['training'] == TRAINING and decoded['complete']['selected'] == plan['selected']
            and all(decoded['complete'][field] == plan['expected'][expected]
                    for field, expected in [('parts', 'layout_parts'), ('records', 'layout_records'),
                                             ('tokens', 'layout_tokens')])
            and [c['part'] for c in decoded['cases']] == plan['selected'],
            'complete fixed lower sample selection required')
    cases = [c for c in decoded['cases'] if c['part'] in TRAINING]
    require([c['part'] for c in cases] == TRAINING, 'complete training cases required')
    needed = {d for c in cases for d in c['dependencies']}
    require(needed <= decoded['states'].keys(), 'training state dependency missing')
    return dict(cases=cases, states={j: decoded['states'][j] for j in sorted(needed)})


def load_training(path, expected):
    require(not path.is_symlink() and path.is_file() and 'results' in path.resolve().parts
            and assembly6.sha(path) == expected, 'exact immutable lower sample hash required')
    return chosen_training(decode_samples(path))


def target_interfaces(pool, target):
    suffix = '/src/' + target.replace('.', '/') + '.agdai'
    return [name for name in pool if name.endswith(suffix)]


def validate_pool(pool, actual):
    require(pool == actual, 'accepted interface pool changed')
    for name in pool:
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts and name.startswith('_build/')
                and '/agda/src/' in name and name.endswith('.agdai'), 'unsupported cache path')


def accepted_phases(prior, pool, source, machine, old, sample_sha):
    require(prior['accepted'] and prior.get('finished_utc') and prior['status'] == 'complete'
            and prior['machine'] == machine and prior['checked_source'] == source
            and not prior['initial_problem2_proved'] and not prior['optimal_initial_pair_proved']
            and not prior['production_authorized'] and not prior['late_original_lower_and_upper_checked']
            and prior['conditional_sample_links_checked'] and prior['accepted_donor_unchanged']
            and len(prior['layouts']) == 1, 'accepted independent lower training predecessor required')
    layout = prior['layouts'][0]
    require(layout['prefix'] == PREFIX and layout['side'] == 'lower'
            and layout['selected_training'] == PRIOR_PARTS and not layout['held_out_checked']
            and layout['input_samples_sha256'] == sample_sha
            and layout['targets'] == ['Family', 'Part0', 'Part4599']
            and [c['part'] for c in layout['cases']] == PRIOR_PARTS,
            'exact accepted first-two training layout required')
    targets = [PREFIX + '.' + name for name in layout['targets']]
    phases = prior['phases']
    require([p['target'] for p in phases] == targets, 'three contiguous accepted phases required')
    for phase in phases:
        record = phase['record']
        require(record['accepted'] and record['exit_code'] == 0 and record['stop_reason'] is None
                and record.get('finished_utc') and record['own_target_cold']
                and record['source_unchanged'] and record['expected_source_matches']
                and record['source_sha256'] == record['expected_source_sha256'] == source['source_sha256']
                and record['root'] == str(old) and record['machine'] == machine['hostname']
                and record['executable_sha256'] == machine['agda_sha256']
                and record['argv'] == argv(machine, phase['target'])
                and 0 < record['cpu_limit_seconds'] <= 120 and record['rss_stop_threshold_gib'] == 1.5
                and phase['borrowed_interfaces_unchanged']
                and len(target_interfaces(pool, phase['target'])) == 1,
                'prior checked-source/compiler/cold-cache provenance differs')
    proof_folder = '/src/' + PREFIX.replace('.', '/') + '/'
    expected_proofs = {'Family.agdai', 'Part0.agdai', 'Part4599.agdai'}
    require({name.rsplit('/', 1)[-1] for name in pool if proof_folder in name
             and (name.rsplit('/', 1)[-1].startswith('Part')
                  or name.rsplit('/', 1)[-1] == 'Family.agdai')} == expected_proofs,
            'unreported generated proof interface present')
    for part in TRAINING[2:]:
        require(not target_interfaces(pool, PREFIX + '.Part' + str(part)), 'new training target is warm')
    require(digest_entries(pool) == prior['last_interface_pool_sha256'], 'reported pool hash differs')
    return phases


def validate_sources(old, current, layout, generated):
    """Every inherited generated dependency and every cached local module agrees."""
    old_generated = layout['generated_sha256']
    actual_generated = {name: assembly6.sha(old / name) for name in old_generated}
    require(actual_generated == old_generated, 'inherited generated source changed')
    require(all(generated.get(name) == digest for name, digest in old_generated.items()),
            'regenerated inherited source or dependency differs')
    for name, _ in source_files(current):
        if name.endswith(('.agda', '.agda-lib')):
            require((old / name).is_file() and assembly6.sha(old / name) == assembly6.sha(current / name),
                    'current main core differs from accepted source')


def validate_cached_sources(old, check, pool):
    for name in pool:
        source = name.split('/agda/', 1)[1][:-1]
        require((old / source).is_file() and (check / source).is_file()
                and assembly6.sha(old / source) == assembly6.sha(check / source),
                'cached module source missing or differs from new stage')


def cold_target(pool, target):
    require(not target_interfaces(pool, target), 'own target unexpectedly warm')


def run(args):
    current = Path.cwd().resolve()
    previous = args.previous.resolve()
    base = previous / 'results/initial-lower-training6'
    old = base / 'check'
    receipt = pinned(previous / 'results' / (previous.name.removeprefix('six-') + '.json'),
                     args.expected_receipt_sha256)
    outer_source = source_identity(previous)
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == 'eapiova' and machine['agda_sha256'] == args.expected_agda_sha256,
            'pinned desktop compiler required')
    validate_receipt(receipt, outer_source, previous, machine['hostname'])
    service = closed_worker(receipt)
    prior = pinned(base / 'report.json', args.expected_report_sha256)
    pool = pinned(base / 'interface-map.json', args.expected_map_sha256)
    donor_source = source_identity(old)
    validate_pool(pool, assembly6.interfaces(old))
    inherited = accepted_phases(prior, pool, donor_source, machine, old, args.expected_sample_sha256)
    sample_path = args.sample.absolute()
    chosen = load_training(sample_path, args.expected_sample_sha256)
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts and previous not in out.parents,
            'fresh private results output required')
    out.mkdir(parents=True)
    report = dict(format='othello-initial-training-resume6-v1', accepted=False, status='preparing',
        created_utc=utc(), machine=machine, predecessor_closed_service=service,
        predecessor_receipt_sha256=args.expected_receipt_sha256,
        predecessor_report_sha256=args.expected_report_sha256, predecessor_map_sha256=args.expected_map_sha256,
        donor_checked_source=donor_source, inherited_accepted_phases=inherited,
        inherited_targets=[p['target'] for p in inherited], selected_training=TRAINING,
        held_out_checked=False, input_samples=str(sample_path), input_samples_sha256=args.expected_sample_sha256,
        phases=[], kernel_cpu_seconds=0., accepted_parts=2, initial_problem2_proved=False,
        optimal_initial_pair_proved=False, production_authorized=False,
        scope='eight independent lower training checker facts and conditional links; no initial theorem')

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used = allocated(current.parent)
        free = shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free, checked_utc=utc(),
                                          reserved_extra_bytes=extra)
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'storage gate reached; accepted donor and logs preserved')

    # Include the entire private source copy, dependency/header/import growth,
    # and bounded interface/log growth before generation or borrowing anything.
    source_names = [name for name, _ in source_files(current)
                    if name.startswith('src/') or name == 'othello.agda-lib']
    source_bytes = sum((current / n).stat().st_blocks * 512 for n in source_names)
    cache_bytes = sum((old / n).stat().st_blocks * 512 for n in pool)
    generated_estimate = sum(len(c['text']) + 4096 for c in chosen['states'].values())
    generated_estimate += sum(len(c['body_text']) + 512 * len(c['dependencies']) + 16384
                              for c in chosen['cases'])
    estimate = source_bytes + cache_bytes + generated_estimate + 8 * 2**20 + 6 * 3 * 2**20
    report['preparation_estimate_bytes'] = estimate
    guard(estimate)
    check = out / 'check'
    check.mkdir()
    for name in source_names:
        destination = check / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current / name, destination)
    layout = emit(check, chosen, side='lower', prefix=PREFIX)
    layout.update(input_samples=str(sample_path), input_samples_sha256=args.expected_sample_sha256,
                  selected_training=TRAINING, held_out_checked=False)
    validate_sources(old, current, prior['layouts'][0], layout['generated_sha256'])
    validate_cached_sources(old, check, pool)
    # Reuse identical accepted source bytes with the original timestamps, so
    # saved-meta imports stay valid. No donor inode is linked into this root.
    copied_sources = set(prior['layouts'][0]['generated_sha256'])
    copied_sources.update(name.split('/agda/', 1)[1][:-1] for name in pool)
    for name in sorted(copied_sources):
        shutil.copy2(old / name, check / name)
        require((old / name).stat().st_ino != (check / name).stat().st_ino
                or (old / name).stat().st_dev != (check / name).stat().st_dev,
                'source copy is not private')
    for name, digest in pool.items():
        copy_interface(old / name, check / name, digest)
    source = source_identity(check)
    require(assembly6.interfaces(check) == pool, 'private interface copy differs')
    report.update(checked_source=source, layouts=[layout], last_interface_pool_sha256=digest_entries(pool),
                  borrowed_interface_map=pool, inherited_sources_reused=sorted(copied_sources))
    atomic_json(out / 'interface-map.json', pool)
    save()
    for index, part in enumerate(TRAINING[2:]):
        guard(3 * 2**20 + 8 * 2**20)
        require(assembly6.machine_identity(args.agda) == machine, 'compiler or machine changed')
        require(assembly6.sha(sample_path) == args.expected_sample_sha256, 'input sample changed')
        target = PREFIX + '.Part' + str(part)
        before = assembly6.interfaces(check)
        cold_target(before, target)
        remaining = args.kernel_cpu_limit - report['kernel_cpu_seconds']
        require(remaining > 1, 'new kernel CPU cap reached')
        record = run_job('target' + str(index), argv(machine, target), out / 'records', root=check,
            expected_source_sha256=source['source_sha256'], timeout=420, cpu_limit=min(120, remaining),
            rss_limit_gib=1.5, log_limit_mib=2, metadata=dict(target=target, own_target_cold=True,
                borrowed_interfaces_sha256=digest_entries(before), inherited_targets=report['inherited_targets'],
                input_samples_sha256=args.expected_sample_sha256, initial_problem2_proved=False))
        after = assembly6.interfaces(check)
        unchanged = all(after.get(n) == h for n, h in before.items())
        own = target_interfaces(after, target)
        input_unchanged = assembly6.sha(sample_path) == args.expected_sample_sha256
        phase = dict(target=target, record=record, borrowed_interfaces_unchanged=unchanged,
            checked_target_source_sha256=assembly6.sha(check / ('src/' + target.replace('.', '/') + '.agda')),
            interfaces_before_sha256=digest_entries(before), interfaces_after_sha256=digest_entries(after),
            own_interface={n: after[n] for n in own}, input_samples_unchanged=input_unchanged)
        report['phases'].append(phase)
        report['kernel_cpu_seconds'] += record['cpu_seconds']
        accepted = bool(record['accepted'] and unchanged and len(own) == 1 and input_unchanged)
        if accepted:
            report['accepted_parts'] += 1
        report.update(status='checking' if accepted else 'target-rejected',
                      last_interface_pool_sha256=digest_entries(after))
        atomic_json(out / 'interface-map.json', after)
        save()
        require(accepted, 'new lower training part or borrowed cache rejected: ' + target)
    require(source_identity(previous) == outer_source and source_identity(old) == donor_source
            and assembly6.interfaces(old) == pool, 'accepted predecessor changed')
    require(source_identity(check) == source and assembly6.sha(sample_path) == args.expected_sample_sha256,
            'new checked source or input changed')
    report.update(accepted=True, status='complete', finished_utc=utc(), conditional_sample_links_checked=True,
                  accepted_predecessor_unchanged=True, input_samples_unchanged=True)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output', 'sample'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-receipt-sha256', 'expected-report-sha256',
                 'expected-map-sha256', 'expected-sample-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--kernel-cpu-limit', type=float, default=1200)
    args = parser.parse_args()
    require(0 < args.kernel_cpu_limit <= 1200, 'bounded positive new kernel CPU limit required')
    run(args)


if __name__ == '__main__':
    main()
