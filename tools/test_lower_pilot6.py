"""Focused LOWER pilot guards; no native solver or Agda invocation."""
import copy
import hashlib
from pathlib import Path
import re
import tempfile
import unittest

import compact_shared6 as compact
import global_assembly6 as assembly
import lower_pilot6 as pilot
from provenance import digest_entries
import symmetry_stats6 as symmetry


def fixture():
    roots = set()
    value = 0
    while len(roots) < 20:
        digits, number = [], value
        for _ in range(36):
            number, digit = divmod(number, 3)
            digits.append(str(digit))
        roots.add(symmetry.canonical_key('w'+''.join(digits))[0])
        value += 1
    roots = sorted(roots)
    return dict(format='othello-global-shared6-plan-v1', direction='lower', threshold=4,
                roots=roots, entries=[dict(state=state, certificate='L', references=[]) for state in roots])


def provenance(plan, digest='a'*64):
    return dict(format='othello-global-shared6-result-v1', status='complete', direction='lower',
                threshold=4, sample_size=20, scalar_replay=True, plan_sha256=digest,
                source_population_kind='canonical frontier full-state classes', subsample_seed=2026100701,
                cases=[dict(state=state, native_sha256='b'*64) for state in plan['roots']])


def training_report(plan):
    _, groups = pilot.generated_sources(plan)
    phases = [dict(label=f"group0-part{i}", accepted=True, cpu_seconds=1.25+i)
              for i in range(groups[0]['parts'])]
    return dict(groups=groups, completed_groups=[0], phases=phases, training_groups=[0],
                heldout_groups=[1], heldout_declared_before_checks=True)


class LowerGenerationTests(unittest.TestCase):
    def test_deterministic_exact_coverage_and_original_rules(self):
        plan = fixture()
        sources, groups = pilot.generated_sources(plan)
        self.assertEqual((sources, groups), pilot.generated_sources(copy.deepcopy(plan)))
        self.assertEqual([root for group in groups for root in group['roots']], plan['roots'])
        self.assertEqual([len(group['roots']) for group in groups], [10, 10])
        for index in range(2):
            text = sources[f'{pilot.DIRECTORY}/Group{index}/Check.agda']
            self.assertEqual(len(re.findall(r'^position\d+ :', text, re.M)), 10)
            self.assertEqual(len(re.findall(r'^  guarantee\d+ :', text, re.M)), 10)
            self.assertIn('Guarantees (Rules.game six) white (lowerGoal 4)', text)
            self.assertIn('guarantees-transfer Fast.fastGame6 (Rules.game six)', text)
        collector = sources[f'{pilot.DIRECTORY}/AllLower.agda']
        self.assertIn('allLower : AllLower rootCodes', collector)
        self.assertIn('Guarantees (Rules.game six) white (lowerGoal 4)', collector)
        self.assertNotIn('AllUpper :', collector)
        for text in sources.values():
            self.assertIn('--save-metas --safe --without-K --cubical-compatible '+pilot.WARNING, text)
            self.assertEqual(text.count(pilot.WARNING), 1)
            self.assertNotIn('postulate', text)
        hashes = pilot.source_hashes(sources)
        self.assertEqual(digest_entries(hashes), digest_entries(pilot.source_hashes(dict(reversed(list(sources.items()))))))

    def test_packed_tables_preserve_certificate_and_equality_obligations(self):
        state, reference = fixture()['roots'][:2]
        original, _, _ = assembly.part_source(1,
            [dict(state=state, certificate='R0;', references=[reference])], {reference: 0, state: 1}, 'lower')
        packed = pilot.packed_part(original)
        first, last = '  entries :', '  shape :'
        self.assertEqual(original.split(first, 1)[1].split(last, 1)[0],
                         packed.split(first, 1)[1].split(last, 1)[0])
        self.assertIn('  shape = refl {x = states}', packed)
        self.assertIn('  accepted = refl {x = true}', packed)
        self.assertIn('selectExport (importKeys "'+compact.pack_state(reference)+'L") P0.export', packed)
        self.assertIn('decodeCompactEntries "'+compact.pack_state(state)+compact.pack_certificate('R0;')+'"', packed)
        with self.assertRaises(ValueError):
            pilot.packed_part(original.replace('  shape = refl\n', ''))

    def test_group_closure_preserves_topological_entries(self):
        plan = fixture()
        shared = 'b'+'1'*36
        plan['entries'].insert(0, dict(state=shared, certificate='L', references=[]))
        for entry in plan['entries'][1:]:
            entry.update(certificate='R0;', references=[shared])
        sources, groups = pilot.generated_sources(plan)
        self.assertEqual([group['entries'] for group in groups], [11, 11])
        for index in range(2):
            part = sources[f'{pilot.DIRECTORY}/Group{index}/Part0.agda']
            expected = compact.encode((entry['state'], entry['certificate']) for entry in
                                      [plan['entries'][0]]+plan['entries'][1+index*10:11+index*10])
            self.assertIn('entries = fromMaybe [] (decodeCompactEntries "'+expected+'")', part)

    def test_scope_and_native_scalar_provenance_are_fail_closed(self):
        plan = fixture()
        pilot.validate_provenance(plan, provenance(plan), 'a'*64)
        for key, value in [('direction', 'upper'), ('sample_size', 19), ('scalar_replay', False),
                           ('status', 'building'), ('plan_sha256', 'c'*64),
                           ('source_population_kind', 'sorted prefix'), ('subsample_seed', None)]:
            bad = provenance(plan)
            bad[key] = value
            with self.assertRaises(ValueError):
                pilot.validate_provenance(plan, bad, 'a'*64)
        bad = provenance(plan)
        bad['cases'].reverse()
        with self.assertRaises(ValueError):
            pilot.validate_provenance(plan, bad, 'a'*64)
        for changed in [dict(plan, direction='upper'), dict(plan, threshold=3),
                        dict(plan, roots=plan['roots'][:-1])]:
            with self.assertRaises(ValueError):
                pilot.generated_sources(changed)
        noncanonical = copy.deepcopy(plan)
        root = next(state for state in plan['roots'] if symmetry.transform_key(state, 1) != state)
        rotated = symmetry.transform_key(root, 1)
        noncanonical['roots'][noncanonical['roots'].index(root)] = rotated
        noncanonical['entries'].append(dict(state=rotated, certificate='L', references=[]))
        with self.assertRaises(ValueError):
            pilot.validate_plan(noncanonical)


