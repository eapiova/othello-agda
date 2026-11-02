"""A local measurement must not recreate imports of child proof parts."""
import unittest

import data_only_pilot6 as pilot


class GeneratorTests(unittest.TestCase):
    def fixture(self):
        a='b'+'2'*36
        b='w'+'2'*36
        owners={a:0,b:1}
        entries=[dict(state=b,certificate='K',references=[a])]
        return a,b,owners,entries

    def test_state_data_has_no_proof_or_other_part_import(self):
        a,b,owners,entries=self.fixture()
        text=pilot.state_source(0,[dict(state=a,certificate='L',references=[])])
        self.assertNotIn('accepted',text)
        self.assertNotIn('Proven',text)
        self.assertNotIn('CheckedExport',text)
        self.assertNotIn('import Tests.DataOnlyPilot6.StateData',text)

    def test_local_part_imports_direct_state_data_only(self):
        a,b,owners,entries=self.fixture()
        text,deps,compact=pilot.part_source(1,entries,owners)
        self.assertEqual(deps,[0])
        self.assertIn('import Tests.DataOnlyPilot6.StateData0 as D0',text)
        self.assertNotIn('LocalPart0',text)
        self.assertNotIn('CheckedExport',text)
        self.assertNotIn('Proven',text)
        self.assertIn('checkDecoded expected table nothing = false',text)
        self.assertIn('sameNat expected (length es)',text)

    def test_forward_part_and_vacuous_negative_fixture_fail_closed(self):
        a,b,owners,entries=self.fixture()
        owners[a]=2
        with self.assertRaises(ValueError):pilot.part_source(1,entries,owners)
        with self.assertRaises(ValueError):
            pilot.negative_source(0,[dict(state=a,certificate='L',references=[])],{a:0})

    def test_borrowed_sources_follow_interfaces_not_other_donor_files(self):
        cache={'_build/2.9.0/agda/src/Game/Core.agdai':'x'}
        self.assertEqual(pilot.borrowed_sources(cache),{'src/Game/Core.agda'})
        self.assertNotIn('src/Everything6.agda',pilot.borrowed_sources(cache))
        with self.assertRaises(ValueError):pilot.borrowed_sources({'../../Core.agdai':'x'})


if __name__=='__main__':unittest.main()
