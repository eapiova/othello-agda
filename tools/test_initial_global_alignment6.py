"""Light generator tests; none of these tests assert Agda acceptance."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from initial_global_alignment6 import emit
from lazy_sample_parts6 import emit as emit_samples
from nat_indexed_pilot6 import number

PREFIX = 'Tests.InitialLazyTrainingLower'


def fixture():
    ids = [10 + 3 * i for i in range(16)]
    states = {2: dict(rows=1, text='wQQQQQQQQQQQQ')}
    cases = []
    for i, j in enumerate(ids):
        n = 1 + i % 4
        text = 'wQQQQQQQQQQQQ' * n
        states[j] = dict(rows=n, text=text)
        cases.append(dict(part=j, rows=n, state_text=text, body_text=('K' + number(400)) * n,
                          references=[400] * n, dependencies=[2, j], tokens=n))
    return dict(cases=list(reversed(cases)), states=states)


class GlobalAlignment(unittest.TestCase):
    def prepare(self, check, data=None, side='lower'):
        data = fixture() if data is None else data
        emit_samples(check, data, side=side, prefix=PREFIX)
        return data

    def test_stages_routes_closed_coverage_and_hashes(self):
        for side in ('lower', 'upper'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data = self.prepare(check, side=side)
                accepted = {p: p.read_bytes() for p in check.rglob('*.agda')}
                result = emit(check, side=side, sample=data, sample_prefix=PREFIX)
                self.assertEqual(result['targets'], ['Stage4', 'Stage8', 'Stage16'])
                self.assertEqual([s['needed_chunks'] for s in result['stages']], [5, 9, 17])
                self.assertEqual([s['owned_rows'] for s in result['stages']], [10, 20, 40])
                self.assertEqual(result['stages'][0]['owned_parts'], [10, 13, 16, 19])
                self.assertFalse(result['initial_problem2_proved'])
                self.assertFalse(result['production_authorized'])
                self.assertEqual(result['generated_bytes'], sum((check/p).stat().st_size
                                 for p in result['generated_sha256']))
                for relative, digest in result['generated_sha256'].items():
                    raw = (check / relative).read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                    text = raw.decode()
                    self.assertIn('--safe --without-K --cubical-compatible', text)
                    self.assertIn('partial : Family.A.Partial G C ownedStates', text)
                    self.assertIn('Laws.self-compatible globalStates fallbackState', text)
                    self.assertIn('Laws.self-compatible globalBodies I.indexedLeaf', text)
                    for banned in ('Laws.Included', '.complete', 'Together', 'postulate', 'accepted = refl'):
                        self.assertNotIn(banned, text)
                text = (check / 'src/Tests/InitialGlobalAlignment6/Stage4.agda').read_text()
                self.assertIn('stateRoute2 = (Laws.left (Laws.at-most 401 2600 refl)', text)
                self.assertIn('bodyRoute10 = (Laws.left (Laws.at-most 2001 3200 refl)', text)
                self.assertIn('demandAligned19 = (stateAligned2 , stateAligned19)', text)
                self.assertIn('P19.linked LookupStates LookupBodies demandAligned19 stateAligned19 bodyAligned19', text)
                self.assertIn('Family.A.join {G = LookupStates} {C = LookupBodies} 3200', text)
                self.assertIn('module Closed = AlignedModel G C', text)
                self.assertIn('partial = Closed.partial', text)
                self.assertNotIn('Body2', text)
                self.assertTrue(all(p.read_bytes() == raw for p, raw in accepted.items()))
                before = {p: p.read_bytes() for p in check.rglob('*.agda')}
                with self.assertRaises(ValueError):
                    emit(check, side=side, sample=data, sample_prefix=PREFIX)
                self.assertEqual(before, {p: p.read_bytes() for p in check.rglob('*.agda')})

    def test_invalid_data_prefix_and_source_metadata(self):
        changes = [lambda d: d['states'].pop(2),
                   lambda d: d['cases'][0].update(part=40000),
                   lambda d: d['cases'][0].update(dependencies=[55]),
                   lambda d: d['cases'][0].update(state_text='b000000000000'),
                   lambda d: d['cases'][0].update(body_text='L')]
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            original = self.prepare(check)
            for change in changes:
                data = copy.deepcopy(original)
                change(data)
                with self.assertRaises(ValueError):
                    emit(check, side='lower', sample=data, sample_prefix=PREFIX)
                self.assertFalse((check / 'src/Tests/InitialGlobalAlignment6').exists())
            for prefix in ('../bad', 'Tests.X;bad', PREFIX, PREFIX + '.X'):
                with self.assertRaises(ValueError):
                    emit(check, side='lower', sample=original, sample_prefix=PREFIX, prefix=prefix)
            p = check / 'src/Tests/InitialLazyTrainingLower/Part10.agda'
            p.write_text(p.read_text() + '\n-- modified fixture\n')
            with self.assertRaisesRegex(ValueError, 'source metadata mismatch'):
                emit(check, side='lower', sample=original, sample_prefix=PREFIX)
            self.assertFalse((check / 'src/Tests/InitialGlobalAlignment6').exists())

    def test_cache_and_symlink_freshness(self):
        for kind in ('cache', 'symlink', 'accepted_symlink'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data = self.prepare(check)
                if kind == 'cache':
                    old = check / '_build/2.8.0/agda/src/Tests/InitialGlobalAlignment6'
                    old.mkdir(parents=True)
                    (old / 'Stage4.agdai').write_bytes(b'cached')
                elif kind == 'symlink':
                    (check / 'src/Tests/InitialGlobalAlignment6').symlink_to(check)
                else:
                    p = check / 'src/Tests/InitialLazyTrainingLower/BodyData10.agda'
                    raw = p.read_bytes()
                    p.unlink()
                    target = check / 'fixture.agda'
                    target.write_bytes(raw)
                    p.symlink_to(target)
                with self.assertRaises(ValueError):
                    emit(check, side='lower', sample=data, sample_prefix=PREFIX)
                self.assertFalse((check / 'src/Tests/InitialGlobalAlignment6/Stage4.agda').exists())


if __name__ == '__main__':
    unittest.main()
