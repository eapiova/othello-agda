"""Sample-demand and freshness guards; actual claims require safe Agda."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

import compact_shared6 as compact
from census_pilot6 import state
import generate6
from indexed_spike6 import BASE, IMAGE
from lazy_sample_parts6 import emit
from nat_indexed_pilot6 import number
import ref


def fixture(side='lower', first=34360):
    a, b, c = first, first + 1, first + 2
    base, image = compact.pack_state(BASE), compact.pack_state(IMAGE)
    if side == 'lower':
        texts = [base * 2, image, image]
        bodies = ['PC1F1LK' + number(a * 200), 'R4' + number(a * 200), 'K' + number(b * 200)]
        tokens = [5, 1, 1]
    else:
        passed = ref.successors(state(BASE[1:], 'black'))[0]
        off = compact.pack_state(generate6.encode_state(ref.successors(passed)[0]))
        texts = [off + base, image, image]
        bodies = ['C0LPF2K' + number(a * 200) + 'C0L', 'R4' + number(a * 200 + 1), 'K' + number(b * 200)]
        tokens = [7, 1, 1]
    refs = [[a * 200], [a * 200 + (side == 'upper')], [b * 200]]
    states = {j: dict(rows=n, text=text) for j, n, text in zip((a, b, c), (2, 1, 1), texts)}
    cases = [dict(part=j, rows=states[j]['rows'], state_text=texts[k], body_text=bodies[k],
                  references=refs[k], dependencies=sorted({j} | {r // 200 for r in refs[k]}),
                  tokens=tokens[k]) for k, j in enumerate((a, b, c))]
    return dict(cases=cases, states=states)


class SampleParts(unittest.TestCase):
    def test_real_game_high_ranks_and_exact_dependencies_both_directions(self):
        for side in ('lower', 'upper'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data = fixture(side)
                result = emit(check, data, side=side)
                self.assertEqual(result['state_chunks'], 3)
                self.assertFalse(result['initial_problem2_proved'])
                self.assertEqual(result['targets'], ['Family', 'Part34360', 'Part34361', 'Part34362'])
                actual = 0
                for name, digest in result['generated_sha256'].items():
                    raw = (check / name).read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                    actual += len(raw)
                    self.assertIn(b'--safe --without-K --cubical-compatible', raw)
                self.assertEqual(actual, result['generated_bytes'])
                p = check / 'src/Tests/LazyInitialSample6/Part34362.agda'
                text = p.read_text()
                self.assertIn('M.rows 6872400 1', text)
                self.assertIn('StateData34361', text)
                self.assertIn('StateData34362', text)
                self.assertNotIn('StateData34360', text)
                self.assertNotIn('import Tests.LazyInitialSample6.Part', text)
                self.assertIn('Family.L.checkPart', text)
                self.assertIn('Family.L.linkedAligned', text)
                s = check / 'src/Tests/LazyInitialSample6/StateData34360.agda'
                self.assertNotIn('states =', s.read_text())

    def test_failed_inputs_create_no_sources(self):
        changes = (
            lambda d: d['cases'].append(copy.deepcopy(d['cases'][0])),
            lambda d: d['states'].pop(34361),
            lambda d: d['cases'][0].update(body_text='L"'),
            lambda d: d['cases'][0].update(references=[6872002]),
            lambda d: d['cases'][0].update(state_text='b000000000000' * 2),
            lambda d: d['cases'][2].update(dependencies=[34362]),
            lambda d: d['states'].update({10: dict(rows=1, text='b000000000000')}),
        )
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            for change in changes:
                data = fixture()
                change(data)
                with self.assertRaises(ValueError):
                    emit(check, data, side='lower')
                self.assertFalse((check / 'src').exists())

    def test_existing_source_cache_and_symlinks_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            result = emit(check, fixture(), side='lower')
            before = {p: p.read_bytes() for p in check.rglob('*.agda')}
            with self.assertRaises(ValueError):
                emit(check, fixture(), side='lower')
            self.assertEqual(before, {p: p.read_bytes() for p in check.rglob('*.agda')})
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            folder = check / '_build/2.8.0/agda/src/Tests/LazyInitialSample6'
            folder.mkdir(parents=True)
            old = folder / 'Part34360.agdai'
            old.write_bytes(b'old cache')
            with self.assertRaises(ValueError):
                emit(check, fixture(), side='lower')
            self.assertEqual(old.read_bytes(), b'old cache')
            self.assertFalse((check / 'src').exists())
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            (check / 'src').symlink_to(check)
            with self.assertRaises(ValueError):
                emit(check, fixture(), side='lower')
            self.assertEqual(list(check.iterdir()), [check / 'src'])


if __name__ == '__main__':
    unittest.main()
