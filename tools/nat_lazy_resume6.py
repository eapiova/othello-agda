#!/usr/bin/env python3
"""Continue only the pinned 53,217-row lazy numeric descendant in private copies.

AI-assisted orchestration; every assertion remains a safe Agda kernel check.
Historical source epochs stay distinct from each subsequent single-part epoch.
"""
import argparse
import copy
import hashlib
from pathlib import Path
import re
import shutil

import assembly6
from cache_resume6 import copy_interface
from compact_logs6 import archive
from indexed_wire_resume6 import pinned
from nat_descendant_resume6 import closed_worker
from nat_lazy_generator6 import generate, PREFIX
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def source_map(root):
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in source_files(root)}


def argv(machine, target, hierarchy=False):
    return [machine['agda_path'], '--no-libraries', '-i', 'src', '--safe',
            '--without-K', '--cubical-compatible', '--save-metas',
            'src/' + target.replace('.', '/') + '.agda', '+RTS',
            '-M2600M' if hierarchy else '-M1350M', '-c', '-s', '-RTS']


def interface_for(pool, target):
    suffix = '/' + target.replace('.', '/') + '.agdai'
    found = [(n, h) for n, h in pool.items() if n.endswith(suffix)]
    require(len(found) <= 1, 'ambiguous target interface: ' + target)
    return found[0] if found else None


def interface_source(name):
    require('/agda/' in name and name.endswith('.agdai'), 'unknown interface path')
    relative = name.split('/agda/', 1)[1]
    require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
            'unsafe interface path')
    require(relative.startswith('src/'), 'interface outside source tree')
    return relative[:-1]


def validate_phase(phase, epoch, machine, roots):
    rec = phase['record']
    name = phase['target'].rsplit('.', 1)[1]
    require(rec['accepted'] and rec['exit_code'] == 0 and rec['stop_reason'] is None
            and rec['source_unchanged'] and rec['expected_source_matches']
            and rec['source_sha256'] == rec['expected_source_sha256'] == epoch['source_sha256']
            and rec['root'] in roots and rec['executable_sha256'] == machine['agda_sha256']
            and rec['argv'] == argv(machine, phase['target'], name.startswith('Node') or name == 'Root')
            and phase['borrowed_interfaces_unchanged'], 'accepted phase provenance differs')


def validate_predecessor(prior, pool, source, machine, old):
    """Validate the two epochs independently; never relabel historical receipts."""
    layout = prior['layout']
    require(prior['format'] == 'othello-nat-lazy-repair6-v1' and prior['accepted']
            and prior['status'] == 'complete' and prior.get('finished_utc')
            and prior['accepted_parts'] == 243 and prior['reused_parts'] == 242
            and prior['repaired_original_conditional_export_checked']
            and prior['accepted_predecessor_unchanged']
            and not prior['initial_problem2_proved'] and not prior['production_authorized']
            and not prior['optimal_initial_pair_proved']
            and layout['parts'] == 267 and layout['rows'] == 53217
            and layout['hierarchy_nodes'] == 31 and layout['side'] == 'lower',
            'only the accepted lower descendant Part242 repair is supported')
    names = layout['targets']
    require(names[:268] == ['Family'] + ['Part' + str(i) for i in range(267)]
            and len(names) == 300 and len(set(names)) == 300 and names[-1] == 'Root'
            and all(re.fullmatch(r'Node[0-9]+', n) for n in names[268:-1]),
            'original bounded hierarchy target order differs')
    require(source == prior['checked_source'] and machine == prior['machine']
            and digest_entries(pool) == prior['last_interface_pool_sha256'], 'source/compiler/cache differs')
    inherited = prior['inherited_accepted_phases']
    expected = [PREFIX + '.' + n for n in names[:243]]
    require([p['target'] for p in inherited] == expected, 'inherited original prefix differs')
    roots = set(prior['accepted_root_paths'])
    for phase in inherited:
        validate_phase(phase, prior['original_checked_source'], machine, roots)
    repair = prior['repair']
    require(repair['part'] == 242 and repair['exported_linked_type_unchanged'], 'repair export differs')
    repair_targets = ['Othello.LazyIndexed6'] + repair['targets']
    expected_repair = [PREFIX + '.LazyFamily', PREFIX + '.RepairBridge']
    expected_repair += [PREFIX + '.StateEq' + str(j) for j in repair['dependencies']]
    expected_repair += [PREFIX + '.Part242']
    require(repair['targets'] == expected_repair and repair['dependencies'] == sorted(set(repair['dependencies']))
            and 242 in repair['dependencies'] and all(0 <= j < 267 for j in repair['dependencies'])
            and [p['target'] for p in prior['phases']] == repair_targets,
            'repair evidence order differs')
    for phase in prior['phases']:
        validate_phase(phase, source, machine, {str(old)})
    accepted = set(expected + repair_targets)
    for target in accepted:
        require(interface_for(pool, target) is not None, 'missing accepted proof interface: ' + target)
    for name in pool:
        path = interface_source(name)
        if path.startswith('src/' + PREFIX.replace('.', '/') + '/'):
            stem = Path(path).stem
            if re.fullmatch(r'(Family|Part[0-9]+|Node[0-9]+|Root|LazyFamily|RepairBridge|StateEq[0-9]+)', stem):
                require(PREFIX + '.' + stem in accepted, 'unaccepted future proof interface')
    return accepted


