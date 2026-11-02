"""AI-assisted tests for the untrusted layered-certificate generator."""
import unittest
import bench6
import shared6

LINE10 = 'b011100221112022112112222002200111100'


class SharedGeneratorTests(unittest.TestCase):
    def build(self, direction, min_indegree=2):
        root = bench6.decode(LINE10)
        choice = shared6.graph_from_search(root, direction, 4)
        return root, choice, shared6.layered(choice, root, min_indegree)

    def test_entries_cite_only_earlier_entries(self):
        root, _, (entries, stats) = self.build('lower')
        self.assertTrue(shared6.replay(entries, root, 'lower', 4))
        self.assertEqual(entries[-1][0], root)
        self.assertLessEqual(stats['checked_tokens'], stats['expanded_tree_nodes'])

    def test_misordered_entries_rejected(self):
        root, _, (entries, _) = self.build('lower')
        self.assertFalse(shared6.replay(entries[-1:] + entries[:-1], root, 'lower', 4))

    def test_tree_mode_matches_expanded_size(self):
        root, choice, (entries, stats) = self.build('upper', 10**9)
        self.assertEqual(len(entries), 1)
        self.assertEqual(stats['checked_tokens'], shared6.expanded_size(choice, root))

    def test_wrong_bound_rejected(self):
        root, _, (entries, _) = self.build('lower')
        self.assertFalse(shared6.replay(entries, root, 'lower', 5))

    def test_agda_template_renders(self):
        text = shared6.agda_text(LINE10, 'lower', 4, 'xyz')
        self.assertTrue(text.startswith('{-# OPTIONS --safe --without-K --cubical-compatible #-}'))
        self.assertIn('module Tests.Bench6.SharedCheck where', text)
        self.assertIn('white (lowerGoal (pos 4))', text)
        self.assertIn('encoded = "xyz"', text)


if __name__ == '__main__':
    unittest.main()
