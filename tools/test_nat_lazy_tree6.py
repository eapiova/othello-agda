"""Cheap source-contract tests; safe Agda alone supplies proof acceptance."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import nat_lazy_tree6 as lazy
import nat_tree_assembly6 as tree


class UniformLazyTree(unittest.TestCase):
    def arguments(self, side):
        return dict(sizes=[2, 1, 1], dependencies={0: [0], 1: [0, 1], 2: [1, 2]},
                    body_texts=['LL', 'K0;', 'K5F;'], root_packed='wQQQQQQQQQQQQ',
                    state_prefix='Tests.TreeMini' + side.title() + 'States',
                    prefix='Tests.TreeMini' + side.title(), cut_depth=1, side=side)

    def test_both_directions_preserve_assembly_and_root_contract(self):
        for side in ('lower', 'upper'):
            with self.subTest(side=side), tempfile.TemporaryDirectory() as tmp:
                check, baseline = Path(tmp) / 'lazy', Path(tmp) / 'old'
                args = self.arguments(side)
                for j, n in enumerate(args['sizes']):
                    lazy.emit_state_text(check, args['state_prefix'], j, n, 'b000000000000' * n)
                state_files = {p: p.read_bytes() for p in check.rglob('*.agda')}
                old = tree.generate(baseline, **args)
                result = lazy.generate(check, **args)
                self.assertTrue(result['uniform_lazy'])
                self.assertFalse(result['initial_problem2_proved'])
                self.assertFalse(result['optimal_initial_pair_proved'])
                self.assertFalse(result['production_authorized'])
                self.assertEqual(old['targets'], result['targets'])
                self.assertEqual(old['rows'], result['rows'])
                self.assertEqual(old['hierarchy_nodes'], result['hierarchy_nodes'])
                raw_files = {}
                for relative, digest in result['generated_sha256'].items():
                    raw = (check / relative).read_bytes()
                    raw_files[relative] = raw
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                    text = raw.decode()
                    before = (baseline / relative).read_text()
                    stem = Path(relative).stem
                    self.assertNotRegex(text, r'S[0-9]+\.states')
                    self.assertNotIn('RepairBridge', text)
                    self.assertNotIn('postulate', text)
                    self.assertIn('--safe --without-K --cubical-compatible', text)
                    if stem == 'Family':
                        player, goal, transport = (('white', 'lowerGoal', 'lowerTransport6')
                            if side == 'lower' else ('black', 'upperGoal', 'upperTransport6'))
                        self.assertTrue(text.startswith(before))
                        self.assertIn(f'module L = Lazy.Checking Fast.fastGame6 {player} ({goal} 4) {transport}', text)
                    elif stem.startswith('Part') and not stem.startswith('PartData'):
                        expected = before.replace('Family.A.Lower.checkPart', 'Family.L.checkPart').replace(
                            'Family.A.linkedAligned', 'Family.L.linkedAligned')
                        self.assertEqual(text, expected)
                        self.assertIn('Family.A.Partial G C Data.states', text)
                    elif stem.startswith('PartData') or stem.startswith('Data'):
                        expected = before
                        for j, n in enumerate(args['sizes']):
                            expected = expected.replace(f'S{j}.states', f'(Lazy.states {n} S{j}.text)')
                        if expected != before:
                            expected = expected.replace('open import Prelude\n',
                                'open import Prelude\n' + lazy.LAZY_IMPORT, 1)
                        self.assertEqual(text, expected)
                    else:
                        # BodyData, hierarchy join proofs, routes and original-rule
                        # completion/transfer are byte-for-byte unchanged.
                        self.assertEqual(raw, (baseline / relative).read_bytes())
                self.assertEqual(result['generated_bytes'], sum(map(len, raw_files.values())))
                for p, raw in state_files.items():
                    self.assertEqual(p.read_bytes(), raw)
                snapshot = {p: p.read_bytes() for p in check.rglob('*') if p.is_file()}
                with self.assertRaises(ValueError):
                    lazy.generate(check, **args)
                self.assertEqual(snapshot, {p: p.read_bytes() for p in check.rglob('*') if p.is_file()})

    def test_state_modules_are_only_compact_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            result = lazy.emit_state_text(check, 'Tests.TreeMiniLowerStates', 511, 200,
                                          'wQQQQQQQQQQQQ' * 200)
            relative, digest = next(iter(result['generated_sha256'].items()))
            raw = (check / relative).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            self.assertEqual(len(raw), result['generated_bytes'])
            text = raw.decode()
            self.assertIn('text : String', text)
            self.assertNotIn('State six', text)
            self.assertNotIn('states =', text)
            self.assertNotIn('import Othello.', text)
            self.assertEqual(text.count('import '), 1)
            with self.assertRaises(ValueError):
                lazy.emit_state_text(check, 'Tests.TreeMiniLowerStates', 511, 200, 'wQQQQQQQQQQQQ' * 200)
            self.assertEqual((check / relative).read_bytes(), raw)

    def test_optional_recursion_preserves_every_nonroot_source(self):
        for side in ('lower', 'upper'):
            with self.subTest(side=side), tempfile.TemporaryDirectory() as tmp:
                baseline, changed = Path(tmp) / 'old', Path(tmp) / 'new'
                args = self.arguments(side)
                old = lazy.generate(baseline, **args)
                new = lazy.generate(changed, **args, lazy_accessibility=True)
                self.assertNotIn('lazy_accessibility', old)
                self.assertTrue(new['lazy_accessibility'])
                for name, digest in old['generated_sha256'].items():
                    if Path(name).stem != 'Root':
                        self.assertEqual(digest, new['generated_sha256'][name])
                        self.assertEqual((baseline / name).read_bytes(), (changed / name).read_bytes())
                    else:
                        original = (baseline / name).read_text()
                        root = (changed / name).read_text()
                        self.assertEqual(root, lazy.with_lazy_accessibility(original, side=side))
                        self.assertIn('Rec.Checking.global-proven', root)
                        self.assertIn('G C rows', root)
                        for bad in (root, original.replace('provenAt =', 'renamed =')):
                            with self.assertRaises(ValueError):
                                lazy.with_lazy_accessibility(bad, side=side)
                for flag in (None, 1, 'true'):
                    fresh = Path(tmp) / ('invalid-' + str(flag))
                    with self.assertRaises(ValueError):
                        lazy.generate(fresh, **args, lazy_accessibility=flag)
                    self.assertFalse(fresh.exists())

    def test_unsafe_or_malformed_input_creates_nothing(self):
        cases = [('../Tests.Bad', 0, 1, 'b000000000000'),
                 ('Tests.Bad/Path', 0, 1, 'b000000000000'),
                 ('Tests..Bad', 0, 1, 'b000000000000'),
                 ('Tests.Bad', -1, 1, 'b000000000000'),
                 ('Tests.Bad', 512, 1, 'b000000000000'),
                 ('Tests.Bad', 0, 201, 'b000000000000' * 201),
                 ('Tests.Bad', 0, True, 'b000000000000'),
                 ('Tests.Bad', 0, 2, 'b000000000000'),
                 ('Tests.Bad', 0, 1, 'bRRRRRRRRRRRR'),
                 ('Tests.Bad', 0, 1, 'b00000000000"'),
                 ('Tests.Bad', 0, 1, 'b00000000000\\')]
        with tempfile.TemporaryDirectory() as tmp:
            for prefix, j, n, text in cases:
                with self.subTest(prefix=prefix, j=j, n=n, text=text):
                    with self.assertRaises(ValueError):
                        lazy.emit_state_text(Path(tmp), prefix, j, n, text)
            self.assertEqual(list(Path(tmp).iterdir()), [])
            for changes in ({'prefix': '../Unsafe'}, {'body_texts': ['L"', 'L', 'L']},
                            {'root_packed': 'bRRRRRRRRRRRR'}, {'sizes': [201]},
                            {'prefix': 'Tests.TreeMiniLowerStates'}):
                args = self.arguments('lower')
                args.update(changes)
                with self.assertRaises(ValueError):
                    lazy.generate(Path(tmp), **args)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_fresh_source_and_symlink_refusal_preserve_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            args = self.arguments('lower')
            folder = check / 'src' / args['prefix'].replace('.', '/')
            folder.mkdir(parents=True)
            fixture = folder / 'Part99.agda'
            fixture.write_bytes(b'preexisting fixture\n')
            with self.assertRaises(ValueError):
                lazy.generate(check, **args)
            self.assertEqual(fixture.read_bytes(), b'preexisting fixture\n')
            fixture.unlink()
            folder.rmdir()
            folder.symlink_to(check, target_is_directory=True)
            with self.assertRaises(ValueError):
                lazy.generate(check, **args)
            with self.assertRaises(ValueError):
                lazy.emit_state_text(check, args['prefix'], 0, 1, 'b000000000000')
            self.assertTrue(folder.is_symlink())

    def test_existing_interface_root_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            args = self.arguments('upper')
            cache = check / '_build/2.8.0/agda/src' / args['prefix'].replace('.', '/')
            cache.mkdir(parents=True)
            fixture = cache / 'Root.agdai'
            fixture.write_bytes(b'old cache')
            with self.assertRaises(ValueError):
                lazy.generate(check, **args)
            self.assertEqual(fixture.read_bytes(), b'old cache')
            self.assertFalse((check / 'src').exists())


if __name__ == '__main__':
    unittest.main()
