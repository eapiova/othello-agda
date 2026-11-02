#!/usr/bin/env python3
"""Combine cold benchmark attempts without hiding unstarted sample jobs.

Result directories contain .job.json metadata and measured .json/.log files.
Exactly one attempt per label must be selected. No solver is run by this tool.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import bench6
from run_job import atomic_json


def report(dataset, directories, singles, *, search_kind='evidence', rules=('rules', 'fast')):
    jobs, records = {}, {}
    for directory in directories:
        for path in sorted(directory.glob('*.job.json')):
            label = json.loads(path.read_text())['label']
            if label in jobs:
                raise ValueError('select one job attempt per label: ' + label)
            jobs[label] = path
        for path in sorted(directory.glob('*.json')):
            if path.name.endswith(('.job.json', '.manifest.json')):
                continue
            record = json.loads(path.read_text())
            if record.get('format') != 'othello-job-v2':
                continue
            label = record['label']
            if label in records:
                raise ValueError('select one measured attempt per label: ' + label)
            records[label] = path
    for job, record in singles:
        label = json.loads(job.read_text())['label']
        if label in jobs or label in records:
            raise ValueError('duplicate single job: ' + label)
        jobs[label], records[label] = job, record
    if set(records) - set(jobs):
        raise ValueError('measured records without frozen job metadata')
    identities = {(json.loads(path.read_text())['executable_sha256'],
                   json.loads(path.read_text()).get('machine'))
                  for path in records.values()}
    if len(identities) > 1:
        raise ValueError('different Agda binaries or machines require separate cost reports')
    if any(json.loads(p.read_text()).get('search_kind', 'evidence') != search_kind for p in jobs.values()):
        raise ValueError('different search implementation from the requested sample')
    result = bench6.analyze(list(jobs.values()), list(records.values()))
    rows = result['observations']
    expected = {}
    for state in dataset['states']:
        for rule in rules:
            for direction in ('lower', 'upper'):
                prefix = 'boolean6' if search_kind == 'boolean' else 'bench6'
                label = f"{prefix}-{state['id']}-{rule}-{direction}"
                expected[label] = dict(label=label, state_id=state['id'],
                    empties=state['empties'], split=state['split'], rules=rule,
                    direction=direction, state=state['state'], threshold=state['value'],
                    native_W=state['mirror'][direction]['nodes'], status='unmeasured')
    if set(jobs) - set(expected):
        raise ValueError('job outside the frozen dataset')
    for row in rows:
        reference = expected[row['label']]
        for key in ('state', 'threshold', 'native_W', 'split', 'empties'):
            if row[key] != reference[key]:
                raise ValueError('job differs from frozen dataset: ' + row['label'])
    rows.extend(expected[label] for label in sorted(set(expected) - set(jobs)))
    for rule in ('rules', 'fast'):
        for direction in ('lower', 'upper'):
            pooled = [r for r in rows if (r['rules'], r['direction']) == (rule, direction)]
            result['combined_rules_direction'][f'{rule}/{direction}'] = bench6.summarize_group(pooled)
            for empties in (8, 10, 12):
                group = [r for r in pooled if r['empties'] == empties]
                result['groups'][f'{rule}/{direction}/{empties}'] = bench6.summarize_group(group)
    result.update(expected_jobs=len(expected), measured_jobs=len(records),
                  measurements_complete=len(records) == len(expected),
                  agda_binary_sha256=next(iter(identities))[0] if identities else None,
                  machine=next(iter(identities))[1] if identities else None,
                  search_kind=search_kind, selected_rules=list(rules),
                  initial_state_W=None, production_gate='pending-global-work-and-resource-validation')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--directory', type=Path, action='append', default=[])
    parser.add_argument('--single', type=Path, nargs=2, action='append', default=[],
                        metavar=('JOB', 'RECORD'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--search-kind', choices=('evidence', 'boolean'), default='evidence')
    parser.add_argument('--rules', choices=('rules', 'fast', 'both'), default='both')
    args = parser.parse_args()
    rules = ('rules', 'fast') if args.rules == 'both' else (args.rules,)
    result = report(json.loads(args.dataset.read_text()), args.directory, args.single,
                    search_kind=args.search_kind, rules=rules)
    atomic_json(args.output, result)
    print(json.dumps({key: result[key] for key in
          ('expected_jobs', 'measured_jobs', 'measurements_complete', 'production_gate')}))


if __name__ == '__main__':
    main()
