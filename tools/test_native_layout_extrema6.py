import copy
import unittest

import native_layout_extrema6 as e


class ExtremaTests(unittest.TestCase):
    def test_only_counter_delta_is_generated(self):
        raw = e.sample.layout.wire.solve6.SOURCE.read_text()
        original = e.sample.generated_source(raw)
        changed = e.generated_source(raw)
        self.assertNotEqual(changed, original)
        self.assertIn('extrema_direct_part=index', changed)
        self.assertIn('layout_direct_dependencies_max_part', changed)
        # The wrapper's own reverse-delta guard rejects any unrelated changes.
        self.assertEqual(e.generated_source(raw), changed)

    def test_complete_extrema_ids(self):
        counts = dict(complete=True, layout_complete=True, layout_censored=False,
            count_overflow=False, layout_parts=20, layout_imported_citations_max_part=17,
            layout_direct_dependencies_max_part=17, layout_max_part_tokens_part=12)
        self.assertEqual(e.extrema(counts), [12, 17])
        for changes in (dict(layout_complete=False), dict(layout_censored=True),
                        dict(count_overflow=True), dict(layout_parts=0),
                        dict(layout_direct_dependencies_max_part=20),
                        dict(layout_max_part_tokens_part=-1)):
            changed = copy.deepcopy(counts)
            changed.update(changes)
            with self.assertRaises(ValueError):
                e.extrema(changed)


if __name__ == '__main__':
    unittest.main()
