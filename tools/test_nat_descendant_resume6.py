"""Recovery must skip exactly successful proofs, never failed or future ones."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from nat_descendant_resume6 import accepted_prefix, closed_worker


class Recovery(unittest.TestCase):
    def setUp(self):
        self.old = Path('/frozen/results/nat-descendant6/check')
        self.source = {'source_sha256': 'source'}
        self.machine = {'agda_sha256': 'binary', 'agda_path': '/agda'}
        self.names = ['Family'] + ['Part' + str(i) for i in range(267)]
        self.names += ['Node' + str(i) for i in range(31)] + ['Root']
        self.targets = ['Tests.NatDescendant6.' + n for n in self.names]
        record = dict(accepted=True, exit_code=0, stop_reason=None,
            source_unchanged=True, expected_source_matches=True, source_sha256='source', expected_source_sha256='source',
            root=str(self.old), executable_sha256='binary')
        self.prior = dict(layout=dict(parts=267, rows=53217, hierarchy_nodes=31,
            targets=self.names), accepted_parts=2,
            phases=[dict(target=t, record=copy.deepcopy(record), borrowed_interfaces_unchanged=True)
                    for t in self.targets[:3]])
        for phase in self.prior['phases']:
            phase['record']['argv'] = self.argv(phase['target'])
        self.pool = {'_build/2.9/agda/' + t.replace('.', '/') + '.agdai': 'hash'
                     for t in self.targets[:3]}

    def read(self):
        return accepted_prefix(self.prior, self.pool, self.source, self.machine, self.old)

    def argv(self, target):
        return ['/agda', '--no-libraries', '-i', 'src', '--safe', '--without-K',
            '--cubical-compatible', '--save-metas', 'src/' + target.replace('.', '/') + '.agda',
            '+RTS', '-M1350M', '-c', '-s', '-RTS']

    def test_only_successful_prefix_is_reused(self):
        failed = copy.deepcopy(self.prior['phases'][-1])
        failed['target'] = self.targets[3]
        failed['record']['argv'] = self.argv(failed['target'])
        failed['record'].update(accepted=False, exit_code=-15, stop_reason='cpu-limit')
        self.prior['phases'].append(failed)
        _, accepted = self.read()
        self.assertEqual(accepted, self.targets[:3])

    def test_unrecorded_future_interface_is_rejected(self):
        self.pool['_build/2.9/agda/' + self.targets[3].replace('.', '/') + '.agdai'] = 'hash'
        with self.assertRaises(ValueError):
            self.read()

    def test_missing_accepted_interface_is_rejected(self):
        self.pool.pop(next(iter(self.pool)))
        with self.assertRaises(ValueError):
            self.read()

    def test_changed_source_or_compiler_is_rejected(self):
        for field in ('source_sha256', 'executable_sha256'):
            with self.subTest(field=field):
                original = self.prior['phases'][1]['record'][field]
                self.prior['phases'][1]['record'][field] = 'changed'
                with self.assertRaises(ValueError):
                    self.read()
                self.prior['phases'][1]['record'][field] = original

    def test_logical_failure_is_not_blindly_retried(self):
        failed = copy.deepcopy(self.prior['phases'][-1])
        failed['target'] = self.targets[3]
        failed['record']['argv'] = self.argv(failed['target'])
        failed['record'].update(accepted=False, exit_code=42)
        self.prior['phases'].append(failed)
        with self.assertRaises(ValueError):
            self.read()

    def test_chained_prefix_preserves_original_record_paths(self):
        inherited = self.prior['phases'].pop(0)
        inherited['record']['root'] = '/older/check'
        self.prior['inherited_accepted_phases'] = [inherited]
        self.prior['accepted_root_paths'] = ['/older/check']
        _, accepted = self.read()
        self.assertEqual(accepted, self.targets[:3])

    def test_changed_safety_flags_are_rejected(self):
        self.prior['phases'][1]['record']['argv'].remove('--safe')
        with self.assertRaises(ValueError):
            self.read()

    def test_worker_exit_is_distinct_from_cpu_killed_child(self):
        receipt = dict(label='pilot', remote_unit='othello6-pilot.service', accepted=False, exit_code=-15)
        status = 'LoadState=loaded\nActiveState=failed\nSubState=failed\nMainPID=0\nControlPID=0\nExecMainStatus=1\n'
        with patch('nat_descendant_resume6.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout=status)):
            self.assertEqual(closed_worker(receipt)['ExecMainStatus'], '1')

    def test_live_predecessor_is_never_reused(self):
        receipt = dict(label='pilot', remote_unit='othello6-pilot.service', accepted=False, exit_code=-15)
        status = 'LoadState=loaded\nActiveState=active\nSubState=running\nMainPID=42\nControlPID=0\nExecMainStatus=0\n'
        with patch('nat_descendant_resume6.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout=status)):
            with self.assertRaises(ValueError):
                closed_worker(receipt)


if __name__ == '__main__':
    unittest.main()
