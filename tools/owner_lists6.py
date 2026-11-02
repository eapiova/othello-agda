#!/usr/bin/env python3
"""Discharge the exact decoded citation list, then build its proof trie.

The source wire is byte-identical to the preserved Part26 import definition.
Every chunk checks an actual take/drop segment of that decoded list. Generic
list joining and trie insertion construct the complete required invariant.
No whole-target Boolean trie traversal or certificate recheck is performed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

import compact_shared6 as compact
import global_assembly6 as assembly
import independent_lower6 as independent
import owner_cuts6 as cuts
import owner_split6 as split
import owner_trees6 as trees
from run_job import positive

PREFIX = 'Tests.OwnerLists6'
DIRECTORY = 'src/Tests/OwnerLists6'
CHUNK = 64


def header(name):
    return cuts.pilot.local_options(assembly.HEADER + f'module {PREFIX}.{name} where\n\n')


def helper_source():
    return header('Lookup') + f'''open import Game.Core
open import Agda.Builtin.Nat using (_+_)
open import Game.Shared
import Tests.DirectCitations6.Coverage as C
import {trees.PREFIX}.Lookup as T

AllL : ∀ {{A : Set}} → (A → Set) → List A → Set
AllL P [] = ⊤
AllL P (x ∷ xs) = P x × AllL P xs

takeL : ∀ {{A : Set}} → ℕ → List A → List A
takeL zero xs = []
takeL (suc n) [] = []
takeL (suc n) (x ∷ xs) = x ∷ takeL n xs

dropL : ∀ {{A : Set}} → ℕ → List A → List A
dropL zero xs = xs
dropL (suc n) [] = []
dropL (suc n) (x ∷ xs) = dropL n xs

listKnown : ∀ {{S}} → Keyed S → List (Trie S) → List ℕ → List (SharedEntry S) → Bool
listKnown k ts [] [] = true
listKnown k ts [] (e ∷ es) = false
listKnown k ts (i ∷ is) [] = false
listKnown k ts (i ∷ is) (e ∷ es) =
  T.knownTree k ts i (entryState e) ∧ listKnown k ts is es

private
  left : ∀ a b → a ∧ b ≡ true → a ≡ true
  left true b e = refl
  left false b ()

  right : ∀ a b → a ∧ b ≡ true → b ≡ true
  right true b e = e
  right false b ()

abstract
  joinTake : ∀ {{A}} (P : A → Set) n xs →
    AllL P (takeL n xs) → AllL P (dropL n xs) → AllL P xs
  joinTake P zero xs pre tail = tail
  joinTake P (suc n) [] pre tail = tt
  joinTake P (suc n) (x ∷ xs) (px , pre) tail = px , joinTake P n xs pre tail

  tree-all : ∀ {{S}} (k : Keyed S) (P : S → Set) es →
    AllL (λ e → P (entryState e)) es → AllT P (shardStates k es)
  tree-all k P [] all = tt
  tree-all k P (sharedEntry s c ∷ es) (ps , all) =
    insert-all (key k s) (shardStates k es) (tree-all k P es all) ps

  drop-nil : ∀ {{A}} n → dropL {{A}} n [] ≡ []
  drop-nil zero = refl
  drop-nil (suc n) = refl

  drop-sum : ∀ {{A}} n m (xs : List A) → dropL n (dropL m xs) ≡ dropL (m + n) xs
  drop-sum n zero xs = refl
  drop-sum n (suc m) [] = drop-nil n
  drop-sum n (suc m) (x ∷ xs) = drop-sum n m xs

  known-sound : ∀ {{S}} (k : Keyed S) (g : Game S) p goal
    (owners : List (CheckedExport g p goal)) ts i s →
    ts ≡ T.trees owners → T.knownTree k ts i s ≡ true → Proven g p goal s
  known-sound k g p goal owners ts i s shape accepted =
    C.ownerKnown-sound k g p goal owners i s
      (trans (sym (T.knownTree-agree k g p goal owners i s))
        (subst (λ tables → T.knownTree k tables i s ≡ true) shape accepted))

  listKnown-sound : ∀ {{S}} (k : Keyed S) (g : Game S) p goal
    (owners : List (CheckedExport g p goal)) ts is es →
    ts ≡ T.trees owners → listKnown k ts is es ≡ true →
    AllL (λ e → Proven g p goal (entryState e)) es
  listKnown-sound k g p goal owners ts [] [] shape accepted = tt
  listKnown-sound k g p goal owners ts [] (e ∷ es) shape ()
  listKnown-sound k g p goal owners ts (i ∷ is) [] shape ()
  listKnown-sound k g p goal owners ts (i ∷ is) (e ∷ es) shape accepted =
    known-sound k g p goal owners ts i (entryState e) shape
      (left (T.knownTree k ts i (entryState e)) (listKnown k ts is es) accepted) ,
    listKnown-sound k g p goal owners ts is es shape
      (right (T.knownTree k ts i (entryState e)) (listKnown k ts is es) accepted)
'''


def fixtures():
    good = header('Fixtures') + f'''open import Game.Core hiding (terminal)
open import Game.Shared
open import {PREFIX}.Lookup
open import Tests.DirectCitations6.Fixtures using (keyedBool; terminal; source)
open import {trees.PREFIX}.Lookup using (trees)

rows : List (SharedEntry Bool)
rows = sharedEntry true known ∷ []

accepted : listKnown keyedBool (trees (source ∷ [])) (0 ∷ []) rows ≡ true
accepted = refl

proved : AllT (Proven terminal white (λ s → s)) (shardStates keyedBool rows)
proved = tree-all keyedBool (Proven terminal white (λ s → s)) rows
  (listKnown-sound keyedBool terminal white (λ s → s) (source ∷ [])
    (trees (source ∷ [])) (0 ∷ []) rows refl accepted)

missing : listKnown keyedBool (trees (source ∷ [])) [] rows ≡ false
missing = refl

wrong-owner : listKnown keyedBool (trees (source ∷ [])) (1 ∷ []) rows ≡ false
wrong-owner = refl

joined : AllL (λ b → b ≡ b) (true ∷ false ∷ [])
joined = joinTake (λ b → b ≡ b) 1 (true ∷ false ∷ [])
  (refl , tt) (refl , tt)
'''
    bad = header('MissingOwner') + f'''open import Game.Core
open import Game.Shared
open import {PREFIX}.Lookup
open import Tests.DirectCitations6.Fixtures using (keyedBool; source)
open import {trees.PREFIX}.Lookup using (trees)

incorrect : listKnown keyedBool (trees (source ∷ [])) []
  (sharedEntry true known ∷ []) ≡ true
incorrect = refl {{x = true}}
'''
    return {f'{DIRECTORY}/Fixtures.agda': good, f'{DIRECTORY}/MissingOwner.agda': bad}


def rejected_missing(record, text, own):
    return bool(record['exit_code'] and record['exit_code'] > 0 and not record['stop_reason'] and
        not own and re.findall(r'error: \[([^]]+)\]', text) == ['UnequalTerms'] and
        'Checking incorrect.' in text and 'listKnown keyedBool' in text and
        re.search(r'\b(true\s+and\s+false|false\s+and\s+true)\s+are not equal at type Bool', text))


def generated(donor, namespace=PREFIX, generated_directory=DIRECTORY, batch_size=CHUNK, reuse_helpers=False):
    PREFIX, DIRECTORY, CHUNK = namespace, generated_directory, batch_size
    if not 1 <= CHUNK <= 64 or (not reuse_helpers and namespace != 'Tests.OwnerLists6'):
        raise ValueError('requires a bounded batch and preserved generic helper namespace')
    helper_prefix = 'Tests.OwnerLists6' if reuse_helpers else PREFIX

    def header(name):
        return cuts.pilot.local_options(assembly.HEADER + f'module {PREFIX}.{name} where\n\n')

    original = (donor/f'{split.DIRECTORY}/Assemble6Split2.agda').read_text()
    routing = cuts.routing(original)
    ordered = sorted(routing)
    literal = independent.state_wire(ordered)
    part = (donor/'src/Tests/OwnerLower6/Root5/Part26.agda').read_text()
    expected = f'imports = shardStates keyed6 (fromMaybe [] (decodeCompactEntries "{literal}"))'
    if part.split('\nimports = ', 1)[1].split('\n', 1)[0] != expected.removeprefix('imports = '):
        raise ValueError('full import literal differs from the accepted conditional part')
    modules = {alias: name for name, alias in re.findall(r'^import (\S+) as (\S+)$', original, re.M)}
    sources = {} if reuse_helpers else {f'{DIRECTORY}/Lookup.agda': helper_source(), **fixtures()}
    data = header('Inputs') + assembly.COMMON + f'''
entries : List (SharedEntry (State six))
entries = fromMaybe [] (decodeCompactEntries "{literal}")
'''
    if not reuse_helpers:
        sources[f'{DIRECTORY}/Inputs.agda'] = data
    phases = [] if reuse_helpers else [('Lookup', 30, False), ('Fixtures', 20, False), ('MissingOwner', 15, True), ('Inputs', 30, False)]
    summary = []
    for j, start in enumerate(range(0, len(ordered), CHUNK)):
        states = ordered[start:start+CHUNK]
        owners = sorted({routing[s] for s in states})
        indices = {owner: i for i, owner in enumerate(owners)}
        text = header(f'Chunk{j}') + assembly.COMMON
        text += f'open import {helper_prefix}.Lookup\nopen import {trees.PREFIX}.Lookup using (trees)\n'
        text += f'import {helper_prefix}.Inputs as I\n'
        text += ''.join(f'import {modules[a]} as {a}\n' for a in sorted({o.split('.')[0] for o in owners}))
        text += f'''
rows : List (SharedEntry (State six))
rows = takeL {CHUNK} (dropL {start} I.entries)

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

  sound : AllL (λ e → Proven Fast.fastGame6 white (lowerGoal 4) (entryState e)) rows
  sound = listKnown-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
    sources tables hints rows association accepted
'''
        sources[f'{DIRECTORY}/Chunk{j}.agda'] = text
        phases.append((f'Chunk{j}', 80, False))
        summary.append(dict(index=j, start=start, states=len(states), owners=len(owners)))
    count = len(summary)
    text = header('Binding') + assembly.COMMON
    text += f'open import {helper_prefix}.Lookup\nimport {helper_prefix}.Inputs as I\n'
    text += 'import Tests.OwnerLower6.Root5.Part26 as I26\n'
    text += ''.join(f'import {PREFIX}.Chunk{j} as C{j}\n' for j in range(count))
    text += '''
Goal : SharedEntry (State six) → Set
Goal e = Proven Fast.fastGame6 white (lowerGoal 4) (entryState e)

'''
    text += f'''abstract
  tail{count} : AllL Goal (dropL {count*CHUNK} I.entries)
  tail{count} = tt

'''
    for j in reversed(range(count)):
        text += f'''abstract
  tail{j} : AllL Goal (dropL {j*CHUNK} I.entries)
  tail{j} = joinTake Goal {CHUNK} (dropL {j*CHUNK} I.entries) C{j}.sound
    (subst (AllL Goal) (sym (drop-sum {CHUNK} {j*CHUNK} I.entries)) tail{j+1})

'''
    text += '''module P26 where
  states : Trie (State six)
  states = I26.states

  abstract
    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = I26.sound (tree-all keyed6 (Proven Fast.fastGame6 white (lowerGoal 4)) I.entries tail0)

  export : CheckedExport Fast.fastGame6 white (lowerGoal 4)
  export = checkedExport states sound
'''
    sources[f'{DIRECTORY}/Binding.agda'] = text
    sources[f'{DIRECTORY}/Facade.agda'] = header('Facade') + f'''import {split.NAMESPACE}.Assemble6Split0 as S0
import {split.NAMESPACE}.Assemble6Split1 as S1
import {PREFIX}.Binding as S2

module P24 = S0.P24
module P25 = S1.P25
module P26 = S2.P26
'''
    root = (donor/f'{split.DIRECTORY}/Check.agda').read_text()
    sources[f'{DIRECTORY}/Root.agda'] = root.replace(
        f'module {split.NAMESPACE}.Check where', f'module {PREFIX}.Root where', 1).replace(
        f'import {split.NAMESPACE}.Assemble6 as A', f'import {PREFIX}.Facade as A', 1)
    phases += [('Binding', 180, False), ('Facade', 30, False), ('Root', 180, False)]
    return sources, phases, dict(citation_states=len(ordered), maximum_states=CHUNK,
        exact_original_import_literal=True, chunks=summary, conditional_part_rechecked=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output', 'runs-root'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-previous-sha256', required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--kernel-cpu-budget', type=positive, required=True)
    args = parser.parse_args()
    args.prefix_donor = None
    args.expected_prefix_sha256 = None
    raise SystemExit(0 if cuts.run(args, generator=generated, directory=DIRECTORY,
        report_format='othello-owner-lists6-v1', negative_guard=rejected_missing)['accepted'] else 2)
