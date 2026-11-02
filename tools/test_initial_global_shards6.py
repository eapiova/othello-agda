"""Light source/integrity tests. These do not assert safe Agda acceptance."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from initial_global_alignment6 import emit as emit_alignment
from initial_global_shards6 import emit
from lazy_sample_parts6 import emit as emit_samples
from test_initial_global_alignment6 import fixture, PREFIX

OUT = 'Tests.InitialGlobalShards6'


class GlobalShards(unittest.TestCase):
    def prepare(self, check, side='lower', data=None):
        data = fixture() if data is None else data
        emit_samples(check, data, side=side, prefix=PREFIX)
        return data

    def test_order_ranges_exact_maps_and_closed_root(self):
        for side in ('lower', 'upper'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data = self.prepare(check, side)
                accepted = {p: p.read_bytes() for p in check.rglob('*.agda')}
                baseline = emit_alignment(check, side=side, sample=data, sample_prefix=PREFIX)
                original = (check / 'src/Tests/InitialGlobalAlignment6/Stage16.agda').read_text()
                result = emit(check, side=side, sample=data, sample_prefix=PREFIX, route_batch=4)
                self.assertEqual(result['targets'], ['Model'] + [f'Routes{i}' for i in range(5)]
                                 + [f'Part{10+3*i}' for i in range(16)] + ['Root'])
                self.assertEqual(result['needed_chunks'], 17)
                self.assertEqual(result['owned_rows'], 40)
                ids = [j for s in result['shards'] for j in s['needed_parts']]
                self.assertEqual(ids, sorted(data['states']))
                self.assertTrue(all(1 <= s['needed_chunks'] <= 4 for s in result['shards']))
                sources = {Path(p).stem: (check / p).read_text() for p in result['generated_sha256']}
                for definition in ('globalStates', 'globalBodies', 'ownedStates', 'G', 'C'):
                    expected = next(line for line in original.splitlines() if line.startswith(definition + ' ='))
                    self.assertIn(expected, sources['Model'])
                self.assertIn('stateRoute2 = (Laws.left (Laws.at-most 401', sources['Routes0'])
                self.assertIn('Laws.route-aligned {map = globalStates} {base = 400} {n = 1}', sources['Routes0'])
                self.assertIn('{xs = Lazy.states 1 S2.text}', sources['Routes0'])
                self.assertIn('demandAligned = (R0.stateAligned2 , R0.stateAligned10)', sources['Part10'])
                self.assertIn('Laws.route-aligned {map = globalBodies} {base = 2000} {n = 1}', sources['Part10'])
                self.assertIn('P.linked LookupStates LookupBodies demandAligned R0.stateAligned10 bodyAligned', sources['Part10'])
                self.assertIn('Family.A.join {G = LookupStates} {C = LookupBodies} 6800', sources['Root'])
                self.assertIn('partial : Family.A.Partial G C ownedStates', sources['Root'])
                self.assertIn('partial = Closed.partial', sources['Root'])
                self.assertIn('Laws.self-compatible globalStates fallbackState', sources['Root'])
                self.assertIn('Laws.self-compatible globalBodies I.indexedLeaf', sources['Root'])
                for name, text in sources.items():
                    self.assertIn('--safe --without-K --cubical-compatible', text)
                    for banned in ('postulate', '.complete', 'Together', 'Laws.Included', 'accepted = refl', '?'):
                        self.assertNotIn(banned, text)
                    if name != 'Model':
                        self.assertNotIn('Laws.totalize', text)
                        self.assertNotIn('globalStates =', text)
                for relative, digest in result['generated_sha256'].items():
                    self.assertEqual(hashlib.sha256((check / relative).read_bytes()).hexdigest(), digest)
                self.assertEqual(result['generated_bytes'], sum((check / p).stat().st_size for p in result['generated_sha256']))
                self.assertTrue(all(p.read_bytes() == raw for p, raw in accepted.items()))
                self.assertFalse(result['initial_problem2_proved'])
                self.assertFalse(result['optimal_initial_pair_proved'])
                self.assertFalse(result['production_authorized'])
                with self.assertRaises(ValueError):
                    emit(check, side=side, sample=data, sample_prefix=PREFIX)
                self.assertEqual(baseline['targets'], ['Stage4', 'Stage8', 'Stage16'])

    def test_single_part_and_maximum_route_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            data = fixture()
            case = min(data['cases'], key=lambda c: c['part'])
            data = dict(cases=[case], states={j: data['states'][j] for j in case['dependencies']})
            self.prepare(check, data=data)
            result = emit(check, side='lower', sample=data, sample_prefix=PREFIX, route_batch=64)
            self.assertEqual(result['targets'], ['Model', 'Routes0', 'Part10', 'Root'])
            root = (check / 'src/Tests/InitialGlobalShards6/Root.agda').read_text()
            self.assertIn('partial = P10.partial', root)

    def test_invalid_ranges_literals_names_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            original = self.prepare(check)
            for batch in (0, 65, -1, True, 1.5, '32'):
                with self.assertRaises(ValueError):
                    emit(check, side='lower', sample=original, sample_prefix=PREFIX, route_batch=batch)
            for prefix in ('../bad', 'Tests.Bad;name', PREFIX, PREFIX + '.X', 'Tests'):
                with self.assertRaises(ValueError):
                    emit(check, side='lower', sample=original, sample_prefix=PREFIX, prefix=prefix)
            changes = [lambda d: d['states'].pop(2),
                       lambda d: d['cases'][0].update(part=40000),
                       lambda d: d['states'][2].update(rows=201),
                       lambda d: d['cases'][0].update(dependencies=[55]),
                       lambda d: d['cases'][0].update(body_text='L'),
                       lambda d: d['cases'][0].update(state_text='b000000000000')]
            for change in changes:
                data = copy.deepcopy(original)
                change(data)
                with self.assertRaises(ValueError):
                    emit(check, side='lower', sample=data, sample_prefix=PREFIX)
            self.assertFalse((check / 'src/Tests/InitialGlobalShards6').exists())
            p = check / 'src/Tests/InitialLazyTrainingLower/Part10.agda'
            p.write_bytes(p.read_bytes() + b'\n-- changed\n')
            with self.assertRaisesRegex(ValueError, 'source metadata mismatch'):
                emit(check, side='lower', sample=original, sample_prefix=PREFIX)
            self.assertFalse((check / 'src/Tests/InitialGlobalShards6').exists())

    def test_cache_symlink_and_namespace_guards(self):
        for kind in ('cache', 'output_symlink', 'accepted_symlink', 'source_parent_symlink'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data = self.prepare(check)
                if kind == 'cache':
                    p = check / '_build/2.8.0/agda/src/Tests/InitialGlobalShards6'
                    p.mkdir(parents=True)
                    (p / 'Root.agdai').write_bytes(b'cached')
                elif kind == 'output_symlink':
                    (check / 'src/Tests/InitialGlobalShards6').symlink_to(check)
                elif kind == 'accepted_symlink':
                    p = check / 'src/Tests/InitialLazyTrainingLower/StateData2.agda'
                    target = check / 'accepted.agda'
                    target.write_bytes(p.read_bytes())
                    p.unlink()
                    p.symlink_to(target)
                else:
                    src = check / 'src'
                    src.rename(check / 'real-src')
                    src.symlink_to(check / 'real-src')
                with self.assertRaises(ValueError):
                    emit(check, side='lower', sample=data, sample_prefix=PREFIX)
                self.assertFalse((check / 'src/Tests/InitialGlobalShards6/Root.agda').exists())


if __name__ == '__main__':
    unittest.main()
