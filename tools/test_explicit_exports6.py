"""Explicit arguments must preserve both certificate proof obligations."""
import unittest

import global_assembly6 as assembly
from explicit_exports6 import explicit_source, packed_source


class ExplicitExportTests(unittest.TestCase):
    def original(self):
        state = 'b' + '1'*36
        part = [{'state':state, 'certificate':'L', 'references':[]}]
        text,_,_ = assembly.part_source(25,part,{state:25},'upper')
        return text.replace(assembly.PREFIX,'Tests.Unattended6.Group6').replace(
            '--safe ', '--save-metas --safe ',1)

    def test_witnesses_and_state_data_are_preserved(self):
        original = self.original()
        explicit = explicit_source(original)
        for first,last in [('states :','abstract'), ('  entries :','  shape :')]:
            self.assertEqual(original.split(first,1)[1].split(last,1)[0],
                             explicit.split(first,1)[1].split(last,1)[0])
        self.assertIn('  shape = refl {x = states}',explicit)
        self.assertIn('  accepted = refl {x = true}',explicit)
        self.assertIn('shardBy-sound',explicit)
        self.assertIn('shardStates keyed6 entries',explicit)
        self.assertIn('--save-metas --safe --without-K --cubical-compatible',explicit)

    def test_changed_or_wrong_bound_template_is_rejected(self):
        original = self.original()
        for changed in (original.replace('  shape = refl\n',''),
                        original.replace('upperGoal 4','upperGoal 3'),
                        original.replace('Group6.Part25','Group6.Part24')):
            with self.assertRaises(ValueError):
                explicit_source(changed)

    def test_packed_routes_preserve_exact_state_order_and_certificate(self):
        state,reference = 'b'+'1'*36, 'w'+'2'*36
        part = [{'state':state,'certificate':'L','references':[reference]}]
        original,_,_ = assembly.part_source(25,part,{state:25,reference:0},'upper')
        original = original.replace(assembly.PREFIX,'Tests.Unattended6.Group6').replace(
            '--safe ', '--save-metas --safe ',1)
        packed = packed_source(original)
        self.assertIn('selectExport (importKeys "wQQQQQQQQQQQQL") P0.export',packed)
        self.assertIn('states = shardStates keyed6 (fromMaybe [] (decodeCompactEntries "bDDDDDDDDDDDDL"))',packed)
        self.assertEqual(original.split('  entries :',1)[1].split('  shape :',1)[0],
                         packed.split('  entries :',1)[1].split('  shape :',1)[0])
        self.assertIn('shardBy-sound',packed)
        with self.assertRaises(ValueError):
            packed_source(original.replace('(decode "wQQQQQQQQQQQQ")','(decode "invalid")'))


if __name__ == '__main__':
    unittest.main()
