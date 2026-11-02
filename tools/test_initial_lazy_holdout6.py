import copy
import unittest

import initial_lazy_holdout6 as h


def frozen():
    return dict(format='othello-initial-lazy-forecast6-v1', heldout_measured_when_fitted=False,
        production_authorized=False, initial_problem2_proved=False, whole_workflow_validated=False,
        training_inputs=dict(lower_report='lower-pin', upper_report='upper-pin'),
        heldout_rows=[dict(direction=s, part=i, predicted_cpu_seconds=2.)
                      for s in ('lower', 'upper') for i in h.selection(s)['held_out']])


class HoldoutTests(unittest.TestCase):
    def test_forecast_is_prospective_and_pinned(self):
        base = frozen()
        self.assertEqual([r['part'] for r in h.forecast_rows(base, 'lower', 'lower-pin')],
                         h.selection('lower')['held_out'])
        for field in ('heldout_measured_when_fitted', 'production_authorized',
                      'initial_problem2_proved', 'whole_workflow_validated'):
            changed = copy.deepcopy(base)
            changed[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                h.forecast_rows(changed, 'lower', 'lower-pin')
        with self.assertRaises(ValueError):
            h.forecast_rows(base, 'lower', 'changed-training')

    def test_fixed_holdout_cannot_drop_or_replace_parts(self):
        for mutate in (lambda d: d['heldout_rows'].pop(),
                       lambda d: d['heldout_rows'][0].update(part=0),
                       lambda d: d['heldout_rows'].__setitem__(1, copy.deepcopy(d['heldout_rows'][0])),
                       lambda d: d['heldout_rows'][0].update(predicted_cpu_seconds=0)):
            changed = frozen()
            mutate(changed)
            with self.assertRaises(ValueError):
                h.forecast_rows(changed, 'lower', 'lower-pin')

    def test_incomplete_or_failed_residual_never_passes(self):
        rows = h.forecast_rows(frozen(), 'lower', 'lower-pin')
        prefix = 'Tests.InitialLazyTrainingLower'
        phases = [dict(target=prefix + '.Part' + str(r['part']),
            record=dict(accepted=True, cpu_seconds=2.),
            borrowed_interfaces_unchanged=True, input_samples_unchanged=True) for r in rows]
        self.assertTrue(h.residual(rows, phases, prefix)['within_30_percent'])
        self.assertFalse(h.residual(rows, phases[:-1], prefix)['within_30_percent'])
        phases[0]['record']['accepted'] = False
        self.assertFalse(h.residual(rows, phases, prefix)['within_30_percent'])

    def test_complete_measurement_outside_margin_fails(self):
        rows = h.forecast_rows(frozen(), 'upper', 'upper-pin')
        prefix = 'Tests.InitialLazyTrainingUpper'
        phases = [dict(target=prefix + '.Part' + str(r['part']),
            record=dict(accepted=True, cpu_seconds=3.),
            borrowed_interfaces_unchanged=True, input_samples_unchanged=True) for r in rows]
        result = h.residual(rows, phases, prefix)
        self.assertTrue(result['complete'])
        self.assertFalse(result['within_30_percent'])
        self.assertEqual(result['relative_error'], .5)

    def test_native_complete_marker_and_selection_are_required(self):
        side = 'lower'
        fixed = h.selection(side)
        decoded = dict(complete=dict(selected=fixed['selected'],
            **{k: fixed['expected']['layout_' + k] for k in ('parts', 'records', 'tokens')}),
            states={i: dict(rows=1, text='sample') for i in fixed['selected']},
            cases=[dict(part=i, rows=1, tokens=1, body_text='L', dependencies=[i],
                        references=[]) for i in fixed['selected']])
        chosen, rows = h.samples(decoded, side)
        self.assertEqual(len(chosen['cases']), 16)
        self.assertEqual(set(rows), set(fixed['selected']))
        for mutate in (lambda d: d['complete'].update(tokens=0),
                       lambda d: d['cases'].pop(),
                       lambda d: d['states'].pop(fixed['selected'][0])):
            changed = copy.deepcopy(decoded)
            mutate(changed)
            with self.assertRaises(ValueError):
                h.samples(changed, side)


if __name__ == '__main__':
    unittest.main()
