"""Incomplete, retroactive or changed evidence must not validate a forecast."""
import copy
from datetime import datetime, timedelta, timezone
import unittest

from nat_forecast6 import HELDOUT, TRAINING
from provenance import digest_entries
from validate_nat_forecast6 import PREFIX, validate


class Validation(unittest.TestCase):
    def setUp(self):
        self.source = dict(source_sha256='a' * 64)
        self.machine = dict(agda_path='/agda', agda_sha256='b' * 64)
        start = datetime(2026, 10, 9, 10, tzinfo=timezone.utc)
        targets = ['Family'] + ['Part' + str(i) for i in range(267)]
        targets += ['Node' + str(i) for i in range(31)] + ['Root']
        phases = []
        pool = {}
        for index, name in enumerate(targets[:268]):
            target = PREFIX + name
            rec = dict(accepted=True, exit_code=0, stop_reason=None, cpu_seconds=1., peak_rss_gib=.5,
                source_unchanged=True, expected_source_matches=True, own_target_cold=True,
                source_sha256=self.source['source_sha256'], expected_source_sha256=self.source['source_sha256'],
                executable_sha256=self.machine['agda_sha256'],
                started_utc=(start + timedelta(seconds=2 * index)).isoformat(),
                finished_utc=(start + timedelta(seconds=2 * index + 1)).isoformat(),
                argv=['/agda', '--no-libraries', '-i', 'src', '--safe', '--without-K',
                      '--cubical-compatible', '--save-metas', 'src/' + target.replace('.', '/') + '.agda',
                      '+RTS', '-M1350M', '-c', '-s', '-RTS'])
            phases.append(dict(target=target, record=rec, borrowed_interfaces_unchanged=True))
            pool['_build/2.9/agda/' + target.replace('.', '/') + '.agdai'] = 'c' * 64
        self.pool = pool
        generated = {'src/Tests/NatDescendant6/BodyData' + str(i) + '.agda': 'd' * 64 for i in range(267)}
        self.report = dict(checked_source=self.source, machine=self.machine, phases=phases,
            accepted_parts=267, initial_problem2_proved=False, production_authorized=False,
            last_interface_pool_sha256=digest_entries(pool),
            layout=dict(parts=267, rows=53217, hierarchy_nodes=31, targets=targets, generated_sha256=generated))
        self.forecast = dict(format='othello-nat-forecast6-v1', training_indices=list(TRAINING),
            heldout_indices=list(HELDOUT), excluded_known_alternate_variant_indices=[231],
            heldout_measured_when_fitted=False, whole_workflow_validated=False, production_authorized=False,
            gate_relative_error=.30, training_source=self.source, machine=self.machine,
            created_utc=(start + timedelta(seconds=202)).isoformat(),
            training_phases=copy.deepcopy(phases[1:101]), heldout_predicted_cpu_seconds=float(len(HELDOUT)),
            rows=[dict(part=i, body_source_sha256='d' * 64, predicted_cpu_seconds=1.) for i in range(267)])

    def read(self):
        return validate(self.forecast, self.report, self.pool)

    def test_complete_fixed_suffix_passes_without_production_claim(self):
        result = self.read()
        self.assertTrue(result['row_forecast_passed'])
        self.assertEqual(result['heldout_count'], 66)
        self.assertFalse(result['whole_workflow_validated'])
        self.assertFalse(result['production_authorized'])

    def test_incomplete_suffix_and_failed_rows_are_rejected(self):
        for mutation in ('missing', 'failed'):
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.report)
                if mutation == 'missing':
                    self.report['phases'].pop()
                    self.report['accepted_parts'] -= 1
                else:
                    self.report['phases'][-1]['record']['accepted'] = False
                with self.assertRaises(ValueError):
                    self.read()
                self.report = original

    def test_duplicate_or_reordered_targets_are_rejected(self):
        self.report['phases'][202] = copy.deepcopy(self.report['phases'][201])
        with self.assertRaises(ValueError):
            self.read()

    def test_changed_compiler_source_flags_or_warm_target_are_rejected(self):
        mutations = [('executable_sha256', 'e' * 64), ('source_sha256', 'e' * 64),
                     ('own_target_cold', False), ('argv', ['/agda'])]
        for field, value in mutations:
            with self.subTest(field=field):
                rec = self.report['phases'][201]['record']
                old = rec[field]
                rec[field] = value
                with self.assertRaises(ValueError):
                    self.read()
                rec[field] = old

    def test_missing_interface_or_changed_body_is_rejected(self):
        self.pool.pop('_build/2.9/agda/Tests/NatDescendant6/Part266.agdai')
        self.report['last_interface_pool_sha256'] = digest_entries(self.pool)
        with self.assertRaises(ValueError):
            self.read()
        self.setUp()
        self.forecast['rows'][266]['body_source_sha256'] = 'e' * 64
        with self.assertRaises(ValueError):
            self.read()

    def test_retroactive_or_timezone_free_forecast_is_rejected(self):
        for timestamp in ('2026-10-09T10:10:00+00:00', '2026-10-09T10:03:22'):
            with self.subTest(timestamp=timestamp):
                self.forecast['created_utc'] = timestamp
                with self.assertRaises(ValueError):
                    self.read()

    def test_model_failure_is_reported_without_relabeling_it_as_incomplete(self):
        self.report['phases'][201]['record']['cpu_seconds'] = 30.
        result = self.read()
        self.assertFalse(result['row_forecast_passed'])
        self.assertTrue(result['fixed_suffix_complete'])

    def test_chained_prefix_keeps_original_training_evidence(self):
        self.report['inherited_accepted_phases'] = self.report['phases'][:226]
        self.report['phases'] = self.report['phases'][226:]
        self.assertTrue(self.read()['row_forecast_passed'])


if __name__ == '__main__':
    unittest.main()
