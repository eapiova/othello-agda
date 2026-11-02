#!/usr/bin/env python3
"""Losslessly archive completed accepted warning logs; never touch proofs.

The original log digest, compressed digest and reversible path mapping are
recorded. JSON receipts, failed logs, all Agda sources and all interfaces stay
unchanged. This is disk housekeeping under an outer coordinator reservation.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path

import assembly6
from provenance import source_identity
from run_job import atomic_json


def archive(path,expected):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('original log hash differs')
    target=path.with_suffix(path.suffix+'.gz')
    if target.exists():raise ValueError('archive already exists')
    packed=gzip.compress(raw,compresslevel=1,mtime=0)
    if gzip.decompress(packed)!=raw:raise ValueError('archive round trip failed')
    temporary=target.with_name(target.name+'.tmp')
    with temporary.open('xb') as stream:
        stream.write(packed);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,target)
    if hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest()!=expected:
        raise ValueError('written archive does not recover original log')
    row=dict(original_name=path.name,archive_name=target.name,original_sha256=expected,
             archive_sha256=assembly6.sha(target),original_bytes=len(raw),archive_bytes=len(packed))
    path.unlink()  # Raw bytes are retained verbatim in the verified gzip archive.
    return row


def run(args):
    previous=args.previous.resolve()
    saved=(previous/'final.json').exists()
    final_path=previous/('final.json' if saved else 'packed.json')
    final=json.loads(final_path.read_text())
    audit=json.loads((previous/'phase-records.json').read_text())
    continued=not saved and 'resumed_from' in final
    donor=(Path(final['resumed_from'])/'check' if continued else
           previous/('collector' if saved else 'check'))
    identity=source_identity(donor);pool=assembly6.interfaces(donor)
    if saved:
        valid=(assembly6.sha(final_path)==audit['final_sha256'] and
               final['status']=='collector-failed' and final['completed_groups']==list(range(10)) and
               pool==audit['collector_interfaces'])
    elif continued:
        valid=(final['status']=='collector-failed' and not final['accepted'] and
               final['completed_groups']==list(range(10)) and
               final['checked_sample_upper_roots']==100 and len(final['phases'])==274 and
               all(phase['accepted'] for phase in final['phases'][:-1]) and
               not final['phases'][-1]['accepted'] and
               final['prefix_sources_unchanged'] and final['prefix_interface_hashes_unchanged'] and
               pool==audit['final_interfaces'] and len(pool)==305)
    else:
        valid=(final['status']=='artifact-budget-stopped' and not final['accepted'] and
               final['completed_groups']==list(range(6)) and
               len(final['phases'])==173 and all(phase['accepted'] for phase in final['phases']) and
               pool==audit['final_interfaces'] and len(pool)==205)
    if not valid or identity['source_sha256']!=final['source_sha256']:
        raise ValueError('requires a verified completed or disk-stopped checkpoint')
    labels=([phase['label'] for phase in final['phases'][173:]] if continued
            else list(audit['records']))
    selected=[]
    for label in labels:
        record=audit['records'][label]
        if not record['accepted']:continue
        path=previous/'records'/f'{label}.log'
        expected=audit['log_hashes'][path.name if saved else label]
        if assembly6.sha(path)!=expected:
            raise ValueError('a selected completed log differs before archival')
        selected.append((path,expected))
    if continued and len(selected)!=100:
        raise ValueError('requires exactly the 100 accepted continuation logs')
    receipt=dict(format='othello-warning-log-archives6-v1',
                 scope='accepted completed warning logs only; original bytes recoverable with gzip',
                 records=[],donor_sources_sha256=identity['source_sha256'],
                 final_report_sha256=assembly6.sha(final_path),
                 phase_audit_sha256=assembly6.sha(previous/'phase-records.json'),
                 continuation_only=continued)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for path,expected in selected:
        receipt['records'].append(archive(path,expected))
        atomic_json(args.output,receipt)
    if source_identity(donor)!=identity or assembly6.interfaces(donor)!=pool:
        raise ValueError('a proof donor changed during log archival')
    receipt.update(donor_sources_unchanged=True,donor_interfaces_unchanged=True,
                   original_log_bytes=sum(row['original_bytes'] for row in receipt['records']),
                   archived_log_bytes=sum(row['archive_bytes'] for row in receipt['records']))
    atomic_json(args.output,receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='records'}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args())


if __name__=='__main__':main()
