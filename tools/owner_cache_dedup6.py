#!/usr/bin/env python3
"""Deduplicate exact interface bytes in closed experiments, never edit proofs.

Only byte-identical, timestamp-identical interfaces from the audited original
325-interface donor are selected. Closed cache paths and content remain intact.
Future checking uses independent copies; the deduplicated roots are immutable.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess

import assembly6
from owner_audit6 import audit
from provenance import source_identity
from run_job import atomic_json, utc

CLOSED = (
    ('owner-trees-kernel-20261008', 'owner-trees6', 'd265e94377c08883e54d52cb3948920936c83db9bd3991761ac486c6d3ed5b4e'),
    ('owner-trees-ready-20261008', 'owner-trees6', '682dfa1fd4222c566e7cefef4e67bb3d07461add0b0a9fe53a0ec600d69c9d9b'),
    ('owner-cuts-kernel-20261008', 'owner-cuts6', 'fb232c41a8556c66e6a43d39174fbe083d7df36d3ade972fa9f7f1134adf650e'),
    ('owner-cuts-ready-20261008', 'owner-cuts6', 'f168e18f689c8f11ca2461f01e2d55cb58d42cf531afb163d8b2901429281fd9'),
    ('owner-lists-kernel-20261008', 'owner-lists6', '322e58669b27c5de9cd522f21c94640db2dff7b915b098fbf5ba8b64102d157c'),
    ('owner-queries-kernel-20261008', 'owner-queries6', 'dfaa13979383671d55dee8f4c1a45eecc5ce7c17c12c2496012e0f3ab9781f32'),
    ('owner-separated-kernel-20261008', 'owner-separated6', '211e86db9281b81ac915d18a1a9ef7c70ff6b8980fdfaac47b64b25d38c6a67d'),
    ('owner-opaque-kernel-20261008', 'owner-opaque6', '4c1e27caa50a82383287edd91435b79a46cf1b92dd6bb8340abb16957d5512d8'),
    ('owner-packed-kernel-20261008', 'owner-packed6', 'a3d53d67cdae3d60e4413fb3d0472e2f4b3feed938d02c294c08b33c7c71b4c7'),
    ('owner-packed-ready-20261008', 'owner-packed6', 'f0c0569eacffe64752b23608ece61f3ffab32d72e93a0d2b196b0d1350b809b4'),
)


def allocated(runs):
    return int(subprocess.check_output(['du', '-s', '-B1', str(runs)]).split()[0])


def run(args):
    runs = args.runs_root.resolve()
    original = runs / 'six-owner-lower-split-20261008/results/owner-split6'
    audit(original, 'dfc012d745b1f09cd720fe350f89a5967b2371473720cfa4ff2e187637d8e56b')
    report = json.loads((original / 'final.json').read_text())
    donor = Path(report['check_root'])
    identity, pool = source_identity(donor), assembly6.interfaces(donor)
    if len(pool) != 325:
        raise ValueError('original donor differs')
    checked, replacements = [], []
    for label, directory, expected in CLOSED:
        outer = runs / ('six-'+label)
        previous = outer / 'results' / directory
        if assembly6.sha(previous / 'final.json') != expected:
            raise ValueError('closed report differs')
        r = json.loads((previous / 'final.json').read_text())
        service = subprocess.run(['systemctl', '--user', 'show', 'othello6-'+label+'.service',
            '-p', 'ActiveState', '-p', 'MainPID'], text=True, capture_output=True)
        state = service.stdout
        if (service.returncode not in (0, 1) or 'ActiveState=active' in state or
                'ActiveState=activating' in state or 'MainPID=0' not in state):
            raise ValueError('a selected experiment is not closed')
        receipt = outer / 'results' / (label+'.json')
        outer_record = json.loads(receipt.read_text())
        if not outer_record.get('finished_utc') or not outer_record['source_unchanged']:
            raise ValueError('selected experiment has no final unchanged-source receipt')
        root = Path(r['check_root'])
        origin, current = source_identity(root), assembly6.interfaces(root)
        if (origin['source_sha256'] != r['source_sha256'] or current != r['final_interfaces'] or
                not r['generated_sources_unchanged'] or not r['donor_unchanged']):
            raise ValueError('closed cache or source differs')
        checked.append(dict(root=str(root), source=origin, interfaces=current,
            final_report=str(previous/'final.json'), final_report_sha256=expected,
            receipt=str(receipt), receipt_sha256=assembly6.sha(receipt)))
        for name, digest in current.items():
            if pool.get(name) != digest:
                continue
            target, canonical = root/name, donor/name
            a, b = target.stat(), canonical.stat()
            if target.is_symlink() or canonical.is_symlink() or a.st_dev != b.st_dev:
                raise ValueError('interface must be a regular same-filesystem file')
            if a.st_ino == b.st_ino:
                continue
            if a.st_mtime_ns != b.st_mtime_ns or a.st_mode != b.st_mode:
                raise ValueError('deduplication would change recorded cache timestamps/mode')
            replacements.append(dict(path=str(target), canonical=str(canonical), sha256=digest,
                original_inode=a.st_ino, canonical_inode=b.st_ino,
                mtime_ns=a.st_mtime_ns, mode=a.st_mode, bytes=a.st_size))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = dict(format='othello-owner-cache-dedup6-v1', status='prepared', created_utc=utc(),
        scope='closed immutable cache allocation only; byte content and paths preserved; no proof claim',
        donor=str(donor), donor_source=identity, donor_interfaces=pool,
        initial_runs_bytes=allocated(runs), checks=checked, replacements=replacements,
        rollback='copy each canonical file with copy2 into a fresh temporary path and replace its original path')
    atomic_json(args.output, result)
    for row in replacements:
        target, canonical = Path(row['path']), Path(row['canonical'])
        temporary = target.with_name(target.name+'.dedup-tmp')
        if temporary.exists() or assembly6.sha(target) != row['sha256'] or assembly6.sha(canonical) != row['sha256']:
            raise ValueError('interface changed before allocation replacement')
        os.link(canonical, temporary)
        os.replace(temporary, target)
    if source_identity(donor) != identity or assembly6.interfaces(donor) != pool:
        raise ValueError('original donor bytes changed')
    for row in checked:
        root = Path(row['root'])
        if (source_identity(root) != row['source'] or assembly6.interfaces(root) != row['interfaces'] or
                assembly6.sha(Path(row['receipt'])) != row['receipt_sha256'] or
                assembly6.sha(Path(row['final_report'])) != row['final_report_sha256']):
            raise ValueError('closed proof evidence changed')
    result.update(status='complete', sources_unchanged=True, interface_bytes_unchanged=True,
        paths_preserved=True, receipts_unchanged=True, final_runs_bytes=allocated(runs),
        replaced_interfaces=len(replacements))
    result['recovered_allocated_bytes'] = result['initial_runs_bytes']-result['final_runs_bytes']
    atomic_json(args.output, result)
    print(json.dumps({k: result[k] for k in ('status', 'replaced_interfaces',
        'recovered_allocated_bytes', 'initial_runs_bytes', 'final_runs_bytes')}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    run(p.parse_args())
