"""Proof reuse boundaries, complete citations, and acyclic pilot assembly."""
import copy
import re
import unittest

import compact_shared6 as compact
import owner_lower6 as owner
from test_lower_pilot6 import fixture


class OwnerLowerTests(unittest.TestCase):
    def setUp(self):
        self.a = 'w'+'2'*36
        self.b = 'b'+'1'*35+'2'
        self.c = 'w'+'0'*35+'1'
        self.entries = [dict(state=self.a, certificate='L', references=[]),
            dict(state=self.b, certificate='R0;', references=[self.a]),
            dict(state=self.c, certificate='R0;', references=[self.b])]
        self.known = {self.a: ('Tests.Checked.Before', 'export')}

    def test_checked_boundary_removes_only_already_proved_entries(self):
        original = copy.deepcopy(self.entries)
        missing = owner.missing_closure(self.entries,self.c,self.known)
        self.assertEqual(missing,self.entries[1:])
        parts,owners = owner.partition_missing(missing,self.known)
        self.assertEqual(parts,[self.entries[1:]])
        self.assertEqual(owners,{self.a:-1,self.b:0,self.c:0})
        self.assertEqual(self.entries,original)
        # The boundary's original certificate need not be replayed: the actual
        # owner's Agda proof, full-state membership and goal are required.
        text,stats = owner.assembly_source(2,0,parts,owners,self.known)
        self.assertIn('E0.export',text)
        self.assertIn('I0.sound',text)
        self.assertIn('sources hints I0.imports coverage',text)
        self.assertIn(owner.independent.state_wire([self.a]),text)
        self.assertNotIn('importStates',text)
        self.assertEqual(stats['citations'],1)

    def test_missing_forward_or_duplicate_evidence_fails_closed(self):
        for entries,known in ((self.entries[1:],{}),
                (self.entries[::-1],{}), (self.entries,self.known)):
            with self.assertRaises(ValueError):
                owner.partition_missing(entries,known)

    def test_prior_chunk_and_current_chunk_use_their_real_exports(self):
        entries=[]
        for i,state in enumerate(fixture()['roots'][:6]):
            entries.append(dict(state=state,certificate='L' if i==0 else 'R0;',
                                references=[] if i==0 else [entries[i-1]['state']]))
        parts=[[entry] for entry in entries]
        owners={entry['state']:i for i,entry in enumerate(entries)}
        text,stats=owner.assembly_source(2,1,parts,owners,{})
        self.assertIn('import Tests.OwnerLower6.Root2.Assemble0 as E0',text)
        self.assertIn('sources = E0.P3.export ∷ []',text)
        self.assertIn('sources = P4.export ∷ []',text)
        self.assertEqual(stats['parts'],[4,5])
        self.assertEqual(stats['citations'],2)

    def test_new_parts_keep_literal_certificates_and_the_original_goal(self):
        plan=fixture()
        root=plan['roots'][2]
        plan['entries'][2].update(certificate='R0;',references=[self.a])
        plan['entries'].insert(0,self.entries[0])
        before=copy.deepcopy(plan)
        row=owner.layout(plan,2,self.known)
        self.assertEqual(plan,before)
        text=row['sources']['src/Tests/OwnerLower6/Root2/Part0.agda']
        self.assertIn(compact.encode([(root,'R0;')]),text)
        self.assertIn('Tests.IndependentLower6.Checker',text)
        self.assertNotRegex(text,re.compile(r'^import Tests\..*Part\d+',re.M))
        root_source=row['sources']['src/Tests/OwnerLower6/Root2/Check.agda']
        self.assertIn('Guarantees (Rules.game six) white (lowerGoal 4) position',root_source)
        self.assertIn('A.P0.sound',root_source)
        self.assertEqual(row['new_known'][root],('Tests.OwnerLower6.Root2.Assemble0','P0.export'))

    def test_already_proven_root_requires_membership_without_replaying_a_part(self):
        plan=fixture()
        root=plan['roots'][2]
        row=owner.layout(plan,2,{root:('Tests.Checked.Before','P7.export')})
        self.assertEqual(row['parts'],0)
        self.assertEqual([p['kind'] for p in row['phases']],['root'])
        self.assertIn('A.P7.sound',row['sources']['src/Tests/OwnerLower6/Root2/Check.agda'])
        self.assertEqual(owner.HELDOUT,list(range(10,20)))
        self.assertFalse(set(owner.TRAINING)&set(owner.HELDOUT))


if __name__=='__main__':
    unittest.main()
