#!/usr/bin/env python3
"""Losslessly archive retired native certificate dumps to recover study room.

Only the 120 closed canonical lower-sample c36 dumps are eligible. Sources,
interfaces, the aggregate profile, measured job receipts and TT stay intact.
Original dump bytes are recovered with gzip and their recorded SHA256.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

import assembly6
from archive_closed_native6 import stream_archive
from owner_cache_dedup6 import allocated
from provenance import source_identity
from run_job import atomic_json, utc

LABEL = 'native-canonical-lower120-profile-fixed-20261006'
SOURCE = 'e26325591700ba0102a59b788ee2ca584a6475cdf65996c74c6be151a32893db'
GIB = 2**30
MIB = 2**20


def durable(path, report):
    atomic_json(path, report)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def run(args):
    runs = args.runs_root.resolve()
    root = runs/('six-'+LABEL)
    unit = subprocess.run(['systemctl', '--user', 'show', 'othello6-'+LABEL+'.service',
                           '-p', 'ActiveState', '-p', 'MainPID'],
                          capture_output=True, text=True, check=True).stdout
    if 'ActiveState=active' in unit or 'MainPID=0' not in unit:
        raise ValueError('native donor must be authoritatively closed')
    receipt = root/'results'/(LABEL+'.json')
    record = json.loads(receipt.read_text())
    source = source_identity(root)
    if (record.get('accepted') is not True or record.get('source_unchanged') is not True or
            record.get('source_sha256') != SOURCE or source['source_sha256'] != SOURCE or
            record.get('exit_code') != 0 or record.get('stop_reason') is not None):
        raise ValueError('exact accepted immutable historical native run required')
    directory = root/'results/canonical-profile6/lower'
    selected = sorted(directory.glob('native-l*-c36.json'), key=lambda p:(p.stat().st_size,p.name))
    if (len(selected) != 120 or {p.name for p in selected} !=
            {'native-l'+str(i).zfill(3)+'-c36.json' for i in range(120)} or
            any(p.is_symlink() or not re.fullmatch(r'native-l\d{3}-c36\.json', p.name) for p in selected)):
        raise ValueError('different retired native certificate set')
    pool = assembly6.interfaces(root)
    protected = {str(receipt):assembly6.sha(receipt),
                 str(directory/'profile.json'):assembly6.sha(directory/'profile.json')}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('fresh archival receipt required')
    initial = allocated(runs)
    if initial >= 10*GIB:
        raise ValueError('no initial staging room under study cap')
    report = dict(format='othello-wire-headroom-archives6-v1', status='archiving',
        created_utc=utc(), source=source, initial_runs_bytes=initial, records=[],
        scope='retired untrusted c36 certificate dumps only; verified lossless gzip',
        no_proof_cache_changes=True, initial_problem2_proved=False,
        production_authorized=False, protected_receipts=protected)
    durable(args.output, report)
    for p in selected:
        used = allocated(runs)
        if used <= 10*GIB-args.headroom_mib*MIB:
            break
        room = 10*GIB-used-2*MIB
        if room <= 0:
            raise ValueError('archive staging cap reached; completed archives retained')
        row = stream_archive(p, room)
        report['records'].append(row)
        durable(args.output, report)  # Persist verified recovery mapping first.
        p.unlink()
    if (source_identity(root) != source or assembly6.interfaces(root) != pool or
            any(assembly6.sha(Path(p)) != digest for p,digest in protected.items())):
        raise ValueError('protected historical source, interface or receipt changed')
    final = allocated(runs)
    report.update(status='complete', finished_utc=utc(), final_runs_bytes=final,
        sources_unchanged=True, interfaces_unchanged=True, receipts_unchanged=True,
        recovered_headroom_bytes=10*GIB-final,
        original_bytes=sum(r['original_bytes'] for r in report['records']),
        archive_bytes=sum(r['archive_bytes'] for r in report['records']))
    durable(args.output, report)
    if final > 10*GIB-args.headroom_mib*MIB:
        raise ValueError('requested recovered headroom unavailable')
    print(json.dumps({k:v for k,v in report.items() if k not in ('records','protected_receipts')}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--headroom-mib', type=int, choices=range(256,1025), default=512)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
