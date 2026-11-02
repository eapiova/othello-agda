#!/usr/bin/env python3
"""Detached bounded validation and full-initial native layout measurements.

These are untrusted feasibility statistics. This job cannot yield an Agda
premise, authorize production, or claim the initial theorem or optimal pair.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
import unittest

import assembly6
from owner_cache_dedup6 import allocated
from provenance import source_identity
from run_job import atomic_json, run_job, utc
import solve6
import test_wire_layout6 as fixtures
import wire_layout6 as layout


def run(args):
    root = Path.cwd().resolve()
    output = args.output.resolve()
    if output.exists() or 'results' not in output.parts:
        raise ValueError('fresh bounded results directory required')
    output.mkdir(parents=True)
    origin = source_identity(root)
    protected_solver = solve6.sha256(solve6.SOURCE)
    report = dict(format='othello-unattended-layout6-v1', status='validating',
        accepted=False, created_utc=utc(), source=origin, phases=[],
        initial_problem2_proved=False, optimal_pair_proved=False,
        production_authorized=False, laptop_required_during_execution=False,
        scope='complete native initial-board partition and import-closure statistics only')

    def save():
        atomic_json(output/'report.json', report)

    def guard():
        used = allocated(root.parent)
        free = shutil.disk_usage(root).free
        if used >= 10*1024**3 or free < 100*1024**3:
            report['status'] = 'storage-stop'
            save()
            raise ValueError('desktop storage gate reached; measurements preserved')
        report['last_storage_gate'] = dict(allocated_runs_bytes=used,
            free_bytes=free, checked_utc=utc())
        save()

    save()
    guard()
    suite = unittest.defaultTestLoader.discover('tools', pattern='test_wire_layout6.py')
    tested = unittest.TextTestRunner(verbosity=1).run(suite)
    report['unit_tests'] = tested.testsRun
    if not tested.wasSuccessful():
        report['status'] = 'unit-validation-failed'
        save()
        return False
    unpinned, pinned = output/'unpinned', output/'pinned'
    layout.build(SimpleNamespace(output=unpinned, line=None))
    layout.build(SimpleNamespace(output=pinned, line=Path('certificates/six-line.json')))
    for name, build, is_pinned in (('unpinned', unpinned, False), ('pinned', pinned, True)):
        guard()
        tests = output/(name+'-tests.json')
        fixtures.run(SimpleNamespace(build=build, reference_build=args.reference_build,
            output=tests, pinned=is_pinned))
        report['phases'].append(dict(label=name+'-fixtures', accepted=True,
            report=str(tests), report_sha256=assembly6.sha(tests),
            build_sha256=assembly6.sha(build/'build.json')))
        save()
    for direction in ('lower', 'upper'):
        guard()
        label = 'initial-'+direction
        data = output/(label+'.json')
        report['status'] = 'measuring-'+label
        save()
        command = [sys.executable, 'tools/wire_layout6.py', 'run', '--counts-only',
            '--build', str(pinned), '--tests', str(output/'pinned-tests.json'),
            '--donor', str(args.native_donor.resolve()), '--output', str(data),
            '--direction', direction, '--native-cpu', str(args.native_cpu),
            '--max-states', '70000000', '--inline-limit', '256',
            '--max-entries', '200', '--max-tokens', '32000',
            '--layout-limit-mib', '512']
        measured = run_job(label, command, output/'records', root=root,
            expected_source_sha256=origin['source_sha256'],
            cpu_limit=args.native_cpu+60, timeout=args.native_cpu+210,
            rss_limit_gib=8.25, log_limit_mib=2,
            metadata=dict(direction=direction, root_key='initial',
                counts_only=True, proof_premise=False))
        payload = json.loads(data.read_text()) if data.is_file() else {}
        accepted = bool(measured['accepted'] and payload.get('layout_complete') is True and
            payload.get('donor_unchanged') is True and payload.get('table_unchanged') is True)
        report['phases'].append(dict(label=label, accepted=accepted, record=measured,
            report=str(data), report_sha256=assembly6.sha(data) if data.is_file() else None,
            layout_complete=payload.get('layout_complete', False)))
        save()
        if not accepted:
            report['status'] = 'native-censored-or-failed'
            save()
            return False
    if source_identity(root) != origin or solve6.sha256(solve6.SOURCE) != protected_solver:
        raise ValueError('protected source changed')
    report.update(status='complete-untrusted-layout', accepted=True,
        finished_utc=utc(), source_unchanged=True, original_solver_unchanged=True)
    save()
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--reference-build', type=Path, required=True)
    p.add_argument('--native-donor', type=Path, required=True)
    p.add_argument('--native-cpu', type=int, choices=range(60,3001), default=3000)
    args = p.parse_args()
    return 0 if run(args) else 1


if __name__ == '__main__':
    raise SystemExit(main())
