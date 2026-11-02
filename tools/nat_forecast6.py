#!/usr/bin/env python3
"""Freeze a prospective numeric-row cost model before a fixed unseen suffix.

Statistical evidence only. It excludes whole-root assembly, setup, throughput
and full initial production; a passing suffix cannot authorize production.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import assembly6
from nat_indexed_pilot6 import ALPHABET
from owner_continue6 import nnls
from provenance import source_identity
from run_job import atomic_json, utc
from wire_workflow6 import require

TRAINING = tuple(range(100))
HELDOUT = tuple(i for i in range(200, 267) if i != 231)
FEATURES = ['certificate nodes/1000', 'move nodes/1000', 'dependency state rows/1000', 'intercept']


def numeric_stats(text):
    position = 0
    counts = {k: 0 for k in 'LKRPCFS'}
    refs = []

    def code(bound):
        nonlocal position
        require(position < len(text) and text[position] in ALPHABET, 'missing grammar count')
        result = ALPHABET.index(text[position])
        position += 1
        require(result <= bound, 'grammar count exceeds bound')
        return result

    def reference():
        nonlocal position
        start = position
        value = 0
        while position < len(text) and text[position] in ALPHABET:
            value = value * 37 + ALPHABET.index(text[position])
            position += 1
        require(position > start and position < len(text) and text[position] == ';'
                and value < 20000000, 'invalid numeric reference')
        position += 1
        refs.append(value)

    def body():
        nonlocal position
        require(position < len(text) and text[position] in counts, 'unknown or missing certificate token')
        token = text[position]
        counts[token] += 1
        position += 1
        if token == 'L':
            return
        if token == 'K':
            reference()
        elif token == 'R':
            code(7)
            reference()
        elif token == 'P':
            body()
        elif token == 'C':
            code(35)
            body()
        elif token == 'F':
            for _ in range(code(36)):
                body()
        elif token == 'S':
            start = position
            while position < len(text) and text[position] in '0123456789':
                position += 1
            require(position > start and position < len(text) and text[position] == ';'
                    and int(text[start:position]) <= 128, 'invalid solve fuel')
            position += 1

    rows = 0
    while position < len(text):
        body()
        rows += 1
    require(rows > 0, 'empty certificate data')
    return dict(rows=rows, tokens=sum(counts.values()), move_nodes=sum(counts[k] for k in 'PCF'),
        references=len(refs), referenced_ids=sorted(set(refs)), kinds=counts, encoded_bytes=len(text))


def features(row):
    require(row['kinds']['S'] == 0, 'native solve cost is unsupported by this model')
    return [row['tokens'] / 1000, row['move_nodes'] / 1000, row['dependency_state_rows'] / 1000, 1.]


def prediction(rows, measurements):
    require(len(rows) == 267 and [r['part'] for r in rows] == list(range(267)), 'complete frozen row features required')
    require(set(measurements) == set(TRAINING), 'exact fixed training set required')
    fitted = nnls([dict(x=features(rows[i]), cpu_seconds=measurements[i]) for i in TRAINING], len(FEATURES))
    expected = [sum(c * x for c, x in zip(fitted['coefficients'], features(row))) for row in rows]
    require(all(v > 0 for v in expected), 'nonpositive prediction')
    return dict(format='othello-nat-forecast6-v1', created_utc=utc(), model=fitted,
        feature_names=FEATURES, training_indices=list(TRAINING), heldout_indices=list(HELDOUT),
        excluded_known_alternate_variant_indices=[231], heldout_measured_when_fitted=False,
        rows=[dict(row, predicted_cpu_seconds=expected[row['part']]) for row in rows],
        heldout_predicted_cpu_seconds=sum(expected[i] for i in HELDOUT),
        all_parts_predicted_cpu_seconds=sum(expected), gate_relative_error=.30,
        whole_workflow_validated=False, production_authorized=False, initial_problem2_proved=False,
        scope='cold own row checks with warm generic/state-data caches; only fixed suffix is prospectively held out',
        limitations=['Training prefix and late suffix may have different board distributions.',
            'Assembly, driver/setup overhead, cold state data, artifact totals and concurrency are excluded.',
            'No full initial-board forecast or production GO follows from this model.'])


def run(args):
    previous = args.previous.resolve()
    require(source_identity(previous)['source_sha256'] == args.expected_previous_source_sha256,
            'predecessor frozen source changed')
    base = previous / 'results/nat-descendant6'
    raw = (base / 'report.json').read_bytes()
    prior = json.loads(raw)
    check = base / 'check'
    source = source_identity(check)
    require(source == prior['checked_source'] and source['source_sha256'] == args.expected_check_source_sha256
            and prior['machine']['agda_sha256'] == args.expected_agda_sha256
            and prior['accepted_parts'] < HELDOUT[0] - 1, 'fixed holdout has started or source/compiler differs')
    require(not prior['initial_problem2_proved'] and not prior['production_authorized'], 'initial production excluded')
    layout = prior['layout']
    require(layout['parts'] == 267 and layout['rows'] == 53217, 'exact complete descendant required')
    states = []
    for i in range(267):
        state_source = (check / f'src/Tests/IndexedWire6/StateData{i}.agda').read_text()
        states.append(int(re.search(r'^states : B\.Vec \(State six\) ([0-9]+)$', state_source, re.M)[1]))
    rows = []
    for i in range(267):
        path = check / f'src/Tests/NatDescendant6/BodyData{i}.agda'
        require(assembly6.sha(path) == layout['generated_sha256'][path.relative_to(check).as_posix()],
                'generated body data changed')
        text = re.search(r'^text = "([^"]*)"$', path.read_text(), re.M)[1]
        row = numeric_stats(text)
        require(row['rows'] == states[i], 'decoded row count differs')
        deps = {i} | {rank // 200 for rank in row['referenced_ids']}
        require(all(d < 267 for d in deps), 'reference outside this descendant')
        for rank in row['referenced_ids']:
            require(rank % 200 < states[rank // 200], 'reference points into a missing row')
        row.update(part=i, dependency_state_rows=sum(states[d] for d in deps), dependencies=sorted(deps),
            body_source_sha256=assembly6.sha(path))
        rows.append(row)
    measurements = {}
    training = []
    for phase in prior['phases']:
        match = re.fullmatch(r'Tests\.NatDescendant6\.Part([0-9]+)', phase['target'])
        if not match or int(match[1]) not in TRAINING:
            continue
        i = int(match[1])
        rec = phase['record']
        require(rec['accepted'] and rec['exit_code'] == 0 and rec['stop_reason'] is None
            and rec['source_unchanged'] and rec['expected_source_matches'] and rec['own_target_cold']
            and rec['source_sha256'] == source['source_sha256']
            and rec['executable_sha256'] == args.expected_agda_sha256
            and phase['borrowed_interfaces_unchanged'], 'failed or changed training check')
        measurements[i] = rec['cpu_seconds']
        training.append(phase)
    result = prediction(rows, measurements)
    latest = json.loads((base / 'report.json').read_text())
    require(latest['accepted_parts'] < HELDOUT[0] - 1 and source_identity(check) == source,
            'holdout began during forecast generation')
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh forecast output required')
    out.mkdir(parents=True)
    result.update(training_report_sha256=hashlib.sha256(raw).hexdigest(), training_source=source,
        training_phases=training, machine=prior['machine'], observed_accepted_parts=latest['accepted_parts'],
        source_features_sha256=hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest())
    atomic_json(out / 'report.json', result)
    atomic_json(out / 'training-snapshot.json', prior)
    print(json.dumps({k: result[k] for k in ['heldout_predicted_cpu_seconds', 'all_parts_predicted_cpu_seconds',
                                         'heldout_measured_when_fitted', 'observed_accepted_parts']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    for name in ('expected-previous-source-sha256', 'expected-check-source-sha256', 'expected-agda-sha256'):
        parser.add_argument('--' + name, required=True)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
