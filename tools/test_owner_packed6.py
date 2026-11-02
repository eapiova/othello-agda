"""Opaque assembly must retain its accepted prefix and the complete literal input."""
from pathlib import Path
import tempfile
import unittest

import independent_lower6 as independent
import owner_cuts6 as cuts
import owner_packed6 as packed
import owner_split6 as split
import test_owner_split6 as split_tests


class OwnerPackedTests(unittest.TestCase):
    def generate(self):
        original = split.split_sources(split_tests.OwnerSplitTests().source())[split.DIRECTORY+'/Assemble6Split2.agda']
        previous = independent.state_wire(sorted(cuts.routing(original)))
        states = ['w'+str(i % 3)+str((i//3) % 3)+str((i//9) % 3)+str((i//27) % 3)+'0'*32 for i in range(80)]
        wire = independent.state_wire(sorted(states))
        original = original.replace(previous, wire)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root/split.DIRECTORY
            directory.mkdir(parents=True)
            (directory/'Assemble6Split2.agda').write_text(original)
            (directory/'Check.agda').write_text('module '+split.NAMESPACE+'.Check where\nimport '+split.NAMESPACE+'.Assemble6 as A\n')
            (directory/'Part26.agda').write_text('imports : Trie (State six)\nimports = shardStates keyed6 (fromMaybe [] (decodeCompactEntries "'+wire+'"))\n')
            return packed.generated(root)

    def test_the_eight_accepted_entries_are_not_checked_again(self):
        sources, phases, summary = self.generate()
        self.assertNotIn(packed.DIRECTORY+'/Data0.agda', sources)
        self.assertNotIn(packed.DIRECTORY+'/Proof0.agda', sources)
        self.assertEqual(summary['segments'][0], {'index': 0, 'start': 0, 'width': 8, 'states': 8, 'reused': True})
        self.assertEqual(sum(row['states'] for row in summary['segments']), 80)
        self.assertIn('rows = takeL 64 (dropL 8 I.entries)', sources[packed.DIRECTORY+'/Data1.agda'])
        self.assertNotIn(('Data0', 60, False), phases)

    def test_final_assembly_requires_all_inputs_and_the_original_conditional_proof(self):
        sources, _, _ = self.generate()
        source = sources[packed.DIRECTORY+'/Binding.agda']
        self.assertIn('import Tests.OwnerOpaque6.Proof0 as P0', source)
        self.assertIn('inputShape : I26.imports ≡ shardStates keyed6 I.entries', source)
        self.assertIn('I26.imports I26.states inputShape I26.sound tail0', source)
        self.assertIn('finished : dropL 136 I.entries ≡ []', source)
        self.assertIn('tail0 = joinCitations Fast.fastGame6 white (lowerGoal 4) 8', source)
        self.assertNotIn('postulate', packed.closure_source())


if __name__ == '__main__':
    unittest.main()
