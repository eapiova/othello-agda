"""Untrusted bridge generation/admission tests, with no Agda or native run."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from native_layout_samples6 import number
from new_row_bridge6 import emit,approved,ANSWER,SCOPE


def fixture():
    a='wQQQQQQQQQQQQ'
    chunks=[dict(part=j,rows=n,module='Tests.FixtureFull.StateData'+str(j),
                 text_sha256=hashlib.sha256((a*n).encode()).hexdigest()) for j,n in [(0,200),(1,200),(2,1)]]
    full=dict(complete=True,rows=401,parts=3,rows_per_part=200,prefix='Tests.FixtureFull',wire_sha256='a'*64,chunks=chunks)
    sample=dict(wire_sha256='a'*64,wire_rows=401,
                cases=[dict(part=2,rows=1,state_text=a,body_text='K'+number(200),
                            references=[200],dependencies=[1,2],tokens=1)],
                states={1:dict(rows=200,text=a*200),2:dict(rows=1,text=a)})
    return full,sample


class NewRowBridge(unittest.TestCase):
    def test_exact_literal_agreement_and_symbolic_only_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'results/check';f,s=fixture()
            report=emit(root,f,s,part=2,row_prefix='Tests.FixtureRows2',prefix='Tests.BridgeFixture',batch_size=1)
            self.assertEqual((report['source_modules'],report['demanded_state_chunks'],report['owned_rows']),(3,2,1))
            self.assertEqual(report['new_boolean_rows'],0)
            self.assertFalse(report['agda_checked']);self.assertFalse(report['initial_problem2_proved'])
            text=(root/'src/Tests/BridgeFixture/Root.agda').read_text()
            self.assertIn('symbolic G C sameStates sameBodies = Part.linked G C',text)
            self.assertIn('R.aligned C bodyPath sameBodies',text)
            self.assertIn('partial = symbolic G C',text)
            self.assertIn('decodeCompactState "wQQQQQQQQQQQQ"',text)
            self.assertNotIn('accepted = refl',text)
            self.assertNotIn('checkPart',text)
            for name,h in report['generated_sha256'].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),h)
            old={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with self.assertRaises(ValueError):emit(root,f,s,part=2,row_prefix='Tests.FixtureRows2')
            self.assertTrue(all(p.read_bytes()==b for p,b in old.items()))

    def test_mismatched_metadata_rejected_before_writes(self):
        changes=[lambda f,s:f.update(complete=False),lambda f,s:f.update(wire_sha256='b'*64),
                 lambda f,s:f['chunks'][1].update(text_sha256='0'*64),
                 lambda f,s:s['states'][1].update(rows=199),
                 lambda f,s:s['cases'][0].update(dependencies=[2]),
                 lambda f,s:s['cases'][0].update(dependencies=[2,1]),
                 lambda f,s:s['cases'][0].update(state_text='b000000000000')]
        for change in changes:
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'results/check';f,s=fixture();change(f,s)
                with self.assertRaises(ValueError):emit(root,f,s,part=2,row_prefix='Tests.FixtureRows2')
                self.assertFalse(root.exists())

    def test_old_row_test_consent_cannot_authorize_full_map_memory(self):
        raw=b'pending-plan-only';auth=dict(approved=True,answer=ANSWER,scope=SCOPE,
            plan_sha256=hashlib.sha256(raw).hexdigest(),cpu_max_seconds=300,hard_memory_gib=12,
            artifact_cap_gib=12,free_disk_gib=80,part=34176,new_boolean_rows=0,
            native_search_allowed=False,production_authorized=False)
        approved(raw,auth)
        for change in [dict(hard_memory_gib=3),dict(part=34175),dict(new_boolean_rows=200),
                       dict(answer='Sì, autorizzo questo test di nuove righe'),dict(production_authorized=True),
                       dict(plan_sha256='0'*64)]:
            with self.subTest(change=change):
                other=copy.deepcopy(auth);other.update(change)
                with self.assertRaises(ValueError):approved(raw,other)


if __name__=='__main__':unittest.main()
