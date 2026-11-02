"""AI-assisted small tests; no solver/native builds, mirror, or Agda jobs."""
import argparse
import copy
import json
import contextlib
import io
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import bench6
import generate6
import ref
import shared6
import symmetry_stats6 as stats


def native(states=None):
    if states is None:
        states = [dict(position='1'*i+'2'*(36-i), turn='black', direction='lower',
                       threshold=-36, leaf=True, selected_index=-1) for i in range(8)]
    return dict(complete=True, root_validated=True, root_holds=True,
                count_overflow=False, oracle_aborted=False, tree_count_kind='exact',
                direction='lower', threshold=-36, frontier_discs=30,
                unique_dag_nodes=len(states), frontier_distinct_L=len(states),
                tree_nodes_S=len(states), hint_occurrences_H=0, states=states)


def diamond():
    states = [ref.State(6, tuple([i % 3] + [0]*j + [1]*(35-j)),
                        ref.BLACK if i % 2 == 0 else ref.WHITE)
              for i, j in enumerate(range(6))]
    root, a, b, c, d, leaf = states
    return root, {root: ('fork', [a, b]), a: ('pass', [c]), b: ('pass', [c]),
                  c: ('pass', [d]), d: ('pass', [leaf]), leaf: ('leaf', [])}


class SymmetryTests(unittest.TestCase):
    def test_disk_union_matches_sets_and_keeps_groups_separate(self):
        store = stats.DiskUnion()
        directory = Path(store.directory.name)
        try:
            a,b='b'+'1'*36,'w'+'1'*36
            self.assertEqual(store.add(0,{a,b}),2)
            self.assertEqual(store.add(0,{a}),2)
            self.assertEqual(store.add(1,{a}),1)
            self.assertTrue(directory.exists())
        finally:
            store.close()
        self.assertFalse(directory.exists())

    def test_cli_larger_union_cap_requires_disk_backend(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            data=native([dict(position='1'*36,turn='black',direction='lower',
                              threshold=-36,leaf=True,selected_index=-1)])
            data['frontier_discs']=36
            (root/'native.json').write_text(json.dumps(data))
            case=dict(status='complete',direction='lower',frontier_discs=36,
                      row=dict(id='terminal',state='b'+'1'*36,value=-36),
                      native_path=str(root/'native.json'))
            (root/'profile.json').write_text(json.dumps(dict(cases=[case])))
            argv=['stats','profiles','--input',str(root/'profile.json'),
                  '--output',str(root/'output.json'),'--max-states','10000000']
            with patch('sys.argv',argv),contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):stats.main()
            with patch('sys.argv',argv+['--disk-union']),contextlib.redirect_stdout(io.StringIO()):
                stats.main()
            result=json.loads((root/'output.json').read_text())
            self.assertEqual(result['status'],'complete')
            self.assertEqual(result['groups'][0]['exact_union_full_states'],1)

    def test_explicit_tag_coordinates(self):
        self.assertEqual([stats.coordinate(t, 1, 2) for t in range(8)],
                         [(1, 2), (2, 4), (4, 3), (3, 1), (1, 3),
                          (3, 4), (4, 2), (2, 1)])

    def test_inverse_color_and_turn_preservation(self):
        rng = random.Random(42)
        for _ in range(15):
            state = ref.State(6, tuple(rng.randrange(3) for _ in range(36)),
                              rng.choice([ref.BLACK, ref.WHITE]))
            for tag in range(8):
                changed = stats.transform(state, tag)
                self.assertEqual(changed.turn, state.turn)
                for color in (0, 1, 2):
                    self.assertEqual(changed.cells.count(color), state.cells.count(color))
                self.assertEqual(stats.transform(changed, stats.INVERSES[tag]), state)
                self.assertEqual(generate6.encode_state(changed),
                                 stats.transform_key(generate6.encode_state(state), tag))

    def test_arbitrary_orientation_successor_sets_and_forced_pass(self):
        line, _, _ = generate6.replay()
        self.assertFalse(ref.placements(line[30]))
        self.assertEqual(len(ref.successors(line[30])), 1)
        rng = random.Random(130)
        arbitrary = [ref.State(6, tuple(rng.randrange(3) for _ in range(36)),
                               rng.choice([ref.BLACK, ref.WHITE])) for _ in range(12)]
        for state in arbitrary + [line[0], line[20], line[30], line[-1]]:
            for tag in range(8):
                self.assertEqual(set(ref.successors(stats.transform(state, tag))),
                                 {stats.transform(child, tag) for child in ref.successors(state)})

    def test_canonical_lex_min_lowest_tag_and_full_turn_key(self):
        state = bench6.decode('b002002000222222222022111001110001000')
        expected = min((generate6.encode_state(stats.transform(state, tag)), tag)
                       for tag in range(8))
        canonical, tag = stats.canonical(state)
        self.assertEqual((generate6.encode_state(canonical), tag), expected)
        for orientation in range(8):
            self.assertEqual(stats.canonical(stats.transform(state, orientation))[0], canonical)
        symmetric = ref.State(6, (ref.BLACK,)*36, ref.WHITE)
        self.assertEqual(stats.canonical(symmetric)[1], 0)
        self.assertNotEqual(stats.canonical_key('b'+'1'*36)[0],
                            stats.canonical_key('w'+'1'*36)[0])

    def test_sample_sorted_uniform_without_replacement_fixed_direction_seeds(self):
        keys = {stats.canonical_key('b'+'1'*i+'2'*(36-i))[0] for i in range(20)}
        sample = stats.canonical_sample(keys, 'lower', -36, 8)
        expected = random.Random(2026100604).sample(sorted(keys), 8)
        self.assertEqual([stats.item_key(item) for item in sample], expected)
        self.assertEqual(sample, stats.canonical_sample(set(reversed(sorted(keys))), 'lower', -36, 8))
        self.assertEqual(len({stats.item_key(item) for item in sample}), 8)
        self.assertNotEqual(sample, stats.canonical_sample(keys, 'upper', -36, 8))

    def test_layered_token_accounting_and_per_certificate_sets(self):
        root, graph = diamond()
        items = [dict(position=generate6.encode_state(s)[1:],
                      turn='black' if s.turn == ref.BLACK else 'white',
                      direction='lower', threshold=-36, leaf=kind == 'leaf',
                      selected_index=-1) for s, (kind, _) in graph.items()]
        data = native(items)
        data['tree_nodes_S'] = shared6.expanded_size(graph, root)
        data['frontier_distinct_L'] = 1
        with patch.object(stats.shared6, 'graph_from_native', return_value=graph):
            result, exact, canonical = stats.certificate_stats(data, root, 'lower', -36, 100, 100)
        self.assertEqual(result['tree_checked_tokens'], 9)
        self.assertEqual(result['checked_tokens'], 8)
        self.assertEqual(result['citations'], 2)
        self.assertEqual(result['token_reduction'], 1)
        self.assertEqual(len(exact), 6)
        self.assertEqual(result['canonical_full_state_classes'], len(canonical))
        tree_entries, tree_stats = shared6.layered(graph, root, 10**9)
        self.assertEqual(sum(c in 'LCFPSK' for _, body in tree_entries for c in body), 9)
        self.assertEqual(tree_stats['checked_tokens'], result['tree_checked_tokens'])
        data['tree_nodes_S'] += 1
        with patch.object(stats.shared6, 'graph_from_native', return_value=graph):
            with self.assertRaisesRegex(ValueError, 'differs'):
                stats.certificate_stats(data, root, 'lower', -36, 100, 100)

    def test_stream_opening_counts_including_leaves_without_successors(self):
        data = native()
        original = bench6.decode('b002002000222222222022111001110001000')
        # Two orientations form one class; the opposite turn is another class.
        keys = [generate6.encode_state(original), stats.transform_key(generate6.encode_state(original), 1)]
        keys.append('w'+keys[0][1:])
        data = native([dict(position=k[1:], turn='black' if k[0] == 'b' else 'white',
                            direction='lower', threshold=-36, leaf=True, selected_index=-1) for k in keys])
        data['frontier_discs'] = 0
        # Force JSON records over multiple stream chunks without expanding states.
        data['padding'] = 'x'*70000
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, output, sample = root/'native.json', root/'stats.json', root/'sample.json'
            source.write_text(json.dumps(data))
            args = argparse.Namespace(input=source, output=output, sample_output=sample,
                                      max_input_bytes=1000000, max_states=10, max_samples=2)
            with patch.object(ref, 'successors', side_effect=AssertionError('scalar replay forbidden')):
                result = stats.opening(args)
            self.assertEqual(result['status'], 'complete')
            self.assertEqual(result['exact_full_states'], 3)
            self.assertEqual(result['canonical_full_state_classes'], 2)
            self.assertEqual(result['exact_frontier_full_states'], 3)
            self.assertEqual(result['canonical_frontier_full_state_classes'], 2)
            saved = json.loads(sample.read_text())
            self.assertEqual(saved['format'], 'canonical-frontier-work6-untrusted-v1')
            self.assertEqual(saved['population_L'], 2)
            self.assertEqual(saved['raw_frontier_distinct_L'], 3)
            self.assertEqual(saved['records'], [])
            self.assertEqual(saved['seed'], 2026100604)
            self.assertNotIn('summary', saved)

    def test_profile_per_certificate_sum_union_and_canonical_union(self):
        roots = [ref.initial(6), stats.transform(ref.initial(6), 1)]
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            cases = []
            for i, root in enumerate(roots):
                children = ref.successors(root)
                states = [dict(position=generate6.encode_state(s)[1:],
                               turn='black' if s.turn == ref.BLACK else 'white',
                               direction='lower', threshold=-36, leaf=s != root,
                               selected_index=-1) for s in [root, *children]]
                data = native(states)
                data.update(frontier_discs=5, frontier_distinct_L=len(children))
                path = folder/f'native-{i}.json'
                path.write_text(json.dumps(data))
                cases.append(dict(status='complete', direction='lower', frontier_discs=5,
                                  row=dict(id=f'l{i:03d}', value=-36,
                                           state=generate6.encode_state(root)),
                                  native_path=f'/old/desktop/location/{path.name}'))
            source = folder/'profile.json'
            source.write_text(json.dumps({'cases': cases}))
            args = argparse.Namespace(input=source, output=folder/'stats.json',
                                      max_input_bytes=100000, max_states=100,
                                      max_samples=2, max_tree_tokens=100)
            report = stats.profiles(args)
            group = report['groups'][0]
            exact = {generate6.encode_state(s) for root in roots for s in [root, *ref.successors(root)]}
            canonical = {stats.canonical_key(key)[0] for key in exact}
            self.assertEqual(report['status'], 'complete')
            self.assertEqual(group['sum_per_certificate_exact_full_states'], 10)
            self.assertEqual(group['exact_union_full_states'], len(exact))
            self.assertEqual(group['canonical_union_full_state_classes'], len(canonical))
            self.assertEqual(group['sum_tree_checked_tokens'], 10)
            self.assertEqual(group['sum_layered_checked_tokens'], 10)
            self.assertEqual(len(group['cases']), 2)
            source.write_text(json.dumps({'cases': [cases[0], cases[0]]}))
            with self.assertRaisesRegex(ValueError, 'duplicate profile case'):
                stats.profiles(args)

    def test_reject_corrupt_native_inputs_and_preserve_failure_progress(self):
        changes = [('complete', False), ('root_holds', False), ('root_validated', False),
                   ('count_overflow', True), ('oracle_aborted', True),
                   ('tree_count_kind', 'lower-bound'), ('unique_dag_nodes', 7),
                   ('frontier_distinct_L', 7), ('tree_nodes_S', True), ('threshold', True)]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = argparse.Namespace(input=root/'input.json', output=root/'stats.json',
                                      sample_output=None, max_input_bytes=100000,
                                      max_states=20, max_samples=3)
            for name, value in changes:
                data = native()
                data[name] = value
                args.input.write_text(json.dumps(data))
                with self.subTest(name=name), self.assertRaises(ValueError):
                    stats.opening(args)
                self.assertEqual(json.loads(args.output.read_text())['status'], 'failure')
            data = native()
            data['states'][1] = copy.deepcopy(data['states'][0])
            args.input.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                stats.opening(args)
            args.input.write_text('{"complete":true,"complete":true}')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                stats.read_native(args.input, lambda _: None)
            args.input.write_text(json.dumps(native())+'garbage')
            with self.assertRaisesRegex(ValueError, 'trailing'):
                stats.read_native(args.input, lambda _: None)
            args.input.write_text(json.dumps(native()))
            with self.assertRaisesRegex(ValueError, 'state cap'):
                stats.read_native(args.input, lambda _: None, max_states=2)
            with self.assertRaisesRegex(ValueError, 'byte cap'):
                stats.read_native(args.input, lambda _: None, max_bytes=10)

    def test_invalid_states_and_limits(self):
        for key in ('b'+'0'*35, 'x'+'0'*36, 'b'+'3'*36):
            with self.assertRaises(ValueError):
                stats.canonical_key(key)
        with self.assertRaises(ValueError):
            stats.transform(ref.initial(4), 0)
        with self.assertRaises(ValueError):
            stats.transform(ref.initial(6), -1)
        with self.assertRaises(ValueError):
            stats.canonical_sample(set(), 'lower', -36, 0)


if __name__ == '__main__':
    unittest.main()
