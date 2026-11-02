"""AI-assisted untrusted rows checked directly against the accepted full map.

Only each owned route is needed; every citation uses the same full resolver.
This measures two existing parts, not full certificate production.
"""
import json
from pathlib import Path

import completion_batch6 as prior
from canonical_join6 import emit_join
from full_map_alignment6 import route
from provenance import source_identity
from wire_workflow6 import require

PARTS = [342,33154]
HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
COMMON = '''open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Agda.Builtin.String using (String)
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatMapRoute as R
import Othello.LazyIndexed6 as Lazy
import Othello.NatIndexed6 as D
'''


def emit(check,prefix):
    check=Path(check)
    require(not check.exists(),'fresh private resolver probe required')
    accepted=json.loads((prior.OUT/'report.json').read_text())
    require(accepted['accepted'],'accepted compact row baseline required')
    manifest=json.loads((prior.bridge.FULL/'results/full-state-map6.json').read_text())
    chunks={c['part']:c for c in manifest['chunks']}
    family=prefix+'.Rows342.Family'
    sources={}
    def add(module,body):
        require(module not in sources,'unique module required')
        sources[module]=HEADER+'-- AI-assisted; all Boolean and linkage claims require safe Agda.\nmodule '+module+' where\n\n'+body
    add(family,COMMON+'''import Tests.CompletionBatchLowerA6.Rows342.Family as Original
module L = Original.L
module A = Original.A
''')
    add(prefix+'.Link',COMMON+f'''import {family} as Family
abstract
  linked : ∀ {{n}} base (fullMap : M.Map (State six)) (stateText bodyText : String) →
    Family.L.checkPart {{n}} (M.lookup fullMap) (λ i → base + B.finToNat i) stateText bodyText ≡ true →
    (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Compatible fullMap G →
    Laws.Aligned (M.rows base n (Lazy.states n stateText)) G →
    Laws.Aligned (M.rows base n (D.bodies n bodyText)) C →
    Family.A.Partial G C (M.rows base n (Lazy.states n stateText))
  linked {{n}} base fullMap stateText bodyText accepted G C sameFull sameStates sameBodies =
    Family.A.rows base (Lazy.states n stateText) G C
      (Family.L.linkPart (M.lookup fullMap) (λ i → base + B.finToNat i)
        stateText bodyText accepted G C sameFull sameStates sameBodies)
''')
    units=[]
    for part in PARTS:
        row=prefix+'.Rows'+str(part)
        bridge=prefix+'.Bridge'+str(part)
        old='Tests.CompletionBatchLowerA6.Rows'+str(part)
        own=chunks[part]['module']
        add(row+'.BodyData'+str(part),COMMON+f'''import {old}.BodyData{part} as Original
text = Original.text
bodies = Original.bodies
''')
        add(row+'.Part'+str(part),COMMON+f'''import {family} as Family
import {prefix}.Link as Link
import {own} as Own
import {row}.BodyData{part} as Body
import Tests.FullInitialLower6.Root as Full using (stateMap)
states : M.Map (State six)
states = M.rows {200*part} 200 (Lazy.states 200 Own.text)
bodies : M.Map (I.IndexedCertificate ℕ)
bodies = M.rows {200*part} 200 Body.bodies
embed : B.Fin 200 → ℕ
embed i = {200*part} + B.finToNat i
abstract
  accepted : Family.L.checkPart (M.lookup Full.stateMap) embed Own.text Body.text ≡ true
  accepted = refl
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Compatible Full.stateMap G → Laws.Aligned states G → Laws.Aligned bodies C →
    Family.A.Partial G C states
  linked = Link.linked {{n = 200}} {200*part} Full.stateMap Own.text Body.text accepted
''')
        add(bridge+'.Root',COMMON+f'''import {family} as Family
import {row}.Part{part} as Part
import {row}.BodyData{part} as Body
import {own} as Own
import Tests.FullInitialLower6.Root as Full using (stateMap)
statePath : R.Route Full.stateMap {200*part} 200 (Lazy.states 200 Own.text)
statePath = {route(0,manifest['parts'],part)}
bodyPath : R.Route Part.bodies {200*part} 200 Body.bodies
bodyPath = R.here
abstract
  symbolic : ∀ G C → Laws.Compatible Full.stateMap G →
    Laws.Compatible Part.bodies C → Family.A.Partial G C Part.states
  symbolic G C sameStates sameBodies = Part.linked G C sameStates
    (R.aligned G statePath sameStates) (R.aligned C bodyPath sameBodies)
''')
        units.append(dict(part=part,rows=200,row_prefix=row,bridge_prefix=bridge))
    check.mkdir(parents=True)
    for module,body in sources.items():
        p=check/'src'/(module.replace('.','/')+'.agda');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
    joint=emit_join(check.parent/'joint-source',manifest,units,prefix=prefix+'.Combined')
    for p in (check.parent/'joint-source/src').rglob('*.agda'):
        target=check/p.relative_to(check.parent/'joint-source');target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(p.read_bytes())
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    return source_identity(check)
