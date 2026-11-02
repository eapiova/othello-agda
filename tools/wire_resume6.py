#!/usr/bin/env python3
"""AI-assisted, same-desktop continuation of a storage-stopped wire prefix.

Run inside one outer study6/remote6 reservation. This tool neither reserves CPU
nor changes a ledger. Only remaining targets run; copied saved-meta interfaces
are evidence for a conditional wire pilot, never an INITIAL6 theorem.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess

import assembly6
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, build_lock, positive, run_job, utc
from wire_workflow6 import validate_targets

FORMAT = 'othello-wire-resume6-v1'
WIRE = 'othello-wire-pilot6-v1'
GIB = 1024**3


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pinned_json(path, expected):
    require(type(expected) is str and re.fullmatch('[0-9a-f]{64}', expected), 'invalid SHA pin')
    require(assembly6.sha(path) == expected, 'pinned artifact changed: ' + str(path))
    return json.loads(path.read_text())


def same_compiler(a, b):
    # A reboot does not change machine/compiler identity; every old receipt still
    # has to match the complete historical machine record, including boot_id.
    return all(a.get(k) == b.get(k) and a.get(k) for k in
               ('hostname', 'agda_path', 'agda_sha256', 'agda_version'))


def closed_service(receipt):
    unit = receipt.get('remote_unit')
    require(type(unit) is str and unit == 'othello6-' + receipt.get('label', '') + '.service'
            and re.fullmatch(r'othello6-[A-Za-z0-9._-]+\.service', unit), 'invalid previous service')
    result = subprocess.run(['systemctl', '--user', 'show', unit,
        '--property=LoadState,ActiveState,SubState,MainPID,ControlPID,ExecMainStatus'],
        capture_output=True, text=True, timeout=15)
    state = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    require(result.returncode == 0 and state.get('LoadState') == 'loaded' and
            state.get('ActiveState') in ('inactive', 'failed') and
            state.get('SubState') in ('dead', 'failed') and
            state.get('MainPID') == state.get('ControlPID') == '0' and
            state.get('ExecMainStatus') == str(receipt['exit_code']), 'previous service is not closed')
    return state


def interface_name(pool, target):
    suffix = '/' + target['path'].removeprefix('src/').removesuffix('.agda') + '.agdai'
    matches = [name for name in pool if name.endswith(suffix)]
    require(len(matches) == 1, 'missing or ambiguous own checked interface')
    return matches[0]


def command(machine, target):
    heap = 2500 if target['kind'] == 'assembly' else 1350
    return [machine['agda_path'], *assembly6.FLAGS, '--save-metas', '-i', 'src',
            target['path'], '+RTS', f'-M{heap}M', '-c', '-s', '-RTS']


def audit_record(phase, target, machine, source_hash, root, borrowed):
    record = phase.get('record', {})
    require(phase.get('target') == target and phase.get('changed_imports') == [] and
            record.get('format') == 'othello-job-v2' and record.get('accepted') is True and
            record.get('exit_code') == 0 and record.get('stop_reason') is None and
            all(record.get(k) is True for k in
                ('own_target_cold', 'source_unchanged', 'expected_source_matches')),
            'failed, modified or non-cold prefix target')
    require(record.get('machine') == machine and record.get('root') == str(root) and
            record.get('source_sha256') == record.get('expected_source_sha256') == source_hash and
            record.get('executable_sha256') == machine['agda_sha256'] and
            record.get('argv') == command(machine, target) and
            record.get('borrowed_interfaces_sha256') == digest_entries(borrowed),
            'prefix source/compiler/flags/cache mismatch')
    require(all(record.get(k) == v for k, v in target.items()), 'prefix target metadata changed')
    label = f"root{target['root_index']}-" + ('assembly' if target['kind'] == 'assembly'
                                            else f"part{target['part']}")
    require(record.get('label') == label, 'prefix label changed')
    for key in ('cpu_seconds', 'peak_rss_gib', 'cpu_limit_seconds', 'rss_stop_threshold_gib'):
        value = record.get(key)
        require(type(value) in (int, float) and math.isfinite(value) and value > 0,
                'missing or invalid prefix resource measurement')
    cpu, rss = record['cpu_seconds'], record['peak_rss_gib']
    require(cpu < positive(record.get('cpu_limit_seconds')) and
            rss < positive(record.get('rss_stop_threshold_gib')) and
            record['rss_stop_threshold_gib'] <= (3. if target['kind'] == 'assembly' else 1.5),
            'prefix exceeded measured resource bounds')
    require(record.get('interfaces_before') == len(borrowed) and
            record.get('interfaces_after') == len(borrowed) + 1 and
            record.get('cache_state') == dict(interfaces_before=len(borrowed),
                                             interfaces_after=len(borrowed)+1),
            'prefix has unsupported cache growth')
    return cpu


def audit_prefix(plan, report, generic, pool, *, machine, source_hash, root,
                 expected_parts, expected_targets, expected_pool_hash):
    require(plan.get('format') == report.get('format') == WIRE and
            report.get('phase') == 'training' and report.get('status') == 'checking' and
            report.get('accepted') is False and report.get('initial_theorem_proved') is False and
            report.get('production_authorized') is False, 'wrong stopped wire report')
    require(type(plan.get('roots')) is list and len(plan['roots']) == 1, 'single root required')
    targets = validate_targets(plan)
    require(len(targets) == expected_targets and 0 < expected_parts < len(targets) - 1,
            'wrong target or prefix count')
    require(report.get('machine') == machine and report.get('source_sha256') == source_hash and
            report.get('borrowed_interfaces_sha256') == digest_entries(generic),
            'prefix report source/compiler/generic cache mismatch')
    phases = report.get('phases')
    require(type(phases) is list and len(phases) == expected_parts,
            'requires exact consecutive accepted prefix')
    require(digest_entries(pool) == expected_pool_hash, 'current prefix pool changed')
    borrowed, cpu, interfaces = dict(generic), 0., []
    for phase, target in zip(phases, targets):
        cpu += audit_record(phase, target, machine, source_hash, root, borrowed)
        name = interface_name(pool, target)
        require(name not in borrowed, 'duplicate or warm prefix target')
        borrowed[name] = pool[name]
        interfaces.append(dict(target=target['path'], path=name, sha256=pool[name]))
        # Its bytes are authenticated by the successor's borrowed digest. The
        # externally pinned final pool authenticates the last prefix target.
    require(borrowed == pool, 'unsupported extra interfaces outside accepted prefix')
    require(math.isclose(cpu, positive(report.get('cpu_seconds')), rel_tol=1e-9, abs_tol=1e-6),
            'prefix CPU total changed')
    return targets, interfaces


def copy_private(source, destination, expected, *, writable=False):
    require(not source.is_symlink() and source.is_file() and assembly6.sha(source) == expected,
            'copy donor changed or is not a regular file')
    require(not destination.exists() and not destination.is_symlink(), 'refusing cache overwrite')
    before = source.stat()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if writable:
        destination.chmod(destination.stat().st_mode | stat.S_IWUSR)
    after, copied = source.stat(), destination.stat()
    require(assembly6.sha(destination) == expected and assembly6.sha(source) == expected and
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and
            copied.st_mtime_ns == before.st_mtime_ns and
            (copied.st_dev, copied.st_ino) != (before.st_dev, before.st_ino),
            'copy2 did not preserve isolated bytes and source mtime')


def storage_gate(study_root):
    used, free = allocated(study_root), shutil.disk_usage(study_root).free
    require(used < 10*GIB and free >= 100*GIB,
            'desktop storage gate reached; accepted checkpoints preserved')
    return dict(allocated_study_bytes=used, free_bytes=free, checked_utc=utc(),
                study_limit_bytes=10*GIB, minimum_free_bytes=100*GIB)


def file_state(root):
    return {name: dict(sha256=assembly6.sha(root/name), mtime_ns=(root/name).stat().st_mtime_ns)
            for name, _ in source_files(root)}


def pool_state(root):
    return {name: dict(sha256=digest, mtime_ns=(root/name).stat().st_mtime_ns)
            for name, digest in assembly6.interfaces(root).items()}


def preserved(check):
    """A damaged historical source must still leave a rejected final report."""
    try:
        return bool(check())
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return False


def run(args):
    previous, prepared, donor = (args.previous_root.resolve(), args.prepared.resolve(), args.donor.resolve())
    output, study = args.output.resolve(), args.study_root.resolve()
    require(not output.exists() and 'results' in output.parts and
            not any(parent == output or parent in output.parents for parent in (previous, prepared, donor))
            and (study == output or study in output.parents) and study in previous.parents and
            study in donor.parents, 'fresh same-desktop isolated results output required')
    require(socket.gethostname() == args.expected_hostname, 'cross-machine continuation forbidden')
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == args.expected_hostname and
            machine['agda_sha256'] == args.expected_agda_sha256, 'exact desktop/compiler required')
    receipt = pinned_json(args.previous_receipt, args.expected_previous_receipt_sha256)
    report = pinned_json(args.previous_report, args.expected_previous_report_sha256)
    plan = pinned_json(prepared/'plan.json', args.expected_plan_sha256)
    require(receipt.get('format') == 'othello-job-v2' and receipt.get('root') == str(previous) and
            receipt.get('machine') == machine['hostname'] and receipt.get('finished_utc') and
            receipt.get('exit_code') == 1 and receipt.get('accepted') is False and
            receipt.get('stop_reason') is None and receipt.get('source_unchanged') is True and
            receipt.get('expected_source_matches') is True and
            receipt.get('source_sha256') == receipt.get('expected_source_sha256') == args.expected_previous_source_sha256,
            'closed unchanged failed outer receipt required')
    service = closed_service(receipt)
    root = Path(report.get('check_root', '')).resolve()
    require(previous in root.parents and previous in prepared.parents and
            previous in args.previous_report.resolve().parents and
            previous in args.previous_receipt.resolve().parents, 'previous artifacts escape desktop snapshot')
    require((previous/'SNAPSHOT.json').is_file() and (root/'SNAPSHOT.json').is_file() and
            (donor/'SNAPSHOT.json').is_file(), 'frozen source SNAPSHOTs required')
    old_identity, donor_identity = source_identity(root), source_identity(donor)
    require(source_identity(previous)['source_sha256'] == args.expected_previous_source_sha256 and
            old_identity['source_sha256'] == args.expected_check_source_sha256 and
            donor_identity['source_sha256'] == args.expected_donor_source_sha256 and
            report.get('donor_source') == donor_identity and
            report.get('plan_sha256') == args.expected_plan_sha256 and
            same_compiler(report.get('machine', {}), machine), 'source/donor/plan/compiler identity mismatch')
    donor_pool, pool = assembly6.interfaces(donor), assembly6.interfaces(root)
    generic = {n: d for n, d in donor_pool.items() if '/src/Tests/' not in n}
    require(generic and digest_entries(generic) == args.expected_generic_interfaces_sha256,
            'generic donor cache changed')
    targets, reused_interfaces = audit_prefix(plan, report, generic, pool,
        machine=report['machine'], source_hash=old_identity['source_sha256'], root=root,
        expected_parts=args.expected_prefix_parts, expected_targets=args.expected_targets,
        expected_pool_hash=args.expected_prefix_interfaces_sha256)
    for target in targets:
        name = target['path']
        require(assembly6.sha(prepared/name) == plan['generated_hashes'][name] == assembly6.sha(root/name)
                and (prepared/name).stat().st_size == target['source_bytes'], 'generated source changed')
    expected_sources = {n: assembly6.sha(donor/n) for n, _ in source_files(donor)
                        if not n.startswith('src/Tests/') and n.endswith(('.agda', '.agda-lib'))}
    expected_sources.update(plan['generated_hashes'])
    require(expected_sources == {n: assembly6.sha(root/n) for n, _ in source_files(root)},
            'checking sources differ from exact generic donor and generated plan')
    protected = {p: assembly6.sha(p) for p in (args.previous_receipt, args.previous_report,
                 prepared/'plan.json', previous/'SNAPSHOT.json', root/'SNAPSHOT.json', donor/'SNAPSHOT.json')}
    old_sources, old_pool, donor_sources, donor_cache = file_state(root), pool_state(root), file_state(donor), pool_state(donor)
    storage = storage_gate(study)
    output.mkdir(parents=True); fresh = output/'check'; fresh.mkdir()
    result = dict(format=FORMAT, status='copying', accepted=False, created_utc=utc(),
        machine=machine, check_root=str(fresh), source_sha256=old_identity['source_sha256'],
        plan_sha256=args.expected_plan_sha256, previous_receipt_sha256=args.expected_previous_receipt_sha256,
        previous_report_sha256=args.expected_previous_report_sha256,
        previous_source_sha256=args.expected_previous_source_sha256,
        donor_source_sha256=args.expected_donor_source_sha256,
        generic_interfaces_sha256=args.expected_generic_interfaces_sha256,
        reused_pool_sha256=args.expected_prefix_interfaces_sha256, closed_previous_service=service,
        reused_phases=report['phases'], reused_interfaces=reused_interfaces, new_phases=[],
        reused_kernel_cpu_seconds=report['cpu_seconds'], previous_outer_cpu_seconds=receipt['cpu_seconds'],
        new_kernel_cpu_seconds=0., cpu_seconds=0., kernel_cpu_budget=args.kernel_cpu_budget,
        expected_targets=len(targets), completed_targets=len(report['phases']),
        last_storage_gate=storage, interface_policy='private copy2; original bytes and mtimes; same desktop/compiler',
        scope='conditional single wire root; no whole initial-position theorem',
        initial_problem2_proved=False, initial_theorem_proved=False, production_authorized=False)
    def save():
        atomic_json(output/'report.json', result)
    save()
    try:
        for name, item in old_sources.items():
            copy_private(root/name, fresh/name, item['sha256'])
        copy_private(root/'SNAPSHOT.json', fresh/'SNAPSHOT.json', protected[root/'SNAPSHOT.json'])
        for name, digest in pool.items():
            copy_private(root/name, fresh/name, digest, writable=True)
        require(source_identity(fresh) == old_identity and assembly6.interfaces(fresh) == pool,
                'fresh private source/cache copy changed')
        result['status'] = 'checking'; save()
        for target in targets[len(report['phases']):]:
            result['last_storage_gate'] = storage_gate(study); save()
            left = args.kernel_cpu_budget - result['new_kernel_cpu_seconds']
            if left < 3:
                result['status'] = 'cpu-stop'; break
            with build_lock(fresh):
                before = assembly6.interfaces(fresh)
                require(before == pool, 'private pool changed between checks')
                suffix = '/' + target['path'].removeprefix('src/').removesuffix('.agda') + '.agdai'
                require(not any(n.endswith(suffix) for n in before), 'remaining own target is not cold')
                require(assembly6.machine_identity(args.agda) == machine, 'compiler changed during continuation')
                assembly = target['kind'] == 'assembly'
                cap = min(left - 1, args.assembly_cpu_limit if assembly else args.part_cpu_limit)
                label = f"root{target['root_index']}-" + ('assembly' if assembly else f"part{target['part']}")
                record = run_job(label, command(machine, target), output/'records', root=fresh,
                    expected_source_sha256=old_identity['source_sha256'], cpu_limit=cap,
                    timeout=cap*2+30, rss_limit_gib=3. if assembly else 1.5, log_limit_mib=2,
                    metadata=dict(machine=machine, own_target_cold=True,
                        borrowed_interfaces_sha256=digest_entries(before), **target), locked=True)
                result['new_kernel_cpu_seconds'] += record['cpu_seconds']
                result['cpu_seconds'] = result['new_kernel_cpu_seconds']
                after = assembly6.interfaces(fresh)
                changed = sorted(n for n, d in before.items() if after.get(n) != d)
                phase = dict(target=target, record=record, changed_imports=changed)
                result['new_phases'].append(phase)
                # Persist failures too, but never make their cache reusable.
                result['status'] = 'check-failed'; save()
                if record.get('accepted') is not True or changed:
                    break
                audit_record(phase, target, machine, old_identity['source_sha256'], fresh, before)
                own = interface_name(after, target)
                require(own not in before and set(after) == set(before) | {own},
                        'new target emitted unsupported interfaces')
                pool = after
                phase['own_interface'] = dict(path=own, sha256=after[own])
                phase['accepted'] = True
                result['completed_targets'] += 1
                result['status'] = 'checking'; save()
                print(json.dumps(dict(label=label, accepted=True, cpu_seconds=record['cpu_seconds'])), flush=True)
        result['accepted'] = result['completed_targets'] == len(targets) and result['status'] == 'checking'
        if result['accepted']:
            result['status'] = 'complete'
    except Exception as error:
        result.update(status='driver-failed', accepted=False, error_type=type(error).__name__, error=str(error))
    # Historical receipts, source bytes/mtimes and complete old caches are
    # checked even after a storage gate or kernel failure.
    result['historical_artifacts_unchanged'] = preserved(lambda: all(assembly6.sha(p) == d for p, d in protected.items()))
    result['previous_sources_unchanged'] = preserved(lambda: file_state(root) == old_sources)
    result['previous_interfaces_unchanged'] = preserved(lambda: pool_state(root) == old_pool)
    result['donor_sources_unchanged'] = preserved(lambda: file_state(donor) == donor_sources)
    result['donor_interfaces_unchanged'] = preserved(lambda: pool_state(donor) == donor_cache)
    result['outer_source_unchanged'] = preserved(lambda: source_identity(previous)['source_sha256'] == args.expected_previous_source_sha256)
    result['generated_sources_unchanged'] = preserved(lambda: all(assembly6.sha(prepared/n) == d for n, d in plan['generated_hashes'].items()))
    result['source_unchanged'] = preserved(lambda: source_identity(fresh) == old_identity)
    if not all(result[k] for k in ('historical_artifacts_unchanged', 'previous_sources_unchanged',
                'previous_interfaces_unchanged', 'donor_sources_unchanged', 'donor_interfaces_unchanged',
                'outer_source_unchanged', 'generated_sources_unchanged', 'source_unchanged')):
        result.update(accepted=False, status='preservation-failed')
    result.update(final_interfaces_sha256=digest_entries(assembly6.interfaces(fresh)), finished_utc=utc())
    save()
    return result['accepted']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous-root', 'previous-receipt', 'previous-report', 'prepared', 'donor', 'study-root', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    for name in ('agda', 'expected-hostname', 'expected-agda-sha256', 'expected-previous-receipt-sha256',
                 'expected-previous-report-sha256', 'expected-previous-source-sha256', 'expected-plan-sha256',
                 'expected-check-source-sha256', 'expected-donor-source-sha256',
                 'expected-generic-interfaces-sha256', 'expected-prefix-interfaces-sha256'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--expected-prefix-parts', type=int, default=168)
    parser.add_argument('--expected-targets', type=int, default=268)
    parser.add_argument('--kernel-cpu-budget', type=positive, required=True)
    parser.add_argument('--part-cpu-limit', type=positive, default=240.)
    parser.add_argument('--assembly-cpu-limit', type=positive, default=240.)
    args = parser.parse_args()
    if not 0 < args.expected_prefix_parts < args.expected_targets - 1:
        parser.error('prefix must leave at least one part and assembly')
    return 0 if run(args) else 1


if __name__ == '__main__':
    raise SystemExit(main())
