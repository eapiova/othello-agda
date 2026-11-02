"""Exercise branch-preserving exact-state certificate factorization."""
import unittest

import bench6
from generate6 import encode_state
import global_assembly6 as assembly
from global_shared6 import replay_many
import lower_split6 as split
import ref
import shared6


class LowerSplitTests(unittest.TestCase):
    def test_factoring_preserves_replies_and_replays_the_bound(self):
        # A deterministic late-game reachable state; search supplies all replies.
        state = ref.initial(6)
        while state.cells.count(0) > 3 and ref.successors(state):
            state = ref.successors(state)[0]
        # Use the independent search to select a true bound and a finite tree.
        direction, threshold = 'lower', -36
        graph = shared6.graph_from_search(state, direction, threshold)
        # Disable pre-existing internal sharing to obtain a simple reply tree.
        def tree(s):
            kind, children = graph[s]
            if kind == 'leaf':
                return 'L'
            if kind == 'pass':
                return 'P'+tree(children[0])
            if kind == 'fork':
                return f'F{len(children)};'+''.join(tree(child) for child in children)
            index = ref.successors(s).index(children[0])
            return f'C{index};'+tree(children[0])
        body = tree(state)
        key = encode_state(state)
        plan = dict(format='othello-global-shared6-plan-v1', direction='lower', threshold=4,
                    roots=[key], entries=[dict(state=key, certificate=body, references=[])])
        result, cuts = split.factor(plan, cap=3)
        self.assertTrue(cuts)
        self.assertEqual(result['roots'], plan['roots'])
        self.assertTrue(all(assembly.tokens(entry['certificate']) <= 3 for entry in result['entries']))
        self.assertEqual(sum(assembly.tokens(entry['certificate']) for entry in result['entries']),
                         assembly.tokens(body)+len(cuts))
        entries = [(bench6.decode(entry['state']), entry['certificate']) for entry in result['entries']]
        # The independent replay takes the fixture's weaker score threshold.
        self.assertTrue(replay_many(entries, [state], direction, threshold))

    def test_small_entries_are_unchanged_and_capacity_fails_closed(self):
        key = 'w'+'2'*36
        plan = dict(format='othello-global-shared6-plan-v1', direction='lower', threshold=4,
                    roots=[key], entries=[dict(state=key, certificate='L', references=[])])
        result, cuts = split.factor(plan)
        self.assertEqual(plan, result)
        self.assertEqual(cuts, [])
        self.assertTrue(replay_many([(bench6.decode(key), 'L')], [bench6.decode(key)], 'lower', 4))
        with self.assertRaises(ValueError):
            split.factor(plan, cap=1)


if __name__ == '__main__':
    unittest.main()
