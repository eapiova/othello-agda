#!/usr/bin/env python3
"""Separate closed Boolean checking from proof-citation assembly.

Each new part proves a conditional sound theorem over a literal import trie.
The root collector must supply that trie's real, already-checked proofs. No
unchecked citation becomes a guarantee; no original certificate is altered.
Only four suffix parts of the bounded stress pilot are intended here.
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
import compact_shared6 as compact
import global_assembly6 as assembly
from lower_local_audit6 import audit as audit_local
from lower_local_plan6 import closure
import lower_pilot6 as pilot
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, build_lock, positive, run_job, utc

PREFIX = 'Tests.IndependentLower6'
DIRECTORY = 'src/Tests/IndependentLower6'
OLD = 'Tests.LowerLocal6.Root4.Group0'


def checker_source():
    return pilot.local_options(assembly.HEADER+f'module {PREFIX}.Checker where\n\n'+'''
open import Prelude
open import Game.Core using (Game; Player)
open import Game.Shared
open import Game.Symmetry using (CertificateTransport)

private
  falseElim : ∀ {A : Set} → false ≡ true → A
  falseElim ()

checkFrom : ∀ {S} → Keyed S → (g : Game S) → (p : Player) →
  (goal : S → Bool) → CertificateTransport g p goal →
  Trie S → List (SharedEntry S) → Bool
checkFrom k g p goal laws t es with layersBy k g p goal laws t es
... | nothing = false
... | just t′ = true

checkFrom-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal
  (laws : CertificateTransport g p goal) t es →
  AllT (Proven g p goal) t → checkFrom k g p goal laws t es ≡ true →
  AllT (Proven g p goal) (shardStates k es)
checkFrom-sound k g p goal laws t es inv e
  with layersBy k g p goal laws t es in el
... | nothing = falseElim e
... | just t′ = layersBy-local-sound k g p goal laws t es inv el
''')


def state_wire(states):
    return ''.join(compact.pack_state(state)+'L' for state in states)


def part_source(index, part, owners):
    external = sorted({state for entry in part for state in entry['references']
                       if owners[state] != index})
    if any(owners[state] >= index for state in external):
        raise ValueError('forward external citation')
    wire = compact.encode((entry['state'], entry['certificate']) for entry in part)
    own = [entry['state'] for entry in part]
    text = assembly.HEADER+f'module {PREFIX}.Part{index} where\n\n'+assembly.COMMON
    text += f'open import {PREFIX}.Checker using (checkFrom; checkFrom-sound)\n'
    text += f'''
imports : Trie (State six)
imports = shardStates keyed6 (fromMaybe [] (decodeCompactEntries "{state_wire(external)}"))

states : Trie (State six)
states = shardStates keyed6 (fromMaybe [] (decodeCompactEntries "{state_wire(own)}"))

abstract
  entries : List (SharedEntry (State six))
  entries = fromMaybe [] (decodeCompactEntries "{wire}")

  shape : shardStates keyed6 entries ≡ states
  shape = refl {{x = states}}

  accepted : checkFrom keyed6 Fast.fastGame6 white (lowerGoal 4)
    lowerTransport6 imports entries ≡ true
  accepted = refl {{x = true}}

  sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) imports →
    AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
  sound inv = subst (AllT (Proven Fast.fastGame6 white (lowerGoal 4))) shape
    (checkFrom-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
      lowerTransport6 imports entries inv accepted)
'''
    return pilot.local_options(text)


def collector_source(root, parts, owners, start):
    text = assembly.HEADER+f'module {PREFIX}.Root where\n\n'+assembly.COMMON
    text += ''.join(f'import {OLD}.Part{index} as P{index}\n' for index in range(start))
    text += ''.join(f'import {PREFIX}.Part{index} as I{index}\n' for index in range(start, len(parts)))
    helper_emitted = False
    for index in range(start, len(parts)):
        original, deps, _ = assembly.part_source(index, parts[index], owners, 'lower')
        packed = pilot.packed_part(original)
        # These are the same selected, already-proved imports as the old part.
        if deps:
            helper = packed.split('importKeys :', 1)[1].split('imports :', 1)[0]
            if not helper_emitted:
                text += '\nimportKeys :'+helper
                helper_emitted = True
        imports = packed.split('\nimports = ', 1)[1].split('\n', 1)[0]
        text += f'''
module P{index} where
  imports : List (CheckedExport Fast.fastGame6 white (lowerGoal 4))
  imports = {imports}

  states : Trie (State six)
  states = I{index}.states

  abstract
    importShape : importStates imports ≡ I{index}.imports
    importShape = refl {{x = I{index}.imports}}

    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = I{index}.sound
      (subst (AllT (Proven Fast.fastGame6 white (lowerGoal 4)))
        importShape (importStates-sound imports))

  export : CheckedExport Fast.fastGame6 white (lowerGoal 4)
  export = checkedExport states sound
'''
    owner = owners[root]
    text += f'''
position : State six
position = decode "{compact.pack_state(root)}"

abstract
  member : knownIn keyed6 P{owner}.states position ≡ true
  member = refl {{x = true}}

  proven : Proven Fast.fastGame6 white (lowerGoal 4) position
  proven = knownIn-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
    P{owner}.states position P{owner}.sound member

  fastGuarantee : Guarantees Fast.fastGame6 white (lowerGoal 4) position
  fastGuarantee = checkSound Fast.fastGame6 white (lowerGoal 4) position
    (proj₁ proven) (proj₂ proven)

  guarantee : Guarantees (Rules.game six) white (lowerGoal 4) position
  guarantee = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement fastGuarantee
'''
    return pilot.local_options(text)


def negative_sources():
    # False terminal and a citation into an empty trie must both reject.
    rows = [('FalseTerminal', 'w'+'1'*36, 'L'), ('MissingCitation', 'w'+'2'*36, 'K')]
    result = {}
    for name, state, cert in rows:
        text = assembly.HEADER+f'module {PREFIX}.{name} where\n\n'+assembly.COMMON
        text += f'open import {PREFIX}.Checker using (checkFrom)\n'
        text += f'''
abstract
  rejected : checkFrom keyed6 Fast.fastGame6 white (lowerGoal 4)
    lowerTransport6 tip (fromMaybe [] (decodeCompactEntries "{state_wire([state])[:-1]+compact.pack_certificate(cert)}")) ≡ true
  rejected = refl {{x = true}}
'''
        result[f'{DIRECTORY}/{name}.agda'] = pilot.local_options(text)
    return result


def negative_ok(record, text, own, changes):
    return bool(not record['accepted'] and record['exit_code'] is not None and record['exit_code'] > 0 and
        not record['stop_reason'] and not own and not changes and
        re.findall(r'error: \[([^]]+)\]', text) == ['UnequalTerms'] and
        re.search(r'\b(true\s+and\s+false|false\s+and\s+true)\s+are not equal at type Bool', text) and
        re.search(r'checkFrom\s+keyed6\s+Fast\.fastGame6\s+white\s+\(lowerGoal\s+4\)', text))


def prepare(args):
    previous = args.previous.resolve()
    verified = audit_local(previous)
    old = json.loads((previous/'final.json').read_text())
    if (verified['pilot_status'] != 'part-failed' or verified['accepted_parts'] != 114 or
            verified['attempted_parts'] != 115 or old['phases'][-1]['exit_code'] != 251 or
            old['phases'][-1]['stop_reason'] is not None or old['layout']['root_index'] != 4):
        raise ValueError('requires the unchanged Part114 heap failure; one recovery only')
    if assembly6.sha(args.plan) != old['plan_sha256']:
        raise ValueError('different factored sample')
    plan = json.loads(args.plan.read_text())
    pilot.validate_plan(plan)
    root = plan['roots'][4]
    entries = closure(plan['entries'], [root])
    parts, owners = assembly.partition(entries, 32000, 150)
    if len(parts) != 118 or root != old['roots'][0]:
        raise ValueError('different stress layout')
    sources = {f'{DIRECTORY}/Checker.agda': checker_source()}
    sources.update(negative_sources())
    for index in range(114, len(parts)):
        sources[f'{DIRECTORY}/Part{index}.agda'] = part_source(index, parts[index], owners)
    sources[f'{DIRECTORY}/Root.agda'] = collector_source(root, parts, owners, 114)
    return old, verified, sources


def preflight(args):
    old, verified, sources = prepare(args)
    result = dict(format='othello-independent-lower6-preflight-v1', status='complete', created_utc=utc(),
        previous=str(args.previous.resolve()), previous_audit=verified,
        previous_report_sha256=assembly6.sha(args.previous/'final.json'),
        previous_source_sha256=old['source_sha256'], plan_sha256=assembly6.sha(args.plan),
        machine=old['machine'], source_hashes=pilot.source_hashes(sources),
        generated_sha256=digest_entries(pilot.source_hashes(sources)), modules=len(sources),
        unchanged_certificate_parts=[114, 115, 116, 117],
        prefix_parts_reused=114, generated_source_bytes=sum(len(text.encode()) for text in sources.values()),
        certificate_heap_mib=1350, certificate_rss_gib=1.5,
        root_assembly_heap_mib=2500, root_assembly_rss_gib=3,
        conditional_imports_must_be_discharged=True, postulates=0,
        initial_problem2_proved=False, production_authorized=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, result)
    print(json.dumps({key: result[key] for key in ('status', 'modules', 'generated_source_bytes', 'generated_sha256')}))


def run(args):
    if args.output.exists():
        raise ValueError('fresh result root required; no retries')
    old, verified, sources = prepare(args)
    pre = json.loads(args.preflight.read_text())
    if (assembly6.sha(args.preflight) != args.expected_preflight_sha256 or
            pre['generated_sha256'] != digest_entries(pilot.source_hashes(sources)) or
            pre['previous_report_sha256'] != assembly6.sha(args.previous/'final.json') or
            pre['plan_sha256'] != assembly6.sha(args.plan)):
        raise ValueError('preflight differs')
    donor = Path(old['check_root'])
    identity, pool = source_identity(donor), assembly6.interfaces(donor)
    machine = assembly6.machine_identity(args.agda)
    if machine != old['machine']:
        raise ValueError('original desktop compiler/machine required')
    runs = args.runs_root.resolve()
    if runs not in args.output.resolve().parents:
        raise ValueError('output must stay inside the study runs')
    required = sum((donor/name).stat().st_size for name in pool)+sum(len(t.encode()) for t in sources.values())+16*1024**2
    if not pilot.disk_allowed(pilot.disk_usage(runs), required):
        raise ValueError('study artifact and free-space guards')
    output = args.output.resolve()
    output.mkdir(parents=True)
    root = output/'check'
    root.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor/name, root/name)
    for name, text in sources.items():
        path = root/name
        if path.exists():
            raise ValueError('new namespace already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    manifest = bench6.refresh_manifest(root, origin={key: identity[key] for key in ('revision', 'dirty')})
    for name, digest in pool.items():
        copy_interface(donor/name, root/name, digest)
    report = dict(format='othello-independent-lower6-v1', status='running', accepted=False,
        machine=machine, source_sha256=manifest['source_sha256'],
        agda_source_sha256=source_identity(root)['agda_source_sha256'], check_root=str(root),
        donor=str(donor), donor_source_sha256=identity['source_sha256'], donor_interfaces_sha256=digest_entries(pool),
        preflight_sha256=args.expected_preflight_sha256, source_hashes=pilot.source_hashes(sources),
        prefix_parts_reused=114, conditional_parts=[], checked_lower_roots=0, root=old['roots'][0],
        phases=[], measured_kernel_cpu_seconds=0, kernel_cpu_budget=args.kernel_cpu_budget,
        heldout_unmeasured=True, initial_problem2_proved=False, production_authorized=False,
        postulates=0, conditional_part_premises_explicit=True, old_accepted_targets_retried=False)
    records, record_hashes, logs, archives = {}, {}, {}, {}

    def fixed():
        return source_identity(donor) == identity and assembly6.interfaces(donor) == pool

    def save():
        atomic_json(output/'independent.json', report)
        after = assembly6.interfaces(root)
        atomic_json(output/'phase-records.json', dict(records=records, record_hashes=record_hashes,
            log_hashes=logs, log_archives=archives, final_interfaces=after,
            final_interfaces_sha256=digest_entries(after)))

    def check(label, target, *, negative=False, collector=False):
        left = args.kernel_cpu_budget-report['measured_kernel_cpu_seconds']
        if left < 15 or not pilot.disk_allowed(pilot.disk_usage(runs), 16*1024**2):
            report['status'] = 'resource-budget-stopped'
            return None
        before = assembly6.interfaces(root)
        suffix = pilot.assert_cold(target, before, DIRECTORY)
        if not fixed() or source_identity(root)['source_sha256'] != manifest['source_sha256'] or assembly6.machine_identity(args.agda) != machine:
            raise ValueError('source/cache/compiler changed')
        heap, rss, cap = (2500, 3, 180) if collector else (1350, 1.5, 90)
        record = run_job(label, [machine['agda_path'], *assembly6.FLAGS, '--save-metas', '-i', 'src', target,
            '+RTS', f'-M{heap}M', '-c', '-s', '-RTS'], output/'records', root=root,
            expected_source_sha256=manifest['source_sha256'], cpu_limit=min(cap, left), timeout=cap*3,
            rss_limit_gib=rss, log_limit_mib=2,
            metadata=dict(machine=machine, own_target_cold=True, borrowed_interfaces_sha256=digest_entries(before),
                old_accepted_targets_retried=False, conditional_part=not negative and not collector,
                root_assembly=collector))
        report['measured_kernel_cpu_seconds'] += record['cpu_seconds']
        after = assembly6.interfaces(root)
        changed = pilot.cache_changes(before, after)
        own = {name: digest for name, digest in after.items() if name.endswith(suffix)}
        unexpected = [name for name in after if name not in before and name not in own]
        log = output/'records'/(label+'.log')
        text = log.read_text()
        metric = dict(assembly.metrics(record), label=label, target=target, heap_mib=heap, rss_limit_gib=rss,
            exit_code=record['exit_code'], cache_changes=changed, unexpected_interfaces=unexpected,
            own_interfaces=own, rts=rts_stats(text), negative_fixture=negative, root_assembly=collector)
        trustworthy = (fixed() and not changed and not unexpected and record['source_unchanged'] and
            record['expected_source_matches'] and record['executable_sha256'] == machine['agda_sha256'])
        metric['accepted'] = bool(record['accepted'] and trustworthy and len(own) == 1)
        metric['expected_outcome_met'] = (negative_ok(record, text, own, changed) and trustworthy
                                          if negative else metric['accepted'])
        records[label] = record
        record_hashes[label] = assembly6.sha(output/'records'/(label+'.json'))
        logs[label] = assembly6.sha(log)
        if metric['accepted']:
            archives[label] = archive(log, logs[label])
        report['phases'].append(metric)
        save()
        print(json.dumps(metric), flush=True)
        return metric

    save()
    try:
        with build_lock(root):
            result = check('checker', f'{DIRECTORY}/Checker.agda')
            if result is None or not result['accepted']:
                report['status'] = 'checker-failed' if result else report['status']
            else:
                for name in ('FalseTerminal', 'MissingCitation'):
                    result = check(name, f'{DIRECTORY}/{name}.agda', negative=True)
                    if result is None or not result['expected_outcome_met']:
                        report['status'] = 'negative-fixture-failed' if result else report['status']
                        break
                else:
                    for index in (114, 115, 116, 117):
                        result = check(f'conditional-part{index}', f'{DIRECTORY}/Part{index}.agda')
                        if result is None or not result['accepted']:
                            report['status'] = 'conditional-part-failed' if result else report['status']
                            break
                        report['conditional_parts'].append(index)
                        save()
                    else:
                        result = check('root-assembly', f'{DIRECTORY}/Root.agda', collector=True)
                        report['accepted'] = bool(result and result['accepted'])
                        report['status'] = 'complete' if report['accepted'] else ('root-assembly-failed' if result else report['status'])
                        report['checked_lower_roots'] = int(report['accepted'])
    except Exception as error:
        report.update(status='harness-failed', accepted=False, error=dict(type=type(error).__name__, message=str(error)))
    report.update(donor_unchanged=fixed(), generated_source_unchanged=source_identity(root)['source_sha256'] == manifest['source_sha256'],
                  final_disk=pilot.disk_usage(runs), finished_utc=utc())
    if not report['donor_unchanged'] or not report['generated_source_unchanged'] or not pilot.disk_allowed(report['final_disk'], 8*1024**2):
        report.update(status='provenance-or-resource-changed', accepted=False, checked_lower_roots=0)
    save()
    atomic_json(output/'final.json', report)
    saved = json.loads((output/'phase-records.json').read_text())
    saved.update(final_sha256=assembly6.sha(output/'final.json'), independent_sha256=assembly6.sha(output/'independent.json'))
    atomic_json(output/'phase-records.json', saved)
    print(json.dumps({key: report[key] for key in ('status', 'accepted', 'conditional_parts', 'checked_lower_roots', 'measured_kernel_cpu_seconds')}))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('preflight', 'run'))
    for name in ('previous', 'plan', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--preflight', type=Path)
    p.add_argument('--expected-preflight-sha256')
    p.add_argument('--agda')
    p.add_argument('--runs-root', type=Path)
    p.add_argument('--kernel-cpu-budget', type=positive)
    args = p.parse_args()
    if args.mode == 'preflight':
        preflight(args)
    else:
        if not all(getattr(args, key) for key in ('preflight', 'expected_preflight_sha256', 'agda', 'runs_root', 'kernel_cpu_budget')):
            p.error('run requires the recorded preflight, original compiler, runs root and CPU budget')
        raise SystemExit(0 if run(args)['accepted'] else 2)


if __name__ == '__main__':
    main()
