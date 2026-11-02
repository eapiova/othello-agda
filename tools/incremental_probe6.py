"""AI-assisted untrusted move fixtures for an incremental-update measurement.

Python generates expected data only. Safe Agda checks both exact ordered
successor lists, after checking the arbitrary-board agreement theorem.
"""
import hashlib
import json
from pathlib import Path
import time

import bench6
import compact_shared6 as compact
import completion_batch6 as prior
import ref
from provenance import source_identity
from run_job import atomic_json,utc
from wire_workflow6 import require

HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
PREFIX='Tests.IncrementalProbe6'


def emit(check):
    start=time.process_time()
    check=Path(check);require(not check.exists(),'fresh incremental probe required')
    sample=json.loads((prior.OUT/'sample.json').read_text())
    case=next(c for c in sample['cases'] if c['part']==33154)
    require(case['rows']==200,'exact200-position baseline required')
    expected=[]
    for i in range(200):
        packed=case['state_text'][13*i:13*(i+1)]
        state=bench6.decode(compact.unpack_state(packed))
        children=ref.successors(state)
        require(len(children)<=36,'bounded successor count required')
        expected.append((len(children),''.join(compact.pack_state(c) for c in children)))
    folder=check/'src/Tests/IncrementalProbe6';folder.mkdir(parents=True)
    proof=prior.ROOT/'src/Othello/Incremental6.agda'
    raw=proof.read_bytes()
    require(all(flag.encode() in raw.splitlines()[0] for flag in ['--safe','--without-K','--cubical-compatible']),
            'safe proof source required')
    destination=check/'src/Othello/Incremental6.agda';destination.parent.mkdir(parents=True);destination.write_bytes(raw)
    common='''open import Prelude
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.Composite as C
import Othello.Encode6 as E
import Othello.LazyIndexed6 as Lazy
'''
    body=common+'''import Tests.FullInitialLower6.StateData33154 as Own
toList : ∀ {A : Set} {n} → B.Vec A n → List A
toList B.nil = []
toList (B.cons x xs) = x ∷ toList xs

equalLists : List (State six) → List (State six) → Bool
equalLists [] [] = true
equalLists [] (_ ∷ _) = false
equalLists (_ ∷ _) [] = false
equalLists (s ∷ ss) (t ∷ ts) = C.equal E.stateEquality6 s t ∧ equalLists ss ts

bench : ∀ {n} → (State six → List (State six)) → B.Vec (State six) n →
  B.Vec (List (State six)) n → Bool
bench f B.nil B.nil = true
bench f (B.cons s ss) (B.cons expected rest) = equalLists (f s) expected ∧ bench f ss rest

states : B.Vec (State six) 200
states = Lazy.states 200 Own.text
expected : B.Vec (List (State six)) 200
expected = '''+''.join(f'(B.cons (toList (Lazy.states {n} "{text}")) ' for n,text in expected)+'B.nil'+')'*200+'\n'
    (folder/'Fixture.agda').write_text(HEADER+'-- AI-assisted untrusted successor data.\nmodule '+PREFIX+'.Fixture where\n\n'+body)
    for name,module,function in [('Baseline','Othello.Fast6','fastSuccessors'),('Variant','Othello.Incremental6','successors')]:
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted exact ordered-successor comparison.\nmodule '+PREFIX+'.'+name+' where\n\n'+common+f'''import {PREFIX}.Fixture as F
import {module} as Moves
abstract
  accepted : F.bench Moves.{function} F.states F.expected ≡ true
  accepted = refl
''')
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'fixture-provenance.json',dict(format='othello-incremental-rule6-fixture-v1',
        created_utc=utc(),positions=200,successor_states=sum(n for n,_ in expected),
        source_part=33154,untrusted_data_only=True,native_solver_executed=False,
        original_incremental_source=str(proof),incremental_source_sha256=hashlib.sha256(raw).hexdigest(),
        preparation_cpu_seconds=time.process_time()-start,mathematical_objective_complete=False))
    return source_identity(check)
