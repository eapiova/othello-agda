"""Cheap fail-closed provenance tests; no Agda, native build, or remote work."""
import copy
from pathlib import Path
import tempfile
import unittest

import assembly6
from initial_lazy_samples6 import selection
from initial_training_resume6 import (PREFIX, TRAINING, accepted_phases, argv,
    chosen_training, cold_target, load_training, validate_cached_sources,
    validate_pool, validate_receipt, validate_sources)
from provenance import digest_entries


class Provenance(unittest.TestCase):
    def setUp(self):
        self.old = Path('/previous/results/initial-lower-training6/check')
        self.source = dict(source_sha256='source')
        self.machine = dict(hostname='eapiova', agda_path='/agda', agda_sha256='compiler')
        self.sample_sha = 'dataset'
        self.targets = [PREFIX + '.' + n for n in ['Family', 'Part0', 'Part4599']]
        self.pool = {'_build/2.9/agda/src/' + t.replace('.', '/') + '.agdai': 'cache'
                     for t in self.targets}
        record = dict(accepted=True, exit_code=0, stop_reason=None, finished_utc='terminal',
            source_unchanged=True, expected_source_matches=True, own_target_cold=True,
            source_sha256='source', expected_source_sha256='source', root=str(self.old),
            machine='eapiova', executable_sha256='compiler', cpu_limit_seconds=60,
            rss_stop_threshold_gib=1.5)
        self.prior = dict(accepted=True, status='complete', finished_utc='terminal',
            machine=self.machine, checked_source=self.source, initial_problem2_proved=False,
            optimal_initial_pair_proved=False, production_authorized=False,
            late_original_lower_and_upper_checked=False, conditional_sample_links_checked=True,
            accepted_donor_unchanged=True, last_interface_pool_sha256=digest_entries(self.pool),
            layouts=[dict(prefix=PREFIX, side='lower', selected_training=[0, 4599], held_out_checked=False,
                input_samples_sha256=self.sample_sha, targets=['Family', 'Part0', 'Part4599'],
                cases=[dict(part=0), dict(part=4599)])],
            phases=[dict(target=t, record=dict(copy.deepcopy(record), argv=argv(self.machine, t)),
                         borrowed_interfaces_unchanged=True) for t in self.targets])

    def validate(self):
        return accepted_phases(self.prior, self.pool, self.source, self.machine, self.old, self.sample_sha)

    def test_exact_reuse_preserves_original_receipts_and_skips_prior_targets(self):
        inherited = self.validate()
        self.assertEqual(inherited, self.prior['phases'])
        new = [PREFIX + '.Part' + str(p) for p in TRAINING[2:]]
        self.assertEqual(len(new), 6)
        self.assertTrue(set(new).isdisjoint(p['target'] for p in inherited))
        for target in new:
            cold_target(self.pool, target)
        self.assertEqual(inherited[0]['record']['root'], str(self.old))

    def test_failed_or_warm_or_changed_phase_rejected(self):
        original = copy.deepcopy(self.prior)
        for field, value in [('accepted', False), ('own_target_cold', False),
                             ('source_sha256', 'changed'), ('executable_sha256', 'changed'),
                             ('root', '/other'), ('machine', 'other'), ('rss_stop_threshold_gib', 3)]:
            with self.subTest(field=field):
                self.prior = copy.deepcopy(original)
                self.prior['phases'][1]['record'][field] = value
                with self.assertRaises(ValueError):
                    self.validate()
        self.prior = original
        self.prior['phases'][1]['record']['argv'].remove('--safe')
        with self.assertRaises(ValueError):
            self.validate()

    def test_phase_gap_missing_part_and_warm_new_target_rejected(self):
        original = copy.deepcopy(self.prior)
        self.prior['phases'].pop(1)
        with self.assertRaises(ValueError):
            self.validate()
        self.prior = original
        first = next(iter(self.pool))
        value = self.pool.pop(first)
        with self.assertRaises(ValueError):
            self.validate()
        self.pool[first] = value
        target = PREFIX + '.Part9756'
        self.pool['_build/2.9/agda/src/' + target.replace('.', '/') + '.agdai'] = 'unexpected'
        with self.assertRaises(ValueError):
            self.validate()
        with self.assertRaises(ValueError):
            cold_target(self.pool, target)

    def test_changed_cache_and_borrowed_cache_receipt_rejected(self):
        actual = dict(self.pool)
        actual[next(iter(actual))] = 'changed'
        with self.assertRaises(ValueError):
            validate_pool(self.pool, actual)
        self.prior['phases'][0]['borrowed_interfaces_unchanged'] = False
        with self.assertRaises(ValueError):
            self.validate()

    def test_failed_outer_receipt_rejected(self):
        previous = Path('/previous')
        receipt = dict(finished_utc='terminal', accepted=True, exit_code=0, stop_reason=None,
            source_unchanged=True, expected_source_matches=True, source_sha256='source',
            expected_source_sha256='source', root=str(previous), machine='eapiova')
        validate_receipt(receipt, self.source, previous, 'eapiova')
        for field, value in [('accepted', False), ('finished_utc', None), ('source_unchanged', False),
                             ('expected_source_sha256', 'changed')]:
            with self.subTest(field=field):
                changed = dict(receipt, **{field: value})
                with self.assertRaises(ValueError):
                    validate_receipt(changed, self.source, previous, 'eapiova')


