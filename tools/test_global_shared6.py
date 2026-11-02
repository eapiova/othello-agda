"""AI-assisted rejection and transport tests for the multi-root graph pilot."""
import copy
import unittest

import bench6
import generate6
import global_shared6 as global_graph
import ref
import shared6
import shared_symmetry6 as single
import symmetry_stats6 as symmetry
from test_shared6 import LINE10


class GlobalGraphTests(unittest.TestCase):
    def test_multi_root_reuses_transformed_goal(self):
        root=generate6.replay()[0][30]
        raw=shared6.graph_from_search(root,'lower',4)
        normalized=single.normalize(raw)
        rotated=symmetry.transform(root,1)
        entries,refs,stats=global_graph.layered_many(normalized,[root,rotated])
        self.assertTrue(global_graph.replay_many(entries,[root,rotated],'lower',4))
        self.assertEqual(stats['roots'],2)
        self.assertGreater(stats['nonidentity_citations'],0)
        owners={}
        for i,(state,_) in enumerate(entries):
            self.assertTrue(refs[state] <= owners.keys())
            owners[state]=i
        self.assertFalse(global_graph.replay_many(entries,[ref.initial(6)],'lower',4))

    def test_move_indices_and_all_replies_survive_union(self):
        root=bench6.decode(LINE10)
        raw=shared6.graph_from_search(root,'lower',4)
        canonical=single.normalize(raw)
        children=canonical[symmetry.canonical(root)[0]][1]
        roots=[root,children[0]]
        entries,_,_=global_graph.layered_many(canonical,roots)
        self.assertTrue(global_graph.replay_many(entries,roots,'lower',4))
        fork=next(s for s,(k,cs) in canonical.items() if k=='fork' and len(cs)>1)
        broken=copy.deepcopy(canonical)
        broken[fork][1].pop()
        with self.assertRaises(ValueError):
            single.validate_graph(broken,symmetry.canonical(root)[0],'lower',4)
        # A wrong branch count is rejected by the replay, not trusted metadata.
        for state,text in entries:
            if 'F2;' in text:
                damaged=[(s,t.replace('F2;','F1;',1) if s==state else t) for s,t in entries]
                self.assertFalse(global_graph.replay_many(damaged,roots,'lower',4))
                break
        else:
            self.fail('fixture needs a two-reply fork')

    def test_missing_future_and_bad_tag(self):
        root=generate6.replay()[0][-1]
        canonical,tag=symmetry.canonical(root)
        self.assertFalse(global_graph.replay_many([(root,'R8;')],[root],'lower',4))
        self.assertFalse(global_graph.replay_many([(root,f'R{tag};'),(canonical,'L')],[root],'lower',4))
        self.assertFalse(global_graph.replay_many([(root,'K')],[root],'lower',4))

    def test_selection_preserves_metadata_and_rejects_mixed_bound(self):
        states=generate6.replay()[0]
        keys=sorted({symmetry.canonical(s)[0] for s in states[-10:]},key=generate6.encode_state)
        cases=[dict(direction='upper',frontier_discs=36,status='complete',
                    row={'state':generate6.encode_state(s),'value':4}) for s in keys]
        profile={'sample_population_kind':'canonical frontier full-state classes','cases':cases}
        selected=global_graph.select_cases(profile,3,91,'upper')
        self.assertEqual(selected,global_graph.select_cases(profile,3,91,'upper'))
        self.assertEqual(len(selected),3)
        bad=copy.deepcopy(profile);bad['cases'][0]['row']['value']=3
        with self.assertRaises(ValueError):global_graph.select_cases(bad,3,91,'upper')
        bad=copy.deepcopy(profile);bad['cases'][0]['status']='leaf-work-capped'
        with self.assertRaises(ValueError):global_graph.select_cases(bad,3,91,'upper')


if __name__=='__main__':unittest.main()
