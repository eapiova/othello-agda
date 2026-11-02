#!/usr/bin/env python3
"""Generate bounded numeric-ID row proofs and symbolic hierarchical assembly.

Only safe Agda can supply an acceptance. This generator is restricted to
feasibility layouts of at most 512 parts; full initial production is excluded.
"""
from pathlib import Path
import hashlib

from indexed_wire_pilot6 import skeleton
from indexed_tree_assembly6 import frontier, project
from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require

DATA = '''open import Prelude
open import Agda.Builtin.String using (String)
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.Indexed as I
import Othello.NatIndexed6 as D
open import Othello.Board using (State; six)
'''


def generate(check: Path, *, sizes, dependencies, body_texts, root_packed,
             state_prefix, prefix='Tests.NatTree6', cut_depth=4, side='lower'):
    require(side in ('lower','upper') and 0<=cut_depth<=12, 'bounded direction required')
    require(0<len(sizes)<=512 and all(0<n<=200 for n in sizes), 'feasibility size cap reached')
    require(len(body_texts)==len(sizes) and set(dependencies)==set(range(len(sizes))), 'incomplete data')
    dependencies={j:set(ds)|{j} for j,ds in dependencies.items()}
    require(all(all(0<=d<len(sizes) for d in ds) for ds in dependencies.values()), 'dependency outside map')
    root,nodes,paths=skeleton(sizes);sources={};targets=[]
    player,goal,transport=('white','lowerGoal','lowerTransport6') if side=='lower' else ('black','upperGoal','upperTransport6')
    def emit(name,body):
        relative='src/'+prefix.replace('.','/')+'/'+name+'.agda'
        sources[relative]=HEADER+'-- AI-assisted untrusted generator; safe Agda checks every proof.\nmodule '+prefix+'.'+name+' where\n\n'+body
    def imports(ds,bodies=()):
        return ''.join(f'import {state_prefix}.StateData{j} as S{j}\n' for j in sorted(ds))+''.join(
            f'import {prefix}.BodyData{j} as C{j}\n' for j in sorted(bodies))
    def pivot(n):return n['right']['lo']*200
    def sparse(n,ds,field='states'):
        if not any(n['lo']<=j<n['hi'] for j in ds):return 'M.absent'
        if 'leaf' in n:
            j=n['leaf'];source='S' if field=='states' else 'C'
            return f'(M.rows {200*j} {sizes[j]} {source}{j}.{field})'
        return f'(M.branch {pivot(n)} {sparse(n["left"],ds,field)} {sparse(n["right"],ds,field)})'
    def included(n,small,large):
        if not any(n['lo']<=j<n['hi'] for j in small):return 'Laws.empty'
        require(small<=large,'non-included demand')
        if 'leaf' in n:return 'Laws.same'
        return f'(Laws.fork {included(n["left"],small,large)} {included(n["right"],small,large)})'
    def route(n,j):
        if 'leaf' in n:return 'Laws.here'
        if j<n['left']['hi']:
            bound=f'(Laws.at-most {200*j+sizes[j]} {pivot(n)} refl)'
            return f'(Laws.left {bound} {route(n["left"],j)})'
        bound=f'(Laws.at-most {pivot(n)} {200*j} refl)'
        return f'(Laws.right {bound} {route(n["right"],j)})'
    emit('Family',DATA+f'''open import Game.Core using (white; black)
open import Othello.Statements using (lowerGoal; upperGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6; upperTransport6)
import Othello.Fast6 as Fast
import Othello.NatAssembly6 as Assembly
module A = Assembly.Assembly Fast.fastGame6 {player} ({goal} 4) {transport}
''')
    targets.append('Family')
    for j,n in enumerate(sizes):
        emit('BodyData'+str(j),DATA+f'\ntext : String\ntext = "{body_texts[j]}"\nbodies : B.Vec (I.IndexedCertificate ℕ) {n}\nbodies = D.bodies {n} text\n')
        emit('PartData'+str(j),DATA+imports(dependencies[j],[j])+f'''
demand : M.Map (State six)
demand = {sparse(root,dependencies[j])}
states : M.Map (State six)
states = M.rows {200*j} {n} S{j}.states
bodies : M.Map (I.IndexedCertificate ℕ)
bodies = M.rows {200*j} {n} C{j}.bodies
''')
        emit('Part'+str(j),DATA+f'import {prefix}.Family as Family\nimport {prefix}.PartData{j} as Data\n'+
            imports([j],[j])+f'''open import Agda.Builtin.Nat using (_+_)
embed : B.Fin {n} → ℕ
embed i = {200*j} + B.finToNat i
abstract
  accepted : Family.A.Lower.checkPart (M.lookup Data.demand) embed S{j}.text C{j}.text ≡ true
  accepted = refl
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned Data.demand G → Laws.Aligned Data.states G → Laws.Aligned Data.bodies C →
    Family.A.Partial G C Data.states
  linked = Family.A.linkedAligned {{n = {n}}} {200*j} Data.demand S{j}.text C{j}.text accepted
''')
        targets.append('Part'+str(j))
    groups={n['number'] for n in frontier(root,cut_depth)};used=[]
    def visit(n):
        if n['number'] not in groups:visit(n['left']);visit(n['right'])
        used.append(n)
    visit(root)
    unions={n['number']:set().union(*(dependencies[j] for j in range(n['lo'],n['hi']))) for n in used}
    for n in used:
        num=n['number'];group=num in groups;ds=unions[num];own=set(range(n['lo'],n['hi']))
        data=DATA+imports(ds,own if group else [])
        if not group:data+=f'import {prefix}.Data{n["left"]["number"]} as Left\nimport {prefix}.Data{n["right"]["number"]} as Right\n'
        states=sparse(n,own);bodies=sparse(n,own,'bodies')
        if not group:
            states=f'M.branch {pivot(n)} Left.states Right.states'
            bodies=f'M.branch {pivot(n)} Left.bodies Right.bodies'
        data+=f'''\ndemand : M.Map (State six)
demand = {sparse(root,ds)}
states : M.Map (State six)
states = {states}
bodies : M.Map (I.IndexedCertificate ℕ)
bodies = {bodies}
'''
        for label,small,smallterm in (
            [(str(j),dependencies[j],f'P{j}.demand') for j in range(n['lo'],n['hi'])] if group else
            [('Left',unions[n['left']['number']],'Left.demand'),('Right',unions[n['right']['number']],'Right.demand')]):
            if group:data+=f'import {prefix}.PartData{label} as P{label}\n'
            data+=f'included{label} : Laws.Included {smallterm} demand\nincluded{label} = {included(root,small,ds)}\n'
        emit('Data'+str(num),data)
        proof=DATA+f'import {prefix}.Family as Family\nimport {prefix}.Data{num} as Data\n'
        if group:proof+=''.join(f'import {prefix}.Part{j} as P{j}\n' for j in range(n['lo'],n['hi']))
        else:proof+=f'import {prefix}.Node{n["left"]["number"]} as Left\nimport {prefix}.Node{n["right"]["number"]} as Right\n'
        proof+='''abstract
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned Data.demand G → Laws.Aligned Data.states G → Laws.Aligned Data.bodies C →
    Family.A.Partial G C Data.states
  linked G C demand states bodies =
'''
        def partial(node,path):
            if 'leaf' in node:
                j=node['leaf'];s=project(path,'states');c=project(path,'bodies')
                return f'(P{j}.linked G C (Laws.aligned-restrict {{G = G}} Data.included{j} demand) ({s}) ({c}))'
            return f'(Family.A.join {{G = G}} {{C = C}} {pivot(node)} {partial(node["left"],path+"a")} {partial(node["right"],path+"b")})'
        if group:proof+='    '+partial(n,'')+'\n'
        else:proof+=f'''    Family.A.join {{G = G}} {{C = C}} {pivot(n)}
      (Left.linked G C (Laws.aligned-restrict {{G = G}} Data.includedLeft demand) (proj₁ states) (proj₁ bodies))
      (Right.linked G C (Laws.aligned-restrict {{G = G}} Data.includedRight demand) (proj₂ states) (proj₂ bodies))
'''
        emit('Node'+str(num),proof);targets.append('Node'+str(num))
    def aligned(n,G,default):
        if 'leaf' in n:
            j=n['leaf'];mapname='Data.states' if G=='G' else 'Data.bodies'
            return f'(Laws.route-aligned {{map = {mapname}}} {{base = {200*j}}} {{n = {sizes[j]}}} {G} {route(root,j)} (Laws.self-compatible {mapname} {default}))'
        return '('+aligned(n['left'],G,default)+' , '+aligned(n['right'],G,default)+')'
    def paired(n):
        if 'leaf' in n:return 'Laws.rows-pair'
        return f'(Laws.fork-pair {paired(n["left"])} {paired(n["right"])})'
    terminal='wQQQQQQQQQQQQ' if side=='lower' else 'bDDDDDDDDDDDD'
    final=DATA+f'''import {prefix}.Family as Family
import {prefix}.Data0 as Data
import {prefix}.Node0 as Node
open import Game.Core using (white; black; Guarantees; next)
open import Game.Symmetry using (Proven)
open import Game.Soundness using (checkSound)
open import Game.Transfer using (guarantees-transfer)
open import Othello.Board using (initial)
open import Othello.Statements using (lowerGoal; upperGoal)
open import Othello.CompactShared6 using (decodeCompactState)
open import Othello.Proof6 using (fastAgreement)
import Othello.Fast6 as Fast
import Othello.Rules as Rules
fallback : State six
fallback = fromMaybe (initial six) (decodeCompactState "{terminal}")
terminal : next Fast.fastGame6 fallback ≡ []
terminal = refl
won : {goal} 4 fallback ≡ true
won = refl
G : ℕ → State six
G = Laws.totalize Data.states fallback
C : ℕ → I.IndexedCertificate ℕ
C = Laws.totalize Data.bodies I.indexedLeaf
statesAligned : Laws.Aligned Data.states G
statesAligned = {aligned(root,'G','fallback')}
bodiesAligned : Laws.Aligned Data.bodies C
bodiesAligned = {aligned(root,'C','I.indexedLeaf')}
paired : Laws.Together Data.states Data.bodies
paired = {paired(root)}
abstract
  rows : ∀ key → Family.A.Lower.V.TreeOK G key (G key) (C key)
  rows = Family.A.complete Data.states Data.bodies paired fallback terminal won
    (Node.linked G C statesAligned statesAligned bodiesAligned)
  provenAt : ∀ key → Proven Fast.fastGame6 {player} ({goal} 4) (G key)
  provenAt = Family.A.Lower.V.global-proven G C rows
root : ℕ
root = {200*(len(sizes)-1)+sizes[-1]-1}
position : State six
position = fromMaybe (initial six) (decodeCompactState "{root_packed}")
rootState : G root ≡ position
rootState = refl
rootProof : Proven Fast.fastGame6 {player} ({goal} 4) position
rootProof = subst (Proven Fast.fastGame6 {player} ({goal} 4)) rootState (provenAt root)
original : Guarantees (Rules.game six) {player} ({goal} 4) position
original = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement
  (checkSound Fast.fastGame6 {player} ({goal} 4) position (proj₁ rootProof) (proj₂ rootProof))
'''
    emit('Root',final);targets.append('Root')
    for name,text in sources.items():
        path=check/name;require(not path.exists(),'refusing generated source overwrite');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    return dict(format='othello-nat-tree-layout6-v1',targets=targets,rows=sum(sizes),parts=len(sizes),
        hierarchy_nodes=len(used),generated_sha256={n:hashlib.sha256(t.encode()).hexdigest() for n,t in sources.items()},
        generated_bytes=sum(len(t.encode()) for t in sources.values()),initial_problem2_proved=False,
        optimal_initial_pair_proved=False,production_authorized=False,side=side)
