#!/usr/bin/env python3
"""Assemble root5 through compact scopes; reuse exact accepted certificates.

Fresh citation wrappers change only interface layout. An immutable staging
prefix reuses the accepted first capsule and the original generic closure.
The new mutable check cache receives independent interface copies.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

import assembly6
import bench6
import global_assembly6 as assembly
import owner_capsule6 as capsule
import owner_cuts6 as cuts
import owner_packed6 as packed
import owner_split6 as split
from provenance import digest_entries, source_files, source_identity
from run_job import positive

PREFIX, DIRECTORY = capsule.PREFIX, capsule.DIRECTORY


def generated(donor):
    original = (donor / f'{split.DIRECTORY}/Assemble6Split2.agda').read_text()
    routing = cuts.routing(original)
    ordered = sorted(routing)
    old, _, partition = packed.generated(donor)  # Includes the exact input guard.
    modules = {alias: module for module, alias in re.findall(
        r'^import (\S+) as (\S+)$', original, re.M)}
    sources, phases = {}, []
    for j, start in enumerate(range(8, len(ordered), 64), 1):
        source = capsule.capsule_source(j, start, ordered[start:start+64], routing, modules)
        if j != 1:
            sources[f'{DIRECTORY}/Chunk{j}.agda'] = source
            phases.append((f'Chunk{j}', 60, False))
    binding = old[f'{packed.DIRECTORY}/Binding.agda']
    binding = binding.replace(f'module {packed.PREFIX}.Binding where', f'module {PREFIX}.Binding where', 1)
    binding = re.sub(r'import '+re.escape(packed.PREFIX)+r'\.Proof(\d+) as P(\d+)',
        lambda m: f'import {PREFIX}.Chunk{m[1]} as P{m[2]}', binding)
    imports, body = binding.split('\nabstract\n  finished :', 1)
    first, imports = imports.split(' where\n', 1)
    # Private names remain available in public proof types but do not reexport
    # entire dependency scopes into each new interface.
    binding = first+' where\n\nprivate\n'+''.join(
        '  '+line+'\n' if line else '\n' for line in imports.strip().splitlines())
    binding += '\nabstract\n  finished :'+body
    sources[f'{DIRECTORY}/Binding.agda'] = binding
    for name in ('Facade', 'Root'):
        sources[f'{DIRECTORY}/{name}.agda'] = old[f'{packed.DIRECTORY}/{name}.agda'].replace(packed.PREFIX, PREFIX)
    phases += [('Binding', 180, False), ('Facade', 30, False), ('Root', 180, False)]
    partition.update(private_import_capsules=True, reused_capsule_states=64,
        reused_first_eight_citations=True, original_generic_closure_reused=True)
    return sources, phases, partition


def receipt_chain(previous, report, initial_pool, machine):
    before = dict(initial_pool)
    for phase in report['phases']:
        record = phase['record']
        path = previous / 'records' / (phase['label']+'.json')
        if (assembly6.sha(path) != phase['record_sha256'] or json.loads(path.read_text()) != record or
                record['borrowed_interfaces_sha256'] != digest_entries(before) or
                phase['cache_changes'] or phase['unexpected_interfaces'] or
                not record['source_unchanged'] or not record['expected_source_matches'] or
                not record['own_target_cold'] or record['source_sha256'] != report['source_sha256'] or
                record['executable_sha256'] != machine['agda_sha256'] or
                not all(f in record['argv'] for f in assembly6.FLAGS+['--save-metas', '-M2500M']) or
                record['rss_stop_threshold_gib'] != 3):
            raise ValueError('citation prefix receipt differs')
        archive = phase['archived_log']
        if archive:
            path = previous / 'records' / archive['archive_name']
            if assembly6.sha(path) != archive['archive_sha256']:
                raise ValueError('citation log archive changed')
            raw = gzip.decompress(path.read_bytes())
        else:
            raw = (previous / 'records' / (phase['label']+'.log')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != phase['raw_log_sha256'] or len(raw) != record['log_bytes']:
            raise ValueError('citation log differs')
        if phase['expected_outcome_met']:
            if not record['accepted'] or len(phase['own_interfaces']) != 1:
                raise ValueError('citation premise was not accepted')
        elif record['accepted'] or record['exit_code'] != 251 or record['stop_reason'] or phase['own_interfaces']:
            raise ValueError('failed interface load incorrectly adopted')
        before.update(phase['own_interfaces'])
    if before != report['final_interfaces']:
        raise ValueError('unrecorded interface in citation prefix')


def checkpoint(previous, expected, machine):
    if assembly6.sha(previous / 'final.json') != expected:
        raise ValueError('checkpoint report differs')
    r = json.loads((previous / 'final.json').read_text())
    root = Path(r['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    if (r['machine'] != machine or pool != r['final_interfaces'] or
            digest_entries(pool) != r['interfaces_sha256'] or
            identity['source_sha256'] != r['source_sha256'] or
            identity['agda_source_sha256'] != r['agda_source_sha256'] or
            not r['donor_unchanged'] or not r['prefix_donor_unchanged'] or
            not r['generated_sources_unchanged'] or
            any(assembly6.sha(root/n) != d for n, d in r['generated_source_hashes'].items())):
        raise ValueError('checkpoint sources, binary or interfaces changed')
    return r, root, identity, pool


def verified_prefix(args, original_pool, machine, sources):
    previous = args.prefix_donor.resolve()
    r, root, identity, pool = checkpoint(previous, args.expected_prefix_sha256, machine)
    inherited = r['reused_generic_prefix']
    base = packed.verified_prefix(SimpleNamespace(prefix_donor=Path(inherited['previous']),
        expected_prefix_sha256=inherited['report_sha256'],
        expected_previous_sha256=args.expected_previous_sha256), original_pool, machine, {})
    expected_sources, _, _ = capsule.generated(root)
    if (r['format'] != 'othello-owner-capsule-probe6-v1' or not r['accepted'] or r['status'] != 'complete' or
            [p['label'] for p in r['phases']] != ['Chunk1'] or
            not r['phases'][0]['expected_outcome_met'] or len(pool) != 335 or
            r['borrowed_interfaces'] != base['interfaces'] or r['certificate_parts_rechecked'] != 0 or
            r['generated_source_hashes'] != cuts.pilot.source_hashes(expected_sources)):
        raise ValueError('requires the accepted unchanged first private capsule')
    receipt_chain(previous, r, base['interfaces'], machine)
    packed_previous = args.packed_donor.resolve()
    p, packed_root, packed_identity, packed_pool = checkpoint(
        packed_previous, args.expected_packed_sha256, machine)
    packed_sources, _, _ = packed.generated(packed_root)
    if (p['format'] != 'othello-owner-packed6-v1' or p['status'] != 'phase-failed' or p['accepted'] or
            len(p['phases']) != 76 or not all(x['expected_outcome_met'] for x in p['phases'][:-1]) or
            p['phases'][-1]['label'] != 'Binding' or p['phases'][-1]['expected_outcome_met'] or
            p['borrowed_interfaces'] != base['interfaces'] or len(packed_pool) != 409 or
            p['generated_source_hashes'] != cuts.pilot.source_hashes(packed_sources)):
        raise ValueError('requires the audited opaque batch checkpoint')
    receipt_chain(packed_previous, p, base['interfaces'], machine)
    selected = p['phases'][0]
    if selected['label'] != 'Closure':
        raise ValueError('generic closure donor differs')
    closure_source = 'src/Tests/OwnerPacked6/Closure.agda'
    merged = args.output.resolve().with_name(args.output.name+'-checked-prefix')
    if merged.exists() or args.runs_root.resolve() not in merged.parents:
        raise ValueError('requires a fresh immutable staging prefix inside runs')
    merged.mkdir()
    for name, _ in source_files(root):
        assembly.hardlink(root/name, merged/name)
    assembly.hardlink(packed_root/closure_source, merged/closure_source)
    borrowed = {**pool, **selected['own_interfaces']}
    for name, digest in borrowed.items():
        origin = root if name in pool else packed_root
        if assembly6.sha(origin/name) != digest:
            raise ValueError('selected accepted interface differs')
        assembly.hardlink(origin/name, merged/name)
    bench6.refresh_manifest(merged, origin={k: identity[k] for k in ('revision', 'dirty')})
    merged_identity = source_identity(merged)
    if (assembly6.interfaces(merged) != borrowed or source_identity(root) != identity or
            source_identity(packed_root) != packed_identity or assembly6.interfaces(packed_root) != packed_pool):
        raise ValueError('staging changed an accepted donor')
    return dict(previous=str(previous), report_sha256=args.expected_prefix_sha256,
        root=str(merged), identity=merged_identity, interfaces=borrowed,
        interfaces_sha256=digest_entries(borrowed), skip_phases=0,
        immutable_staging_only=True, original_capsule_root=str(root),
        original_capsule_source_sha256=identity['source_sha256'],
        closure_report=str(packed_previous), closure_report_sha256=args.expected_packed_sha256,
        original_eight_citations_reused=True, original_capsule_reused=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'prefix-donor', 'packed-donor', 'output', 'runs-root'):
        p.add_argument('--'+name, type=Path, required=True)
    for name in ('previous', 'prefix', 'packed'):
        p.add_argument('--expected-'+name+'-sha256', required=True)
    p.add_argument('--agda', required=True)
    p.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(p.parse_args(), generator=generated, directory=DIRECTORY,
        report_format='othello-owner-capsule-full6-v1', prefix_validator=verified_prefix)['accepted'] else 2)
