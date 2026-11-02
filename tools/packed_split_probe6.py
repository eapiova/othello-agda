"""AI-assisted separation of Boolean checking and conditional row linkage."""
import hashlib
from pathlib import Path

import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json,utc
from wire_workflow6 import require

PREFIX='Tests.PackedNatSplitProbe6'
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'


def emit(check):
    check=Path(check);require(not check.exists(),'fresh split probe required')
    check.mkdir(parents=True)
    original=prior.ROOT/'src/Othello/CompatibleRows6.agda';raw=original.read_bytes()
    target=check/'src/Othello/CompatibleRows6.agda';target.parent.mkdir(parents=True);target.write_bytes(raw)
    folder=check/'src/Tests/PackedNatSplitProbe6';folder.mkdir(parents=True)
    common='''open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.LazyIndexed6 as Lazy
import Tests.CompletionBatchLowerA6.Rows33154.Part33154 as Original
import Tests.CompletionBatchLowerA6.Rows33154.Family as Family
import Tests.CompletionBatchLowerA6.Rows33154.BodyData33154 as Body
import Tests.FullInitialLower6.StateData33154 as Own
import Tests.SparseCitationFixed6.Rows33154.Part33154 as Sparse
import Tests.PackedNatProbe6.Data as Data
'''
    left=common+'''abstract
  accepted : Family.L.Lower.checkRows (M.lookup Sparse.demand) Original.embed Data.states Body.bodies ≡ true
  accepted = refl
'''
    right=common+'''embed : B.Fin 200 → ℕ
embed i = B.finToNat i + 6630800
abstract
  accepted : Family.L.Lower.checkRows (M.lookup Sparse.demand) embed Data.states Body.bodies ≡ true
  accepted = refl
'''
    old=common+f'''import {PREFIX}.Left as Checked
import Tests.DirectRowsProbeFixed6.Link as Link
abstract
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned Original.demand G → Laws.Aligned Original.states G →
    Laws.Aligned Original.bodies C → Family.A.Partial G C Original.states
  linked G C sameDemand sameStates sameBodies =
    Link.linked {{n = 200}} 6630800 Sparse.demand Data.states (Lazy.states 200 Own.text)
      Body.bodies Body.bodies Data.same refl Checked.accepted G C
      (Sparse.aligned G sameDemand) sameStates sameBodies
'''
    new=common+f'''open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.Fast6 as Fast
import Othello.CompatibleRows6 as Compatible
import {PREFIX}.Right as Checked
module C = Compatible.Checking Fast.fastGame6 white (lowerGoal 4) lowerTransport6
abstract
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Compatible Sparse.demand G → Laws.Compatible Original.states G →
    Laws.Compatible Original.bodies C → Family.A.Partial G C Original.states
  linked = C.linked {{n = 200}} 6630800 Sparse.demand Data.states (Lazy.states 200 Own.text)
    Body.bodies Body.bodies Data.same refl Checked.accepted
'''
    for name,body in [('Left',left),('Right',right),('Aligned',old),('Compatible',new)]:
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted safe cost separation; original certificate rows only.\nmodule '+PREFIX+'.'+name+' where\n\n'+body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-packed-split6-sources-v1',created_utc=utc(),
        source=str(original),source_sha256=hashlib.sha256(raw).hexdigest(),original_rows=200,new_distinct_rows=0,
        obligations=['generic right-addition/compatible linkage','separate left/right owner Boolean checking','aligned old linkage','compatible new linkage'],
        mathematical_objective_complete=False))
    return source_identity(check)
