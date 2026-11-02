"""Statistical projections must retain censoring and reject incomplete totals."""
import unittest
from shared_study6 import terminal_projection


class ProjectionTests(unittest.TestCase):
    def profile(self):
        return {'sample_seed': 42, 'sample_population_L': 100,
                'selected_states': ['a', 'b'],
                'cases': [{'frontier_discs': 36, 'status': 'complete',
                           'native': {'complete': True, 'tree_nodes_S': n},
                           'encoded_bytes': 2*n} for n in [10, 30]]}

    def test_other_cut_censoring_preserved(self):
        profile = self.profile()
        profile['cases'].append({'frontier_discs': 28, 'status': 'leaf-work-capped',
                                 'row': {'id': 'heavy'}})
        result = terminal_projection(profile)
        self.assertEqual(result['full_terminal_samples_S'], 40)
        self.assertEqual(result['censored_other_cuts'][0]['id'], 'heavy')

    def test_censored_terminal_rejected(self):
        profile = self.profile()
        profile['cases'][0]['status'] = 'capped'
        with self.assertRaises(ValueError): terminal_projection(profile)

    def test_missing_terminal_rejected(self):
        profile = self.profile()
        profile['cases'].pop()
        with self.assertRaises(ValueError): terminal_projection(profile)


if __name__ == '__main__': unittest.main()
