import unittest
import tempfile
from pathlib import Path
import indexed_wire_pilot6 as pilot


class WireIDs(unittest.TestCase):
    def test_file_partition_reaches_explicit_full_pilot_size_gate(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'small.wire'
            path.write_text('b1EMHMMNDPHMD\tPC1F1L\t\n')
            with self.assertRaisesRegex(ValueError,'complete accepted descendant required'):
                pilot.generate(Path(name),path)

    def test_reference_occurrences_follow_native_column(self):
        _,_,paths=pilot.skeleton([2,1,1])
        addresses={'old':(0,1),'next':(1,0)}
        self.assertEqual(pilot.indexed_body('PF2KR4C0K',['old','next','old'],addresses,paths),
                         'PF2Ka01R4ba00C0Ka01')

    def test_unknown_and_extra_reference_fail_closed(self):
        _,_,paths=pilot.skeleton([2,1,1])
        with self.assertRaises(ValueError):pilot.indexed_body('K',['absent'],{},paths)
        with self.assertRaises(ValueError):pilot.indexed_body('L',['old'],{'old':(0,0)},paths)
        with self.assertRaises(ValueError):pilot.indexed_body('R8',['old'],{'old':(0,0)},paths)

    def test_local_row_cap_and_nonuniform_paths(self):
        _,_,paths=pilot.skeleton([200,1,1,3,2])
        self.assertEqual(len(set(paths.values())),5)
        self.assertEqual(pilot.encode_id(0,199,paths),paths[0]+'5E')
        with self.assertRaises(ValueError):pilot.encode_id(0,200,paths)

    def test_solve_tokens_cannot_consume_reference_column(self):
        _,_,paths=pilot.skeleton([1,1])
        self.assertEqual(pilot.indexed_body('C0S80;K',['old'],{'old':(0,0)},paths),'C0S80;Ka00')
        with self.assertRaises(ValueError):pilot.indexed_body('?',[],{},paths)


if __name__=='__main__':unittest.main()