def expand_epochs(epochs):
    """Authenticate full historical maps and compact, lossless successor deltas."""
    maps, previous = [], {}
    for epoch in epochs:
        if 'sources' in epoch:
            current = dict(epoch['sources'])
        else:
            require('source_delta' in epoch, 'missing epoch source evidence')
            current = {**previous, **epoch['source_delta']}
        require(digest_entries(current) == epoch['identity']['source_sha256'],
                'epoch map digest differs')
        require(set(previous) <= set(current), 'epoch removed historical source')
        maps.append(current)
        previous = current
    return maps


def compact_epochs(epochs):
    maps = expand_epochs(epochs)
    result, previous = [], {}
    for epoch, current in zip(epochs, maps):
        item = {k: copy.deepcopy(v) for k, v in epoch.items()
                if k not in ('sources', 'source_delta')}
        item['source_delta'] = {n: h for n, h in current.items() if previous.get(n) != h}
        result.append(item)
        previous = current
    require(expand_epochs(result) == maps, 'compact epoch round trip differs')
    return result


def storage_stop(actual, log, expected):
    require(expected and hashlib.sha256(log).hexdigest() == expected
            and actual['accepted'] is False and actual['exit_code'] == 1
            and actual['stop_reason'] is None
            and log.rstrip().endswith(b'ValueError: storage gate reached'),
            'only an authenticated between-target storage stop may be resumed')


