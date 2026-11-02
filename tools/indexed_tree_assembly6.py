#!/usr/bin/env python3
"""Generate symbolic balanced linking above independent indexed proof parts.

No Boolean acceptance or native result is turned into a premise here. Every
generated leaf calls a checked Part.linked; parents restrict alignment demands.
Concrete state and body maps appear only in the final root module.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

import indexed_spike6 as spike
import indexed_wire_pilot6 as wire
from wire_workflow6 import require


def embed_id(path, term='i'):
    for bit in reversed(path):
        term = ('B.left' if bit == 'a' else 'B.right')+' ('+term+')'
    return term


def project(path, term='proof'):
    for bit in path:
        term = ('proj₁' if bit == 'a' else 'proj₂')+' ('+term+')'
    return term


def frontier(root, depth):
    if depth == 0 or 'leaf' in root:
        return [root]
    return frontier(root['left'], depth-1)+frontier(root['right'], depth-1)


def generate(check: Path, *, sizes, dependencies, root_packed, base_prefix=wire.PREFIX,
             prefix='Tests.IndexedTree6', cut_depth=4, state_field='states', body_field='bodies',
             linked_field='linked', side='lower', local_warning_filter=False):
    """Dependency sets must reproduce the existing Part local resolvers exactly."""
    require(side in ('lower','upper') and sizes and 0 <= cut_depth <= 12, 'bounded direction/layout required')
    require(len(sizes) <= 512 and all(0 < n <= 200 for n in sizes), 'feasibility layout cap reached')
    require(set(dependencies) == set(range(len(sizes))), 'every part needs a dependency set')
    dependencies = {j:set(ds) for j,ds in dependencies.items()}
    require(all(all(0 <= k < len(sizes) for k in ds) for ds in dependencies.values()), 'dependency outside shape')
    root,nodes,paths = wire.skeleton(sizes)
    leaves = frontier(root, cut_depth)
    groups = {n['number'] for n in leaves}
    used=[]
    def visit(node):
        if node['number'] not in groups:
            visit(node['left']);visit(node['right'])
        used.append(node)
    visit(root)
    unions={}
    for node in used:
        unions[node['number']] = set(range(node['lo'],node['hi'])) | set().union(
            *(dependencies[j] for j in range(node['lo'],node['hi'])))
    common=spike.COMMON.replace(spike.PREFIX,base_prefix)
    common='\n'.join(l for l in common.splitlines() if not l.startswith('module Upper ='))+'\n'
    if side=='upper':
        common=common.replace('white (lowerGoal 4) lowerTransport6','black (upperGoal 4) upperTransport6')
    sources={};targets=[]
    header=spike.HEADER
    if local_warning_filter:
        header=header.replace('--cubical-compatible #-}', '--cubical-compatible -WnoUnsupportedIndexedMatch #-}',1)
    def emit(name,text):
        relative='src/'+prefix.replace('.','/')+'/'+name+'.agda'
        sources[relative]=header+'-- AI-assisted untrusted generator; Agda checks all linking.\nmodule '+prefix+'.'+name+' where\n\n'+text
    def demanded(node,deps):
        if not any(node['lo'] <= d < node['hi'] for d in deps):return 'Demand.absent'
        if 'leaf' in node:return '(Demand.need S'+str(node['leaf'])+'.'+state_field+')'
        return '(Demand.branches '+demanded(node['left'],deps)+' '+demanded(node['right'],deps)+')'
    def inclusion(node,small,large):
        if not any(node['lo'] <= d < node['hi'] for d in small):return 'Demand.empty'
        require(small <= large,'non-included demand')
        if 'leaf' in node:return 'Demand.same'
        return '(Demand.fork '+inclusion(node['left'],small,large)+' '+inclusion(node['right'],small,large)+')'
    layout='open import Prelude\nimport Game.Balanced as B\n'
    for node in reversed(nodes):
        value=('B.leaf '+str(node['size']) if 'leaf' in node else
               f'B.branch shape{node["left"]["number"]} shape{node["right"]["number"]}')
        layout+=f'shape{node["number"]} : B.Shape\nshape{node["number"]} = {value}\n'
    emit('Layout',layout)
    for node in used:
        num=node['number'];deps=unions[num];group=num in groups
        data=common+f'import {prefix}.Layout as Layout\nimport Game.BalancedDemand as Demand\n'
        data+=''.join(f'import {base_prefix}.StateData{j} as S{j}\n' for j in sorted(deps))
        if group:
            data+=''.join(f'import {base_prefix}.BodyData{j} as C{j}\n' for j in range(node['lo'],node['hi']))
        else:
            data+=f'import {prefix}.Data{node["left"]["number"]} as Left\nimport {prefix}.Data{node["right"]["number"]} as Right\n'
        data+=f'''
embed : B.Id Layout.shape{num} → B.Id Shape.shape
embed = λ i → {embed_id(node['path'])}
demand : Demand.Demand (State six) Shape.shape
demand = {demanded(root,deps)}
bodies : B.Tree (I.IndexedCertificate (B.Id Shape.shape)) Layout.shape{num}
'''
        if group:
            def bodies(n):
                if 'leaf' in n:return '(B.rows C'+str(n['leaf'])+'.'+body_field+')'
                return '(B.join '+bodies(n['left'])+' '+bodies(n['right'])+')'
            data+='bodies = '+bodies(node)+'\n'
            for j in range(node['lo'],node['hi']):
                data+=f'''
partDemand{j} : Demand.Demand (State six) Shape.shape
partDemand{j} = {demanded(root,dependencies[j])}
included{j} : Demand.Included partDemand{j} demand
included{j} = {inclusion(root,dependencies[j],deps)}
own{j} : ∀ {{G}} → Demand.Aligned demand G →
  ∀ i → G ({embed_id(paths[j], 'B.row i')}) ≡ B.lookupVec S{j}.{state_field} i
own{j} proof = {project(paths[j])}
'''
        else:
            data+='bodies = B.join Left.bodies Right.bodies\n'
            for label,child in [('Left',node['left']),('Right',node['right'])]:
                data+=f'''
included{label} : Demand.Included {label}.demand demand
included{label} = {inclusion(root,unions[child['number']],deps)}
'''
        emit('Data'+str(num),data)
        proof=common+f'import {prefix}.Layout as Layout\nimport Game.BalancedDemand as Demand\nimport {prefix}.Data{num} as Data\n'
        if group:
            proof+=''.join(f'import {base_prefix}.Part{j} as P{j}\n' for j in range(node['lo'],node['hi']))
        else:
            proof+=f'import {prefix}.Node{node["left"]["number"]} as Left\nimport {prefix}.Node{node["right"]["number"]} as Right\n'
        proof+=f'''
abstract
  linked : (G : B.Id Shape.shape → State six) →
    (C : B.Id Shape.shape → I.IndexedCertificate (B.Id Shape.shape)) →
    Demand.Aligned Data.demand G →
    (∀ i → C (Data.embed i) ≡ B.lookup Data.bodies i) →
    ∀ i → Lower.V.TreeOK G (Data.embed i) (G (Data.embed i)) (C (Data.embed i))
'''
        if group:
            for j in range(node['lo'],node['hi']):
                relative=paths[j][len(node['path']):]
                pat=embed_id(relative,'B.row i');arg=embed_id(relative,'B.row k')
                proof+=f'''  linked G C states bodies ({pat}) =
    P{j}.{linked_field} G C
      (View.compatible {{local = Demand.asView Data.partDemand{j}}} {{G = G}}
        (Demand.aligned-view {{d = Data.partDemand{j}}} {{G = G}}
          (Demand.restrict {{G = G}} Data.included{j} states)))
      (Data.own{j} {{G = G}} states) (λ k → bodies ({arg})) i
'''
        else:
            for label,constructor in [('Left','left'),('Right','right')]:
                proof+=f'''  linked G C states bodies (B.{constructor} i) =
    {label}.linked G C (Demand.restrict {{G = G}} Data.included{label} states)
      (λ k → bodies (B.{constructor} k)) i
'''
        emit('Node'+str(num),proof);targets.append('Node'+str(num))
    ident=embed_id(paths[len(sizes)-1], 'B.row ('+'B.fsuc ('*(sizes[-1]-1)+'B.fzero'+')'*(sizes[-1]-1)+')')
    player,goal=('white','lowerGoal') if side=='lower' else ('black','upperGoal')
    final=common+f'''import Game.BalancedDemand as Demand
import {prefix}.Data0 as Data
import {prefix}.Node0 as Node
open import Othello.CompactShared6 using (decodeCompactState)
open import Game.Soundness using (checkSound)
open import Game.Transfer using (guarantees-transfer)
open import Othello.Proof6 using (fastAgreement)
import Othello.Rules as Rules

G : B.Id Shape.shape → State six
G = B.lookup (Demand.totalize Data.demand (initial six))
C : B.Id Shape.shape → I.IndexedCertificate (B.Id Shape.shape)
C = B.lookup Data.bodies
abstract
  rows : ∀ i → Lower.V.TreeOK G i (G i) (C i)
  rows = Node.linked G C (Demand.self-aligned Data.demand (initial six)) (λ i → refl)
  provenAt : ∀ i → Proven Fast.fastGame6 {player} ({goal} 4) (G i)
  provenAt = Lower.V.global-proven G C rows
root : B.Id Shape.shape
root = {ident}
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
    hashes={}
    for name,text in sources.items():
        path=check/name;require(not path.exists(),'refusing generated source overwrite')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        hashes[name]=hashlib.sha256(text.encode()).hexdigest()
    return dict(format='othello-indexed-tree-layout6-v1',targets=targets,
        rows=sum(sizes),parts=len(sizes),group_count=len(leaves),proof_nodes=len(used),
        generated_sha256=hashes,generated_bytes=sum(len(t.encode()) for t in sources.values()),
        base_prefix=base_prefix,prefix=prefix,side=side,cut_depth=cut_depth,
        local_warning_filter='-WnoUnsupportedIndexedMatch' if local_warning_filter else None,
        child_proof_imports=True,initial_problem2_proved=False,optimal_initial_pair_proved=False)
