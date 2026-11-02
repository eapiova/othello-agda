"""Guards for acyclic splits, checked literal imports and prefix provenance."""
import unittest
import os
from pathlib import Path
import tempfile

import part77_pilot6 as pilot


class Part77PilotTests(unittest.TestCase):
    def setUp(self):
        self.a = 'b' + '0' * 36
        self.b = 'b' + '0' * 35 + '1'
        self.c = 'b' + '0' * 35 + '2'
        self.part = [dict(state=self.b, certificate='L', references=[]),
                     dict(state=self.c, certificate='C0;L', references=[self.a, self.b])]
        self.owners = {self.a: 4, self.b: 77, self.c: 77}

    def test_split_redirects_only_local_earlier_citations(self):
        sources, pivot = pilot.split_sources(self.part, self.owners, 'upper')
        self.assertEqual(pivot, 1)
        self.assertIn('module Tests.GlobalPilot6.Part77Tail where', sources['Part77Tail'])
        self.assertIn('import Tests.GlobalPilot6.Part77Prefix as P77', sources['Part77Tail'])
        self.assertIn('import Tests.GlobalPilot6.Part4 as P4', sources['Part77Tail'])
        self.assertNotIn('import Tests.GlobalPilot6.Part78', sources['Part77Tail'])
        self.assertIn('accepted = refl', sources['Part77Tail'])
        self.assertIn('merge-all A.states B.states A.sound B.sound', sources['Part77Split'])

    def test_literal_imports_require_full_checked_state_coverage(self):
        sources = pilot.thin_sources(self.part, self.owners, 'upper')
        imports, checker = sources['Part77ThinImports'], sources['Part77Thin']
        self.assertIn('covered keyed6 P4.states states4 ≡ true', imports)
        self.assertIn('covered4 = refl', imports)
        self.assertIn('P4.states states4 P4.sound covered4', imports)
        self.assertNotIn('states77 :', imports)
        self.assertIn('imports = Thin.exports', checker)
        self.assertIn('accepted = refl', checker)
        self.assertIn('shardBy-sound', checker)
        self.assertNotIn('selectExport', checker)
        self.assertNotIn('postulate', imports + checker)

    def test_lower_bound_is_kept_in_literal_import_soundness(self):
        sources = pilot.thin_sources(self.part, self.owners, 'lower')
        self.assertIn('Fast.fastGame6 white (lowerGoal 4)', sources['Part77ThinImports'])
        self.assertIn('lowerTransport6', sources['Part77Thin'])

    def test_split_rejects_an_unisolatable_or_wrong_part(self):
        with self.assertRaises(ValueError):
            pilot.split_sources(self.part[1:], self.owners, 'upper')
        with self.assertRaises(ValueError):
            pilot.split_sources(self.part, {**self.owners, self.b: 76}, 'upper')

    def test_noncontiguous_or_unpreserved_prefix_is_rejected(self):
        r = dict(format='othello-memory-repair6-v1', status='part-failed', accepted=False,
                 compacting_gc=True, preserved_sources_unchanged=True,
                 preserved_interfaces_unchanged=True,
                 parts=[dict(index=i, accepted=i < 77) for i in range(78)])
        pilot.validate_prefix(r)
        for change in (dict(parts=r['parts'][:-1]), dict(compacting_gc=False),
                       dict(preserved_interfaces_unchanged=False)):
            with self.assertRaises(ValueError):
                pilot.validate_prefix({**r, **change})
        r['parts'][45]['accepted'] = False
        with self.assertRaises(ValueError):
            pilot.validate_prefix(r)

    def test_adapter_source_replacement_preserves_immutable_donor(self):
        with tempfile.TemporaryDirectory() as tmp:
            original, replacement = Path(tmp) / 'original', Path(tmp) / 'replacement'
            original.write_text('old failed body')
            os.link(original, replacement)
            pilot.replace_link(replacement, 'checked adapter')
            self.assertEqual(original.read_text(), 'old failed body')
            self.assertEqual(replacement.read_text(), 'checked adapter')
            self.assertNotEqual(original.stat().st_ino, replacement.stat().st_ino)


if __name__ == '__main__':
    unittest.main()
