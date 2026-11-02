"""Cheap provenance and source-isolation tests; these never run Agda."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from nat_lazy_resume6 import (PREFIX, argv, generate_next, helper_plan,
                             unchanged_cached_sources, validate_predecessor,
                             compact_epochs, expand_epochs, storage_stop)
from nat_descendant_resume6 import closed_worker
from provenance import digest_entries


class Continuation(unittest.TestCase):
    def setUp(self):
        self.machine = dict(agda_path='/agda', agda_sha256='binary')
        self.old = Path('/accepted/check')
        self.source = dict(source_sha256='repair-source')
        self.original = dict(source_sha256='old-source')
        names = ['Family'] + ['Part' + str(i) for i in range(267)]
        names += ['Node' + str(i) for i in range(31)] + ['Root']
        self.repair = dict(part=242, dependencies=[0, 242], exported_linked_type_unchanged=True,
            targets=[PREFIX + '.LazyFamily', PREFIX + '.RepairBridge', PREFIX + '.StateEq0',
                     PREFIX + '.StateEq242', PREFIX + '.Part242'])
        inherited = [self.phase(PREFIX + '.' + n, self.original, '/historical/check') for n in names[:243]]
        phases = [self.phase(n, self.source, str(self.old)) for n in ['Othello.LazyIndexed6'] + self.repair['targets']]
        self.pool = {self.interface(p['target']): 'hash' for p in inherited + phases}
        self.prior = dict(format='othello-nat-lazy-repair6-v1', accepted=True, status='complete',
            finished_utc='done', accepted_parts=243, reused_parts=242,
            repaired_original_conditional_export_checked=True, accepted_predecessor_unchanged=True,
            initial_problem2_proved=False, production_authorized=False, optimal_initial_pair_proved=False,
            layout=dict(parts=267, rows=53217, hierarchy_nodes=31, side='lower', targets=names),
            checked_source=self.source, original_checked_source=self.original, machine=self.machine,
            last_interface_pool_sha256=digest_entries(self.pool), inherited_accepted_phases=inherited,
            accepted_root_paths=['/historical/check'], phases=phases, repair=self.repair)

    @staticmethod
    def interface(target):
        return '_build/2.9/agda/src/' + target.replace('.', '/') + '.agdai'

    def phase(self, target, source, root):
        return dict(target=target, borrowed_interfaces_unchanged=True,
            record=dict(accepted=True, exit_code=0, stop_reason=None, source_unchanged=True,
                expected_source_matches=True, source_sha256=source['source_sha256'],
                expected_source_sha256=source['source_sha256'], root=root,
                executable_sha256='binary', argv=argv(self.machine, target)))

    def read(self):
        return validate_predecessor(self.prior, self.pool, self.source, self.machine, self.old)

    def test_mixed_epochs_remain_separate(self):
        accepted = self.read()
        self.assertIn(PREFIX + '.Part242', accepted)
        self.assertNotIn(PREFIX + '.Part243', accepted)
        self.assertEqual(self.prior['inherited_accepted_phases'][0]['record']['source_sha256'], 'old-source')

    def test_relabeling_original_as_repair_source_is_rejected(self):
        self.prior['inherited_accepted_phases'][0]['record']['source_sha256'] = 'repair-source'
        with self.assertRaises(ValueError):
            self.read()

    def test_missing_and_future_interfaces_are_rejected(self):
        for target, add in [(PREFIX + '.Part242', False), (PREFIX + '.Part243', True),
                            (PREFIX + '.Node0', True), (PREFIX + '.StateEq1', True)]:
            with self.subTest(target=target):
                original = copy.deepcopy(self.pool)
                if add:
                    self.pool[self.interface(target)] = 'hash'
                else:
                    self.pool.pop(self.interface(target))
                self.prior['last_interface_pool_sha256'] = digest_entries(self.pool)
                with self.assertRaises(ValueError):
                    self.read()
                self.pool = original
                self.prior['last_interface_pool_sha256'] = digest_entries(self.pool)

    def test_wrong_flags_compiler_source_exit_are_rejected(self):
        rec = self.prior['phases'][-1]['record']
        for field, value in [('argv', ['/agda', '--safe']), ('executable_sha256', 'other'),
                             ('source_sha256', 'old-source'), ('exit_code', 1)]:
            with self.subTest(field=field):
                original = rec[field]
                rec[field] = value
                with self.assertRaises(ValueError):
                    self.read()
                rec[field] = original

    def test_live_predecessor_is_rejected(self):
        receipt = dict(label='repair', remote_unit='othello6-repair.service', accepted=True)
        output = 'LoadState=loaded\nActiveState=active\nSubState=running\nMainPID=10\nControlPID=0\n'
        with patch('nat_descendant_resume6.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout=output)):
            with self.assertRaises(ValueError):
                closed_worker(receipt)

    def test_helper_reuse_requires_accepted_identical_source(self):
        helper = PREFIX + '.LazyFamily'
        cold = PREFIX + '.StateEq243'
        repair = dict(targets=[helper, cold, PREFIX + '.Part243'])
        path = 'src/' + helper.replace('.', '/') + '.agda'
        pool = {self.interface(helper): 'cache'}
        reused, targets = helper_plan(repair, pool, {helper}, {path: 'source'}, {path: 'source'})
        self.assertEqual(targets, [cold])
        self.assertEqual(reused[0]['interface_sha256'], 'cache')
        for accepted, after in [(set(), {path: 'source'}), ({helper}, {path: 'changed'})]:
            with self.assertRaises(ValueError):
                helper_plan(repair, pool, accepted, {path: 'source'}, after)

    def test_cached_import_of_changed_proof_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'src/Some.agda'
            source.parent.mkdir()
            source.write_text('open import ' + PREFIX + '.Part243\n')
            pool = {'_build/2.9/agda/src/Some.agdai': 'cache'}
            before = {'src/Some.agda': 'same'}
            with self.assertRaises(ValueError):
                unchanged_cached_sources(root, before, before, pool, PREFIX + '.Part243')

    def test_only_current_unchecked_part_can_be_generated(self):
        with patch('nat_lazy_resume6.generate') as generator:
            for part, count, pool in [(244, 243, {}), (242, 242, {}),
                    (243, 243, {self.interface(PREFIX + '.Part243'): 'cache'})]:
                with self.assertRaises(ValueError):
                    generate_next(Path('/unused'), part, count, pool)
            generator.assert_not_called()

    def test_generation_preserves_all_old_sources_except_own_part(self):
        before = {'src/PartData.agda': 'data', 'src/' + PREFIX.replace('.', '/') + '/Part243.agda': 'old'}
        after = dict(before)
        after['src/PartData.agda'] = 'changed'
        with patch('nat_lazy_resume6.source_map', side_effect=[before, after]), \
                patch('nat_lazy_resume6.generate', return_value=dict(generated_sha256={})):
            with self.assertRaises(ValueError):
                generate_next(Path('/unused'), 243, 243, {})


class CompactEvidence(unittest.TestCase):
    def test_full_and_delta_epochs_round_trip_with_identical_identities(self):
        first = {'src/A.agda': 'a', 'src/Part.agda': 'strict'}
        second = {**first, 'src/Part.agda': 'lazy', 'src/Eq.agda': 'proof'}
        epochs = [dict(kind='first', identity=dict(source_sha256=digest_entries(first)), sources=first),
                  dict(kind='second', identity=dict(source_sha256=digest_entries(second)), sources=second)]
        compact = compact_epochs(epochs)
        self.assertEqual(expand_epochs(compact), [first, second])
        self.assertNotIn('sources', compact[1])
        self.assertNotIn('src/A.agda', compact[1]['source_delta'])
        self.assertEqual([e['identity'] for e in compact], [e['identity'] for e in epochs])

    def test_mutated_delta_digest_is_rejected(self):
        source = {'src/A.agda': 'checked'}
        epochs = [dict(identity=dict(source_sha256=digest_entries(source)), source_delta=source)]
        epochs[0]['source_delta']['src/A.agda'] = 'changed'
        with self.assertRaises(ValueError):
            expand_epochs(epochs)

    def test_removed_historical_source_is_rejected(self):
        epochs = [dict(identity=dict(source_sha256=digest_entries({'src/A.agda': 'a'})),
                       sources={'src/A.agda': 'a'}),
                  dict(identity=dict(source_sha256=digest_entries({})), sources={})]
        with self.assertRaises(ValueError):
            expand_epochs(epochs)

    def test_only_pinned_storage_failure_can_resume(self):
        import hashlib
        log = b'Traceback...\nValueError: storage gate reached\n'
        digest = hashlib.sha256(log).hexdigest()
        actual = dict(accepted=False, exit_code=1, stop_reason=None)
        storage_stop(actual, log, digest)
        for bad, text, pin in [({**actual, 'accepted': True}, log, digest),
                               ({**actual, 'stop_reason': 'rss'}, log, digest),
                               (actual, b'Agda failed', digest), (actual, log, 'wrong')]:
            with self.assertRaises(ValueError):
                storage_stop(bad, text, pin)


if __name__ == '__main__':
    unittest.main()
