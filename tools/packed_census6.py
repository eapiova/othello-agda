#!/usr/bin/env python3
"""Read-only footprint of the completed packed sample, never proof input."""
import argparse
import json
from pathlib import Path

from assembly6 import interfaces
from interface_census6 import VERSION,census_file
from provenance import digest_entries,source_identity
from run_job import atomic_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();previous=args.previous.resolve()
    final=json.loads((previous/'packed.json').read_text())
    audit=json.loads((previous/'phase-records.json').read_text())
    if (final['status']!='collector-failed' or final['accepted'] or
            final['checked_sample_upper_roots']!=100 or final['completed_groups']!=list(range(10)) or
            len(final['phases'])!=274 or not all(p['accepted'] for p in final['phases'][:-1]) or
            final['phases'][-1]['label']!='packed-all100' or final['phases'][-1]['accepted'] or
            not final['prefix_sources_unchanged'] or not final['prefix_interface_hashes_unchanged']):
        raise ValueError('requires the completed packed sample and preserved checkpoint')
    root=Path(final['resumed_from'])/'check';pool=audit['final_interfaces']
    identity=source_identity(root)
    if len(pool)!=305 or interfaces(root)!=pool or identity['source_sha256']!=final['source_sha256']:
        raise ValueError('source or interface provenance differs')
    rows={name:census_file(root/name,digest) for name,digest in pool.items()}
    totals={key:sum(row[key] for row in rows.values()) for key in
        ('compressed_bytes','payload_bytes','nodes','node_words','node_array_bytes',
         'saved_meta_bindings','signature_definitions','string_characters','lazy_text_bytes','strict_text_bytes')}
    if source_identity(root)!=identity or interfaces(root)!=pool:
        raise ValueError('diagnostic changed a proof donor')
    atomic_json(args.output,dict(format='othello-packed-interface-census6-v1',
        scope='read-only encoded size/count diagnostic; no new kernel acceptance',
        interface_format_version=VERSION,source_sha256=identity['source_sha256'],
        interfaces_sha256=digest_entries(pool),interfaces=len(pool),records=rows,totals=totals,
        donor_sources_unchanged=True,donor_interfaces_unchanged=True))
    print(json.dumps(totals),flush=True)


if __name__=='__main__':main()
