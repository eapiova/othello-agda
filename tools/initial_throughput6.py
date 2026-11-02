#!/usr/bin/env python3
"""Capped 1/4/8-worker throughput of an accepted real initial extrema slice.

Each worker owns private sources and caches and recomputes one cold target.
Closed batch inputs are shared only after every worker has terminated; measured
proof bytes and receipts are preserved. This is a feasibility measurement.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

import assembly6
from cache_resume6 import copy_interface
from indexed_wire_resume6 import pinned
from initial_training_resume6 import target_interfaces, validate_pool, validate_receipt
from nat_descendant_resume6 import closed_worker
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_identity
from run_job import atomic_json, utc
from wire_workflow6 import require


def closure(root, target):
    """Exact project import closure; builtin modules stay with the pinned compiler."""
    seen, pending = set(), [target]
    while pending:
        module = pending.pop()
        require(re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*', module),
                'invalid import module')
        if module in seen:
            continue
        relative = 'src/' + module.replace('.', '/') + '.agda'
        source = root / relative
        if module.startswith('Agda.Builtin.') or module == 'Agda.Primitive':
            require(not source.exists(), 'shadowed builtin source refused')
            continue
        require(source.is_file() and not source.is_symlink(), 'missing regular project import: ' + module)
        seen.add(module)
        pending.extend(re.findall(r'^\s*(?:open\s+)?import\s+([A-Za-z][A-Za-z0-9_.]*)',
                                  source.read_text(), flags=re.M))
    return {'src/' + module.replace('.', '/') + '.agda' for module in seen} | {'othello.agda-lib'}


WORKER = '''import json,pathlib,sys
sys.path.insert(0,sys.argv[1]);from run_job import run_job
a=json.loads(sys.argv[2])
r=run_job(a['label'],a['argv'],pathlib.Path(a['output']),root=pathlib.Path(a['root']),
 timeout=360,cpu_limit=120,rss_limit_gib=1.5,log_limit_mib=2,
 expected_source_sha256=a['source_sha256'],metadata=a['metadata'])
raise SystemExit(0 if r['accepted'] else 1)
'''


def run(args):
    current, previous = Path.cwd().resolve(), args.previous.resolve()
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == 'eapiova' and machine['agda_sha256'] == args.expected_agda_sha256,
            'exact desktop compiler required')
    outer = source_identity(previous)
    actual = pinned(previous / 'results' / (previous.name.removeprefix('six-') + '.json'),
                    args.expected_receipt_sha256)
    validate_receipt(actual, outer, previous, machine['hostname'])
    service = closed_worker(actual)
    base = previous / 'results/initial-extrema-slices6'
    prior = pinned(base / 'report.json', args.expected_report_sha256)
    old = base / 'check'
    pool = pinned(base / 'interface-map.json', args.expected_map_sha256)
    old_source = source_identity(old)
    require(prior['accepted'] and prior['status'] == 'complete' and prior['accepted_slices'] == 12
            and prior['checked_source'] == old_source and prior['machine'] == machine
            and prior['accepted_donor_unchanged'], 'closed accepted real extrema slices required')
    validate_pool(pool, assembly6.interfaces(old))
    require(digest_entries(pool) == prior['last_interface_pool_sha256'], 'donor pool differs')
    selected = [p for p in prior['phases'] if p['target'] == args.module]
    require(len(selected) == 1 and '.Slice' in args.module and selected[0]['record']['accepted']
            and selected[0]['record']['own_target_cold'] and selected[0]['borrowed_interfaces_unchanged']
            and selected[0]['record']['executable_sha256'] == machine['agda_sha256'],
            'exact previously accepted real slice required')
    files = closure(old, args.module)
    own_interfaces = set(target_interfaces(pool, args.module))
    borrowed = {n: h for n, h in pool.items()
                if n.split('/agda/', 1)[1][:-1] in files
                and n not in own_interfaces}
    require(len(borrowed) == len(files) - 2, 'complete unambiguous warm dependency closure required')
    out = args.output.resolve()
    require(not out.exists() and current in out.parents and 'results' in out.parts, 'fresh pilot required')
    out.mkdir(parents=True)
    report = dict(format='othello-initial-throughput6-v1', accepted=False, status='preparing',
        created_utc=utc(), machine=machine, donor_closed_service=service, donor_checked_source=old_source,
        donor_receipt_sha256=args.expected_receipt_sha256, donor_report_sha256=args.expected_report_sha256,
        donor_map_sha256=args.expected_map_sha256, target=args.module, batches=[],
        borrowed_pool_sha256=digest_entries(borrowed), dependency_sources=sorted(files),
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='controlled same-workload cold-target throughput; no initial theorem or production forecast')

    def save():
        atomic_json(out / 'report.json', report)

    estimate = sum((old / n).stat().st_blocks * 512 for n in files | borrowed.keys())
    single_wall = None
    for slots in (1, 4, 8):
        used, free = allocated(current.parent), shutil.disk_usage(current.parent).free
        extra = slots * estimate + 16 * 2**20
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free,
                                          reserved_extra_bytes=extra, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30,
                'throughput storage gate reached before batch')
        plans = []
        for i in range(slots):
            root = out / ('p' + str(slots) + '-' + str(i))
            root.mkdir()
            for name in sorted(files):
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old / name, destination)
            for name, digest in borrowed.items():
                copy_interface(old / name, root / name, digest)
            source = source_identity(root)
            require(assembly6.interfaces(root) == borrowed and not target_interfaces(borrowed, args.module),
                    'private cold-target closure differs')
            plans.append(dict(label='p' + str(slots) + '-' + str(i), root=str(root),
                source_sha256=source['source_sha256'], output=str(out / 'records'),
                argv=[args.agda, '--no-libraries', '-i', 'src', '--safe', '--without-K',
                      '--cubical-compatible', '--save-metas', 'src/' + args.module.replace('.', '/') + '.agda',
                      '+RTS', '-M1350M', '-c', '-s', '-RTS'],
                metadata=dict(target=args.module, own_target_cold=True, machine=machine,
                              borrowed_pool_sha256=digest_entries(borrowed), independent_private_cache=True,
                              initial_problem2_proved=False)))
        report['status'] = 'batch-' + str(slots)
        save()
        started = time.monotonic()
        processes = [subprocess.Popen([sys.executable, '-c', WORKER, str(current / 'tools'), json.dumps(p)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for p in plans]
        return_codes = [p.wait() for p in processes]
        wall = time.monotonic() - started
        records = [json.loads((out / 'records' / (p['label'] + '.json')).read_text()) for p in plans]
        checks = []
        for plan, record in zip(plans, records):
            root = Path(plan['root'])
            after = assembly6.interfaces(root)
            unchanged = all(after.get(n) == h for n, h in borrowed.items())
            source_unchanged = source_identity(root)['source_sha256'] == plan['source_sha256']
            checks.append(dict(label=plan['label'], record=record,
                borrowed_interfaces_unchanged=unchanged, source_unchanged=source_unchanged,
                final_pool_sha256=digest_entries(after)))
        accepted = all(c == 0 for c in return_codes) and all(
            x['record']['accepted'] and x['borrowed_interfaces_unchanged'] and x['source_unchanged']
            and len(target_interfaces(assembly6.interfaces(Path(p['root'])), args.module)) == 1
            for x, p in zip(checks, plans))
        if slots == 1:
            single_wall = wall
        row = dict(slots=slots, accepted=accepted, wall_seconds=wall,
            cpu_seconds=sum(r['cpu_seconds'] for r in records),
            sum_peak_rss_gib=sum(r['peak_rss_gib'] for r in records),
            effective_slots=slots * single_wall / wall, phases=checks, closed_input_sharing=[])
        report['batches'].append(row)
        save()
        require(accepted, 'throughput batch rejected; preserve all records')
        # These workers will never run again. Preserve their exact source,
        # timestamps and borrowed interface hashes while reclaiming duplicates.
        for plan in plans:
            root = Path(plan['root'])
            prepared = []
            for name in sorted(files | borrowed.keys()):
                target, canonical = root / name, old / name
                a, b = target.stat(), canonical.stat()
                require(assembly6.sha(target) == assembly6.sha(canonical)
                        and (a.st_size, a.st_mtime_ns, a.st_mode, a.st_dev)
                        == (b.st_size, b.st_mtime_ns, b.st_mode, b.st_dev), 'closed input sharing differs')
                journal = dict(path=str(target), canonical=str(canonical), sha256=assembly6.sha(target),
                               original_inode=a.st_ino, mtime_ns=a.st_mtime_ns, mode=a.st_mode,
                               reclaimed_allocated_bytes=a.st_blocks * 512)
                prepared.append(journal)
            row['closed_input_sharing'].extend(prepared)
            row['closed_sharing_status'] = 'prepared-' + plan['label']
            save()
            for journal in prepared:
                target, canonical = Path(journal['path']), Path(journal['canonical'])
                temporary = target.with_name(target.name + '.closed-input-tmp')
                require(not temporary.exists(), 'stale closed input temporary')
                os.link(canonical, temporary)
                os.replace(temporary, target)
            final_pool = assembly6.interfaces(root)
            require(source_identity(root)['source_sha256'] == plan['source_sha256']
                    and all(final_pool.get(n) == h for n, h in borrowed.items()),
                    'closed source or interfaces changed after sharing')
            row['closed_sharing_status'] = 'complete-' + plan['label']
            save()
        save()
    require(source_identity(previous) == outer and source_identity(old) == old_source
            and assembly6.interfaces(old) == pool, 'closed accepted donor changed')
    report.update(accepted=True, status='complete', finished_utc=utc(), accepted_donor_unchanged=True)
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('agda', 'module', 'expected-agda-sha256', 'expected-receipt-sha256',
                 'expected-report-sha256', 'expected-map-sha256'):
        parser.add_argument('--' + name, required=True)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
