#!/usr/bin/env python3
"""Resume a storage-stopped global sample alignment without rechecking its prefix."""
import argparse
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
from indexed_wire_resume6 import pinned
from initial_training_resume6 import cold_target, target_interfaces, validate_pool
from nat_descendant_resume6 import closed_worker
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def argv(machine, target):
    return [machine['agda_path'], '--no-libraries', '-i', 'src', '--safe', '--without-K',
            '--cubical-compatible', '--save-metas', 'src/' + target.replace('.', '/') + '.agda',
            '+RTS', '-M2700M', '-c', '-s', '-RTS']


def accepted_prefix(prior, pool, source, machine, old, roots=None):
    layout = prior['layout']
    if layout['format'] == 'othello-initial-global-named6-v1':
        from initial_lazy_samples6 import selection
        side = layout['side']
        require(side in ('lower', 'upper'), 'named sample direction required')
        rows, chunks, routes = (3047, 2702, 85) if side == 'lower' else (3125, 3359, 105)
        helpers = ['StateMap' + str(i) for i in range(255)] + ['BodyMap255', 'OwnedMap256']
        parts = selection(side)['selected']
        expected_targets = helpers + ['Model'] + ['Routes' + str(i) for i in range(routes)]
        expected_targets += ['Part' + str(i) for i in parts] + ['Root']
        require(layout['owned_rows'] == rows and layout['needed_chunks'] == chunks
                and layout['owned_parts'] == parts and layout['targets'] == expected_targets
                and [h['target'] for h in layout['map_helpers']] == helpers
                and layout['map_batch'] == layout['route_batch'] == 32
                and layout['prefix'] == 'Tests.InitialGlobalNamed' + side.title(),
                'exact existing named sample layout required')
    else:
        require(layout['format'] == 'othello-initial-global-shards6-v1' and layout['side'] == 'upper'
                and layout['owned_rows'] == 3125 and layout['needed_chunks'] == 3359
                and len(layout['owned_parts']) == 16 and len(layout['targets']) == 123
                and layout['targets'][-1] == 'Root', 'exact existing upper sample layout required')
    targets = [layout['prefix'] + '.' + name for name in layout['targets']]
    phases = prior.get('inherited_accepted_phases', []) + prior['phases']
    roots = {str(old)} if roots is None else roots
    require(0 < len(phases) < len(targets) and [p['target'] for p in phases] == targets[:len(phases)]
            and prior['selected_targets'] == layout['targets'], 'contiguous incomplete accepted prefix required')
    for phase in phases:
        record = phase['record']
        require(record['accepted'] and record['exit_code'] == 0 and record['stop_reason'] is None
                and record['source_unchanged'] and record['expected_source_matches'] and record['own_target_cold']
                and record['source_sha256'] == record['expected_source_sha256'] == source['source_sha256']
                and record['root'] in roots
                and record['executable_sha256'] == machine['agda_sha256']
                and record['argv'] == argv(machine, phase['target']) and record['machine'] == machine['hostname']
                and phase['borrowed_interfaces_unchanged'], 'accepted prefix source/compiler/flags differ')
    for i, target in enumerate(targets):
        require(len(target_interfaces(pool, target)) == (1 if i < len(phases) else 0),
                'unreported or missing proof interface')
    require(abs(sum(p['record']['cpu_seconds'] for p in phases) - prior['assembly_cpu_seconds']) < 1e-6,
            'inherited CPU accounting differs')
    return targets, phases


