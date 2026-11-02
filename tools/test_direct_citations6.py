"""Owner hints must not remove, assume or alter any citation proof."""
import unittest

import direct_citations6 as direct
import independent_lower6 as independent


class DirectCitationsTests(unittest.TestCase):
    def fixture(self):
        entries = []
        for i in range(118):
            n, digits = i, []
            for _ in range(36):
                n, digit = divmod(n, 3)
                digits.append(str(digit))
            entries.append(dict(state='b'+''.join(digits), certificate='L', references=[]))
        for i in range(114, 118):
            entries[i].update(certificate='R0;', references=[entries[i-1]['state'], entries[0]['state']])
        return [[e] for e in entries], {e['state']: i for i, e in enumerate(entries)}

    def test_actual_exports_discharge_all_literal_imports(self):
        parts, owners = self.fixture()
        root = parts[-1][0]['state']
        text, stats = direct.root_source(root, parts, owners)
        self.assertEqual([r['part'] for r in stats], [114, 115, 116, 117])
        self.assertEqual([r['owners'] for r in stats], [[0, 113], [0, 114], [0, 115], [0, 116]])
        self.assertEqual(text.count('coverage = refl {x = true}'), 4)
        self.assertEqual(text.count('sources hints I'), 8)
        self.assertNotIn('importStates', text)
        self.assertNotIn('selectExport', text)
        self.assertEqual(text.split('\nposition :')[1],
                         independent.collector_source(root, parts, owners, 114).split('\nposition :')[1])
        self.assertIn('P114.export', text)
        self.assertIn('I114.sound', text)

    def test_forward_owner_is_rejected_by_generator(self):
        parts, owners = self.fixture()
        parts[114][0]['references'] = [parts[117][0]['state']]
        with self.assertRaises(ValueError):
            direct.root_source(parts[-1][0]['state'], parts, owners)

    def test_hint_soundness_uses_full_state_membership(self):
        text = direct.helper_source()
        self.assertIn('knownIn k (exportStates e) s', text)
        self.assertIn('knownIn-sound k g p goal (exportStates e) s (exportSound e) accepted', text)
        self.assertIn('coveredBy k es tip (node m l r) = false', text)
        self.assertIn('ownerKnown k [] i s = false', text)
        self.assertNotIn('postulate', text)
        self.assertIn('--safe --without-K --cubical-compatible', text)

    def test_fixtures_include_wrong_owner_collisions_and_omissions(self):
        text = direct.fixture_source()
        for name in ('good', 'proved', 'wrong-owner', 'missing-owner', 'collision', 'omitted-branch', 'empty'):
            self.assertIn(name+' :', text)


if __name__ == '__main__':
    unittest.main()
