import copy
import json
from pathlib import Path
import tempfile
import unittest

import initial_lazy_forecast6 as f


def fixtures(side):
    fixed = f.selection(side)
    rows = {i: dict(part=i, rows=200, tokens=1000 + k * 100, dependencies=1 + k * 10,
                    body_bytes=2000, references=20) for k, i in enumerate(fixed['selected'])}
    summary = dict(samples_sha256='sample-' + side)
    prefix = 'Tests.InitialLazyTraining' + side.title()
    machine = dict(hostname='eapiova', agda_sha256=f.AGDA, agda_path='/exact/agda')
    targets = ['Family'] + ['Part' + str(i) for i in fixed['training']]
    generated = {'src/' + (prefix + '.' + n).replace('.', '/') + '.agda': 'a' * 64 for n in targets}
    layout = dict(side=side, prefix=prefix, selected_training=fixed['training'], held_out_checked=False,
                  input_samples_sha256=summary['samples_sha256'], targets=targets,
                  generated_sha256=generated, cases=[rows[i] for i in fixed['training']])
    report = dict(accepted=True, status='complete', machine=machine, checked_source=dict(source_sha256='new'),
                  initial_problem2_proved=False, production_authorized=False, layouts=[layout], phases=[])
    for k, n in enumerate(targets):
        target = prefix + '.' + n
        argv = ['/exact/agda', '--no-libraries', '-i', 'src', '--safe', '--without-K',
                '--cubical-compatible', '--save-metas', 'src/' + target.replace('.', '/') + '.agda',
                '+RTS', '-M1350M', '-c', '-s', '-RTS']
        record = dict(accepted=True, exit_code=0, stop_reason=None, source_unchanged=True,
            expected_source_matches=True, own_target_cold=True, source_sha256='new',
            expected_source_sha256='new', agda_source_sha256='new', executable_sha256=f.AGDA,
            executable_path='/exact/agda', machine='eapiova', argv=argv, command=argv,
            cpu_seconds=2 + k, peak_rss_kib=250000 + k * 1000, finished_utc='done',
            interfaces_before=k, interfaces_after=k + 1,
            cache_state=dict(interfaces_before=k, interfaces_after=k + 1))
        report['phases'].append(dict(target=target, record=record, borrowed_interfaces_unchanged=True))
    return report, summary, rows


class ForecastTests(unittest.TestCase):
    def validate(self, report):
        _, summary, rows = fixtures('lower')
        return f.validate_training(report, 'lower', summary, rows, 'new')

    def test_training_guard_cases(self):
        base, _, _ = fixtures('lower')
        changes = [lambda d: d['phases'].pop(),
                   lambda d: d['phases'].append(copy.deepcopy(d['phases'][1])),
                   lambda d: d['phases'][1]['record'].update(accepted=False),
                   lambda d: d['phases'][1]['record'].update(executable_sha256='wrong'),
                   lambda d: d['phases'][1].update(target='Tests.InitialLazyTrainingLower.Part1331'),
                   lambda d: d['phases'][1]['record'].update(own_target_cold=False),
                   lambda d: d['phases'][1]['record']['argv'].remove('--safe')]
        self.assertEqual(len(self.validate(base)), 8)
        for change in changes:
            with self.subTest(change=change):
                changed = copy.deepcopy(base)
                change(changed)
                with self.assertRaises((ValueError, RuntimeError, SystemExit)):
                    self.validate(changed)

    def test_lower_inherited_source_epoch(self):
        report, summary, rows = fixtures('lower')
        inherited, report['phases'] = report['phases'][:3], report['phases'][3:]
        for p in inherited:
            p['record'].update(source_sha256='old', expected_source_sha256='old', agda_source_sha256='old')
        report.update(inherited_accepted_phases=inherited, donor_checked_source=dict(source_sha256='old'),
                      accepted_predecessor_unchanged=True, input_samples_unchanged=True)
        self.assertEqual(len(f.validate_training(report, 'lower', summary, rows, 'new', 'old')), 8)
        with self.assertRaises((ValueError, RuntimeError, SystemExit)):
            f.validate_training(report, 'lower', summary, rows, 'new', 'new')

    def test_pin_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'input.json'
            path.write_text('{}')
            with self.assertRaises((ValueError, RuntimeError, SystemExit)):
                f.load(path, 'wrong')

    def test_native_pin_and_fixed_plan(self):
        plan = dict(sides={s: f.selection(s) for s in ('lower', 'upper')})
        native = dict(accepted=True, fixture_source_unchanged=True,
                      source=dict(source_sha256='native', agda_source_sha256=f.CORE), phases=[])
        summaries, hashes = {}, {}
        for side in ('lower', 'upper'):
            _, s, rows = fixtures(side)
            fixed = f.selection(side)
            s.update(direction=side, native_complete=True, source_sha256='native',
                     complete=dict(selected=fixed['selected'],
                         **{k: fixed['expected']['layout_' + k] for k in ('parts', 'records', 'tokens')}),
                     cases=list(rows.values()))
            summaries[side], hashes[side] = s, 'hash-' + side
            native['phases'].append(dict(direction=side, accepted=True, complete=True,
                summary_sha256=hashes[side], sample_sha256=s['samples_sha256']))
        self.assertEqual(len(f.validate_native(native, plan, summaries, hashes)['upper']), 16)
        changed = copy.deepcopy(hashes)
        changed['lower'] = 'wrong'
        with self.assertRaises((ValueError, RuntimeError, SystemExit)):
            f.validate_native(native, plan, summaries, changed)

    def test_deterministic_prediction_and_freeze(self):
        rows, training = {}, []
        for side in ('lower', 'upper'):
            report, summary, rows[side] = fixtures(side)
            training.extend(f.validate_training(report, side, summary, rows[side], 'new'))
        first = f.prediction(rows, training)
        self.assertEqual(first, f.prediction(rows, training))
        self.assertEqual(len(first['heldout_rows']), 16)
        self.assertFalse(first['heldout_measured_when_fitted'])
        self.assertFalse(first['production_authorized'])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'results' / 'frozen'
            f.freeze(out, first, dict(training='hash'))
            manifest = json.loads((out / 'manifest.json').read_text())
            self.assertEqual(manifest['report_sha256'], f.sha((out / 'report.json').read_bytes()))
            with self.assertRaises((ValueError, RuntimeError, SystemExit)):
                f.freeze(out, first, {})


if __name__ == '__main__':
    unittest.main()
