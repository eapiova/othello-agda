#!/usr/bin/env python3
"""Cold isolated kernel checks inside one supervised study reservation.

Each worker is a separate run_job process with its own source and build lock.
Finished build directories are disposable; their frozen manifest, generated
proof text, job metadata and full measured JSON/log remain in the batch output.
No interfaces are transported. Resource failures are retained as observations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import bench6
from provenance import source_identity
from run_job import atomic_json, positive, utc

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--agda', default='agda')
    parser.add_argument('--concurrency', type=int, choices=range(1, 9), default=1)
    parser.add_argument('--state-id', action='append')
    parser.add_argument('--rules', choices=('rules', 'fast', 'both'), default='both')
    parser.add_argument('--search-kind', choices=('evidence', 'boolean'), default='evidence')
    parser.add_argument('--skip-label', action='append', default=[])
    parser.add_argument('--cpu-limit', type=positive, default=100)
    parser.add_argument('--timeout', type=positive, default=180)
    parser.add_argument('--rss-limit-gib', type=positive, default=1.5)
    parser.add_argument('--heap-mib', type=int, default=1200)
    parser.add_argument('--keep-roots', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'results'):
        parser.error('batch output must be inside this source snapshot results/')
    output.mkdir(parents=True, exist_ok=False)
    binary = Path(shutil.which(args.agda) or args.agda).resolve(strict=True)
    version = subprocess.check_output([str(binary), '--version'], text=True).strip()
    if not version.startswith('Agda version '):
        parser.error('expected an Agda executable')
    data = json.loads(args.dataset.read_text())
    if not data.get('native_complete'):
        parser.error('dataset must have complete measured mirror counts')
    rows = [r for r in data['states'] if args.state_id is None or r['id'] in args.state_id]
    if not rows or (args.state_id and set(args.state_id) != {r['id'] for r in rows}):
        parser.error('unknown or empty benchmark selection')
    prefix = 'boolean6' if args.search_kind == 'boolean' else 'bench6'
    selected_rules = ('rules', 'fast') if args.rules == 'both' else (args.rules,)
    cases = [(r, rules, direction) for r in rows for rules in selected_rules
             for direction in ('lower', 'upper')
             if f"{prefix}-{r['id']}-{rules}-{direction}" not in args.skip_label]
    records, pending = output / 'records', output / 'pending'
    records.mkdir(); pending.mkdir()
    state = {'format': 'othello-kernel-batch6-v1', 'source': source_identity(ROOT),
             'dataset_sha256': hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
             'agda_path': str(binary), 'agda_version': version,
             'agda_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
             'concurrency': args.concurrency, 'per_job_cpu_limit': args.cpu_limit,
             'search_kind': args.search_kind, 'selected_rules': list(selected_rules),
             'per_job_rss_limit_gib': args.rss_limit_gib, 'total_cases': len(cases),
             'completed': [], 'active': [], 'started_utc': utc(), 'finished_utc': None}
    running = {}

    def save():
        state['active'] = list(running)
        atomic_json(output / 'batch.json', state)

    save()
    while cases or running:
        while cases and len(running) < args.concurrency:
            if shutil.disk_usage(ROOT).free < 100 * 1024**3:
                state['waiting_for_disk_gate'] = True
                break
            state['waiting_for_disk_gate'] = False
            row, rules, direction = cases.pop(0)
            job = bench6.freeze(row, rules, direction, pending, root=ROOT, search_kind=args.search_kind)
            label, root = job['label'], Path(job['root'])
            command = [str(binary), '--no-libraries', '--safe', '--without-K',
                       '--cubical-compatible', '-i', 'src', 'src/Tests/Bench6/Check.agda',
                       '+RTS', f'-M{args.heap_mib}M', '-RTS']
            job.update(command=command, generated_proof=(root/'src/Tests/Bench6/Check.agda').read_text())
            atomic_json(records / (label + '.job.json'), job)
            shutil.copy2(root/'SNAPSHOT.json', records/(label+'.manifest.json'))
            argv = [sys.executable, str(ROOT/'tools/run_job.py'), label, str(records),
                    '--root', str(root), '--expected-source-sha256', job['source_sha256'],
                    '--cpu-limit', str(args.cpu_limit), '--timeout', str(args.timeout),
                    '--rss-limit-gib', str(args.rss_limit_gib), '--log-limit-mib', '2',
                    '--', *command]
            process = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            running[label] = (process, root)
            save()
        for label, (process, root) in list(running.items()):
            if process.poll() is None:
                continue
            _, stderr = process.communicate()
            record_path = records / (label+'.json')
            if not record_path.exists():
                (records/(label+'.supervisor-error.log')).write_bytes(stderr)
                raise RuntimeError('missing measured record for '+label)
            record = json.loads(record_path.read_text())
            state['completed'].append({'label': label, 'accepted': record['accepted'],
                                       'cpu_seconds': record['cpu_seconds'],
                                       'peak_rss_gib': record['peak_rss_gib'],
                                       'stop_reason': record['stop_reason']})
            del running[label]
            if not args.keep_roots:
                assert root.is_relative_to(pending)
                shutil.rmtree(root)
            save()
        if cases or running:
            time.sleep(.2)
    state['finished_utc'] = utc()
    state['accepted_count'] = sum(r['accepted'] for r in state['completed'])
    # The batch's completion means measurements were saved, not all proofs passed.
    atomic_json(output / 'analysis.json', bench6.analyze(sorted(records.glob('*.job.json')),
                                                       sorted(p for p in records.glob('*.json')
                                                              if not p.name.endswith(('.job.json','.manifest.json')))))
    save()
    print(json.dumps({'measurements': len(state['completed']), 'accepted': state['accepted_count'],
                      'report': str(output/'batch.json')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
