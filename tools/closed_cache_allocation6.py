#!/usr/bin/env python3
"""Share exact duplicate interface allocation in explicitly closed runs.

No bytes, paths, timestamps, modes, sources or receipts are changed. These
historical caches remain immutable; every future checking cache is copied.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import assembly6
from owner_cache_dedup6 import allocated
from provenance import source_identity
from rewrite_dedup6 import closed
from run_job import atomic_json, utc

LABELS = (
    'owner-lower-split-20261008', 'owner-lower-training-20261008',
    'owner-trees-ready-20261008', 'owner-gc-ready-20261008', 'owner-gc-20261008',
    'owner-single-20261008', 'owner-pruned-20261008', 'owner-rebind-20261008',
    'owner-capsule-full-20261008', 'owner-capsule-ready-20261008',
    'owner-packed-ready-20261008', 'rewrite-filter-20261008',
    'rewrite-prefix-20261008', 'rewrite-owners-20261008',
    'rewrite-training-ready-20261008', 'rewrite-holdout-20261008',
)


def run(args):
    runs = args.runs_root.resolve()
    checks, groups, replacements = [], {}, []
    for label in LABELS:
        closed(label)
        root = runs / ('six-' + label)
        receipt = root / 'results' / (label + '.json')
        record = json.loads(receipt.read_text())
        identity = source_identity(root)
        if (not record.get('finished_utc') or not record['source_unchanged'] or
                not record['expected_source_matches'] or record['source_sha256'] != identity['source_sha256']):
            raise ValueError('requires the original finished unchanged-source run')
        pool = assembly6.interfaces(root)
        checks.append(dict(label=label, root=str(root), source=identity, interfaces=pool,
                           receipt=str(receipt), receipt_sha256=assembly6.sha(receipt)))
        for name, digest in pool.items():
            path = root / name
            stat = path.stat()
            if path.is_symlink():
                raise ValueError('requires regular same-filesystem interface files')
            key = (path.name, digest, stat.st_size, stat.st_mtime_ns, stat.st_mode, stat.st_dev)
            groups.setdefault(key, []).append(path)
    for paths in groups.values():
        canonical = paths[0]
        for target in paths[1:]:
            if target.stat().st_ino == canonical.stat().st_ino:
                continue
            replacements.append(dict(path=str(target), canonical=str(canonical),
                sha256=assembly6.sha(canonical), original_inode=target.stat().st_ino,
                canonical_inode=canonical.stat().st_ino, mtime_ns=target.stat().st_mtime_ns,
                mode=target.stat().st_mode, bytes=target.stat().st_size))
    report = dict(format='othello-closed-cache-allocation6-v1', status='prepared', created_utc=utc(),
        scope='immutable allocation only; no proof claim', checks=checks, replacements=replacements,
        initial_runs_bytes=allocated(runs),
        rollback='copy2 each canonical file to a fresh temporary path and replace its original path')
    atomic_json(args.output, report)
    for row in replacements:
        target, canonical = Path(row['path']), Path(row['canonical'])
        temporary = target.with_name(target.name + '.allocation-tmp')
        a, b = target.stat(), canonical.stat()
        if (temporary.exists() or assembly6.sha(target) != row['sha256'] or
                assembly6.sha(canonical) != row['sha256'] or
                a.st_mtime_ns != b.st_mtime_ns or a.st_mode != b.st_mode or a.st_dev != b.st_dev):
            raise ValueError('interface changed before allocation replacement')
        os.link(canonical, temporary)
        os.replace(temporary, target)
    for row in checks:
        root = Path(row['root'])
        if (source_identity(root) != row['source'] or assembly6.interfaces(root) != row['interfaces'] or
                assembly6.sha(Path(row['receipt'])) != row['receipt_sha256']):
            raise ValueError('closed proof evidence changed')
    report.update(status='complete', final_runs_bytes=allocated(runs),
        replaced_interfaces=len(replacements), sources_unchanged=True, interfaces_unchanged=True,
        receipts_unchanged=True, paths_preserved=True)
    report['recovered_allocated_bytes'] = report['initial_runs_bytes'] - report['final_runs_bytes']
    atomic_json(args.output, report)
    print(json.dumps({k: report[k] for k in
        ('status', 'replaced_interfaces', 'recovered_allocated_bytes', 'final_runs_bytes')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args())
