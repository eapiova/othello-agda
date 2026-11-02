"""Keep censored training and holdout results out of resource-gate forecasts."""
import copy
import unittest

import rewrite_holdout6 as cost


def fixture():
    rows, measured = [], []
    for index in cost.TRAINING+cost.HELDOUT:
        phases = []
        for kind in ('certificate', 'assembly', 'root'):
            x = [index+1., 1.] if kind == 'root' else [index+1., index/2., 1.]
            p = dict(label=f'root{index}-{kind}', kind=kind, target=f'Root{index}/{kind}', x=x)
            phases.append(p)
            if index in cost.TRAINING:
                measured.append(dict(p, root_index=index, accepted=True,
                    record=dict(accepted=True, stop_reason=None, cpu_seconds=sum(x))))
        rows.append(dict(index=index, phases=phases))
    return dict(format='othello-rewrite-training6-v1', status='complete', accepted=True,
        completed_indices=cost.TRAINING.copy(), training_indices=cost.TRAINING,
        heldout_indices=cost.HELDOUT, checked_sample_lower_roots=10, heldout_measured=False,
        donor_unchanged=True, original_donor_unchanged=True, generated_sources_unchanged=True,
        repairs=[], phases=measured, rows=rows, layout_sha256='a'*64)


class RewriteHoldoutTests(unittest.TestCase):
    def test_forecast_preserves_fixed_unmeasured_holdout(self):
        training = fixture()
        before = copy.deepcopy(training)
        forecast = cost.prediction(training)
        self.assertEqual(training, before)
        self.assertEqual({p['root_index'] for p in forecast['rows']}, set(cost.HELDOUT))
        self.assertFalse(forecast['heldout_measured_when_fitted'])
        self.assertFalse(forecast['production_authorized'])
        self.assertGreater(forecast['predicted_cpu_seconds'], 0)

    def test_failed_partial_or_contaminated_training_is_rejected(self):
        for change in (lambda r: r.update(heldout_measured=True),
                lambda r: r['completed_indices'].pop(), lambda r: r['phases'].pop(),
                lambda r: r['phases'][0].update(accepted=False),
                lambda r: r['phases'][0]['record'].update(stop_reason='rss-limit'),
                lambda r: r.update(donor_unchanged=False),
                lambda r: r['phases'].append(dict(r['phases'][0], label='root10-certificate'))):
            training = fixture(); change(training)
            with self.assertRaises(ValueError):
                cost.prediction(training)

    def test_partial_or_failed_holdout_has_no_gate_residual(self):
        forecast = cost.prediction(fixture())
        phases = [dict(label=p['label'], accepted=True,
            record=dict(cpu_seconds=p['predicted_cpu_seconds']*1.10)) for p in forecast['rows']]
        self.assertAlmostEqual(cost.residuals(forecast, phases)['relative_error'], .10)
        self.assertIsNone(cost.residuals(forecast, phases[:-1])['relative_error'])
        phases[0]['accepted'] = False
        self.assertIsNone(cost.residuals(forecast, phases)['relative_error'])

    def test_resume_keeps_the_original_forecast_and_skips_only_an_accepted_prefix(self):
        training = fixture()
        forecast = cost.prediction(training)
        declared = [dict(p, root_index=row['index']) for row in training['rows']
            if row['index'] in cost.HELDOUT for p in row['phases']]
        phases = [dict(p, accepted=True, record=dict(accepted=True, stop_reason=None, cpu_seconds=1.))
            for p in declared[:4]]
        report = dict(format='othello-rewrite-heldout6-v1', status='disk-stop', accepted=False,
            phases=phases, heldout_measured=True, donor_unchanged=True, generated_sources_unchanged=True,
            prospective_prediction=forecast, completed_indices=[10], checked_sample_lower_roots=11,
            nested_cpu_seconds=4., heldout_residual=dict(relative_error=None),
            existing_conditional_parts_rechecked=0)
        self.assertEqual(cost.resume_prefix(training, forecast, report), 4)
        for change in (lambda r: r['phases'].reverse(),
                lambda r: r['phases'][0].update(accepted=False),
                lambda r: r['phases'][0].update(x=[99., 99., 99.]),
                lambda r: r.update(nested_cpu_seconds=5.),
                lambda r: r.update(completed_indices=[]),
                lambda r: r.update(prospective_prediction={}),
                lambda r: r['heldout_residual'].update(relative_error=.1)):
            changed = copy.deepcopy(report); change(changed)
            with self.assertRaises(ValueError):
                cost.resume_prefix(training, forecast, changed)


if __name__ == '__main__':
    unittest.main()
