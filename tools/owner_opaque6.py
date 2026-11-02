#!/usr/bin/env python3
"""Probe an opaque proof-list type without changing its checked meaning."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import assembly6
import global_assembly6 as assembly
import owner_cuts6 as cuts
import owner_queries6 as queries
import owner_separated6 as separated
from provenance import digest_entries, source_identity
from run_job import positive

PREFIX = 'Tests.OwnerOpaque6'
DIRECTORY = 'src/Tests/OwnerOpaque6'


def header(name):
    return cuts.pilot.local_options(assembly.HEADER+f'module {PREFIX}.{name} where\n\n')


def generated(donor):
    helper = header('Lists') + '''open import Game.Core
open import Game.Shared
import Tests.OwnerLists6.Lookup as L

abstract
  Citations : ∀ {S} → Game S → Player → (S → Bool) → List (SharedEntry S) → Set
  Citations g p goal es = L.AllL (λ e → Proven g p goal (entryState e)) es

  acceptedCitations : ∀ {S} (k : Keyed S) (g : Game S) p goal
    (owners : List (CheckedExport g p goal)) ts hints es →
    ts ≡ Tests.OwnerTrees6.Lookup.trees owners → L.listKnown k ts hints es ≡ true →
    Citations g p goal es
  acceptedCitations k g p goal owners ts hints es shape accepted =
    L.listKnown-sound k g p goal owners ts hints es shape accepted

  joinCitations : ∀ {S} (g : Game S) p goal n es →
    Citations g p goal (L.takeL n es) → Citations g p goal (L.dropL n es) →
    Citations g p goal es
  joinCitations g p goal n es first tail =
    L.joinTake (λ e → Proven g p goal (entryState e)) n es first tail

  emptyCitations : ∀ {S} (g : Game S) p goal es → es ≡ [] → Citations g p goal es
  emptyCitations g p goal .[] refl = tt

  treeCitations : ∀ {S} (k : Keyed S) (g : Game S) p goal es →
    Citations g p goal es → AllT (Proven g p goal) (shardStates k es)
  treeCitations k g p goal es all = L.tree-all k (Proven g p goal) es all
'''
    # This import makes the association function's exact module provenance explicit.
    helper = helper.replace('import Tests.OwnerLists6.Lookup as L\n',
        'import Tests.OwnerLists6.Lookup as L\nimport Tests.OwnerTrees6.Lookup\n')
    proof = header('Proof0')+assembly.COMMON+f'''open import {PREFIX}.Lists
import Tests.OwnerSeparated6.Data0 as D

abstract
  sound : Citations Fast.fastGame6 white (lowerGoal 4) D.rows
  sound = acceptedCitations keyed6 Fast.fastGame6 white (lowerGoal 4)
    D.sources D.tables D.hints D.rows D.association D.accepted
'''
    tree = header('Tree0')+assembly.COMMON+f'''open import {PREFIX}.Lists
import {PREFIX}.Proof0 as P
import Tests.OwnerSeparated6.Data0 as D

abstract
  sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) (shardStates keyed6 D.rows)
  sound = treeCitations keyed6 Fast.fastGame6 white (lowerGoal 4) D.rows P.sound
'''
    return {f'{DIRECTORY}/Lists.agda': helper, f'{DIRECTORY}/Proof0.agda': proof,
        f'{DIRECTORY}/Tree0.agda': tree}, [('Lists', 30, False), ('Proof0', 60, False), ('Tree0', 60, False)], dict(
        citation_states=8, opaque_type_definition='the original AllL of Proven',
        checked_boolean_reused=True, first_eight_only=True, standalone_lower_root_completed=False)


def verified_prefix(args, original_pool, machine, sources):
    previous = args.prefix_donor.resolve()
    if assembly6.sha(previous/'final.json') != args.expected_prefix_sha256:
        raise ValueError('separated prefix report differs')
    r = json.loads((previous/'final.json').read_text())
    root = Path(r['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    inherited = r['reused_generic_prefix']
    prior_args = SimpleNamespace(prefix_donor=Path(inherited['previous']),
        expected_prefix_sha256=inherited['report_sha256'], expected_previous_sha256=args.expected_previous_sha256)
    old = queries.verified_prefix(prior_args, original_pool, machine, {})
    original_sources, _, _ = separated.generated(Path(json.loads((Path(r['previous'])/'final.json').read_text())['check_root']))
    if (r['format'] != 'othello-owner-separated-probe6-v1' or r['status'] != 'phase-failed' or r['accepted'] or
            [p['label'] for p in r['phases']] != ['Data0', 'Proof0'] or
            [p['expected_outcome_met'] for p in r['phases']] != [True, False] or
            r['phases'][-1]['record']['exit_code'] != 251 or r['phases'][-1]['record']['stop_reason'] or
            r['borrowed_interfaces'] != old['interfaces'] or r['machine'] != machine or
            r['previous_report_sha256'] != args.expected_previous_sha256 or
            not r['donor_unchanged'] or not r['prefix_donor_unchanged'] or not r['generated_sources_unchanged'] or
            identity['source_sha256'] != r['source_sha256'] or identity['agda_source_sha256'] != r['agda_source_sha256'] or
            pool != r['final_interfaces'] or digest_entries(pool) != r['interfaces_sha256'] or
            r['generated_source_hashes'] != cuts.pilot.source_hashes(original_sources) or
            any(assembly6.sha(root/n) != d for n, d in r['generated_source_hashes'].items())):
        raise ValueError('separately accepted Boolean data, compiler or source changed')
    before = dict(old['interfaces'])
    for phase in r['phases']:
        record = phase['record']
        receipt = previous/'records'/(phase['label']+'.json')
        if (assembly6.sha(receipt) != phase['record_sha256'] or json.loads(receipt.read_text()) != record or
                record['borrowed_interfaces_sha256'] != digest_entries(before) or
                phase['cache_changes'] or phase['unexpected_interfaces'] or
                not record['source_unchanged'] or not record['expected_source_matches'] or not record['own_target_cold'] or
                record['source_sha256'] != identity['source_sha256'] or
                record['executable_sha256'] != machine['agda_sha256'] or
                not all(f in record['argv'] for f in assembly6.FLAGS+['--save-metas', '-M2500M']) or
                record['rss_stop_threshold_gib'] != 3):
            raise ValueError('separated prefix receipt differs')
        if phase['archived_log']:
            packed = phase['archived_log']
            path = previous/'records'/packed['archive_name']
            if assembly6.sha(path) != packed['archive_sha256']:
                raise ValueError('separated prefix archive differs')
            raw = gzip.decompress(path.read_bytes())
        else:
            raw = (previous/'records'/(phase['label']+'.log')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != phase['raw_log_sha256'] or len(raw) != record['log_bytes']:
            raise ValueError('separated prefix log differs')
        if phase['expected_outcome_met']:
            if not record['accepted'] or len(phase['own_interfaces']) != 1:
                raise ValueError('Boolean data was not accepted')
        elif record['accepted'] or phase['own_interfaces']:
            raise ValueError('failed soundness proof was incorrectly adopted')
        before.update(phase['own_interfaces'])
    if before != pool or len(pool) != len(original_pool)+4:
        raise ValueError('unrecorded separated-prefix interface')
    return dict(previous=str(previous), report_sha256=args.expected_prefix_sha256, root=str(root),
        identity=identity, interfaces=pool, interfaces_sha256=digest_entries(pool),
        original_phases=r['phases'], skip_phases=0, checked_boolean_data_reused=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'prefix-donor', 'output', 'runs-root'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-previous-sha256', required=True)
    parser.add_argument('--expected-prefix-sha256', required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(parser.parse_args(), generator=generated, directory=DIRECTORY,
        report_format='othello-owner-opaque-probe6-v1', prefix_validator=verified_prefix,
        complete_lower_root=False)['accepted'] else 2)
