"""A repair needs the exact terminal heap failure and certified prefix."""
import copy
from pathlib import Path
import tempfile
import unittest

from nat_lazy_repair6 import heap_prefix
from test_nat_descendant_resume6 import Recovery


class HeapRepair(unittest.TestCase):
    def setUp(self):
        fixture = Recovery()
        fixture.setUp()
        self.fixture = fixture
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / 'records').mkdir()
        self.log = self.base / 'records/last.log'
        self.log.write_text('agda: Heap exhausted;\nagda: Current maximum heap size is 1415577600 bytes (1350 MB).\n')
        failure = copy.deepcopy(fixture.prior['phases'][-1])
        failure['target'] = fixture.targets[3]
        failure['record'].update(label='last', accepted=False, exit_code=251, stop_reason=None,
            argv=fixture.argv(failure['target']), log_bytes=self.log.stat().st_size)
        fixture.prior['phases'].append(failure)

    def read(self):
        f = self.fixture
        return heap_prefix(f.prior, f.pool, f.source, f.machine, f.old, self.base)

    def test_exact_heap_failure_preserves_only_accepted_prefix(self):
        prefix, failure = self.read()
        self.assertEqual(prefix, self.fixture.targets[:3])
        self.assertEqual(len(failure['log_sha256']), 64)

    def test_non_heap_log_cannot_be_used_for_repair(self):
        self.log.write_text('type mismatch\n')
        self.fixture.prior['phases'][-1]['record']['log_bytes'] = self.log.stat().st_size
        with self.assertRaises(ValueError):
            self.read()

    def test_other_exit_cpu_stop_or_changed_flags_are_rejected(self):
        rec = self.fixture.prior['phases'][-1]['record']
        for field, value in [('exit_code', 1), ('stop_reason', 'cpu-limit'),
                             ('argv', ['/agda']), ('source_sha256', 'different')]:
            with self.subTest(field=field):
                old = rec[field]
                rec[field] = value
                with self.assertRaises(ValueError):
                    self.read()
                rec[field] = old

    def test_future_own_interface_prevents_repair(self):
        target = self.fixture.targets[3]
        self.fixture.pool['_build/2.9/agda/' + target.replace('.', '/') + '.agdai'] = 'unexpected'
        with self.assertRaises(ValueError):
            self.read()


if __name__ == '__main__':
    unittest.main()
