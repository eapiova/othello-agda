"""A repair may change only the unchecked proof and add checked bridges."""
from pathlib import Path
import tempfile
import unittest

from nat_lazy_generator6 import PREFIX, expressions, generate, parse_map


class Generator(unittest.TestCase):
    def test_sparse_map_bridge_has_the_original_shape(self):
        node = parse_map('(M.branch 200 (M.rows 0 200 S0.states) (M.branch 48400 M.absent (M.rows 48400 200 S242.states)))')
        fast, equality, deps = expressions(node)
        self.assertEqual(deps, {0, 242})
        self.assertIn('Lazy.states 200 S242.text', fast)
        self.assertIn('cong (M.rows 48400 200) E242.same', equality)
        self.assertEqual(equality.count('branchEqual'), 2)

    def test_bad_map_grammar_is_rejected(self):
        for text in ('', 'M.absent junk', '(M.rows 0 200 S0.states',
                     '(M.branch x M.absent M.absent)', '(M.rows 0 n S0.states)',
                     '(M.rows 0 200 arbitrary)', 'M.absent;'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_map(text)

    def test_only_the_next_unchecked_part_can_change(self):
        with self.assertRaises(ValueError):
            generate(Path('/unused'), 241, accepted_parts=242)

    def test_generated_repair_preserves_conditional_export_and_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            folder = check / 'src' / PREFIX.replace('.', '/')
            folder.mkdir(parents=True)
            states = check / 'src/Tests/IndexedWire6'
            states.mkdir(parents=True)
            for j in (0, 242):
                (states / f'StateData{j}.agda').write_text('states : B.Vec (State six) 200\nstates = original\n')
            data = '''import Tests.IndexedWire6.StateData0 as S0
import Tests.IndexedWire6.StateData242 as S242
demand = (M.branch 48400 (M.rows 0 200 S0.states) (M.rows 48400 200 S242.states))
'''
            (folder / 'PartData242.agda').write_text(data)
            old = '''{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.NatDescendant6.Part242 where

open import Prelude
import Tests.NatDescendant6.Family as Family
import Tests.NatDescendant6.PartData242 as Data
import Tests.IndexedWire6.StateData242 as S242
import Tests.NatDescendant6.BodyData242 as C242
embed i = 48400 + B.finToNat i
abstract
  accepted : oldCheck ≡ true
  accepted = refl
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned Data.demand G → Laws.Aligned Data.states G → Laws.Aligned Data.bodies C →
    Family.A.Partial G C Data.states
  linked = originalLink
'''
            (folder / 'Part242.agda').write_text(old)
            untouched = {p: p.read_bytes() for p in check.rglob('*.agda') if p.name != 'Part242.agda'}
            result = generate(check, 242, accepted_parts=242)
            repaired = (folder / 'Part242.agda').read_text()
            signature = old.split('  linked : ', 1)[1].split('\n  linked = ', 1)[0]
            self.assertIn('  linked : ' + signature + '\n', repaired)
            self.assertIn('Bridge.link {n = 200}', repaired)
            bridge = (folder / 'RepairBridge.agda').read_text()
            self.assertIn('subst (Family.A.Partial G C) statesEqual', bridge)
            self.assertIn('sym demandEqual', bridge)
            self.assertEqual(result['dependencies'], [0, 242])
            self.assertTrue(result['exported_linked_type_unchanged'])
            self.assertEqual(result['targets'][-1], PREFIX + '.Part242')
            for path, raw in untouched.items():
                self.assertEqual(path.read_bytes(), raw)
            self.assertIn('same = refl', (folder / 'StateEq242.agda').read_text())
            with self.assertRaises(ValueError):
                generate(check, 242, accepted_parts=242)


if __name__ == '__main__':
    unittest.main()
