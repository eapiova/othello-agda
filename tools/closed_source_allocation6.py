#!/usr/bin/env python3
"""Recover allocation from exact duplicate sources in closed frozen jobs.

This is storage maintenance, never a new proof run. Logical paths, source bytes,
timestamps, modes, proof interfaces and measurement receipts are preserved.
Mutable future check roots must copy2 these immutable historical sources.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re

import assembly6
from closed_cache_allocation6 import LABELS
from owner_cache_dedup6 import allocated
from provenance import source_identity
from rewrite_dedup6 import closed
from run_job import atomic_json, utc


def run(args):
    runs = args.runs_root.resolve()
    groups, checks, replacements = {}, [], []
    labels=json.loads(args.labels.read_text()) if args.labels else LABELS
    if not (0<len(labels)<=32 and len(labels)==len(set(labels)) and
            all(isinstance(x,str) and re.fullmatch(r'[A-Za-z0-9-]+',x) for x in labels)):
        raise ValueError('one to 32 unique closed labels required')
    for label in labels:
        closed(label)
        root = runs / ('six-' + label)
        receipt = root / 'results' / (label + '.json')
        record = json.loads(receipt.read_text())
        identity = source_identity(root)
        if (not record.get('finished_utc') or not record.get('source_unchanged') or
                not record.get('expected_source_matches') or
                record['source_sha256'] != identity['source_sha256']):
            raise ValueError('requires a closed unchanged frozen source')
        manifest = root / 'SNAPSHOT.json'
        files = json.loads(manifest.read_text())['files']
        checks.append(dict(root=str(root), label=label, source=identity,
            receipt=str(receipt), receipt_sha256=assembly6.sha(receipt),
            manifest_sha256=assembly6.sha(manifest),
            interfaces=assembly6.interfaces(root)))
        for name, digest in files.items():
            relative = Path(name)
            if (relative.is_absolute() or '..' in relative.parts or
                    relative.parts[0] in ('results', '_build') or
                    relative.suffix in ('.agdai', '.o', '.hi')):
                raise ValueError('only top-level frozen source paths are eligible')
            path = root / relative
            st = path.stat()
            if path.is_symlink() or not path.is_file():
                raise ValueError('regular same-filesystem source files required')
            key = (name, digest, st.st_size, st.st_mtime_ns, st.st_mode, st.st_dev)
            groups.setdefault(key, []).append(path)
    for key, paths in groups.items():
        canonical = paths[0]
        for target in paths[1:]:
            if target.stat().st_ino != canonical.stat().st_ino and target.stat().st_nlink==1:
                replacements.append(dict(path=str(target), canonical=str(canonical),
                    sha256=key[1], bytes=key[2], mtime_ns=key[3], mode=key[4],
                    device=key[5], original_inode=target.stat().st_ino))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('fresh maintenance receipt required')
    report = dict(format='othello-closed-source-allocation6-v1', status='prepared',
        created_utc=utc(), checks=checks, replacements=replacements,
        initial_runs_bytes=allocated(runs),
        scope='exact immutable frozen source allocation; no proof computation',
        rollback='copy2 canonical to a temporary path, then replace the target')
    atomic_json(args.output, report)
    for row in replacements:
        target, canonical = Path(row['path']), Path(row['canonical'])
        a, b = target.stat(), canonical.stat()
        temporary = target.with_name(target.name + '.source-allocation-tmp')
        if (temporary.exists() or assembly6.sha(target) != row['sha256'] or
                assembly6.sha(canonical) != row['sha256'] or
                (a.st_size, a.st_mtime_ns, a.st_mode, a.st_dev) !=
                (b.st_size, b.st_mtime_ns, b.st_mode, b.st_dev)):
            raise ValueError('frozen source changed before allocation replacement')
        os.link(canonical, temporary)
        os.replace(temporary, target)
    for row in checks:
        root = Path(row['root'])
        if (source_identity(root) != row['source'] or
                assembly6.interfaces(root) != row['interfaces'] or
                assembly6.sha(Path(row['receipt'])) != row['receipt_sha256'] or
                assembly6.sha(root / 'SNAPSHOT.json') != row['manifest_sha256']):
            raise ValueError('protected proof or source evidence changed')
    report.update(status='complete', finished_utc=utc(), final_runs_bytes=allocated(runs),
        sources_unchanged=True, interfaces_unchanged=True, receipts_unchanged=True,
        replaced_source_files=len(replacements))
    report['recovered_allocated_bytes'] = report['initial_runs_bytes'] - report['final_runs_bytes']
    atomic_json(args.output, report)
    print(json.dumps({k: report[k] for k in ('status', 'replaced_source_files',
        'recovered_allocated_bytes', 'initial_runs_bytes', 'final_runs_bytes')}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--labels',type=Path,help='JSON list of exact terminal frozen job labels')
    run(p.parse_args())
