"""Guards against deleting actual checking obligations during decoder repair."""
import unittest

import global_assembly6 as assembly
import memory_repair6 as repair


class MemoryRepairTests(unittest.TestCase):
    def setUp(self):
        state = 'b' + '0' * 36
        part = [{'state': state, 'certificate': 'L', 'references': []}]
        self.new, _, _ = assembly.part_source(0, part, {state: 0}, 'upper')
        self.old = self.new.replace('  shape :',
            '  decoded : decodeCompactEntries "b000000000000L" ≡ just entries\n'
            '  decoded = refl\n\n  shape :', 1)

    def test_only_unused_decoder_equality_is_removed(self):
        self.assertEqual(repair.remove_unused_equality(self.old), self.new)
        for proof in ['shape = refl', 'accepted = refl', 'shardBy-sound',
                      'states = ', 'entries = fromMaybe']:
            self.assertIn(proof, repair.remove_unused_equality(self.old))

    def test_unknown_layout_or_missing_check_is_rejected(self):
        for source in [self.new, self.old.replace('  decoded = refl', '  decoded = other'),
                       self.old.replace('  accepted :', '  omitted :')]:
            with self.assertRaises(ValueError):
                repair.remove_unused_equality(source)

    def test_repaired_root_requires_proven_pair_and_original_rule_transfer(self):
        state = 'b' + '0' * 36
        source = assembly.assembly_source([state], {state: 0}, 'upper')
        self.assertIn('knownIn-sound', source)
        self.assertIn('P0.sound accepted0', source)
        self.assertIn('(proj₁ proven0) (proj₂ proven0)', source)
        self.assertIn('guarantees-transfer Fast.fastGame6 (Rules.game six)', source)
        self.assertNotIn('fastGuarantee0 with', source)

    def test_boolean_coverage_keeps_certificate_acceptance_and_soundness(self):
        state = 'b' + '0' * 36
        part = [{'state': state, 'certificate': 'L', 'references': []}]
        covered, _, _ = assembly.part_source(0, part, {state: 0}, 'upper', export_mode='coverage')
        self.assertIn('coverage = refl', covered)
        self.assertIn('accepted = refl', covered)
        self.assertIn('covered-sound', covered)
        self.assertIn('shardBy-sound', covered)
        self.assertNotIn('shape :', covered)
        self.assertNotIn('decoded :', covered)
        self.assertEqual(self.new.split('states = ')[1].split('abstract')[0],
                         covered.split('states = ')[1].split('abstract')[0])


if __name__ == '__main__':
    unittest.main()
