#!/usr/bin/env python3
"""Use accepted pruned owners in the unchanged opaque citation checker.

No certificate is recomputed. Only exact citation membership is checked in a
fresh scope, then the accepted generic closure proves the original invariant.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

import assembly6
import bench6
import global_assembly6 as assembly
import owner_capsule_full6 as full
import owner_cuts6 as cuts
import owner_pruned6 as pruned
import owner_single6 as single
from provenance import digest_entries, source_identity
from run_job import positive

PREFIX = 'Tests.OwnerRebind6'
DIRECTORY = 'src/Tests/OwnerRebind6'


def generated(donor):
    sources, phases, partition = single.generated(donor)
    _, _, owners = pruned.generated(donor)
    mapping = {}
    for row in owners['bindings']:
        old = (donor/row['original_source']).read_text()
        module = re.search(r'^module (\S+) where$', old, re.M)[1]
        mapping[module] = f'{pruned.PREFIX}.{row["module"]}'
    result = {}
    for path, text in sources.items():
        text = text.replace(single.PREFIX, PREFIX)
        for old, new in mapping.items():
            # Replace imported namespaces only; state literals and proof terms
            # remain exactly those of the accepted conditional certificate.
            text = re.sub(r'^(import )'+re.escape(old)+r'( as \S+)$',
                          lambda m: m[1]+new+m[2], text, flags=re.M)
            text = re.sub(r'^(  import )'+re.escape(old)+r'( as \S+)$',
                          lambda m: m[1]+new+m[2], text, flags=re.M)
        if re.search(r'^\s*import Tests\.(DirectCitations6\.Root|OwnerLower6\.Root5\.Assemble)', text, re.M):
            raise ValueError('the old full owner closure is still imported')
        result[path.replace(single.DIRECTORY, DIRECTORY)] = text
    partition.update(pruned_owner_bindings_reused=9, single_complete_citation_scope=True,
        original_membership_obligations_unchanged=True, conditional_parts_rechecked=0)
    return result, phases, partition


def verified_prefix(args, original_pool, machine, sources):
    # This stages the already checked opaque API, input decoder and generic
    # closure. Unused old citation facts are retained, but never imported.
    inherited = full.verified_prefix(args, original_pool, machine, sources)
    previous = args.pruned_donor.resolve()
    r, root, identity, pool = full.checkpoint(previous, args.expected_pruned_sha256, machine)
    expected_sources, _, _ = pruned.generated(root)
    labels = ['R4P114']+[f'R5Assemble{i}' for i in range(6)]+['R5Part24','R5Part25','R5Part26']
    if (r['format'] != 'othello-owner-pruned6-v1' or r['status'] != 'phase-failed' or r['accepted'] or
            [p['label'] for p in r['phases']] != labels or
            not all(p['expected_outcome_met'] for p in r['phases'][:-1]) or
            r['phases'][-1]['expected_outcome_met'] or len(pool) != 336 or
            r['borrowed_interfaces'] != original_pool or r['certificate_parts_rechecked'] != 0 or
            r['generated_source_hashes'] != cuts.pilot.source_hashes(expected_sources)):
        raise ValueError('requires all nine accepted pruned owner bindings and the preserved failed join')
    full.receipt_chain(previous, r, original_pool, machine)
    merged = Path(inherited['root'])
    borrowed = dict(inherited['interfaces'])
    selected = {}
    for phase in r['phases'][:-1]:
        target = phase['target']
        assembly.hardlink(root/target, merged/target)
        for name, digest in phase['own_interfaces'].items():
            if name in borrowed or assembly6.sha(root/name) != digest:
                raise ValueError('new accepted owner interface conflicts with the generic prefix')
            assembly.hardlink(root/name, merged/name)
            borrowed[name] = digest
            selected[name] = digest
    bench6.refresh_manifest(merged, origin={k:identity[k] for k in ('revision','dirty')})
    if (len(borrowed) != 345 or assembly6.interfaces(merged) != borrowed or
            source_identity(root) != identity or assembly6.interfaces(root) != pool):
        raise ValueError('staging changed a proof donor')
    inherited.update(identity=source_identity(merged), interfaces=borrowed,
        interfaces_sha256=digest_entries(borrowed), pruned_owner_donor=str(previous),
        pruned_owner_report_sha256=args.expected_pruned_sha256,
        pruned_owner_source_sha256=identity['source_sha256'],
        pruned_owner_interfaces=selected, pruned_owner_bindings_reused=9)
    return inherited


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('previous','prefix-donor','packed-donor','pruned-donor','output','runs-root'):
        p.add_argument('--'+name, type=Path, required=True)
    for name in ('previous','prefix','packed','pruned'):
        p.add_argument('--expected-'+name+'-sha256', required=True)
    p.add_argument('--agda', required=True)
    p.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(p.parse_args(), generator=generated, directory=DIRECTORY,
        report_format='othello-owner-rebind6-v1', prefix_validator=verified_prefix)['accepted'] else 2)