class LowerRejectionTests(unittest.TestCase):
    TEXT = '''file.agda:37.14-29: error: [UnequalTerms]
The terms
  true
and
  false
are not equal at type Bool
when checking that the expression refl {x = true} has type
checkShardBy keyed6 Fast.fastGame6 white (lowerGoal 4)
lowerTransport6 imports entries
≡ true
'''

    def test_false_all_black_lower_leaf_and_exact_bool_rejection(self):
        text = pilot.negative_source()
        self.assertIn(compact.pack_state('w'+'1'*36)+'L', text)
        self.assertIn('Fast.fastGame6 white (lowerGoal 4)', text)
        record = dict(accepted=False, exit_code=42, stop_reason=None)
        self.assertTrue(pilot.negative_rejected(record, [], [], self.TEXT))
        self.assertFalse(pilot.negative_rejected(record, ['changed'], [], self.TEXT))
        self.assertFalse(pilot.negative_rejected(record, [], ['own.agdai'], self.TEXT))
        for changed in [dict(record, stop_reason='cpu-limit'), dict(record, exit_code=-9),
                        dict(record, accepted=True, exit_code=0), dict(record, exit_code=None)]:
            self.assertFalse(pilot.negative_rejected(changed, [], [], self.TEXT))
        for changed in [self.TEXT.replace('false', 'true'), self.TEXT.replace('Bool', 'Nat'),
                        self.TEXT.replace('white (lowerGoal 4)', 'black (upperGoal 4)'),
                        self.TEXT.replace('lowerTransport6', 'upperTransport6'),
                        self.TEXT+'error: [NotInScope]\n', 'error: [NotInScope]\n']:
            self.assertFalse(pilot.negative_rejected(record, [], [], changed))


