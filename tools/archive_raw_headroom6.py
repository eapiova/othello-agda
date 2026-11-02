#!/usr/bin/env python3
"""Recover bounded storage by extending the closed raw-profile gzip archive.

Only native JSON iterations from the already archived raw lower profile are
selected. Canonical data, transposition tables, proof sources, interfaces,
measurement receipts and failures remain untouched. Every removed raw file is
recoverable byte for byte from a verified archive and a durable path mapping.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import assembly6
from archive_closed_native6 import MIB, GIB, allocated, stream_archive
from provenance import source_identity
from rewrite_dedup6 import closed
from run_job import atomic_json, utc

PROFILE = 'native-lower120-profile-20261006'
SOURCE = '816061559a2046ca674f635a07e3f2ef980a9859d7f8ea689b320cda3cc88558'
HISTORY = ('raw-lower-archives6.json', 'raw-lower-archives-resume6.json')


def run(args):
    runs = args.runs_root.resolve()
    old = runs / ('six-' + PROFILE)
    directory = old / 'results/hint-profile6/lower120'
    history_root = runs / 'six-warning-assembly-resume-20261007/results'
    closed(PROFILE)
    record_path = old / 'results' / (PROFILE + '.json')
    record = json.loads(record_path.read_text())
    identity, pool = source_identity(old), assembly6.interfaces(old)
    if (not record['accepted'] or record['exit_code'] != 0 or
            not record['source_unchanged'] or not record['expected_source_matches'] or
            record['source_sha256'] != SOURCE or identity['source_sha256'] != SOURCE):
        raise ValueError('requires the exact completed raw profile')
    protected = {str(record_path): assembly6.sha(record_path),
                 str(directory / 'profile.json'): assembly6.sha(directory / 'profile.json')}
    archived = set()
    for filename in HISTORY:
        path = history_root / filename
        history = json.loads(path.read_text())
        protected[str(path)] = assembly6.sha(path)
        if history['source_sha256'] != SOURCE:
            raise ValueError('archive history belongs to a different profile')
        for row in history['records']:
            raw, packed = Path(row['original']), Path(row['archive'])
            if (raw.parent != directory or packed != raw.with_suffix('.json.gz') or
                    raw.exists() or not packed.is_file() or packed.is_symlink() or
                    assembly6.sha(packed) != row['archive_sha256'] or raw.name in archived):
                raise ValueError('previous archive mapping differs')
            archived.add(raw.name)
    files = sorted(directory.glob('native-*.json'), key=lambda p: (p.stat().st_size, p.name))
    if len(files) + len(archived) != 360:
        raise ValueError('different original raw-profile file set')
    initial = allocated(runs)
    limit = 10 * GIB
    target = limit - 512 * MIB
    estimate = initial
    report = dict(format='othello-raw-headroom6-v1', status='archiving', created_utc=utc(),
        scope='closed raw-profile native JSON only; verified lossless gzip; no proof claim',
        source=identity, interfaces=pool, protected=protected, records=[],
        previous_archives=len(archived), initial_runs_bytes=initial,
        maximum_runs_bytes=limit, target_runs_bytes=target,
        rollback='decompress archive to its recorded original path and verify original_sha256')
    atomic_json(args.output, report)
    for path in files:
        if estimate <= target:
            break
        room = limit - estimate - 2 * MIB
        if room <= 0:
            raise ValueError('insufficient archive staging headroom under the unchanged cap')
        blocks = path.stat().st_blocks * 512
        row = stream_archive(path, room)
        report['records'].append(row)
        atomic_json(args.output, report)  # Durable recovery mapping before removing raw allocation.
        path.unlink()
        estimate += Path(row['archive']).stat().st_blocks * 512 - blocks
        report['estimated_runs_bytes'] = estimate
        atomic_json(args.output, report)
    if (source_identity(old) != identity or assembly6.interfaces(old) != pool or
            any(assembly6.sha(Path(name)) != digest for name, digest in protected.items())):
        raise ValueError('source, proof cache or protected report changed')
    final = allocated(runs)
    report.update(status='complete' if final <= target else 'insufficient-headroom',
        final_runs_bytes=final, recovered_allocated_bytes=initial-final,
        sources_unchanged=True, interfaces_unchanged=True, protected_reports_unchanged=True)
    atomic_json(args.output, report)
    print(json.dumps({k: report[k] for k in
        ('status', 'final_runs_bytes', 'recovered_allocated_bytes')}))
    if final > target:
        raise ValueError('remaining raw iterations cannot supply the required headroom')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args())
