"""AI-assisted guards against partial proof claims and global extrapolation."""
import copy
import unittest
from global_report6 import summarize


def fixtures():
    native=dict(status='complete',scalar_replay=True,sample_size=2,
                source_population_kind='canonical frontier full-state classes',
                source_population=100,source_sample_seed=4,subsample_seed=5,
                direction='upper',threshold=4,plan_sha256='same',
                cases=[{'state':'first','compact_bytes':10},{'state':'second','compact_bytes':30}],
                stats=dict(roots=2,checked_tokens=10,global_compact_bytes=20,
                           union_canonical_states=12,reachable_canonical_states=11,
                           entries=5,per_root_d4_tokens=12,per_root_compact_bytes=40,
                           global_legacy_bytes=50,exact_baseline_bytes=60))
    part=dict(accepted=True,checked_tokens=10,compact_bytes=20,cpu_seconds=1,peak_rss_gib=.5)
    assembly=dict(plan_sha256='same',roots=2,direction='upper',threshold=4,
                  accepted=True,status='complete',part_count=1,parts=[part],
                  assembly={'accepted':True},machine={'hostname':'fixture'},ab=[])
    return native,assembly


class GlobalReportTests(unittest.TestCase):
    def test_complete_sample_still_cannot_authorize_production(self):
        n,a=fixtures();r=summarize(n,a)
        self.assertEqual(r['checked_root_guarantees'],2)
        self.assertFalse(r['production_authorized'])
        # The per-leaf mean is 20, not global-union 20/2; no population DAG total.
        self.assertEqual(r['per_leaf_compact_data_projection']['encoded_gib'],2000/2**30)
        self.assertNotIn('global_population_bytes',r['graph'])

    def test_accepted_shards_without_assembly_are_no_root_theorem(self):
        n,a=fixtures();a['assembly']['accepted']=False;a['accepted']=False
        r=summarize(n,a);self.assertEqual(r['checked_root_guarantees'],0)
        self.assertEqual(r['accepted_parts'],1)

    def test_graph_identity_and_complete_coverage_are_required(self):
        n,a=fixtures();wrong=copy.deepcopy(a);wrong['plan_sha256']='other'
        with self.assertRaises(ValueError):summarize(n,wrong)
        wrong=copy.deepcopy(a);wrong['parts'][0]['checked_tokens']=9
        with self.assertRaises(ValueError):summarize(n,wrong)
        wrong=copy.deepcopy(n);wrong['source_population_kind']='raw states'
        with self.assertRaises(ValueError):summarize(wrong,a)

    def test_subset_proof_does_not_become_a_complete_graph_claim(self):
        n,a=fixtures();a['accepted']=False;a['assembly']['accepted']=False
        subset=dict(plan_sha256='same',direction='upper',threshold=4,accepted=True,
                    assembly={'accepted':True},checked_root_guarantees=1,roots=['first'])
        r=summarize(n,a,subset)
        self.assertEqual(r['checked_subset_root_guarantees'],1)
        self.assertEqual(r['checked_root_guarantees'],0)
        self.assertFalse(r['production_authorized'])
        subset['roots']=['not-in-sample']
        with self.assertRaises(ValueError):summarize(n,a,subset)


if __name__=='__main__':unittest.main()
