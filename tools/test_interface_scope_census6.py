"""Hand-encoded scope fixtures distinguish scalars from typed references."""
import struct
import unittest

from interface_scope_census6 import scope_fields


def payload(nodes, root):
    raw = struct.pack('<Iq', root, len(nodes))
    for node in nodes:
        raw += struct.pack('<q', len(node))
        for i in range(0, len(node) - 1, 2):
            raw += struct.pack('<Q', node[i] << 32 | node[i + 1])
        if len(node) % 2:
            raw += struct.pack('<I', node[-1])
    return raw


class ScopeCensus(unittest.TestCase):
    def fixture(self):
        # 99 is an uninterpreted name key/value, never a node pointer here.
        nodes = [(), (99, 99), (1, 0, 0, 0), (0, 2), (3,),
                 (0, 0, 4, 1, 0), (99, 5), (0, 6, 0, 0, 0)]
        root = [0] * 24
        root[7] = 7
        nodes.append(tuple(root))
        return nodes

    def test_typed_maps_namespace_and_counts(self):
        result = scope_fields(payload(self.fixture(), 8))
        self.assertEqual(result['scope_modules'], 1)
        self.assertEqual(result['scope_namespaces'], 1)
        self.assertEqual(result['scope_import_keys'], 1)
        self.assertEqual(result['scope_name_keys'], 1)
        self.assertEqual(result['scope_module_keys'], 0)
        self.assertEqual(result['largest_scope_name_key_counts'], [1])

    def test_rejects_wrong_shapes_bad_namespace_and_truncated_input(self):
        for index, replacement in ((7, (0,)), (6, (0,)),
                                   (3, (3, 2)), (4, (3, 3))):
            nodes = self.fixture()
            nodes[index] = replacement
            with self.subTest(index=index), self.assertRaises(ValueError):
                scope_fields(payload(nodes, 8))
        with self.assertRaises(ValueError):
            scope_fields(payload(self.fixture(), 8)[:20])
