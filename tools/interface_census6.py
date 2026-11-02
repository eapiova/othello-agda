#!/usr/bin/env python3
"""Read-only census of the desktop compiler's verified saved-meta interfaces.

This is a diagnostic, never a proof importer or an interface writer. The small
reader follows Agda cb568525's x86_64 serialisation format and rejects other
versions. Only aggregate sizes/counts leave the checking machine.
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import struct

from assembly6 import interfaces, sha
from provenance import digest_entries, source_identity
from run_job import atomic_json

VERSION = 202603220


def decompress(raw):
    if len(raw) < 28 or struct.unpack_from('<Q', raw, 16)[0] != VERSION:
        raise ValueError('not the expected desktop Agda interface format')
    library = ctypes.util.find_library('zstd')
    if library is None:
        raise ValueError('libzstd is unavailable')
    lib = ctypes.CDLL(library)
    lib.ZSTD_getFrameContentSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    lib.ZSTD_getFrameContentSize.restype = ctypes.c_ulonglong
    lib.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                    ctypes.c_void_p, ctypes.c_size_t]
    lib.ZSTD_decompress.restype = ctypes.c_size_t
    compressed = raw[24:]
    source = ctypes.create_string_buffer(compressed)
    size = lib.ZSTD_getFrameContentSize(source, len(compressed))
    if not 0 < size <= 64 * 1024**2:
        raise ValueError('missing or excessive zstd content size')
    destination = ctypes.create_string_buffer(size)
    if lib.ZSTD_decompress(destination, size, source, len(compressed)) != size:
        raise ValueError('interface decompression failed')
    return destination.raw


def node_array(raw):
    """Read only the pinned format's node array, preserving word order."""
    offset = 0

    def take(size):
        nonlocal offset
        if size < 0 or offset + size > len(raw):
            raise ValueError('truncated interface payload')
        result = raw[offset:offset+size]
        offset += size
        return result

    def integer():
        value = struct.unpack('<q', take(8))[0]
        if not 0 <= value <= len(raw):
            raise ValueError('invalid interface array length')
        return value

    root = struct.unpack('<I', take(4))[0]
    count = integer()
    nodes = []
    for _ in range(count):
        length = integer()
        data = take(4 * length)
        node = list(struct.unpack(f'<{length}I', data))
        # Agda packs pairs as (a << 32) | b before native-endian writes:
        # on x86_64 the low word b occurs first in the byte stream.
        for index in range(0, length - 1, 2):
            node[index], node[index+1] = node[index+1], node[index]
        nodes.append(tuple(node))
    if root >= count or len(nodes[root]) != 24:
        raise ValueError('unexpected Interface record')
    return root,nodes,offset


def census_payload(raw):
    """Count encoded arrays without interpreting or changing proof terms."""
    root,nodes,offset=node_array(raw)

    def take(size):
        nonlocal offset
        if size < 0 or offset + size > len(raw):
            raise ValueError('truncated interface payload')
        result=raw[offset:offset+size];offset+=size
        return result

    def integer():
        value=struct.unpack('<q',take(8))[0]
        if not 0 <= value <= len(raw):raise ValueError('invalid interface array length')
        return value

    node_bytes=offset-4
    histogram=Counter(map(len,nodes));words=sum(map(len,nodes))
    signature = nodes[nodes[root][8]]
    if len(signature) != 4:
        raise ValueError('unexpected Signature record')
    definitions = nodes[signature[1]]
    metas = nodes[nodes[root][9]]
    if len(definitions) % 2 or len(metas) % 2:
        raise ValueError('malformed definition or meta map')
    result = dict(payload_bytes=len(raw), node_array_bytes=node_bytes,
                  nodes=len(nodes), node_words=words,
                  node_arity_histogram=dict(sorted(histogram.items())),
                  signature_definitions=len(definitions)//2,
                  saved_meta_bindings=len(metas)//2)
    strings = integer()
    string_chars = 0
    for _ in range(strings):
        length = integer()
        take(4*length)
        string_chars += length
    result.update(strings=strings, string_characters=string_chars)
    for label in ('lazy_text', 'strict_text'):
        number = integer()
        lengths = []
        for _ in range(number):
            length = integer()
            take(length)
            lengths.append(length)
        result[label+'_items'] = number
        result[label+'_bytes'] = sum(lengths)
        result[label+'_largest_bytes'] = max(lengths, default=0)
    result['other_array_bytes'] = len(raw) - offset
    return result


def warning_fields(raw):
    """Typed cardinalities of Interface.iWarnings; no untyped graph traversal.

    cb568525 encodes Set as a list node, TCWarning as six fields, and the
    Warning sum as a tag followed by arguments. Tag 40 is IndexedMatch.
    """
    root,nodes,_=node_array(raw)
    tags=Counter()
    warnings=nodes[nodes[root][20]]
    for index in warnings:
        warning=nodes[index]
        if len(warning)!=6:raise ValueError('unexpected TCWarning record')
        variant=nodes[warning[2]]
        if not variant:raise ValueError('missing Warning constructor tag')
        tags[variant[0]]+=1
    return dict(warnings=len(warnings),warning_tags=dict(sorted(tags.items())),
                unsupported_indexed_match_warnings=tags[40])


def census_file(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('interface does not match its recorded digest')
    result = census_payload(decompress(raw))
    result.update(compressed_bytes=len(raw), sha256=expected)
    return result


def run(args):
    previous = args.previous.resolve()
    donor = previous / 'collector'
    audit = json.loads((previous/'phase-records.json').read_text())
    final = json.loads((previous/'final.json').read_text())
    if sha(previous/'final.json') != audit['final_sha256']:
        raise ValueError('completed report changed')
    if (final['format'] != 'othello-cache-resume6-v1' or
            final['status'] != 'collector-failed' or final['accepted'] or
            final['checked_regrouped_upper_roots'] != 100 or
            final['completed_groups'] != list(range(10))):
        raise ValueError('requires the completed saved-meta 100-root sample')
    expected = audit['collector_interfaces']
    identity = source_identity(donor)
    if interfaces(donor) != expected or identity['source_sha256'] != final['source_sha256']:
        raise ValueError('interface or source provenance changed')
    records = {name: census_file(donor/name, digest) for name,digest in expected.items()}
    totals = {}
    for key in ('compressed_bytes', 'payload_bytes', 'nodes', 'node_words',
                'node_array_bytes', 'saved_meta_bindings', 'signature_definitions',
                'string_characters', 'lazy_text_bytes', 'strict_text_bytes'):
        totals[key] = sum(row[key] for row in records.values())
    result = dict(format='othello-interface-census6-v1',
                  scope='read-only encoded size/count diagnostics; no new kernel acceptance',
                  interface_format_version=VERSION, source_sha256=identity['source_sha256'],
                  interfaces_sha256=digest_entries(expected), interfaces=len(expected),
                  records=records, totals=totals,
                  largest_by_nodes=sorted(records, key=lambda name:records[name]['nodes'], reverse=True)[:12])
    if interfaces(donor) != expected or source_identity(donor) != identity:
        raise ValueError('diagnostic changed a donor')
    result['donor_sources_unchanged'] = True
    result['donor_interfaces_unchanged'] = True
    atomic_json(args.output, result)
    print(json.dumps({k:v for k,v in result.items() if k != 'records'}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
