"""Detached regrouping must preserve coverage and transparent root positions."""
import re
import unittest

from closed_roots6 import collector_source
from unattended_assembly6 import grouped_sources, import_probes


def fixture():
    states=[]
    for value in range(100):
        cells=[]
        for _ in range(36):
            value,digit=divmod(value,3);cells.append(str(digit))
        states.append('b'+''.join(reversed(cells)))
    return dict(format='othello-global-shared6-plan-v1',direction='upper',threshold=4,
        roots=states,entries=[dict(state=s,certificate='L',references=[]) for s in states])


class UnattendedTests(unittest.TestCase):
    def test_group_coverage_and_opacity(self):
        plan=fixture();sources,groups=grouped_sources(plan)
        self.assertEqual([s for g in groups for s in g['roots']],plan['roots'])
        self.assertEqual(sum(g['entries'] for g in groups),100)
        for i in range(10):
            text=sources[f'src/Tests/Unattended6/Group{i}/Check.agda']
            self.assertEqual(len(re.findall(r'^position\d+ :',text,re.M)),10)
            self.assertEqual(len(re.findall(r'^  guarantee\d+ :',text,re.M)),10)
            self.assertIn('--save-metas --safe --without-K --cubical-compatible',text)
            self.assertNotIn('postulate',text)
        collective=sources['src/Tests/Unattended6/All100.agda']
        self.assertIn('allUpper : AllUpper rootCodes',collective)
        self.assertIn('Rules.game six',collective)

    def test_exact_prior_import_sets(self):
        states=fixture()['roots'];witnesses={}
        for i,s in enumerate(states):
            if i<57:module='Tests.GlobalPilot6.CheckSubset';fact=f'guarantee{i}'
            elif i<59:module='Tests.GlobalPilot6.CheckNew';fact=f'guarantee{i-57}'
            elif i<66:module='Tests.GlobalPilot6.CheckContinueNew';fact=f'guarantee{i-59}'
            else:module=f'Tests.ClosedPilot6.Root{i-66}.Check';fact='guarantee0'
            witnesses[s]=(module,fact)
        original=collector_source(states,witnesses)
        probes=import_probes(original)
        self.assertEqual(len(probes),6)
        self.assertEqual(probes['src/Tests/Unattended6/ImportsAll100.agda'].count('import Tests.'),37)
        self.assertEqual(probes['src/Tests/Unattended6/ImportsNew8.agda'].count('import Tests.'),8)
        with self.assertRaises(ValueError):import_probes(original.replace('Tests.ClosedPilot6.Root0.Check','Tests.Wrong.Check'))


if __name__=='__main__':unittest.main()
