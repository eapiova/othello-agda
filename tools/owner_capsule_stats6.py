#!/usr/bin/env python3
"""Read-only census of the checked private-import capsule, not a proof input."""
import argparse
import json
from pathlib import Path

from assembly6 import interfaces, sha
from interface_census6 import census_file, decompress, warning_fields
from provenance import digest_entries, source_identity
from run_job import atomic_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--expected-report-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    previous = args.previous.resolve()
    if sha(previous / 'final.json') != args.expected_report_sha256:
        raise ValueError('capsule report differs')
    r = json.loads((previous / 'final.json').read_text())
    if (r['format'] != 'othello-owner-capsule-probe6-v1' or not r['accepted'] or
            r['status'] != 'complete' or len(r['phases']) != 1 or
            r['phases'][0]['label'] != 'Chunk1' or not r['phases'][0]['expected_outcome_met'] or
            not r['generated_sources_unchanged'] or not r['prefix_donor_unchanged'] or
            r['certificate_parts_rechecked'] != 0 or r['checked_sample_lower_roots'] != 5):
        raise ValueError('requires the completed partial capsule probe')
    root = Path(r['check_root'])
    identity, pool = source_identity(root), interfaces(root)
    if (pool != r['final_interfaces'] or digest_entries(pool) != r['interfaces_sha256'] or
            identity['source_sha256'] != r['source_sha256']):
        raise ValueError('capsule source/cache changed')
    own = r['phases'][0]['own_interfaces']
    if len(own) != 1 or not all(pool.get(n) == d for n, d in own.items()):
        raise ValueError('capsule was not checked')
    records = {}
    for name, digest in own.items():
        row = census_file(root / name, digest)
        row.update(warning_fields(decompress((root / name).read_bytes())))
        records[name] = row
    if source_identity(root) != identity or interfaces(root) != pool:
        raise ValueError('diagnostic changed a donor')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, dict(format='othello-owner-capsule-census6-v1',
        scope='read-only capsule interface diagnostic; no new acceptance',
        report_sha256=args.expected_report_sha256, records=records,
        donor_sources_unchanged=True, donor_interfaces_unchanged=True))
    print(json.dumps(records), flush=True)


if __name__ == '__main__':
    main()
