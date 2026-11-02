"""Shard boundaries preserve the dependency order and selective imports."""
import unittest
from unittest.mock import patch

import ref
import shared_assembly6 as assembly


class AssemblyTests(unittest.TestCase):
    def states(self, count):
        return [ref.State(6, (0,)*i + (1,)*(36-i), ref.BLACK) for i in range(count)]

    def test_balances_entries_even_when_root_dominates_tokens(self):
        states = self.states(17)
        entries = [(s, 'L') for s in states[:-1]] + [(states[-1], 'P'*100+'L')]
        with patch.object(assembly, 'references', return_value=set()):
            parts, owners = assembly.partition(entries, {}, 8)
        self.assertGreaterEqual(len(parts), 6)
        self.assertEqual([s for part in parts for s,_,_ in part], states)
        self.assertTrue(all(owners[s] == i for i,p in enumerate(parts) for s,_,_ in p))

    def test_self_and_forward_citations_rejected(self):
        states = self.states(3)
        for target in [states[0], states[2]]:
            with patch.object(assembly, 'references', return_value={target}):
                with self.assertRaisesRegex(ValueError, 'self or forward'):
                    assembly.partition([(s, 'K') for s in states], {}, 2)

    def test_imports_only_keys_actually_cited_from_each_shard(self):
        a,b,c = self.states(3)
        source, dependencies = assembly.part_source(2, [(c, 'K', {b})],
                                                   {a:0,b:1,c:2}, 'lower')
        self.assertEqual(dependencies, [1])
        self.assertIn('selectExport', source)
        self.assertIn('P1.export', source)
        self.assertNotIn('P0.export', source)


if __name__ == '__main__': unittest.main()
