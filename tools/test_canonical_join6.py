import copy
from pathlib import Path
import tempfile
import unittest

from canonical_join6 import emit_join


class JoinPreparation(unittest.TestCase):
    def setUp(self):
        self.full = dict(prefix='Tests.Full', complete=True, rows_per_part=200, rows=810, parts=5)
        self.units = [dict(part=j, rows=min(200,810-200*j),row_prefix=f'Tests.Sample.Rows{j}',
                           bridge_prefix=f'Tests.Sample.Bridge{j}') for j in (1,3,4)]
        self.tmp = tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name)/'results'/'joint'

    def test_same_G_and_C_semantic_partial(self):
        r=emit_join(self.output,self.full,self.units)
        source=(self.output/'src/Tests/CanonicalCombined6/Root.agda').read_text()
        self.assertTrue(r['common_body_map']);self.assertFalse(r['joint_target_is_import_only'])
        self.assertEqual(r['owned_rows'],410)
        self.assertIn('globalBodies = (M.branch 600 P1.bodies (M.branch 800 P3.bodies P4.bodies))',source)
        self.assertIn('ownedTogether = (Laws.fork-pair Laws.rows-pair (Laws.fork-pair Laws.rows-pair Laws.rows-pair))',source)
        for j in (1,3,4):
            self.assertIn(f'Bridge{j}.symbolic LookupStates LookupBodies sameStates',source)
            self.assertIn(f'(R.compatible LookupBodies bodyRoute{j} sameBodies)',source)
            self.assertIn(f'Family.A.Partial LookupStates LookupBodies P{j}.states',source)
        self.assertIn('Family.A.join {G = LookupStates} {C = LookupBodies} 600',source)
        self.assertIn('bodyRoute1 = (R.left refl R.here)',source)
        self.assertIn('bodyRoute4 = (R.right refl (R.right refl R.here))',source)
        self.assertNotIn('accepted = refl',source)
        self.assertTrue(r['partial_only']);self.assertFalse(r['agda_checked'])
        self.assertFalse(r['initial_problem2_proved']);self.assertFalse(r['combined_partial_coverage_proved'])
        self.assertFalse(r['optimal_initial_pair_proved']);self.assertFalse(r['production_authorized'])

    def test_deterministic_sources_and_reject_overwrite(self):
        a=emit_join(self.output,self.full,self.units)
        b=emit_join(self.output.parent/'second',self.full,list(reversed(self.units)))
        self.assertEqual(a['generated_sha256'],b['generated_sha256'])
        with self.assertRaises(ValueError):emit_join(self.output,self.full,self.units)

    def test_invalid_units_leave_no_output(self):
        variants=[]
        x=copy.deepcopy(self.units);x.append(copy.deepcopy(x[0]));variants.append(x)
        x=copy.deepcopy(self.units);x[2]['rows']=200;variants.append(x)
        x=copy.deepcopy(self.units);x[0]['row_prefix']='Tests.CanonicalCombined6.Child';variants.append(x)
        x=copy.deepcopy(self.units);x[0]['bridge_prefix']=x[1]['row_prefix'];variants.append(x)
        x=copy.deepcopy(self.units);x[0]['part']=0;variants.append(x)
        x=copy.deepcopy(self.units);x[0]['bridge_prefix']='Bad; postulate';variants.append(x)
        for x in variants:
            with self.subTest(x=x),self.assertRaises(ValueError):emit_join(self.output,self.full,x)
            self.assertFalse(self.output.exists())

    def test_symlink_parent_refused(self):
        real=self.output.parent/'real';real.mkdir(parents=True)
        link=self.output.parent/'link';link.symlink_to(real,target_is_directory=True)
        with self.assertRaises(ValueError):emit_join(link/'joint',self.full,self.units)
        self.assertFalse((real/'joint').exists())


if __name__=='__main__':unittest.main()
