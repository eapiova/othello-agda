#!/usr/bin/env python3
"""Check a complete citation trie in bounded prefix subtrees, then assemble it.

Each leaf obligation retains the actual target subtree and checks every full
state against a real accepted owner. Generic structural joining requires both
children and the value at every internal node. Generated hints are untrusted.
All accepted certificates and proof donors remain immutable.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import compact_shared6 as compact
import global_assembly6 as assembly
import independent_lower6 as independent
import lower_pilot6 as pilot
from memory_probe6 import rts_stats
import owner_split6 as split
import owner_trees6 as trees
from owner_audit6 import audit
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, positive, run_job, utc

PREFIX = 'Tests.OwnerCuts6'
DIRECTORY = 'src/Tests/OwnerCuts6'
MAX_STATES = 200


def header(name):
    return pilot.local_options(assembly.HEADER + f'module {PREFIX}.{name} where\n\n')


def helper_source():
    return header('Join') + '''open import Prelude
open import Game.Shared

subT : ∀ {A} → List Bool → Trie A → Trie A
subT [] t = t
subT (_ ∷ ps) tip = tip
subT (false ∷ ps) (node m l r) = subT ps l
subT (true ∷ ps) (node m l r) = subT ps r

valueT : ∀ {A} → Trie A → Maybe A
valueT tip = nothing
valueT (node m l r) = m

leftT : ∀ {A} → Trie A → Trie A
leftT tip = tip
leftT (node m l r) = l

rightT : ∀ {A} → Trie A → Trie A
rightT tip = tip
rightT (node m l r) = r

abstract
  joinAll : ∀ {A} (P : A → Set) (t : Trie A) →
    AllM P (valueT t) → AllT P (leftT t) → AllT P (rightT t) → AllT P t
  joinAll P tip pm pl pr = tt
  joinAll P (node m l r) pm pl pr = pm , (pl , pr)
'''


def key_bits(state):
    compact.pack_state(state)  # Validate the entire raw state.
    return ('0' if state[0] == 'b' else '1') + ''.join(
        {'0': '00', '1': '01', '2': '10'}[c] for c in state[1:])


def path_term(path):
    if not path or any(c not in '01' for c in path):
        if path == '':
            return '[]'
        raise ValueError('invalid binary prefix')
    return ' ∷ '.join('false' if c == '0' else 'true' for c in path) + ' ∷ []'


def routing(original):
    source_row = re.search(r'^  sources = (.+)$', original, re.M)
    if not source_row or original.count('\nmodule P26 where\n') != 1:
        raise ValueError('requires the original failed Part26 binding')
    owners = source_row[1].removesuffix(' ∷ []').split(' ∷ ')
    if not owners or any(not re.fullmatch(r'(E\d+(\.P\d+)?|S\d+\.P\d+)\.export', s) for s in owners):
        raise ValueError('invalid recorded citation owners')
    hint_row = re.search(r'^  hints = (.+)$', original, re.M)
    groups = re.findall(r'routesFor (\d+) "([^"]*)"', hint_row[1])
    if [int(n) for n, _ in groups] != list(range(len(owners))):
        raise ValueError('owner hints are not the recorded complete ordered groups')
    states = {}
    for owner, wire in groups:
        if len(wire) % 14:
            raise ValueError('invalid state-only hint wire')
        for i in range(0, len(wire), 14):
            if wire[i+13] != 'L':
                raise ValueError('hint must carry no certificate evidence')
            state = compact.unpack_state(wire[i:i+13])
            if state in states:
                raise ValueError('duplicate citation state')
            states[state] = owners[int(owner)]
    if not states:
        raise ValueError('empty stress obligation')
    return states


def cuts(states, limit=MAX_STATES):
    leaves, nodes = {}, set()

    def visit(path, current):
        if len(current) <= limit:
            leaves[path] = current
            return
        if len(path) >= 73:
            raise ValueError('duplicate full state key')
        nodes.add(path)
        for bit in '01':
            child = path + bit
            visit(child, {s: owner for s, owner in current.items() if key_bits(s).startswith(child)})

    visit('', states)
    flattened = [s for group in leaves.values() for s in group]
    if len(flattened) != len(states) or set(flattened) != set(states):
        raise ValueError('partition lost or duplicated a citation')
    return leaves, nodes


def fixtures():
    good = header('Fixtures') + f'''open import Prelude
open import Game.Shared
open import {PREFIX}.Join

t : Trie Bool
t = node nothing (build [] true) (build [] false)

accepted : AllT (λ b → b ≡ b) t
accepted = joinAll (λ b → b ≡ b) t tt
  (refl , (tt , tt)) (refl , (tt , tt))

left-shape : subT (false ∷ []) t ≡ build [] true
left-shape = refl

right-shape : subT (true ∷ []) t ≡ build [] false
right-shape = refl
'''
    bad = header('OmittedChild') + f'''open import Prelude
open import Game.Shared
open import {PREFIX}.Join

-- The right child contains false, so it cannot establish the true-only goal.
incorrect : AllT (λ b → b ≡ true)
  (node nothing (build [] true) (build [] false))
incorrect = joinAll (λ b → b ≡ true)
  (node nothing (build [] true) (build [] false)) tt
  (refl , (tt , tt)) (refl , (tt , tt))
'''
    return {f'{DIRECTORY}/Fixtures.agda': good, f'{DIRECTORY}/OmittedChild.agda': bad}


def generated(donor):
    original = (donor/f'{split.DIRECTORY}/Assemble6Split2.agda').read_text()
    states = routing(original)
    leaves, nodes = cuts(states)
    paths = sorted(leaves)
    numbers = {p: i for i, p in enumerate(paths)}
    imports = dict(re.findall(r'^import (\S+) as (\S+)$', original, re.M))
    modules = {alias: name for name, alias in imports.items()}
    sources = {f'{DIRECTORY}/Join.agda': helper_source(), **fixtures()}
    phases = [('Join', 30, False), ('Fixtures', 20, False), ('OmittedChild', 15, True)]
    summaries = []
    for path in sorted(paths, key=lambda p: (-len(leaves[p]), p)):
        index, group = numbers[path], leaves[path]
        if not group:
            continue  # Its actual subtree must reduce to tip during assembly.
        owners = sorted(set(group.values()))
        used = sorted({expr.split('.')[0] for expr in owners})
        text = header(f'Cut{index}') + assembly.COMMON
        text += f'open import {trees.PREFIX}.Lookup using (trees; coveredTrees; coveredTrees-sound)\n'
        text += f'open import {PREFIX}.Join using (subT)\n'
        text += ''.join(f'import {modules[alias]} as {alias}\n' for alias in used)
        text += 'import Tests.OwnerLower6.Root5.Part26 as I26\n\n'
        text += f'prefix : List Bool\nprefix = {path_term(path)}\n\n'
        text += f'''dropPrefix : List Bool → List Bool → List Bool
dropPrefix [] bs = bs
dropPrefix (_ ∷ ps) [] = []
dropPrefix (_ ∷ ps) (_ ∷ bs) = dropPrefix ps bs

routesFor : ℕ → String → Trie ℕ → Trie ℕ
routesFor owner wire tail = add (fromMaybe [] (decodeCompactEntries wire)) tail
  where
  add : List (SharedEntry (State six)) → Trie ℕ → Trie ℕ
  add [] tail = tail
  add (e ∷ es) tail = insertT (dropPrefix prefix (key6 (entryState e))) owner (add es tail)

sources : List (CheckedExport Fast.fastGame6 white (lowerGoal 4))
sources = {' ∷ '.join(owners)} ∷ []

tables : List (Trie (State six))
tables = {' ∷ '.join(e.replace('.export', '.states') for e in owners)} ∷ []

target : Trie (State six)
target = subT prefix I26.imports

hints : Trie ℕ
'''
        hints = 'tip'
        for j, expr in reversed(list(enumerate(owners))):
            wire = independent.state_wire(sorted(s for s, owner in group.items() if owner == expr))
            hints = f'routesFor {j} "{wire}" ({hints})'
        text += f'hints = {hints}\n\n'
        text += '''abstract
  association : tables ≡ trees sources
  association = refl {x = tables}

  accepted : coveredTrees keyed6 tables hints target ≡ true
  accepted = refl {x = true}

  sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) target
  sound = coveredTrees-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
    sources tables hints target association accepted
'''
        sources[f'{DIRECTORY}/Cut{index}.agda'] = text
        phases.append((f'Cut{index}', 80, False))
        summaries.append(dict(index=index, prefix=path, states=len(group), owners=len(owners)))
    text = header('Binding') + assembly.COMMON
    text += f'open import {PREFIX}.Join\nimport Tests.OwnerLower6.Root5.Part26 as I26\n'
    text += ''.join(f'import {PREFIX}.Cut{numbers[p]} as C{numbers[p]}\n' for p in paths if leaves[p])
    text += '\nGoal : State six → Set\nGoal = Proven Fast.fastGame6 white (lowerGoal 4)\n\n'
    expressions = {}
    for path in sorted(set(paths) | nodes, key=lambda p: (-len(p), p)):
        if path in leaves:
            expressions[path] = f'C{numbers[path]}.sound' if leaves[path] else 'tt'
            continue
        name = 'joined' + ('Root' if not path else path)
        target = f'(subT ({path_term(path)}) I26.imports)'
        text += f'''abstract
  {name} : AllT Goal {target}
  {name} = joinAll Goal {target} tt
    ({expressions[path+'0']}) ({expressions[path+'1']})

'''
        expressions[path] = name
    text += f'''module P26 where
  states : Trie (State six)
  states = I26.states

  abstract
    sound : AllT Goal states
    sound = I26.sound ({expressions['']})

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
    return sources, phases, dict(citation_states=len(states), maximum_states=MAX_STATES,
        leaves=summaries, empty_subtrees=sum(not v for v in leaves.values()), join_nodes=len(nodes))


def verified_donor(previous, expected, agda):
    if assembly6.sha(previous/'final.json') != expected:
        raise ValueError('states-only report differs')
    report = json.loads((previous/'final.json').read_text())
    if (report['format'] != 'othello-owner-trees6-v1' or report['status'] != 'phase-failed' or
            report['accepted'] or [p['label'] for p in report['phases']] != ['Fixtures', 'WrongAssociation', 'Binding'] or
            not all(p['expected_outcome_met'] for p in report['phases'][:2]) or
            report['phases'][-1]['expected_outcome_met'] or
            report['phases'][-1]['record']['exit_code'] != 251 or
            report['phases'][-1]['record']['stop_reason'] or
            not report['donor_unchanged'] or not report['helper_donor_unchanged'] or
            not report['generated_sources_unchanged'] or not report['reused_helper']):
        raise ValueError('requires the audited states-only heap failure and accepted safeguards')
    audit(Path(report['previous']), report['previous_report_sha256'])
    root = Path(report['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    machine = assembly6.machine_identity(agda)
    if (pool != report['final_interfaces'] or len(pool) != 327 or
            digest_entries(pool) != report['interfaces_sha256'] or machine != report['machine'] or
            identity['source_sha256'] != report['source_sha256'] or
            identity['agda_source_sha256'] != report['agda_source_sha256'] or
            any(assembly6.sha(root/n) != d for n, d in report['generated_source_hashes'].items())):
        raise ValueError('accepted donor, compiler or generated source changed')
    helper = report['reused_helper']
    helper_root = Path(helper['root'])
    if (source_identity(helper_root)['source_sha256'] != helper['source_sha256'] or
            assembly6.sha(helper_root/helper['name']) != helper['sha256'] or
            assembly6.sha(Path(helper['previous'])/'final.json') != helper['report_sha256']):
        raise ValueError('accepted generic transfer donor changed')
    before = {**report['borrowed_interfaces'], helper['name']: helper['sha256']}
    for phase in report['phases']:
        record = phase['record']
        receipt = previous/'records'/(phase['label']+'.json')
        if (assembly6.sha(receipt) != phase['record_sha256'] or json.loads(receipt.read_text()) != record or
                record['borrowed_interfaces_sha256'] != digest_entries(before) or
                phase['cache_changes'] or phase['unexpected_interfaces'] or
                not record['source_unchanged'] or not record['expected_source_matches'] or
                record['executable_sha256'] != machine['agda_sha256'] or
                not all(f in record['argv'] for f in assembly6.FLAGS+['--save-metas', '-M2500M']) or
                record['rss_stop_threshold_gib'] != 3):
            raise ValueError('donor receipt provenance differs')
        if phase['archived_log']:
            packed = phase['archived_log']
            path = previous/'records'/packed['archive_name']
            if assembly6.sha(path) != packed['archive_sha256']:
                raise ValueError('accepted log archive differs')
            raw = gzip.decompress(path.read_bytes())
        else:
            raw = (previous/'records'/(phase['label']+'.log')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != phase['raw_log_sha256'] or len(raw) != record['log_bytes']:
            raise ValueError('donor log differs')
        before.update(phase['own_interfaces'])
    if before != pool:
        raise ValueError('unrecorded donor interface')
    return report, root, identity, pool, machine


def rejected_omission(record, text, own):
    return bool(record['exit_code'] and record['exit_code'] > 0 and not record['stop_reason'] and
        not own and re.findall(r'error: \[([^]]+)\]', text) == ['UnequalTerms'] and
        re.search(r'incorrect\s*=\s*joinAll', text) and
        'AllM (λ b → b ≡ true) (just false)' in text)


def reused_prefix(args, original_pool, machine, sources):
    if not args.prefix_donor:
        return None
    previous = args.prefix_donor.resolve()
    if assembly6.sha(previous/'final.json') != args.expected_prefix_sha256:
        raise ValueError('generic prefix report differs')
    report = json.loads((previous/'final.json').read_text())
    root = Path(report['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    if (report['format'] != 'othello-owner-cuts6-v1' or report['status'] != 'phase-failed' or report['accepted'] or
            [p['label'] for p in report['phases']] != ['Join', 'Fixtures', 'OmittedChild'] or
            [p['expected_outcome_met'] for p in report['phases']] != [True, True, False] or
            report['borrowed_interfaces'] != original_pool or report['machine'] != machine or
            report['previous_report_sha256'] != args.expected_previous_sha256 or
            not report['donor_unchanged'] or not report['generated_sources_unchanged'] or
            identity['source_sha256'] != report['source_sha256'] or
            identity['agda_source_sha256'] != report['agda_source_sha256'] or
            pool != report['final_interfaces'] or digest_entries(pool) != report['interfaces_sha256'] or
            report['generated_source_hashes'] != pilot.source_hashes(sources) or
            any(assembly6.sha(root/n) != d for n, d in report['generated_source_hashes'].items())):
        raise ValueError('generic prefix or original obligations changed')
    before = dict(original_pool)
    for phase in report['phases']:
        record = phase['record']
        receipt = previous/'records'/(phase['label']+'.json')
        if (assembly6.sha(receipt) != phase['record_sha256'] or json.loads(receipt.read_text()) != record or
                record['borrowed_interfaces_sha256'] != digest_entries(before) or
                phase['cache_changes'] or phase['unexpected_interfaces'] or
                not record['source_unchanged'] or not record['expected_source_matches'] or
                record['executable_sha256'] != machine['agda_sha256'] or
                not all(f in record['argv'] for f in assembly6.FLAGS+['--save-metas', '-M2500M']) or
                record['rss_stop_threshold_gib'] != 3):
            raise ValueError('generic prefix receipt differs')
        if phase['archived_log']:
            packed = phase['archived_log']
            path = previous/'records'/packed['archive_name']
            if assembly6.sha(path) != packed['archive_sha256']:
                raise ValueError('generic prefix archive changed')
            raw = gzip.decompress(path.read_bytes())
        else:
            raw = (previous/'records'/(phase['label']+'.log')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != phase['raw_log_sha256'] or len(raw) != record['log_bytes']:
            raise ValueError('generic prefix log changed')
        if phase['negative_fixture']:
            if not rejected_omission(record, raw.decode(), phase['own_interfaces']):
                raise ValueError('omitted child was not rejected for the required false-state reason')
        elif not record['accepted'] or len(phase['own_interfaces']) != 1:
            raise ValueError('generic prefix was not accepted by Agda')
        before.update(phase['own_interfaces'])
    if before != pool or len(pool) != len(original_pool)+2:
        raise ValueError('unrecorded generic prefix interface')
    return dict(previous=str(previous), report_sha256=args.expected_prefix_sha256, root=str(root),
        identity=identity, interfaces=pool, interfaces_sha256=digest_entries(pool),
        original_phases=report['phases'], omitted_child_rejection_audited=True,
        original_harness_failure='pretty-printed incorrect declaration spans two lines')


def run(args, generator=generated, directory=DIRECTORY, report_format='othello-owner-cuts6-v1',
        negative_guard=rejected_omission, prefix_validator=reused_prefix, complete_lower_root=True,
        rts_extra=()):
    previous = args.previous.resolve()
    old, donor, identity, pool, machine = verified_donor(previous, args.expected_previous_sha256, args.agda)
    sources, phases, partition = generator(donor)
    reused = prefix_validator(args, pool, machine, sources)
    base, borrowed = (Path(reused['root']), reused['interfaces']) if reused else (donor, pool)
    if reused:
        phases = phases[reused.get('skip_phases', 3):]
    output, runs = args.output.resolve(), args.runs_root.resolve()
    required = sum((base/n).stat().st_size for n in borrowed) + sum(len(s.encode()) for s in sources.values()) + 48*1024**2
    if output.exists() or runs not in output.parents or not pilot.disk_allowed(pilot.disk_usage(runs), required):
        raise ValueError('fresh root and unchanged storage headroom required')
    output.mkdir(parents=True)
    root = output/'check'
    root.mkdir()
    for name, _ in source_files(base):
        assembly.hardlink(base/name, root/name)
    for name, text in sources.items():
        path = root/name
        if path.exists():
            if path.read_text() != text:
                raise ValueError('a preserved generated target differs')
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    manifest = bench6.refresh_manifest(root, origin={k: identity[k] for k in ('revision', 'dirty')})
    for name, digest in borrowed.items():
        copy_interface(base/name, root/name, digest)
    report = dict(format=report_format, status='checking', accepted=False, created_utc=utc(),
        previous=str(previous), previous_report_sha256=args.expected_previous_sha256, check_root=str(root),
        source_sha256=manifest['source_sha256'], agda_source_sha256=source_identity(root)['agda_source_sha256'],
        machine=machine, borrowed_interfaces=borrowed, borrowed_interfaces_sha256=digest_entries(borrowed),
        reused_generic_prefix=reused,
        generated_source_hashes=pilot.source_hashes(sources), partition=partition,
        phases=[], nested_cpu_seconds=0., nested_cpu_budget=args.kernel_cpu_budget,
        checked_sample_lower_roots=5, certificate_parts_rechecked=0, postulates=0,
        heldout_measured=False, initial_problem2_proved=False, production_authorized=False)
    atomic_json(output/'preflight.json', report)
    for name, limit, negative in phases:
        left = args.kernel_cpu_budget-report['nested_cpu_seconds']
        if left < 10 or not pilot.disk_allowed(pilot.disk_usage(runs), 16*1024**2):
            report['status'] = 'cpu-stop' if left < 10 else 'disk-stop'
            break
        before = assembly6.interfaces(root)
        target = f'{directory}/{name}.agda'
        suffix = pilot.assert_cold(target, before, directory)
        cap = min(limit, left-2)
        record = run_job(name, [machine['agda_path'], *assembly6.FLAGS, '--save-metas', '-v', 'tc.decl:10',
            '-i', 'src', target, '+RTS', '-M2500M', '-c', '-s', *rts_extra, '-RTS'], output/'records', root=root,
            expected_source_sha256=manifest['source_sha256'], cpu_limit=cap, timeout=cap*2+30,
            rss_limit_gib=3, log_limit_mib=8, metadata=dict(machine=machine, own_target_cold=True,
                certificate_parts_rechecked=0, prefix_cut_lookup=True, borrowed_interfaces_sha256=digest_entries(before)))
        after = assembly6.interfaces(root)
        changes = pilot.cache_changes(before, after)
        own = {n: d for n, d in after.items() if n.endswith(suffix)}
        unexpected = [n for n in after if n not in before and n not in own]
        log = output/'records'/(name+'.log')
        text = log.read_text()
        digest = assembly6.sha(log)
        rejected = bool(negative and negative_guard(record, text, own))
        outcome = rejected if negative else bool(record['accepted'] and len(own) == 1)
        outcome = bool(outcome and not changes and not unexpected and record['source_unchanged'] and
            record['expected_source_matches'] and record['executable_sha256'] == machine['agda_sha256'])
        packed = archive(log, digest) if outcome and not negative else None
        report['phases'].append(dict(label=name, target=target, expected_outcome_met=outcome,
            negative_fixture=negative, record=record, record_sha256=assembly6.sha(output/'records'/(name+'.json')),
            cache_changes=changes, unexpected_interfaces=unexpected, own_interfaces=own,
            raw_log_sha256=digest, archived_log=packed, rts=rts_stats(text), declaration_tail=text.splitlines()[-35:]))
        report['nested_cpu_seconds'] += record['cpu_seconds']
        atomic_json(output/'running.json', report)
        if not outcome:
            report['status'] = 'cache-mismatch' if changes or unexpected else 'phase-failed'
            break
    report['donor_unchanged'] = source_identity(donor) == identity and assembly6.interfaces(donor) == pool
    report['prefix_donor_unchanged'] = bool(not reused or (source_identity(base) == reused['identity'] and
        assembly6.interfaces(base) == borrowed and
        assembly6.sha(Path(reused['previous'])/'final.json') == reused['report_sha256']))
    report['generated_sources_unchanged'] = all(assembly6.sha(root/n) == d for n, d in report['generated_source_hashes'].items())
    report['final_interfaces'] = assembly6.interfaces(root)
    report['interfaces_sha256'] = digest_entries(report['final_interfaces'])
    report['latest_disk'] = pilot.disk_usage(runs)
    report['accepted'] = bool(len(report['phases']) == len(phases) and all(p['expected_outcome_met'] for p in report['phases']) and
        report['donor_unchanged'] and report['prefix_donor_unchanged'] and
        report['generated_sources_unchanged'] and pilot.disk_allowed(report['latest_disk']))
    if report['accepted']:
        report.update(status='complete', checked_sample_lower_roots=6 if complete_lower_root else 5)
    atomic_json(output/'final.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'accepted', 'checked_sample_lower_roots', 'nested_cpu_seconds')}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output', 'runs-root'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-previous-sha256', required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--kernel-cpu-budget', type=positive, required=True)
    parser.add_argument('--prefix-donor', type=Path)
    parser.add_argument('--expected-prefix-sha256')
    raise SystemExit(0 if run(parser.parse_args())['accepted'] else 2)
