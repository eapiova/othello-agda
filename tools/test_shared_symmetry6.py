"""AI-assisted scalar rejection tests and bounded real-line fixture generation."""
import copy
import sys
import unittest
from pathlib import Path
import bench6
import generate6
import ref
import shared6
import shared_symmetry6 as gen
import symmetry_stats6 as sym
from test_hint_bench6 import fixture
from test_shared6 import LINE10


class SymmetryGeneratorTests(unittest.TestCase):
    def test_move_index_transport(self):
        state = bench6.decode(LINE10)
        raw = shared6.graph_from_search(state, 'lower', 4)
        canonical = gen.normalize(raw)
        changed = False
        for s, (kind, children) in raw.items():
            if isinstance(kind, tuple):
                c, tag = sym.canonical(s)
                if canonical[c][1] == [sym.transform(children[0], tag)]:
                    self.assertEqual(ref.successors(c)[canonical[c][0][1]], sym.transform(children[0], tag))
                    changed |= kind[1] != canonical[c][0][1]
        self.assertTrue(changed)
        entries, stats = gen.layered(canonical, state)
        self.assertTrue(gen.replay(entries, state, 'lower', 4))
        self.assertGreater(stats['nonidentity_citations'], 0)
        self.assertEqual(stats['checked_tokens'], sum(sum(c in 'LCFPSKR' for c in t) for _, t in entries))

    def test_bad_tag_and_missing_reference(self):
        state = generate6.replay()[0][-1]
        c, tag = sym.canonical(state)
        self.assertFalse(gen.replay([(state, 'R8;')], state, 'lower', 4))
        self.assertFalse(gen.replay([(state, f'R{tag};')], state, 'lower', 4))
        self.assertTrue(gen.replay([(c, 'L'), (state, f'R{tag};')], state, 'lower', 4))
        self.assertFalse(gen.replay([(state, f'R{tag};'), (c, 'L')], state, 'lower', 4))

    def test_missing_opponent_branch(self):
        root = bench6.decode(LINE10)
        row, native = fixture(root, 'lower')
        graph = shared6.graph_from_native(native, root, 'lower', row['value'])
        fork = next(s for s, (k, cs) in graph.items() if k == 'fork' and len(cs) > 1)
        broken = copy.deepcopy(graph)
        broken[fork][1].pop()
        with self.assertRaisesRegex(ValueError, 'missing opponent branch'):
            gen.validate_graph(broken, root, 'lower', row['value'])
        entries, _ = gen.layered(gen.normalize(graph), root)
        damaged = [(s, t.replace('F2;', 'F1;', 1)) for s, t in entries]
        if damaged != entries:
            self.assertFalse(gen.replay(damaged, root, 'lower', row['value']))
        native['states'] = [item for item in native['states'] if item['position'] != ''.join(map(str, graph[fork][1][0].cells))]
        with self.assertRaises(ValueError):
            gen.graph_from_native(native, root, 'lower', row['value'])

    def test_legal_forced_pass_both_bounds(self):
        root = generate6.replay()[0][30]
        self.assertFalse(ref.placements(root))
        self.assertEqual(len(ref.successors(root)), 1)
        for direction in ('lower', 'upper'):
            row, native = fixture(root, direction)
            self.assertEqual(row['value'], 4)
            encoded, stats = gen.build(native, root, direction, 4)
            self.assertIn('P', encoded)
            self.assertGreater(stats['nonidentity_citations'], 0)
            self.assertEqual(stats['encoded_bytes'], len(encoded))


def write_fixture():
    root = generate6.replay()[0][30]
    certificates, report = {}, {}
    for direction in ('lower', 'upper'):
        row, native = fixture(root, direction)
        if row['value'] != 4:
            raise ValueError('fixture is not +4')
        certificates[direction], report[direction] = gen.build(native, root, direction, 4)
    Path(sys.argv[sys.argv.index('--generate-fixture') + 1]).write_text(gen.fixture_text(root, certificates))
    import json
    print(json.dumps(report))


if __name__ == '__main__':
    if '--generate-fixture' in sys.argv:
        write_fixture()
    else:
        unittest.main()
