import unittest
from explicit_exports6 import pack_tables
import global_assembly6 as assembly
from warning_tables6 import warning_source,WARNING,OLD,NEW


class WarningTablesTests(unittest.TestCase):
    def fixture(self):
        state='b'+'1'*36
        text,_,_=assembly.part_source(0,[dict(state=state,certificate='L',references=[])],
                                     {state:0},'upper')
        text=pack_tables(text).replace(assembly.PREFIX,OLD+'.Group0')
        text=text.replace('--safe ','--save-metas --safe ',1)
        return text.replace('  shape = refl\n','  shape = refl {x = states}\n').replace(
            '  accepted = refl\n','  accepted = refl {x = true}\n')

    def test_only_warning_option_and_namespace_change(self):
        text=self.fixture();changed=warning_source(text)
        self.assertEqual(changed.replace(' '+WARNING,'',1).replace(NEW,OLD),text)
        self.assertIn('  accepted = refl {x = true}',changed)
        self.assertIn('shardBy-sound',changed)

    def test_missing_acceptance_or_safe_option_rejected(self):
        text=self.fixture()
        with self.assertRaises(ValueError):warning_source(text.replace('  accepted = refl {x = true}',''))
        with self.assertRaises(ValueError):warning_source(text.replace('--safe ',''))


if __name__=='__main__':unittest.main()
