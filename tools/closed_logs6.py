#!/usr/bin/env python3
"""Losslessly archive completed old root-local accepted check logs.

This never adopts an old cache as a proof dependency. Capture and preserve its
current bytes, including quarantined historical caches, without restoring them.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import assembly6
from compact_logs6 import archive
from provenance import digest_entries,source_identity
from run_job import atomic_json


def current_interfaces(root):
    # Historical immutable copies are hardlinks; hash each inode once.
    seen={};files={}
    for path in root.rglob('*.agdai'):
        stat=path.stat();key=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)
        if key not in seen:seen[key]=assembly6.sha(path)
        files[path.relative_to(root).as_posix()]=seen[key]
    return files


def run(args):
    previous=args.previous.resolve();final_path=previous/'closed.json'
    final=json.loads(final_path.read_text())
    if (assembly6.sha(final_path)!=args.expected_report_sha256 or
            final['status']!='collector-failed' or final['accepted'] or
            final['checked_sample_upper_roots']!=100):
        raise ValueError('requires the recorded completed original root-local pilot')
    source=source_identity(previous/'all100');interfaces=current_interfaces(previous)
    failed=json.loads((previous/'records/all100.json').read_text())
    if source['source_sha256']!=failed['source_sha256']:
        raise ValueError('historical source bytes differ')
    selected=[]
    for path in sorted((previous/'records').glob('*.json')):
        record=json.loads(path.read_text())
        if not record['accepted']:continue
        log=path.with_suffix('.log')
        if (not record['source_unchanged'] or not record['expected_source_matches'] or
                log.stat().st_size!=record['log_bytes']):
            raise ValueError('an old accepted receipt or its log differs')
        selected.append((path,log,assembly6.sha(log)))
    if len(selected)!=146:raise ValueError('different historical accepted-log set')
    receipt=dict(format='othello-closed-log-archives6-v1',records=[],
        scope='accepted historical logs only; no old-cache adoption or restoration',
        report_sha256=args.expected_report_sha256,source_sha256=source['source_sha256'],
        current_interfaces_sha256=digest_entries(interfaces),
        raw_digests_captured_at_archival=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for record,log,digest in selected:
        row=archive(log,digest);row['receipt_sha256']=assembly6.sha(record)
        receipt['records'].append(row);atomic_json(args.output,receipt)
    if source_identity(previous/'all100')!=source or current_interfaces(previous)!=interfaces:
        raise ValueError('a historical source or cache changed during archival')
    receipt.update(sources_unchanged=True,current_interfaces_unchanged=True,
        original_log_bytes=sum(r['original_bytes'] for r in receipt['records']),
        archived_log_bytes=sum(r['archive_bytes'] for r in receipt['records']))
    atomic_json(args.output,receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='records'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--expected-report-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    run(p.parse_args())
