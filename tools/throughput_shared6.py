#!/usr/bin/env python3
"""AI-assisted capped 1/2/4/8-shard throughput; run inside othello6.slice.

Each concurrent measurement has its own supervisor process and build root.
Dependency interfaces must originate from the same verified desktop compiler.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import assembly6
import bench6
from provenance import source_files, source_identity
from run_job import atomic_json


def run(args):
    origin = source_identity(args.donor)
    machine = assembly6.machine_identity(args.agda)
    report_file = args.donor.parent / 'assembly.json'
    if report_file.exists():
        previous = json.loads(report_file.read_text())
        if previous.get('machine') != machine:
            raise ValueError('dependency compiler or machine differs')
    files = list(source_files(args.donor))
    interfaces = assembly6.interfaces(args.donor)
    suffix = '/' + args.module.replace('.', '/') + '.agdai'
    if any(name.endswith(suffix) for name in interfaces):
        raise ValueError('donor already contains target shard interface')
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    report = {'format':'othello-shared-throughput6-v1', 'machine':machine,
              'source_sha256':origin['source_sha256'], 'module':args.module,
              'scope':'measured shard workload; not a production forecast', 'batches':[]}
    runner = Path(__file__).with_name('run_job.py').resolve()
    single_wall = None
    for slots in [1, 2, 4, 8]:
        roots = []
        for i in range(slots):
            root = output / f'p{slots}-{i}'; root.mkdir()
            for name, data in files:
                path=root/name; path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            digest=bench6.refresh_manifest(root)['source_sha256']
            for name, sha in interfaces.items():
                path=root/name; path.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(args.donor/name,path)
                if assembly6.sha(path)!=sha: raise ValueError('interface copy hash mismatch')
            roots.append((root,digest))
        processes=[]; started=time.monotonic()
        for i,(root,digest) in enumerate(roots):
            label=f'throughput-p{slots}-{i}'
            cmd=[sys.executable,str(runner),label,str(output/'records'),
                 '--root',str(root),'--expected-source-sha256',digest,
                 '--cpu-limit','90','--timeout','180','--rss-limit-gib','1.5',
                 '--log-limit-mib','2','--',args.agda,*assembly6.FLAGS,'-i','src',
                 'src/'+args.module.replace('.','/')+'.agda','+RTS','-M1200M','-RTS']
            processes.append((label,subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)))
        for _, process in processes: process.wait()
        wall=time.monotonic()-started
        records=[json.loads((output/'records'/f'{label}.json').read_text()) for label,_ in processes]
        accepted=all(r['accepted'] for r in records)
        if slots==1: single_wall=wall
        row={'slots':slots,'wall_seconds':wall,'accepted':accepted,
             'total_cpu_seconds':sum(r['cpu_seconds'] for r in records),
             'sum_peak_rss_gib':sum(r['peak_rss_gib'] for r in records),
             'effective_slots':slots*single_wall/wall,
             'cold_target_shards':True,'verified_dependency_interfaces':True}
        report['batches'].append(row);atomic_json(output/'throughput.json',report)
        if not accepted: return False
    report['accepted']=True
    atomic_json(output/'throughput.json',report)
    return True


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--donor',type=Path,required=True)
    p.add_argument('--module',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    return 0 if run(p.parse_args()) else 1

if __name__=='__main__': raise SystemExit(main())
