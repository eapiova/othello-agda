#!/usr/bin/env python3
"""Bounded reference and scalar validation of the inline-cut exporter.

This is untrusted tool validation, never an Agda premise. The existing native
counter, scalar certificate and pinned-line fixtures run against each build.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import solve6
import test_census_wire6 as fixtures
import wire_cuts6 as cuts
from run_job import atomic_json, utc


def run(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    suite = unittest.TestSuite()
    for pattern in ('test_wire_workflow6.py', 'test_census_wire6.py',
                    'test_wire_pilot6.py', 'test_unattended_wire6.py'):
        suite.addTests(unittest.defaultTestLoader.discover('tools', pattern=pattern))
    tested = unittest.TextTestRunner(verbosity=1).run(suite)
    if not tested.wasSuccessful():
        raise ValueError('exporter/workflow unit fixtures rejected')

    unpinned = output / 'unpinned'
    pinned = output / 'pinned'
    cuts.build(SimpleNamespace(output=unpinned, line=None))
    cuts.build(SimpleNamespace(output=pinned, line=Path('certificates/six-line.json')))
    receipts = {}
    for label, limit in (('default', 256), ('aggressive', 1)):
        folder = output / label
        folder.mkdir()
        report = folder / 'tests.json'
        fixtures.run(SimpleNamespace(build=unpinned, reference_build=args.reference_build,
                                     output=report),
                     build_validator=cuts.checked_build,
                     source_generator=cuts.generated_source,
                     native_options=['--wire-inline-limit', str(limit)],
                     max_body_tokens=1 + 36 * max(2, limit))
        receipts[label] = dict(path=str(report), sha256=solve6.sha256(report))
    folder = output / 'pinned-tests'
    folder.mkdir()
    report = folder / 'tests.json'
    fixtures.pinned_run(SimpleNamespace(build=pinned, output=report),
                        build_validator=cuts.checked_build,
                        native_options=['--wire-inline-limit', '1'], max_body_tokens=73)
    receipts['pinned'] = dict(path=str(report), sha256=solve6.sha256(report))
    result = dict(format='othello-wire-cuts6-validation-v1', accepted=True,
                  created_utc=utc(), unit_tests=tested.testsRun, receipts=receipts,
                  unpinned_build_sha256=solve6.sha256(unpinned/'build.json'),
                  pinned_build_sha256=solve6.sha256(pinned/'build.json'),
                  max_body_tokens=9217, aggressive_max_body_tokens=73,
                  original_solver_sha256=solve6.sha256(solve6.SOURCE),
                  initial_problem2_proved=False, production_authorized=False,
                  trust='native/scalar fixtures only; no proof premise')
    atomic_json(output/'report.json', result)
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args)


if __name__ == '__main__':
    main()
