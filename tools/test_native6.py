#!/usr/bin/env python3
"""Bounded native/scalar differential checks; this test is outside Agda trust."""
from __future__ import annotations
import json
from pathlib import Path
import random
import resource
import subprocess
import time
import unittest
import ref
import solve6


def reachable(seed: int, empties: int) -> ref.State:
    rng = random.Random(seed)
    state = ref.initial(6)
    while state.cells.count(0) > empties:
        children = ref.successors(state)
        if not children:
            raise AssertionError(f'game terminated early for seed {seed}')
        state = rng.choice(children)
    return state


class Native6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = solve6.build()

    def test_malformed_rejected(self):
        for position in ('', '0' * 35, '0' * 37, '0' * 35 + '3', '0' * 35 + 'x'):
            with self.subTest(position=position), self.assertRaises(ValueError):
                solve6.query('moves', position)
        for kwargs in ({'turn': 'no'}, {'tt_bits': -1}, {'tt_bits': 27}, {'small': -1}, {'deep_order': -1}, {'deep_order': 37}, {'fuel': -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                solve6.query('moves', **kwargs)
        with self.assertRaises(ValueError):
            solve6.query('perft', depth=-1)
        with self.assertRaises(ValueError):
            solve6.query('perft')
        # Binary validates independently of Python.
        bad = subprocess.run([str(self.binary), 'moves', '--position', 'bad'], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn('error', json.loads(bad.stderr))

    def test_move_and_perft_agreement(self):
        states = [ref.initial(6)]
        rng = random.Random(20261005)
        state = states[0]
        for _ in range(35):
            children = ref.successors(state)
            if not children:
                break
            state = rng.choice(children)
            states.append(state)
        for s in states:
            with self.subTest(state=s):
                self.assertEqual(solve6.successors(s), ref.successors(s))
                expected_moves = [list(move) for move, _ in ref.placements(s)]
                if not expected_moves and ref.successors(s):
                    expected_moves = ['pass']
                output = solve6.moves(s)
                self.assertEqual([m['move'] for m in output], expected_moves)
                self.assertEqual([m['index'] for m in output], list(range(len(output))))
        for s in (states[0], states[9], states[20], states[-1]):
            for depth in range(5):
                self.assertEqual(solve6.perft(s, depth), ref.perft(s, depth))

    def test_forced_pass_and_terminal(self):
        forced = ref.State(6, tuple(map(int, '210222' + '2' * 30)), ref.BLACK)
        self.assertFalse(ref.placements(forced))
        self.assertTrue(ref.placements(forced._replace(turn=ref.WHITE)))
        self.assertEqual(solve6.moves(forced)[0]['move'], 'pass')
        self.assertEqual(solve6.successors(forced), ref.successors(forced))
        for depth in range(5):
            self.assertEqual(solve6.perft(forced, depth), ref.perft(forced, depth))
        ref.value.cache_clear()
        self.assertEqual(solve6.solve(forced), ref.value(forced))
        self.assertEqual(solve6.solve(forced), 36)
        # Both players immobile while empty cells remain: no fictitious passes.
        terminal = ref.State(6, (1,) + (0,) * 35, ref.WHITE)
        self.assertTrue(solve6.query('moves', terminal)['terminal'])
        self.assertEqual(solve6.perft(terminal, 0), 1)
        self.assertEqual(solve6.perft(terminal, 1), 0)
        self.assertEqual(solve6.solve(terminal), -1)

    def test_reachable_exact_and_threshold_values(self):
        for seed in range(12):
            state = reachable(seed, 8 if seed < 2 else 6)
            self.assertLessEqual(state.cells.count(0), 8)
            ref.value.cache_clear()  # independent cache boundary per position
            expected = ref.value(state)
            with self.subTest(seed=seed, value=expected):
                self.assertEqual(solve6.solve(state), expected)
                for threshold in (expected - 1, expected, expected + 1):
                    if -36 <= threshold <= 36:
                        self.assertEqual(solve6.bounds(state, 'lower', threshold), expected >= threshold)
                        self.assertEqual(solve6.bounds(state, 'upper', threshold), expected <= threshold)
        ref.value.cache_clear()

    def test_mirror_scalar_counts_and_fuel(self):
        from validate6 import scalar_mirror
        forced = ref.State(6, tuple(map(int, '210222' + '2' * 30)), ref.BLACK)
        terminal = ref.State(6, (1,) + (0,) * 35, ref.WHITE)
        states = [forced, terminal, ref.State(6, (2,) * 36, ref.BLACK), reachable(17, 4)]
        for state in states:
            for turn in (ref.BLACK, ref.WHITE):
                state = state._replace(turn=turn)
                for direction in ('lower', 'upper'):
                    for threshold in (-36, -1, 0, 1, 36):
                        for fuel in (0, 1, 2, 80):
                            with self.subTest(state=state, direction=direction, threshold=threshold, fuel=fuel):
                                expected, nodes = scalar_mirror(state, direction, threshold, fuel)
                                result = solve6.query('mirror', state, direction=direction, threshold=threshold, fuel=fuel)
                                self.assertEqual((result['holds'], result['nodes']), (expected, nodes))
                                self.assertEqual(result['tt_bytes'], 0)
                                self.assertTrue(result['noTT'])
                                self.assertEqual(result['order'], 'row-major')
                                self.assertEqual(result['fuel'], fuel)

    def test_deep_order_configuration(self):
        state = reachable(35, 6)
        ref.value.cache_clear()
        expected = ref.value(state)
        for order in (0, 5, 13, 36):
            result = solve6.query('solve', state, deep_order=order, small=0, tt_bits=4)
            self.assertEqual(result['value'], expected)
            self.assertEqual(result['deep_order'], order)
        self.assertEqual(solve6.query('moves')['deep_order'], 13)
        ref.value.cache_clear()

    def test_full_keys_and_table_collisions(self):
        selftest = solve6.query('tt-selftest', tt_bits=0)
        self.assertTrue(selftest['ok'])
        self.assertTrue(selftest['forced_equal_hash'])
        self.assertGreater(selftest['tt_collisions'], 0)
        collisions = 0
        for seed in range(4):
            state = reachable(seed + 30, 7)
            ref.value.cache_clear()
            expected = ref.value(state)
            for bits in (0, 2, 8):
                result = solve6.query('solve', state, tt_bits=bits, small=0)
                self.assertEqual(result['value'], expected)
                self.assertEqual(result['tt_bytes'], 48 * (1 << bits))
                collisions += result['tt_collisions']
        self.assertGreater(collisions, 0)
        ref.value.cache_clear()


def main():
    start = time.monotonic()
    before_self = resource.getrusage(resource.RUSAGE_SELF)
    before_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Native6Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    after_self = resource.getrusage(resource.RUSAGE_SELF)
    after_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = ((after_self.ru_utime + after_self.ru_stime) - (before_self.ru_utime + before_self.ru_stime)
           + (after_children.ru_utime + after_children.ru_stime) - (before_children.ru_utime + before_children.ru_stime))
    record = {'ok': result.wasSuccessful(), 'tests': result.testsRun,
              'cpu_seconds_including_children': cpu, 'wall_seconds': time.monotonic() - start,
              'self_maxrss_kib': after_self.ru_maxrss, 'children_maxrss_kib': after_children.ru_maxrss,
              'build': json.loads((solve6.BUILD / 'build.json').read_text()),
              'exact_random_positions': 16, 'max_empty_cells': 8,
              'reference_cache': 'cleared separately for each exact position',
              'initial_full_solve': False, 'trust': 'untrusted differential evidence; no Agda claims'}
    (solve6.BUILD / 'tests.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k != 'build'}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    main()