def validate_continuation(prior, pool, source, machine, old):
    """Retain accepted receipts from every epoch without relabelling them."""
    require(prior['format'] == 'othello-nat-lazy-resume6-v1' and not prior['accepted']
            and 243 <= prior['accepted_parts'] <= 267
            and not prior['initial_problem2_proved'] and not prior['production_authorized']
            and not prior['optimal_initial_pair_proved'] and not prior['root_checked'],
            'bounded unfinished lazy descendant required')
    repair_root = Path(prior['inherited_repair_phases'][0]['record']['root'])
    pins = prior.get('base_repair_pins', dict(root=str(repair_root),
        report=prior['predecessor_report_sha256'], map=prior['predecessor_map_sha256'],
        receipt=prior['predecessor_receipt_sha256']))
    require(Path(pins['root']) == repair_root, 'base repair root differs')
    repair_outer = repair_root.parents[2]
    repair_label = repair_outer.name.removeprefix('six-')
    receipt = pinned(repair_outer / 'results' / (repair_label + '.json'), pins['receipt'])
    require(receipt['accepted'] and receipt['source_unchanged'] and receipt['expected_source_matches']
            and receipt['source_sha256'] == source_identity(repair_outer)['source_sha256'],
            'base repair receipt differs')
    closed_worker(receipt)
    base = pinned(repair_root.parent / 'report.json', pins['report'])
    base_pool = pinned(repair_root.parent / 'interface-map.json', pins['map'])
    require(assembly6.interfaces(repair_root) == base_pool, 'base repair cache changed')
    accepted = validate_predecessor(base, base_pool, source_identity(repair_root), machine, repair_root)
    require(prior['inherited_accepted_phases'] == base['inherited_accepted_phases']
            and prior['inherited_repair_phases'] == base['phases']
            and prior['layout']['targets'] == base['layout']['targets']
            and prior['layout']['parts'] == 267 and prior['layout']['rows'] == 53217
            and source == prior['checked_source'] and machine == prior['machine']
            and digest_entries(pool) == prior['last_interface_pool_sha256'],
            'inherited facts or current source/cache differ')
    epochs = expand_epochs(prior['source_epochs'])
    require(epochs[0] == source_map(Path(base['heap_failure']['record']['record']['root']))
            and epochs[1] == source_map(repair_root) and epochs[-1] == source_map(old)
            and prior['source_epochs'][-1]['identity'] == source, 'epoch endpoints differ')
    for name, digest in base_pool.items():
        path = interface_source(name)
        require(pool.get(name) == digest and path in epochs[1]
                and epochs[-1].get(path) == epochs[1][path], 'accepted base source/cache changed')
    phases = prior.get('inherited_lazy_phases', []) + prior['phases']
    count = prior['accepted_parts']
    require([g['part'] for g in prior['generations']] == list(range(243, count)),
            'generation prefix differs')
    require([p['target'] for p in phases if p['kind'] == 'part']
            == [PREFIX + '.Part' + str(j) for j in range(243, count)], 'lazy part prefix differs')
    hierarchy = [p['target'] for p in phases if p['kind'] == 'hierarchy']
    require(hierarchy == [PREFIX + '.' + n for n in prior['layout']['targets'][268:268+len(hierarchy)]],
            'hierarchy prefix differs')
    helper_targets = {t for g in prior['generations'] for t in g['targets'][:-1]}
    for phase in phases:
        idx = phase['source_epoch']
        require(type(idx) is int and 2 <= idx < len(epochs) and phase['validated']
                and phase['kind'] in ('helper', 'part', 'hierarchy'), 'invalid phase epoch or kind')
        validate_phase(phase, prior['source_epochs'][idx]['identity'], machine,
                       set(prior['accepted_root_paths']) | {str(old)})
        require(phase['kind'] != 'helper' or phase['target'] in helper_targets,
                'unrecognised helper receipt')
        path = 'src/' + phase['target'].replace('.', '/') + '.agda'
        require(path in epochs[idx] and epochs[-1].get(path) == epochs[idx][path]
                and interface_for(pool, phase['target']), 'accepted lazy source/interface changed')
        accepted.add(phase['target'])
    for name in pool:
        path = interface_source(name)
        if path.startswith('src/' + PREFIX.replace('.', '/') + '/'):
            stem = Path(path).stem
            if re.fullmatch(r'(Family|Part[0-9]+|Node[0-9]+|Root|LazyFamily|RepairBridge|StateEq[0-9]+)', stem):
                require(PREFIX + '.' + stem in accepted, 'unaccepted future proof interface')
    return accepted, base, pins


def unchanged_cached_sources(root, before_sources, after_sources, pool, changed_target):
    """A cached module may neither change bytes nor import the changed proof."""
    require(interface_for(pool, changed_target) is None, 'changed target already cached')
    pattern = re.compile(r'\b(?:open\s+)?import\s+' + re.escape(changed_target) + r'(?=\s|$)', re.M)
    for name in pool:
        path = interface_source(name)
        require(path in before_sources and after_sources.get(path) == before_sources[path],
                'reused module source changed: ' + path)
        require(not pattern.search((root / path).read_text()),
                'cached module imports changed unchecked proof: ' + path)


