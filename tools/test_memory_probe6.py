"""Meaningful guards for staging real proofs without importing assumptions."""
import unittest

import global_assembly6 as assembly
import memory_probe6 as probe


class MemoryProbeTests(unittest.TestCase):
    def setUp(self):
        self.root = 'b' + '0' * 36

    def test_part_stages_preserve_checking_boundaries(self):
        part = [{'state': self.root, 'certificate': 'L', 'references': []}]
        source, _, _ = assembly.part_source(0, part, {self.root: 0}, 'upper')
        phases = probe.part_phases(source, 0)
        self.assertNotIn('imports :', phases['dependencies'])
        self.assertNotIn('abstract', phases['states'])
        self.assertIn('entries = fromMaybe', phases['decode'])
        self.assertNotIn('shape :', phases['decode'])
        self.assertIn('shape = refl', phases['shape'])
        self.assertNotIn('accepted :', phases['shape'])
        self.assertIn('accepted = refl', phases['check'])
        self.assertNotIn('sound :', phases['check'])
        self.assertIn('shardBy-sound', phases['sound'])
        # The original failed source additionally had a decoder roundtrip
        # equality. Both layouts retain that proof before the shape stage.
        old = source.replace('  shape :',
            '  decoded : decodeCompactEntries "x" ≡ just entries\n'
            '  decoded = refl\n\n  shape :', 1)
        self.assertIn('decoded = refl', probe.part_phases(old, 0)['decode'])
        with self.assertRaises(ValueError):
            probe.part_phases(source, 1)

    def test_guarantees_use_checked_pair_and_original_rules(self):
        owners = {self.root: 2}
        source = probe.root_source([self.root], owners, 'upper', 'rules')
        self.assertIn('accepted0 = refl', source)
        self.assertIn('knownIn-sound', source)
        self.assertIn('P2.sound accepted0', source)
        self.assertIn('(proj₁ proven0) (proj₂ proven0)', source)
        self.assertIn('Guarantees (Rules.game six)', source)
        self.assertIn('fastAgreement fastGuarantee0', source)
        self.assertNotIn(' with ', source)
        self.assertNotIn('postulate', source)

    def test_invalid_roots_or_stage_rejected(self):
        owners = {self.root: 0}
        for roots, direction, stage in [([], 'upper', 'rules'),
                ([self.root, self.root], 'upper', 'rules'),
                (['w' + '0' * 36], 'upper', 'rules'),
                ([self.root], 'draw', 'rules'), ([self.root], 'upper', 'assume')]:
            with self.assertRaises(ValueError):
                probe.root_source(roots, owners, direction, stage)
        with self.assertRaises(ValueError):
            probe.module_source('../Unsafe', '')

    def test_rts_stats_do_not_confuse_allocation_and_residency(self):
        log = '1,234,567 bytes allocated in the heap\n12,345 bytes copied during GC\n' \
              '4,567 bytes maximum residency (2 sample(s))\n44 MiB total memory in use\n'
        self.assertEqual(probe.rts_stats(log), {'allocated_bytes': 1234567,
                         'copied_bytes': 12345, 'maximum_residency_bytes': 4567,
                         'total_memory_in_use': 44, 'total_memory_unit': 'MiB'})
        self.assertEqual(probe.rts_stats('agda: Heap exhausted'), {})


if __name__ == '__main__':
    unittest.main()
