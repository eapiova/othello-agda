"""Heldout prediction must precede measurements and reject censored training."""
import copy
import unittest

import owner_continue6 as cost
import owner_lower6 as owner


def fixture():
    rows=[]
    phases=[]
    for index in owner.TRAINING+owner.HELDOUT:
        part=[]
        for kind in ('certificate','assembly','root'):
            x=([index+1.,index/2.,1.] if kind!='root' else [index+1.,1.])
            p=dict(label=f'root{index}-{kind}',kind=kind,x=x)
            part.append(p)
            if index in owner.TRAINING:
                phases.append(dict(p,accepted=True,record=dict(accepted=True,stop_reason=None,
                                    cpu_seconds=sum(x))))
        rows.append(dict(index=index,phases=part))
    pre=dict(generated_sha256='a'*64,rows=rows)
    training=dict(format='othello-owner-lower6-training-v1',status='complete',accepted=True,
        completed_indices=owner.TRAINING,heldout_measured=False,donors_unchanged=True,
        generated_sources_unchanged=True,generated_sha256='a'*64,rows=rows,phases=phases)
    return pre,training


class OwnerContinueTests(unittest.TestCase):
    def test_forecast_uses_only_complete_training_and_fixed_holdout(self):
        pre,training=fixture()
        before=copy.deepcopy(training)
        result=cost.prediction(pre,training)
        self.assertEqual(training,before)
        self.assertFalse(result['heldout_measured_when_fitted'])
        self.assertEqual({p['root_index'] for p in result['rows']},set(owner.HELDOUT))
        self.assertEqual(len(result['rows']),30)
        self.assertGreater(result['predicted_cpu_seconds'],0)
        self.assertFalse(result['production_authorized'])

    def test_partial_censored_or_heldout_training_is_rejected(self):
        for mutate in (lambda t:t.update(heldout_measured=True),
                       lambda t:t['phases'].pop(),
                       lambda t:t['phases'][0]['record'].update(stop_reason='cpu-limit'),
                       lambda t:t['phases'][0].update(accepted=False),
                       lambda t:t['phases'].append(dict(t['phases'][0],label='root10-part0'))):
            pre,training=fixture();mutate(training)
            with self.assertRaises(ValueError):cost.prediction(pre,training)

    def test_no_finite_fit_from_invalid_measurements(self):
        for cpu in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):cost.nnls([dict(x=[1,1],cpu_seconds=cpu)],2)

    def test_residual_is_censored_until_the_entire_holdout_accepts(self):
        forecast=cost.prediction(*fixture())
        phases=[dict(label=p['label'],accepted=True,
                     record=dict(cpu_seconds=p['predicted_cpu_seconds']*1.10)) for p in forecast['rows']]
        result=cost.residuals(forecast,phases)
        self.assertAlmostEqual(result['relative_error'],.10)
        self.assertTrue(result['within_30_percent'])
        self.assertIsNone(cost.residuals(forecast,phases[:-1])['relative_error'])
        phases[0]['accepted']=False
        self.assertIsNone(cost.residuals(forecast,phases)['relative_error'])
        with self.assertRaises(ValueError):cost.residuals(forecast,phases+[phases[0]])


if __name__=='__main__':unittest.main()
