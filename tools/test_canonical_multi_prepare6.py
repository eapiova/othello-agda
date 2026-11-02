"""Static offline preparation tests; no Agda, solver, SSH, or worker runs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from canonical_multi_prepare6 import prepare
from test_new_row_bridge6 import fixture


def multi_fixture():
    full, sample = fixture()
    text = sample['states'][1]['text']
    sample['cases'].append(dict(part=1, rows=200, state_text=text,
        body_text='L;'*200, references=[], dependencies=[1], tokens=200))
    sample['cases'].sort(key=lambda c: c['part'])
    sample['selected'] = [1, 2]
    return full, sample


class CanonicalMultiPreparation(unittest.TestCase):
    def inputs(self, root, change=None):
        full, sample = multi_fixture()
        if change:
            change(full, sample)
        paths = root/'sample.json', root/'full.json'
        for path, value in zip(paths, (sample, full)):
            path.write_text(json.dumps(value, sort_keys=True))
        pins = dict(expected_sample_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                    expected_full_sha256=hashlib.sha256(paths[1].read_bytes()).hexdigest())
        return paths, pins

    def test_deterministic_layout_exact_hashes_and_import_only_joint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, pins = self.inputs(root)
            before = [p.read_bytes() for p in paths]
            a = prepare(*paths, parts=[2, 1], output=root/'a', prefix='Tests.MultiFixture', **pins)
            b = prepare(*paths, parts=[1, 2], output=root/'b', prefix='Tests.MultiFixture', **pins)
            self.assertEqual(a, b)
            self.assertEqual(before, [p.read_bytes() for p in paths])
            self.assertEqual(a['parts'], [1, 2])
            self.assertEqual(a['selected_rows'], 201)
            self.assertEqual(a['distinct_demanded_state_chunks'], 2)
            self.assertTrue(a['partial_only'])
            self.assertTrue(a['joint_target_is_import_only'])
            for flag in ('agda_checked', 'production_authorized', 'initial_problem2_proved',
                         'optimal_initial_pair_proved', 'combined_body_map_coverage_proved'):
                self.assertFalse(a[flag])
            files = {p.relative_to(root/'a').as_posix(): p.read_bytes()
                     for p in (root/'a').rglob('*') if p.is_file()}
            self.assertEqual(set(files), set(a['generated_sha256']) | {'manifest.json'})
            for name, digest in a['generated_sha256'].items():
                self.assertEqual(hashlib.sha256(files[name]).hexdigest(), digest)
                self.assertEqual(files[name], (root/'b'/name).read_bytes())
                if name.endswith('.agda'):
                    header = files[name].splitlines()[0]
                    self.assertTrue(header.startswith(b'{-# OPTIONS ') and header.endswith(b'#-}'))
                    for option in (b'--safe', b'--without-K', b'--cubical-compatible'):
                        self.assertIn(option, header.split())
                    self.assertNotIn('/StateData', name)
            joint = files[a['joint_target']].decode()
            self.assertIn('import Tests.MultiFixture.Bridge1.Root as Part1', joint)
            self.assertIn('import Tests.MultiFixture.Bridge2.Root as Part2', joint)
            self.assertNotIn('partial :', joint)
            self.assertNotIn('open import', joint)
            for item in a['layouts']:
                self.assertEqual(item['row_layout']['emitted_state_chunks'], 0)
                self.assertEqual(item['bridge_layout']['new_boolean_rows'], 0)
                self.assertFalse(item['bridge_layout']['agda_checked'])
            self.assertEqual(json.loads(files['manifest.json']), json.loads(json.dumps(a)))

    def test_refuses_bad_inputs_before_requested_output(self):
        changes = [lambda f,s:s.update(wire_sha256='b'*64),
                   lambda f,s:s.update(wire_rows=400),
                   lambda f,s:f.update(complete=False),
                   lambda f,s:f['chunks'].pop(0),
                   lambda f,s:f['chunks'][0].update(rows=199),
                   lambda f,s:f['chunks'][0].update(module='Tests.Bad;evil'),
                   lambda f,s:f['chunks'][0].update(text_sha256='invalid'),
                   lambda f,s:s['states'][1].update(rows=199),
                   lambda f,s:s['cases'][0].update(dependencies=[1,1]),
                   lambda f,s:s['cases'][0].update(body_text='invalid literal'),
                   lambda f,s:s['cases'][1].update(rows=200)]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                paths, pins = self.inputs(root, change)
                with self.assertRaises((ValueError, KeyError)):
                    prepare(*paths, parts=[1, 2], output=root/'out', **pins)
                self.assertFalse((root/'out').exists())

    def test_part_selection_namespace_and_pin_refusals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, pins = self.inputs(root)
            for parts in ([], [0], [-1], [True], [1,1], [3], list(range(1,18))):
                with self.subTest(parts=parts), self.assertRaises(ValueError):
                    prepare(*paths, parts=parts, output=root/'out', **pins)
                self.assertFalse((root/'out').exists())
            for prefix in ('Bad;module', 'Tests.FixtureFull', 'Tests.'+'A'*150):
                with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                    prepare(*paths, parts=[1], output=root/'out', prefix=prefix, **pins)
            for key in pins:
                wrong = dict(pins); wrong[key] = '0'*64
                with self.subTest(key=key), self.assertRaises(ValueError):
                    prepare(*paths, parts=[1], output=root/'out', **wrong)
                self.assertFalse((root/'out').exists())

    def test_refuses_existing_output_and_symlinks_preserving_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, pins = self.inputs(root)
            accepted = root/'accepted'; accepted.mkdir()
            cache = accepted/'Keep.agdai'; cache.write_bytes(b'accepted')
            with self.assertRaises(ValueError):
                prepare(*paths, parts=[1], output=accepted, **pins)
            self.assertEqual(cache.read_bytes(), b'accepted')
            link = root/'linked'; link.symlink_to(accepted, target_is_directory=True)
            for out in (link, link/'fresh'):
                with self.subTest(output=out), self.assertRaises(ValueError):
                    prepare(*paths, parts=[1], output=out, **pins)
            broken = root/'broken'; broken.symlink_to(root/'absent')
            with self.assertRaises(ValueError):
                prepare(*paths, parts=[1], output=broken, **pins)
            sample_link = root/'sample-link'; sample_link.symlink_to(paths[0])
            with self.assertRaises(ValueError):
                prepare(sample_link, paths[1], parts=[1], output=root/'out', **pins)
            self.assertFalse((root/'out').exists())


if __name__ == '__main__':
    unittest.main()
