"""Untrusted row-code data; safe matching and semantic row soundness are required."""
import hashlib
import json
from pathlib import Path

import bench6
import compact_shared6 as compact
import completion_batch6 as prior
from direct_rows_probe6 import HEADER
from provenance import source_identity
from run_job import atomic_json,utc
from sparse_citation_pilot6 import tree


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    pins={}
    for rel in ['Othello/RowPacked6.agda','Game/EncodedResolver.agda','Othello/RowPackedIndexed6.agda','Game/MappedTransfer.agda']:
        source=prior.ROOT/'src'/rel;raw=source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe','--without-K','--cubical-compatible'])
        target=check/'src'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pins[str(source)]=hashlib.sha256(raw).hexdigest()
    sample=json.loads((prior.OUT/'sample.json').read_text());case=next(c for c in sample['cases'] if c['part']==33154)
    keys=sorted(set(case['references']))
    common='''open import Prelude
open import Othello.Board using (State; six; black; white)
import Othello.Finite as F
import Game.Balanced as B
import Game.NatMap as M
import Othello.RowPacked6 as Packed
import Othello.LazyIndexed6 as Lazy
'''
    data=common
    literals={}
    for key in keys:
        chunk=sample['states'][str(key//200)];packed=chunk['text'][13*(key%200):13*(key%200+1)]
        s=bench6.decode(compact.unpack_state(packed))
        codes=[sum(s.cells[6*r+c]*3**c for c in range(6)) for r in range(6)]
        data+=f's{key} : Packed.PackedState\ns{key} = Packed.packed ('+' F.∷ '.join([*map(str,codes),'F.[]'])+') '+('black' if s.turn==1 else 'white')+'\n'
        literals[key]=packed
    expression=tree(keys,lambda k:f'(M.rows {k} 1 (B.cons s{k} B.nil))',lambda pivot,l,r:f'(M.branch {pivot} {l} {r})')
    data+='demand : M.Map Packed.PackedState\ndemand = '+expression+'\n'
    # Each supplied code is checked against its same-key accepted compact input.
    data+='''pairs : List (State six × Packed.PackedState)
pairs = '''+' ∷ '.join([f'((B.lookupVec (Lazy.states 1 "{literals[k]}") B.fzero) , s{k})' for k in keys]+['[]'])+'''
allMatch : List (State six × Packed.PackedState) → Bool
allMatch [] = true
allMatch ((s , t) ∷ pairs) = Packed.matches s t ∧ allMatch pairs
abstract
  everyCodeMatches : allMatch pairs ≡ true
  everyCodeMatches = refl
'''
    previous=prior.ROOT/'results/direct-symmetry-probe6-20261018/check/src/Tests/DirectSymmetryProbe6/Variant.agda'
    baseline=previous.read_text().replace('module Tests.DirectSymmetryProbe6.Variant where','module Tests.RowPackedProbe6.Baseline where')
    variant=baseline.replace('Tests.RowPackedProbe6.Baseline','Tests.RowPackedProbe6.Variant')
    variant=variant.replace('import Othello.DirectedRows6 as Rows','import Othello.RowPackedIndexed6 as Rows\nimport Othello.RowPacked6 as Packed\nimport Tests.RowPackedProbe6.RefData as Refs')
    variant=variant.replace('(G : ℕ → State six) → Check.V.Compatible (M.lookup Sparse.demand) G →', '(G : ℕ → Packed.PackedState) → Check.V.Compatible (M.lookup Refs.demand) G →')
    variant=variant.replace('Check.V.TreeOK G','Check.V.Old.TreeOK (λ j → Packed.decode (G j))')
    variant=variant.replace('Check.linked (M.lookup Sparse.demand)','Check.linked (M.lookup Refs.demand)')
    folder=check/'src/Tests/RowPackedProbe6';folder.mkdir(parents=True)
    for name,body in [('RefData',HEADER+'-- AI-assisted untrusted codes, checked against the exact old inputs.\nmodule Tests.RowPackedProbe6.RefData where\n'+data),('Baseline',baseline),('Variant',variant)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-row-packed6-sources-v1',created_utc=utc(),copied_core_sha256=pins,existing_rows=200,new_distinct_rows=0,unique_cited_codes=len(keys),row_cases=729,native_solver_executed=False,working_state_remains_original_board=True,all_codes_require_checked_matching=True,mathematical_objective_complete=False))
    return source_identity(check)
