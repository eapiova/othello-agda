#!/usr/bin/env python3
"""Complete root5 citation assembly with opaque list facts and exact imports.

Reuse the accepted first eight citations, then check each remaining contiguous
slice once. Joining uses only safe opaque-list lemmas. The conditional part's
input trie is related to the identical decoded literal by one shape equality.
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
import global_assembly6 as assembly
import independent_lower6 as independent
import owner_cuts6 as cuts
import owner_opaque6 as opaque
import owner_split6 as split
from provenance import digest_entries, source_identity
from run_job import positive

PREFIX = 'Tests.OwnerPacked6'
DIRECTORY = 'src/Tests/OwnerPacked6'


def header(name):
    return cuts.pilot.local_options(assembly.HEADER+f'module {PREFIX}.{name} where\n\n')


def closure_source():
    return header('Closure') + '''open import Game.Core
open import Agda.Builtin.Nat using (_+_)
open import Game.Shared
open import Tests.OwnerOpaque6.Lists
import Tests.OwnerLists6.Lookup as L

abstract
  shiftCitations : ∀ {S} (g : Game S) p goal n m es →
    Citations g p goal (L.dropL (m + n) es) →
    Citations g p goal (L.dropL n (L.dropL m es))
  shiftCitations g p goal n m es tail =
    subst (Citations g p goal) (sym (L.drop-sum n m es)) tail

  closeCitations : ∀ {S} (k : Keyed S) (g : Game S) p goal es
    (imports states : Trie S) → imports ≡ shardStates k es →
    (AllT (Proven g p goal) imports → AllT (Proven g p goal) states) →
    Citations g p goal es → AllT (Proven g p goal) states
  closeCitations k g p goal es imports states shape continueProof all =
    continueProof (subst (AllT (Proven g p goal)) (sym shape)
      (treeCitations k g p goal es all))
'''


def generated(donor):
    original = (donor/f'{split.DIRECTORY}/Assemble6Split2.agda').read_text()
    routing = cuts.routing(original)
    ordered = sorted(routing)
    literal = independent.state_wire(ordered)
    part = (donor/'src/Tests/OwnerLower6/Root5/Part26.agda').read_text()
    if part.split('\nimports = ', 1)[1].split('\n', 1)[0] != f'shardStates keyed6 (fromMaybe [] (decodeCompactEntries "{literal}"))':
        raise ValueError('accepted conditional input differs')
    modules = {alias: name for name, alias in re.findall(r'^import (\S+) as (\S+)$', original, re.M)}
    sources = {f'{DIRECTORY}/Closure.agda': closure_source()}
    phases = [('Closure', 30, False)]
    segments = [dict(index=0, start=0, width=8, states=8, reused=True)]
    if len(ordered) <= 8:
        raise ValueError('requires the original stress list and its checked eight-entry prefix')
    for j, start in enumerate(range(8, len(ordered), 64), 1):
        states = ordered[start:start+64]
        owners = sorted({routing[s] for s in states})
        indices = {owner: i for i, owner in enumerate(owners)}
        data = header(f'Data{j}')+assembly.COMMON
        data += 'open import Tests.OwnerLists6.Lookup\nopen import Tests.OwnerTrees6.Lookup using (trees)\n'
        data += 'import Tests.OwnerLists6.Inputs as I\n'
        data += ''.join(f'import {modules[a]} as {a}\n' for a in sorted({e.split('.')[0] for e in owners}))
        data += f'''
rows : List (SharedEntry (State six))
rows = takeL 64 (dropL {start} I.entries)

sources : List (CheckedExport Fast.fastGame6 white (lowerGoal 4))
sources = {' ∷ '.join(owners)} ∷ []

tables : List (Trie (State six))
tables = {' ∷ '.join(o.replace('.export', '.states') for o in owners)} ∷ []

hints : List ℕ
hints = {' ∷ '.join(str(indices[routing[s]]) for s in states)} ∷ []

abstract
  association : tables ≡ trees sources
  association = refl {{x = tables}}

  accepted : listKnown keyed6 tables hints rows ≡ true
  accepted = refl {{x = true}}
'''
        proof = header(f'Proof{j}')+assembly.COMMON+f'''open import Tests.OwnerOpaque6.Lists
import {PREFIX}.Data{j} as D

abstract
  sound : Citations Fast.fastGame6 white (lowerGoal 4) D.rows
  sound = acceptedCitations keyed6 Fast.fastGame6 white (lowerGoal 4)
    D.sources D.tables D.hints D.rows D.association D.accepted
'''
        sources[f'{DIRECTORY}/Data{j}.agda'] = data
        sources[f'{DIRECTORY}/Proof{j}.agda'] = proof
        phases += [(f'Data{j}', 60, False), (f'Proof{j}', 60, False)]
        segments.append(dict(index=j, start=start, width=64, states=len(states), owners=len(owners), reused=False))
    last = segments[-1]
    end = last['start']+last['width']
    text = header('Binding')+assembly.COMMON
    text += 'open import Tests.OwnerOpaque6.Lists\nopen import Tests.OwnerLists6.Lookup using (dropL)\n'
    text += f'open import {PREFIX}.Closure\nimport Tests.OwnerLists6.Inputs as I\n'
    text += 'import Tests.OwnerLower6.Root5.Part26 as I26\nimport Tests.OwnerOpaque6.Proof0 as P0\n'
    text += ''.join(f'import {PREFIX}.Proof{row["index"]} as P{row["index"]}\n' for row in segments[1:])
    text += f'''
abstract
  finished : dropL {end} I.entries ≡ []
  finished = refl {{x = []}}

  tail{len(segments)} : Citations Fast.fastGame6 white (lowerGoal 4) (dropL {end} I.entries)
  tail{len(segments)} = emptyCitations Fast.fastGame6 white (lowerGoal 4) (dropL {end} I.entries) finished

'''
    for row in reversed(segments):
        j, start, width = row['index'], row['start'], row['width']
        text += f'''abstract
  tail{j} : Citations Fast.fastGame6 white (lowerGoal 4) (dropL {start} I.entries)
  tail{j} = joinCitations Fast.fastGame6 white (lowerGoal 4) {width} (dropL {start} I.entries)
    P{j}.sound (shiftCitations Fast.fastGame6 white (lowerGoal 4) {width} {start} I.entries tail{j+1})

'''
    text += '''module P26 where
  states : Trie (State six)
  states = I26.states

  abstract
    inputShape : I26.imports ≡ shardStates keyed6 I.entries
    inputShape = refl {x = I26.imports}

    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = closeCitations keyed6 Fast.fastGame6 white (lowerGoal 4) I.entries
      I26.imports I26.states inputShape I26.sound tail0

  export : CheckedExport Fast.fastGame6 white (lowerGoal 4)
  export = checkedExport states sound
'''
    sources[f'{DIRECTORY}/Binding.agda'] = text
    sources[f'{DIRECTORY}/Facade.agda'] = header('Facade')+f'''import {split.NAMESPACE}.Assemble6Split0 as S0
import {split.NAMESPACE}.Assemble6Split1 as S1
import {PREFIX}.Binding as S2

module P24 = S0.P24
module P25 = S1.P25
module P26 = S2.P26
'''
    root = (donor/f'{split.DIRECTORY}/Check.agda').read_text()
    if (root.count(f'module {split.NAMESPACE}.Check where') != 1 or
            root.count(f'import {split.NAMESPACE}.Assemble6 as A') != 1):
        raise ValueError('the preserved original-rule guarantee differs')
    sources[f'{DIRECTORY}/Root.agda'] = root.replace(f'module {split.NAMESPACE}.Check where',
        f'module {PREFIX}.Root where', 1).replace(f'import {split.NAMESPACE}.Assemble6 as A',
        f'import {PREFIX}.Facade as A', 1)
    phases += [('Binding', 180, False), ('Facade', 30, False), ('Root', 180, False)]
    return sources, phases, dict(citation_states=len(ordered), maximum_new_chunk_states=64,
        reused_prefix_states=8, segments=segments, exact_original_import_literal=True,
        conditional_part_rechecked=False, opaque_list_facts=True)


def verified_prefix(args, original_pool, machine, sources):
    previous = args.prefix_donor.resolve()
    if assembly6.sha(previous/'final.json') != args.expected_prefix_sha256:
        raise ValueError('opaque prefix report differs')
    r = json.loads((previous/'final.json').read_text())
    root = Path(r['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    inherited = r['reused_generic_prefix']
    old = opaque.verified_prefix(SimpleNamespace(prefix_donor=Path(inherited['previous']),
        expected_prefix_sha256=inherited['report_sha256'], expected_previous_sha256=args.expected_previous_sha256),
        original_pool, machine, {})
    original_sources, _, _ = opaque.generated(root)
    if (r['format'] != 'othello-owner-opaque-probe6-v1' or r['status'] != 'complete' or not r['accepted'] or
            [p['label'] for p in r['phases']] != ['Lists', 'Proof0', 'Tree0'] or
            not all(p['expected_outcome_met'] for p in r['phases']) or
            r['borrowed_interfaces'] != old['interfaces'] or r['machine'] != machine or
            r['previous_report_sha256'] != args.expected_previous_sha256 or
            not r['donor_unchanged'] or not r['prefix_donor_unchanged'] or not r['generated_sources_unchanged'] or
            identity['source_sha256'] != r['source_sha256'] or identity['agda_source_sha256'] != r['agda_source_sha256'] or
            pool != r['final_interfaces'] or digest_entries(pool) != r['interfaces_sha256'] or
            r['generated_source_hashes'] != cuts.pilot.source_hashes(original_sources) or
            any(assembly6.sha(root/n) != d for n, d in r['generated_source_hashes'].items())):
        raise ValueError('accepted opaque prefix, exact input or compiler changed')
    before = dict(old['interfaces'])
    for phase in r['phases']:
        record = phase['record']
        receipt = previous/'records'/(phase['label']+'.json')
        if (assembly6.sha(receipt) != phase['record_sha256'] or json.loads(receipt.read_text()) != record or
                record['borrowed_interfaces_sha256'] != digest_entries(before) or phase['cache_changes'] or
                phase['unexpected_interfaces'] or not record['accepted'] or len(phase['own_interfaces']) != 1 or
                not record['source_unchanged'] or not record['expected_source_matches'] or not record['own_target_cold'] or
                record['source_sha256'] != identity['source_sha256'] or record['executable_sha256'] != machine['agda_sha256'] or
                not all(f in record['argv'] for f in assembly6.FLAGS+['--save-metas', '-M2500M']) or
                record['rss_stop_threshold_gib'] != 3):
            raise ValueError('opaque prefix receipt differs')
        packed = phase['archived_log']
        path = previous/'records'/packed['archive_name']
        raw = gzip.decompress(path.read_bytes())
        if (assembly6.sha(path) != packed['archive_sha256'] or
                hashlib.sha256(raw).hexdigest() != phase['raw_log_sha256'] or len(raw) != record['log_bytes']):
            raise ValueError('opaque prefix log differs')
        before.update(phase['own_interfaces'])
    if before != pool or len(pool) != len(original_pool)+7:
        raise ValueError('unrecorded opaque prefix interface')
    return dict(previous=str(previous), report_sha256=args.expected_prefix_sha256, root=str(root),
        identity=identity, interfaces=pool, interfaces_sha256=digest_entries(pool),
        original_phases=r['phases'], skip_phases=0, original_eight_citations_reused=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'prefix-donor', 'output', 'runs-root'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-previous-sha256', required=True)
    parser.add_argument('--expected-prefix-sha256', required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(parser.parse_args(), generator=generated, directory=DIRECTORY,
        report_format='othello-owner-packed6-v1', prefix_validator=verified_prefix)['accepted'] else 2)
