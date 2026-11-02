"""AI-assisted bounded codec tests; no search or native solver work."""
import itertools
import re
import unittest
from pathlib import Path

import bench6
import compact_shared6 as compact
import ref
import shared_symmetry6 as shared


FIXTURE = Path(__file__).resolve().parents[1] / 'src/Tests/GeneratedSharedSymmetry6.agda'


def fixture_entries(direction):
    source = FIXTURE.read_text()
    match = re.search(rf'{direction}Encoded = "([^"]+)"', source)
    if match is None:
        raise ValueError('missing old-format generated fixture')
    wire = match.group(1)
    return [(bench6.decode(state), body)
            for state, body in re.findall(r'([bw][012]{36})(.*?)(?=[bw][012]{36}|$)', wire)]


class CompactSharedTests(unittest.TestCase):
    def test_all_27_triples_both_players(self):
        for index, triple in enumerate(itertools.product('012', repeat=3)):
            for player in 'bw':
                raw = player + ''.join(triple) * 12
                packed = player + compact.TRIPLES[index] * 12
                self.assertEqual(compact.pack_state(raw), packed)
                self.assertEqual(compact.unpack_state(packed), raw)
                self.assertEqual(compact.pack_state(bench6.decode(raw)), packed)

    def test_invalid_states(self):
        packed, raw = 'b' + '0' * 12, 'w' + '1' * 36
        for broken in ('', packed[:-1], packed + '0', 'x' + packed[1:],
                       'bR' + '0' * 11, 'b_' + '0' * 11, 'b０' + '0' * 11, None):
            with self.subTest(packed=broken), self.assertRaises(ValueError):
                compact.unpack_state(broken)
        for broken in ('', raw[:-1], raw + '0', 'x' + raw[1:], 'w3' + '1' * 35,
                       'w１' + '1' * 35, None, ref.initial(4),
                       ref.State(6, (True,) * 36, 1)):
            with self.subTest(raw=broken), self.assertRaises(ValueError):
                compact.pack_state(broken)

    def test_certificate_tokens_and_boundaries(self):
        cases = [('L', 'L'), ('K', 'K'), ('PL', 'PL'), ('R0;', 'R0'),
                 ('R7;', 'R7'), ('C0;L', 'C0L'), ('C35;K', 'CZK'),
                 ('F0;', 'F0'), ('F2;LK', 'F2LK'),
                 ('F36;' + 'L' * 36, 'F_' + 'L' * 36),
                 ('S0;', 'S0;'), ('S128;', 'S128;'), ('PC1;F1;L', 'PC1F1L')]
        for old, packed in cases:
            self.assertEqual(compact.pack_certificate(old), packed)
            self.assertEqual(compact.unpack_certificate(packed), old)
        old = 'P' * 5000 + 'L'
        self.assertEqual(compact.unpack_certificate(compact.pack_certificate(old)), old)

    def test_malformed_certificates_fail_closed(self):
        old_invalid = ('', 'X', 'P', 'R', 'R;', 'R8;', 'R-1;', 'R１;', 'R1',
                       'C0;', 'C36;L', 'F2;L', 'F37;' + 'L' * 37,
                       'S;', 'S129;', 'S1', 'S-1;', 'Lx', 'LL', 'R0;;', None)
        compact_invalid = ('', 'X', 'P', 'R', 'R8', 'RA', 'R１', 'R1;',
                           'C', 'C0', 'C_L', 'CaL', 'F', 'F2L', 'Fa',
                           'F_' + 'L' * 35, 'S;', 'S129;', 'S1', 'S-1;',
                           'Lx', 'LL', 'R0;', None)
        for broken in old_invalid:
            with self.subTest(old=broken), self.assertRaises(ValueError):
                compact.pack_certificate(broken)
        for broken in compact_invalid:
            with self.subTest(compact=broken), self.assertRaises(ValueError):
                compact.unpack_certificate(broken)

    def test_real_forced_pass_fixtures_and_missing_reference(self):
        for direction in ('lower', 'upper'):
            entries = fixture_entries(direction)
            self.assertEqual(len(entries), 2)
            root = entries[-1][0]
            self.assertFalse(ref.placements(root))
            self.assertEqual(len(ref.successors(root)), 1)
            packed = compact.encode(entries)
            pieces = re.findall(r'([bw][0-9A-Q]{12})(.*?)(?=[bw][0-9A-Q]{12}|$)', packed)
            recovered = [(bench6.decode(compact.unpack_state(state)),
                          compact.unpack_certificate(body)) for state, body in pieces]
            self.assertEqual(recovered, entries)
            self.assertTrue(shared.replay(recovered, root, direction, 4))
            self.assertFalse(shared.replay([recovered[-1]], root, direction, 4))
            self.assertFalse(shared.replay([(root, 'R8;')], root, direction, 4))
            self.assertLess(len(packed), sum(37 + len(body) for _, body in entries))


if __name__ == '__main__':
    unittest.main()
