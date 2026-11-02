#!/usr/bin/env python3
"""Validate extrema counters against the full scalar-replayed small export."""
import argparse
import json
from pathlib import Path

import check_native_layout_samples6 as fixtures
import native_layout_extrema6 as extrema
from run_job import atomic_json


def run(args):
    original = fixtures.sample
    fixtures.sample = extrema
    try:
        fixtures.run(args)
    finally:
        fixtures.sample = original
    out = args.output.resolve()
    report = json.loads((out / 'report.json').read_text())
    comparisons = []
    for index, receipt in enumerate(report['cases']):
        if not receipt['case']['holds']:
            continue
        native = json.loads((out / ('fixture' + str(index) + '-sample.json')).read_text())
        counts = json.loads(native['stdout'])
        entries = [dict(state=k, certificate=c, references=sorted(rs))
                   for k, c, rs in fixtures.wire.records(out / ('fixture' + str(index) + '.wire'))]
        parts, owners = fixtures.assembly.partition(entries, max_entries=2, max_tokens=32000)
        measured = []
        for j, part in enumerate(parts):
            refs = {r for row in part for r in row['references'] if owners[r] != j}
            measured.append(dict(imported_citations=len(refs),
                direct_dependencies=len({owners[r] for r in refs}),
                tokens=sum(fixtures.assembly.tokens(row['certificate']) for row in part)))
        expected = {}
        for feature, key in (('imported_citations', 'layout_imported_citations_max_part'),
                             ('direct_dependencies', 'layout_direct_dependencies_max_part'),
                             ('tokens', 'layout_max_part_tokens_part')):
            expected[key] = max(range(len(parts)), key=lambda j: measured[j][feature])
            assert counts[key] == expected[key], (index, key, counts[key], expected[key])
        assert extrema.extrema(counts) == sorted(set(expected.values()))
        comparisons.append(dict(fixture=index, expected=expected))
    assert comparisons
    report.update(format='othello-native-layout-extrema-fixtures6-v1',
        first_maximum_indices_checked=True, extrema_comparisons=comparisons,
        scope='native counter indices only; complete small scalar replay unchanged; no Agda premise')
    atomic_json(out / 'report.json', report)
    print(json.dumps(dict(accepted=True, extrema_fixtures=len(comparisons))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args())
