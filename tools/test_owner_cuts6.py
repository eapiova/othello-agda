"""The generator cannot silently discard, duplicate or invent citation owners."""
import tempfile
from pathlib import Path
import unittest

import compact_shared6 as compact
import owner_cuts6 as cuts
import owner_split6 as split
import test_owner_split6 as split_tests


class OwnerCutsTests(unittest.TestCase):
    def test_partition_has_disjoint_complete_prefixes(self):
        states = {}
        for i in range(513):
            digits, n = [], i
            for _ in range(6):
                digits.append(str(n % 3))
                n //= 3
            state = ('w' if i % 2 else 'b') + ''.join(digits) + '0'*30
            states[state] = 'E0.export'
        leaves, nodes = cuts.cuts(states)
        flattened = [s for group in leaves.values() for s in group]
        self.assertEqual(set(flattened), set(states))
        self.assertEqual(len(flattened), len(states))
        for path, group in leaves.items():
            self.assertLessEqual(len(group), cuts.MAX_STATES)
            self.assertTrue(all(cuts.key_bits(s).startswith(path) for s in group))
            self.assertFalse(any(other != path and other.startswith(path) for other in leaves))
        self.assertTrue(nodes)

    def test_key_matches_the_full_player_and_every_cell(self):
        state = 'w' + '012'*12
        self.assertEqual(cuts.key_bits(state), '1'+'000110'*12)
        self.assertEqual(len(cuts.key_bits(state)), 73)
        with self.assertRaises(ValueError):
            cuts.key_bits('b'+'0'*35+'3')

    def test_bad_wires_and_duplicate_states_are_rejected(self):
        original = split.split_sources(split_tests.OwnerSplitTests().source())[split.DIRECTORY+'/Assemble6Split2.agda']
        self.assertEqual(len(cuts.routing(original)), 1)
        with self.assertRaises(ValueError):
            cuts.routing(original.replace('routesFor 0 "', 'routesFor 1 "'))
        state = next(iter(cuts.routing(original)))
        wire = compact.pack_state(state)+'L'
        with self.assertRaises(ValueError):
            cuts.routing(original.replace(wire, wire+wire))

    def test_proofs_use_actual_imports_owners_and_both_children(self):
        original = split.split_sources(split_tests.OwnerSplitTests().source())[split.DIRECTORY+'/Assemble6Split2.agda']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root/split.DIRECTORY
            directory.mkdir(parents=True)
            (directory/'Assemble6Split2.agda').write_text(original)
            (directory/'Check.agda').write_text('module '+split.NAMESPACE+'.Check where\nimport '+split.NAMESPACE+'.Assemble6 as A\n')
            sources, _, summary = cuts.generated(root)
        leaf = next(text for name, text in sources.items() if '/Cut' in name)
        self.assertIn('target = subT prefix I26.imports', leaf)
        self.assertIn('sources = S25.P25.export ∷ []', leaf)
        self.assertIn('association : tables ≡ trees sources', leaf)
        self.assertIn('sources tables hints target association accepted', leaf)
        self.assertIn('sound = I26.sound (C0.sound)', sources[cuts.DIRECTORY+'/Binding.agda'])
        self.assertEqual(summary['citation_states'], 1)
        helper = cuts.helper_source()
        self.assertIn('AllM P (valueT t) → AllT P (leftT t) → AllT P (rightT t)', helper)
        self.assertIn('pm , (pl , pr)', helper)
        self.assertNotIn('postulate', helper)

    def test_negative_guard_accepts_wrapped_declarations_only_for_the_expected_error(self):
        record = {'exit_code': 42, 'stop_reason': None}
        log = 'incorrect\n  = joinAll\nerror: [UnequalTerms]\nAllM (λ b → b ≡ true) (just false)'
        self.assertTrue(cuts.rejected_omission(record, log, {}))
        self.assertFalse(cuts.rejected_omission(record, log.replace('UnequalTerms', 'AmbiguousName'), {}))
        self.assertFalse(cuts.rejected_omission(record, log, {'unexpected.agdai': 'hash'}))
        self.assertFalse(cuts.rejected_omission({**record, 'stop_reason': 'cpu-limit'}, log, {}))


if __name__ == '__main__':
    unittest.main()
