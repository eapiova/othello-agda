#!/usr/bin/env python3
"""Losslessly archive completed native iteration JSON; preserve proof evidence.

Only the explicitly pinned, closed profiles below are eligible. Master profiles,
solver inputs, transposition tables, sources, interfaces and job receipts stay
at their original paths. Each archived iteration remains recoverable byte for
byte through the durable journal, which is written before removing its raw copy.
"""
import argparse
import json
from pathlib import Path
import re

import assembly6
from archive_closed_native6 import GIB, MIB, allocated, stream_archive
from provenance import source_identity
from rewrite_dedup6 import closed
from run_job import atomic_json, utc

PLAN = (
    ('native-hint-profile120-20261006', 'hint-profile6/upper120',
     'da5f09c707da6d5f81ce57edbf01f6f09af7c22fa618c2c8ffd868dd37c20957'),
    ('native-upper22-cached-fixed-20261006', 'hint-profile6/upper22',
     '5e183923f82a22082d724ace046f122b10e72d43c88c36230b5f1cb3353c51d2'),
    ('native-canonical-lower120-profile-fixed-20261006', 'canonical-profile6/lower',
     'e26325591700ba0102a59b788ee2ca584a6475cdf65996c74c6be151a32893db'),
    ('native-canonical-upper120-profile-fixed-20261006', 'canonical-profile6/upper',
     '9434ceb03afec742bbb9b1d269724038af8bc71675ad6a92d11e9c409b464619'),
)


def run(args):
    runs = args.runs_root.resolve()
    if args.output.exists() or not 64 <= args.headroom_mib <= 1536:
        raise ValueError('fresh journal and bounded headroom required')
    identities, pools, protected, files = {}, {}, {}, []
    for label, folder, expected in PLAN:
        closed(label)
        root = runs / ('six-' + label)
        receipt = root / 'results' / (label + '.json')
        record = json.loads(receipt.read_text())
        identity = source_identity(root)
        if (not record['accepted'] or record['exit_code'] != 0
                or not record['source_unchanged'] or not record['expected_source_matches']
                or record['source_sha256'] != expected or identity['source_sha256'] != expected):
            raise ValueError('exact completed native profile required: ' + label)
        identities[str(root)] = identity
        pools[str(root)] = assembly6.interfaces(root)
        directory = root / 'results' / folder
        for p in (receipt, directory / 'profile.json'):
            protected[str(p)] = assembly6.sha(p)
        for p in directory.glob('native-*.json'):
            if (p.is_symlink() or not p.is_file() or p.stat().st_nlink != 1
                    or not re.fullmatch(r'native-[lu][0-9]+-c[0-9]+\.json', p.name)):
                raise ValueError('unexpected native iteration path: ' + str(p))
            files.append(p)
    files.sort(key=lambda p: (p.stat().st_size, str(p)))
    initial = allocated(runs)
    limit, target = 10 * GIB, 10 * GIB - args.headroom_mib * MIB
    if initial >= limit:
        raise ValueError('no staging room under the artifact cap')
    report = dict(format='othello-closed-profiles-archives6-v1', status='archiving',
        created_utc=utc(), scope='closed native iteration bytes only; no proof claims',
        initial_runs_bytes=initial, target_runs_bytes=target, maximum_runs_bytes=limit,
        source_identities=identities, interface_pool_sha256={p: assembly6.digest_entries(v)
            for p, v in pools.items()}, protected_receipts=protected, records=[],
        rollback='gunzip to original path; verify original_sha256; restore recorded mode/mtime',
        initial_problem2_proved=False, production_authorized=False)
    atomic_json(args.output, report)
    estimate = initial
    for p in files:
        if estimate <= target:
            break
        stat = p.stat()
        row = stream_archive(p, limit - estimate - 2 * MIB)
        row.update(original_mode=stat.st_mode, original_mtime_ns=stat.st_mtime_ns)
        report['records'].append(row)
        atomic_json(args.output, report)
        p.unlink()
        estimate += Path(row['archive']).stat().st_blocks * 512 - stat.st_blocks * 512
        report['estimated_runs_bytes'] = estimate
        atomic_json(args.output, report)
    if (any(source_identity(Path(p)) != d for p, d in identities.items())
            or any(assembly6.interfaces(Path(p)) != d for p, d in pools.items())
            or any(assembly6.sha(Path(p)) != h for p, h in protected.items())):
        raise ValueError('protected source, proof interface or receipt changed')
    final = allocated(runs)
    report.update(status='complete' if final <= target else 'available-iterations-archived',
        finished_utc=utc(), final_runs_bytes=final, reclaimed_allocated_bytes=initial-final,
        sources_unchanged=True, interfaces_unchanged=True, protected_receipts_unchanged=True)
    atomic_json(args.output, report)
    print(json.dumps({k: report[k] for k in
        ('status', 'final_runs_bytes', 'reclaimed_allocated_bytes')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--headroom-mib', type=int, default=1024)
    run(parser.parse_args())
