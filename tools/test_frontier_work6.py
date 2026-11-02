#!/usr/bin/env python3
"""Small mocked sampler checks; no native builds or Agda compilation."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import frontier_work6 as work
import ref
import solve6


def graph():
    states = []
    for i in range(8):
        position = '1' * i + '2' * (36-i)
        states.append(dict(position=position, turn='black', direction='lower',
                           threshold=-36, leaf=True, selected_index=-1))
    return dict(complete=True, root_validated=True, root_holds=True,
                count_overflow=False, oracle_aborted=False, tree_count_kind='exact',
                direction='lower', threshold=-36, frontier_discs=30,
                unique_dag_nodes=8, frontier_distinct_L=8, tree_nodes_S=8,
                hint_occurrences_H=0, cpu_seconds=1.25, states=states,
                build_metadata={'source_sha256': 'original-source', 'binary_sha256': 'original-binary'})


def mirror(item, nodes=100):
    return dict(holds=True, noTT=True, order='row-major', fuel=80,
                direction=item['direction'], threshold=item['threshold'],
                nodes=nodes, cpu_seconds=0.002)


class SamplerTests(unittest.TestCase):
    def test_reject_incomplete_overflow_unvalidated(self):
        for name, value in [('complete', False), ('root_validated', False),
                            ('root_holds', False), ('count_overflow', True),
                            ('oracle_aborted', True), ('tree_count_kind', 'lower-bound')]:
            g = graph(); g[name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                work.validate_graph(g)

    def test_bad_duplicate_mismatched_leaves_counts(self):
        changes = [('position', '0' * 35), ('position', 'x' * 36),
                   ('turn', 'purple'), ('direction', 'upper'), ('threshold', -35),
                   ('threshold', True), ('leaf', 1), ('selected_index', 0),
                   ('extra', 'bad')]
        for field, value in changes:
            g = graph(); g['states'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                work.validate_graph(g)
        g = graph(); g['states'][1] = copy.deepcopy(g['states'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            work.validate_graph(g)
        for field, value in [('frontier_distinct_L', 7), ('unique_dag_nodes', 9),
                             ('tree_nodes_S', True), ('hint_occurrences_H', -1)]:
            g = graph(); g[field] = value
            with self.assertRaises(ValueError): work.validate_graph(g)

    def test_semantic_leaf_markers(self):
        g = graph(); g['states'][0]['leaf'] = False
        with self.assertRaisesRegex(ValueError, 'nonleaf'): work.validate_graph(g)
        g = graph(); g['states'][0]['position'] = solve6.position012(ref.initial(6))
        with self.assertRaisesRegex(ValueError, 'nonterminal leaf'): work.validate_graph(g)
        g = graph(); g['frontier_discs'] = 36
        g['states'][0].update(position='1'*35+'0', leaf=False)
        with self.assertRaisesRegex(ValueError, 'terminal marked nonleaf'): work.validate_graph(g)

    def test_selection_uniform_without_replacement_deterministic(self):
        leaves = work.validate_graph(graph())
        first = work.select(leaves, 5, 13)
        self.assertEqual(first, work.select(leaves, 5, 13))
        self.assertNotEqual(first, work.select(leaves, 5, 14))
        self.assertEqual(len({s['position'] for s in first}), 5)
        self.assertEqual(len(work.select(leaves, 20, 13)), 8)
        with self.assertRaises(ValueError): work.select(leaves, 0, 13)

    def test_timeout_failure_false_holds_never_zero_work(self):
        item = graph()['states'][0]
        responses = [subprocess.TimeoutExpired(['mirror'], 0.1), RuntimeError('failed'),
                     {**mirror(item), 'holds': False}, {**mirror(item), 'noTT': False}]
        for response in responses:
            kwargs = {'side_effect': response} if isinstance(response, Exception) else {'return_value': response}
            with patch.object(work.solve6, 'query', **kwargs): result = work.measure(item, 0.1)
            self.assertIsNone(result['W'])
            self.assertTrue(result['censored'])
            self.assertIn(result['status'], ('timeout', 'failure'))
            self.assertGreaterEqual(result['wall_seconds'], 0)
            summary = work.estimates([result], 8, 1)
            self.assertNotIn('statistical_estimated_distinct_leaf_total_W', summary)
            self.assertFalse(summary['uncensored'])

    def test_completed_literal_call_and_estimates_labelled(self):
        item = graph()['states'][0]
        with patch.object(work.solve6, 'query', return_value=mirror(item, 123)) as query:
            record = work.measure(item, 0.2)
        query.assert_called_once_with('mirror', work.scalar(item), direction='lower',
                                      threshold=-36, fuel=80, timeout=0.2)
        self.assertEqual(record['W'], 123)
        self.assertEqual(record['native_record']['cpu_seconds'], 0.002)
        summary = work.estimates([record], 8, 1)
        self.assertEqual(summary['statistical_estimated_distinct_leaf_total_W'], 984)
        self.assertIn('statistical', summary['kind'])
        self.assertIn('never exact', summary['kind'])
        self.assertEqual(summary['recommendation'].split(';')[0], 'none')

    def test_bounded_reader_sample_only_resume_and_retained_metadata(self):
        with tempfile.TemporaryDirectory(dir=solve6.ROOT/'results') as directory:
            source, output = Path(directory)/'graph.json', Path(directory)/'sample.json'
            source.write_text(json.dumps(graph()))
            with self.assertRaises(ValueError): work.read_graph(source, max_bytes=10)
            with self.assertRaises(ValueError): work.read_graph(source, max_states=2)
            with patch.object(work.solve6, 'query', side_effect=AssertionError('no subprocess')):
                work.run(source, output, samples=2, seed=7, sample_only=True)
            saved = json.loads(output.read_text())
            self.assertEqual(saved['graph_metadata']['cpu_seconds'], 1.25)
            self.assertEqual(saved['graph_metadata']['build_metadata'], graph()['build_metadata'])
            self.assertEqual(saved['records'], [])
            self.assertEqual(len(saved['sampled_states']), 2)
            self.assertEqual(saved['input_sha256'], solve6.sha256(source))
            with patch.object(work.solve6, 'query', side_effect=[
                    mirror(saved['sampled_states'][0]), subprocess.TimeoutExpired(['mirror'], 0.1)]) as query:
                work.run(source, output, samples=2, seed=7)
                self.assertEqual(query.call_count, 2)
            saved = json.loads(output.read_text())
            self.assertEqual([r['status'] for r in saved['records']], ['complete', 'timeout'])
            self.assertNotIn('statistical_estimated_distinct_leaf_total_W', saved['summary'])
            with patch.object(work.solve6, 'query', side_effect=AssertionError('retained results')):
                work.run(source, output, samples=2, seed=7)
            with self.assertRaisesRegex(ValueError, 'configuration mismatch'):
                work.run(source, output, samples=2, seed=8)
            source.write_text('{"complete":true,"complete":false}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'): work.read_graph(source)


if __name__ == '__main__':
    unittest.main()
