"""Streaming provenance/partition tests; these do not assert Agda acceptance."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from full_state_map6 import generate


class FullStateMap(unittest.TestCase):
    def emit(self, root, states, **changes):
        raw=b''.join(s.encode()+b'\tL\t\n' for s in states)
        wire=root/'input.wire';wire.write_bytes(raw)
        args=dict(expected_sha256=hashlib.sha256(raw).hexdigest(),expected_rows=len(states),
                  expected_parts=(len(states)+199)//200,prefix='Tests.FullMapFixture',map_batch=1)
        args.update(changes)
        return generate(wire,root/'results/check',**args)

    def test_streamed_partition_reuses_only_exact_old_literals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a='b000000000000';b='wQQQQQQQQQQQQ'
            old=root/'old.agda';old.write_bytes(b'preserved accepted source\n')
            digest=hashlib.sha256((a*200).encode()).hexdigest()
            report=self.emit(root,[a]*200+[b],reuse={0:dict(module='Tests.Accepted.StateData0',text_sha256=digest)})
            self.assertTrue(report['complete']);self.assertFalse(report['agda_checked'])
            self.assertEqual((report['rows'],report['parts']), (201,2))
            self.assertEqual(report['game_rows_checked'],0)
            self.assertEqual(report['last_encoded_state'],b)
            check=root/'results/check';folder=check/'src/Tests/FullMapFixture'
            self.assertFalse((folder/'StateData0.agda').exists())
            self.assertIn('Tests.Accepted.StateData0',(folder/'Map0.agda').read_text())
            self.assertIn('M.rows 200 1',(folder/'Map1.agda').read_text())
            self.assertIn('M.branch 200 L.stateMap R.stateMap',(folder/'Map2.agda').read_text())
            self.assertEqual(old.read_bytes(),b'preserved accepted source\n')
            for n,h in report['generated_sha256'].items():
                self.assertEqual(hashlib.sha256((check/n).read_bytes()).hexdigest(),h)
            self.assertFalse(report['initial_problem2_proved'])
            self.assertFalse(report['production_authorized'])
            with self.assertRaises(ValueError):
                generate(root/'input.wire',check,expected_sha256=report['wire_sha256'],
                    expected_rows=201,expected_parts=2,prefix='Tests.FullMapFixture')

    def test_bad_input_never_exports_a_complete_root(self):
        for changes in [dict(expected_sha256='0'*64),dict(expected_rows=202),
                        dict(reuse={0:dict(module='Tests.Accepted.Data',text_sha256='0'*64)}),
                        dict(max_source_bytes=10)]:
            with self.subTest(changes=changes),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                with self.assertRaises(ValueError):self.emit(root,['b000000000000']*201,**changes)
                self.assertFalse((root/'results/check/src/Tests/FullMapFixture/Root.agda').exists())

    def test_malformed_or_truncated_record_fails_closed(self):
        for raw in [b'b000000000000\tL\t',b'bRRRRRRRRRRRR\tL\t\n',
                    b'b000000000000\tL\tx\n',b'b000000000000\tL\t\t\n']:
            with self.subTest(raw=raw),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);wire=root/'input.wire';wire.write_bytes(raw)
                with self.assertRaises(ValueError):
                    generate(wire,root/'results/check',expected_sha256=hashlib.sha256(raw).hexdigest(),
                        expected_rows=1,expected_parts=1,prefix='Tests.BadWire')
                self.assertFalse((root/'results/check/src/Tests/BadWire/Root.agda').exists())

    def test_wrong_partition_or_namespace_creates_no_output(self):
        for changes in [dict(expected_parts=3),dict(prefix='../src/Unsafe'),
                        dict(map_batch=True),dict(reuse={2:dict(module='Tests.Old.Data',text_sha256='0'*64)})]:
            with self.subTest(changes=changes),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                with self.assertRaises(ValueError):self.emit(root,['b000000000000']*201,**changes)
                self.assertFalse((root/'results/check').exists())


if __name__=='__main__':unittest.main()
