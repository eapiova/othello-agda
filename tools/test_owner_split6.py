"""Recovery must preserve obligations, actual exports and the failed source."""
import copy
import unittest

import owner_lower6 as owner
from owner_split6 import split_sources,NAMESPACE,DIRECTORY
from test_lower_pilot6 import fixture


class OwnerSplitTests(unittest.TestCase):
    def source(self):
        roots=fixture()['roots']
        entries=[dict(state=roots[i%20],certificate='L',references=[]) for i in range(27)]
        # Unique full states for this generator-only dependency fixture.
        for i,e in enumerate(entries):e['state']='w'+str(i%3)+str((i//3)%3)+str((i//9)%3)+'0'*33
        parts=[[e] for e in entries];owners={e['state']:i for i,e in enumerate(entries)}
        for i in (24,25,26):parts[i][0]['references']=[parts[i-1][0]['state']]
        text,_=owner.assembly_source(5,6,parts,owners,{})
        return text

    def test_each_closed_obligation_retains_its_literals_and_real_owners(self):
        original=self.source();sources=split_sources(original)
        self.assertEqual(original,self.source())
        for i in range(3):
            text=sources[f'{DIRECTORY}/Assemble6Split{i}.agda']
            self.assertIn(f'module {NAMESPACE}.Assemble6Split{i} where',text)
            self.assertIn(f'module P{24+i} where',text)
            self.assertEqual(text.count('coverage = refl {x = true}'),1)
            self.assertIn(f'I{24+i}.sound',text)
            self.assertNotIn(f'module P{25+i} where',text)
        self.assertIn('S24.P24.export',sources[f'{DIRECTORY}/Assemble6Split1.agda'])
        self.assertIn('S25.P25.export',sources[f'{DIRECTORY}/Assemble6Split2.agda'])
        facade=sources[f'{DIRECTORY}/Assemble6.agda']
        self.assertIn('module P26 = S2.P26',facade)
        self.assertNotIn('coverage = refl',facade)

    def test_unexpected_bindings_are_not_silently_pruned(self):
        with self.assertRaises(ValueError):split_sources(self.source().replace('module P25 where','module P99 where'))


if __name__=='__main__':unittest.main()
