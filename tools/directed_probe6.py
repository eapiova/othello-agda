"""Untrusted action conversion; safe Agda checks legality, ownership and citations."""
import hashlib
import json
from pathlib import Path

import bench6
import compact_shared6 as compact
import completion_batch6 as prior
import direct_rows_probe6 as literal
import ref
from provenance import source_identity
from run_job import atomic_json, utc


def converted(text, states, text_output=False):
    offset=0;counts=dict(choices=0,directed_choices=0,leaves=0,citations=0,forks=0,passes=0,solve=0)
    def fin(n):return 'F.zero' if n==0 else '(F.suc '+fin(n-1)+')'
    def encode_id(n):
        digits=''
        while n:
            n,d=divmod(n,37);digits=compact.COUNTS[d]+digits
        return (digits or '0')+';'
    def number(base=37):
        nonlocal offset
        end=text.index(';',offset);raw=text[offset:end];offset=end+1
        assert 1<=len(raw)<=8
        return int(raw) if base==10 else sum(compact.COUNTS.index(c)*37**i for i,c in enumerate(reversed(raw)))
    def node(s,depth=0):
        nonlocal offset
        assert depth<128
        tag=text[offset];offset+=1
        if tag=='L':counts['leaves']+=1;return 'L' if text_output else 'D.indexedLeaf'
        if tag=='K':
            counts['citations']+=1;i=number()
            return 'K'+encode_id(i) if text_output else f'(D.cite {i})'
        if tag=='S':
            counts['solve']+=1;n=number(10)
            return 'S'+str(n)+';' if text_output else f'(D.indexedSolve {n})'
        if tag=='P':
            counts['passes']+=1
            child=node(ref.State(6,s.cells,3-s.turn),depth+1)
            return 'P'+child if text_output else '(D.indexedPass '+child+')'
        assert tag in 'RCF'
        n=compact.COUNTS.index(text[offset]);offset+=1
        if tag=='R':
            counts['citations']+=1;assert n<=7;i=number()
            return 'R'+compact.COUNTS[n]+encode_id(i) if text_output else f'(D.citeBy {n} {i})'
        placements=ref.placements(s)
        children=tuple(t for _,t in placements) or ref.successors(s)
        if tag=='C':
            counts['choices']+=1;assert n<len(children)
            child=node(children[n],depth+1)
            if placements:
                counts['directed_choices']+=1;r,c=placements[n][0]
                if text_output:return 'Q'+compact.COUNTS[6*r+c]+child
                return f'(D.indexedPick ({fin(r)} , {fin(c)}) {child})'
            if text_output:return 'C'+compact.COUNTS[n]+child
            return f'(D.indexedChoice {n} {child})'
        counts['forks']+=1;assert n==len(children)
        nodes=[node(t,depth+1) for t in children]
        return 'F'+compact.COUNTS[n]+''.join(nodes) if text_output else '(D.indexedFork '+literal.vec(nodes,'_∷_','[]')+')'
    result=[node(s) for s in states]
    assert offset==len(text)
    return result,counts


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    pins={}
    for rel in ['Game/DirectedIndexed.agda','Othello/DirectMoves6.agda','Othello/DirectedRows6.agda']:
        source=prior.ROOT/'src'/rel;raw=source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe','--without-K','--cubical-compatible'])
        target=check/'src'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pins[str(source)]=hashlib.sha256(raw).hexdigest()
    case=next(c for c in json.loads((prior.OUT/'sample.json').read_text())['cases'] if c['part']==33154)
    states=[bench6.decode(compact.unpack_state(case['state_text'][13*i:13*i+13])) for i in range(200)]
    directed,counts=converted(case['body_text'],states)
    common='''open import Prelude
open import Othello.Board using (State; Coord; six)
import Othello.Finite as F
import Game.Balanced as B
import Game.Indexed as I
import Game.DirectedIndexed as D
import Game.NatMap as M
import Othello.LazyIndexed6 as Lazy
import Tests.FullInitialLower6.StateData33154 as Own
import Tests.CompletionBatchLowerA6.Rows33154.BodyData33154 as Body
import Tests.CompletionBatchLowerA6.Rows33154.Part33154 as Original
import Tests.SparseCitationFixed6.Rows33154.Part33154 as Sparse
'''
    data=common+'''oldBodies : B.Vec (I.IndexedCertificate ℕ) 200
oldBodies = '''+literal.vec(literal.bodies(case['body_text'],200),'B.cons','B.nil')+'''
newBodies : B.Vec (D.DirectedCertificate ℕ (Coord six)) 200
newBodies = '''+literal.vec(directed,'B.cons','B.nil')+'''
abstract
  exactOldBodies : oldBodies ≡ Body.bodies
  exactOldBodies = refl
'''
    settings='''open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.DirectedRows6 as Rows
import Tests.DirectedProbe6.Data as Data
module Check = Rows.Checking white (lowerGoal 4) lowerTransport6
ss : B.Vec (State six) 200
ss = Lazy.states 200 Own.text
'''
    folder=check/'src/Tests/DirectedProbe6';folder.mkdir(parents=True)
    sources=[('Data',data)]
    for name,bodies,v,method in [('Baseline','oldBodies','Check.Old.V','Check.ordinary-linked'),('Variant','newBodies','Check.V','Check.linked')]:
        sources.append((name,common+settings+f'''abstract
  linked : (G : ℕ → State six) → {v}.Compatible (M.lookup Sparse.demand) G → ∀ i →
    {v}.TreeOK G (Original.embed i) (B.lookupVec ss i) (B.lookupVec Data.{bodies} i)
  linked = {method} (M.lookup Sparse.demand) Original.embed ss Data.{bodies} refl
'''))
    for name,body in sources:
        (folder/(name+'.agda')).write_text(literal.HEADER+'-- AI-assisted; existing 200 states, untrusted converted actions.\nmodule Tests.DirectedProbe6.'+name+' where\n\n'+body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-directed6-sources-v1',created_utc=utc(),copied_core_sha256=pins,source_part=33154,existing_rows=200,new_distinct_rows=0,conversion_counts=counts,native_solver_executed=False,untrusted_conversion=True,mathematical_objective_complete=False))
    return source_identity(check)
