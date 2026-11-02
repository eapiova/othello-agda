"""AI-assisted untrusted integer-state data for the original safe row checker.

The checker still sees ordinary State six values. The instance equality and
the original conditional Partial judgment must both be checked by Agda.
"""
import hashlib
import json
from pathlib import Path

import compact_shared6 as compact
import completion_batch6 as prior
import ref
from provenance import source_identity
from run_job import atomic_json,utc
from wire_workflow6 import require

PREFIX='Tests.PackedNatProbe6'
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'


def code(raw):
    require(len(raw)==37 and raw[0] in 'bw' and all(c in '012' for c in raw[1:]),'exact ternary state required')
    return 2*sum(int(c)*3**i for i,c in enumerate(raw[1:]))+(raw[0]=='w')


def emit(check):
    check=Path(check);require(not check.exists(),'fresh packed-state probe required')
    sample=json.loads((prior.OUT/'sample.json').read_text())
    case=next(c for c in sample['cases'] if c['part']==33154)
    require(case['rows']==200 and len(case['state_text'])==2600,'exact200-row state instance required')
    codes=[code(compact.unpack_state(case['state_text'][13*i:13*i+13])) for i in range(200)]
    check.mkdir(parents=True)
    original=prior.ROOT/'src/Othello/PackedNat6.agda';raw=original.read_bytes()
    target=check/'src/Othello/PackedNat6.agda';target.parent.mkdir(parents=True);target.write_bytes(raw)
    folder=check/'src/Tests/PackedNatProbe6';folder.mkdir(parents=True)
    common='''open import Prelude
open import Othello.Board using (State; six; initial)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.LazyIndexed6 as Lazy
import Othello.PackedNat6 as Packed
import Tests.CompletionBatchLowerA6.Rows33154.Part33154 as Original
import Tests.CompletionBatchLowerA6.Rows33154.Family as Family
import Tests.CompletionBatchLowerA6.Rows33154.BodyData33154 as Body
import Tests.FullInitialLower6.StateData33154 as Own
import Tests.SparseCitationFixed6.Rows33154.Part33154 as Sparse
'''
    initial=ref.initial(6)
    raw_initial=('b' if initial.turn==ref.BLACK else 'w')+''.join(map(str,initial.cells))
    data=common+'''codes : B.Vec ℕ 200
codes = '''+''.join(f'(B.cons {n} ' for n in codes)+'B.nil'+')'*200+'''
states : B.Vec (State six) 200
states = Packed.states codes
abstract
  same : states ≡ Lazy.states 200 Own.text
  same = refl
  initial-correct : Packed.decode '''+str(code(raw_initial))+''' ≡ initial six
  initial-correct = refl
'''
    baseline=common+'''abstract
  accepted : Family.L.Lower.checkRows (M.lookup Sparse.demand) Original.embed
    (Lazy.states 200 Own.text) Body.bodies ≡ true
  accepted = refl
'''
    variant=common+f'''import {PREFIX}.Data as Data
import Tests.DirectRowsProbeFixed6.Link as Link
abstract
  accepted : Family.L.Lower.checkRows (M.lookup Sparse.demand) Original.embed Data.states Body.bodies ≡ true
  accepted = refl
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned Original.demand G → Laws.Aligned Original.states G →
    Laws.Aligned Original.bodies C → Family.A.Partial G C Original.states
  linked G C sameDemand sameStates sameBodies =
    Link.linked {{n = 200}} 6630800 Sparse.demand Data.states (Lazy.states 200 Own.text)
      Body.bodies Body.bodies Data.same refl accepted G C
      (Sparse.aligned G sameDemand) sameStates sameBodies
'''
    for name,body in [('Data',data),('Baseline',baseline),('Variant',variant)]:
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted untrusted numeric representation; original checker semantics.\nmodule '+PREFIX+'.'+name+' where\n\n'+body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-packed-nat6-sources-v1',created_utc=utc(),
        packed_source=str(original),packed_source_sha256=hashlib.sha256(raw).hexdigest(),
        numeric_codes_are_untrusted_data=True,numeric_serialization='Python exact integers emitted as decimal Agda literals; no floating point conversion.',
        positions=200,source_part=33154,new_distinct_rows=0,
        obligations=['initial-state equality','200-row state-vector equality','original Boolean row checker','original conditional Partial linkage'],
        mathematical_objective_complete=False))
    return source_identity(check)