def generate_next(check, part, accepted_parts, pool):
    require(part == accepted_parts and 243 <= part < 267, 'only the next descendant part may be generated')
    target = PREFIX + '.Part' + str(part)
    require(interface_for(pool, target) is None, 'next part unexpectedly accepted')
    before = source_map(check)
    repair = generate(check, part, accepted_parts=accepted_parts)
    after = source_map(check)
    allowed = set(repair['generated_sha256'])
    changed = 'src/' + target.replace('.', '/') + '.agda'
    require({n for n in before if before[n] != after.get(n)} <= {changed}
            and set(after) - set(before) <= allowed and not set(before) - set(after),
            'generator altered unrelated source')
    for name, digest in repair['generated_sha256'].items():
        require(after.get(name) == digest, 'generated helper differs')
    unchanged_cached_sources(check, before, after, pool, target)
    return repair, before, after


def helper_plan(repair, pool, accepted, before_sources, after_sources):
    reused, cold = [], []
    for target in repair['targets'][:-1]:
        found = interface_for(pool, target)
        if found:
            path = 'src/' + target.replace('.', '/') + '.agda'
            require(target in accepted and before_sources.get(path) == after_sources.get(path),
                    'helper reuse lacks accepted identical source')
            reused.append(dict(target=target, interface_path=found[0], interface_sha256=found[1],
                               source_sha256=after_sources[path]))
        else:
            require(target not in accepted, 'accepted helper interface missing')
            cold.append(target)
    return reused, cold


