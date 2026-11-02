"""Scope separation and log admission; never invokes Agda or native search."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from collections import namedtuple

from canonical_state_pilot6 import ANSWER, SCOPE, ANSWER60, SCOPE60, approved, checked_modules, storage


class CanonicalPilot(unittest.TestCase):
    def test_only_explicit_repeated_row_scope_is_admitted(self):
        raw = json.dumps(dict(scope=SCOPE,free_disk_gib=80)).encode()
        auth = dict(approved=True, scope=SCOPE, answer=ANSWER,
                    plan_sha256=hashlib.sha256(raw).hexdigest(), cpu_max_seconds=600,
                    hard_memory_gib=12, artifact_cap_gib=12, free_disk_gib=80,
                    part=34176, repeated_boolean_rows=200, new_distinct_game_rows=0,
                    native_search_allowed=False, production_authorized=False)
        approved(raw, auth)
        for change in (dict(scope='resume-part34176-full-map-bridge6-v1'),
                       dict(answer='Sì, autorizzo il completamento'),
                       dict(repeated_boolean_rows=0), dict(new_distinct_game_rows=200),
                       dict(free_disk_gib=60), dict(production_authorized=True),
                       dict(native_search_allowed=True), dict(plan_sha256='0'*64)):
            with self.subTest(change=change):
                altered = copy.deepcopy(auth); altered.update(change)
                with self.assertRaises(ValueError): approved(raw, altered)

    def test_warnings_do_not_count_as_module_checks(self):
        text = ('Checking Tests.X.Root (/tmp/Root.agda).\n'
                'when checking the definition of example\n'
                ' Checking Tests.X.Part (/tmp/Part.agda).\n')
        self.assertEqual(checked_modules(text), ['Tests.X.Root', 'Tests.X.Part'])

    def test_sixty_requires_distinct_scope_and_explicit_exception(self):
        plan=dict(scope=SCOPE60,free_disk_gib=60,temporary_disk_floor_exception=True)
        raw=json.dumps(plan).encode()
        auth=dict(approved=True,scope=SCOPE60,answer=ANSWER60,
            plan_sha256=hashlib.sha256(raw).hexdigest(),cpu_max_seconds=600,
            hard_memory_gib=12,artifact_cap_gib=12,free_disk_gib=60,
            part=34176,repeated_boolean_rows=200,new_distinct_game_rows=0,
            native_search_allowed=False,production_authorized=False,
            temporary_disk_floor_exception=True)
        self.assertEqual(approved(raw,auth),60)
        for change in (dict(scope=SCOPE),dict(answer=ANSWER),dict(free_disk_gib=80),
                       dict(temporary_disk_floor_exception=False)):
            altered=copy.deepcopy(auth);altered.update(change)
            with self.assertRaises(ValueError):approved(raw,altered)

    def test_scoped_floor_keeps_global_policy_and_artifact_cap(self):
        Usage=namedtuple('Usage','total used free')
        with patch('canonical_state_pilot6.subprocess.check_output',return_value=str(10*2**30)+' /runs'), \
             patch('canonical_state_pilot6.shutil.disk_usage',return_value=Usage(100*2**30,31*2**30,69*2**30)):
            self.assertEqual(storage(Path('/runs/test'),floor=60)['free_floor_bytes'],60*2**30)
            with self.assertRaises(ValueError):storage(Path('/runs/test'),floor=80)
        with patch('canonical_state_pilot6.subprocess.check_output',return_value=str(12*2**30)+' /runs'), \
             patch('canonical_state_pilot6.shutil.disk_usage',return_value=Usage(100*2**30,31*2**30,69*2**30)):
            with self.assertRaises(ValueError):storage(Path('/runs/test'),floor=60)
        with patch('canonical_state_pilot6.subprocess.check_output',return_value=str(10*2**30)+' /runs'), \
             patch('canonical_state_pilot6.shutil.disk_usage',return_value=Usage(100*2**30,41*2**30,59*2**30)):
            with self.assertRaises(ValueError):storage(Path('/runs/test'),floor=60)


if __name__ == '__main__':
    unittest.main()
