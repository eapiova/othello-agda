#!/usr/bin/env python3
"""Bounded citation assembly with owner hints and no merged proof-state trie.

Generated Agda stays outside src/. Owner hints are untrusted: each cited full
state must be found in its owner's already-proved export. No certificates are
rechecked, changed, or accepted through native execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import global_assembly6 as assembly
import independent_lower6 as independent
from independent_lower_audit6 import audit
from lower_local_plan6 import closure
import lower_pilot6 as pilot
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc

PREFIX = 'Tests.DirectCitations6'
DIRECTORY = 'src/Tests/DirectCitations6'
EXPECTED_PLAN = 'ce09d22ba8fb3f186b6510fcc161e0c73f4ef2abfb14799600e728e5a3a86e32'


def header(name):
    return pilot.local_options(assembly.HEADER + f'module {PREFIX}.{name} where\n\n')


def helper_source():
    return header('Coverage') + '''open import Game.Core
open import Game.Shared

private
  left : ∀ a b → a ∧ b ≡ true → a ≡ true
  left true b e = refl
  left false b ()

  right : ∀ a b → a ∧ b ≡ true → b ≡ true
  right true b e = e
  right false b ()

ownerKnown : ∀ {S} {g : Game S} {p goal} → Keyed S →
  List (CheckedExport g p goal) → ℕ → S → Bool
ownerKnown k [] i s = false
ownerKnown k (e ∷ es) zero s = knownIn k (exportStates e) s
ownerKnown k (e ∷ es) (suc i) s = ownerKnown k es i s

ownerKnown-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal es i s →
  ownerKnown {g = g} {p = p} {goal = goal} k es i s ≡ true → Proven g p goal s
ownerKnown-sound k g p goal [] i s ()
ownerKnown-sound k g p goal (e ∷ es) zero s accepted =
  knownIn-sound k g p goal (exportStates e) s (exportSound e) accepted
ownerKnown-sound k g p goal (e ∷ es) (suc i) s accepted =
  ownerKnown-sound k g p goal es i s accepted

ownedValue : ∀ {S} {g : Game S} {p goal} → Keyed S →
  List (CheckedExport g p goal) → Maybe ℕ → Maybe S → Bool
ownedValue k es owner nothing = true
ownedValue k es nothing (just s) = false
ownedValue k es (just i) (just s) = ownerKnown k es i s

ownedValue-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal es owner m →
  ownedValue {g = g} {p = p} {goal = goal} k es owner m ≡ true → AllM (Proven g p goal) m
ownedValue-sound k g p goal es owner nothing accepted = tt
ownedValue-sound k g p goal es nothing (just s) ()
ownedValue-sound k g p goal es (just i) (just s) accepted =
  ownerKnown-sound k g p goal es i s accepted

-- The target controls recursion. Hints cannot omit a target branch or state.
coveredBy : ∀ {S} {g : Game S} {p goal} → Keyed S →
  List (CheckedExport g p goal) → Trie ℕ → Trie S → Bool
coveredBy k es hints tip = true
coveredBy k es tip (node m l r) = false
coveredBy k es (node owner x y) (node m l r) =
  ownedValue k es owner m ∧ (coveredBy k es x l ∧ coveredBy k es y r)

coveredBy-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal es hints target →
  coveredBy {g = g} {p = p} {goal = goal} k es hints target ≡ true → AllT (Proven g p goal) target
coveredBy-sound k g p goal es hints tip accepted = tt
coveredBy-sound k g p goal es tip (node m l r) ()
coveredBy-sound k g p goal es (node owner x y) (node m l r) accepted =
  ownedValue-sound k g p goal es owner m
    (left (ownedValue k es owner m) rest accepted) ,
  (coveredBy-sound k g p goal es x l
    (left (coveredBy k es x l) (coveredBy k es y r) parts) ,
   coveredBy-sound k g p goal es y r
    (right (coveredBy k es x l) (coveredBy k es y r) parts))
  where
  rest = coveredBy k es x l ∧ coveredBy k es y r
  parts = right (ownedValue k es owner m) rest accepted
'''


def fixture_source():
    return header('Fixtures') + f'''open import Game.Core hiding (terminal)
open import Game.Certificate using (leaf)
open import Game.Composite using (stateEquality)
open import Game.Shared
open import {PREFIX}.Coverage

private
  boolEq : Bool → Bool → Bool
  boolEq false false = true
  boolEq true true = true
  boolEq _ _ = false

  boolEq-sound : ∀ x y → boolEq x y ≡ true → x ≡ y
  boolEq-sound false false e = refl
  boolEq-sound false true ()
  boolEq-sound true false ()
  boolEq-sound true true e = refl

keyedBool : Keyed Bool
keyedBool = keyed (λ _ → []) (stateEquality boolEq boolEq-sound)

terminal : Game Bool
terminal = record {{ turn = λ _ → white ; next = λ _ → [] ; forcedPass = λ _ → false }}

source : CheckedExport terminal white (λ s → s)
source = checkedExport (build [] true)
  (build-all {{A = Bool}} {{P = Proven terminal white (λ s → s)}}
    [] {{a = true}} (leaf , refl))

good : coveredBy keyedBool (source ∷ []) (build [] 0) (build [] true) ≡ true
good = refl

proved : AllT (Proven terminal white (λ s → s)) (build [] true)
proved = coveredBy-sound keyedBool terminal white (λ s → s)
  (source ∷ []) (build [] 0) (build [] true) good

wrong-owner : coveredBy keyedBool (source ∷ []) (build [] 1) (build [] true) ≡ false
wrong-owner = refl

missing-owner : coveredBy {{g = terminal}} {{p = white}} {{goal = λ s → s}}
  keyedBool [] (build [] 0) (build [] true) ≡ false
missing-owner = refl

collision : coveredBy keyedBool (source ∷ []) (build [] 0) (build [] false) ≡ false
collision = refl

omitted-branch : coveredBy keyedBool (source ∷ []) (build [] 0)
  (node nothing (build [] true) tip) ≡ false
omitted-branch = refl

empty : coveredBy keyedBool (source ∷ []) tip tip ≡ true
empty = refl
'''


def import_source():
    return (header('Imports') +
            ''.join(f'import {independent.OLD}.Part{i} as P{i}\n' for i in range(114)) +
            ''.join(f'import {independent.PREFIX}.Part{i} as I{i}\n' for i in range(114, 118)))


def root_source(root, parts, owners):
    if len(parts) != 118 or owners[root] != 117:
        raise ValueError('requires the fixed root-local suffix')
    text = header('Root') + assembly.COMMON
    text += f'open import {PREFIX}.Coverage using (coveredBy; coveredBy-sound)\n'
    text += import_source().split('where\n\n', 1)[1]
    text += '''
-- Compact strings here only construct owner hints; they carry no evidence.
routesFor : ℕ → String → Trie ℕ → Trie ℕ
routesFor owner wire tail = add (fromMaybe [] (decodeCompactEntries wire)) tail
  where
  add : List (SharedEntry (State six)) → Trie ℕ → Trie ℕ
  add [] tail = tail
  add (e ∷ es) tail = insertT (key6 (entryState e)) owner (add es tail)
'''
    summaries = []
    for index in range(114, 118):
        external = sorted({state for entry in parts[index] for state in entry['references']
                           if owners[state] != index})
        dependencies = sorted({owners[state] for state in external})
        if not external or any(owner >= index for owner in dependencies):
            raise ValueError('missing or non-acyclic citation owners')
        groups = [[state for state in external if owners[state] == owner] for owner in dependencies]
        sources = ' ∷ '.join(f'P{owner}.export' for owner in dependencies) + ' ∷ []'
        hints = 'tip'
        for j, states in reversed(list(enumerate(groups))):
            hints = f'routesFor {j} "{independent.state_wire(states)}" ({hints})'
        text += f'''
module P{index} where
  sources : List (CheckedExport Fast.fastGame6 white (lowerGoal 4))
  sources = {sources}

  hints : Trie ℕ
  hints = {hints}

  states : Trie (State six)
  states = I{index}.states

  abstract
    coverage : coveredBy keyed6 sources hints I{index}.imports ≡ true
    coverage = refl {{x = true}}

    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = I{index}.sound
      (coveredBy-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
        sources hints I{index}.imports coverage)

  export : CheckedExport Fast.fastGame6 white (lowerGoal 4)
  export = checkedExport states sound
'''
        summaries.append(dict(part=index, cited_states=len(external), owners=dependencies,
                              per_owner_states=[len(group) for group in groups]))
    # Preserve the original guarantee and full-state membership, byte for byte.
    original = independent.collector_source(root, parts, owners, 114)
    text += '\nposition :' + original.split('\nposition :', 1)[1]
    return text, summaries


def generated(plan):
    pilot.validate_plan(plan)
    root = plan['roots'][4]
    entries = closure(plan['entries'], [root])
    parts, owners = assembly.partition(entries, 32000, 150)
    source, summaries = root_source(root, parts, owners)
    negative = header('WrongOwner') + f'''open import Prelude
open import Game.Shared using (build)
open import {PREFIX}.Coverage using (coveredBy)
open import {PREFIX}.Fixtures using (keyedBool; source)

incorrect : coveredBy keyedBool (source ∷ []) (build [] 1) (build [] true) ≡ true
incorrect = refl {{x = true}}
'''
    sources = {f'{DIRECTORY}/Coverage.agda': helper_source(),
               f'{DIRECTORY}/Fixtures.agda': fixture_source(),
               f'{DIRECTORY}/WrongOwner.agda': negative,
               f'{DIRECTORY}/Imports.agda': import_source(),
               f'{DIRECTORY}/Root.agda': source}
    return sources, summaries, root, parts, owners


def run(args):
    previous = args.previous.resolve()
    verified = audit(previous)
    old = json.loads((previous/'final.json').read_text())
    if (verified['accepted'] or verified['conditional_parts'] != [114, 115, 116, 117]
            or verified['negatives_rejected'] != 2 or old['phases'][-1]['stop_reason'] != 'cpu-limit'):
        raise ValueError('requires the audited conditional-part donor')
    if assembly6.sha(args.plan) != EXPECTED_PLAN:
        raise ValueError('fixed sampled graph differs')
    sources, summaries, state, parts, owners = generated(json.loads(args.plan.read_text()))
    donor = Path(old['check_root'])
    origin, original_pool = source_identity(donor), assembly6.interfaces(donor)
    machine = assembly6.machine_identity(args.agda)
    if machine != old['machine'] or len(original_pool) != 151:
        raise ValueError('different machine, binary or donor')
    for index in range(114, 118):
        expected = independent.part_source(index, parts[index], owners)
        if (donor/f'{independent.DIRECTORY}/Part{index}.agda').read_text() != expected:
            raise ValueError('accepted conditional certificate source differs')
    pool = {name: digest for name, digest in original_pool.items()
            if not name.endswith('/Game/SharedExport.agdai')}
    if len(pool) != 150:
        raise ValueError('unexpected unused generic interface')
    helper = None
    helper_donor = None
    if args.helper_donor:
        helper_donor = args.helper_donor.resolve()
        if assembly6.sha(helper_donor/'final.json') != args.expected_helper_report_sha256:
            raise ValueError('helper donor report differs')
        first = json.loads((helper_donor/'final.json').read_text())
        helper_root = Path(first['check_root'])
        helper_pool = assembly6.interfaces(helper_root)
        helper_name = '_build/2.9.0/agda/src/Tests/DirectCitations6/Coverage.agdai'
        if (first['status'] != 'phase-failed' or first['accepted'] or
                [phase['label'] for phase in first['phases']] != ['Coverage', 'Fixtures'] or
                not first['phases'][0]['expected_outcome_met'] or
                first['phases'][1]['expected_outcome_met'] or
                first['phases'][1]['record']['stop_reason'] or
                'UnsolvedMetaVariables' not in '\n'.join(first['phases'][1]['declaration_tail']) or
                first['machine'] != machine or first['borrowed_interfaces'] != pool or
                helper_pool != first['final_interfaces'] or len(helper_pool) != 151 or
                source_identity(helper_root)['source_sha256'] != first['source_sha256'] or
                assembly6.sha(helper_root/f'{DIRECTORY}/Coverage.agda') !=
                pilot.source_hashes(sources)[f'{DIRECTORY}/Coverage.agda'] or
                first['phases'][0]['own_interfaces'] != {helper_name: helper_pool[helper_name]} or
                pilot.cache_changes(pool, helper_pool)):
            raise ValueError('cannot reuse this helper acceptance')
        helper = dict(previous=str(helper_donor), report_sha256=args.expected_helper_report_sha256,
                      source_sha256=first['source_sha256'], original_interfaces=helper_pool,
                      name=helper_name, sha256=helper_pool[helper_name],
                      original_phase=first['phases'][0])
    output, runs = args.output.resolve(), args.runs_root.resolve()
    required = sum((donor/name).stat().st_size for name in pool)+sum(len(t.encode()) for t in sources.values())+20*1024**2
    if output.exists() or runs not in output.parents or not pilot.disk_allowed(pilot.disk_usage(runs), required):
        raise ValueError('fresh root, unchanged disk guards and cache headroom required')
    output.mkdir(parents=True)
    root = output/'check'
    root.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor/name, root/name)
    for name, text in sources.items():
        path = root/name
        if path.exists():
            raise ValueError('new target already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    manifest = bench6.refresh_manifest(root, origin={key: origin[key] for key in ('revision', 'dirty')})
    for name, digest in pool.items():
        copy_interface(donor/name, root/name, digest)
    if helper:
        copy_interface(helper_root/helper['name'], root/helper['name'], helper['sha256'])
    report = dict(format='othello-direct-citations6-v1', status='running', accepted=False,
        created_utc=utc(), root=state, check_root=str(root), previous=str(previous),
        previous_report_sha256=assembly6.sha(previous/'final.json'), previous_audit=verified,
        source_sha256=manifest['source_sha256'], agda_source_sha256=source_identity(root)['agda_source_sha256'],
        machine=machine, donor_source_sha256=origin['source_sha256'],
        donor_interfaces_sha256=digest_entries(original_pool), borrowed_interfaces=pool,
        generated_sha256=digest_entries(pilot.source_hashes(sources)), source_hashes=pilot.source_hashes(sources),
        certificate_parts_rechecked=0, prefix_parts_reused=114, conditional_parts_reused=[114, 115, 116, 117],
        citation_tables=summaries, reused_helper=helper, postulates=0, heldout_unmeasured=True,
        initial_problem2_proved=False, production_authorized=False, phases=[])
    atomic_json(output/'preflight.json', report)
    spent = 0.0
    def check(name, cap, *, negative=False):
        nonlocal spent
        target = f'{DIRECTORY}/{name}.agda'
        before = assembly6.interfaces(root)
        suffix = pilot.assert_cold(target, before, DIRECTORY)
        if not pilot.disk_allowed(pilot.disk_usage(runs), 16*1024**2):
            report['status'] = 'disk-stop'
            return False
        record = run_job(name, [machine['agda_path'], *assembly6.FLAGS, '--save-metas',
            '-v', 'tc.decl:10', '-i', 'src', target, '+RTS', '-M2500M', '-c', '-s', '-RTS'],
            output/'records', root=root, expected_source_sha256=manifest['source_sha256'],
            cpu_limit=cap, timeout=cap*2+30, rss_limit_gib=3, log_limit_mib=8,
            metadata=dict(machine=machine, own_target_cold=True, certificates_rechecked=0,
                          borrowed_interfaces_sha256=digest_entries(before), assembly_profile=True))
        spent += record['cpu_seconds']
        after = assembly6.interfaces(root)
        changes = pilot.cache_changes(before, after)
        own = {name: value for name, value in after.items() if name.endswith(suffix)}
        unexpected = [name for name in after if name not in before and name not in own]
        log = output/'records'/(name+'.log')
        text = log.read_text()
        wrong_rejected = bool(negative and record['exit_code'] and record['exit_code'] > 0 and
            not record['stop_reason'] and not own and not changes and not unexpected and
            re.findall(r'error: \[([^]]+)\]', text) == ['UnequalTerms'] and
            re.search(r'\b(true\s+and\s+false|false\s+and\s+true)\s+are not equal at type Bool', text))
        outcome = wrong_rejected if negative else record['accepted'] and len(own) == 1
        outcome = bool(outcome and not changes and not unexpected and record['source_unchanged'] and
            record['expected_source_matches'] and record['executable_sha256'] == machine['agda_sha256'])
        packed = archive(log, assembly6.sha(log)) if not negative and outcome else None
        phase = dict(label=name, record=record, record_sha256=assembly6.sha(output/'records'/(name+'.json')),
            expected_outcome_met=outcome, negative_fixture=negative, cache_changes=changes,
            unexpected_interfaces=unexpected, own_interfaces=own, raw_log_sha256=hashlib.sha256(text.encode()).hexdigest(),
            archived_log=packed, rts=rts_stats(text), declaration_tail=text.splitlines()[-45:])
        report['phases'].append(phase)
        report['nested_cpu_seconds'] = spent
        atomic_json(output/'running.json', report)
        if not outcome:
            report['status'] = 'cache-mismatch' if changes or unexpected else 'phase-failed'
        return outcome
    sequence = [('Coverage', 30, False), ('Fixtures', 20, False), ('WrongOwner', 15, True),
                ('Imports', 30, False), ('Root', 180, False)]
    if helper:
        sequence = sequence[1:]
    for name, cap, negative in sequence:
        if not check(name, cap, negative=negative):
            break
    report['donor_unchanged'] = source_identity(donor) == origin and assembly6.interfaces(donor) == original_pool
    report['helper_donor_unchanged'] = bool(not helper or
        (assembly6.sha(helper_donor/'final.json') == args.expected_helper_report_sha256 and
         source_identity(helper_root)['source_sha256'] == helper['source_sha256'] and
         assembly6.interfaces(helper_root) == helper['original_interfaces']))
    report['generated_source_unchanged'] = all(assembly6.sha(root/name) == value for name, value in report['source_hashes'].items())
    report['final_interfaces'] = assembly6.interfaces(root)
    report['interfaces_sha256'] = digest_entries(report['final_interfaces'])
    report['nested_cpu_seconds'] = spent
    report['latest_disk'] = pilot.disk_usage(runs)
    report['accepted'] = bool(len(report['phases']) == len(sequence) and
        all(phase['expected_outcome_met'] for phase in report['phases']) and report['donor_unchanged'] and
        report['helper_donor_unchanged'] and report['generated_source_unchanged'] and
        pilot.disk_allowed(report['latest_disk'], 8*1024**2))
    report['checked_lower_roots'] = int(report['accepted'])
    if report['accepted']:
        report['status'] = 'complete'
    atomic_json(output/'final.json', report)
    print(json.dumps({key: report[key] for key in ('status', 'accepted', 'checked_lower_roots', 'nested_cpu_seconds')}))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'plan', 'output', 'runs-root'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--agda', required=True)
    p.add_argument('--helper-donor', type=Path)
    p.add_argument('--expected-helper-report-sha256')
    raise SystemExit(0 if run(p.parse_args())['accepted'] else 2)
