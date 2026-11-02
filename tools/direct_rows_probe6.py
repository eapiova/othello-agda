"""AI-assisted untrusted constructor literals, with checked codec equalities.

No solver is run. The same checker and the accepted sparse resolver are used.
Literal equality, Boolean row checking, and symbolic linkage are obligations.
"""
import json
from pathlib import Path

from compact_shared6 import COUNTS, unpack_state
from provenance import source_identity
from wire_workflow6 import require

PART = 33154
BASE = PART*200
FIXED = Path('results/sparse-citation-pilot6-20261018-fixed')
OLD = 'Tests.CompletionBatchLowerA6.Rows33154'
SPARSE = 'Tests.SparseCitationFixed6.Rows33154'
HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
COMMON = '''open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Othello.Board using (State; six; state; empty; blackCell; whiteCell; black; white)
import Othello.Finite as F
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.LazyIndexed6 as Lazy
'''


def vec(items, cons, nil):
    return ''.join('('+cons+' '+x+' ' for x in items)+nil+')'*len(items)


def state_literal(packed):
    raw=unpack_state(packed)
    cells=[['empty','blackCell','whiteCell'][int(c)] for c in raw[1:]]
    rows=[vec(cells[i:i+6],'F._∷_','F.[]') for i in range(0,36,6)]
    return '(state '+vec(rows,'F._∷_','F.[]')+' '+('black' if raw[0]=='b' else 'white')+')'


def bodies(text, count):
    offset=0
    def number():
        nonlocal offset
        end=text.index(';',offset)
        raw=text[offset:end]
        require(1<=len(raw)<=5,'bounded complete numeric key required')
        result=0
        for digit in raw:
            require(digit in COUNTS,'base37 digit required')
            result=result*37+COUNTS.index(digit)
        require(result<20000000,'numeric key bound')
        offset=end+1
        return result
    def node(depth=0):
        nonlocal offset
        require(depth<128 and offset<len(text),'bounded complete certificate required')
        tag=text[offset];offset+=1
        if tag=='L':return 'I.indexedLeaf'
        if tag=='K':return '(I.cite '+str(number())+')'
        if tag=='P':return '(I.indexedPass '+node(depth+1)+')'
        require(tag in 'RCF' and offset<len(text) and text[offset] in COUNTS,'known certificate token required')
        n=COUNTS.index(text[offset]);offset+=1
        if tag=='R':
            require(n<=7,'D4 tag bound')
            return f'(I.citeBy {n} {number()})'
        if tag=='C':
            require(n<=35,'move index bound')
            return f'(I.indexedChoice {n} '+node(depth+1)+')'
        require(n<=36,'fork width bound')
        return '(I.indexedFork '+vec([node(depth+1) for _ in range(n)],'_∷_','[]')+')'
    result=[node() for _ in range(count)]
    require(offset==len(text),'exactly all certificate text must be consumed')
    return result


