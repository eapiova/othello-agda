"""Prospective model fixtures reject partial or contaminated training."""
import copy
import unittest
import census_forecast6 as forecast


def inputs():
    targets=[]
    for i in range(8):
        targets += [dict(kind='part',root_index=i,path=f'root{i}/part',tokens=(i+1)*1000,
                         entries=150,imported_citations=i*100),
                    dict(kind='assembly',root_index=i,path=f'root{i}/assembly',transitive_entries=(i+1)*150)]
    plan=dict(format=forecast.FORMAT,targets=targets)
    phases=[]
    for t in targets[:8]:
        x=forecast.features(t)
        y=sum(c*v for c,v in zip([1,2,3,.5] if t['kind']=='part' else [2,.5],x))
        phases.append(dict(target=t,changed_imports=[],record=dict(accepted=True,
            cpu_seconds=y,own_target_cold=True,source_unchanged=True,expected_source_matches=True,
            source_sha256='source',executable_sha256='binary')))
    training=dict(format=forecast.FORMAT,phase='training',accepted=True,status='complete',
        plan_sha256='plan',donor_unchanged=True,generated_sources_unchanged=True,
        phases=phases,source_sha256='source',machine=dict(agda_sha256='binary'))
    return plan,training


class ForecastTests(unittest.TestCase):
    def test_fixed_unseen_predictions(self):
        plan,training=inputs()
        r=forecast.prediction(plan,training,'plan','training')
        self.assertEqual(set(r['root_predictions_cpu_seconds']), {'4','5','6','7'})
        self.assertFalse(r['heldout_measured_when_fitted'])
        self.assertFalse(r['production_authorized'])
        for row in r['rows']:
            x=forecast.features(row['target'])
            expected=sum(c*v for c,v in zip([1,2,3,.5] if row['target']['kind']=='part' else [2,.5],x))
            self.assertAlmostEqual(row['predicted_cpu_seconds'],expected,places=6)

    def test_reject_partial_or_changed_training(self):
        plan,original=inputs()
        changes=[lambda t:t['phases'].pop(), lambda t:t.update(phase='heldout'),
                 lambda t:t.update(plan_sha256='changed'),
                 lambda t:t['phases'][0]['record'].update(accepted=False),
                 lambda t:t['phases'][0]['record'].update(own_target_cold=False),
                 lambda t:t['phases'][0]['changed_imports'].append('dependency')]
        for change in changes:
            training=copy.deepcopy(original); change(training)
            with self.assertRaises(ValueError): forecast.prediction(plan,training,'plan','training')


if __name__=='__main__': unittest.main()
