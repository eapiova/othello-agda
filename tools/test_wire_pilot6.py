#!/usr/bin/env python3
"""Rule, reference-order and streamed-shard regression fixtures."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import compact_shared6 as compact
from generate6 import encode_state
import ref
import wire_pilot6 as pilot


class WirePilotTests(unittest.TestCase):
    def test_missing_reply_wrong_player_and_truncation_fail_closed(self):
        root=encode_state(ref.initial(6))
        for text in ('F3;LLL','C0;L','P','S80;'):
            with self.assertRaises(ValueError):pilot.validate_entry(root,text,set(),{},'lower')

    def test_full_citation_state_and_declared_references_are_checked(self):
        s=ref.State(6,(2,)*36,ref.WHITE);key=encode_state(s)
        pilot.validate_entry(key,'L',set(),{},'lower')
        with self.assertRaises(ValueError):pilot.validate_entry(key,'K',{key},{},'lower')
        known={'b'+key[1:]:0}
        with self.assertRaises(ValueError):pilot.validate_entry(key,'K',{key},known,'lower')
        known={key:0}
        other=encode_state(s._replace(turn=ref.BLACK))
        with self.assertRaises(ValueError):pilot.validate_entry(other,'R0;',{key},known,'lower')
        with self.assertRaises(ValueError):pilot.validate_entry(key,'L',set(),known,'lower')

    def test_two_streamed_shards_keep_actual_bound_and_dependency(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)/'results';base.mkdir()
            representative='b1'+'2'*35;root='b'+'2'*35+'1'
            raw=(compact.pack_state(representative)+'\tL\t\n'+
                 compact.pack_state(root)+'\tR2\t'+compact.pack_state(representative)+'\n').encode()
            wire=base/'wire';wire.write_bytes(raw)
            report=base/'native.json'
            native=dict(format='othello-census-wire6-run-v1',status='complete-untrusted-wire',
                wire_complete=True,native_complete=True,donor_unchanged=True,table_unchanged=True,
                wire_output_sha256=hashlib.sha256(raw).hexdigest(),root_key=root,
                request=dict(direction='lower',threshold=4),counts=dict(wire_records=2,unique_dag_nodes=1))
            report.write_text(json.dumps(native))
            output=base/'prepared'
            pilot.emit(SimpleNamespace(wire=wire,report=report,output=output,max_records=10,
                max_tokens=100,max_entries=1,max_source_bytes=100000))
            plan=json.loads((output/'plan.json').read_text())
            self.assertEqual(plan['roots'][0]['key'],root)
            self.assertEqual([t['dependencies'] for t in plan['targets'] if t['kind']=='part'],[[],[0]])
            self.assertTrue(plan['scalar_replay_complete'])
            self.assertFalse(plan['accepted'])
            for name,digest in plan['generated_hashes'].items():
                self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(),digest)
            self.assertIn('decodeCompactEntries', (output/plan['targets'][0]['path']).read_text())


if __name__=='__main__':unittest.main()
