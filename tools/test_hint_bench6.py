"""Scalar synthetic DAG validation: no native compiler or Agda required."""
import copy
import unittest
import ref
import hint_bench6
import generate6
from test_frontier6 import sample, scalar_prefix


def fixture(state, direction='lower', discs=36):
    value = ref.value(state)
    memo, tree, hints = scalar_prefix(state, direction == 'lower', value, discs)
    native = dict(complete=True, root_validated=True, root_holds=True,
                  count_overflow=False, tree_count_kind='exact', direction=direction,
                  threshold=value, frontier_discs=discs, tree_nodes_S=tree,
                  unique_dag_nodes=len(memo), hint_occurrences_H=hints,
                  states=[dict(position=''.join(map(str,s.cells)),
                      turn='white' if s.turn == ref.WHITE else 'black',
                      direction=direction, threshold=value, leaf=v[2], selected_index=v[3])
                          for s,v in memo.items()])
    return dict(state=generate6.encode_state(state), value=value), native


class HintTests(unittest.TestCase):
    def test_roundtrip_row_major_and_both_bounds(self):
        for direction in ('lower','upper'):
            row,native = fixture(sample(33,9), direction)
            encoded, count = hint_bench6.certificate(row,direction,native)
            self.assertEqual(count,native['tree_nodes_S'])
            for item in native['states']:
                if item['selected_index'] >= 0:
                    self.assertIn(f"C{item['selected_index']};", encoded)
            self.assertIn('checkLocal Fast.fastGame6',hint_bench6.proof_text(row,direction,encoded))

    def test_missing_reply_and_partial_rejected(self):
        row,native = fixture(sample(33,9))
        bad = copy.deepcopy(native)
        bad['states'].pop(0)
        bad['unique_dag_nodes'] -= 1
        with self.assertRaisesRegex(ValueError,'missing required child'):
            hint_bench6.certificate(row,'lower',bad)
        native['complete'] = False
        with self.assertRaisesRegex(ValueError,'incomplete'):
            hint_bench6.certificate(row,'lower',native)

    def test_pass_and_negative_threshold(self):
        states, _, events = generate6.replay()
        passed = states[30]
        swapped = ref.State(6, tuple(3-c if c else 0 for c in passed.cells), 3-passed.turn)
        row,native = fixture(swapped)
        encoded, _ = hint_bench6.certificate(row,'lower',native)
        self.assertTrue(encoded.startswith('P'))
        self.assertLess(row['value'],0)
        self.assertIn(f"neg {abs(row['value'])}",hint_bench6.proof_text(row,'lower',encoded))

    def test_frontier_solve_and_size_cap(self):
        row,native = fixture(sample(33,9),discs=33)
        self.assertEqual(hint_bench6.certificate(row,'lower',native),('S80;',1))
        with self.assertRaisesRegex(ValueError,'byte cap'):
            hint_bench6.certificate(row,'lower',native,3)

    def test_bound_and_count_rejected(self):
        row,native = fixture(sample(33,9))
        native['tree_nodes_S'] += 1
        with self.assertRaisesRegex(ValueError,'tree count'):
            hint_bench6.certificate(row,'lower',native)
        native['states'][0]['threshold'] += 1
        with self.assertRaisesRegex(ValueError,'mismatched bound'):
            hint_bench6.certificate(row,'lower',native)


if __name__ == '__main__':
    unittest.main()
