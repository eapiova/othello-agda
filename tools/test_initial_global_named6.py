"""Light integrity/normalized-source tests; no claim of Agda acceptance."""
import copy
import hashlib
from pathlib import Path
import re
import tempfile
import unittest

from initial_global_named6 import emit
from initial_global_shards6 import emit as emit_original
from lazy_sample_parts6 import emit as emit_samples
from test_initial_global_alignment6 import fixture, PREFIX

OUT = 'Tests.InitialGlobalNamed6'


class GlobalNamed(unittest.TestCase):
    def prepare(self, check, side='lower', data=None):
        data = fixture() if data is None else data
        emit_samples(check, data, side=side, prefix=PREFIX)
        return data

    def test_normalized_maps_routes_and_order_both_sides(self):
        for side in ('lower', 'upper'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data = self.prepare(check, side)
                accepted = {p: p.read_bytes() for p in check.rglob('*.agda')}
                emit_original(check, side=side, sample=data, sample_prefix=PREFIX)
                original = (check / 'src/Tests/InitialGlobalShards6/Model.agda').read_text()
                result = emit(check, side=side, sample=data, sample_prefix=PREFIX,
                              route_batch=4, map_batch=4)
                sources = {Path(p).stem: (check / p).read_text() for p in result['generated_sha256']}
                positions = {name: i for i, name in enumerate(result['targets'])}
                helpers = {h['target'] for h in result['map_helpers']}
                self.assertLess(max(positions[n] for n in helpers), positions['Model'])
                self.assertEqual(result['targets'][-1], 'Root')
                self.assertEqual(result['needed_chunks'], 17)
                self.assertEqual(result['owned_rows'], 40)
                self.assertEqual([j for s in result['shards'] for j in s['needed_parts']], sorted(data['states']))
                for h in result['map_helpers']:
                    if h['group']:
                        self.assertLessEqual(h['leaf_chunks'], 4)
                    else:
                        self.assertEqual(sources[h['target']].count(' as L\n') + sources[h['target']].count(' as R\n'), 2)
                        self.assertNotIn('StateData', sources[h['target']])
                for name, source in sources.items():
                    self.assertIn('open import Prelude hiding (map)', source)
                    for dependency in re.findall(r'import ' + re.escape(OUT) + r'\.(\w+)', source):
                        self.assertLess(positions[dependency], positions[name])
                    self.assertIn('--safe --without-K --cubical-compatible', source)
                    for banned in ('postulate', '.complete', 'Together', 'Laws.Included', 'accepted = refl', '?'):
                        self.assertNotIn(banned, source)
                self.assertNotIn('StateData', sources['Model'])
                self.assertNotIn('BodyData', sources['Model'])

                def expand(module, field):
                    source = sources[module]
                    expr = re.search(r'^' + field + r' = (.+)$', source, re.M).group(1)
                    aliases = dict(re.findall(r'import ' + re.escape(OUT) + r'\.(\w+) as (\w+)', source))
                    aliases = {alias: target for target, alias in aliases.items()}
                    def qualified(match):
                        alias, member = match.group(1), match.group(2)
                        return '(' + expand(aliases[alias], member) + ')' if alias in aliases else match.group(0)
                    expr = re.sub(r'\b(\w+)\.(\w+)\b', qualified, expr)
                    expr = re.sub(r'\bnode\d+\b', lambda m: '(' + expand(module, m.group(0)) + ')', expr)
                    return expr

                def normalize(expr):
                    return re.sub(r'[\s()]', '', expr)

                for field in ('globalStates', 'globalBodies', 'ownedStates'):
                    baseline = re.search(r'^' + field + r' = (.+)$', original, re.M).group(1)
                    self.assertEqual(normalize(expand('Model', field)), normalize(baseline))
                for name, source in sources.items():
                    if name.startswith(('Routes', 'Part')):
                        constructors = re.findall(r'Laws\.(?:left|right) ([^\n]+)', source)
                        for constructor in constructors:
                            self.assertRegex(constructor, r'^\{pivot = \d+\} \{l = \w+\.\w+\} \{r = \w+\.\w+\} \{base = \d+\} \{n = \d+\} \{xs = ')
                self.assertIn('{xs = Lazy.states 1 S2.text}', sources['Routes0'])
                self.assertIn('partial : Family.A.Partial G C ownedStates', sources['Root'])
                self.assertIn('partial = Closed.partial', sources['Root'])
                self.assertIn('Laws.self-compatible globalStates fallbackState', sources['Root'])
                self.assertIn('Laws.self-compatible globalBodies I.indexedLeaf', sources['Root'])
                for p, digest in result['generated_sha256'].items():
                    self.assertEqual(hashlib.sha256((check / p).read_bytes()).hexdigest(), digest)
                self.assertEqual(result['generated_bytes'], sum((check / p).stat().st_size for p in result['generated_sha256']))
                self.assertTrue(all(p.read_bytes() == raw for p, raw in accepted.items()))
                for flag in ('initial_problem2_proved', 'optimal_initial_pair_proved', 'production_authorized'):
                    self.assertFalse(result[flag])
                with self.assertRaises(ValueError):
                    emit(check, side=side, sample=data, sample_prefix=PREFIX)

    def test_single_part_and_maximum_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            data = fixture()
            case = min(data['cases'], key=lambda c: c['part'])
            data = dict(cases=[case], states={j: data['states'][j] for j in case['dependencies']})
            self.prepare(check, data=data)
            result = emit(check, side='lower', sample=data, sample_prefix=PREFIX, route_batch=64, map_batch=64)
            self.assertEqual(result['targets'][-4:], ['Model', 'Routes0', 'Part10', 'Root'])
            root = (check / 'src/Tests/InitialGlobalNamed6/Root.agda').read_text()
            self.assertIn('partial = P10.partial', root)

    def test_invalid_ranges_literals_names_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            original = self.prepare(check)
            for parameter in ('route_batch', 'map_batch'):
                for batch in (0, 65, -1, True, 1.5, '32'):
                    with self.assertRaises(ValueError):
                        emit(check, side='lower', sample=original, sample_prefix=PREFIX, **{parameter: batch})
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
            self.assertFalse((check / 'src/Tests/InitialGlobalNamed6').exists())
            p = check / 'src/Tests/InitialLazyTrainingLower/Part10.agda'
            p.write_bytes(p.read_bytes() + b'\n-- changed\n')
            with self.assertRaisesRegex(ValueError, 'source metadata mismatch'):
                emit(check, side='lower', sample=original, sample_prefix=PREFIX)
            self.assertFalse((check / 'src/Tests/InitialGlobalNamed6').exists())

    def test_cache_symlink_and_namespace_guards(self):
        for kind in ('cache', 'output_symlink', 'accepted_symlink', 'source_parent_symlink'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data = self.prepare(check)
                if kind == 'cache':
                    p = check / '_build/2.8.0/agda/src/Tests/InitialGlobalNamed6'
                    p.mkdir(parents=True)
                    (p / 'Root.agdai').write_bytes(b'cached')
                elif kind == 'output_symlink':
                    (check / 'src/Tests/InitialGlobalNamed6').symlink_to(check)
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
                self.assertFalse((check / 'src/Tests/InitialGlobalNamed6/Root.agda').exists())


if __name__ == '__main__':
    unittest.main()
