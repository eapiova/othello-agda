"""A list proof must discharge the literal actually used by the certificate."""
from pathlib import Path
import tempfile
import unittest

import independent_lower6 as independent
import owner_lists6 as lists
import owner_cuts6 as cuts
import owner_split6 as split
import test_owner_split6 as split_tests


class OwnerListsTests(unittest.TestCase):
    def generate(self, corrupt=False, **kwargs):
        original = split.split_sources(split_tests.OwnerSplitTests().source())[split.DIRECTORY+'/Assemble6Split2.agda']
        wire = independent.state_wire(sorted(cuts.routing(original)))
        if corrupt:
            wire = independent.state_wire(['w'+'0'*36])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root/split.DIRECTORY
            directory.mkdir(parents=True)
            (directory/'Assemble6Split2.agda').write_text(original)
            (directory/'Check.agda').write_text('module '+split.NAMESPACE+'.Check where\nimport '+split.NAMESPACE+'.Assemble6 as A\n')
            (directory/'Part26.agda').write_text('imports : Trie (State six)\nimports = shardStates keyed6 (fromMaybe [] (decodeCompactEntries "'+wire+'"))\n')
            return lists.generated(root, **kwargs)

    def test_different_accepted_import_literal_rejects_before_checking(self):
        with self.assertRaises(ValueError):
            self.generate(corrupt=True)

    def test_chunks_take_the_actual_input_and_complete_assembly_uses_it(self):
        sources, _, summary = self.generate()
        chunk = sources[lists.DIRECTORY+'/Chunk0.agda']
        self.assertIn('rows = takeL 64 (dropL 0 I.entries)', chunk)
        self.assertIn('sources tables hints rows association accepted', chunk)
        binding = sources[lists.DIRECTORY+'/Binding.agda']
        self.assertIn('tree-all keyed6 (Proven Fast.fastGame6 white (lowerGoal 4)) I.entries tail0', binding)
        self.assertIn('tail1 : AllL Goal (dropL 64 I.entries)', binding)
        self.assertIn('tail1 = tt', binding)
        self.assertEqual(summary['citation_states'], 1)
        self.assertFalse(summary['conditional_part_rechecked'])

    def test_generic_checker_rejects_unequal_list_lengths(self):
        source = lists.helper_source()
        self.assertIn('listKnown k ts [] (e ∷ es) = false', source)
        self.assertIn('listKnown k ts (i ∷ is) [] = false', source)
        self.assertIn('insert-all (key k s)', source)
        self.assertIn('drop-sum n (suc m) [] = drop-nil n', source)
        self.assertNotIn('postulate', source)

    def test_small_queries_reuse_the_accepted_helper_and_actual_input(self):
        sources, phases, _ = self.generate(namespace='Tests.OwnerQueries6',
            generated_directory='src/Tests/OwnerQueries6', batch_size=8, reuse_helpers=True)
        self.assertFalse(any(name.endswith('/Lookup.agda') or name.endswith('/Inputs.agda') for name in sources))
        self.assertEqual(phases[0][0], 'Chunk0')
        chunk = sources['src/Tests/OwnerQueries6/Chunk0.agda']
        self.assertIn('open import Tests.OwnerLists6.Lookup', chunk)
        self.assertIn('import Tests.OwnerLists6.Inputs as I', chunk)
        self.assertIn('rows = takeL 8 (dropL 0 I.entries)', chunk)


if __name__ == '__main__':
    unittest.main()
