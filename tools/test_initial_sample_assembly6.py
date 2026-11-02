#!/usr/bin/env python3
"""Light generator checks; does not invoke Agda or accept any proof."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from initial_sample_assembly6 import emit


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.args = dict(side='lower', sample_prefix='Tests.InitialLazyTrainingLower',
                         parts=list(range(16)), sizes=[200] * 16)

    def tearDown(self):
        self.temp.cleanup()

    def generate(self, **changes):
        return emit(self.root, **(self.args | changes))

    def test_structure_and_metadata(self):
        meta = self.generate()
        self.assertEqual(meta['targets'], ['Stage4', 'Stage8', 'Stage16'])
        self.assertEqual([s['rows'] for s in meta['stages']], [800, 1600, 3200])
        total = 0
        for relative, digest in meta['generated_sha256'].items():
            raw = (self.root / relative).read_bytes()
            total += len(raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            text = raw.decode()
            self.assertIn('--safe --without-K --cubical-compatible', text)
            self.assertIn('abstract\n  linked :', text)
            self.assertIn('Family.A.join {G = G} {C = C}', text)
            self.assertIn('Laws.Aligned P0.demand G', text)
            self.assertNotIn('accepted =', text)
            self.assertNotIn('postulate', text)
            self.assertNotIn('BodyData', text)
        self.assertEqual(total, meta['generated_bytes'])
        stage4 = (self.root / 'src/Tests/InitialSampleAssembly6/Stage4.agda').read_text()
        self.assertNotIn('Part4 as', stage4)
        self.assertIn('M.branch 400', stage4)
        self.assertFalse(meta['agda_checked'])
        self.assertFalse(meta['complete_initial_bound_measured'])

    def test_invalid_inputs_leave_no_sources(self):
        cases = [dict(parts=[1, 1], sizes=[1, 1]), dict(parts=[2, 1], sizes=[1, 1]),
                 dict(parts=[40000], sizes=[1]), dict(parts=[-1], sizes=[1]),
                 dict(parts=[True], sizes=[1]), dict(parts=[], sizes=[]),
                 dict(parts=list(range(17)), sizes=[1]*17), dict(sizes=[0]*16),
                 dict(sizes=[201]*16), dict(sizes=[1]), dict(prefix='../bad'),
                 dict(sample_prefix='Tests.InitialLazyTrainingUpper'), dict(side='both'),
                 dict(prefix='Tests.InitialLazyTrainingLower.Assembly')]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(Exception):
                self.generate(**case)
            self.assertFalse((self.root / 'src').exists())

    def test_overwrite_and_cache_interface_guards(self):
        self.generate()
        with self.assertRaises(Exception):
            self.generate()
        prefix = 'Tests.OtherAssembly'
        interface = self.root / '_build/2.8/agda/src/Tests/OtherAssembly'
        interface.mkdir(parents=True)
        with self.assertRaises(Exception):
            self.generate(prefix=prefix)

    def test_symlink_and_cache_root_guards(self):
        link = self.root / 'link'
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(Exception):
            emit(link, **self.args)
        src = self.root / 'src'
        src.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(Exception):
            self.generate()
        with self.assertRaises(Exception):
            emit(self.root / 'privatecache/new', **self.args)

    def test_single_upper_sparse_part(self):
        meta = self.generate(side='upper', sample_prefix='Tests.InitialLazyTrainingUpper',
                             parts=[39999], sizes=[1])
        self.assertEqual(meta['targets'], ['Stage1'])
        source = (self.root / 'src/Tests/InitialSampleAssembly6/Stage1.agda').read_text()
        self.assertIn('states = P39999.states', source)
        self.assertIn('(P39999.linked G C demand sameStates sameBodies)', source)


if __name__ == '__main__':
    unittest.main()
