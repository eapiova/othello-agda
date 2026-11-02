"""A collector recovery must keep all roots and their original witnesses."""
import re
import unittest

from collector_thin6 import thin_source
from closed_roots6 import collector_source


def original_fixture():
    states = []
    for value in range(100):
        cells = []
        for _ in range(36):
            value, digit = divmod(value, 3)
            cells.append(str(digit))
        states.append('b' + ''.join(reversed(cells)))
    witnesses = {state: (f'Tests.Fixture.Group{i//5}', f'guarantee{i%5}')
                 for i, state in enumerate(states)}
    return collector_source(states, witnesses)


class ThinCollectorTests(unittest.TestCase):
    def test_preserves_root_order_and_witness_order(self):
        original = original_fixture()
        generated = thin_source(original)
        expected_codes = re.findall(r'"([^"]+)"', original.split('rootCodes = ', 1)[1])
        expected_facts = re.findall(r'R\d+\.guarantee\d+', original.split('  allUpper = ', 1)[1])
        actual_facts = re.findall(r'R\d+\.guarantee\d+', generated)
        self.assertEqual(re.findall(r'"([^"]+)"', generated), expected_codes)
        self.assertEqual(actual_facts, expected_facts)
        self.assertIn('Guarantees (Rules.game six) black (upperGoal 4)', generated)
        self.assertEqual(generated.count(' : AllUpper codes'), 20)
        self.assertNotIn('refl', generated)
        self.assertNotIn('postulate', generated)

    def test_incomplete_original_is_rejected(self):
        original = original_fixture()
        self.assertRaises(ValueError, thin_source, original.replace('R0.guarantee0 ,', 'tt ,', 1))
        self.assertRaises(ValueError, thin_source, original.replace('rootCodes = "', 'rootCodes = ', 1))


if __name__ == '__main__':
    unittest.main()
