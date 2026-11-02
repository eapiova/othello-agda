#!/usr/bin/env python3
"""Cheap sampler patch/codec checks. No native build, graph run or Agda."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import native_layout_samples6 as sample


class Samples(unittest.TestCase):
    def fixture(self):
        b = 'b'+'0'*12;w = 'w'+'1'*12
        return [
            dict(kind='row',part=1,row=0,state=b,body='F2KR3',references=[0,1]),
            dict(kind='row',part=1,row=1,state=w,body='PC0L',references=[]),
            dict(kind='states',part=0,rows=2,text=b+w),
            dict(kind='states',part=1,rows=2,text=b+w),
            dict(kind='complete',parts=2,records=4,tokens=8,selected_rows=2,
                 record_cap=1000,output_limit_bytes=1024**2,max_entries=200,
                 max_tokens=32000,selected=[1]),
        ]

    def decode(self, items, suffix=''):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'sample.jsonl'
            path.write_text(''.join(json.dumps(i)+'\n' for i in items)+suffix)
            return sample.decode_samples(path)

    def test_generated_reversible_patch_guards(self):
        raw = sample.layout.wire.solve6.SOURCE.read_text()
        result = sample.generated_source(raw)
        self.assertIn('sample_record(P,O,turn,body,refs)',result)
        self.assertIn('size_t owner=(assigned&LAYOUT_OWNER)/200;',result)
        self.assertIn('layout_part_count*200+layout_part_entries-1',result)
        self.assertIn('full wire output forbidden for samples',result)
        self.assertIn('sample_states=layout_allocate(sample_record_cap*13)',result)
        self.assertEqual(result,sample.generated_source(raw))
        # Both composing generators enforce exact inverse patching themselves.
        self.assertNotEqual(result,sample.layout.generated_source(raw))

    def test_small_sample(self):
        items = self.fixture();items[1]['body']='PC0L'
        result = self.decode(items)
        self.assertEqual(result['cases'][0]['body_text'],'F2K0;R31;PC0L')
        self.assertEqual(result['cases'][0]['references'],[0,1])
        self.assertEqual(result['cases'][0]['dependencies'],[0,1])
        self.assertEqual(result['cases'][0]['tokens'],6)
        self.assertEqual(result['states'][0]['rows'],2)

    def test_numeric_conversion(self):
        self.assertEqual(sample.number(37),'10;')
        self.assertEqual(sample.number(6990000),sample.number(6990000))
        self.assertEqual(sample.convert_body('R7',[37]),('R710;',1))
        with self.assertRaises(ValueError):sample.number(20000000)

    def test_negative_artifacts(self):
        base = self.fixture();base[1]['body']='PC0L'
        variants = []
        variants.append(base[:-1])
        variants.append([base[0],base[0],*base[1:]])
        variants.append([*base[:2],base[2],base[2],*base[3:]])
        variants.append([*base,base[0]])
        variants.append([base[0],base[2],base[1],*base[3:]])
        variants.append([*base[:2],base[3],base[4]])
        edits = [(0,'row',1),(0,'references',[200,1]),(0,'references',[0,2]),(0,'references',[0]),
                 (0,'references',[0,1,0]),(0,'body','L"'),(0,'body','F_L'),
                 (0,'body','K'),(0,'body','LL'),(0,'body','C_L'),
                 (0,'state','x'+'0'*12),(2,'text','b'+'0'*11),
                 (2,'rows',1),(4,'selected',[1,1]),(4,'selected',[0]),
                 (4,'selected',[40000]),(4,'selected_rows',1),
                 (4,'record_cap',200),(4,'record_cap',8000001),
                 (4,'output_limit_bytes',33*1024**2),(4,'max_entries',1),
                 (4,'max_tokens',1),(4,'records',1),(4,'parts',1),
                 (4,'tokens',1)]
        for index,key,value in edits:
            changed=copy.deepcopy(base);changed[index][key]=value;variants.append(changed)
        for index, variant in enumerate(variants):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):self.decode(variant)
        with self.assertRaises(ValueError):self.decode(base[:-1],'{"kind":"complete"}')
        with self.assertRaises(ValueError):self.decode([], '{"kind":"row","kind":"row"}\n')

    def test_body_parser(self):
        self.assertEqual(sample.convert_body('F0',[]),('F0',1))
        for body,refs in [('P',[]),('R8',[0]),('S1;',[]),('K',[-1]),('L',[0])]:
            with self.subTest(body=body):
                with self.assertRaises(ValueError):sample.convert_body(body,refs)


if __name__ == '__main__':unittest.main()