class Dataset(unittest.TestCase):
    def fixture(self):
        plan = selection('lower')
        cases = [dict(part=p, dependencies=[p]) for p in plan['selected']]
        return dict(cases=cases, states={p: dict(rows=1, text='dummy') for p in plan['selected']},
            complete=dict(selected=plan['selected'], parts=plan['expected']['layout_parts'],
                          records=plan['expected']['layout_records'], tokens=plan['expected']['layout_tokens']))

    def test_only_training_demands_are_retained(self):
        chosen = chosen_training(self.fixture())
        self.assertEqual([c['part'] for c in chosen['cases']], TRAINING)
        self.assertEqual(set(chosen['states']), set(TRAINING))

    def test_wrong_selection_or_missing_dependency_rejected(self):
        decoded = self.fixture()
        decoded['complete']['selected'] = decoded['complete']['selected'][:-1]
        with self.assertRaises(ValueError):
            chosen_training(decoded)
        decoded = self.fixture()
        decoded['states'].pop(TRAINING[3])
        with self.assertRaises(ValueError):
            chosen_training(decoded)

    def test_wrong_dataset_hash_rejected_before_decode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'results/lower.samples.jsonl'
            path.parent.mkdir()
            path.write_text('invalid data\n')
            with self.assertRaisesRegex(ValueError, 'sample hash'):
                load_training(path, 'wrong')


class Sources(unittest.TestCase):
    def test_changed_source_and_missing_inherited_dependency_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            old, current, check = [Path(directory) / n for n in ['old', 'current', 'check']]
            name = 'src/Prelude.agda'
            dependency = 'src/Tests/InitialLazyTrainingLower/StateData0.agda'
            for root in [old, current, check]:
                (root / name).parent.mkdir(parents=True)
                (root / name).write_text('same core')
            (old / dependency).parent.mkdir(parents=True)
            (old / dependency).write_text('same state')
            generated = {dependency: assembly6.sha(old / dependency)}
            layout = dict(generated_sha256=generated)
            validate_sources(old, current, layout, generated)
            with self.assertRaises(ValueError):
                validate_sources(old, current, layout, {})
            (current / name).write_text('changed core')
            with self.assertRaises(ValueError):
                validate_sources(old, current, layout, generated)
            pool = {'_build/2.9/agda/src/Prelude.agdai': 'cache'}
            validate_cached_sources(old, check, pool)
            (check / name).unlink()
            with self.assertRaises(ValueError):
                validate_cached_sources(old, check, pool)


if __name__ == '__main__':
    unittest.main()
