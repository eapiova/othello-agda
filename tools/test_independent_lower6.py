"""Conditional parts must keep every citation as a proof obligation."""
import re
import unittest

import compact_shared6 as compact
import independent_lower6 as independent
from independent_collect6 import coverage_source


class IndependentLowerTests(unittest.TestCase):
    def setUp(self):
        self.a = 'w'+'2'*36
        self.b = 'b'+'1'*35+'2'
        self.c = 'w'+'0'*35+'1'
        self.entries = [dict(state=self.a, certificate='L', references=[]),
            dict(state=self.b, certificate='R0;', references=[self.a]),
            dict(state=self.c, certificate='R0;', references=[self.b])]
        self.parts = [[entry] for entry in self.entries]
        self.owners = {entry['state']: index for index, entry in enumerate(self.entries)}

    def test_closed_part_keeps_bytes_without_earlier_proof_imports(self):
        source = independent.part_source(1, self.parts[1], self.owners)
        wire = compact.encode([(self.b, 'R0;')])
        self.assertIn('decodeCompactEntries "'+wire+'"', source)
        self.assertIn('imports = shardStates keyed6', source)
        self.assertIn(independent.state_wire([self.a]), source)
        self.assertIn('AllT (Proven Fast.fastGame6 white (lowerGoal 4)) imports →', source)
        self.assertIn('lowerTransport6 imports entries inv accepted', source)
        self.assertNotRegex(source, re.compile(r'^import Tests\..*Part\d+', re.M))
        self.assertNotIn(independent.OLD, source)

    def test_root_collector_discharges_each_required_import_trie(self):
        source = independent.collector_source(self.c, self.parts, self.owners, 1)
        self.assertIn(f'import {independent.OLD}.Part0 as P0', source)
        self.assertNotIn(f'import {independent.OLD}.Part1', source)
        self.assertIn('importShape : importStates imports ≡ I1.imports', source)
        self.assertIn('importShape : importStates imports ≡ I2.imports', source)
        self.assertIn('importShape (importStates-sound imports)', source)
        self.assertIn('selectExport (importKeys', source)
        self.assertIn('P1.export', source)
        self.assertIn('Guarantees (Rules.game six) white (lowerGoal 4)', source)
        self.assertEqual(source.count('importKeys :'), 1)

    def test_false_leaf_and_missing_citation_have_empty_imports(self):
        sources = independent.negative_sources()
        self.assertEqual(len(sources), 2)
        for text in sources.values():
            self.assertIn('lowerTransport6 tip', text)
            self.assertIn('rejected = refl {x = true}', text)
            self.assertIn('--safe --without-K --cubical-compatible', text)
        self.assertIn(compact.pack_state('w'+'1'*36)+'L', sources[independent.DIRECTORY+'/FalseTerminal.agda'])
        self.assertIn(compact.pack_state('w'+'2'*36)+'K', sources[independent.DIRECTORY+'/MissingCitation.agda'])

    def test_scope_or_resource_error_is_not_a_successful_negative(self):
        record = dict(accepted=False, exit_code=42, stop_reason=None)
        text = '''error: [UnequalTerms]
true and false are not equal at type Bool
checkFrom keyed6 Fast.fastGame6 white (lowerGoal 4)
'''
        self.assertTrue(independent.negative_ok(record, text, [], []))
        self.assertFalse(independent.negative_ok(record, text, ['own.agdai'], []))
        self.assertFalse(independent.negative_ok(record, text, [], ['changed']))
        self.assertFalse(independent.negative_ok(dict(record, stop_reason='rss-limit'), text, [], []))
        self.assertFalse(independent.negative_ok(record, text.replace('false', 'true'), [], []))
        self.assertFalse(independent.negative_ok(record, text+'error: [NotInScope]', [], []))

    def collector_fixture(self):
        entries = []
        for index in range(118):
            n, digits = index, []
            for _ in range(36):
                n, digit = divmod(n, 3)
                digits.append(str(digit))
            state = 'b'+''.join(digits)
            entries.append(dict(state=state, certificate='L', references=[]))
        for entry in entries[114:]:
            entry.update(certificate='R0;', references=[entries[0]['state']])
        owners = {entry['state']: index for index, entry in enumerate(entries)}
        return independent.collector_source(entries[-1]['state'], [[entry] for entry in entries], owners, 114)

    def test_coverage_replacement_keeps_actual_imports_and_goal(self):
        original = self.collector_fixture()
        patched = coverage_source(original)
        self.assertEqual(re.findall(r'^  imports = (.*)$', patched, re.M),
                         re.findall(r'^  imports = (.*)$', original, re.M))
        self.assertNotIn('importShape', patched)
        self.assertEqual(patched.count('coverage = refl {x = true}'), 4)
        self.assertEqual(patched.count('(importStates-sound imports) coverage'), 4)
        self.assertEqual(patched.split('\nposition :')[1], original.split('\nposition :')[1])

    def test_malformed_citation_proof_template_fails_closed(self):
        original = self.collector_fixture()
        with self.assertRaises(ValueError):
            coverage_source(original.replace('importShape = refl {x = I115.imports}', 'importShape = refl'))


if __name__ == '__main__':
    unittest.main()
