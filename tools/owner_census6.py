#!/usr/bin/env python3
"""Read-only footprint of the accepted root5 citation prefix; never proof input."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from assembly6 import interfaces, sha
from interface_census6 import VERSION, census_file, decompress, warning_fields
from provenance import digest_entries, source_identity
from run_job import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--expected-report-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    previous = args.previous.resolve()
    if sha(previous / 'final.json') != args.expected_report_sha256:
        raise ValueError('citation report differs')
    report = json.loads((previous / 'final.json').read_text())
    phases = report['phases']
    if (report['format'] != 'othello-owner-packed6-v1' or
            report['status'] != 'phase-failed' or report['accepted'] or
            len(phases) != 76 or not all(p['expected_outcome_met'] for p in phases[:-1]) or
            phases[-1]['label'] != 'Binding' or phases[-1]['expected_outcome_met'] or
            phases[-1]['record']['exit_code'] != 251 or
            report['certificate_parts_rechecked'] != 0 or
            report['checked_sample_lower_roots'] != 5 or report['postulates'] != 0 or
            not report['generated_sources_unchanged'] or not report['prefix_donor_unchanged']):
        raise ValueError('requires the preserved, incomplete citation-prefix checkpoint')
    root = Path(report['check_root'])
    identity, pool = source_identity(root), interfaces(root)
    if (len(pool) != 409 or pool != report['final_interfaces'] or
            digest_entries(pool) != report['interfaces_sha256'] or
            identity['source_sha256'] != report['source_sha256']):
        raise ValueError('citation sources or interfaces differ')
    rows = {}
    by_module = {}
    for name, digest in pool.items():
        row = census_file(root / name, digest)
        row.update(warning_fields(decompress((root / name).read_bytes())))
        rows[name] = row
        match = re.search(r'/agda/src/(.+)\.agdai$', name)
        if not match:
            raise ValueError('unrecognized interface path')
        by_module[match[1].replace('/', '.')] = name

    # This lexical graph is a diagnostic, not evidence for a theorem/import.
    # Agda's own receipts remain the authority for checked dependencies.
    graph = {}
    for source in (root / 'src').rglob('*.agda'):
        module = '.'.join(source.relative_to(root / 'src').with_suffix('').parts)
        graph[module] = sorted(set(re.findall(
            r'^\s*(?:open\s+)?import\s+([A-Za-z0-9_.]+)',
            source.read_text(), re.M)))

    def summary(names):
        keys = ('compressed_bytes', 'payload_bytes', 'nodes', 'node_words',
                'saved_meta_bindings', 'signature_definitions', 'warnings',
                'unsupported_indexed_match_warnings')
        return dict(interfaces=len(names), **{
            key: sum(rows[name][key] for name in names) for key in keys})

    def closure(start):
        seen, pending = set(), [start]
        while pending:
            module = pending.pop()
            if module not in seen:
                seen.add(module)
                pending.extend(graph.get(module, []))
        names = {by_module[m] for m in seen if m in by_module}
        return dict(modules=sorted(seen), summary=summary(names))

    result = dict(format='othello-owner-census6-v1',
        scope='read-only encoded footprint and lexical imports; no new kernel claim',
        interface_format_version=VERSION, previous=str(previous),
        previous_report_sha256=args.expected_report_sha256,
        source_sha256=identity['source_sha256'],
        interfaces_sha256=digest_entries(pool), totals=summary(pool),
        generated_totals=summary([n for n in pool if '/OwnerPacked6/' in n]),
        records=rows, largest_by_nodes=sorted(rows, key=lambda n: rows[n]['nodes'], reverse=True)[:20],
        lexical_closures={m: closure(m) for m in (
            'Tests.OwnerPacked6.Binding', 'Tests.OwnerPacked6.Data1',
            'Tests.OwnerPacked6.Proof1', 'Tests.DirectCitations6.Root')})
    if interfaces(root) != pool or source_identity(root) != identity:
        raise ValueError('diagnostic changed its proof donor')
    result.update(donor_sources_unchanged=True, donor_interfaces_unchanged=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, result)
    print(json.dumps({k: result[k] for k in ('format', 'totals', 'generated_totals')}), flush=True)


if __name__ == '__main__':
    main()
