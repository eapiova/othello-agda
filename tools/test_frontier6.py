#!/usr/bin/env python3
"""Small scalar cross-checks of native proof-prefix statistics."""
import random
import unittest
import ref
import frontier6


def sample(discs=31, seed=9):
    rng = random.Random(seed)
    s = ref.initial(6)
    while sum(c != 0 for c in s.cells) < discs:
        children = ref.successors(s)
        if not children:
            break
        s = rng.choice(children)
    return s


def scalar_prefix(s, lower, threshold, discs):
    memo = {}
    def holds(state):
        v = ref.value(state)
        return v >= threshold if lower else v <= threshold
    def visit(state):
        if state in memo:
            return memo[state]
        children = ref.successors(state)
        leaf = not children or sum(c != 0 for c in state.cells) >= discs
        tree, hints, selected = 1, 0, -1
        if not leaf:
            own = (state.turn == ref.WHITE) == lower
            if own and ref.placements(state):
                selected = next(i for i, child in enumerate(children) if holds(child))
                children = (children[selected],)
                hints = 1
            for child in children:
                ct, ch, _, _ = visit(child)
                tree += ct
                hints += ch
        memo[state] = (tree, hints, leaf, selected)
        return memo[state]
    tree, hints, _, _ = visit(s)
    return memo, tree, hints


class FrontierTests(unittest.TestCase):
    def check_prefix(self, s, lower=True, discs=36):
        value = ref.value(s)
        threshold = value if lower else value + 1
        actual = frontier6.query(s, direction='lower' if lower else 'upper',
                                threshold=threshold, frontier_discs=discs,
                                max_states=10000, tt_bits=4, small=0, emit_states=True)
        memo, tree, hints = scalar_prefix(s, lower, threshold, discs)
        self.assertTrue(actual['complete'], actual)
        self.assertEqual(actual['tree_nodes_S'], tree)
        self.assertEqual(actual['hint_occurrences_H'], hints)
        self.assertEqual(actual['unique_dag_nodes'], len(memo))
        self.assertEqual(actual['frontier_distinct_L'], sum(v[2] for v in memo.values()))
        for state in actual['states']:
            s2 = ref.State(6, tuple(map(int, state['position'])),
                           ref.WHITE if state['turn'] == 'white' else ref.BLACK)
            self.assertEqual(state['selected_index'], memo[s2][3])
        return actual

    def test_tiny_both_bounds(self):
        for seed in (3, 9, 12):
            for lower in (False, True):
                self.check_prefix(sample(seed=seed), lower)

    def test_frontier_leaf_and_negative_bound(self):
        s = sample(31)
        self.check_prefix(s, discs=32)
        result = frontier6.query(s, threshold=-36, frontier_discs=31, tt_bits=0)
        self.assertTrue(result['complete'])
        self.assertEqual(result['tree_nodes_S'], 1)

    def test_failed_root(self):
        s = sample(34)
        value = ref.value(s)
        direction, threshold = ('lower', value+1) if value < 36 else ('upper', value-1)
        result = frontier6.query(s, direction=direction, threshold=threshold, tt_bits=0)
        self.assertTrue(result['root_validated'])
        self.assertFalse(result['root_holds'])
        self.assertFalse(result['complete'])

    def test_caps(self):
        s = sample(31)
        result = frontier6.query(s, threshold=ref.value(s), max_states=1, frontier_discs=36, tt_bits=0)
        self.assertFalse(result['complete'])
        self.assertEqual(result['tree_count_kind'], 'lower-bound')
        result = frontier6.query(s, max_nodes=1, tt_bits=0)
        self.assertFalse(result['root_validated'])
        self.assertTrue(result['oracle_aborted'])

    def test_study_same_process_grid(self):
        s = sample(31)
        value = ref.value(s)
        records = list(frontier6.study(s, threshold=value, frontier_grid='32,34',
                                      tt_bits=4, small=0, max_states=10000,
                                      baseline_cpu_seconds=2, max_cpu_seconds=2))
        self.assertEqual(records[0]['record_type'], 'exact')
        self.assertTrue(records[0]['complete'])
        self.assertEqual(records[0]['value'], value)
        self.assertIn('binary_sha256', records[0]['build_metadata'])
        self.assertEqual(records[-1]['complete_cases'], 4)
        for record in records[1:-1]:
            standalone = frontier6.query(s, threshold=value, direction=record['direction'],
                                         frontier_discs=record['frontier_discs'],
                                         tt_bits=4, small=0, max_states=10000)
            for key in ('tree_nodes_S', 'unique_dag_nodes', 'frontier_distinct_L',
                        'hint_occurrences_H', 'complete'):
                self.assertEqual(record[key], standalone[key])
        self.assertEqual(records[-1]['nodes'], sum(r['nodes'] for r in records[:-1]))
        self.assertEqual(records[-1]['native_calls'], sum(r['native_calls'] for r in records[:-1]))

    def test_study_skip_and_partial(self):
        s = sample(31)
        value = ref.value(s)
        skipped = list(frontier6.study(s, threshold=value+1, frontier_grid='36', tt_bits=0))
        self.assertEqual(len(skipped), 2)
        self.assertTrue(skipped[-1]['skipped_grid'])
        self.assertFalse(skipped[-1]['complete'])
        partial = list(frontier6.study(s, threshold=value, frontier_grid='36', tt_bits=0,
                                      max_states=1, max_nodes=1))
        self.assertTrue(partial[0]['complete'])
        self.assertFalse(partial[-1]['complete'])
        self.assertTrue(all(not r['complete'] for r in partial[1:-1]))

    def test_completed_cases_after_abort_match_scalar(self):
        aborted = completed_later = False
        for seed in (3, 9, 12):
            state = sample(31, seed)
            value = ref.value(state)
            for cap in (32, 128):
                records = list(frontier6.study(state, threshold=value,
                    frontier_grid='36,32,31', tt_bits=4, small=0, max_nodes=cap,
                    max_states=10000, emit_states=True))
                seen_abort = False
                for record in records[1:-1]:
                    seen_abort |= record['oracle_aborted']
                    aborted |= seen_abort
                    if not record['complete']:
                        continue
                    completed_later |= seen_abort
                    memo, tree, hints = scalar_prefix(state,
                        record['direction'] == 'lower', value, record['frontier_discs'])
                    self.assertEqual(record['tree_nodes_S'], tree)
                    self.assertEqual(record['hint_occurrences_H'], hints)
                    self.assertEqual(record['unique_dag_nodes'], len(memo))
                    for item in record['states']:
                        child = ref.State(6, tuple(map(int, item['position'])),
                            ref.WHITE if item['turn'] == 'white' else ref.BLACK)
                        self.assertEqual(item['selected_index'], memo[child][3])
        self.assertTrue(aborted)
        self.assertTrue(completed_later)

    def test_pass_and_dedup(self):
        found_pass = found_dedup = False
        for seed in range(40):
            s = sample(32, seed)
            result = self.check_prefix(s)
            found_dedup |= result['dedup_hits'] > 0
            for state in result['states']:
                p = ref.State(6, tuple(map(int, state['position'])),
                              ref.WHITE if state['turn'] == 'white' else ref.BLACK)
                found_pass |= not ref.placements(p) and bool(ref.successors(p))
            if found_pass and found_dedup:
                break
        self.assertTrue(found_pass)
        self.assertTrue(found_dedup)


if __name__ == '__main__':
    unittest.main()
