#!/usr/bin/env python3
"""Small independent fixtures; no native process or kernel launch."""
import copy
import unittest
import census_pilot6 as pilot
import ref
import shared6


def fixture(root, direction='lower'):
    rows, sizes = {}, {}
    def build(actual):
        s = pilot.ccanonical(actual)
        if s in rows: return sizes[s]
        children = ref.successors(s)
        row = dict(position=''.join(map(str,s.cells)), turn='black' if s.turn == ref.BLACK else 'white',
                   direction=direction, threshold=4, leaf=not children, selected_index=0)
        rows[s] = row
        if children and ref.placements(s) and s.turn == shared6.forcing_player(direction):
            holds = lambda t: ref.value(t) >= 4 if direction == 'lower' else ref.value(t) <= 4
            i = next(i for i,t in enumerate(children) if holds(t))
            row['selected_index'] = i; children = (children[i],)
        sizes[s] = 1 + sum(build(t) for t in children)
        return sizes[s]
    count = build(root)
    return dict(root_position=''.join(map(str,root.cells)), root_turn='black' if root.turn == 1 else 'white',
        direction=direction, threshold=4, complete=True, root_validated=True, root_holds=True,
        frontier_discs=36, tree_nodes_S=count, unique_dag_nodes=len(rows), states=list(rows.values()))


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.root = pilot.state('021222'+'222222'+'021222'+'222222'*3, 'black')
        self.sample = fixture(self.root)

    def test_correct_scalar_graph_and_transport(self):
        root, graph = pilot.validate_sample(self.sample)
        sources, jobs, stats = pilot.root_sources(graph, root, 'lower', 3, 32000, 150)
        self.assertGreater(stats['checked_tokens'], 0)
        self.assertEqual(jobs[-1]['kind'], 'assembly')
        for text in sources.values():
            self.assertIn('module Tests.CensusPilot6.Root3.', text)
            self.assertIn('private\n  open import Prelude', text)
            self.assertIn('--save-metas --safe --without-K --cubical-compatible', text)
            self.assertIn('-WnoRewritesNothing', text)
            self.assertNotIn('Tests.GlobalPilot6', text)
            self.assertNotIn('postulate', text)
        part = next(t for n,t in sources.items() if n.endswith('Part0.agda'))
        self.assertIn('\nexport :', part)
        self.assertNotIn('\nabstract\n  export :', part)
        self.assertIn('Guarantees (Rules.game six) white (lowerGoal 4)', sources[jobs[-1]['path']])

    def test_invalid_index(self):
        # White has an actual forcing choice on this board.
        sample = fixture(pilot.state('012222'+'222222'+'012222'+'222222'*3, 'white'))
        choice = next(r for r in sample['states'] if not r['leaf'] and
                      ref.placements(pilot.state(r['position'],r['turn'])) and r['turn']=='white')
        choice['selected_index'] = 999
        with self.assertRaisesRegex(ValueError, 'selected index'): pilot.validate_sample(sample)
        choice['selected_index'] = True
        with self.assertRaisesRegex(ValueError, 'selected index'): pilot.validate_sample(sample)

    def test_full_graph_split_replays(self):
        root, graph = pilot.validate_sample(self.sample)
        forced = {s for s in graph if graph[s][0] != 'leaf'}
        entries, _, stats = pilot.shared.layered_many(graph, [root], forced)
        self.assertTrue(pilot.shared.replay_many(entries, [root], 'lower', 4))
        self.assertGreaterEqual(stats['entries'], len(forced))
        sources, jobs, _ = pilot.root_sources(graph, root, 'lower', 0, 32000, 1, forced)
        self.assertTrue(any(t.get('dependencies') for t in jobs))
        for t in jobs:
            self.assertGreaterEqual(t['transitive_entries'], 0)

    def test_missing_opponent_reply(self):
        sample = copy.deepcopy(self.sample)
        self.assertGreater(len(ref.successors(pilot.ccanonical(self.root))), 1)
        sample['states'].pop()
        with self.assertRaisesRegex(ValueError, 'missing opponent reply'): pilot.validate_sample(sample)

    def test_wrong_terminal_bound(self):
        sample = fixture(pilot.state('1'*36, 'black'))
        with self.assertRaisesRegex(ValueError, 'terminal bound'): pilot.validate_sample(sample)

    def test_duplicate_missing_and_counters(self):
        sample = copy.deepcopy(self.sample); sample['states'].append(sample['states'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate'): pilot.validate_sample(sample)
        sample = copy.deepcopy(self.sample); sample['states'] = []
        with self.assertRaisesRegex(ValueError, 'missing rows'): pilot.validate_sample(sample)
        for key in ('unique_dag_nodes','tree_nodes_S'):
            sample = copy.deepcopy(self.sample); sample[key] += 1
            with self.assertRaisesRegex(ValueError, 'dishonest'): pilot.validate_sample(sample)

    def test_unreachable_row(self):
        sample = copy.deepcopy(self.sample)
        extra = fixture(pilot.state('2'*36,'black'))['states'][0]
        sample['states'].append(extra)
        with self.assertRaisesRegex(ValueError, 'unreachable'): pilot.validate_sample(sample)

    def test_partition_cap_and_no_forward_reference(self):
        with self.assertRaisesRegex(ValueError, 'token cap'):
            pilot.assembly.partition([dict(state='b'+'2'*36,certificate='P'+'L',references=[])], 1, 150)
        with self.assertRaisesRegex(ValueError, 'forward'):
            pilot.assembly.partition([dict(state='b'+'2'*36,certificate='K',references=['w'+'2'*36])])

    def test_noncanonical_and_direction(self):
        sample = copy.deepcopy(self.sample); sample['states'][0]['direction']='upper'
        with self.assertRaisesRegex(ValueError, 'direction'): pilot.validate_sample(sample)
        sample = copy.deepcopy(self.sample); sample['complete']=False
        with self.assertRaisesRegex(ValueError, 'incomplete'): pilot.validate_sample(sample)


if __name__ == '__main__': unittest.main()
