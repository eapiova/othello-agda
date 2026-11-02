"""Bounded source integrity tests; these do not assert Agda acceptance."""
import copy
import hashlib
from pathlib import Path
import re
import tempfile
import unittest

from initial_global_direct6 import emit
from initial_global_named6 import emit as emit_named
from lazy_sample_parts6 import emit as emit_samples
from test_initial_global_alignment6 import fixture, PREFIX

NAMED = 'Tests.InitialGlobalNamed6'
DIRECT = 'Tests.InitialGlobalDirect6'


class GlobalDirect(unittest.TestCase):
    def prepare(self, check, side='lower'):
        data = fixture()
        emit_samples(check, data, side=side, prefix=PREFIX)
        layout = emit_named(check, side=side, sample=data, sample_prefix=PREFIX,
                            route_batch=4, map_batch=4)
        return data, layout

    def run_emit(self, check, data, layout, **kwargs):
        return emit(check, side=kwargs.pop('side', 'lower'), sample=data,
                    sample_prefix=PREFIX, named_layout=layout, **kwargs)

    def test_direct_fields_preserve_semantic_references_both_sides(self):
        for side in ('lower', 'upper'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data, layout = self.prepare(check, side)
                accepted = {p: p.read_bytes() for p in check.rglob('*.agda')}
                result = self.run_emit(check, data, layout, side=side)
                self.assertEqual(result['targets'], ['Part' + str(j) for j in layout['owned_parts']] + ['Root'])
                self.assertEqual(len(result['targets']), 17)
                self.assertEqual(result['owned_parts'], layout['owned_parts'])
                self.assertEqual(result['needed_chunks'], 17)
                self.assertEqual(result['named_prefix'], NAMED)
                for target in result['targets']:
                    path = check / 'src' / Path(*DIRECT.split('.')) / (target + '.agda')
                    direct = path.read_text()
                    baseline = (check / 'src' / Path(*NAMED.split('.')) / (target + '.agda')).read_text()
                    self.assertNotRegex(direct, r'^\s*module \w+ =', re.M)
                    self.assertNotRegex(direct, r'import ' + re.escape(NAMED) + r'\.(?:Part\d+|Root)\b')
                    self.assertIn('--safe --without-K --cubical-compatible', direct)
                    for banned in ('postulate', '?', '.complete', 'accepted = refl', 'Closed.partial'):
                        self.assertNotIn(banned, direct)
                    # Independently inline baseline alias declarations, then compare
                    # all expressions, types, map references and joins as full text.
                    if target != 'Root':
                        for alias, routes in re.findall(r'^  module (R\d+) = (Routes\d+)\.AlignedModel LookupStates sameStates$', baseline, re.M):
                            baseline = re.sub(r'\b' + alias + r'\.stateAligned(\d+)\b',
                                              lambda m: f'({routes}.AlignedModel.stateAligned{m[1]} LookupStates sameStates)', baseline)
                        self.assertIn('partial = P.linked LookupStates LookupBodies demandAligned', direct)
                        self.assertEqual(baseline.split('bodyRoute :')[1].split('module AlignedModel')[0],
                                         direct.split('bodyRoute :')[1].split('module AlignedModel')[0])
                    else:
                        for alias, part in re.findall(r'^  module (P\d+) = (Part\d+)\.AlignedModel LookupStates LookupBodies sameStates sameBodies$', baseline, re.M):
                            baseline = re.sub(r'\b' + alias + r'\.partial\b',
                                              f'({part}.AlignedModel.partial LookupStates LookupBodies sameStates sameBodies)', baseline)
                        baseline = baseline.replace('module Closed = AlignedModel G C\n  (Laws.self-compatible globalStates fallbackState)\n  (Laws.self-compatible globalBodies I.indexedLeaf)\n', '')
                        baseline = baseline.replace('partial = Closed.partial', 'partial = AlignedModel.partial G C\n    (Laws.self-compatible globalStates fallbackState)\n    (Laws.self-compatible globalBodies I.indexedLeaf)')
                        baseline = baseline.replace('import ' + NAMED + '.Part', 'import ' + DIRECT + '.Part')
                        self.assertEqual(direct.count('.AlignedModel.partial LookupStates LookupBodies sameStates sameBodies'), 16)
                    baseline = re.sub(r'^  module \w+ = .+\n', '', baseline, flags=re.M)
                    baseline = baseline.replace('module ' + NAMED + '.' + target, 'module ' + DIRECT + '.' + target)
                    baseline = baseline.replace('-- AI-assisted UNTRUSTED global sample named map.', '-- AI-assisted UNTRUSTED direct sample field applications.')
                    self.assertEqual(direct, baseline)
                for relative, digest in result['generated_sha256'].items():
                    self.assertEqual(hashlib.sha256((check / relative).read_bytes()).hexdigest(), digest)
                self.assertEqual(result['generated_bytes'], sum((check / p).stat().st_size for p in result['generated_sha256']))
                self.assertTrue(all(p.read_bytes() == raw for p, raw in accepted.items()))
                for flag in ('initial_problem2_proved', 'optimal_initial_pair_proved', 'production_authorized'):
                    self.assertIs(result[flag], False)
                with self.assertRaises(ValueError):
                    self.run_emit(check, data, layout, side=side)

    def test_malformed_layout_dependencies_and_source_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            data, layout = self.prepare(check)
            changes = [lambda x: x.update(format='wrong'), lambda x: x.update(side='upper'),
                       lambda x: x['owned_parts'].pop(), lambda x: x['needed_parts'].pop(),
                       lambda x: x['shards'][0]['needed_parts'].pop(),
                       lambda x: x['generated_sha256'].update({next(iter(x['generated_sha256'])): '0' * 64}),
                       lambda x: x.update(map_batch=True)]
            for change in changes:
                bad = copy.deepcopy(layout)
                change(bad)
                with self.assertRaises(ValueError):
                    self.run_emit(check, data, bad)
            bad_data = copy.deepcopy(data)
            bad_data['cases'][0]['dependencies'] = [55]
            with self.assertRaises(ValueError):
                self.run_emit(check, bad_data, layout)
            for relative in ('src/Tests/InitialLazyTrainingLower/StateData2.agda',
                             'src/Tests/InitialGlobalNamed6/Part10.agda',
                             'src/Tests/InitialGlobalNamed6/Model.agda'):
                path = check / relative
                raw = path.read_bytes()
                path.write_bytes(raw + b'\n-- mutation\n')
                with self.assertRaisesRegex(ValueError, 'source metadata mismatch'):
                    self.run_emit(check, data, layout)
                path.write_bytes(raw)
            self.assertFalse((check / 'src/Tests/InitialGlobalDirect6').exists())

    def test_private_imports_preserve_all_proof_declarations(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            data, layout = self.prepare(check)
            direct = self.run_emit(check, data, layout)
            for bad in (1, 'yes', None):
                with self.assertRaises(ValueError):
                    self.run_emit(check, data, layout, prefix='Tests.BadPrivate', private_imports=bad)
            private = self.run_emit(check, data, layout, prefix='Tests.PrivateDirect', private_imports=True)
            self.assertTrue(private['private_imports'])
            for target in direct['targets']:
                public = (check / 'src/Tests/InitialGlobalDirect6' / (target + '.agda')).read_text()
                hidden = (check / 'src/Tests/PrivateDirect' / (target + '.agda')).read_text()
                self.assertEqual(hidden.count('private\n'), 1)
                restored = hidden.replace('private\n', '', 1)
                restored = re.sub(r'^  ((?:open )?import .+)$', r'\1', restored, flags=re.M)
                restored = restored.replace('module Tests.PrivateDirect.', 'module Tests.InitialGlobalDirect6.')
                restored = restored.replace('import Tests.PrivateDirect.', 'import Tests.InitialGlobalDirect6.')
                self.assertEqual(restored, public)

    def test_module_using_lists_preserve_all_terms_without_new_modules(self):
        for side in ('lower', 'upper'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data, layout = self.prepare(check, side)
                direct = self.run_emit(check, data, layout, side=side)
                narrowed = self.run_emit(check, data, layout, side=side,
                    prefix='Tests.ModuleOnly', module_imports_only=True)
                self.assertEqual(narrowed['targets'], direct['targets'])
                self.assertEqual(len(narrowed['generated_sha256']), 17)
                for target in direct['targets']:
                    before = (check / 'src/Tests/InitialGlobalDirect6' / (target + '.agda')).read_text()
                    after = (check / 'src/Tests/ModuleOnly' / (target + '.agda')).read_text()
                    self.assertIn(' using (module AlignedModel)', after)
                    restored = after.replace(' using (module AlignedModel)', '')
                    restored = restored.replace('Tests.ModuleOnly', 'Tests.InitialGlobalDirect6')
                    self.assertEqual(restored, before)
                for bad in (1, 'yes', None):
                    with self.assertRaises(ValueError):
                        self.run_emit(check, data, layout, prefix='Tests.Invalid', module_imports_only=bad)

    def test_namespace_cache_and_symlink_guards(self):
        for kind in ('cache', 'output', 'donor', 'parent', 'overlap'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data, layout = self.prepare(check)
                kwargs = {}
                if kind == 'cache':
                    (check / '_build/2.8.0/agda/src/Tests/InitialGlobalDirect6').mkdir(parents=True)
                elif kind == 'output':
                    (check / 'src/Tests/InitialGlobalDirect6').symlink_to(check)
                elif kind == 'donor':
                    path = check / 'src/Tests/InitialGlobalNamed6/Routes0.agda'
                    real = check / 'route.agda'
                    real.write_bytes(path.read_bytes())
                    path.unlink()
                    path.symlink_to(real)
                elif kind == 'parent':
                    (check / 'src').rename(check / 'real-src')
                    (check / 'src').symlink_to(check / 'real-src')
                else:
                    kwargs['prefix'] = NAMED + '.Direct'
                with self.assertRaises(ValueError):
                    self.run_emit(check, data, layout, **kwargs)
                self.assertFalse((check / 'src/Tests/InitialGlobalDirect6/Root.agda').exists())


if __name__ == '__main__':
    unittest.main()
