import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
from nat_indexed_pilot6 import convert_wire, number


class NumericWireTests(unittest.TestCase):
    leaves=[{'path':'a','leaf':0,'size':200}, {'path':'ba','leaf':1,'size':200},
            {'path':'bb','leaf':2,'size':17}]

    def test_grammar_and_row_digits_that_look_like_tokens(self):
        text='PC1F2Ka0KR4ba0RS80;Kbb0G'
        changed,refs=convert_wire(text,self.leaves)
        self.assertEqual(refs,[20,227,416])
        self.assertEqual(changed,'PC1F2K'+number(20)+'R4'+number(227)+'S80;K'+number(416))

    def test_partial_and_invalid_data_are_rejected(self):
        for text in ['K','R8a00','Ka','Kbb0H','F2L','C_L','S129;','Q']:
            with self.subTest(text=text),self.assertRaises(ValueError):
                convert_wire(text,self.leaves)

    def test_numeric_format(self):
        self.assertEqual(number(0),'0;')
        self.assertEqual(number(37),'10;')
        with self.assertRaises(ValueError):number(20000000)


if __name__=='__main__':unittest.main()
