#!/usr/bin/env python3
"""Bounded private-import API pilot on unchanged accepted packed certificates.

The facade reexports existing checked definitions and transparent game aliases.
Generated sources live only in a frozen results root; core/P1 files stay fixed.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface
from global_assembly6 import COMMON,hardlink
from interface_census6 import census_file
from memory_probe6 import rts_stats
from provenance import digest_entries,source_files,source_identity
from run_job import atomic_json,run_job

OLD='Tests.PackedTables6'
NEW='Tests.ScopeFacade6'
OPTIONS='{-# OPTIONS --save-metas --safe --without-K --cubical-compatible #-}\n'
FACADE='''{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.ProofFacade6 where

private
  import Prelude as Pre
  import Agda.Builtin.String as Text
  import Game.Core as Core
  import Game.Shared as Shared
  import Game.Soundness as Sound
  import Game.Transfer as Transfer
  import Othello.Board as Board
  import Othello.Shared6 as Shared6
  import Othello.CompactShared6 as Compact
  import Othello.SharedSymmetry6 as Symmetry6
  import Othello.Statements as Statements
  import Othello.Proof6 as Proof6
  import Othello.Fast6 as Fast
  import Othello.Rules as Rules

open Pre public using
  (List; []; _∷_; Bool; true; false; _≡_; refl; subst; fromMaybe; map;
   _×_; _,_; proj₁; proj₂; ⊤; tt)
open Text public using (String)
open Core public using (black; white; Guarantees)
open Shared public using
  (Trie; tip; AllT; Proven; SharedEntry; entryState; shardStates;
   checkShardBy; shardBy-sound; CheckedExport; checkedExport; selectExport;
   knownIn; knownIn-sound)
open Sound public using (checkSound)
open Transfer public using (guarantees-transfer)
open Board public using (State; six; initial)
open Shared6 public using (keyed6; key6)
open Compact public using (decodeCompactState; decodeCompactEntries)
open Symmetry6 public using (lowerTransport6; upperTransport6)
open Statements public using (lowerGoal; upperGoal)
open Proof6 public using (fastAgreement)

fastGame6 : Core.Game (State six)
fastGame6 = Fast.fastGame6

rulesGame6 : Core.Game (State six)
rulesGame6 = Rules.game six

decode : String → State six
decode text = fromMaybe (initial six) (decodeCompactState text)
'''


def scope_source(original):
    if original.count(COMMON)!=1 or '--safe --without-K --cubical-compatible' not in original:
        raise ValueError('different packed proof template')
    changed=original.replace(COMMON,'open import Othello.ProofFacade6\n\n',1)
    changed=changed.replace(OLD,NEW).replace('Fast.fastGame6','fastGame6').replace('(Rules.game six)','rulesGame6')
    head,body=changed.split(' where\n',1)
    prefix,tail=body.split('\nstates :',1)
    changed=head+' where\n\nprivate\n'+''.join('  '+line+'\n' if line else '\n'
        for line in prefix.strip().splitlines())+'\nstates :'+tail
    before=original.split('  entries :',1)[1].split('  shape :',1)[0]
    after=changed.split('  entries :',1)[1].split('  shape :',1)[0]
    if before!=after or '  accepted = refl {x = true}' not in changed or '  shape = refl {x = states}' not in changed:
        raise ValueError('certificate or equality witness changed')
    return changed


def guarantee_source(part1):
    match=re.search(r'states = shardStates keyed6 \(fromMaybe \[\] \(decodeCompactEntries "([^"]+)"\)\)',part1)
    if not match or len(match[1])<14:raise ValueError('missing exported state list')
    code=match[1][:13]
    return OPTIONS+f'''module Tests.ScopeFacade6.Guarantee where

private
  open import Othello.ProofFacade6
  import Tests.ScopeFacade6.Group0.Part1 as P
  import Othello.Rules as Original

position : State six
position = decode "{code}"

accepted : knownIn keyed6 P.states position ≡ true
accepted = refl

proven : Proven fastGame6 black (upperGoal 4) position
proven = knownIn-sound keyed6 fastGame6 black (upperGoal 4)
  P.states position P.sound accepted

fastGuarantee : Guarantees fastGame6 black (upperGoal 4) position
fastGuarantee = checkSound fastGame6 black (upperGoal 4) position
  (proj₁ proven) (proj₂ proven)

guarantee : Guarantees rulesGame6 black (upperGoal 4) position
guarantee = guarantees-transfer fastGame6 rulesGame6 fastAgreement fastGuarantee

guaranteeOriginal : Guarantees (Original.game six) black (upperGoal 4) position
guaranteeOriginal = guarantee
'''


def run(args):
    previous=args.previous.resolve()
    final=json.loads((previous/'packed.json').read_text())
    audit=json.loads((previous/'phase-records.json').read_text())
    donor=Path(final['resumed_from'])/'check';pool=audit['final_interfaces']
    identity=source_identity(donor);machine=assembly6.machine_identity(args.agda)
    if (final['status']!='collector-failed' or final['accepted'] or
            final['completed_groups']!=list(range(10)) or final['checked_sample_upper_roots']!=100 or
            identity['source_sha256']!=final['source_sha256'] or assembly6.interfaces(donor)!=pool or
            len(pool)!=305 or machine!=final['machine']):
        raise ValueError('requires the unchanged completed packed sample and original binary')
    originals={i:(donor/f'src/Tests/PackedTables6/Group0/Part{i}.agda').read_text() for i in (0,1)}
    sources={'src/Othello/ProofFacade6.agda':FACADE,
             **{f'src/Tests/ScopeFacade6/Group0/Part{i}.agda':scope_source(text) for i,text in originals.items()},
             'src/Tests/ScopeFacade6/Guarantee.agda':guarantee_source(originals[1])}
    if re.findall(r'import Tests\.ScopeFacade6\.Group0\.Part(\d+) as',sources['src/Tests/ScopeFacade6/Group0/Part1.agda'])!=['0']:
        raise ValueError('requires the first two dependency-closed real shards')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    root=output/'check';root.mkdir()
    for name,_ in source_files(donor):hardlink(donor/name,root/name)
    for name,text in sources.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    manifest=bench6.refresh_manifest(root,origin={k:identity[k] for k in ('revision','dirty')})
    generic={name:digest for name,digest in pool.items() if '/Tests/PackedTables6/' not in name}
    if len(generic)!=32:raise ValueError('wrong generic pool')
    for name,digest in generic.items():copy_interface(donor/name,root/name,digest)
    report=dict(format='othello-scope-facade6-v1',status='running',accepted=False,
                source_sha256=manifest['source_sha256'],machine=machine,phases=[],
                original_source_sha256=identity['source_sha256'],initial_problem2_proved=False,
                production_authorized=False,generated_source_hashes={name:assembly6.sha(root/name) for name in sources},
                baseline={str(i):census_file(donor/f'_build/2.9.0/agda/src/Tests/PackedTables6/Group0/Part{i}.agdai',
                    pool[f'_build/2.9.0/agda/src/Tests/PackedTables6/Group0/Part{i}.agdai']) for i in (0,1)})
    records={};spent=0.0
    for label,target in [('facade','src/Othello/ProofFacade6.agda'),
                         ('part0','src/Tests/ScopeFacade6/Group0/Part0.agda'),
                         ('part1','src/Tests/ScopeFacade6/Group0/Part1.agda'),
                         ('guarantee','src/Tests/ScopeFacade6/Guarantee.agda')]:
        before=assembly6.interfaces(root)
        suffix='/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'
        if any(name.endswith(suffix) for name in before):raise ValueError('own target not cold')
        record=run_job(label,[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
            '+RTS','-M1350M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=min(90,args.kernel_cpu_budget-spent),
            timeout=270,rss_limit_gib=1.5,log_limit_mib=2,
            metadata={'machine':machine,'own_target_cold':True,
                      'interface_isolation':'private copies, one serial cache',
                      'borrowed_interfaces_sha256':digest_entries(before)})
        spent+=record['cpu_seconds'];after=assembly6.interfaces(root)
        changes=[name for name,digest in before.items() if after.get(name)!=digest]
        metric={
            key:record[key] for key in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib')}
        metric.update(label=label,target=target,exit_code=record['exit_code'],cache_changes=changes,
                      rts=rts_stats((output/'records'/f'{label}.log').read_text()))
        if changes:metric['accepted']=False
        if record['accepted'] and not changes:
            own=[name for name in after if name.endswith(suffix)]
            if len(own)!=1:raise ValueError('missing accepted interface')
            metric['interface']=census_file(root/own[0],after[own[0]])
        records[label]=record;report['phases'].append(metric);report['measured_kernel_cpu_seconds']=spent
        atomic_json(output/'scope.json',report);print(json.dumps(metric),flush=True)
        if not metric['accepted']:report['status']='phase-failed';break
    else:report['status']='complete';report['accepted']=True
    if source_identity(donor)!=identity or assembly6.interfaces(donor)!=pool:
        raise ValueError('original proof donor changed')
    report.update(donor_sources_unchanged=True,donor_interfaces_unchanged=True)
    atomic_json(output/'phase-records.json',dict(records=records,
        record_hashes={name:assembly6.sha(output/'records'/f'{name}.json') for name in records},
        log_hashes={name:assembly6.sha(output/'records'/f'{name}.log') for name in records},
        final_interfaces=assembly6.interfaces(root),generated_source_hashes=report['generated_source_hashes']))
    atomic_json(output/'scope.json',report)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--kernel-cpu-budget',type=float,default=150)
    run(p.parse_args())
