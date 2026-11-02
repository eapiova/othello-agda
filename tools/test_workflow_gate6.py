"""Resource screens cannot turn partial evidence or sample reuse into a GO."""
import copy
import unittest

from test_rewrite_holdout6 import fixture
import workflow_gate6 as gate


def inputs():
    training = fixture()
    frozen = gate.prediction(training)
    phases = [dict(p, accepted=True, record=dict(cpu_seconds=p['predicted_cpu_seconds'], peak_rss_gib=.5))
        for p in frozen['rows']]
    heldout = dict(prospective_prediction=frozen, status='complete', accepted=True,
        completed_indices=gate.HELDOUT, checked_sample_lower_roots=20,
        donor_unchanged=True, generated_sources_unchanged=True, postulates=0,
        existing_conditional_parts_rechecked=0, phases=phases,
        heldout_residual=gate.residuals(frozen, phases))
    bounds = []
    for direction in ('lower', 'upper'):
        bounds.append(dict(status='complete', direction=direction, threshold=4,
            source_population_kind='canonical frontier full-state classes',
            scalar_replay=True, sample_size=2, source_population=1000000,
            source_sample_seed=1, subsample_seed=2,
            stats=dict(global_token_gain=1.001),
            cases=[dict(state=str(i), d4_layered_tokens=100000, compact_bytes=100000)
                   for i in range(2)]))
    return dict(training=training, heldout=heldout, lower=bounds[0], upper=bounds[1],
        upper_cost=dict(aggregate_within_30_percent=True, heldout_measured_when_fitted=False,
                        coefficients=[1.]),
        throughput=dict(accepted=True, batches=[dict(slots=8, accepted=True, effective_slots=6.)]))


class WorkflowGateTests(unittest.TestCase):
    def test_large_nominal_components_reject_current_representation(self):
        r = gate.evaluate(**inputs())
        self.assertEqual(r['recommendation'], 'NO_GO_CURRENT_REPRESENTATION')
        self.assertGreater(r['nominal_compact_gib'], 10)
        self.assertGreater(r['nominal_token_wall_hours_with_margin'], 168)
        self.assertFalse(r['production_authorized'])
        self.assertTrue(all(c['population_global_sharing_factor_applied'] == 1 for c in r['components']))

    def test_partial_refitted_and_unchecked_evidence_are_rejected(self):
        for change in (lambda x: x['heldout']['phases'].pop(),
                lambda x: x['heldout'].update(accepted=False),
                lambda x: x['heldout'].update(donor_unchanged=False),
                lambda x: x['heldout'].update(postulates=1),
                lambda x: x['heldout']['prospective_prediction'].update(predicted_cpu_seconds=0),
                lambda x: x['lower'].update(status='censored'),
                lambda x: x['lower'].update(source_population_kind='raw states'),
                lambda x: x['upper_cost'].update(heldout_measured_when_fitted=True)):
            x = copy.deepcopy(inputs()); change(x)
            with self.assertRaises(ValueError):
                gate.evaluate(**x)

    def test_small_component_projection_still_cannot_authorize_production(self):
        x = inputs()
        for bound in (x['lower'], x['upper']):
            bound['source_population'] = 2
        r = gate.evaluate(**x)
        self.assertEqual(r['recommendation'], 'NEEDS_FULL_WORKFLOW_PILOT')
        self.assertFalse(r['production_authorized'])
        self.assertFalse(r['initial_problem2_proved'])


if __name__ == '__main__':
    unittest.main()
