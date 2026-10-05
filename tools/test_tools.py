#!/usr/bin/env python3
"""Rules-oracle cross-checks and adversarial certificate-input tests."""
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
import generate
import ref

ROOT = Path(__file__).resolve().parents[1]

class RulesTests(unittest.TestCase):
    def test_initial_moves(self):
        self.assertEqual([p for p, _ in ref.placements(ref.initial(4))],
                         [(0, 1), (1, 0), (2, 3), (3, 2)])

    def test_known_perft(self):
        self.assertEqual([ref.perft(ref.initial(8), d) for d in range(6)],
                         [1, 4, 12, 56, 244, 1396])

    def test_no_edge_wrap(self):
        cells = [0] * 16
        cells[3], cells[4] = ref.WHITE, ref.BLACK
        self.assertEqual(ref.captured(ref.State(4, tuple(cells), ref.BLACK), 0, 2), ())

    def test_corner_and_multiple_directions(self):
        cells = [0] * 16
        cells[1], cells[2] = ref.WHITE, ref.BLACK
        self.assertEqual(ref.captured(ref.State(4, tuple(cells), ref.BLACK), 0, 0), (1,))
        cells = [0] * 16
        cells[6] = cells[9] = ref.WHITE
        cells[7] = cells[13] = ref.BLACK
        s = ref.State(4, tuple(cells), ref.BLACK)
        self.assertEqual(set(ref.captured(s, 1, 1)), {6, 9})
        self.assertEqual(ref.captured(s, 1, 3), ())  # occupied

    def test_empty_terminal(self):
        s = ref.State(4, (0,) * 16, ref.BLACK)
        self.assertEqual(ref.successors(s), ())
        self.assertEqual(ref.score(s), 0)

    def test_differential_random_games(self):
        rng = random.Random(2026)
        for n in (4, 6, 8):
            for _ in range(12):
                s = ref.initial(n)
                while True:
                    scalar = ref.successors(s)
                    bits = tuple(generate.scalar(t) for t in generate.successors(generate.from_scalar(s)))
                    self.assertEqual(bits, scalar)
                    if not scalar:
                        break
                    s = rng.choice(scalar)

    def test_independent_exact_value(self):
        self.assertEqual(ref.value(ref.initial(4)), 8)
        self.assertEqual(generate.value(generate.from_scalar(ref.initial(4))), 8)
        final = ref.perfect_line(ref.initial(4))[-1]
        self.assertEqual(final["score"], 8)

class CertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = generate.strict_load(ROOT / "certificates/four-v1.json")

    def test_both_bounds_and_every_visited_position(self):
        visited = set()
        for direction in ("lower", "upper"):
            self.assertTrue(generate.independent_check(ref.initial(4), self.doc[direction], direction, 8, visited))
        for s in visited:
            self.assertEqual(ref.successors(s), tuple(generate.scalar(t) for t in
                             generate.successors(generate.from_scalar(s))))

    def test_missing_or_extra_opponent_reply(self):
        for delta in (-1, 1):
            node = copy.deepcopy(self.doc["lower"])
            self.assertEqual(node["kind"], "fork")
            if delta == -1:
                node["children"].pop()
            else:
                node["children"].append(node["children"][0])
            self.assertFalse(generate.independent_check(ref.initial(4), node, "lower", 8))

    def test_illegal_choice_and_premature_leaf_and_pass(self):
        node = copy.deepcopy(self.doc["upper"])
        node["index"] = 63
        self.assertFalse(generate.independent_check(ref.initial(4), node, "upper", 8))
        self.assertFalse(generate.independent_check(ref.initial(4), {"kind": "leaf"}, "lower", 8))
        self.assertFalse(generate.independent_check(ref.initial(4),
                         {"kind": "pass", "child": {"kind": "leaf"}}, "lower", 8))

    def test_forced_pass_and_losing_leaf(self):
        found_pass = found_bad_terminal = False
        def walk(s, node):
            nonlocal found_pass, found_bad_terminal
            children = ref.successors(s)
            if node["kind"] == "pass":
                found_pass = True
                self.assertFalse(ref.placements(s))
                self.assertEqual(len(children), 1)
                walk(children[0], node["child"])
            elif node["kind"] == "choice":
                walk(children[node["index"]], node["child"])
            elif node["kind"] == "fork":
                for t, c in zip(children, node["children"]):
                    walk(t, c)
            else:
                found_bad_terminal = True
                self.assertFalse(generate.independent_check(s, node, "lower", ref.score(s) + 1))
        walk(ref.initial(4), self.doc["lower"])
        self.assertTrue(found_pass)
        self.assertTrue(found_bad_terminal)

    def test_reject_malformed_data(self):
        for replacement in (True, 4.0, "four", 6):
            bad = copy.deepcopy(self.doc)
            bad["size"] = replacement
            with self.assertRaises(ValueError):
                generate.validate_document(bad)
        for replacement in (True, -1, 64, 1.5, "0; postulate injected"):
            bad = {"kind": "choice", "index": replacement, "child": {"kind": "leaf"}}
            with self.assertRaises(ValueError):
                generate.validate_node(bad)
        with self.assertRaises(ValueError):
            generate.validate_node({"kind": "leaf", "postulate": "x"})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"size":4,"size":4}')
            with self.assertRaises(ValueError):
                generate.strict_load(path)

    def test_emission_is_deterministic(self):
        actual = (ROOT / "src/Othello/Generated4.agda").read_text()
        self.assertEqual(generate.emit_agda(self.doc), actual)

if __name__ == "__main__":
    unittest.main()
