import unittest
import global_assembly6 as assembly
from explicit_exports6 import pack_tables
from scope_facade6 import scope_source


class ScopeFacadeTests(unittest.TestCase):
    def original(self):
        state,reference='b'+'1'*36,'w'+'2'*36
        part=[{'state':state,'certificate':'L','references':[reference]}]
        raw,_,_=assembly.part_source(1,part,{state:1,reference:0},'upper')
        raw=raw.replace(assembly.PREFIX,'Tests.PackedTables6.Group0')
        raw=raw.replace('--safe ','--save-metas --safe ',1)
        raw=raw.replace('  shape = refl\n','  shape = refl {x = states}\n')
        raw=raw.replace('  accepted = refl\n','  accepted = refl {x = true}\n')
        return pack_tables(raw)

    def test_certificates_and_both_checks_survive_namespace_change(self):
        old=self.original();new=scope_source(old)
        self.assertEqual(old.split('  entries :',1)[1].split('  shape :',1)[0],
                         new.split('  entries :',1)[1].split('  shape :',1)[0])
        self.assertIn('private\n  open import Othello.ProofFacade6',new)
        self.assertIn('  import Tests.ScopeFacade6.Group0.Part0 as P0',new)
        self.assertIn('\nstates : Trie (State six)',new)
        self.assertIn('checkShardBy keyed6 fastGame6 black (upperGoal 4)',new)
        self.assertIn('  shape = refl {x = states}',new)
        self.assertIn('  accepted = refl {x = true}',new)
        self.assertIn('shardBy-sound',new)

    def test_missing_witness_or_changed_safety_template_is_rejected(self):
        old=self.original()
        for changed in (old.replace('  accepted = refl {x = true}','  accepted = ?'),
                        old.replace('--safe ','')):
            with self.assertRaises(ValueError):scope_source(changed)


if __name__=='__main__':unittest.main()
