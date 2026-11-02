#!/usr/bin/env python3
"""Finish a frozen shard pilot without retaining its native graph in memory.

AI-assisted. Accepted earlier records, source manifests and compiler identity
are checked before their interfaces are reused. The unfinished shard is cold.
The original failed envelope is retained and charged separately.
"""
import argparse
import json
from pathlib import Path
import shutil

import assembly6
import bench6
from provenance import source_files, source_identity
from run_job import atomic_json, run_job


def run(args):
    old = args.previous.resolve()
    report = json.loads((old / 'assembly.json').read_text())
    machine = assembly6.machine_identity(args.agda)
    if report['machine'] != machine:
        raise ValueError('same machine, boot and Agda binary are required')
    completed = len(report['parts'])
    if not completed or completed >= report['actual_shards']:
        raise ValueError('requires an unfinished pilot with accepted earlier shards')
    if any(not p['accepted'] for p in report['parts']):
        raise ValueError('earlier shard was rejected')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    accepted_sources = set()
    for i in range(completed):
        record = json.loads((old / f'records/shared-part{i}.json').read_text())
        identity = source_identity(old / f'part{i}')
        if (not record['accepted'] or not record['source_unchanged'] or
                record['executable_sha256'] != machine['agda_sha256'] or
                identity['source_sha256'] != record['source_sha256']):
            raise ValueError('earlier record/source/binary evidence disagrees')
        accepted_sources.add(identity['source_sha256'])
    report['resumed_from'] = str(old)
    report['resume_scope'] = 'accepted dependencies reused; unfinished shard and assembly checked'
    atomic_json(output / 'assembly.json', report)
    donor = None
    for i in range(completed, report['actual_shards']):
        root = old / f'part{i}'
        if source_identity(root)['source_sha256'] not in accepted_sources:
            raise ValueError('unfinished shard source differs from accepted dependency roots')
        suffix = f'/Tests/SharedAssembly6/Part{i}.agdai'
        for p in root.rglob('*.agdai'):
            if p.as_posix().endswith(suffix):
                p.unlink()
        if donor is not None:
            for rel,digest in assembly6.interfaces(donor).items():
                target = root / rel
                if target.exists():
                    if assembly6.sha(target) != digest:
                        raise ValueError('conflicting dependency interface')
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(donor / rel, target)
        record = run_job(f'shared-resumed-part{i}', [args.agda,*assembly6.FLAGS,'-i','src',
            f'src/Tests/SharedAssembly6/Part{i}.agda','+RTS','-M1200M','-RTS'],
            output/'records', root=root, cpu_limit=600, timeout=900,
            rss_limit_gib=1.5, log_limit_mib=2,
            metadata={'machine':machine,'own_shard_cold':True,'resume':True})
        metrics = {k:record[k] for k in ['accepted','cpu_seconds','wall_seconds',
                   'peak_rss_gib','cache_state','stop_reason']}
        # Source sizing was enforced by the original generator. Do not invent
        # per-part token metrics when the failed envelope had not recorded them.
        report['parts'].append(metrics)
        atomic_json(output/'assembly.json',report)
        if not record['accepted']:
            return False
        donor = root
    root = output/'assembly'
    root.mkdir()
    for rel,data in source_files(donor):
        target=root/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    digest=bench6.refresh_manifest(root)['source_sha256']
    for rel,sha in assembly6.interfaces(donor).items():
        target=root/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(donor/rel,target)
        if assembly6.sha(target) != sha:
            raise ValueError('dependency transfer mismatch')
    record=run_job('shared-resumed-assembly',[args.agda,*assembly6.FLAGS,'-i','src',
        'src/Tests/SharedAssembly6/Check.agda','+RTS','-M1200M','-RTS'],
        output/'records',root=root,expected_source_sha256=digest,
        cpu_limit=180,timeout=300,rss_limit_gib=1.5,log_limit_mib=2,
        metadata={'machine':machine,'accepted_dependency_interfaces':True})
    report['assembly']={k:record[k] for k in ['accepted','cpu_seconds','wall_seconds',
                       'peak_rss_gib','cache_state','stop_reason']}
    report['accepted']=record['accepted'];atomic_json(output/'assembly.json',report)
    return record['accepted']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--agda',required=True)
    return 0 if run(parser.parse_args()) else 1


if __name__ == '__main__':raise SystemExit(main())