def run(args):
    current, previous = Path.cwd(), args.previous.resolve()
    base = previous / args.previous_results
    require(base.is_relative_to(previous / 'results'), 'predecessor results outside frozen root')
    label = previous.name.removeprefix('six-')
    actual = pinned(previous / 'results' / (label + '.json'), args.expected_receipt_sha256)
    outer_source = source_identity(previous)
    require(actual.get('finished_utc') and actual['source_unchanged']
            and actual['expected_source_matches']
            and actual['source_sha256'] == actual['expected_source_sha256'] == outer_source['source_sha256'],
            'terminal unchanged predecessor required')
    closed = closed_worker(actual)
    prior = pinned(base / 'report.json', args.expected_report_sha256)
    pool = pinned(base / 'interface-map.json', args.expected_map_sha256)
    old, machine = base / 'check', assembly6.machine_identity(args.agda)
    source = source_identity(old)
    require(machine['hostname'] == 'eapiova' and machine['agda_sha256'] == args.expected_agda_sha256
            and assembly6.interfaces(old) == pool, 'exact same-machine compiler/cache required')
    if prior['format'] == 'othello-nat-lazy-repair6-v1':
        require(actual['accepted'] and actual['exit_code'] == 0 and actual['stop_reason'] is None,
                'accepted repair predecessor required')
        accepted = validate_predecessor(prior, pool, source, machine, old)
        repair_base = prior
        base_pins = dict(root=str(old), report=args.expected_report_sha256,
                         map=args.expected_map_sha256, receipt=args.expected_receipt_sha256)
        inherited_lazy = []
        generations = []
        epochs = [dict(kind='inherited-original', identity=prior['original_checked_source'],
                       sources=source_map(Path(prior['heap_failure']['record']['record']['root']))),
                  dict(kind='accepted-repair', identity=source, sources=source_map(old))]
    else:
        storage_stop(actual, (previous / 'results' / (label + '.log')).read_bytes(),
                     args.expected_stop_log_sha256)
        accepted, repair_base, base_pins = validate_continuation(prior, pool, source, machine, old)
        inherited_lazy = copy.deepcopy(prior.get('inherited_lazy_phases', []) + prior['phases'])
        generations = copy.deepcopy(prior['generations'])
        epochs = prior['source_epochs']
    start_part = prior['accepted_parts']
    sources = source_map(old)
    for name, digest in prior['layout']['generated_sha256'].items():
        require(sources.get(name) == digest, 'pinned descendant source differs')
    for name, _ in source_files(current):
        if name.endswith(('.agda', '.agda-lib')) and name not in (
                'src/Tests/LazyIndexed6.agda', 'src/Everything6.agda'):
            require(sources.get(name) == assembly6.sha(current / name), 'shared authoritative source differs')
    # Verify the original source epoch against its untouched historical root.
    original_root = Path(repair_base['heap_failure']['record']['record']['root'])
    original_source = source_identity(original_root)
    require(original_source == prior['original_checked_source'], 'historical source epoch differs')
    original_sources = source_map(original_root)
    repaired_parts = {'src/' + PREFIX.replace('.', '/') + '/Part' + str(j) + '.agda'
                      for j in range(242, start_part)}
    for name, digest in original_sources.items():
        if name not in repaired_parts:
            require(sources.get(name) == digest, 'historical inherited module changed')
    original_pool = assembly6.interfaces(original_root)
    # The failed own target is absent; inherited cache proof bytes must be preserved.
    for name, digest in original_pool.items():
        require(pool.get(name) == digest, 'historical interface changed')
    unchanged_cached_sources(old, original_sources, sources, original_pool, PREFIX + '.Part242')
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts and not out.is_relative_to(previous),
            'fresh private continuation root required')
    out.mkdir(parents=True)
    report = dict(format='othello-nat-lazy-resume6-v1', accepted=False, status='preparing', created_utc=utc(),
        machine=machine, checked_source=source, layout=copy.deepcopy(prior['layout']),
        predecessor_closed_service=closed, predecessor_receipt_sha256=args.expected_receipt_sha256,
        predecessor_report_sha256=args.expected_report_sha256, predecessor_map_sha256=args.expected_map_sha256,
        inherited_accepted_phases=copy.deepcopy(prior['inherited_accepted_phases']),
        inherited_repair_phases=copy.deepcopy(repair_base['phases']),
        inherited_lazy_phases=inherited_lazy, base_repair_pins=base_pins,
        accepted_root_paths=prior['accepted_root_paths'] + [str(old)],
        original_checked_source=original_source, original_source_root=str(original_root),
        source_epochs=compact_epochs(epochs),
        reused_parts=start_part, accepted_parts=start_part, phases=[], helper_phases=[], part_phases=[], hierarchy_phases=[],
        generations=generations, reused_helpers=[], kernel_cpu_seconds=0., archived_logs=[], root_checked=False,
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='existing 267-part lower descendant only; safe lazy continuation and original hierarchy')

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used, free = allocated(current.parent), shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30, 'storage gate reached')

    estimate = sum((old / n).stat().st_blocks * 512 for n in sources)
    estimate += sum((old / n).stat().st_blocks * 512 for n in pool)
    guard(estimate + 20 * 2**20)
    check = out / 'check'
    check.mkdir()
    for name in sources:
        path = check / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old / name, path)
        require(path.stat().st_ino != (old / name).stat().st_ino
                or path.stat().st_dev != (old / name).stat().st_dev, 'source copy is not private')
    for name, digest in pool.items():
        copy_interface(old / name, check / name, digest)
    require(source_identity(check) == source and assembly6.interfaces(check) == pool, 'private copy differs')
    report.update(private_source_and_cache_bytes=estimate, last_interface_pool_sha256=digest_entries(pool))
    atomic_json(out / 'interface-map.json', pool)
    save()

    def check_target(target, kind):
        guard()
        remaining = args.kernel_cpu_limit - report['kernel_cpu_seconds']
        require(remaining > 1, 'nested CPU allowance exhausted')
        before = assembly6.interfaces(check)
        require(interface_for(before, target) is None, 'own target unexpectedly warm')
        epoch = source_identity(check)
        require(epoch == report['checked_source'], 'source changed outside generation epoch')
        require(assembly6.machine_identity(args.agda) == machine, 'compiler identity changed')
        hierarchy = kind == 'hierarchy'
        rec = run_job('lazy' + str(len(report['phases'])), argv(machine, target, hierarchy), out / 'records',
            root=check, expected_source_sha256=epoch['source_sha256'], timeout=args.wall_limit,
            cpu_limit=min(args.hierarchy_cpu_limit if hierarchy else args.part_cpu_limit, remaining),
            rss_limit_gib=3 if hierarchy else 1.5, log_limit_mib=args.log_limit_mib,
            metadata=dict(target=target, own_target_cold=True, source_epoch=len(report['source_epochs']) - 1,
                          reused_parts=start_part, initial_problem2_proved=False))
        after = assembly6.interfaces(check)
        unchanged = all(after.get(n) == h for n, h in before.items())
        valid = bool(rec['accepted'] and rec['exit_code'] == 0 and rec['stop_reason'] is None
                     and rec['source_unchanged'] and rec['expected_source_matches'] and unchanged
                     and source_identity(check) == epoch and interface_for(after, target))
        phase = dict(target=target, kind=kind, source_epoch=len(report['source_epochs']) - 1,
                     record=rec, borrowed_interfaces_unchanged=unchanged, validated=valid)
        report['phases'].append(phase)
        report[kind + '_phases'].append(phase)
        report['kernel_cpu_seconds'] += rec['cpu_seconds']
        if valid:
            accepted.add(target)
            if kind == 'part':
                report['accepted_parts'] += 1
            if target == PREFIX + '.Root':
                report['root_checked'] = True
        report.update(status='checking-' + kind if valid else kind + '-failed',
                      last_interface_pool_sha256=digest_entries(after))
        atomic_json(out / 'interface-map.json', after)
        save()
        require(valid, 'target or prior interface check failed: ' + target)
        log = out / 'records' / (rec['label'] + '.log')
        require(log.stat().st_size == rec['log_bytes'], 'accepted log size differs')
        row = archive(log, assembly6.sha(log))
        row.update(directory=str(log.parent), record_sha256=assembly6.sha(log.with_suffix('.json')))
        report['archived_logs'].append(row)
        save()

    for part in range(start_part, 267):
        guard(20 * 2**20)
        before_pool = assembly6.interfaces(check)
        repair, before_sources, after_sources = generate_next(check, part, report['accepted_parts'], before_pool)
        require(assembly6.interfaces(check) == before_pool, 'generation changed cache')
        reused, cold = helper_plan(repair, before_pool, accepted, before_sources, after_sources)
        epoch = source_identity(check)
        report['source_epochs'].append(dict(kind='lazy-part', part=part, identity=epoch,
            source_delta={n: h for n, h in after_sources.items() if before_sources.get(n) != h}))
        report['checked_source'] = epoch
        report['generations'].append(repair)
        report['layout']['generated_sha256'].update(repair['generated_sha256'])
        report['reused_helpers'].extend(dict(part=part, **row) for row in reused)
        save()
        for target in cold:
            check_target(target, 'helper')
        check_target(PREFIX + '.Part' + str(part), 'part')
    for name in prior['layout']['targets'][268:]:
        target = PREFIX + '.' + name
        require(assembly6.sha(check / ('src/' + target.replace('.', '/') + '.agda'))
                == sources['src/' + target.replace('.', '/') + '.agda'], 'hierarchy source changed')
        if target not in accepted:
            check_target(target, 'hierarchy')
    require(source_identity(previous) == outer_source and source_identity(old) == source
            and assembly6.interfaces(old) == pool and source_identity(original_root) == original_source
            and assembly6.interfaces(original_root) == original_pool, 'accepted predecessor changed')
    require(report['root_checked'] and report['accepted_parts'] == 267, 'descendant root remains unchecked')
    report.update(accepted=True, status='complete', finished_utc=utc(), descendant_original_lower_checked=True,
                  accepted_predecessor_unchanged=True)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-receipt-sha256', 'expected-report-sha256', 'expected-map-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--previous-results', type=Path, default=Path('results/nat-lazy-repair6'))
    parser.add_argument('--expected-stop-log-sha256')
    parser.add_argument('--kernel-cpu-limit', type=float, default=1600)
    parser.add_argument('--part-cpu-limit', type=float, default=120)
    parser.add_argument('--hierarchy-cpu-limit', type=float, default=180)
    parser.add_argument('--wall-limit', type=float, default=420)
    parser.add_argument('--log-limit-mib', type=float, default=2)
    args = parser.parse_args()
    require(all(getattr(args, name) > 0 for name in ('kernel_cpu_limit', 'part_cpu_limit', 'hierarchy_cpu_limit',
                                                    'wall_limit', 'log_limit_mib')), 'positive resource caps required')
    run(args)


if __name__ == '__main__':
    main()