def emit(check, prefix):
    check=Path(check)
    root=Path(__file__).resolve().parents[1]
    accepted=json.loads((root/FIXED/'report.json').read_text())
    scope=json.loads((root/FIXED/'semantic-scope-audit.json').read_text())
    require(scope['accepted'] and accepted['record']['accepted']
            and scope['unchecked_unused_modules']==['Tests.SparseCitationFixed6.Rows33154.Family'],
            'audited sparse semantic join must be accepted first')
    sample=json.loads((root/'results/completion-batch-lower-a6-20261018/sample.json').read_text())
    case=next(c for c in sample['cases'] if c['part']==PART)
    require(case['rows']==200 and len(case['state_text'])==2600,'full200-row case required')
    texts=[case['state_text'][13*i:13*i+13] for i in range(200)]
    constructor_states=vec([state_literal(t) for t in texts],'B.cons','B.nil')
    constructor_bodies=vec(bodies(case['body_text'],200),'B.cons','B.nil')
    imports=COMMON+f'''import {OLD}.Part33154 as Original
import {OLD}.Family as Family
import {OLD}.BodyData33154 as Body
import Tests.FullInitialLower6.StateData33154 as Own
import {SPARSE}.Part33154 as Sparse
module V = Family.L.Lower.V
'''
    sources={}
    sources['States']=COMMON+'''import Tests.FullInitialLower6.StateData33154 as Own
rows : B.Vec (State six) 200
rows = '''+constructor_states+'''
abstract
  same : rows ≡ Lazy.states 200 Own.text
  same = refl
'''
    sources['Bodies']=COMMON+f'''import {OLD}.BodyData33154 as Body
rows : B.Vec (I.IndexedCertificate ℕ) 200
rows = {constructor_bodies}
abstract
  same : rows ≡ Body.bodies
  same = refl
'''
    sources['Baseline']=imports+'''abstract
  accepted : Family.L.checkPart (M.lookup Sparse.demand) Original.embed Own.text Body.text ≡ true
  accepted = refl
'''
    sources['Link']=COMMON+f'''import {OLD}.Family as Family
module V = Family.L.Lower.V
abstract
  linked : ∀ {{n}} base (demand : M.Map (State six))
    (ss oldSS : B.Vec (State six) n) (cs oldCS : B.Vec (I.IndexedCertificate ℕ) n) →
    ss ≡ oldSS → cs ≡ oldCS →
    Family.L.Lower.checkRows (M.lookup demand) (λ i → base + B.finToNat i) ss cs ≡ true →
    (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned demand G → Laws.Aligned (M.rows base n oldSS) G →
    Laws.Aligned (M.rows base n oldCS) C → Family.A.Partial G C (M.rows base n oldSS)
  linked {{n}} base demand ss oldSS cs oldCS ssEqual csEqual accepted G C sameDemand sameStates sameBodies =
    Family.A.rows base oldSS G C row
    where
    resolver : I.Resolver ℕ (State six)
    resolver = M.lookup demand
    embed : B.Fin n → ℕ
    embed = λ i → base + B.finToNat i
    compatible : V.Compatible resolver G
    compatible = Laws.aligned-compatible {{map = demand}} {{G = G}} sameDemand
    stateExact : (i : B.Fin n) → G (embed i) ≡ B.lookupVec ss i
    stateExact i = trans (sameStates i) (cong (λ xs → B.lookupVec xs i) (sym ssEqual))
    bodyExact : (i : B.Fin n) → C (embed i) ≡ B.lookupVec cs i
    bodyExact i = trans (sameBodies i) (cong (λ xs → B.lookupVec xs i) (sym csEqual))
    row : (i : B.Fin n) → V.TreeOK G (embed i) (G (embed i)) (C (embed i))
    row i =
      subst (λ s → V.TreeOK G (embed i) s (C (embed i))) (sym (stateExact i))
        (subst (λ c → V.TreeOK G (embed i) (B.lookupVec ss i) c) (sym (bodyExact i))
          (V.lift-local {{L = resolver}} {{G = G}} compatible
            (V.checkLocal-sound resolver (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
              (Family.L.Lower.checkRows-row resolver embed ss cs accepted i))))
'''
    sources['Rows']=imports+f'''import {prefix}.States as S
import {prefix}.Bodies as D
import {prefix}.Link as Link
abstract
  accepted : Family.L.Lower.checkRows (M.lookup Sparse.demand) Original.embed S.rows D.rows ≡ true
  accepted = refl
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned Original.demand G → Laws.Aligned Original.states G →
    Laws.Aligned Original.bodies C → Family.A.Partial G C Original.states
  linked G C sameDemand sameStates sameBodies =
    Link.linked {{n = 200}} {BASE} Sparse.demand S.rows (Lazy.states 200 Own.text)
      D.rows Body.bodies S.same D.same accepted G C
      (Sparse.aligned G sameDemand) sameStates sameBodies
'''
    folder=check/'src'/prefix.replace('.','/')
    require(not check.exists(),'fresh private root required')
    folder.mkdir(parents=True)
    for name,body in sources.items():
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted, untrusted literals checked against accepted codecs.\nmodule '+prefix+'.'+name+' where\n\n'+body)
    (check/'othello.agda-lib').write_bytes((root/'othello.agda-lib').read_bytes())
    return source_identity(check)
