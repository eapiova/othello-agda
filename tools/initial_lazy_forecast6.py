#!/usr/bin/env python3
"""Freeze a prospective initial-layout conditional-row cost forecast; never launch checks."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from initial_lazy_samples6 import selection
from owner_continue6 import nnls
from run_job import atomic_json, utc
from wire_workflow6 import require

AGDA = 'c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842'
CORE = '729fae0e8b475a48630d4177fd1312fe982d09b87692f15dfd1ec446c40e3c40'
FEATURES = ['certificate tokens/1000', 'dependency state chunks/1000', 'intercept']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, expected=None):
    raw = Path(path).read_bytes()
    require(expected is None or sha(raw) == expected, 'input SHA pin mismatch: ' + str(path))
    return json.loads(raw), sha(raw)


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def features(case):
    require(positive(case['tokens']) and positive(case['dependencies']), 'invalid native features')
    return [case['tokens'] / 1000, case['dependencies'] / 1000, 1.]


def validate_native(native, plan, summaries, summary_hashes):
    require(native['accepted'] and native['fixture_source_unchanged']
            and native['source']['agda_source_sha256'] == CORE, 'unaccepted native source/core')
    require(len(native['phases']) == 2, 'exact native side phases required')
    rows = {}
    for side in ('lower', 'upper'):
        fixed = selection(side)
        require(plan['sides'][side] == fixed, 'fixed training8/heldout8 plan changed')
        matches = [p for p in native['phases'] if p['direction'] == side]
        require(len(matches) == 1, 'missing or duplicate native phase')
        p, s = matches[0], summaries[side]
        require(p['accepted'] and p['complete'] and p['summary_sha256'] == summary_hashes[side]
                and p['sample_sha256'] == s['samples_sha256'], 'native summary pin mismatch')
        require(s['direction'] == side and s['native_complete']
                and s['source_sha256'] == native['source']['source_sha256']
                and s['complete']['selected'] == fixed['selected']
                and all(s['complete'][key] == fixed['expected']['layout_' + key]
                        for key in ('parts', 'records', 'tokens'))
                and [c['part'] for c in s['cases']] == fixed['selected'], 'native dataset differs')
        rows[side] = {c['part']: c for c in s['cases']}
        for c in s['cases']:
            features(c)
    return rows


def validate_training(report, side, summary, rows, expected_source, expected_inherited=None):
    fixed = selection(side)
    machine = report['machine']
    require(report['accepted'] and report['status'] == 'complete'
            and machine['hostname'] == 'eapiova' and machine['agda_sha256'] == AGDA
            and not report['initial_problem2_proved'] and not report['production_authorized']
            and not report.get('optimal_initial_pair_proved', False),
            'unaccepted training/compiler/machine')
    require(report['checked_source']['source_sha256'] == expected_source, 'training source epoch differs')
    require(len(report['layouts']) == 1, 'one side layout required')
    layout = report['layouts'][0]
    prefix = 'Tests.InitialLazyTraining' + side.title()
    require(layout['side'] == side and layout['prefix'] == prefix
            and layout['selected_training'] == fixed['training'] and not layout['held_out_checked']
            and layout['input_samples_sha256'] == summary['samples_sha256']
            and layout['targets'] == ['Family'] + ['Part' + str(i) for i in fixed['training']]
            and layout['cases'] == [rows[i] for i in fixed['training']], 'exact training layout differs')
    inherited = report.get('inherited_accepted_phases', [])
    if inherited:
        require(side == 'lower' and expected_inherited is not None
                and report['donor_checked_source']['source_sha256'] == expected_inherited
                and [p['target'] for p in inherited] == [prefix + '.' + n for n in ('Family', 'Part0', 'Part4599')]
                and report['accepted_predecessor_unchanged'] and report['input_samples_unchanged'],
                'old lower source epoch/inherited phases differ')
    else:
        require(expected_inherited is None, 'expected inherited epoch missing')
    measurements = []
    targets = set()
    for epoch, phases in [(expected_inherited, inherited), (expected_source, report['phases'])]:
        for phase in phases:
            target, rec = phase['target'], phase['record']
            require(target not in targets and target in [prefix + '.' + n for n in layout['targets']],
                    'duplicate/unexpected/heldout training target')
            targets.add(target)
            expected_argv = [machine['agda_path'], '--no-libraries', '-i', 'src', '--safe', '--without-K',
                '--cubical-compatible', '--save-metas', 'src/' + target.replace('.', '/') + '.agda',
                '+RTS', '-M1350M', '-c', '-s', '-RTS']
            require(rec.get('target', target) == target
                    and rec['accepted'] and rec['exit_code'] == 0 and rec['stop_reason'] is None
                    and rec['source_unchanged'] and rec['expected_source_matches'] and rec['own_target_cold']
                    and rec['source_sha256'] == rec['expected_source_sha256'] == epoch
                    and rec['agda_source_sha256'] == epoch
                    and rec['executable_sha256'] == AGDA and rec['machine'] == machine['hostname']
                    and rec['argv'] == expected_argv and rec['command'] == expected_argv
                    and rec['executable_path'] == machine['agda_path']
                    and phase['borrowed_interfaces_unchanged'] and positive(rec['cpu_seconds'])
                    and positive(rec['peak_rss_kib']) and rec.get('finished_utc'),
                    'failed training acceptance/source/compiler/cold/safe provenance')
            cache = rec['cache_state']
            require(cache['interfaces_before'] == rec['interfaces_before']
                    and cache['interfaces_after'] == rec['interfaces_after']
                    and 0 <= cache['interfaces_before'] <= cache['interfaces_after'], 'cache counts differ')
            target_source = 'src/' + target.replace('.', '/') + '.agda'
            require(re.fullmatch('[0-9a-f]{64}', layout['generated_sha256'][target_source]), 'missing source identity')
            if 'checked_target_source_sha256' in phase:
                require(phase['checked_target_source_sha256'] == layout['generated_sha256'][target_source]
                        and phase['input_samples_unchanged'], 'target/sample source changed')
            match = re.fullmatch(re.escape(prefix) + r'\.Part([0-9]+)', target)
            if match:
                i = int(match[1])
                measurements.append(dict(side=side, part=i, x=features(rows[i]),
                    cpu_seconds=rec['cpu_seconds'], peak_rss_kib=rec['peak_rss_kib'],
                    source_epoch=epoch, target_source_sha256=layout['generated_sha256'][target_source],
                    cache_state=cache, record=rec))
    require(targets == {prefix + '.' + n for n in layout['targets']}
            and sorted(m['part'] for m in measurements) == fixed['training'], 'missing training records')
    return sorted(measurements, key=lambda m: m['part'])


def prediction(rows, training):
    require(len(training) == 16, 'all16 training parts required')
    cpu = nnls(training, 3)
    rss = nnls([dict(x=m['x'], cpu_seconds=m['peak_rss_kib']) for m in training], 3)
    heldout = []
    for side in ('lower', 'upper'):
        for i in selection(side)['held_out']:
            x = features(rows[side][i])
            c, r = (sum(a * b for a, b in zip(model['coefficients'], x)) for model in (cpu, rss))
            require(positive(c) and positive(r), 'nonpositive prediction')
            heldout.append(dict(side=side, part=i, features=x, predicted_cpu_seconds=c, predicted_peak_rss_kib=r))
    return dict(format='othello-initial-lazy-forecast6-v1', cpu_model=cpu, rss_model=rss,
        feature_names=FEATURES, heldout=heldout,
        heldout_rows=[dict(r, direction=r['side'], predicted_peak_rss_gib=r['predicted_peak_rss_kib'] / 2**20)
                      for r in heldout],
        heldout_predicted_cpu_seconds=sum(r['predicted_cpu_seconds'] for r in heldout),
        heldout_predicted_cpu_seconds_by_side={s: sum(r['predicted_cpu_seconds'] for r in heldout if r['side'] == s)
                                             for s in ('lower', 'upper')},
        heldout_measured_when_fitted=False, validation_relative_error_limit=.30,
        validation_criterion='each side heldout CPU sum relative error abs(measured-predicted)/predicted <= 0.30',
        validation_pending=True, whole_workflow_validated=False, production_authorized=False,
        initial_problem2_proved=False, optimal_initial_pair_proved=False,
        scope='row-check prediction ONLY: genuine initial-layout uniform-lazy conditional parts',
        original_9_oct_forecast_status='inconclusive; unchanged',
        uncertainty='16 stratified training parts; no calibrated confidence interval. RSS descriptive only; no memory admission gate.',
        limitations=['CPU includes needed state imports in each own-target-cold check; imported chunks are not all cold.',
                    'Cache counts before/after are recorded; generic and already imported interfaces can be warm.',
                    'Full initial cost is unknown: assembly, concurrency, generation and interface volume are unmeasured.',
                    'No production GO or initial-board proof follows from this forecast.'])


def freeze(output, result, inputs):
    out = Path(output).resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh results output required; overwrite/refit forbidden')
    out.mkdir(parents=True, exist_ok=False)
    atomic_json(out / 'report.json', dict(result, created_utc=utc(), input_sha256=inputs, training_inputs=inputs))
    atomic_json(out / 'manifest.json', dict(format='othello-initial-lazy-forecast6-manifest-v1',
        frozen=True, report_sha256=sha((out / 'report.json').read_bytes()), input_sha256=inputs,
        heldout_measured_when_fitted=False, refit_authorized=False))


def run(args):
    names = ('native_report', 'plan', 'lower_summary', 'upper_summary', 'lower_report', 'upper_report')
    data, hashes = {}, {}
    for name in names:
        data[name], hashes[name] = load(getattr(args, name), getattr(args, 'expected_' + name + '_sha256'))
    summaries = {s: data[s + '_summary'] for s in ('lower', 'upper')}
    rows = validate_native(data['native_report'], data['plan'], summaries,
                           {s: hashes[s + '_summary'] for s in summaries})
    training = []
    for s in ('lower', 'upper'):
        training.extend(validate_training(data[s + '_report'], s, summaries[s], rows[s],
            getattr(args, 'expected_' + s + '_source_sha256'),
            args.expected_lower_inherited_source_sha256 if s == 'lower' else None))
    require(data['lower_report']['machine'] == data['upper_report']['machine'], 'training machines differ')
    result = prediction(rows, training)
    result.update(training=training, machine=data['lower_report']['machine'],
        source_provenance={n: data[n]['checked_source'] for n in ('lower_report', 'upper_report')},
        lower_inherited_source=data['lower_report'].get('donor_checked_source'), native_core_sha256=CORE)
    # Detect an input update (including a holdout phase appearing) before the freeze.
    for name in names:
        require(sha(Path(getattr(args, name)).read_bytes()) == hashes[name], 'input changed while fitting')
    freeze(args.output, result, hashes)
    print(json.dumps(dict(heldout_predicted_cpu_seconds=result['heldout_predicted_cpu_seconds'],
                         production_authorized=False)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('native-report', 'plan', 'lower-summary', 'upper-summary', 'lower-report', 'upper-report'):
        p.add_argument('--' + name, type=Path, required=True)
        p.add_argument('--expected-' + name + '-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    for side in ('lower', 'upper'):
        p.add_argument('--expected-' + side + '-source-sha256', required=True)
    p.add_argument('--expected-lower-inherited-source-sha256')
    run(p.parse_args())


if __name__ == '__main__':
    main()
