#!/usr/bin/env python3
"""Measure independent local Boolean checks on already accepted wire data.

This experiment imports state data, never earlier part proofs. Its facts are
conditional local checker acceptances: no global linking, indexed-order proof,
initial-board guarantee or optimal-play theorem is claimed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
import census_pilot6 as pilot
import census_wire6 as wire
import compact_shared6 as compact
import global_assembly6 as assembly
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from unattended_wire6 import closed_record
import wire_pilot6
from wire_workflow6 import require

FORMAT = 'othello-data-only-pilot6-v1'
PREFIX = 'Tests.DataOnlyPilot6'
COMMON = '''open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (white)
open import Game.Shared
open import Othello.Board using (State; six)
open import Othello.Shared6 using (keyed6; key6)
open import Othello.CompactShared6 using (decodeCompactEntries)
open import Othello.SharedSymmetry6 using (lowerTransport6)
open import Othello.Statements using (lowerGoal)
import Othello.Fast6 as Fast
'''
LOCAL_HELPERS = '''
length : ∀ {A : Set} → List A → ℕ
length [] = 0
length (_ ∷ xs) = suc (length xs)

sameNat : ℕ → ℕ → Bool
sameNat zero zero = true
sameNat (suc n) (suc m) = sameNat n m
sameNat _ _ = false

checkDecoded : ℕ → Trie (State six) → Maybe (List (SharedEntry (State six))) → Bool
checkDecoded expected table nothing = false
checkDecoded expected table (just es) = sameNat expected (length es) ∧ finished
  where
  completed : Maybe (Trie (State six))
  completed = layersBy keyed6 Fast.fastGame6 white (lowerGoal 4) lowerTransport6 table es
  finished : Bool
  finished with completed
  ... | nothing = false
  ... | just t = true
'''


def scoped(module, helpers, public):
    return (pilot.HEADER+'module '+module+' where\n\nprivate\n'+
        ''.join('  '+line+'\n' if line else '\n' for line in helpers.splitlines())+
        '\n'+public)


def state_source(index, entries):
    # Dummy leaf tokens decode states only. No state validity fact is exported.
    text = ''.join(compact.pack_state(e['state'])+'L' for e in entries)
    return scoped(PREFIX+'.StateData'+str(index), COMMON,
        'states : Trie (State six)\nstates = shardStates keyed6\n'+
        '  (fromMaybe [] (decodeCompactEntries "'+text+'"))\n')


def part_source(index, entries, owners):
    deps = sorted({owners[r] for e in entries for r in e['references'] if owners[r] != index})
    require(all(d < index for d in deps), 'forward part dependency')
    imports = ''.join(f'import {PREFIX}.StateData{d} as D{d}\n' for d in deps)
    table = 'tip'
    for d in reversed(deps):
        cited = sorted({r for e in entries for r in e['references'] if owners[r] == d})
        keys = ''.join(compact.pack_state(r)+'L' for r in cited)
        selected = ('selectT (map (λ e → key6 (entryState e))\n'+
            '    (fromMaybe [] (decodeCompactEntries "'+keys+'"))) D'+str(d)+'.states')
        table = 'mergeT ('+selected+') ('+table+')'
    text = compact.encode((e['state'], e['certificate']) for e in entries)
    helpers = COMMON+imports+LOCAL_HELPERS+'\nimports : Trie (State six)\nimports = '+table+'\n'
    public = (f'abstract\n  accepted : checkDecoded {len(entries)} imports\n'+
        f'    (decodeCompactEntries "{text}") ≡ true\n'+
        '  accepted = refl {x = true}\n')
    return scoped(PREFIX+'.LocalPart'+str(index), helpers, public), deps, text


def negative_source(index, entries, owners):
    _, deps, text = part_source(index, entries, owners)
    require(deps, 'missing-import fixture needs a genuine external citation')
    public = (f'malformed : checkDecoded {len(entries)} tip (decodeCompactEntries "?") ≡ false\n'+
        'malformed = refl\n\n'+
        f'omitted : checkDecoded {len(entries)+1} tip (decodeCompactEntries "{text}") ≡ false\n'+
        'omitted = refl\n\n'+
        f'missingImport : checkDecoded {len(entries)} tip (decodeCompactEntries "{text}") ≡ false\n'+
        'missingImport = refl\n')
    return scoped(PREFIX+'.Rejected', COMMON+LOCAL_HELPERS, public)


def read_partition(data, max_tokens=32000, max_entries=200):
    entries = [dict(state=s,certificate=c,references=sorted(rs)) for s,c,rs in wire.records(data)]
    require(entries and len(entries) <= 100000, 'bounded accepted wire required')
    parts, owners = assembly.partition(entries,max_tokens,max_entries)
    return parts, owners


def borrowed_sources(interfaces):
    names=set()
    for name in interfaces:
        require(name.startswith('_build/') and '/agda/' in name and name.endswith('.agdai'),
            'unsupported generic interface location')
        names.add(name.split('/agda/',1)[1][:-1])
    return names


def run(args):
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh isolated output required')
    out.mkdir(parents=True)
    current = Path.cwd().resolve()
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == 'eapiova' and
        machine['agda_sha256'] == args.expected_agda_sha256, 'original desktop/compiler required')
    historical = args.wire_root.resolve()
    completed = args.completed_root.resolve()
    donor = args.donor.resolve()
    report = dict(format=FORMAT, created_utc=utc(), status='auditing-inputs', accepted=False,
        machine=machine, phases=[], local_boolean_only=True, child_proof_imports=False,
        indexed_order_guard_checked=False, global_linking_proved=False,
        initial_problem2_proved=False, optimal_pair_proved=False, production_authorized=False,
        laptop_required_during_execution=False, kernel_cpu_seconds=0.)
    def save(): atomic_json(out/'report.json',report)
    def guard():
        used = allocated(current.parent)
        free = shutil.disk_usage(current.parent).free
        require(used < 10*2**30 and free >= 100*2**30,
            'desktop storage gate reached; accepted local facts preserved')
        report['last_storage_gate'] = dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc())
        save()
    save(); guard()
    original_source = source_identity(historical)
    completed_source = source_identity(completed)
    donor_source = source_identity(donor)
    require(original_source['source_sha256'] == args.expected_wire_source_sha256 and
        completed_source['source_sha256'] == args.expected_completed_source_sha256 and
        donor_source['source_sha256'] == args.expected_donor_source_sha256, 'historical source differs')
    receipt = completed/'results/wire-cut-ply10-resume-20261009.json'
    closed_record(json.loads(receipt.read_text()), args.expected_completed_source_sha256)
    final_path = completed/'results/wire-resume6/report.json'
    require(assembly6.sha(final_path) == args.expected_completed_report_sha256, 'completed pilot digest differs')
    final = json.loads(final_path.read_text())
    require(final.get('accepted') is True and final.get('status') == 'complete' and
        final.get('completed_targets') == final.get('expected_targets') == 268 and
        final.get('historical_artifacts_unchanged') is True and
        all(p['record'].get('accepted') is True for p in final['reused_phases']+final['new_phases']),
        'complete accepted original-rule pilot required')
    native_path = historical/'results/wire-advance6/lower-ply10-native.json'
    native = json.loads(native_path.read_text())
    data = native_path.with_name('lower-ply10.wire')
    require(native.get('native_complete') is True and native.get('wire_complete') is True and
        native['request']['direction'] == 'lower' and
        assembly6.sha(data) == native.get('wire_output_sha256'), 'matching complete wire required')
    plan_path = historical/'results/wire-advance6/lower-ply10-prepared/plan.json'
    require(assembly6.sha(plan_path) == args.expected_plan_sha256, 'original plan differs')
    plan = json.loads(plan_path.read_text())
    parts, owners = read_partition(data)
    require(len(parts) == 267 and sum(map(len,parts)) == native['counts']['wire_records'] == 53217,
        'original partition differs')
    baselines = {p['target']['part']:p['record'] for p in final['reused_phases']+final['new_phases']
        if p['target']['kind'] == 'part'}
    selection = sorted(set((0,53,106,159,212,266,max(plan['targets'][:-1],key=lambda t:t['imported_citations'])['part'])))
    report.update(selected_parts=selection, complete_descendant_wire=True,
        wire_sha256=assembly6.sha(data),original_plan_sha256=assembly6.sha(plan_path),
        completed_report_sha256=assembly6.sha(final_path), rows=53217, state_data_parts=267,
        input_source_sha256=dict(wire=original_source['source_sha256'],completed=completed_source['source_sha256'],
            donor=donor_source['source_sha256']))
    generated = {}
    local_targets = {}
    def add(name,text):
        require('Proven' not in text and 'CheckedExport' not in text and 'postulate' not in text,
            'diagnostic accidentally exports a semantic proof')
        path='src/'+PREFIX.replace('.','/')+'/'+name+'.agda'
        generated[path]=text
    for i,es in enumerate(parts):add('StateData'+str(i),state_source(i,es))
    targets=[]
    for i in range(len(parts)):
        text,deps,_=part_source(i,parts[i],owners)
        add('LocalPart'+str(i),text)
        target=dict(path='src/'+PREFIX.replace('.','/')+'/LocalPart'+str(i)+'.agda',
            kind='local-boolean',part=i,dependencies=deps,entries=len(parts[i]),
            old_cpu_seconds=baselines[i]['cpu_seconds'],old_peak_rss_gib=baselines[i]['peak_rss_gib'])
        local_targets[i]=target
        if i in selection:targets.append(target)
    negative_index=next(i for i in selection if targets[selection.index(i)]['dependencies'])
    add('Rejected',negative_source(negative_index,parts[negative_index],owners))
    targets.insert(0,dict(path='src/'+PREFIX.replace('.','/')+'/Rejected.agda',kind='negative-fixtures'))
    loads=''.join(f'import {PREFIX}.StateData{i} as D{i}\n' for i in range(len(parts)))
    add('LoadAll',scoped(PREFIX+'.LoadAll',COMMON+loads,
        'loadedParts : ℕ\nloadedParts = 267\n'))
    targets.append(dict(path='src/'+PREFIX.replace('.','/')+'/LoadAll.agda',kind='all-data-import-only'))
    donor_before=assembly6.interfaces(donor)
    generic={n:d for n,d in donor_before.items() if '/src/Tests/' not in n}
    require(len(generic)==31 and digest_entries(generic)==args.expected_generic_interfaces_sha256,
        'generic same-machine cache differs')
    sources={name:raw for name,raw in source_files(current) if name.endswith(('.agda','.agda-lib'))}
    borrowed=borrowed_sources(generic)
    for name in borrowed:
        require(name in sources and (donor/name).is_file() and (donor/name).read_bytes()==sources[name],
            'source differs from borrowed generic interface: '+name)
    record_generated={n:hashlib.sha256(s.encode()).hexdigest() for n,s in generated.items()}
    report.update(generated_sha256=record_generated,total_generated_source_bytes=sum(len(s.encode()) for s in generated.values()),
        prospective_targets=targets,generic_interfaces_sha256=digest_entries(generic),status='checking-local-facts')
    base=out/'source';base.mkdir()
    for name,raw in sources.items():
        path=base/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        if name in borrowed:shutil.copystat(donor/name,path)
    for name,text in generated.items():
        path=base/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    all_names=list(sources)+list(generated)
    def fresh_work(path):
        path.mkdir()
        for name in all_names:
            destination=path/name;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(base/name,destination)
        for name,digest in generic.items():copy_interface(donor/name,path/name,digest)
        return path
    complete_pass=getattr(args,'complete_local_pass',False)
    report.update(complete_local_pass_requested=complete_pass,complete_all_local_rows=False)
    save()
    for k,target in enumerate(targets):
        guard()
        require(report['kernel_cpu_seconds']+args.part_cpu_limit+30 <= args.kernel_cpu_budget,
            'internal kernel allowance reached')
        work=fresh_work(out/('check'+str(k)))
        source_hash=source_identity(work)['source_sha256']
        before=assembly6.interfaces(work)
        command=[machine['agda_path'],*assembly6.FLAGS,'--save-metas','-i','src',target['path'],
            '+RTS','-M1350M','-c','-s','-RTS']
        record=run_job('target'+str(k),command,out/'records',root=work,
            expected_source_sha256=source_hash,timeout=2*args.part_cpu_limit+30,
            cpu_limit=args.part_cpu_limit,rss_limit_gib=1.5,log_limit_mib=2,
            metadata=dict(machine=machine,own_target_cold=True,local_boolean_only=True,
                child_proof_imports=False,indexed_order_guard_checked=False,global_linking_proved=False))
        after=assembly6.interfaces(work)
        borrowed_ok=all(after.get(n)==digest for n,digest in before.items())
        phase=dict(target=target,record=record,borrowed_interfaces_unchanged=borrowed_ok,
            accepted=record.get('accepted') is True and borrowed_ok)
        report['phases'].append(phase)
        report['kernel_cpu_seconds']+=record['cpu_seconds'];save()
        if not phase['accepted']:
            report['status']='local-fact-failed';save();return False
    if complete_pass:
        report.update(status='checking-remaining-local-rows',warm_phases=[])
        warm=fresh_work(out/'serial-local-check')
        warm_hash=source_identity(warm)['source_sha256']
        for i,target in local_targets.items():
            if i in selection:continue  # Preserve the exact accepted cold facts.
            guard()
            require(report['kernel_cpu_seconds']+args.part_cpu_limit+30 <= args.kernel_cpu_budget,
                'internal kernel allowance reached; accepted local row prefix preserved')
            before=assembly6.interfaces(warm)
            require(not any(n.endswith('/LocalPart'+str(i)+'.agdai') for n in before),
                'new local target unexpectedly warm')
            command=[machine['agda_path'],*assembly6.FLAGS,'--save-metas','-i','src',target['path'],
                '+RTS','-M1350M','-c','-s','-RTS']
            record=run_job('local'+str(i),command,out/'records',root=warm,
                expected_source_sha256=warm_hash,timeout=2*args.part_cpu_limit+30,
                cpu_limit=args.part_cpu_limit,rss_limit_gib=1.5,log_limit_mib=2,
                metadata=dict(machine=machine,own_target_cold=True,local_boolean_only=True,
                    state_data_cache_context='serial warm; earlier local proof parts are never imported',
                    child_proof_imports=False,indexed_order_guard_checked=False,global_linking_proved=False))
            after=assembly6.interfaces(warm)
            borrowed_ok=all(after.get(n)==d for n,d in before.items())
            phase=dict(target=target,record=record,borrowed_interfaces_unchanged=borrowed_ok,
                accepted=record.get('accepted') is True and borrowed_ok)
            report['warm_phases'].append(phase);report['kernel_cpu_seconds']+=record['cpu_seconds']
            report['accepted_local_parts']=len(selection)+sum(p['accepted'] for p in report['warm_phases'])
            save()
            if not phase['accepted']:
                report['status']='local-row-failed';save();return False
        report['complete_all_local_rows']=True
    require(source_identity(historical)==original_source and source_identity(completed)==completed_source and
        source_identity(donor)==donor_source and assembly6.interfaces(donor)==donor_before,
        'historical source or interfaces changed')
    pairs=[p for p in report['phases'] if p['target']['kind']=='local-boolean']
    new=sum(p['record']['cpu_seconds'] for p in pairs)
    old=sum(p['target']['old_cpu_seconds'] for p in pairs)
    report.update(status='complete-local-boolean-pilot',accepted=True,finished_utc=utc(),
        historical_artifacts_unchanged=True,old_selected_part_cpu_seconds=old,
        new_selected_local_cpu_seconds=new,observed_old_to_new_cpu_ratio=old/new,
        comparison_limitations=['New targets have state interfaces cold; old targets reused already accepted earlier proof interfaces.',
            'No indexed reference-order guard, compatibility, global soundness or explicit joint spine is measured.',
            'The import-only target does not assemble or normalize a complete resolver or validity proof.'])
    if complete_pass:
        all_pairs=pairs+report['warm_phases']
        report.update(all_local_rows_old_part_cpu_seconds=sum(p['target']['old_cpu_seconds'] for p in all_pairs),
            all_local_rows_new_part_cpu_seconds=sum(p['record']['cpu_seconds'] for p in all_pairs),
            all_local_rows_comparison_context='selected targets cold data; remainder serial warm data; every target cold',
            accepted_local_parts=len(all_pairs))
    save();return True


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('wire-root','completed-root','donor','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-wire-source-sha256','expected-completed-source-sha256',
        'expected-donor-source-sha256','expected-completed-report-sha256','expected-plan-sha256',
        'expected-generic-interfaces-sha256'):p.add_argument('--'+name,required=True)
    p.add_argument('--kernel-cpu-budget',type=float,default=1800)
    p.add_argument('--part-cpu-limit',type=float,default=180)
    p.add_argument('--complete-local-pass',action='store_true')
    args=p.parse_args()
    return 0 if run(args) else 1


if __name__=='__main__':raise SystemExit(main())
