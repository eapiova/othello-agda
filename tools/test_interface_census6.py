"""The census must reject truncated or incompatible compiler data."""
import struct
import unittest

from interface_census6 import census_payload, decompress,warning_fields


class InterfaceCensusTests(unittest.TestCase):
    def test_packed_words_and_record_maps(self):
        # A hand-encoded cb568525 fixture. Empty node 0; two definitions in
        # map 1; one meta in map 2; signature 3; Interface 4.
        nodes = [b'\0'*8,
                 struct.pack('<qQQ', 4, (10 << 32) | 11, (12 << 32) | 13),
                 struct.pack('<qQ', 2, (14 << 32) | 15),
                 struct.pack('<qQQ', 4, 1, 0)]
        fields = [0]*24
        fields[8], fields[9] = 3, 2
        nodes.append(struct.pack('<q', 24) + b''.join(
            struct.pack('<Q', (fields[i] << 32) | fields[i+1])
            for i in range(0, 24, 2)))
        raw = struct.pack('<Iq', 4, 5) + b''.join(nodes)
        raw += struct.pack('<qqqq', 0, 0, 0, 0)
        row = census_payload(raw)
        self.assertEqual(row['signature_definitions'], 2)
        self.assertEqual(row['saved_meta_bindings'], 1)
        self.assertEqual(row['nodes'], 5)
        self.assertEqual(row['node_words'], 34)
        with self.assertRaises(ValueError):
            census_payload(raw[:50])

    def test_incompatible_version_is_rejected_before_decompression(self):
        with self.assertRaises(ValueError):
            decompress(struct.pack('<QQQ', 0, 0, 42) + b'junk')

    def test_warning_tags_are_read_as_typed_records(self):
        fields=[0]*24;fields[20]=3
        nodes=[(),(40,0),(0,0,1,0,0,0),(2,),tuple(fields)]
        def encode(node):
            data=struct.pack('<q',len(node))
            for i in range(0,len(node)-1,2):
                data+=struct.pack('<Q',(node[i]<<32)|node[i+1])
            if len(node)%2:data+=struct.pack('<I',node[-1])
            return data
        raw=struct.pack('<Iq',4,len(nodes))+b''.join(map(encode,nodes))
        self.assertEqual(warning_fields(raw),dict(warnings=1,warning_tags={40:1},
                         unsupported_indexed_match_warnings=1))
        nodes[2]=(0,0,1)
        broken=struct.pack('<Iq',4,len(nodes))+b''.join(map(encode,nodes))
        with self.assertRaises(ValueError):warning_fields(broken)


if __name__ == '__main__':
    unittest.main()