def run(args):
    current, previous = Path.cwd().resolve(), args.previous.resolve()
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == 'eapiova' and machine['agda_sha256'] == args.expected_agda_sha256,
            'exact same desktop compiler required')
    outer = source_identity(previous)
    actual = pinned(previous / 'results' / (previous.name.removeprefix('six-') + '.json'),
                    args.expected_receipt_sha256)
    require(actual.get('finished_utc') and not actual['accepted'] and actual['exit_code'] == 1
            and actual['stop_reason'] is None and actual['source_unchanged'] and actual['expected_source_matches']
            and actual['source_sha256'] == actual['expected_source_sha256'] == outer['source_sha256']
            and actual['root'] == str(previous) and actual['machine'] == machine['hostname'],
            'terminal unchanged storage-stop receipt required')
    service = closed_worker(actual)
    base = previous / args.previous_results
    old = base / 'check'
    prior = pinned(base / 'report.json', args.expected_report_sha256)
    pool = pinned(base / 'interface-map.json', args.expected_map_sha256)
    source_old = source_identity(old)
    require(not prior['accepted'] and prior['status'] == 'checking' and prior['machine'] == machine
            and prior['checked_source'] == source_old and prior['sample_parts_rechecked'] == 0
            and not prior['initial_problem2_proved'] and not prior['production_authorized'],
            'exact incomplete storage-stopped pilot required')
    validate_pool(pool, assembly6.interfaces(old))
    require(digest_entries(pool) == prior['last_interface_pool_sha256'], 'prefix pool hash differs')
    guard_old = prior['last_storage_gate']
    require(guard_old['allocated_study_bytes'] + guard_old['reserved_extra_bytes'] >= 10 * 2**30
            or guard_old['free_bytes'] - guard_old['reserved_extra_bytes'] < 100 * 2**30,
            'predecessor did not stop at its storage guard')
    roots = {p['record']['root'] for p in prior.get('inherited_accepted_phases', []) + prior['phases']}
    require(str(old) in roots, 'current predecessor has no checked phase')
    for path in roots:
        checked = Path(path).resolve()
        require(current.parent in checked.parents and str(checked) == path
                and source_identity(checked) == source_old,
                'inherited source root is outside the study or differs')
    targets, inherited = accepted_prefix(prior, pool, source_old, machine, old, roots)
    for name, digest in prior['layout']['generated_sha256'].items():
        require(assembly6.sha(old / name) == digest, 'generated prefix source differs')
    out = args.output.resolve()
    require(not out.exists() and current in out.parents and 'results' in out.parts, 'fresh private resume required')
    out.mkdir(parents=True)
    report = dict(prior)
    report.update(format='othello-initial-shards-resume6-v1', created_utc=utc(), status='preparing',
        predecessor_closed_service=service, predecessor_receipt_sha256=args.expected_receipt_sha256,
        predecessor_report_sha256=args.expected_report_sha256, predecessor_map_sha256=args.expected_map_sha256,
        inherited_accepted_phases=inherited, phases=[], reused_targets=len(inherited),
        accepted_targets_rechecked=0, current_cpu_seconds=0., inherited_checked_source=source_old)

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used, free = allocated(current.parent), shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free,
                                          reserved_extra_bytes=extra, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'resume storage gate reached; accepted prefix preserved')

    files = [name for name, _ in source_files(old)]
    guard(sum((old / n).stat().st_blocks * 512 for n in files + list(pool)) + 16 * 2**20)
    check = out / 'check'
    check.mkdir()
    for name in files:
        destination = check / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old / name, destination)
    for name, digest in pool.items():
        copy_interface(old / name, check / name, digest)
    source = source_identity(check)
    require(source == source_old and assembly6.interfaces(check) == pool, 'private prefix copy differs')
    report['checked_source'] = source
    atomic_json(out / 'interface-map.json', pool)
    save()
    for target in targets[len(inherited):]:
        guard(8 * 2**20)
        before = assembly6.interfaces(check)
        cold_target(before, target)
        remaining = args.cpu_limit - report['current_cpu_seconds']
        require(remaining > 1, 'resume CPU cap reached')
        record = run_job('target' + str(len(report['phases'])), argv(machine, target), out / 'records',
            root=check, expected_source_sha256=source['source_sha256'], timeout=420,
            cpu_limit=min(60, remaining), rss_limit_gib=3, log_limit_mib=2,
            metadata=dict(target=target, own_target_cold=True, initial_problem2_proved=False))
        after = assembly6.interfaces(check)
        unchanged = all(after.get(n) == h for n, h in before.items())
        report['phases'].append(dict(target=target, record=record, borrowed_interfaces_unchanged=unchanged,
                                     parts=prior['layout']['owned_parts']))
        report['current_cpu_seconds'] += record['cpu_seconds']
        report['assembly_cpu_seconds'] += record['cpu_seconds']
        report.update(status='checking' if record['accepted'] and unchanged else 'target-rejected',
                      last_interface_pool_sha256=digest_entries(after))
        atomic_json(out / 'interface-map.json', after)
        save()
        require(record['accepted'] and unchanged, 'resumed target rejected: ' + target)
    require(source_identity(previous) == outer and source_identity(old) == source_old
            and assembly6.interfaces(old) == pool and source_identity(check) == source,
            'accepted prefix or current source changed')
    report.update(accepted=True, status='complete', finished_utc=utc(), accepted_donor_unchanged=True,
        global_lookup_alignment_checked=True, global_self_alignment_measured=True)
    if 'assembly_forecast' in prior:
        prediction = prior['assembly_forecast']['predicted_nested_cpu_seconds']
        error = abs(report['assembly_cpu_seconds'] - prediction) / prediction
        report['assembly_forecast_residual'] = dict(complete=True, predicted_nested_cpu_seconds=prediction,
            measured_nested_cpu_seconds=report['assembly_cpu_seconds'], relative_error=error,
            within_30_percent=error <= .30, whole_workflow_validated=False)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--previous-results', default='results/initial-upper-holdout-global-shards6',
        choices=('results/initial-upper-holdout-global-shards6','results/initial-upper-shards-resume6',
                 'results/initial-lower-global-named6','results/initial-upper-global-named6'))
    for name in ('agda', 'expected-agda-sha256', 'expected-receipt-sha256',
                 'expected-report-sha256', 'expected-map-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--cpu-limit', type=float, default=400)
    args = parser.parse_args()
    require(0 < args.cpu_limit <= 600, 'bounded remaining CPU budget required')
    run(args)


if __name__ == '__main__':
    main()
