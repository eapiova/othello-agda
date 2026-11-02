"""Small scalar/mocked tests for repeated hint leaves and closed-work caps."""
import copy
import subprocess
import unittest
import hint_profile6
import ref
from test_frontier6 import sample
from test_hint_bench6 import fixture


class ProfileTests(unittest.TestCase):
    def test_topological_weights_match_expanded_certificate(self):
        repeated = False
        for seed in range(10):
            row, native = fixture(sample(32, seed), 'lower', 36)
            weights = hint_profile6.graph_weights(row, 'lower', native)
            self.assertEqual(len(weights), sum(item['leaf'] for item in native['states']))
            repeated |= any(n > 1 for n in weights.values())
            result = hint_profile6.leaf_work(row, 'lower', native,
                query=lambda *a, **kw: self.fail('terminal L never runs forces'))
            self.assertTrue(result['complete'])
            self.assertEqual(result['weighted_W'], 0)
            self.assertEqual(result['terminal_leaf_occurrences'], sum(weights.values()))
        self.assertTrue(repeated)
        row, native = fixture(sample(32, 9), 'lower', 34)
        weights = hint_profile6.graph_weights(row, 'lower', native)
        expected = 7 * sum(weight for state, weight in weights.items() if ref.successors(state))
        self.assertGreater(expected, 0)
        result = hint_profile6.leaf_work(row, 'lower', native,
            query=lambda command, state, **kw: dict(holds=True, noTT=True, order='row-major',
                fuel=80, direction='lower', threshold=row['value'], nodes=7, cpu_seconds=0.001))
        self.assertTrue(result['complete'])
        self.assertEqual(result['weighted_W'], expected)

    def test_count_and_missing_child_rejected(self):
        row, native = fixture(sample(32, 2), 'lower', 36)
        bad = copy.deepcopy(native); bad['tree_nodes_S'] += 1
        with self.assertRaisesRegex(ValueError, 'count differs'):
            hint_profile6.graph_weights(row, 'lower', bad)
        bad = copy.deepcopy(native); bad['states'].pop(0)
        with self.assertRaisesRegex(ValueError, 'missing graph child'):
            hint_profile6.graph_weights(row, 'lower', bad)

    def test_censor_and_false_bound_never_completed_total(self):
        row, native = fixture(sample(32, 3), 'upper', 34)
        def timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(['mirror'], 0.01)
        result = hint_profile6.leaf_work(row, 'upper', native, query=timeout)
        self.assertFalse(result['complete']); self.assertIsNone(result['weighted_W'])
        self.assertTrue(any(r['status'] == 'timeout' for r in result['records']))
        result = hint_profile6.leaf_work(row, 'upper', native, query=lambda *a, **k: {'holds': False})
        self.assertFalse(result['complete']); self.assertIsNone(result['weighted_W'])
        self.assertTrue(any(r['status'] == 'failure' for r in result['records']))

    def test_leaf_cap_omits_total(self):
        row, native = fixture(sample(32, 2), 'lower', 34)
        result = hint_profile6.leaf_work(row, 'lower', native, max_leaves=0,
            query=lambda *a, **k: self.fail('no native query under cap'))
        self.assertFalse(result['complete']); self.assertIsNone(result['weighted_W'])
        self.assertEqual(result['stop_reason'], 'distinct-leaf cap')


if __name__ == '__main__':
    unittest.main()
