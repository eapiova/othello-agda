"""Parse grammar correctly and keep failed/partial timings out of forecasts."""
import unittest
import nat_forecast6 as forecast


class Forecast(unittest.TestCase):
    def test_citation_digits_resembling_tokens_are_not_nodes(self):
        r = forecast.numeric_stats('KFR;')
        self.assertEqual(r['tokens'], 1)
        self.assertEqual(r['referenced_ids'], [582])

    def test_nested_and_multiple_rows(self):
        r = forecast.numeric_stats('F2R0K;KR;C3PLL')
        self.assertEqual(r['rows'], 3)
        self.assertEqual(r['tokens'], 7)
        self.assertEqual(r['references'], 2)
        self.assertEqual(r['referenced_ids'], [20, 27])
        self.assertEqual(r['move_nodes'], 3)

    def test_bad_data_is_rejected(self):
        for text in ['', 'R8L;', 'K;', 'F2L', 'K0', 'C_L', 'S129;', 'S;', 'R0K0;?']:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    forecast.numeric_stats(text)

    def test_solve_is_not_modelled_as_a_constant_leaf(self):
        r = forecast.numeric_stats('S80;')
        r['dependency_state_rows'] = 200
        with self.assertRaises(ValueError):
            forecast.features(r)

    def test_training_must_be_complete(self):
        with self.assertRaises(ValueError):
            forecast.prediction([], {})


if __name__ == '__main__':
    unittest.main()
