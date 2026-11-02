#!/usr/bin/env python3
"""States-only citation lookup, with kernel-checked association to real exports.

Reuse the preserved 325-interface lower prefix. Only the formerly failing
Part26 citation assembly is changed, in a fresh namespace and private cache.
No conditional certificate is repeated, no proof donor is altered, and no cap
is raised. Boolean tables carry no proof until their association is checked.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import direct_citations6 as direct
import global_assembly6 as assembly
import lower_pilot6 as pilot
from memory_probe6 import rts_stats
from owner_audit6 import audit
import owner_lower6 as owner
import owner_split6 as split
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc

PREFIX='Tests.OwnerTrees6'
DIRECTORY='src/Tests/OwnerTrees6'


def header(name):
    return pilot.local_options(assembly.HEADER+f'module {PREFIX}.{name} where\n\n')


def helper_source():
    return header('Lookup')+f'''open import Game.Core
open import Game.Shared
import {direct.PREFIX}.Coverage as C

trees : ∀ {{S}} {{g : Game S}} {{p goal}} →
  List (CheckedExport g p goal) → List (Trie S)
trees [] = []
trees (e ∷ es) = exportStates e ∷ trees es

knownTree : ∀ {{S}} → Keyed S → List (Trie S) → ℕ → S → Bool
knownTree k [] i s = false
knownTree k (t ∷ ts) zero s = knownIn k t s
knownTree k (t ∷ ts) (suc i) s = knownTree k ts i s

valueTrees : ∀ {{S}} → Keyed S → List (Trie S) → Maybe ℕ → Maybe S → Bool
valueTrees k ts owner nothing = true
valueTrees k ts nothing (just s) = false
valueTrees k ts (just i) (just s) = knownTree k ts i s

coveredTrees : ∀ {{S}} → Keyed S → List (Trie S) → Trie ℕ → Trie S → Bool
coveredTrees k ts hints tip = true
coveredTrees k ts tip (node m l r) = false
coveredTrees k ts (node owner x y) (node m l r) =
  valueTrees k ts owner m ∧ (coveredTrees k ts x l ∧ coveredTrees k ts y r)

private
  and-cong : ∀ {{a b c d}} → a ≡ b → c ≡ d → a ∧ c ≡ b ∧ d
  and-cong refl refl = refl

abstract
  knownTree-agree : ∀ {{S}} (k : Keyed S) (g : Game S) p goal
    (es : List (CheckedExport g p goal)) i s →
    knownTree k (trees es) i s ≡ C.ownerKnown k es i s
  knownTree-agree k g p goal [] i s = refl
  knownTree-agree k g p goal (e ∷ es) zero s = refl
  knownTree-agree k g p goal (e ∷ es) (suc i) s =
    knownTree-agree k g p goal es i s

  valueTrees-agree : ∀ {{S}} (k : Keyed S) (g : Game S) p goal
    (es : List (CheckedExport g p goal)) owner m →
    valueTrees k (trees es) owner m ≡ C.ownedValue k es owner m
  valueTrees-agree k g p goal es owner nothing = refl
  valueTrees-agree k g p goal es nothing (just s) = refl
  valueTrees-agree k g p goal es (just i) (just s) = knownTree-agree k g p goal es i s

  coveredTrees-agree : ∀ {{S}} (k : Keyed S) (g : Game S) p goal
    (es : List (CheckedExport g p goal)) hints target →
    coveredTrees k (trees es) hints target ≡ C.coveredBy k es hints target
  coveredTrees-agree k g p goal es hints tip = refl
  coveredTrees-agree k g p goal es tip (node m l r) = refl
  coveredTrees-agree k g p goal es (node owner x y) (node m l r) =
    and-cong (valueTrees-agree k g p goal es owner m)
      (and-cong (coveredTrees-agree k g p goal es x l)
                (coveredTrees-agree k g p goal es y r))

  coveredTrees-sound : ∀ {{S}} (k : Keyed S) (g : Game S) p goal
    (es : List (CheckedExport g p goal)) ts hints target →
    ts ≡ trees es → coveredTrees k ts hints target ≡ true → AllT (Proven g p goal) target
  coveredTrees-sound k g p goal es ts hints target shape accepted =
    C.coveredBy-sound k g p goal es hints target
      (trans (sym (coveredTrees-agree k g p goal es hints target))
        (subst (λ tables → coveredTrees k tables hints target ≡ true) shape accepted))
'''


def fixtures():
    text=header('Fixtures')+f'''open import Game.Core hiding (terminal)
open import Game.Shared
open import {PREFIX}.Lookup
open import {direct.PREFIX}.Fixtures using (keyedBool; terminal; source)

tables : List (Trie Bool)
tables = build [] true ∷ []

association : tables ≡ trees (source ∷ [])
association = refl

good : coveredTrees keyedBool tables (build [] 0) (build [] true) ≡ true
good = refl

proved : AllT (Proven terminal white (λ s → s)) (build [] true)
proved = coveredTrees-sound keyedBool terminal white (λ s → s)
  (source ∷ []) tables (build [] 0) (build [] true) association good

missing : coveredTrees keyedBool [] (build [] 0) (build [] true) ≡ false
missing = refl

wrong-owner : coveredTrees keyedBool tables (build [] 1) (build [] true) ≡ false
wrong-owner = refl

collision : coveredTrees keyedBool tables (build [] 0) (build [] false) ≡ false
collision = refl

omitted : coveredTrees keyedBool tables (build [] 0)
  (node nothing (build [] true) tip) ≡ false
omitted = refl

-- A raw state table can pass a Boolean check but has no proof association.
disconnected : coveredTrees keyedBool (build [] false ∷ [])
  (build [] 0) (build [] false) ≡ true
disconnected = refl
'''
    wrong=header('WrongAssociation')+f'''open import Game.Core
open import Game.Shared
open import {PREFIX}.Lookup using (trees)
open import {direct.PREFIX}.Fixtures using (source)

incorrect : (build [] false ∷ []) ≡ trees (source ∷ [])
incorrect = refl
'''
    return {f'{DIRECTORY}/Fixtures.agda':text,f'{DIRECTORY}/WrongAssociation.agda':wrong}


def binding_source(original):
    if (original.count(f'module {split.NAMESPACE}.Assemble6Split2 where')!=1 or
            original.count('\nmodule P26 where\n')!=1 or
            original.count('    coverage = refl {x = true}')!=1):
        raise ValueError('requires exactly the recorded unchecked Part26 binding')
    text=original.replace(f'module {split.NAMESPACE}.Assemble6Split2 where',f'module {PREFIX}.Binding where',1)
    text=text.replace(f'open import {direct.PREFIX}.Coverage using (coveredBy; coveredBy-sound)',
                      f'open import {PREFIX}.Lookup using (trees; coveredTrees; coveredTrees-sound)',1)
    row=re.search(r'^  sources = (.+)$',text,re.M)
    if not row or not all(re.fullmatch(r'(E\d+(\.P\d+)?|S\d+\.P\d+)\.export',p.strip())
                          for p in row[1].removesuffix(' ∷ []').split(' ∷ ')):
        raise ValueError('unsupported owner export expressions')
    tables=row[1].replace('.export','.states')
    text=text[:row.end()]+f'\n\n  tables : List (Trie (State six))\n  tables = {tables}'+text[row.end():]
    before='''  abstract
    coverage : coveredBy keyed6 sources hints I26.imports ≡ true
    coverage = refl {x = true}

    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = I26.sound
      (coveredBy-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
        sources hints I26.imports coverage)
'''
    after='''  abstract
    association : tables ≡ trees sources
    association = refl {x = tables}

    coverage : coveredTrees keyed6 tables hints I26.imports ≡ true
    coverage = refl {x = true}

    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = I26.sound
      (coveredTrees-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
        sources tables hints I26.imports association coverage)
'''
    if text.count(before)!=1:
        raise ValueError('old checked-export soundness obligation differs')
    text=text.replace(before,after,1)
    if re.search(r'^  hints = (.*)$',text,re.M)[1]!=re.search(r'^  hints = (.*)$',original,re.M)[1]:
        raise ValueError('owner routing hints changed')
    return text


def generated(donor):
    sources={f'{DIRECTORY}/Lookup.agda':helper_source(),
             f'{DIRECTORY}/Binding.agda':binding_source((donor/f'{split.DIRECTORY}/Assemble6Split2.agda').read_text())}
    sources.update(fixtures())
    sources[f'{DIRECTORY}/Facade.agda']=header('Facade')+f'''import {split.NAMESPACE}.Assemble6Split0 as S0
import {split.NAMESPACE}.Assemble6Split1 as S1
import {PREFIX}.Binding as S2

module P24 = S0.P24
module P25 = S1.P25
module P26 = S2.P26
'''
    root=(donor/f'{split.DIRECTORY}/Check.agda').read_text()
    before=f'module {split.NAMESPACE}.Check where'
    if root.count(before)!=1 or root.count(f'import {split.NAMESPACE}.Assemble6 as A')!=1:
        raise ValueError('original root guarantee source differs')
    root=root.replace(before,f'module {PREFIX}.Root where',1).replace(
        f'import {split.NAMESPACE}.Assemble6 as A',f'import {PREFIX}.Facade as A',1)
    sources[f'{DIRECTORY}/Root.agda']=root
    return sources


def run(args):
    previous=args.previous.resolve()
    verified=audit(previous,args.expected_previous_sha256)
    old=json.loads((previous/'final.json').read_text())
    if (old['format']!='othello-owner-lower6-split-v1' or old['status']!='phase-failed' or
            len(old['phases'])!=3 or [p['accepted'] for p in old['phases']]!=[True,True,False] or
            old['phases'][-1]['record']['exit_code']!=251 or old['phases'][-1]['record']['stop_reason']):
        raise ValueError('requires the audited single-binding heap failure')
    donor=Path(old['check_root']);identity=source_identity(donor);pool=assembly6.interfaces(donor)
    machine=assembly6.machine_identity(args.agda)
    if machine!=old['machine'] or len(pool)!=325:
        raise ValueError('original machine, binary or checked prefix differs')
    sources=generated(donor)
    helper=None
    helper_donor=None
    helper_pool=None
    if args.helper_donor:
        helper_donor=args.helper_donor.resolve()
        if assembly6.sha(helper_donor/'final.json')!=args.expected_helper_sha256:
            raise ValueError('helper report differs')
        first=json.loads((helper_donor/'final.json').read_text())
        helper_root=Path(first['check_root'])
        helper_identity=source_identity(helper_root)
        helper_pool=assembly6.interfaces(helper_root)
        helper_name='_build/2.9.0/agda/'+DIRECTORY+'/Lookup.agdai'
        if (first['format']!='othello-owner-trees6-v1' or first['status']!='phase-failed' or first['accepted'] or
                first['machine']!=machine or first['borrowed_interfaces']!=pool or
                [p['label'] for p in first['phases']]!=['Lookup','Fixtures'] or
                not first['phases'][0]['expected_outcome_met'] or first['phases'][1]['expected_outcome_met'] or
                first['phases'][1]['record']['stop_reason'] or
                first['phases'][0]['own_interfaces']!={helper_name:helper_pool.get(helper_name)} or
                helper_pool!=first['final_interfaces'] or len(helper_pool)!=326 or
                helper_identity['source_sha256']!=first['source_sha256'] or
                assembly6.sha(helper_root/f'{DIRECTORY}/Lookup.agda')!=pilot.source_hashes(sources)[f'{DIRECTORY}/Lookup.agda'] or
                pilot.cache_changes(pool,helper_pool)):
            raise ValueError('cannot reuse this generic transfer acceptance')
        helper=dict(previous=str(helper_donor),report_sha256=args.expected_helper_sha256,
                    root=str(helper_root),source_sha256=helper_identity['source_sha256'],
                    name=helper_name,sha256=helper_pool[helper_name],original_phase=first['phases'][0])
    output,runs=args.output.resolve(),args.runs_root.resolve()
    required=sum((donor/n).stat().st_size for n in pool)+sum(len(t.encode()) for t in sources.values())+32*1024**2
    if output.exists() or runs not in output.parents or not pilot.disk_allowed(pilot.disk_usage(runs),required):
        raise ValueError('fresh root and unchanged storage headroom required')
    output.mkdir(parents=True);root=output/'check';root.mkdir()
    for name,_ in source_files(donor):assembly.hardlink(donor/name,root/name)
    for name,text in sources.items():
        p=root/name
        if p.exists():raise ValueError('new target already exists')
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    manifest=bench6.refresh_manifest(root,origin={k:identity[k] for k in ('revision','dirty')})
    for name,digest in pool.items():copy_interface(donor/name,root/name,digest)
    if helper:copy_interface(helper_root/helper['name'],root/helper['name'],helper['sha256'])
    report=dict(format='othello-owner-trees6-v1',status='checking',accepted=False,created_utc=utc(),
        previous=str(previous),previous_report_sha256=args.expected_previous_sha256,previous_audit=verified,
        check_root=str(root),source_sha256=manifest['source_sha256'],
        agda_source_sha256=source_identity(root)['agda_source_sha256'],machine=machine,
        borrowed_interfaces=pool,borrowed_interfaces_sha256=digest_entries(pool),
        generated_source_hashes=pilot.source_hashes(sources),certificate_parts_rechecked=0,
        reused_helper=helper,association_required=True,checked_sample_lower_roots=5,nested_cpu_seconds=0.,phases=[],
        postulates=0,heldout_measured=False,initial_problem2_proved=False,production_authorized=False)
    atomic_json(output/'preflight.json',report)
    sequence=[('Lookup',30,False),('Fixtures',20,False),('WrongAssociation',15,True),
              ('Binding',180,False),('Facade',30,False),('Root',180,False)]
    if helper:sequence=sequence[1:]
    for name,cap,negative in sequence:
        before=assembly6.interfaces(root);target=f'{DIRECTORY}/{name}.agda'
        suffix=pilot.assert_cold(target,before,DIRECTORY)
        if not pilot.disk_allowed(pilot.disk_usage(runs),16*1024**2):report['status']='disk-stop';break
        record=run_job(name,[machine['agda_path'],*assembly6.FLAGS,'--save-metas','-v','tc.decl:10','-i','src',
            target,'+RTS','-M2500M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=cap,timeout=cap*2+30,
            rss_limit_gib=3,log_limit_mib=8,
            metadata=dict(machine=machine,own_target_cold=True,certificate_parts_rechecked=0,
                          borrowed_interfaces_sha256=digest_entries(before),states_only_lookup=True))
        after=assembly6.interfaces(root);changes=pilot.cache_changes(before,after)
        own={n:d for n,d in after.items() if n.endswith(suffix)}
        unexpected=[n for n in after if n not in before and n not in own]
        log=output/'records'/(name+'.log');text=log.read_text();log_sha=assembly6.sha(log)
        rejected=bool(negative and record['exit_code'] and record['exit_code']>0 and not record['stop_reason'] and
            not own and re.findall(r'error: \[([^]]+)\]',text)==['UnequalTerms'] and
            'incorrect = refl' in text)
        outcome=rejected if negative else bool(record['accepted'] and len(own)==1)
        outcome=bool(outcome and not changes and not unexpected and record['source_unchanged'] and
                     record['expected_source_matches'] and record['executable_sha256']==machine['agda_sha256'])
        packed=archive(log,log_sha) if outcome and not negative else None
        report['phases'].append(dict(label=name,target=target,record=record,
            record_sha256=assembly6.sha(output/'records'/(name+'.json')),expected_outcome_met=outcome,
            negative_fixture=negative,cache_changes=changes,unexpected_interfaces=unexpected,own_interfaces=own,
            raw_log_sha256=log_sha,archived_log=packed,rts=rts_stats(text),declaration_tail=text.splitlines()[-35:]))
        report['nested_cpu_seconds']+=record['cpu_seconds'];atomic_json(output/'running.json',report)
        if not outcome:report['status']='cache-mismatch' if changes or unexpected else 'phase-failed';break
    report['donor_unchanged']=source_identity(donor)==identity and assembly6.interfaces(donor)==pool
    report['helper_donor_unchanged']=bool(not helper or
        (source_identity(helper_root)['source_sha256']==helper['source_sha256'] and
         assembly6.interfaces(helper_root)==helper_pool and
         assembly6.sha(helper_donor/'final.json')==args.expected_helper_sha256))
    report['generated_sources_unchanged']=all(assembly6.sha(root/n)==d for n,d in report['generated_source_hashes'].items())
    report['final_interfaces']=assembly6.interfaces(root);report['interfaces_sha256']=digest_entries(report['final_interfaces'])
    report['latest_disk']=pilot.disk_usage(runs)
    report['accepted']=bool(len(report['phases'])==len(sequence) and all(p['expected_outcome_met'] for p in report['phases']) and
        report['donor_unchanged'] and report['helper_donor_unchanged'] and report['generated_sources_unchanged'] and
        pilot.disk_allowed(report['latest_disk']))
    if report['accepted']:report.update(status='complete',checked_sample_lower_roots=6)
    atomic_json(output/'final.json',report)
    print(json.dumps({k:report[k] for k in ('status','accepted','checked_sample_lower_roots','nested_cpu_seconds')}))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('previous','output','runs-root'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--expected-previous-sha256',required=True);p.add_argument('--agda',required=True)
    p.add_argument('--helper-donor',type=Path);p.add_argument('--expected-helper-sha256')
    raise SystemExit(0 if run(p.parse_args())['accepted'] else 2)
