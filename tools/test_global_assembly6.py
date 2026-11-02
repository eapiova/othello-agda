"""AI-assisted acyclic shard/source tests for the global graph kernel harness."""
import copy
import unittest

import compact_shared6 as compact
import generate6
import global_assembly6 as assembly
import global_shared6 as global_graph
import shared6
import shared_symmetry6 as single


class GlobalAssemblyTests(unittest.TestCase):
    def setUp(self):
        root=generate6.replay()[0][30]
        graph=single.normalize(shared6.graph_from_search(root,'lower',4))
        entries,refs,_=global_graph.layered_many(graph,[root])
        self.plan=global_graph.encode_plan(entries,refs,[root],'lower')

    def test_partition_and_imports_are_acyclic(self):
        assembly.validate_plan(self.plan)
        parts,owners=assembly.partition(self.plan['entries'],max_tokens=100,max_entries=1)
        self.assertGreaterEqual(len(parts),2)
        for i,part in enumerate(parts):
            source,deps,_=assembly.part_source(i,part,owners,'lower')
            self.assertTrue(all(j<i for j in deps))
            self.assertIn('checkShardBy',source)
            self.assertIn('decodeCompactEntries',source)
            self.assertIn('shape = refl',source)
        roots=assembly.assembly_source(self.plan['roots'],owners,'lower')
        self.assertIn('guarantees-transfer',roots)
        self.assertIn('Guarantees (Rules.game six)',roots)

    def test_corrupt_import_manifest_is_rejected(self):
        bad=copy.deepcopy(self.plan)
        bad['entries'][0]['references']=[bad['entries'][0]['state']]
        with self.assertRaises(ValueError):assembly.validate_plan(bad)
        bad=copy.deepcopy(self.plan);bad['roots']=['b'+'0'*36]
        with self.assertRaises(ValueError):assembly.validate_plan(bad)

    def test_legacy_ab_uses_identical_states_and_imports(self):
        parts,owners=assembly.partition(self.plan['entries'],max_entries=1)
        compact_source,compact_deps,packed=assembly.part_source(1,parts[1],owners,'lower')
        old_source,old_deps,old=assembly.part_source(1,parts[1],owners,'lower','legacy','LegacyAB')
        self.assertEqual(compact_deps,old_deps)
        self.assertEqual(compact_source.split('states = ')[1].split('abstract')[0],
                         old_source.split('states = ')[1].split('abstract')[0])
        self.assertLess(packed,old)
        self.assertIn('decodeSharedEntries',old_source)

    def test_part_size_limit_is_a_hard_gate(self):
        with self.assertRaises(ValueError):
            assembly.partition(self.plan['entries'],max_tokens=1)


if __name__=='__main__':unittest.main()
