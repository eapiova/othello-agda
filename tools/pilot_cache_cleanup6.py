#!/usr/bin/env python3
"""Remove only redundant private generic caches from completed API pilots.

All own proof interfaces, immutable sources, measurements and the canonical
305-interface donor stay unchanged. A hashed receipt records every removed
cache and the retained proofs. This is reproducible cache housekeeping.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import assembly6
from provenance import source_identity
from run_job import atomic_json


def run(args):
    previous=args.previous.resolve()
    final=json.loads((previous/'packed.json').read_text())
    audit=json.loads((previous/'phase-records.json').read_text())
    donor=Path(final['resumed_from'])/'check'
    identity=source_identity(donor);pool=assembly6.interfaces(donor)
    if pool!=audit['final_interfaces'] or len(pool)!=305 or identity['source_sha256']!=final['source_sha256']:
        raise ValueError('canonical donor differs')
    generic={name for name in pool if '/Tests/PackedTables6/' not in name}
    if len(generic)!=32:raise ValueError('wrong generic cache set')
    jobs=[]
    for pilot in args.pilot:
        pilot=pilot.resolve();root=pilot/'check'
        name='scope.json' if (pilot/'scope.json').exists() else 'warning.json'
        result=json.loads((pilot/name).read_text())
        details=json.loads((pilot/'phase-records.json').read_text())
        before=assembly6.interfaces(root);source=source_identity(root)
        if (result['status'] not in ('complete','phase-failed') or
                not result['donor_sources_unchanged'] or not result['donor_interfaces_unchanged'] or
                source['source_sha256']!=result['source_sha256'] or before!=details['final_interfaces'] or
                not generic<=before.keys()):
            raise ValueError('requires an unchanged completed private pilot')
        own={n:h for n,h in before.items() if n not in generic}
        if not own or any('/Tests/' not in n and '/Othello/ProofFacade6.agdai' not in n for n in own):
            raise ValueError('unexpected own pilot interfaces')
        jobs.append((pilot,root,source,before,own))
    receipt=dict(format='othello-pilot-generic-cache-cleanup6-v1',
        scope='temporary private generic caches only; own proof interfaces and canonical pool retained',
        canonical_source_sha256=identity['source_sha256'],canonical_interfaces=pool,pilots=[])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for pilot,root,source,before,own in jobs:
        removed={name:dict(sha256=before[name],bytes=(root/name).stat().st_size) for name in sorted(generic)}
        for name in sorted(generic):(root/name).unlink()
        if assembly6.interfaces(root)!=own or source_identity(root)!=source:
            raise ValueError('own proof or source changed during cleanup')
        receipt['pilots'].append(dict(pilot=str(pilot),source_sha256=source['source_sha256'],
            removed=removed,retained_own_interfaces=own,own_interfaces_unchanged=True,sources_unchanged=True))
        atomic_json(args.output,receipt)
    if assembly6.interfaces(donor)!=pool or source_identity(donor)!=identity:
        raise ValueError('canonical donor changed during cleanup')
    receipt.update(canonical_sources_unchanged=True,canonical_interfaces_unchanged=True,
                   removed_private_bytes=sum(row['bytes'] for p in receipt['pilots'] for row in p['removed'].values()))
    atomic_json(args.output,receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('pilots','canonical_interfaces')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--pilot',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    run(p.parse_args())
