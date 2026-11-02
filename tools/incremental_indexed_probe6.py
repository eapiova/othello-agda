"""AI-assisted indexed-row comparison, preserving the original Partial type."""
import hashlib
import json
from pathlib import Path

import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json,utc
from wire_workflow6 import require

PREFIX='Tests.IncrementalIndexedProbe6'
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
CORE=['Game/IndexedTransfer.agda','Othello/IncrementalIndexed6.agda']


def emit(check, *, prefix=PREFIX, split=False, fused=False, skip_core=False):
    check=Path(check);require(not check.exists(),'fresh indexed optimization root required')
    check.mkdir(parents=True)
    pins={}
    for relative in CORE:
        source=prior.ROOT/'src'/relative;raw=source.read_bytes()
        require(all(flag.encode() in raw.splitlines()[0] for flag in ['--safe','--without-K','--cubical-compatible']),
                'safe generic source required')
        if not skip_core:
            target=check/'src'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pins[str(source)]=hashlib.sha256(raw).hexdigest()
    folder=check/'src'/prefix.replace('.','/');folder.mkdir(parents=True)
    common='''open import Prelude
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Tests.CompletionBatchLowerA6.Rows33154.Part33154 as Original
import Tests.CompletionBatchLowerA6.Rows33154.Family as Family
import Tests.CompletionBatchLowerA6.Rows33154.BodyData33154 as Body
import Tests.FullInitialLower6.StateData33154 as Own
import Tests.SparseCitationFixed6.Rows33154.Part33154 as Sparse
'''
    baseline=common+'''abstract
  accepted : Family.L.checkPart (M.lookup Sparse.demand) Original.embed Own.text Body.text ≡ true
  accepted = refl
'''
    variant=common+'''open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.IncrementalIndexed6 as Faster
import Tests.FullResolverProbe6.Link as Link
module Check = Faster.Checking white (lowerGoal 4) lowerTransport6
abstract
  fastAccepted : Check.Optimized.checkPart (M.lookup Sparse.demand) Original.embed Own.text Body.text ≡ true
  fastAccepted = refl
  accepted : Family.L.checkPart (M.lookup Sparse.demand) Original.embed Own.text Body.text ≡ true
  accepted = Check.accepted-old (M.lookup Sparse.demand) Original.embed Own.text Body.text fastAccepted
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned Original.demand G → Laws.Aligned Original.states G →
    Laws.Aligned Original.bodies C → Family.A.Partial G C Original.states
  linked G C sameDemand sameStates sameBodies =
    Link.linked {n = 200} 6630800 Sparse.demand Own.text Body.text accepted G C
      (Laws.aligned-compatible {map = Sparse.demand} {G = G} (Sparse.aligned G sameDemand))
      sameStates sameBodies
'''
    sources=[('Baseline',baseline),('Variant',variant)]
    if fused:
        shared=common+'''open import Game.Core using (white)
import Othello.LazyIndexed6 as Lazy
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.Fast6 as Fast
import Othello.CompatibleRows6 as Compatible
import Othello.IncrementalIndexed6 as Faster
import Tests.PackedNatProbe6.Data as Packed
module Link = Compatible.Checking Fast.fastGame6 white (lowerGoal 4) lowerTransport6
module Improved = Faster.Checking white (lowerGoal 4) lowerTransport6
'''
        sources=[]
        for name,ss,method in [('Char','Lazy.states 200 Own.text','Link.linked'),
                               ('Nat','Packed.states','Link.linked'),
                               ('FastChar','Lazy.states 200 Own.text','Improved.linkedRows'),
                               ('FastNat','Packed.states','Improved.linkedRows')]:
            sources.append((name,shared+f'''states : M.Map (State six)
states = M.rows 6630800 200 ({ss})
bodies : M.Map (I.IndexedCertificate ℕ)
bodies = Original.bodies
abstract
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Compatible Sparse.demand G → Laws.Compatible states G →
    Laws.Compatible bodies C → Family.A.Partial G C states
  linked = {method} {{n = 200}} 6630800 Sparse.demand ({ss}) ({ss})
    Body.bodies Body.bodies refl refl refl
'''))
        sources.append(('Root',''.join(f'import {prefix}.{name}\n' for name,_,_ in
            [('Char',0,0),('Nat',0,0),('FastChar',0,0),('FastNat',0,0)])))
    if split:
        settings='''open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.IncrementalIndexed6 as Faster
module Check = Faster.Checking white (lowerGoal 4) lowerTransport6
'''
        fast=common+settings+'''abstract
  fastAccepted : Check.Optimized.checkPart (M.lookup Sparse.demand) Original.embed Own.text Body.text ≡ true
  fastAccepted = refl
'''
        transported=common+settings+f'''import {prefix}.Fast as Verified
import Tests.FullResolverProbe6.Link as Link
abstract
  accepted : Family.L.checkPart (M.lookup Sparse.demand) Original.embed Own.text Body.text ≡ true
  accepted = Check.accepted-old (M.lookup Sparse.demand) Original.embed Own.text Body.text Verified.fastAccepted
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned Original.demand G → Laws.Aligned Original.states G →
    Laws.Aligned Original.bodies C → Family.A.Partial G C Original.states
  linked G C sameDemand sameStates sameBodies =
    Link.linked {{n = 200}} 6630800 Sparse.demand Own.text Body.text accepted G C
      (Laws.aligned-compatible {{map = Sparse.demand}} {{G = G}} (Sparse.aligned G sameDemand))
      sameStates sameBodies
'''
        sources=[('Baseline',baseline),('Fast',fast),('Transported',transported)]
    for name,body in sources:
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted safe indexed-row comparison; existing rows only.\nmodule '+prefix+'.'+name+' where\n\n'+body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-incremental-indexed6-sources-v1',
        created_utc=utc(),copied_core_sha256=pins,source_part=33154,rows=200,new_distinct_rows=0,
        separated_evaluation_and_proof_transport=split,
        fused_boolean_refl_and_soundness=fused,import_only_root=fused,
        reused_checked_core=skip_core,
        benchmark_scope='Same compact data and singleton resolver; new evaluation is transported to the original Boolean acceptance and Partial judgment.',
        mathematical_objective_complete=False))
    return source_identity(check)
