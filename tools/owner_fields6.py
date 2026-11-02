#!/usr/bin/env python3
"""Read-only payload diagnostics of accepted owner and certificate interfaces.

Never edits an interface and never supplies a theorem premise. Field indices
are reported without pretending that arbitrary payload words are references.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

import assembly6
from interface_census6 import census_file, decompress, node_array, warning_fields
from provenance import digest_entries, source_identity
from run_job import atomic_json


def string_diagnostic(raw):
    root, nodes, offset = node_array(raw)
    count = struct.unpack_from('<q', raw, offset)[0]
    offset += 8
    if not 0 <= count <= len(raw):
        raise ValueError('invalid string-array length')
    longest = []
    for index in range(count):
        size = struct.unpack_from('<q', raw, offset)[0]
        offset += 8
        if not 0 <= size <= (len(raw)-offset)//4:
            raise ValueError('invalid string length')
        data = raw[offset:offset+size*4]
        offset += size*4
        if size >= 500:
            preview = ''.join(chr(x) for x in struct.unpack('<'+str(min(size,240))+'I', data[:960]))
            longest.append(dict(index=index, characters=size, prefix=preview))
    fields = []
    for index, value in enumerate(nodes[root]):
        fields.append(dict(index=index, encoded_word=value,
            referenced_array_arity=len(nodes[value]) if value < len(nodes) else None))
    warnings = []
    for value in nodes[nodes[root][20]]:
        w = nodes[value]
        if len(w) != 6:
            raise ValueError('unexpected warning record')
        variant = nodes[w[2]]
        warnings.append(dict(tag=variant[0], encoded_fields=list(w),
            referenced_field_arities=[len(nodes[x]) if x < len(nodes) else None for x in w]))
    return dict(root_fields=fields, warning_records=warnings,
        longest_strings=sorted(longest,key=lambda r:r['characters'],reverse=True)[:5])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--expected-report-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    previous=args.previous.resolve()
    if assembly6.sha(previous/'final.json') != args.expected_report_sha256:
        raise ValueError('owner report differs')
    r=json.loads((previous/'final.json').read_text())
    root=Path(r['check_root'])
    identity,pool=source_identity(root),assembly6.interfaces(root)
    if (r['format'] != 'othello-owner-pruned6-v1' or r['accepted'] or
            r['status'] != 'phase-failed' or len(pool) != 336 or pool != r['final_interfaces'] or
            identity['source_sha256'] != r['source_sha256'] or digest_entries(pool) != r['interfaces_sha256'] or
            not all(x['expected_outcome_met'] for x in r['phases'][:-1]) or
            r['phases'][-1]['label'] != 'R5Part26' or r['phases'][-1]['expected_outcome_met']):
        raise ValueError('requires the unchanged nine-binding checkpoint')
    names=['Tests.LowerPilot6.Group0.Part0','Tests.LowerLocal6.Root4.Group0.Part0',
        'Tests.DirectCitations6.Root','Tests.OwnerLower6.Root5.Assemble5',
        'Tests.OwnerPruned6.R4P114','Tests.OwnerPruned6.R5Assemble5',
        'Tests.OwnerPruned6.R5Part25']
    rows={}
    for module in names:
        name='_build/2.9.0/agda/src/'+module.replace('.','/')+'.agdai'
        raw=decompress((root/name).read_bytes())
        rows[module]=dict(census_file(root/name,pool[name]),**warning_fields(raw),**string_diagnostic(raw))
    if source_identity(root) != identity or assembly6.interfaces(root) != pool:
        raise ValueError('diagnostic changed the donor')
    output=dict(format='othello-owner-fields6-v1',
        scope='read-only encoded arrays and string prefixes; no proof or live-memory claim',
        previous=str(previous),previous_report_sha256=args.expected_report_sha256,
        source_sha256=identity['source_sha256'],interfaces_sha256=digest_entries(pool),
        rows=rows,donor_sources_unchanged=True,donor_interfaces_unchanged=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    atomic_json(args.output,output)
    print(json.dumps({m:{k:x[k] for k in ('payload_bytes','nodes','warnings','longest_strings')}
                      for m,x in rows.items()},indent=2))


if __name__=='__main__':
    main()
