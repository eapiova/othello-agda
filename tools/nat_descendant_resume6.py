#!/usr/bin/env python3
"""Resume an exact numeric descendant prefix after a bounded resource stop.

This never changes prior proof sources, compiler flags or accepted interfaces,
and cannot be used to generate full initial-board production data.
"""
import argparse
from pathlib import Path
import shutil
import subprocess

import assembly6
from cache_resume6 import copy_interface
from indexed_wire_resume6 import pinned
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def closed_worker(receipt):
    """The worker exits 1 on rejection; the measured child may exit by signal."""
    unit = receipt['remote_unit']
    require(unit == 'othello6-' + receipt['label'] + '.service', 'predecessor unit label differs')
    proc = subprocess.run(['systemctl', '--user', 'show', unit, '-p', 'LoadState',
        '-p', 'ActiveState', '-p', 'SubState', '-p', 'MainPID', '-p', 'ControlPID', '-p', 'ExecMainStatus'],
        capture_output=True, text=True, timeout=15)
    state = dict(line.split('=', 1) for line in proc.stdout.splitlines() if '=' in line)
    require(proc.returncode in (0, 1) and state.get('LoadState') in ('loaded', 'not-found')
            and state.get('ActiveState') in ('inactive', 'failed')
            and state.get('SubState') in ('dead', 'failed')
            and state.get('MainPID') == state.get('ControlPID') == '0',
            'predecessor is still live or unobservable')
    if state['LoadState'] == 'loaded':
        require(state.get('ExecMainStatus') == ('0' if receipt['accepted'] else '1'),
                'closed worker exit differs from the measured acceptance')
    return state


def accepted_prefix(prior, pool, source, machine, old):
    """Require a contiguous accepted target prefix and no unreported proofs."""
    layout = prior['layout']
    require(layout['parts'] == 267 and layout['rows'] == 53217
            and layout['hierarchy_nodes'] == 31 and layout['targets'][-1] == 'Root',
            'only the complete existing descendant is supported')
    targets = ['Tests.NatDescendant6.' + n for n in layout['targets']]
    phases = prior.get('inherited_accepted_phases', []) + prior['phases']
    roots = {str(old)} | set(prior.get('accepted_root_paths', []))
    require([p['target'] for p in phases] == targets[:len(phases)], 'target order is not a prefix')
    accepted = []
    for index, phase in enumerate(phases):
        record = phase['record']
        name = phase['target'].rsplit('.', 1)[1]
        hierarchy = name.startswith('Node') or name == 'Root'
        expected_argv = [machine['agda_path'], '--no-libraries', '-i', 'src', '--safe',
            '--without-K', '--cubical-compatible', '--save-metas',
            'src/' + phase['target'].replace('.', '/') + '.agda', '+RTS',
            '-M2600M' if hierarchy else '-M1350M', '-c', '-s', '-RTS']
        require(record['source_unchanged'] and record['expected_source_matches']
                and record['source_sha256'] == record['expected_source_sha256'] == source['source_sha256']
                and record['root'] in roots
                and record['executable_sha256'] == machine['agda_sha256']
                and record['argv'] == expected_argv,
                'prior source/compiler provenance differs')
        require(phase['borrowed_interfaces_unchanged'], 'borrowed proof cache changed')
        if not record['accepted']:
            require(index == len(phases) - 1 and record['stop_reason'] == 'cpu-limit',
                    'only a final CPU-limited failed check can be retried unchanged')
            break
        require(record['exit_code'] == 0 and record['stop_reason'] is None,
                'accepted target lacks a successful exit')
        accepted.append(phase['target'])
    for target in targets:
        suffix = '/' + target.replace('.', '/') + '.agdai'
        require(any(name.endswith(suffix) for name in pool) == (target in accepted),
                'own proof interface does not match the recorded accepted prefix')
    require(prior['accepted_parts'] == sum(t.rsplit('.', 1)[1].startswith('Part') for t in accepted),
            'accepted part count differs')
    return targets, accepted


