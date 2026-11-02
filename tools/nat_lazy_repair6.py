#!/usr/bin/env python3
"""Check a lazy replacement for one heap-exhausted descendant part.

All accepted original proofs/data stay intact. The new conditional export has
the original type and is bridged by separately kernel-checked vector equalities.
This finite experiment does not authorize or generate initial-board production.
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
from nat_descendant_resume6 import accepted_prefix, closed_worker
from nat_lazy_generator6 import generate, PREFIX
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require


def heap_prefix(prior, pool, source, machine, old, base):
    failed = prior['phases'][-1]
    rec = failed['record']
    expected = PREFIX + '.Part' + str(prior['accepted_parts'])
    require(failed['target'] == expected and rec['accepted'] is False
            and rec['exit_code'] == 251 and rec['stop_reason'] is None
            and rec['source_unchanged'] and rec['expected_source_matches']
            and rec['source_sha256'] == rec['expected_source_sha256'] == source['source_sha256']
            and rec['executable_sha256'] == machine['agda_sha256'], 'a recorded next-part heap failure is required')
    expected_argv = [machine['agda_path'], '--no-libraries', '-i', 'src', '--safe',
        '--without-K', '--cubical-compatible', '--save-metas',
        'src/' + expected.replace('.', '/') + '.agda', '+RTS', '-M1350M', '-c', '-s', '-RTS']
    require(rec['argv'] == expected_argv, 'heap-failure compiler flags differ')
    log = base / 'records' / (rec['label'] + '.log')
    require(log.stat().st_size == rec['log_bytes'] and 'agda: Heap exhausted;' in log.read_text()
            and '1415577600 bytes (1350 MB)' in log.read_text(), 'exact heap exhaustion log required')
    accepted = copy.deepcopy(prior)
    accepted['phases'].pop()
    targets, prefix = accepted_prefix(accepted, pool, source, machine, old)
    require(targets[len(prefix)] == expected, 'failed module is not the next target')
    return prefix, dict(record=failed, log_sha256=assembly6.sha(log))


def run(args):
    current = Path.cwd()
    previous = args.previous.resolve()
    base = previous / 'results/nat-final6'
    label = previous.name.removeprefix('six-')
    actual = pinned(previous / 'results' / (label + '.json'), args.expected_receipt_sha256)
    outer_source = source_identity(previous)
    require(actual.get('finished_utc') and actual['source_unchanged'] and actual['expected_source_matches']
            and outer_source['source_sha256'] == actual['source_sha256'], 'closed unchanged predecessor required')
    closed = closed_worker(actual)
    prior = pinned(base / 'report.json', args.expected_report_sha256)
    pool = pinned(base / 'interface-map.json', args.expected_map_sha256)
    old = base / 'check'
    source = source_identity(old)
    machine = assembly6.machine_identity(args.agda)
    require(machine == prior['machine'] and machine['hostname'] == 'eapiova'
            and machine['agda_sha256'] == args.expected_agda_sha256
            and prior['checked_source'] == source and assembly6.interfaces(old) == pool
            and digest_entries(pool) == prior['last_interface_pool_sha256'], 'exact checked predecessor required')
    prefix, failed = heap_prefix(prior, pool, source, machine, old, base)
    require(prior['accepted_parts'] == 242 and not prior['initial_problem2_proved']
            and not prior['production_authorized'], 'only the observed 242-part descendant prefix is supported')
    for name, digest in prior['layout']['generated_sha256'].items():
        require(assembly6.sha(old / name) == digest, 'original generated source differs')
    # The new checker itself already has a cold acceptance with this compiler.
    proof = args.lazy_proof.resolve()
    proof_label = proof.name.removeprefix('six-')
    proof_receipt = pinned(proof / 'results' / (proof_label + '.json'), args.expected_lazy_receipt_sha256)
    closed_worker(proof_receipt)
    proof_source = source_identity(proof)
    require(proof_receipt['accepted'] and proof_receipt['source_unchanged']
            and proof_receipt['expected_source_matches'] and proof_receipt['interfaces_before'] == 0
            and proof_source['source_sha256'] == proof_receipt['source_sha256']
            and proof_receipt['executable_sha256'] == machine['agda_sha256'], 'cold safe checker acceptance required')
    lazy_name = 'src/Othello/LazyIndexed6.agda'
    require(assembly6.sha(current / lazy_name) == assembly6.sha(proof / lazy_name), 'checked lazy source differs')
    for name, _ in source_files(current):
        if name.endswith(('.agda', '.agda-lib')) and name not in (
                lazy_name, 'src/Tests/LazyIndexed6.agda', 'src/Everything6.agda'):
            require(assembly6.sha(old / name) == assembly6.sha(current / name), 'shared core source differs')
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh private repair root required')
    out.mkdir(parents=True)
    report = dict(format='othello-nat-lazy-repair6-v1', accepted=False, status='preparing',
        created_utc=utc(), machine=machine, original_checked_source=source,
        original_layout=prior['layout'], predecessor_closed_service=closed,
        predecessor_receipt_sha256=args.expected_receipt_sha256,
        predecessor_report_sha256=args.expected_report_sha256,
        predecessor_map_sha256=args.expected_map_sha256, heap_failure=failed,
        inherited_accepted_phases=[p for p in prior.get('inherited_accepted_phases', []) + prior['phases']
                                  if p['record']['accepted']],
        accepted_root_paths=sorted({str(old)} | set(prior.get('accepted_root_paths', []))),
        reused_parts=242, accepted_parts=242, phases=[], kernel_cpu_seconds=0., archived_logs=[],
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        original_row_forecast_validated=False,
        scope='one unchecked lazy replacement and explicit vector bridges; accepted prefix unchanged')

    def save():
        atomic_json(out / 'report.json', report)

    def guard(extra=0):
        used = allocated(current.parent)
        free = shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'storage gate reached; all accepted proofs remain intact')

    estimate = sum((old / n).stat().st_blocks * 512 for n, _ in source_files(old))
    estimate += sum((old / n).stat().st_blocks * 512 for n in pool)
    guard(estimate + 20 * 2**20)
    check = out / 'check'
    check.mkdir()
    for name, _ in source_files(old):
        path = check / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old / name, path)
    for name, digest in pool.items():
        copy_interface(old / name, check / name, digest)
    require(source_identity(check) == source and assembly6.interfaces(check) == pool, 'private copy differs')
    shutil.copy2(current / lazy_name, check / lazy_name)
    repair = generate(check, 242, accepted_parts=242)
    changed = 'src/' + PREFIX.replace('.', '/') + '/Part242.agda'
    require(not any(n.endswith('/' + PREFIX.replace('.', '/') + '/Part242.agdai') for n in pool),
            'failed part unexpectedly has a proof interface')
    for name in pool:
        path = name.split('/agda/', 1)[1][:-1]
        require(assembly6.sha(old / path) == assembly6.sha(check / path), 'a reused module source changed')
        require(not re.search(r'\bimport\s+' + re.escape(PREFIX + '.Part242') + r'\b',
                              (check / path).read_text()), 'a reused module depends on the changed target')
    for name, raw in source_files(old):
        if name != changed:
            require((check / name).read_bytes() == raw, 'an unrelated old source changed')
    checked = source_identity(check)
    layout = copy.deepcopy(prior['layout'])
    layout['generated_sha256'].update(repair['generated_sha256'])
    report.update(checked_source=checked, layout=layout, repair=repair,
        private_source_and_cache_bytes=estimate, reused_interface_sources_unchanged=True,
        lazy_source_sha256=assembly6.sha(check / lazy_name), source_epochs=[source, checked],
        last_interface_pool_sha256=digest_entries(pool))
    atomic_json(out / 'interface-map.json', pool)
    save()
    targets = ['Othello.LazyIndexed6'] + repair['targets']
    for index, target in enumerate(targets):
        guard()
        remaining = args.kernel_cpu_limit - report['kernel_cpu_seconds']
        require(remaining > 1, 'nested CPU allowance exhausted')
        before = assembly6.interfaces(check)
        suffix = '/' + target.replace('.', '/') + '.agdai'
        require(not any(n.endswith(suffix) for n in before), 'repair target unexpectedly warm')
        rec = run_job('repair' + str(index), [args.agda, '--no-libraries', '-i', 'src', '--safe',
            '--without-K', '--cubical-compatible', '--save-metas', 'src/' + target.replace('.', '/') + '.agda',
            '+RTS', '-M1350M', '-c', '-s', '-RTS'], out / 'records', root=check,
            expected_source_sha256=checked['source_sha256'], timeout=420,
            cpu_limit=min(120, remaining), rss_limit_gib=1.5, log_limit_mib=2,
            metadata=dict(target=target, own_target_cold=True, reused_parts=242, initial_problem2_proved=False))
        after = assembly6.interfaces(check)
        unchanged = all(after.get(n) == h for n, h in before.items())
        report['phases'].append(dict(target=target, record=rec, borrowed_interfaces_unchanged=unchanged))
        report['kernel_cpu_seconds'] += rec['cpu_seconds']
        report['last_interface_pool_sha256'] = digest_entries(after)
        atomic_json(out / 'interface-map.json', after)
        save()
        require(rec['accepted'] and unchanged, 'repair check or reused interface failed: ' + target)
        # This child has finished. Keep its exact log bytes in a verified gzip;
        # the controlling service and all proof/build sources stay untouched.
        log = out / 'records' / (rec['label'] + '.log')
        require(log.stat().st_size == rec['log_bytes'], 'completed target log size differs')
        row = archive(log, assembly6.sha(log))
        row.update(directory=str(log.parent), record_sha256=assembly6.sha(log.with_suffix('.json')))
        report['archived_logs'].append(row)
        save()
    require(source_identity(previous) == outer_source and source_identity(old) == source
            and assembly6.interfaces(old) == pool and source_identity(check) == checked,
            'predecessor or repaired source changed')
    report.update(accepted=True, status='complete', finished_utc=utc(), accepted_parts=243,
                  repaired_original_conditional_export_checked=True, accepted_predecessor_unchanged=True)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'lazy-proof', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-receipt-sha256', 'expected-report-sha256',
                 'expected-map-sha256', 'expected-lazy-receipt-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--kernel-cpu-limit', type=float, default=400)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