class LowerCacheTests(unittest.TestCase):
    def test_cold_target_and_every_old_hash(self):
        target = f'{pilot.DIRECTORY}/Group0/Part0.agda'
        interface = '_build/2.9.0/agda/Tests/LowerPilot6/Group0/Part0.agdai'
        pilot.assert_cold(target, {'_build/agda/Other/Part0.agdai': 'a'*64})
        with self.assertRaises(ValueError):
            pilot.assert_cold(target, {interface: 'a'*64})
        with self.assertRaises(ValueError):
            pilot.assert_cold('src/Tests/Upper/Part0.agda', {})
        before = dict(old='a'*64, removed='b'*64)
        after = dict(old='c'*64, added='d'*64)
        self.assertEqual({row['path'] for row in pilot.cache_changes(before, after)}, {'old', 'removed'})
        self.assertEqual(pilot.cache_changes(before, dict(before, added='d'*64)), [])

    def test_only_generic_interfaces_are_privately_copied(self):
        generic = {f'_build/agda/Core/M{i}.agdai': 'a'*64 for i in range(32)}
        pool = dict(generic, **{f'_build/agda/Tests/WarningTables6/M{i}.agdai': 'b'*64 for i in range(274)})
        self.assertEqual(pilot.generic_interfaces(pool), generic)
        bad = dict(pool)
        bad['_build/agda/Tests/Other/M0.agdai'] = bad.pop('_build/agda/Tests/WarningTables6/M0.agdai')
        with self.assertRaises(ValueError):
            pilot.generic_interfaces(bad)
        with tempfile.TemporaryDirectory() as directory:
            source, destination = Path(directory)/'donor.agdai', Path(directory)/'private.agdai'
            source.write_bytes(b'checked cache fixture')
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            pilot.copy_interface(source, destination, digest)
            self.assertNotEqual(source.stat().st_ino, destination.stat().st_ino)
            destination.write_bytes(b'changed private cache')
            self.assertEqual(source.read_bytes(), b'checked cache fixture')

    def test_storage_guards_include_final_growth(self):
        usage = dict(runs_bytes=pilot.MAX_RUNS_BYTES-20*pilot.MIB, free_bytes=pilot.MIN_FREE_BYTES)
        self.assertTrue(pilot.disk_allowed(usage))
        self.assertFalse(pilot.disk_allowed(dict(usage, runs_bytes=pilot.MAX_RUNS_BYTES-10*pilot.MIB)))
        self.assertFalse(pilot.disk_allowed(dict(usage, free_bytes=pilot.MIN_FREE_BYTES-1)))


class LowerHeldoutTests(unittest.TestCase):
    def test_fixed_fit_and_later_residuals(self):
        plan = fixture()
        report = training_report(plan)
        prediction = pilot.predict(plan, report)
        self.assertEqual(prediction['features'], pilot.FEATURE_NAMES)
        self.assertEqual(len(prediction['coefficients']), 4)
        self.assertTrue(all(value >= 0 for value in prediction['coefficients']))
        self.assertEqual(prediction['training_groups'], [0])
        self.assertEqual(prediction['heldout_groups'], [1])
        self.assertFalse(prediction['heldout_measured_when_fitted'])
        self.assertFalse(prediction['upper_timings_used'])
        expected = prediction['heldout_rows'][0]['predicted_cpu_seconds']
        phases = [dict(label='group1-part0', accepted=True, cpu_seconds=expected+2)]
        self.assertAlmostEqual(pilot.residuals(prediction, phases)['rows'][0]['residual_cpu_seconds'], 2)
        phases[0]['accepted'] = False
        self.assertIsNone(pilot.residuals(prediction, phases)['rows'][0]['residual_cpu_seconds'])

    def test_fit_refuses_heldout_leakage_or_incomplete_training(self):
        plan = fixture()
        original = training_report(plan)
        for label in ('group1-part0', 'group1-bounds'):
            report = copy.deepcopy(original)
            report['phases'].append(dict(label=label, accepted=False, cpu_seconds=0))
            with self.assertRaises(ValueError):
                pilot.predict(plan, report)
        for mutation in ('accepted', 'completed', 'declaration', 'missing'):
            report = copy.deepcopy(original)
            if mutation == 'accepted':
                report['phases'][0]['accepted'] = False
            elif mutation == 'completed':
                report['completed_groups'] = []
            elif mutation == 'declaration':
                report['heldout_declared_before_checks'] = False
            else:
                report['phases'] = []
            with self.assertRaises(ValueError):
                pilot.predict(plan, report)


if __name__ == '__main__':
    unittest.main()
