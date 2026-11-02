"""A component projection cannot authorize production or hide bad samples."""
import copy
import unittest

import sharing_report6 as gate


def profile(direction, kind='canonical frontier full-state classes'):
    discs=20 if direction=='lower' else 22
    cases=[dict(state='b'+'2'*i+'1'*(discs-i)+'0'*(36-discs),
                checked_tokens=100+i,entries=10+i,layered_encoded_bytes=1000+i,
                unique_nodes=80+i,tree_checked_tokens=150+i) for i in [0,1]]
    group=dict(direction=direction,threshold=4,frontier_discs=36,cases=cases,
               sum_tree_checked_tokens=301,sum_layered_checked_tokens=201,
               sharing_between_certificates=1,canonical_union_reduction=1)
    return dict(status='complete',sample_population_L=100,
                sample_population_kind=kind,selected_sample_count=2,sample_seed=42,groups=[group])


def pilot():
    return dict(accepted=True,stats=dict(checked_tokens=100,entries=10),
                parts=[dict(accepted=True,cpu_seconds=10,peak_rss_gib=.2)],
                assembly=dict(accepted=True,cpu_seconds=.1,peak_rss_gib=.2))


class GateTests(unittest.TestCase):
    def test_cheap_components_do_not_authorize_production(self):
        throughput=dict(accepted=True,batches=[dict(slots=8,accepted=True,effective_slots=6.6)])
        result=gate.report(profile('lower'),profile('upper'),pilot(),pilot(),throughput)
        self.assertFalse(result['production_authorized'])
        self.assertEqual(result['recommendation'],'NEEDS_FULL_WORKFLOW_PILOT')

    def test_censored_or_missing_sample_is_rejected(self):
        data=profile('lower');cost=gate.model(pilot())
        data['status']='failure'
        with self.assertRaises(ValueError):gate.sample(data,'lower',cost)
        data=profile('lower');data['groups'][0]['cases'].pop()
        with self.assertRaises(ValueError):gate.sample(data,'lower',cost)

    def test_other_upper_frontier_is_rejected(self):
        data=profile('upper');cost=gate.model(pilot())
        data['groups'][0]['cases'][0]['state']='b'+'1'*20+'0'*16
        with self.assertRaisesRegex(ValueError,'different opening frontier'):
            gate.sample(data,'upper',cost)

    def test_raw_and_canonical_populations_cannot_be_mixed(self):
        throughput=dict(accepted=True,batches=[dict(slots=8,accepted=True,effective_slots=6.6)])
        with self.assertRaisesRegex(ValueError,'different sampling units'):
            gate.report(profile('lower'),profile('upper','distinct raw frontier states'),
                        pilot(),pilot(),throughput)

    def test_wrong_bound_is_rejected(self):
        data=profile('lower');data['groups'][0]['threshold']=5
        with self.assertRaisesRegex(ValueError,'wrong bound'):
            gate.sample(data,'lower',gate.model(pilot()))


if __name__=='__main__':unittest.main()
