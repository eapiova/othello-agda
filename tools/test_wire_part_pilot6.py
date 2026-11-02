"""Scope admission and frozen disjoint sample tests; no Agda or native jobs."""
import copy
import hashlib
import json
import unittest

from initial_lazy_samples6 import selection
from wire_part_pilot6 import plan, approved, ANSWER, SCOPE


class NewRowPilot(unittest.TestCase):
    def fixture(self):
        p = plan(dict(accepted=True, layout=dict(side='lower', owned_rows=3047,
                                               owned_parts=selection('lower')['selected'])))
        raw = (json.dumps(p, indent=2) + '\n').encode()
        auth = dict(approved=True, answer=ANSWER, scope=SCOPE, question_item='test-fixture-only',
                    plan_sha256=hashlib.sha256(raw).hexdigest(),
                    native_search_allowed=False, production_authorized=False)
        auth.update({k:p[k] for k in ('cpu_max_seconds', 'hard_memory_gib',
                                     'artifact_cap_gib', 'free_disk_gib', 'new_rows')})
        return p, raw, auth

    def test_frozen_new_sample_and_resource_caps(self):
        p, raw, auth = self.fixture()
        self.assertEqual(p['selection']['selected'], [380, 4654, 12541, 15478, 17924, 21836, 29329, 34176])
        self.assertFalse(set(p['selection']['selected']) & set(selection('lower')['selected']))
        self.assertEqual(p['new_rows'], 1600)
        self.assertEqual(p['part_rss_limit_gib'], 1.5)
        self.assertLess(p['outer_cpu_cap_seconds'], p['outer_reservation_seconds'])
        self.assertLess(p['outer_reservation_seconds'], p['cpu_max_seconds'])
        self.assertFalse(p['native_search_allowed'])
        approved(p, raw, auth)

    def test_old_linkage_approval_and_changed_resources_are_refused(self):
        p, raw, auth = self.fixture()
        changes = [dict(answer='Sì, autorizzo solo questo collegamento'), dict(scope='map-only'),
                   dict(plan_sha256='0'*64), dict(cpu_max_seconds=1200), dict(hard_memory_gib=12),
                   dict(new_rows=3047), dict(production_authorized=True), dict(native_search_allowed=True),
                   dict(question_item=''), dict(approved=False)]
        for change in changes:
            with self.subTest(change=change):
                bad = copy.deepcopy(auth); bad.update(change)
                with self.assertRaisesRegex(ValueError, 'human scope approval'):
                    approved(p, raw, bad)
        with self.assertRaises(ValueError):
            approved(p, raw+b' ', auth)


if __name__ == '__main__':
    unittest.main()
