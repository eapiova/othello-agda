#!/usr/bin/env python3
"""AI-assisted cold kernel benchmark generator and censored measurement analysis.

prepare defaults to a pending 90-state dataset: --compute is for a supervised
native desktop job. emit freezes one independent solve fact per job, refreshes
SNAPSHOT.json after inserting generated code, and never executes checks. analyze
retains resource failures and reports held-out predictions without inventing an
initial-state work count. Native output is untrusted; only Agda refl checks prove.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

import ref
from provenance import source_files, digest_entries, git_info, source_identity
from run_job import atomic_json, utc

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = '{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'


def decode(text):
    if len(text) != 37 or text[0] not in 'bw' or set(text[1:]) - set('012'):
        raise ValueError('invalid encoded 6x6 state')
    return ref.State(6, tuple(map(int, text[1:])), ref.BLACK if text[0] == 'b' else ref.WHITE)


def prepare(samples, output, compute=False, native_timeout=60):
    sample = json.loads(Path(samples).read_text())
    rows = []
    for empties in (8, 10, 12):
        encoded = sample['kernel'][str(empties)]
        if len(encoded) != 30 or len(set(encoded)) != 30:
            raise ValueError('need 30 distinct states per stratum')
        for index, text in enumerate(encoded):
            state = decode(text)
            if state.cells.count(ref.EMPTY) != empties:
                raise ValueError('state does not match empty-count stratum')
            rows.append({'id': f'e{empties:02d}s{index:02d}', 'state': text,
                         'empties': empties, 'split': 'train' if index < 24 else 'held-out',
                         'value': None, 'mirror': {}})
    data = {'format': 'othello-kernel-bench6-v1', 'fuel': 80,
            'score': 'raw white-minus-black; no empties award',
            'samples_sha256': hashlib.sha256(Path(samples).read_bytes()).hexdigest(),
            'split': 'first 24 train, last 6 held-out in each frozen sample stratum',
            'states': rows, 'created_utc': utc(), 'native_complete': False}
    atomic_json(Path(output), data)
    if compute:
        complete(data, output, native_timeout)
    return data


def complete(data, output, timeout):
    import solve6
    for row in data['states']:
        state = decode(row['state'])
        if row['value'] is None:
            result = solve6.query('solve', state, timeout=timeout)
            row.update(value=result['value'], native_value=result)
            atomic_json(Path(output), data)
        if type(row['value']) is not int or not -36 <= row['value'] <= 36:
            raise ValueError('native value must be signed raw score in [-36,36]')
        for direction in ('lower', 'upper'):
            if direction not in row['mirror']:
                result = solve6.query('mirror', state, direction=direction,
                                      threshold=row['value'], fuel=80, timeout=timeout)
                if result.get('holds') is not True or result.get('nodes', 0) <= 0:
                    raise ValueError('exact-bound mirror must hold with positive work')
                row['mirror'][direction] = result
                atomic_json(Path(output), data)
    data['native_complete'] = True
    atomic_json(Path(output), data)
    return data


def proof_text(module, encoded, value, rules, direction, search_kind='evidence'):
    decode(encoded)
    if type(value) is not int or not -36 <= value <= 36:
        raise ValueError('invalid signed threshold')
    game = 'Rules.game six' if rules == 'rules' else 'Fast.fastGame6'
    player = 'white' if direction == 'lower' else 'black'
    threshold = f"{'pos' if value >= 0 else 'neg'} {abs(value)}"
    if search_kind not in ('evidence', 'boolean'):
        raise ValueError('unknown search implementation')
    search_import = ('open import Game.Search using (forces)' if search_kind == 'evidence'
                     else 'open import Game.BooleanSearch using () renaming (forcesB to forces)')
    return OPTIONS + f'''-- AI-assisted generation. Exactly one independent kernel solve fact.
module {module} where

open import Prelude
open import Game.Core using (white; black)
{search_import}
open import Othello.Board using (State; six; initial)
open import Othello.Encode6 using (decodeState)
open import Tests.Bench6.Goals
import Othello.Rules as Rules
import Othello.Fast6 as Fast

position : State six
position = fromMaybe (initial six) (decodeState "{encoded}")

decoded : decodeState "{encoded}" ≡ just position
decoded = refl

accepted : forces 80 ({game}) {player} ({direction}Goal ({threshold})) position ≡ true
accepted = refl
'''


def refresh_manifest(root, origin=None):
    """Refresh only after all mutations, before launch; verify immediately."""
    old = root / 'SNAPSHOT.json'
    if origin is None:
        if old.exists():
            origin = json.loads(old.read_text())['git']
        else:
            original = source_identity(ROOT)
            origin = {key: original[key] for key in ('revision', 'dirty')}
    entries = {name: hashlib.sha256(raw).hexdigest() for name, raw in source_files(root)}
    manifest = {'format': 'othello-source-snapshot-v1', 'files': entries,
                'source_sha256': digest_entries(entries), 'git': origin, 'created_utc': utc()}
    atomic_json(old, manifest)
    source_identity(root)
    return manifest


def freeze(row, rules, direction, output, root=ROOT, search_kind='evidence'):
    if row.get('value') is None:
        raise ValueError('prepare --compute / complete is required before emit')
    work = row.get('mirror', {}).get(direction, {}).get('nodes')
    if not isinstance(work, int) or work <= 0:
        raise ValueError('emit requires measured native mirror W for this direction')
    original = source_identity(Path(root))
    prefix = 'boolean6' if search_kind == 'boolean' else 'bench6'
    label = f"{prefix}-{row['id']}-{rules}-{direction}"
    destination = Path(output).resolve() / label
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in source_files(Path(root)):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    relative = 'src/Tests/Bench6/Check.agda'
    path = destination / relative
    path.write_text(proof_text('Tests.Bench6.Check', row['state'], row['value'], rules, direction, search_kind))
    manifest = refresh_manifest(destination, {key: original[key] for key in ('revision', 'dirty')})
    job = {'format': 'othello-kernel-bench6-job-v1', 'label': label,
           'state_id': row['id'], 'empties': row['empties'], 'split': row['split'],
           'state': row['state'], 'threshold': row['value'], 'direction': direction,
           'rules': rules, 'search_kind': search_kind, 'native_W': work, 'cold': True, 'fuel': 80,
           'source_sha256': manifest['source_sha256'], 'root': str(destination),
           'command': ['agda', '--no-libraries', '--safe', '--without-K', '--cubical-compatible',
                       '-i', 'src', relative, '+RTS', '-M1500M', '-RTS']}
    # Job metadata outside frozen source keeps its own source digest stable.
    atomic_json(destination.with_name(label + '.job.json'), job)
    return job


RESOURCE_FAILURES = ('timeout', 'cpu-limit', 'rss-threshold', 'heap-limit')


def fit_cpu(rows):
    """Fit CPU=a+cK*W, a,cK>=0, using squared relative errors.

    Resource failures contribute one-sided relative residuals at their measured
    completion lower bounds. Distinct exact W values are required to identify
    both coefficients; censoring alone does not identify a unique fit.
    """
    exact = [(r['native_W'], r['cpu_seconds']) for r in rows
             if r['status'] == 'accepted' and r['cpu_seconds'] > 0]
    lower = [(r['native_W'], r['cpu_seconds']) for r in rows
             if r['status'] in RESOURCE_FAILURES and r['cpu_seconds'] > 0]
    result = {'identifiable': len({w for w, _ in exact}) >= 2,
              'intercept_cpu_seconds': None, 'cK_cpu_seconds_per_node': None,
              'exact_count': len(exact), 'distinct_exact_W': len({w for w, _ in exact}),
              'censored_count': len(lower),
              'completion_lower_bounds': [{'native_W': w, 'cpu_seconds': y} for w, y in lower]}
    if not result['identifiable']:
        result['reason'] = 'at least two distinct exact W values are required for intercept and slope'
        return result
    if any(w <= 0 for w, _ in exact + lower):
        raise ValueError('CPU fit requires positive native W')
    scale = max(w for w, _ in exact + lower)
    points = [(w / scale, y, False) for w, y in exact]
    points += [(w / scale, y, True) for w, y in lower]
    ceiling_a = max(y for _, y, _ in points)
    ceiling_b = max(y / x for x, y, _ in points)

    def at_slope(b):
        # For fixed scaled slope, the intercept derivative is monotone.
        lo, hi = 0.0, ceiling_a
        for _ in range(80):
            a = (lo + hi) / 2
            derivative = sum((min(0.0, a + b*x - y) if censored else a + b*x - y) / (y*y)
                             for x, y, censored in points)
            if derivative < 0:
                lo = a
            else:
                hi = a
        a = (lo + hi) / 2
        loss = sum((min(0.0, (a + b*x) / y - 1) if censored else (a + b*x) / y - 1)**2
                   for x, y, censored in points)
        return loss, a, b

    # Partial minimization preserves convexity. Include nonnegative boundaries.
    lo, hi = 0.0, ceiling_b
    fraction = (math.sqrt(5) - 1) / 2
    left, right = hi - fraction*(hi-lo), lo + fraction*(hi-lo)
    fleft, fright = at_slope(left), at_slope(right)
    for _ in range(100):
        if fleft[0] < fright[0]:
            hi, right, fright = right, left, fleft
            left = hi - fraction*(hi-lo)
            fleft = at_slope(left)
        else:
            lo, left, fleft = left, right, fright
            right = lo + fraction*(hi-lo)
            fright = at_slope(right)
    loss, a, b = min(at_slope(0), at_slope(ceiling_b), fleft, fright)
    result.update(intercept_cpu_seconds=a, cK_cpu_seconds_per_node=b / scale,
                  relative_squared_loss=loss, exact_W_range=[min(w for w, _ in exact), max(w for w, _ in exact)])
    return result


def rss_envelope(rows):
    measured = [r for r in rows if r['status'] != 'unmeasured']
    accepted = [r['peak_rss_gib'] for r in measured if r['status'] == 'accepted']
    censored = [r['rss_lower_gib'] for r in measured if r['status'] in ('rss-threshold', 'heap-limit')]
    return {'measured_count': len(measured), 'accepted_count': len(accepted),
            'accepted_min_gib': min(accepted) if accepted else None,
            'accepted_max_gib': max(accepted) if accepted else None,
            'observed_peak_max_gib': max((r['peak_rss_gib'] for r in measured), default=None),
            'memory_censored_lower_max_gib': max(censored, default=None),
            'extrapolation_guaranteed': False}


def summarize_group(group, cpu=None):
    train = [r for r in group if r['split'] == 'train']
    cpu = fit_cpu(train) if cpu is None else cpu
    held = []
    for row in group:
        if row['split'] != 'held-out':
            continue
        prediction = {'label': row['label'], 'status': row['status'], 'native_W': row['native_W'],
                      'cpu_prediction': None, 'cpu_within_30_percent': None}
        if cpu['identifiable']:
            prediction['cpu_prediction'] = cpu['intercept_cpu_seconds'] + cpu['cK_cpu_seconds_per_node'] * row['native_W']
        if row['status'] == 'accepted':
            prediction.update(observed_cpu=row['cpu_seconds'], observed_rss_gib=row['peak_rss_gib'])
            if prediction['cpu_prediction'] is not None and row['cpu_seconds'] > 0:
                ratio = prediction['cpu_prediction'] / row['cpu_seconds']
                prediction.update(cpu_prediction_over_actual=ratio, cpu_within_30_percent=0.7 <= ratio <= 1.3)
        elif row['status'] != 'unmeasured':
            prediction['observed_rss_gib'] = row['peak_rss_gib']
            if row['status'] in RESOURCE_FAILURES:
                prediction['observed_completion_cpu_lower_bound'] = row['cpu_seconds']
                if prediction['cpu_prediction'] is not None and row['cpu_seconds'] > 0:
                    prediction['cpu_prediction_over_completion_lower_bound'] = prediction['cpu_prediction'] / row['cpu_seconds']
        held.append(prediction)
    evaluated = [h for h in held if h['cpu_within_30_percent'] is not None]
    # The gate requires every frozen held-out job to complete and be evaluable.
    gate = None
    if held and len(evaluated) == len(held):
        gate = all(h['cpu_within_30_percent'] for h in evaluated)
    elif any(h['cpu_within_30_percent'] is False for h in evaluated):
        gate = False
    return {'cpu_model': cpu, 'rss_envelope': rss_envelope(group),
            'status_counts': {s: sum(r['status'] == s for r in group) for s in sorted({r['status'] for r in group})},
            'held_out': held, 'held_out_cpu_30_percent_gate': gate,
            'held_out_cpu_evaluated_count': len(evaluated),
            'held_out_cpu_gate_complete': bool(held) and len(evaluated) == len(held)}


def analyze(jobs, records):
    measurements = {}
    for path in records:
        record = json.loads(Path(path).read_text())
        label = record.get('label')
        if label in measurements:
            raise ValueError('duplicate result labels: select one measured attempt explicitly')
        measurements[label] = (record, Path(path).parent)
    rows = []
    for path in jobs:
        job = json.loads(Path(path).read_text())
        measured = measurements.get(job['label'])
        record = measured[0] if measured else None
        row = dict(job)
        row.setdefault('search_kind', 'evidence')
        row['status'] = 'unmeasured'
        if record:
            if record.get('source_sha256') != job['source_sha256']:
                raise ValueError('measurement source differs from frozen benchmark job')
            row.update(cpu_seconds=record['cpu_seconds'], peak_rss_gib=record['peak_rss_gib'],
                       rss_lower_gib=record['peak_rss_gib'], exit_code=record['exit_code'],
                       stop_reason=record.get('stop_reason'))
            if record.get('accepted'):
                row['status'] = 'accepted'
            else:
                row['status'] = record.get('stop_reason') or 'check-failed'
                if row['status'] == 'rss-threshold':
                    row['rss_lower_gib'] = max(row['rss_lower_gib'], record['rss_stop_threshold_gib'])
                # GHC heap exhaustion is a memory-censored observation even
                # when the supervisor itself did not reach its RSS threshold.
                log = measured[1] / (job['label'] + '.log')
                if row['status'] == 'check-failed' and log.exists() and 'Heap exhausted' in log.read_text(errors='replace'):
                    row['status'] = 'heap-limit'
        rows.append(row)
    if len({r['search_kind'] for r in rows}) > 1:
        raise ValueError('different search implementations require separate cost reports')
    groups, combined = {}, {}
    for rules in ('rules', 'fast'):
        for direction in ('lower', 'upper'):
            pooled = [r for r in rows if (r['rules'], r['direction']) == (rules, direction)]
            combined[f'{rules}/{direction}'] = summarize_group(pooled)
            for empties in (8, 10, 12):
                group = [r for r in pooled if r['empties'] == empties]
                groups[f'{rules}/{direction}/{empties}'] = summarize_group(group)
    return {'format': 'othello-kernel-bench6-analysis-v2', 'groups': groups,
            'combined_rules_direction': combined, 'observations': rows,
            'model': 'CPU=a+cK*W with nonnegative intercept and slope; squared relative errors plus right-censored hinge losses; training only',
            'limitations': ['Failures and unmeasured jobs remain in observations, held-out rows and status counts.',
                'At least two distinct exact training W values are required to identify intercept and slope; sparse fits are exploratory.',
                'Combined fits pool empties only within the same rules/direction; frozen last-six held-out splits remain unchanged.',
                'Resource failures give completion CPU lower bounds, not completed runtimes; other failures supply no completion bound.',
                'RSS envelopes are measured observations, not guaranteed extrapolated memory requirements; heap caps differ from RSS caps.',
                'The ±30% gate is incomplete until every supplied held-out job completes and is evaluable.',
                'No initial-state estimate is possible without measured initial-state W.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--samples', type=Path, default=ROOT / 'certificates/six-samples.json')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--compute', action='store_true')
    p.add_argument('--native-timeout', type=float, default=60)
    p = sub.add_parser('complete')
    p.add_argument('dataset', type=Path)
    p.add_argument('--native-timeout', type=float, default=60)
    p = sub.add_parser('emit')
    p.add_argument('dataset', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--state-id')
    p.add_argument('--rules', choices=('rules', 'fast', 'both'), default='both')
    p.add_argument('--direction', choices=('lower', 'upper', 'both'), default='both')
    p.add_argument('--search-kind', choices=('evidence', 'boolean'), default='evidence')
    p = sub.add_parser('analyze')
    p.add_argument('--jobs', type=Path, nargs='+', required=True)
    p.add_argument('--records', type=Path, nargs='*', default=[])
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result = prepare(args.samples, args.output, args.compute, args.native_timeout)
        print(json.dumps({'states': len(result['states']), 'native_complete': result['native_complete']}))
    elif args.action == 'complete':
        complete(json.loads(args.dataset.read_text()), args.dataset, args.native_timeout)
    elif args.action == 'emit':
        data = json.loads(args.dataset.read_text())
        rows = [r for r in data['states'] if args.state_id is None or r['id'] == args.state_id]
        if not rows:
            parser.error('state id not found')
        for row in rows:
            for rules in ('rules', 'fast') if args.rules == 'both' else (args.rules,):
                for direction in ('lower', 'upper') if args.direction == 'both' else (args.direction,):
                    print(json.dumps(freeze(row, rules, direction, args.output, search_kind=args.search_kind)))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(args.output, analyze(args.jobs, args.records))


if __name__ == '__main__':
    main()
