#!/usr/bin/env python3
"""Probe scope compaction of actual citation proofs, preserving all certificates.

The opaque checked type is reused. Membership/association are re-elaborated
only to measure a new single-module, private-import layout; no conditional
certificate is repeated. The preserved 409-interface checkpoint is untouched.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

import global_assembly6 as assembly
import independent_lower6 as independent
import owner_cuts6 as cuts
import owner_packed6 as packed
import owner_split6 as split
from run_job import positive

PREFIX = 'Tests.OwnerCapsule6'
DIRECTORY = 'src/Tests/OwnerCapsule6'


def header(name):
    return cuts.pilot.local_options(assembly.HEADER + f'module {PREFIX}.{name} where\n\n')


def capsule_source(index, start, states, routing, modules, *, entire=False):
    owners = sorted({routing[s] for s in states})
    indices = {owner: i for i, owner in enumerate(owners)}
    dependencies = assembly.COMMON
    dependencies += 'open import Tests.OwnerLists6.Lookup\n'
    dependencies += 'open import Tests.OwnerTrees6.Lookup using (trees)\n'
    dependencies += 'open import Tests.OwnerOpaque6.Lists\n'
    dependencies += 'import Tests.OwnerLists6.Inputs as I\n'
    dependencies += ''.join(f'import {modules[a]} as {a}\n'
        for a in sorted({e.split('.')[0] for e in owners}))
    text = header(f'Chunk{index}') + 'private\n'
    text += ''.join('  ' + line + '\n' if line else '\n' for line in dependencies.splitlines())
    rows = 'I.entries' if entire else f'takeL 64 (dropL {start} I.entries)'
    text += f'''
rows : List (SharedEntry (State six))
rows = {rows}

private
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

abstract
  sound : Citations Fast.fastGame6 white (lowerGoal 4) rows
  sound = acceptedCitations keyed6 Fast.fastGame6 white (lowerGoal 4)
    sources tables hints rows association accepted
'''
    return text


def generated(donor):
    original = (donor / f'{split.DIRECTORY}/Assemble6Split2.agda').read_text()
    routing = cuts.routing(original)
    ordered = sorted(routing)
    wire = independent.state_wire(ordered)
    conditional = (donor / 'src/Tests/OwnerLower6/Root5/Part26.agda').read_text()
    if conditional.split('\nimports = ', 1)[1].split('\n', 1)[0] != (
            f'shardStates keyed6 (fromMaybe [] (decodeCompactEntries "{wire}"))'):
        raise ValueError('original conditional input differs')
    modules = {alias: module for module, alias in re.findall(
        r'^import (\S+) as (\S+)$', original, re.M)}
    states = ordered[8:72]
    if len(states) != 64:
        raise ValueError('requires the unchanged first new 64-state citation slice')
    source = capsule_source(1, 8, states, routing, modules)
    return {f'{DIRECTORY}/Chunk1.agda': source}, [('Chunk1', 60, False)], dict(
        citation_states=64, chunk_start=8, scope_compaction=True,
        original_opaque_api_reused=True, exact_original_import_literal=True,
        conditional_part_rechecked=False, complete_input_invariant=False,
        standalone_lower_root_completed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'prefix-donor', 'output', 'runs-root'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-previous-sha256', required=True)
    parser.add_argument('--expected-prefix-sha256', required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(parser.parse_args(), generator=generated,
        directory=DIRECTORY, report_format='othello-owner-capsule-probe6-v1',
        prefix_validator=packed.verified_prefix, complete_lower_root=False)['accepted'] else 2)
