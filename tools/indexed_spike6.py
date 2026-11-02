#!/usr/bin/env python3
"""Bounded real three-shard indexed proof and explicit optimal-path pilot.

Every local proof imports only state data and its own body data. The global
soundness application is assembled separately. This uses a late 6x6 position,
not the initial board; all acceptance and play claims come from safe Agda.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import assembly6
import compact_shared6 as compact
import generate6
from census_pilot6 import state
from owner_cache_dedup6 import allocated
from provenance import source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require
import ref

PREFIX = 'Tests.IndexedSpike6'
HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'
BASE = 'b001112211122211211212111221122211111'
IMAGE = 'b211100221112112112111212221122111112'
COMMON = '''open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (white; black; Guarantees)
open import Game.Symmetry using (Proven)
import Game.Indexed as I
import Game.Balanced as B
import Game.BalancedView as View
import Othello.Indexed6 as D
open import Othello.Board using (State; six; initial)
open import Othello.Statements using (lowerGoal; upperGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6; upperTransport6)
import Othello.Fast6 as Fast
import Tests.IndexedSpike6.Shape as Shape

module Lower = D.Checking Shape.shape Fast.fastGame6 white (lowerGoal 4) lowerTransport6
module Upper = D.Checking Shape.shape Fast.fastGame6 black (upperGoal 4) upperTransport6

presentStates : ∀ {n} → B.Vec (State six) n → B.Vec (Maybe (State six)) n
presentStates B.nil = B.nil
presentStates (B.cons s ss) = B.cons (just s) (presentStates ss)
'''


def module(name, body):
    return HEADER+'-- AI-assisted untrusted pilot; safe Agda checks the claims.\nmodule '+PREFIX+'.'+name+' where\n\n'+body


def prepare(check):
    base = state(BASE[1:], 'black')
    passed = ref.successors(base)
    require(not ref.placements(base) and len(passed)==1, 'expected genuine forced pass')
    choices = ref.successors(passed[0])
    require(len(choices)==2, 'expected both opponent replies')
    terminal = ref.successors(choices[1])
    require(len(terminal)==1 and not ref.successors(terminal[0]), 'expected terminal selected reply')
    require(terminal[0].cells.count(ref.BLACK)==16 and terminal[0].cells.count(ref.WHITE)==20,
            'selected late line must end 16-20')
    off = generate6.encode_state(choices[0])
    path = [generate6.encode_state(passed[0]), generate6.encode_state(choices[1]),
            generate6.encode_state(terminal[0])]
    texts = {
        'lower_states': [compact.pack_state(BASE)*2, compact.pack_state(IMAGE), compact.pack_state(IMAGE)],
        'upper_states': [compact.pack_state(off)+compact.pack_state(BASE), compact.pack_state(IMAGE), compact.pack_state(IMAGE)],
        'lower_bodies': ['PC1F1LKa00', 'R4a00', 'Kba00'],
        'upper_bodies': ['C0LPF2Ka00C0L', 'R4a01', 'Kba00'],
    }
    sources = {}
    def emit(name, body):
        sources['src/'+PREFIX.replace('.', '/')+'/'+name+'.agda'] = module(name, body)
    emit('Shape', '''open import Prelude
import Game.Balanced as B
shape : B.Shape
shape = B.branch (B.leaf 2) (B.branch (B.leaf 1) (B.leaf 1))
''')
    sizes = [2, 1, 1]
    embeds = ['λ i → B.left (B.row i)', 'λ i → B.right (B.left (B.row i))',
              'λ i → B.right (B.right (B.row i))']
    for j,n in enumerate(sizes):
        emit('StateData'+str(j), '''open import Prelude
open import Agda.Builtin.String using (String)
import Game.Balanced as B
import Othello.Indexed6 as D
open import Othello.Board using (State; six)
'''+''.join(f'{side}Text : String\n{side}Text = "{texts[side+"_states"][j]}"\n'
                   f'{side} : B.Vec (State six) {n}\n{side} = D.states {n} {side}Text\n'
                   for side in ('lower','upper')))
        emit('BodyData'+str(j), '''open import Prelude
open import Agda.Builtin.String using (String)
import Game.Balanced as B
import Game.Indexed as I
import Othello.Indexed6 as D
import Tests.IndexedSpike6.Shape as Shape
'''+''.join(f'{side}Text : String\n{side}Text = "{texts[side+"_bodies"][j]}"\n'
                   f'{side} : B.Vec (I.IndexedCertificate (B.Id Shape.shape)) {n}\n'
                   f'{side} = D.bodies Shape.shape {n} {side}Text\n'
                   for side in ('lower','upper')))
        dependencies = sorted({j, 0 if j < 2 else 1})
        imports = ''.join(f'import {PREFIX}.StateData{k} as S{k}\n' for k in dependencies)
        imports += f'import {PREFIX}.BodyData{j} as OwnBody\n'
        body = COMMON+imports+f'\nembed : B.Fin {n} → B.Id Shape.shape\nembed = {embeds[j]}\n'
        for side,checker in (('lower','Lower'),('upper','Upper')):
            view = ('View.branches (View.present (presentStates S0.'+side+')) View.absent'
                    if j < 2 else
                    'View.branches View.absent (View.branches (View.present (presentStates S1.'+side+')) View.absent)')
            body += f'''
{side}View : View.View (State six) Shape.shape
{side}View = {view}
{side}Resolver : I.Resolver (B.Id Shape.shape) (State six)
{side}Resolver = View.resolve {side}View
abstract
  {side}Accepted : {checker}.checkPart {side}Resolver embed S{j}.{side}Text OwnBody.{side}Text ≡ true
  {side}Accepted = refl

{side}Linked : (G : B.Id Shape.shape → State six) →
  (C : B.Id Shape.shape → I.IndexedCertificate (B.Id Shape.shape)) →
  {checker}.V.Compatible {side}Resolver G →
  (∀ i → G (embed i) ≡ B.lookupVec S{j}.{side} i) →
  (∀ i → C (embed i) ≡ B.lookupVec OwnBody.{side} i) →
  ∀ i → {checker}.V.TreeOK G (embed i) (G (embed i)) (C (embed i))
{side}Linked G C compatible sameState sameBody =
  {checker}.linkPart {side}Resolver embed S{j}.{side}Text OwnBody.{side}Text
    {side}Accepted G C compatible sameState sameBody
'''
        require('.Part' not in imports, 'local checker imports a child proof')
        emit('Part'+str(j), body)
    imports = ''.join(f'import {PREFIX}.StateData{j} as S{j}\nimport {PREFIX}.BodyData{j} as C{j}\n'
                      f'import {PREFIX}.Part{j} as P{j}\n' for j in range(3))
    body = COMMON+imports
    for side, checker in (('lower','Lower'),('upper','Upper')):
        body += f'''
{side}States : B.Tree (State six) Shape.shape
{side}States = B.join (B.rows S0.{side}) (B.join (B.rows S1.{side}) (B.rows S2.{side}))
{side}Bodies : B.Tree (I.IndexedCertificate (B.Id Shape.shape)) Shape.shape
{side}Bodies = B.join (B.rows C0.{side}) (B.join (B.rows C1.{side}) (B.rows C2.{side}))
{side}G : B.Id Shape.shape → State six
{side}G = B.lookup {side}States
{side}C : B.Id Shape.shape → I.IndexedCertificate (B.Id Shape.shape)
{side}C = B.lookup {side}Bodies

{side}Compatible0 : {checker}.V.Compatible P0.{side}Resolver {side}G
{side}Compatible0 (B.left (B.row B.fzero)) u refl = refl
{side}Compatible0 (B.left (B.row (B.fsuc B.fzero))) u refl = refl
{side}Compatible0 (B.right (B.left (B.row B.fzero))) u ()
{side}Compatible0 (B.right (B.right (B.row B.fzero))) u ()

{side}Compatible2 : {checker}.V.Compatible P2.{side}Resolver {side}G
{side}Compatible2 (B.left (B.row B.fzero)) u ()
{side}Compatible2 (B.left (B.row (B.fsuc B.fzero))) u ()
{side}Compatible2 (B.right (B.left (B.row B.fzero))) u refl = refl
{side}Compatible2 (B.right (B.right (B.row B.fzero))) u ()

{side}Rows : ∀ i → {checker}.V.TreeOK {side}G i ({side}G i) ({side}C i)
{side}Rows (B.left (B.row i)) = P0.{side}Linked {side}G {side}C
  {side}Compatible0 (λ j → refl) (λ j → refl) i
{side}Rows (B.right (B.left (B.row i))) = P1.{side}Linked {side}G {side}C
  {side}Compatible0 (λ j → refl) (λ j → refl) i
{side}Rows (B.right (B.right (B.row i))) = P2.{side}Linked {side}G {side}C
  {side}Compatible2 (λ j → refl) (λ j → refl) i
'''
    body += '''
root : B.Id Shape.shape
root = B.right (B.right (B.row B.fzero))
lowerRoot : Proven Fast.fastGame6 white (lowerGoal 4) (lowerG root)
lowerRoot = Lower.V.global-proven lowerG lowerC lowerRows root
upperRoot : Proven Fast.fastGame6 black (upperGoal 4) (upperG root)
upperRoot = Upper.V.global-proven upperG upperC upperRows root
abstract
  offUpper : Proven Fast.fastGame6 black (upperGoal 4)
    (B.lookupVec S0.upper B.fzero)
  offUpper = Upper.V.global-proven upperG upperC upperRows (B.left (B.row B.fzero))
'''
    body += '''
open import Game.Soundness using (checkSound)
open import Game.Transfer using (guarantees-transfer)
open import Othello.Proof6 using (fastAgreement)
import Othello.Rules as Rules

lowerOriginal : Guarantees (Rules.game six) white (lowerGoal 4) (lowerG root)
lowerOriginal = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement
  (checkSound Fast.fastGame6 white (lowerGoal 4) (lowerG root)
    (proj₁ lowerRoot) (proj₂ lowerRoot))
upperOriginal : Guarantees (Rules.game six) black (upperGoal 4) (upperG root)
upperOriginal = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement
  (checkSound Fast.fastGame6 black (upperGoal 4) (upperG root)
    (proj₁ upperRoot) (proj₂ upperRoot))
'''
    emit('Assemble', body)
    positions = [BASE,*path]
    body = COMMON+f'''import {PREFIX}.Assemble as A
import {PREFIX}.StateData0 as S0
import Game.Spine as Spine
open import Game.Certificate using (certificateStrategy)
open import Game.Joint
open import Game.Transfer using (completedPlay-transfer)
open import Othello.Encode6 using (stateEquality6)
open import Othello.CompactShared6 using (decodeCompactState)
open import Othello.Proof6 using (terminalCounts; counts-sound; fastAgreement)
import Othello.Rules as Rules
open import Othello.Statements using (ScoreSix)
'''
    # Positions in types keep reductions bounded to the selected small line.
    for j,s in enumerate(positions):
        body += f'position{j} : State six\nposition{j} = fromMaybe (initial six) (decodeCompactState "{compact.pack_state(s)}")\n'
    body += '''
module W = Spine.Paths Fast.fastGame6 white (lowerGoal 4)
module Bk = Spine.Paths Fast.fastGame6 black (upperGoal 4)

whiteSpine : W.Spine position0
whiteSpine = W.forced refl refl
  (W.pick {i = 1} refl refl refl
    (W.split refl refl (W.cons (W.finish refl refl) W.nil)))

blackSpine : Bk.Spine position0
blackSpine = Bk.forced refl refl
  (Bk.split refl refl
    (Bk.cons (Bk.plug A.offUpper)
      (Bk.cons (Bk.pick {i = 0} refl refl refl (Bk.finish refl refl)) Bk.nil)))

lower : Proven Fast.fastGame6 white (lowerGoal 4) position0
lower = W.proven whiteSpine
upper : Proven Fast.fastGame6 black (upperGoal 4) position0
upper = Bk.proven blackSpine
path : List (State six)
path = position1 ∷ position2 ∷ position3 ∷ []

joint : jointCheck stateEquality6 Fast.fastGame6 terminalCounts position0
  (certificateStrategy (proj₁ lower)) (certificateStrategy (proj₁ upper)) path ≡ true
joint = refl

completed : Σ (State six) (λ t →
  CompletedPlay Fast.fastGame6 white (certificateStrategy (proj₁ lower))
    (certificateStrategy (proj₁ upper)) position0 t × (terminalCounts t ≡ true))
completed = joint-sound stateEquality6 Fast.fastGame6 terminalCounts position0
  (certificateStrategy (proj₁ lower)) (certificateStrategy (proj₁ upper)) path joint

open import Othello.Board using (discs)

originalPlay : Σ (State six) (λ t →
  CompletedPlay (Rules.game six) white (certificateStrategy (proj₁ lower))
    (certificateStrategy (proj₁ upper)) position0 t ×
    ((discs black t ≡ 16) × (discs white t ≡ 20)))
originalPlay with completed
... | t , play , counts = t ,
  completedPlay-transfer Fast.fastGame6 (Rules.game six) fastAgreement play ,
  counts-sound t counts
'''
    # The spike uses completedPlay in the type, and count extraction is checked
    # by the existing terminalCounts checker. No initial Problem2 type occurs.
    body = body.replace('open import Game.Core using (white; black; Guarantees)',
                        'open import Game.Core using (white; black; Guarantees; CompletedPlay)')
    body = body.replace('open import Othello.Statements using (ScoreSix)\n','')
    emit('Spines', body)
    emit('Rejected', COMMON+f'''import {PREFIX}.Part0 as P0
import {PREFIX}.Part1 as P1
import {PREFIX}.StateData0 as S0
import {PREFIX}.StateData1 as S1

missingReply : Lower.checkPart P0.lowerResolver P0.embed S0.lowerText "PC1F0Ka00" ≡ false
missingReply = refl
badCount : Lower.checkPart P1.lowerResolver P1.embed S1.lowerText "R4a00L" ≡ false
badCount = refl
cycle : Lower.checkPart P0.lowerResolver P0.embed S0.lowerText "Ka01Ka00" ≡ false
cycle = refl
badTag : Lower.checkPart P1.lowerResolver P1.embed S1.lowerText "R8a00" ≡ false
badTag = refl
missingImport : Lower.checkPart (λ _ → nothing) P1.embed S1.lowerText "R4a00" ≡ false
missingImport = refl
''')
    emit('Everything', f'import Everything6\nimport {PREFIX}.Spines\nimport {PREFIX}.Rejected\n')
    hashes = {}
    for name,text in sources.items():
        dest=check/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(text)
        hashes[name]=hashlib.sha256(text.encode()).hexdigest()
    return dict(generated_sha256=hashes, total_generated_bytes=sum(len(s.encode()) for s in sources.values()),
                rows_per_direction=4, shards_per_direction=3, local_child_proof_imports=False,
                initial_problem2_proved=False, optimal_initial_pair_proved=False,
                explicit_late_path=positions, terminal=dict(black=16,white=20),
                native_preparation_only=True)


def run(args):
    current=Path.cwd().resolve()
    out=args.output.resolve()
    require(not out.exists() and 'results' in out.parts,'fresh isolated output required')
    out.mkdir(parents=True)
    machine=assembly6.machine_identity(args.agda)
    require(machine['hostname']=='eapiova' and machine['agda_sha256']==args.expected_agda_sha256,
            'pinned desktop/compiler required')
    check=out/'check'
    check.mkdir()
    shutil.copytree(current/'src',check/'src',copy_function=shutil.copy2)
    shutil.copy2(current/'othello.agda-lib',check/'othello.agda-lib')
    report=dict(format='othello-indexed-spike6-v1',created_utc=utc(),status='preparing',accepted=False,
                machine=machine, phases=[], kernel_cpu_seconds=0., initial_problem2_proved=False,
                optimal_initial_pair_proved=False, production_authorized=False)
    def save(): atomic_json(out/'report.json',report)
    save()
    report['prepared']=prepare(check)
    source=source_identity(check)
    report['checked_source']=source
    save()
    targets=['Part0','Part1','Part2','Assemble','Spines','Rejected','Everything']
    for j,name in enumerate(targets):
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        require(used<10*2**30 and free>=100*2**30,'storage gate reached; earlier facts preserved')
        require(report['kernel_cpu_seconds']<args.kernel_cpu_limit,'kernel budget reached')
        command=[args.agda,'--no-libraries','-i','src','--safe','--without-K','--cubical-compatible',
                 '--save-metas',f'src/{PREFIX.replace(".","/")}/{name}.agda',
                 '+RTS','-M1350M','-c','-s','-RTS']
        record=run_job('target'+str(j),command,out/'records',root=check,timeout=160,
                       cpu_limit=min(90.,args.kernel_cpu_limit-report['kernel_cpu_seconds']),
                       rss_limit_gib=1.5,log_limit_mib=2,expected_source_sha256=source['source_sha256'],
                       metadata=dict(target=name,cache_policy='own target cold; prior same-root imports reused',
                                     child_proof_imports=(name not in ('Part0','Part1','Part2'))))
        report['phases'].append(dict(target=name,record=record))
        report['kernel_cpu_seconds']+=record['cpu_seconds']
        save()
        require(record['accepted'],'safe kernel target failed: '+name)
    report.update(status='complete',accepted=True,finished_utc=utc(),
                  late_original_rule_bounds_checked=True, late_joint_16_20_checked=True,
                  original_source_unchanged=source_identity(check)['source_sha256']==source['source_sha256'])
    save()
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--expected-agda-sha256',required=True)
    p.add_argument('--kernel-cpu-limit',type=float,default=160.)
    args=p.parse_args()
    r=run(args)
    print(json.dumps(dict(accepted=r['accepted'],kernel_cpu_seconds=r['kernel_cpu_seconds'],
                          initial_problem2_proved=False)))


if __name__=='__main__': main()
