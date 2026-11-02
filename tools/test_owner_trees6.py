"""State tables must be associated to real owners before proving a citation."""
import re
import unittest

import owner_trees6 as trees
import owner_split6 as split
import test_owner_split6 as split_tests


class OwnerTreesTests(unittest.TestCase):
    def source(self):
        return split.split_sources(split_tests.OwnerSplitTests().source())[split.DIRECTORY+'/Assemble6Split2.agda']

    def test_new_boolean_path_keeps_exact_owners_hints_imports_and_goal(self):
        original=self.source();source=trees.binding_source(original)
        for name in ('sources','hints','states'):
            self.assertEqual(re.search(r'^  '+name+' = (.*)$',source,re.M)[1],
                             re.search(r'^  '+name+' = (.*)$',original,re.M)[1])
        self.assertIn('tables = S25.P25.states ∷ []',source)
        self.assertIn('association : tables ≡ trees sources',source)
        self.assertIn('association = refl {x = tables}',source)
        self.assertIn('sources tables hints I26.imports association coverage',source)
        self.assertIn('coveredTrees keyed6 tables hints I26.imports ≡ true',source)
        self.assertNotIn('coveredBy keyed6 sources',source)
        self.assertIn('I26.sound',source)

    def test_missing_association_or_changed_signature_fails_generator(self):
        with self.assertRaises(ValueError):
            trees.binding_source(self.source().replace('coverage = refl {x = true}','coverage = refl'))

    def test_generic_soundness_transfers_to_existing_checked_export_lemma(self):
        source=trees.helper_source()
        self.assertIn('ts ≡ trees es → coveredTrees k ts hints target ≡ true',source)
        self.assertIn('C.coveredBy-sound k g p goal es hints target',source)
        self.assertIn('knownIn k t s',source)
        self.assertNotIn('postulate',source)
        self.assertIn('--safe --without-K --cubical-compatible',source)

    def test_disconnected_table_needs_a_rejected_association(self):
        sources=trees.fixtures()
        self.assertIn('open import Game.Core hiding (terminal)',sources[trees.DIRECTORY+'/Fixtures.agda'])
        self.assertIn('disconnected = refl',sources[trees.DIRECTORY+'/Fixtures.agda'])
        negative=sources[trees.DIRECTORY+'/WrongAssociation.agda']
        self.assertIn('(build [] false ∷ []) ≡ trees (source ∷ [])',negative)
        self.assertIn('incorrect = refl',negative)


if __name__=='__main__':unittest.main()
