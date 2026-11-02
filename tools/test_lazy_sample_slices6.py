#!/usr/bin/env python3
"""Light rank/boundary, raw-row integrity, and fail-closed generator checks."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import lazy_sample_slices6 as slices
import native_layout_samples6 as native
import test_native_layout_samples6 as fixtures


class Slices(unittest.TestCase):
    def write(self, root, items):
        path = root / 'sample.jsonl'
        path.write_text(''.join(json.dumps(item) + '\n' for item in items), encoding='ascii')
        return path

    def boundary_fixture(self):
        p = 39999
        states = [('b' if r % 2 == 0 else 'w') + ('0' if r % 2 == 0 else '1')*12
                  for r in range(151)]
        rows = [dict(kind='row', part=p, row=r, state=state, body='K',
                     references=[200*p+r-1 if r else 0]) for r, state in enumerate(states)]
        return rows + [dict(kind='states', part=0, rows=1, text='b'+'0'*12),
                       dict(kind='states', part=p, rows=151, text=''.join(states)),
                       dict(kind='complete', parts=40000, records=40150, tokens=40150,
                            selected_rows=151, record_cap=8000000, output_limit_bytes=1024**2,
                            max_entries=200, max_tokens=32000, selected=[p])]

    def test_original_rank_boundaries_and_exact_row_bodies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            items = self.boundary_fixture()
            report = slices.emit(root/'check', self.write(root, items), side='upper')
            self.assertEqual([s['slice_base'] for s in report['slices']],
                             [7999800, 7999850, 7999900, 7999950])
            self.assertEqual([s['rows'] for s in report['slices']], [50, 50, 50, 1])
            folder = root/'check/src/Tests/InitialSlices6'
            family = (folder/'Family.agda').read_text()
            self.assertIn('Fast.fastGame6 black (upperGoal 4) upperTransport6', family)
            self.assertEqual((folder/'StateData39999.agda').read_text().split('text = "')[1].split('"')[0],
                             items[-2]['text'])
            for meta in report['slices']:
                own = items[meta['start_offset']:meta['start_offset']+meta['rows']]
                source = (folder/(meta['target']+'.agda')).read_text()
                self.assertIn(f'embed i = {meta["slice_base"]} + B.finToNat i', source)
                self.assertIn(f'linkedAligned {{n = {meta["rows"]}}} {meta["slice_base"]}', source)
                self.assertIn('M.rows 7999800 151 (Lazy.states 151 S39999.text)', source)
                self.assertEqual(source.split('ownSliceText = "')[1].split('"')[0],
                                 ''.join(row['state'] for row in own))
                body_file = folder/f'BodyData39999X{meta["start_offset"]}.agda'
                encoded = body_file.read_text().split('text = "')[1].split('"')[0]
                self.assertEqual(encoded, ''.join(native.convert_body(row['body'], row['references'])[0]
                                                  for row in own))
                self.assertEqual(meta['references'], [r for row in own for r in row['references']])
            self.assertEqual(report['slices'][1]['references'][0], 7999849)
            for relative, digest in report['generated_sha256'].items():
                self.assertEqual(hashlib.sha256((root/'check'/relative).read_bytes()).hexdigest(), digest)
            self.assertFalse(report['production_authorized'])

    def test_small_fixture_lower_and_custom_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = slices.emit(root/'check', self.write(root, fixtures.Samples().fixture()),
                                 side='lower', rows_per_slice=1)
            self.assertEqual([m['slice_base'] for m in report['slices']], [200, 201])
            self.assertEqual([m['tokens'] for m in report['slices']], [3, 3])
            self.assertEqual(report['slices'][1]['dependencies'], [1])

    def test_missing_malformed_rows_states_refs_selection(self):
        base = fixtures.Samples().fixture()
        variants = [base[:-1], base[1:], [*base[:2], *base[3:]], [base[0], base[0], *base[1:]]]
        for index, key, value in [(0,'row',1), (0,'state','x'+'0'*12),
                                  (0,'references',[200,1]), (0,'references',[0]),
                                  (0,'body','LL'), (2,'text','b'+'0'*11),
                                  (4,'selected',[0]), (4,'selected',[1,1])]:
            changed = copy.deepcopy(base)
            changed[index][key] = value
            variants.append(changed)
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.assertRaises(ValueError):
                    slices.emit(root/'check', self.write(root, variant), side='lower')
                self.assertFalse((root/'check/src').exists())

    def test_bounds_namespace_overwrite_cache_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write(root, fixtures.Samples().fixture())
            for options in [dict(prefix='Tests.12'), dict(prefix='../Escape'),
                            dict(rows_per_slice=51), dict(rows_per_slice=True), dict(side='other')]:
                args = dict(side='lower'); args.update(options)
                with self.assertRaises(ValueError): slices.emit(root/'check', path, **args)
            slices.emit(root/'check', path, side='lower')
            with self.assertRaises(ValueError): slices.emit(root/'check', path, side='lower')
            cache = root/'cached/_build/2.8/agda/src/Tests/InitialSlices6'
            cache.mkdir(parents=True)
            with self.assertRaises(ValueError): slices.emit(root/'cached', path, side='lower')
            (root/'alias').symlink_to(root/'check', target_is_directory=True)
            with self.assertRaises(ValueError):
                slices.emit(root/'alias', path, side='lower', prefix='Tests.Fresh6')
            (root/'oversized').write_bytes(b' '* (slices.MAX_BYTES+1))
            with self.assertRaises(ValueError): slices.emit(root/'fresh', root/'oversized', side='lower')

    def test_validated_case_and_reread_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write(root, fixtures.Samples().fixture())
            decoded = native.decode_samples(path)
            decoded['cases'][0]['body_text'] = 'L'
            with patch.object(native, 'decode_samples', return_value=decoded):
                with self.assertRaises(ValueError): slices.emit(root/'check', path, side='lower')
            self.assertFalse((root/'check/src').exists())


if __name__ == '__main__': unittest.main()
