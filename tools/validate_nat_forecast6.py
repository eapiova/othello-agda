#!/usr/bin/env python3
"""Validate the frozen numeric-row forecast against its entire fixed suffix.

This produces statistical evidence, not a proof or a production authorization.
It deliberately excludes assembly, setup, failed attempts and throughput.
"""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

from nat_forecast6 import HELDOUT, TRAINING
from provenance import digest_entries
from run_job import atomic_json, utc
from wire_workflow6 import require

PREFIX = 'Tests.NatDescendant6.'


def pinned(path, expected):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'pinned artifact changed')
    return json.loads(raw)


def instant(value):
    parsed = datetime.fromisoformat(value)
    require(parsed.utcoffset() is not None, 'measurement time needs a timezone')
    return parsed


def validate(forecast, report, pool):
    require(forecast['format'] == 'othello-nat-forecast6-v1'
            and forecast['training_indices'] == list(TRAINING)
            and forecast['heldout_indices'] == list(HELDOUT)
            and forecast['excluded_known_alternate_variant_indices'] == [231]
            and forecast['heldout_measured_when_fitted'] is False
            and forecast['whole_workflow_validated'] is False
            and forecast['production_authorized'] is False
            and forecast['gate_relative_error'] == .30,
            'the original fixed row-only experiment is required')
    source = report['checked_source']
    machine = report['machine']
    require(source == forecast['training_source'] and machine == forecast['machine']
            and report['initial_problem2_proved'] is False
            and report['production_authorized'] is False,
            'source, compiler or experiment scope differs')
    layout = report['layout']
    require(layout['parts'] == 267 and layout['rows'] == 53217
            and layout['hierarchy_nodes'] == 31
            and layout['targets'][:268] == ['Family'] + ['Part' + str(i) for i in range(267)]
            and layout['targets'][-1] == 'Root', 'original complete descendant layout required')
    require(digest_entries(pool) == report['last_interface_pool_sha256'],
            'certified interface map differs from the report')
    phases = report.get('inherited_accepted_phases', []) + report['phases']
    require([p['target'] for p in phases] == [PREFIX + n for n in layout['targets'][:len(phases)]],
            'measurements are not the unique ordered target prefix')
    measured = {}
    training = []
    for phase in phases:
        name = phase['target'].removeprefix(PREFIX)
        if not name.startswith('Part'):
            continue
        i = int(name[4:])
        rec = phase['record']
        if rec['accepted'] is not True:
            continue
        expected = [machine['agda_path'], '--no-libraries', '-i', 'src', '--safe',
                    '--without-K', '--cubical-compatible', '--save-metas',
                    'src/' + phase['target'].replace('.', '/') + '.agda',
                    '+RTS', '-M1350M', '-c', '-s', '-RTS']
        require(rec['exit_code'] == 0 and rec['stop_reason'] is None
                and rec['source_unchanged'] is True and rec['expected_source_matches'] is True
                and rec['own_target_cold'] is True and phase['borrowed_interfaces_unchanged'] is True
                and rec['source_sha256'] == rec['expected_source_sha256'] == source['source_sha256']
                and rec['executable_sha256'] == machine['agda_sha256']
                and rec['argv'] == expected, 'accepted row provenance differs')
        require(math.isfinite(rec['cpu_seconds']) and rec['cpu_seconds'] > 0
                and math.isfinite(rec['peak_rss_gib']) and 0 < rec['peak_rss_gib'] <= 1.5,
                'row CPU or memory measurement is invalid')
        suffix = '/' + phase['target'].replace('.', '/') + '.agdai'
        require(sum(n.endswith(suffix) for n in pool) == 1, 'accepted own interface is missing or ambiguous')
        measured[i] = phase
        if i in TRAINING:
            training.append(phase)
    require(set(measured) == set(range(267)) and report['accepted_parts'] == 267,
            'all rows, including the entire held-out suffix, must be accepted')
    require(training == forecast['training_phases'], 'training evidence changed after fitting')
    rows = forecast['rows']
    require(len(rows) == 267 and [r['part'] for r in rows] == list(range(267)),
            'frozen feature rows are incomplete')
    for row in rows:
        name = 'src/Tests/NatDescendant6/BodyData' + str(row['part']) + '.agda'
        require(row['body_source_sha256'] == layout['generated_sha256'][name],
                'held-out body source differs from the forecast')
        require(math.isfinite(row['predicted_cpu_seconds']) and row['predicted_cpu_seconds'] > 0,
                'invalid frozen prediction')
    created = instant(forecast['created_utc'])
    require(all(instant(measured[i]['record']['finished_utc']) < created for i in TRAINING)
            and all(created < instant(measured[i]['record']['started_utc']) for i in HELDOUT),
            'forecast was not frozen between training and held-out checks')
    predicted = sum(rows[i]['predicted_cpu_seconds'] for i in HELDOUT)
    require(math.isclose(predicted, forecast['heldout_predicted_cpu_seconds'], rel_tol=1e-12),
            'frozen suffix total differs from its rows')
    actual = sum(measured[i]['record']['cpu_seconds'] for i in HELDOUT)
    error = actual / predicted - 1
    return dict(format='othello-nat-forecast-validation6-v1', created_utc=utc(),
        fixed_suffix_complete=True, heldout_count=len(HELDOUT), accepted_parts=267,
        predicted_cpu_seconds=predicted, measured_cpu_seconds=actual,
        relative_error=error, gate_relative_error=.30, row_forecast_passed=abs(error) <= .30,
        max_heldout_rss_gib=max(measured[i]['record']['peak_rss_gib'] for i in HELDOUT),
        whole_workflow_validated=False, production_authorized=False, initial_problem2_proved=False,
        scope='entire prospectively fixed suffix; successful cold own row checks only',
        excluded=['Assembly', 'Setup and cold generic/state-data compilation',
                  'Failed or CPU-censored attempts and retry overhead', 'Parallel throughput',
                  'Known alternate variant part 231 from the suffix timing test'],
        machine=machine, checked_source=source,
        heldout=[dict(part=i, predicted_cpu_seconds=rows[i]['predicted_cpu_seconds'],
                      measured_cpu_seconds=measured[i]['record']['cpu_seconds'],
                      peak_rss_gib=measured[i]['record']['peak_rss_gib']) for i in HELDOUT])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('forecast', 'report', 'map', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('forecast', 'report', 'map'):
        parser.add_argument('--expected-' + name + '-sha256', required=True)
    args = parser.parse_args()
    forecast = pinned(args.forecast, args.expected_forecast_sha256)
    report = pinned(args.report, args.expected_report_sha256)
    pool = pinned(args.map, args.expected_map_sha256)
    result = validate(forecast, report, pool)
    require(not args.output.exists() and 'results' in args.output.parts, 'fresh results output required')
    result.update(forecast_sha256=args.expected_forecast_sha256,
                  report_sha256=args.expected_report_sha256, map_sha256=args.expected_map_sha256)
    atomic_json(args.output, result)
    print(json.dumps({k: result[k] for k in ('fixed_suffix_complete', 'heldout_count',
        'measured_cpu_seconds', 'predicted_cpu_seconds', 'relative_error', 'row_forecast_passed')}))


if __name__ == '__main__':
    main()
