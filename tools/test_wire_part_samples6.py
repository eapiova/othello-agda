"""Wire translation and failure isolation, without any Agda acceptance claim."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from compact_shared6 import TRIPLES
from lazy_sample_parts6 import emit
from native_layout_samples6 import number
import wire_part_samples6 as sample


def state(n):
    digits = ''
    for _ in range(12):
        n, d = divmod(n, 27)
        digits += TRIPLES[d]
    return 'b' + digits


def fixture(count=401):
    rows = [(state(i), 'L', '') for i in range(count)]
    rows[200] = (state(200), 'F2KK', state(0) + state(199))
    rows[205] = (state(205), 'R4', state(0))
    if count > 400:
        rows[400] = (state(400), 'PK', state(200))
    return rows


class WireParts(unittest.TestCase):
    def run_sample(self, root, rows=None, **changes):
        rows = fixture() if rows is None else rows
        raw = ''.join('\t'.join(row) + '\n' for row in rows).encode()
        path = root / 'input.wire'
        path.write_bytes(raw)
        options = dict(expected_sha256=hashlib.sha256(raw).hexdigest(),
                       expected_rows=len(rows), selected=[1, 2])
        options.update(changes)
        result = sample.extract(path, **options)
        self.assertEqual(path.read_bytes(), raw)
        return result

    def test_numeric_ids_partial_final_chunk_and_existing_emitter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            got = self.run_sample(root)
            self.assertEqual(got['indexed_reference_states'], 3)
            self.assertEqual(got['reference_occurrences'], 4)
            self.assertEqual(got['wire_scans'], 2)
            self.assertFalse(got['whole_graph_index_retained'])
            self.assertEqual(set(got['states']), {0, 1, 2})
            self.assertEqual([c['rows'] for c in got['cases']], [200, 1])
            self.assertEqual(got['cases'][0]['references'], [0, 199, 0])
            self.assertTrue(got['cases'][0]['body_text'].startswith('F2K0;K' + number(199)))
            self.assertEqual(got['cases'][1]['body_text'], 'PK' + number(200))
            generated = emit(root / 'results/check', got, side='lower', prefix='Tests.WireFixture')
            self.assertEqual(generated['targets'], ['Family', 'Part1', 'Part2'])
            self.assertFalse(got['agda_checked'])
            self.assertFalse(generated['initial_problem2_proved'])

    def test_pin_count_selection_and_retained_memory_bounds(self):
        for changes in (dict(expected_sha256='0' * 64), dict(expected_rows=402),
                        dict(selected=[2, 1]), dict(selected=[1, 1]), dict(selected=[True]),
                        dict(max_sample_bytes=10), dict(max_reference_occurrences=2, max_unique_references=2),
                        dict(max_unique_references=2)):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    self.run_sample(Path(tmp), **changes)

    def test_unknown_forward_and_ambiguous_references_and_bad_syntax(self):
        variants = []
        for change in (
                lambda r: r.__setitem__(200, (state(200), 'K', state(999))),
                lambda r: r.__setitem__(200, (state(200), 'K', state(300))),
                lambda r: r.__setitem__(1, (state(0), 'L', '')),
                lambda r: r.__setitem__(200, (state(200), 'K', '')),
                lambda r: r.__setitem__(200, (state(200), 'F2L', '')),
                lambda r: r.__setitem__(200, (state(200), 'R8', state(0)))):
            rows = fixture(); change(rows); variants.append(rows)
        for rows in variants:
            with self.subTest(row=rows[200]), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    self.run_sample(Path(tmp), rows)

    def test_change_between_complete_scans_is_rejected(self):
        original = sample._records
        calls = 0
        def changed(path, *args):
            nonlocal calls
            calls += 1
            yield from original(path, *args)
            if calls == 1:
                raw = path.read_bytes()
                path.write_bytes(raw.replace(b'\tL\t\n', b'\tP\t\n', 1))
        with tempfile.TemporaryDirectory() as tmp, patch.object(sample, '_records', changed):
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                self.run_sample(Path(tmp))

    def test_malformed_unselected_rows_and_symlink_input(self):
        for raw in (b'b000000000000\tL\t', b'b000000000000\tL\tx\n',
                    b'bRRRRRRRRRRRR\tL\t\n', b'b000000000000\tL\t\t\n'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'bad.wire'; path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    sample.extract(path, expected_sha256=hashlib.sha256(raw).hexdigest(),
                                   expected_rows=1, selected=[0])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); path = root / 'real'; path.write_bytes(b'b000000000000\tL\t\n')
            link = root / 'link'; link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, 'nonsymlink'):
                sample.extract(link, expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                               expected_rows=1, selected=[0])

    def test_new_stratified_parts_are_fixed_and_disjoint(self):
        excluded = [0, 100, 34365]
        a = sample.selection(34366, excluded)
        self.assertEqual(a, sample.selection(34366, excluded))
        self.assertEqual(a['selected'], sorted(set(a['selected'])))
        self.assertFalse(set(a['selected']) & set(excluded))
        self.assertEqual(set(a['training']) | set(a['held_out']), set(a['selected']))
        with self.assertRaises(ValueError):
            sample.selection(4, [0, 1, 2, 3], count=2)


if __name__ == '__main__':
    unittest.main()