def run(args):
    current = Path.cwd()
    previous = args.previous.resolve()
    base = previous / args.previous_results
    label = previous.name.removeprefix('six-')
    actual = pinned(previous / 'results' / (label + '.json'), args.expected_previous_receipt_sha256)
    outer_source = source_identity(previous)
    require(actual.get('finished_utc') and actual['source_unchanged'] and actual['expected_source_matches']
            and outer_source['source_sha256'] == actual['source_sha256'],
            'a terminal unchanged predecessor is required')
    service = closed_worker(actual)
    prior = pinned(base / 'report.json', args.expected_previous_report_sha256)
    pool = pinned(base / 'interface-map.json', args.expected_previous_map_sha256)
    old = base / 'check'
    source = source_identity(old)
    machine = assembly6.machine_identity(args.agda)
    actual_pool = assembly6.interfaces(old)
    require(machine == prior['machine'] and machine['hostname'] == 'eapiova'
            and machine['agda_sha256'] == args.expected_agda_sha256
            and prior['checked_source'] == source
            and all(actual_pool.get(name) == digest for name, digest in pool.items())
            and digest_entries(pool) == prior['last_interface_pool_sha256'],
            'exact same-machine source and interface map required')
    require(not prior['initial_problem2_proved'] and not prior['production_authorized'],
            'full initial production is excluded')
    targets, accepted = accepted_prefix(prior, pool, source, machine, old)
    require(accepted and len(accepted) < len(targets), 'no unfinished accepted prefix to resume')
    # Authenticate every generated target against the original bounded layout.
    for name, digest in prior['layout']['generated_sha256'].items():
        require(assembly6.sha(old / name) == digest, 'generated descendant source changed')
    for name, _ in source_files(current):
        if name.endswith(('.agda', '.agda-lib')):
            require(assembly6.sha(old / name) == assembly6.sha(current / name), 'current core source differs')
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh private results required')
    out.mkdir(parents=True)
    report = dict(format='othello-nat-descendant-resume6-v1', accepted=False, status='preparing',
        created_utc=utc(), machine=machine, checked_source=source, layout=prior['layout'],
        predecessor_closed_service=service, predecessor_receipt_sha256=args.expected_previous_receipt_sha256,
        predecessor_report_sha256=args.expected_previous_report_sha256,
        predecessor_map_sha256=args.expected_previous_map_sha256,
        reused_targets=len(accepted), reused_parts=prior['accepted_parts'],
        uncertified_interfaces_excluded={name: digest for name, digest in actual_pool.items() if name not in pool},
        inherited_accepted_phases=[p for p in prior.get('inherited_accepted_phases', []) + prior['phases']
                                  if p['record']['accepted']],
        accepted_root_paths=sorted({str(old)} | set(prior.get('accepted_root_paths', []))),
        phases=[], accepted_parts=prior['accepted_parts'], kernel_cpu_seconds=0.,
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='exact numeric descendant prefix reuse and unfinished target checks; initial production excluded')

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used = allocated(current.parent)
        free = shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'storage gate reached; all accepted targets are preserved')

    estimate = sum((old / n).stat().st_blocks * 512 for n, _ in source_files(old))
    estimate += sum((old / n).stat().st_blocks * 512 for n in pool)
    guard(estimate + 16 * 2**20)
    check = out / 'check'
    check.mkdir()
    for name, _ in source_files(old):
        path = check / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old / name, path)
    for name, digest in pool.items():
        copy_interface(old / name, check / name, digest)
    require(source_identity(check) == source and assembly6.interfaces(check) == pool,
            'private source/cache copy differs')
    # Provenance of inherited phases retains its original path; new phases are
    # recorded under the fresh check root. The two lists remain distinct.
    report['private_source_and_cache_bytes'] = estimate
    report['last_interface_pool_sha256'] = digest_entries(pool)
    atomic_json(out / 'interface-map.json', pool)
    save()
    for index, target in enumerate(targets[len(accepted):]):
        guard()
        remaining = args.kernel_cpu_limit - report['kernel_cpu_seconds']
        require(remaining > 1, 'nested CPU cap reached')
        name = target.rsplit('.', 1)[1]
        hierarchy = name.startswith('Node') or name == 'Root'
        before = assembly6.interfaces(check)
        suffix = '/' + target.replace('.', '/') + '.agdai'
        require(not any(n.endswith(suffix) for n in before), 'own target unexpectedly warm')
        record = run_job('target' + str(index), [args.agda, '--no-libraries', '-i', 'src', '--safe',
            '--without-K', '--cubical-compatible', '--save-metas', 'src/' + target.replace('.', '/') + '.agda',
            '+RTS', '-M2600M' if hierarchy else '-M1350M', '-c', '-s', '-RTS'], out / 'records', root=check,
            expected_source_sha256=source['source_sha256'], timeout=420,
            cpu_limit=min(180 if hierarchy else 120, remaining), rss_limit_gib=3 if hierarchy else 1.5,
            log_limit_mib=2, metadata=dict(target=target, own_target_cold=True, reused_prefix=len(accepted),
                                        initial_problem2_proved=False))
        after = assembly6.interfaces(check)
        unchanged = all(after.get(n) == h for n, h in before.items())
        report['phases'].append(dict(target=target, record=record, borrowed_interfaces_unchanged=unchanged))
        report['kernel_cpu_seconds'] += record['cpu_seconds']
        if record['accepted'] and name.startswith('Part'):
            report['accepted_parts'] += 1
        report.update(status='checking-hierarchy' if hierarchy else 'checking-remaining-parts',
                      last_interface_pool_sha256=digest_entries(after))
        atomic_json(out / 'interface-map.json', after)
        save()
        require(record['accepted'] and unchanged, 'target or cache failed: ' + target)
    require(source_identity(previous) == outer_source and source_identity(old) == source
            and assembly6.interfaces(old) == actual_pool, 'accepted predecessor changed')
    report.update(accepted=True, status='complete', finished_utc=utc(),
                  descendant_original_lower_checked=True, accepted_predecessor_unchanged=True)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--previous-results', default='results/nat-descendant6')
    parser.add_argument('--output', type=Path, required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-previous-receipt-sha256',
                 'expected-previous-report-sha256', 'expected-previous-map-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--kernel-cpu-limit', type=float, default=1800)
    args = parser.parse_args()
    require(not Path(args.previous_results).is_absolute() and '..' not in Path(args.previous_results).parts
            and Path(args.previous_results).parts[0] == 'results', 'predecessor results path required')
    run(args)


if __name__ == '__main__':
    main()
