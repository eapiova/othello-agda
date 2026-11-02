"""Root isolation must preserve exact citations and exact collection coverage."""
import unittest

import closed_roots6 as closed


class ClosedRootTests(unittest.TestCase):
    def setUp(self):
        self.a='b'+'0'*36
        self.b='b'+'0'*35+'1'
        self.c='w'+'0'*36
        self.plan=dict(format='othello-global-shared6-plan-v1',direction='upper',threshold=4,
            roots=[self.b,self.c],entries=[dict(state=self.a,certificate='L',references=[]),
                dict(state=self.b,certificate='C0;L',references=[self.a]),
                dict(state=self.c,certificate='L',references=[])])

    def test_closure_preserves_dependencies_order_and_certificate_bytes(self):
        entries=closed.closure_entries(self.plan,[self.b])
        self.assertEqual(entries,self.plan['entries'][:2])
        self.assertEqual(closed.closure_entries(self.plan,[self.c]),self.plan['entries'][2:])
        self.assertNotIn(self.c,[e['state'] for e in entries])

    def test_bad_root_or_forward_citation_is_rejected(self):
        for roots in ([],[self.b,self.b],[self.a]):
            with self.assertRaises(ValueError):closed.closure_entries(self.plan,roots)
        self.plan['entries'][0]['references']=[self.b]
        with self.assertRaises(ValueError):closed.closure_entries(self.plan,[self.b])

    def test_root_namespace_and_original_rules_bound_are_preserved(self):
        sources,parts=closed.root_sources(self.plan,self.b,4)
        self.assertEqual(len(parts),1)
        proof=sources['src/Tests/ClosedPilot6/Root4/Check.agda']
        self.assertIn('import Tests.ClosedPilot6.Root4.Part0',proof)
        self.assertNotIn('Tests.GlobalPilot6',proof)
        self.assertIn('abstract\n  accepted0',proof)
        self.assertIn('Guarantees (Rules.game six)',proof)
        self.assertIn('(proj₁ proven0) (proj₂ proven0)',proof)

    def test_collector_requires_exact_root_coverage(self):
        with self.assertRaises(ValueError):closed.collector_source([self.b,self.c],{self.b:('M','bound')})
        with self.assertRaises(ValueError):closed.collector_source([self.b],{self.b:('M','bound'),self.c:('N','bound')})
        text=closed.collector_source([self.b,self.c],{self.b:('M','bound'),self.c:('N','bound')})
        self.assertIn('allUpper : AllUpper rootCodes',text)
        self.assertIn('R0.bound , (R1.bound , (tt))',text)
        self.assertIn('Guarantees (Rules.game six) black (upperGoal 4)',text)
        self.assertNotIn('postulate',text)


if __name__=='__main__':unittest.main()
