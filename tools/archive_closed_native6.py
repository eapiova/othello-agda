#!/usr/bin/env python3
"""Lossless archival of closed native iteration data, never proof caches.

The original bytes and digests remain recoverable with gzip. Canonical inputs,
Agda sources, interfaces, transposition tables and JSON measurement receipts
are excluded. Run under a coordinator reservation in a frozen desktop root.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess

import assembly6
from provenance import source_identity
from run_job import atomic_json, utc

GIB = 1024**3
MIB = 1024**2
CLOSED = {
    'six-native-lower20-warm-20261006':
        'da5f09c707da6d5f81ce57edbf01f6f09af7c22fa618c2c8ffd868dd37c20957',
    'six-native-lower20-resume-20261006':
        'b63bb67fc37a6039d73f6af63e802ecd53fc97d043e7b4a6cba9e38ef5e38b04',
}


def allocated(runs):
    return int(subprocess.check_output(['du', '-s', '-B1', str(runs)]).split()[0])


def stream_archive(path, room):
    before = path.stat()
    expected = assembly6.sha(path)
    target = path.with_suffix(path.suffix+'.gz')
    temporary = target.with_name(target.name+'.tmp')
    if path.is_symlink() or target.exists() or temporary.exists():
        raise ValueError('original must be a regular file with a fresh archive path')
    try:
        with path.open('rb') as raw, temporary.open('xb') as destination:
            class Limited:
                def write(self, data):
                    if destination.tell()+len(data) > room:
                        raise ValueError('archive staging would exceed the unchanged artifact cap')
                    return destination.write(data)
                def flush(self):
                    return destination.flush()
            with gzip.GzipFile(filename='', fileobj=Limited(), mode='wb',
                               compresslevel=1, mtime=0) as packed:
                for chunk in iter(lambda: raw.read(MIB), b''):
                    packed.write(chunk)
            destination.flush()
            os.fsync(destination.fileno())
        recovered = hashlib.sha256()
        count = 0
        with gzip.open(temporary, 'rb') as stream:
            for chunk in iter(lambda: stream.read(MIB), b''):
                recovered.update(chunk)
                count += len(chunk)
        if (count != before.st_size or recovered.hexdigest() != expected or
                assembly6.sha(path) != expected):
            raise ValueError('written archive does not recover the unchanged original')
        os.replace(temporary, target)
        row = dict(original=str(path), archive=str(target), original_sha256=expected,
                   archive_sha256=assembly6.sha(target), original_bytes=count,
                   archive_bytes=target.stat().st_size, original_nlink=before.st_nlink)
        return row
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def run(args):
    runs = args.runs_root.resolve()
    identities, pools, receipts, files = {}, {}, {}, []
    for name, expected in CLOSED.items():
        root = runs/name
        receipt = root/'results'/(name.removeprefix('six-')+'.json')
        record = json.loads(receipt.read_text())
        identity = source_identity(root)
        if (not record['accepted'] or record['exit_code'] != 0 or
                not record['source_unchanged'] or record['source_sha256'] != expected or
                identity['source_sha256'] != expected):
            raise ValueError('requires the exact completed, unchanged native iteration run')
        identities[name] = identity
        pools[name] = assembly6.interfaces(root)
        receipts[str(receipt)] = assembly6.sha(receipt)
        selected = sorted((root/'results/native6').glob('lower20-iteration-*.json'))
        if len(selected) != (4 if 'warm' in name else 3):
            raise ValueError('different original closed iteration set')
        files.extend(selected)
    files.sort(key=lambda p: (p.stat().st_size, str(p)))
    initial = allocated(runs)
    if initial >= 10*GIB:
        raise ValueError('no initial archive staging headroom under the study cap')
    report = dict(format='othello-closed-native-archives6-v1', status='archiving',
        created_utc=utc(), initial_runs_bytes=initial, maximum_runs_bytes=10*GIB,
        records=[], original_sources=identities, original_interfaces=pools,
        measurement_receipts=receipts,
        scope='closed lower20 iteration JSON only; all bytes preserved in verified gzip',
        digest_provenance='original raw hashes captured at archival; no proof claims',
        canonical_inputs_untouched=True, proofs_untouched=True)
    atomic_json(args.output, report)
    for path in files:
        room = 10*GIB-allocated(runs)-2*MIB
        if room <= 0:
            raise ValueError('archive staging headroom exhausted')
        row = stream_archive(path, room)
        report['records'].append(row)
        # Persist the reversible mapping before unlinking the raw name.
        atomic_json(args.output, report)
        path.unlink()
        report['latest_runs_bytes'] = allocated(runs)
        atomic_json(args.output, report)
    if (any(source_identity(runs/name) != identities[name] or
            assembly6.interfaces(runs/name) != pools[name] for name in CLOSED) or
            any(assembly6.sha(Path(name)) != digest for name, digest in receipts.items())):
        raise ValueError('a source, interface or original measurement receipt changed')
    report.update(status='complete', sources_unchanged=True, interfaces_unchanged=True,
        receipts_unchanged=True, final_runs_bytes=allocated(runs),
        original_bytes=sum(r['original_bytes'] for r in report['records']),
        archive_bytes=sum(r['archive_bytes'] for r in report['records']))
    atomic_json(args.output, report)
    if report['final_runs_bytes'] >= 10*GIB-256*MIB:
        raise ValueError('less than the required 256 MiB recovered headroom')
    print(json.dumps({k:v for k,v in report.items() if k not in
                     ('records','original_sources','original_interfaces','measurement_receipts')}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    run(p.parse_args())
