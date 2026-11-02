#!/usr/bin/env python3
"""Deduplicate identical interfaces in the three closed filtered proof caches.

Only exact bytes, timestamps and modes may be shared. Sources, receipts,
interface paths and unique proof bytes remain unchanged. Future Agda jobs use
independent private copies, never these immutable caches.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess

import assembly6
from owner_audit6 import audit
from owner_cache_dedup6 import allocated
from provenance import source_identity
from run_job import atomic_json, utc

CLOSED = (
    ('rewrite-filter-20261008', 'rewrite-filter6', 'fe9822fbe11776e9e9482f64caaaf3641934180c6aac454f75fbae21848b8325'),
    ('rewrite-prefix-20261008', 'rewrite-prefix6', 'a2605b0e9892ba67c47991285ef6b6177c799b43bdbaf8ffa0b253e29723a46c'),
    ('rewrite-owners-20261008', 'rewrite-owners6', '079859e69971195de5640846bb083c37364360b2d74f696f51a95b5f79b42799'),
)


def closed(label):
    p = subprocess.run(['systemctl', '--user', 'show', 'othello6-'+label+'.service',
        '-p', 'ActiveState', '-p', 'MainPID'], capture_output=True, text=True)
    if (p.returncode not in (0, 1) or 'ActiveState=active' in p.stdout or
            'ActiveState=activating' in p.stdout or 'MainPID=0' not in p.stdout):
        raise ValueError('requires a closed, immutable selected job')


def run(args):
    runs = args.runs_root.resolve()
    previous = args.previous.resolve()
    audit(previous, args.expected_previous_sha256)
    r = json.loads((previous/'final.json').read_text())
    if r['format'] != 'othello-rewrite-training6-v1' or not r['accepted'] or r['status'] != 'complete':
        raise ValueError('requires the complete checked training donor')
    closed('rewrite-training-ready-20261008')
    donor = Path(r['check_root'])
    identity, pool = source_identity(donor), assembly6.interfaces(donor)
    checks, replacements = [], []
    for label, directory, expected in CLOSED:
        closed(label)
        outer = runs/('six-'+label)
        report_path = outer/'results'/directory/'final.json'
        if assembly6.sha(report_path) != expected:
            raise ValueError('selected closed report differs')
        report = json.loads(report_path.read_text())
        root = Path(report['check_root'])
        origin, current = source_identity(root), assembly6.interfaces(root)
        receipt = outer/'results'/(label+'.json')
        record = json.loads(receipt.read_text())
        if (not report['accepted'] or report['status'] != 'complete' or not report['donor_unchanged'] or
                not report['generated_sources_unchanged'] or origin['source_sha256'] != report['source_sha256'] or
                current != report['final_interfaces'] or not record['accepted'] or not record['finished_utc'] or
                not record['source_unchanged'] or not record['expected_source_matches']):
            raise ValueError('closed proof evidence differs')
        checks.append(dict(root=str(root), source=origin, interfaces=current,
            report=str(report_path), report_sha256=expected, receipt=str(receipt), receipt_sha256=assembly6.sha(receipt)))
        for name, digest in current.items():
            if pool.get(name) != digest:
                continue
            target, canonical = root/name, donor/name
            a, b = target.stat(), canonical.stat()
            if (target.is_symlink() or canonical.is_symlink() or a.st_dev != b.st_dev or
                    a.st_mtime_ns != b.st_mtime_ns or a.st_mode != b.st_mode or
                    a.st_size != b.st_size or assembly6.sha(canonical) != digest):
                raise ValueError('sharing would change content, timestamp or mode')
            if a.st_ino != b.st_ino:
                replacements.append(dict(path=str(target), canonical=str(canonical), sha256=digest,
                    original_inode=a.st_ino, canonical_inode=b.st_ino, mtime_ns=a.st_mtime_ns,
                    mode=a.st_mode, bytes=a.st_size))
    result = dict(format='othello-rewrite-dedup6-v1', status='prepared', created_utc=utc(),
        scope='closed immutable cache allocation; no proof claim', donor=str(donor),
        donor_source=identity, donor_interfaces=pool, donor_report_sha256=args.expected_previous_sha256,
        checks=checks, replacements=replacements, initial_runs_bytes=allocated(runs),
        rollback='copy2 each canonical file to a fresh temporary path, then replace its original path')
    atomic_json(args.output, result)
    for row in replacements:
        target, canonical = Path(row['path']), Path(row['canonical'])
        temporary = target.with_name(target.name+'.rewrite-dedup-tmp')
        if temporary.exists() or assembly6.sha(target) != row['sha256'] or assembly6.sha(canonical) != row['sha256']:
            raise ValueError('interface changed before exact allocation replacement')
        os.link(canonical, temporary); os.replace(temporary, target)
    if source_identity(donor) != identity or assembly6.interfaces(donor) != pool:
        raise ValueError('canonical proof donor changed')
    for check in checks:
        root = Path(check['root'])
        if (source_identity(root) != check['source'] or assembly6.interfaces(root) != check['interfaces'] or
                assembly6.sha(Path(check['report'])) != check['report_sha256'] or
                assembly6.sha(Path(check['receipt'])) != check['receipt_sha256']):
            raise ValueError('closed proof evidence changed')
    result.update(status='complete', sources_unchanged=True, interface_bytes_unchanged=True,
        paths_preserved=True, receipts_unchanged=True, replaced_interfaces=len(replacements), final_runs_bytes=allocated(runs))
    result['recovered_allocated_bytes'] = result['initial_runs_bytes']-result['final_runs_bytes']
    atomic_json(args.output, result)
    print(json.dumps({k: result[k] for k in ('status', 'replaced_interfaces', 'recovered_allocated_bytes')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'runs-root', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-previous-sha256', required=True)
    run(parser.parse_args())
