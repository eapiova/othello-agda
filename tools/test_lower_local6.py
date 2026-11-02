"""Check closure isolation, literal certificates, heldout and prefix guards."""
import copy
import unittest

import compact_shared6 as compact
from lower_local6 import generated_layout
from lower_local_plan6 import closure, describe
import lower_pilot6 as pilot
from test_lower_pilot6 import fixture


class LowerLocalTests(unittest.TestCase):
    def test_layout_uses_only_one_exact_root_closure(self):
        plan = fixture()
        terminal = 'b'+'1'*36
        plan['entries'].insert(0, dict(state=terminal, certificate='L', references=[]))
        plan['entries'][5].update(certificate='R0;', references=[terminal])
        original = copy.deepcopy(plan)
        layout = generated_layout(plan, 4)
        self.assertEqual(plan, original)
        self.assertEqual(layout['roots'], [plan['roots'][4]])
        self.assertEqual(layout['groups'][0]['entries'], 2)
        prefix = layout['directory']
        source = layout['sources'][prefix+'/Group0/Part0.agda']
        expected = compact.encode((entry['state'], entry['certificate']) for entry in
            closure(plan['entries'], [plan['roots'][4]]))
        self.assertIn('decodeCompactEntries "'+expected+'"', source)
        self.assertIn('shape = refl {x = states}', source)
        self.assertIn('accepted = refl {x = true}', source)
        self.assertIn('Guarantees (Rules.game six) white (lowerGoal 4)',
            layout['sources'][prefix+'/Group0/Check.agda'])
        collector = layout['sources'][prefix+'/AllLower.agda']
        self.assertIn('Root4.Group0.Check', collector)
        self.assertIn('allLower = R0.guarantee0 , (tt)', collector)
        for text in layout['sources'].values():
            self.assertNotIn('Tests.LowerPilot6', text)
            self.assertNotIn('Tests.ClosedPilot6', text)
            self.assertIn('--safe --without-K --cubical-compatible', text)

    def test_transitive_import_cost_excludes_independent_parts(self):
        a, b, c = fixture()['roots'][:3]
        entries = [dict(state=a, certificate='L', references=[]),
            dict(state=b, certificate='L', references=[]),
            dict(state=c, certificate='R0;', references=[a])]
        stats = describe(entries, max_entries=1)
        self.assertEqual(stats['rows'][2]['dependencies'], [0])
        self.assertEqual(stats['rows'][2]['imported_entries'], 1)
        self.assertEqual([entry['state'] for entry in closure(entries, [c])], [a, c])

    def test_heldout_or_proved_root_cannot_be_selected(self):
        for index in (0, 1, -1, 10, 19, 20, None, '4'):
            with self.assertRaises(ValueError):
                generated_layout(fixture(), index)

    def test_new_targets_are_cold_in_their_own_namespace(self):
        layout = generated_layout(fixture(), 4)
        target = layout['directory']+'/Group0/Part0.agda'
        pilot.assert_cold(target, {}, layout['directory'])
        with self.assertRaises(ValueError):
            pilot.assert_cold(target, {'_build/agda/'+target[4:-5]+'.agdai': 'a'*64}, layout['directory'])


if __name__ == '__main__':
    unittest.main()
