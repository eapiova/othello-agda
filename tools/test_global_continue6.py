"""Continuation guards keep ordinary failures distinct from resource recovery."""
import unittest

import global_continue6 as continuation
import part77_pilot6 as pilot


class GlobalContinueTests(unittest.TestCase):
    def test_only_resource_failure_gets_one_alternate(self):
        metric = dict(accepted=False, heap_exhausted=False, stop_reason=None)
        self.assertFalse(continuation.resource_failure(metric))
        self.assertTrue(continuation.resource_failure({**metric, 'heap_exhausted': True}))
        for reason in ('rss-threshold', 'cpu-limit', 'timeout'):
            self.assertTrue(continuation.resource_failure({**metric, 'stop_reason': reason}))
        self.assertFalse(continuation.resource_failure({**metric, 'accepted': True, 'heap_exhausted': True}))

    def test_generalized_literal_tables_keep_actual_owners_and_bound(self):
        earlier = 'b' + '0' * 36
        state = 'w' + '0' * 35 + '1'
        part = [dict(state=state, certificate='L', references=[earlier])]
        sources = pilot.thin_sources(part, {earlier: 77, state: 93}, 'upper', index=93)
        self.assertEqual(set(sources), {'Part93ThinImports', 'Part93Thin'})
        imports, checker = sources['Part93ThinImports'], sources['Part93Thin']
        self.assertIn('P77.states states77 P77.sound covered77', imports)
        self.assertIn('module Tests.GlobalPilot6.Part93Thin where', checker)
        self.assertIn('import Tests.GlobalPilot6.Part93ThinImports as Thin', checker)
        self.assertIn('Fast.fastGame6 black (upperGoal 4)', checker)
        self.assertIn('accepted = refl', checker)
        self.assertIn('shardBy-sound', checker)

    def test_forward_citation_and_wrong_part_are_rejected(self):
        earlier, state = 'b' + '0'*36, 'w' + '0'*36
        part = [dict(state=state, certificate='L', references=[earlier])]
        with self.assertRaises(ValueError):
            pilot.thin_sources(part, {earlier: 94, state: 93}, 'upper', index=93)
        with self.assertRaises(ValueError):
            pilot.thin_sources(part, {earlier: 77, state: 94}, 'upper', index=93)


if __name__ == '__main__':
    unittest.main()
