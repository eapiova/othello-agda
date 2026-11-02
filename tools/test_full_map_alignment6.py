"""Route partition tests; generation itself is not Agda acceptance."""
import re
import unittest
from full_map_alignment6 import route


class MapAlignment(unittest.TestCase):
    def test_small_and_full_dimension_routes_reach_exact_leaf(self):
        for size,ids in [(1,[0]),(17,list(range(17))),(34366,[0,1,17182,17183,32767,34364,34365])]:
            for j in ids:
                term=route(0,size,j)
                self.assertEqual(term.count('('),term.count(')'))
                lo,hi=0,size
                for side in re.findall(r'R\.(left|right)',term):
                    mid=(lo+hi)//2
                    if side=='left':hi=mid
                    else:lo=mid
                self.assertEqual((lo,hi),(j,j+1))
                self.assertTrue(term.endswith('R.here'+')'*term.count('(')))
                self.assertLessEqual(term.count('('),16)

    def test_bad_bounds_are_refused(self):
        for args in [(0,0,0),(0,2,2),(-1,2,0),(0,4,-1),(0,4,True)]:
            with self.subTest(args=args),self.assertRaises(ValueError):route(*args)

    def test_all_full_chunk_paths_use_logarithmic_depth(self):
        for j in range(34366):
            term=route(0,34366,j)
            self.assertLessEqual(term.count('refl'),16)
            self.assertEqual(term.count('R.here'),1)
