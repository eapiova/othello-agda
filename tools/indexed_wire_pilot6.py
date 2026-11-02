#!/usr/bin/env python3
"""Independent typed-ID parts and symbolic assembly of an accepted descendant.

This is a capped feasibility pilot, not initial-board production. Native wire
data is untrusted; Agda checks every row, reference guard and global assembly.
Accepted semantic legacy parts are preserved rather than modified or repeated.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import assembly6
from cache_resume6 import copy_interface
import compact_shared6 as compact
import data_only_pilot6 as data_only
import indexed_spike6 as spike
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_identity
from run_job import atomic_json, run_job, utc
from unattended_wire6 import closed_record
from wire_workflow6 import require

PREFIX='Tests.IndexedWire6'
COUNTS='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_'


def embedding(path, variable='i'):
    term='B.row '+variable
    for bit in reversed(path): term=('B.left' if bit=='a' else 'B.right')+' ('+term+')'
    return term


def skeleton(sizes):
    nodes=[];paths={}
    def make(lo,hi,path):
        number=len(nodes);node=dict(number=number,lo=lo,hi=hi,path=path)
        nodes.append(node)
        if hi-lo==1:
            node['leaf']=lo;paths[lo]=path;node['size']=sizes[lo]
        else:
            mid=(lo+hi)//2
            node['left']=make(lo,mid,path+'a');node['right']=make(mid,hi,path+'b')
        return node
    root=make(0,len(sizes),'')
    return root,nodes,paths


def encode_id(part,row,paths):
    require(0<=row<200,'local index cap')
    return paths[part]+COUNTS[row//37]+COUNTS[row%37]


def indexed_body(body,refs,addresses,paths):
    out=[];r=0;i=0
    while i<len(body):
        token=body[i];i+=1
        if token in 'KR':
            out.append(token)
            if token=='R':
                require(i<len(body) and body[i] in '01234567','invalid native tag')
                out.append(body[i]);i+=1
            require(r<len(refs) and refs[r] in addresses,'unresolved native citation')
            part,row=addresses[refs[r]];r+=1
            out.append(encode_id(part,row,paths))
        elif token in 'LP': out.append(token)
        elif token in 'CF':
            require(i<len(body) and body[i] in COUNTS,'invalid bounded token')
            out.extend((token,body[i]));i+=1
        elif token=='S':
            end=body.index(';',i)
            require(body[i:end].isdigit(),'invalid solve token')
            out.append(body[i-1:end+1]);i=end+1
        else: raise ValueError('invalid native body token')
    require(r==len(refs),'extra native references')
    return ''.join(out)


def generate(check,wire_path):
    wire_path=Path(wire_path)
    parts,owners=data_only.read_partition(wire_path)
    raw=wire_path.read_bytes()
    require(len(parts)==267 and sum(map(len,parts))==53217,'complete accepted descendant required')
    root,nodes,paths=skeleton(list(map(len,parts)))
    addresses={compact.pack_state(e['state']):(j,k) for j,p in enumerate(parts) for k,e in enumerate(p)}
    require(len(addresses)==53217,'duplicate row states')
    native={}
    for line in raw.decode('ascii').splitlines():
        key,body,reftext=line.split('\t')
        require(len(reftext)%13==0,'truncated reference column')
        require(key not in native,'duplicate native row')
        native[key]=(body,[reftext[k:k+13] for k in range(0,len(reftext),13)])
    require(set(native)==set(addresses),'wire/partition mismatch')
    sources={};targets=[];dependencies={}
    common=spike.COMMON.replace(spike.PREFIX,PREFIX)
    common='\n'.join(l for l in common.splitlines() if not l.startswith('module Upper ='))+'\n'
    def emit(name,text):
        sources['src/'+PREFIX.replace('.','/')+'/'+name+'.agda']=spike.HEADER+'module '+PREFIX+'.'+name+' where\n\n'+text
    shape='open import Prelude\nimport Game.Balanced as B\n'
    for node in reversed(nodes):
        ident='shape'+str(node['number'])
        value=('B.leaf '+str(node['size']) if 'leaf' in node else
               'B.branch shape'+str(node['left']['number'])+' shape'+str(node['right']['number']))
        shape+=f'{ident} : B.Shape\n{ident} = {value}\n'
    shape+='shape : B.Shape\nshape = shape0\n'
    emit('Shape',shape)
    def view(node,deps):
        if not any(node['lo']<=d<node['hi'] for d in deps):return 'View.absent'
        if 'leaf' in node:return '(View.present (View.allStates S'+str(node['leaf'])+'.states))'
        return '(View.branches '+view(node['left'],deps)+' '+view(node['right'],deps)+')'
    def compatible(node,deps):
        if not any(node['lo']<=d<node['hi'] for d in deps):return 'tt'
        if 'leaf' in node:
            d=node['leaf'];embed=embedding(paths[d])
            return f'(View.present-compatible S{d}.states (λ {{ (B.row i) → G ({embed}) }}) (λ i → refl))'
        return '('+compatible(node['left'],deps)+' , '+compatible(node['right'],deps)+')'
    for j,entries in enumerate(parts):
        n=len(entries);dep=sorted({j}|{owners[r] for e in entries for r in e['references']})
        require(all(d<=j for d in dep),'forward part dependency')
        dependencies[j]=dep
        stateText=''.join(compact.pack_state(e['state']) for e in entries)
        bodyText=''.join(indexed_body(*native[compact.pack_state(e['state'])],addresses,paths) for e in entries)
        emit('StateData'+str(j),f'''open import Prelude
open import Agda.Builtin.String using (String)
import Game.Balanced as B
import Othello.Indexed6 as D
open import Othello.Board using (State; six)
text : String
text = "{stateText}"
states : B.Vec (State six) {n}
states = D.states {n} text
''')
        emit('BodyData'+str(j),f'''open import Prelude
open import Agda.Builtin.String using (String)
import Game.Balanced as B
import Game.Indexed as I
import Othello.Indexed6 as D
import {PREFIX}.Shape as Shape
text : String
text = "{bodyText}"
bodies : B.Vec (I.IndexedCertificate (B.Id Shape.shape)) {n}
bodies = D.bodies Shape.shape {n} text
''')
        imports=''.join(f'import {PREFIX}.StateData{d} as S{d}\n' for d in dep)
        imports+=f'import {PREFIX}.BodyData{j} as Body\n'
        require('.Part' not in imports,'local check imports earlier proofs')
        embed=embedding(paths[j])
        emit('Part'+str(j),common+imports+f'''
embed : B.Fin {n} → B.Id Shape.shape
embed = λ i → {embed}
localView : View.View (State six) Shape.shape
localView = {view(root,dep)}
L : I.Resolver (B.Id Shape.shape) (State six)
L = View.resolve localView
abstract
  accepted : Lower.checkPart L embed S{j}.text Body.text ≡ true
  accepted = refl

linked : (G : B.Id Shape.shape → State six) →
  (C : B.Id Shape.shape → I.IndexedCertificate (B.Id Shape.shape)) →
  Lower.V.Compatible L G →
  (∀ i → G (embed i) ≡ B.lookupVec S{j}.states i) →
  (∀ i → C (embed i) ≡ B.lookupVec Body.bodies i) →
  ∀ i → Lower.V.TreeOK G (embed i) (G (embed i)) (C (embed i))
linked G C compatible sameState sameBody =
  Lower.linkPart L embed S{j}.text Body.text accepted G C compatible sameState sameBody
''')
        targets.append('Part'+str(j))
    for kind,element,field,mod in [('StateTree','State six','states','StateData'),
                                 ('BodyTree','I.IndexedCertificate (B.Id Shape.shape)','bodies','BodyData')]:
        text=common+''.join(f'import {PREFIX}.{mod}{j} as D{j}\n' for j in range(len(parts)))
        for node in reversed(nodes):
            num=node['number']
            value=('B.rows D'+str(node['leaf'])+'.'+field if 'leaf' in node else
                   f'B.join tree{node["left"]["number"]} tree{node["right"]["number"]}')
            text+=f'tree{num} : B.Tree ({element}) Shape.shape{num}\ntree{num} = {value}\n'
        text+=f'tree : B.Tree ({element}) Shape.shape\ntree = tree0\n'
        emit(kind,text)
    text=common+f'import {PREFIX}.StateTree as States\nimport {PREFIX}.BodyTree as Bodies\n'
    text+=''.join(f'import {PREFIX}.Part{j} as P{j}\nimport {PREFIX}.StateData{j} as S{j}\n' for j in range(len(parts)))
    text+='''
G : B.Id Shape.shape → State six
G = B.lookup States.tree
C : B.Id Shape.shape → I.IndexedCertificate (B.Id Shape.shape)
C = B.lookup Bodies.tree
'''
    for j in range(len(parts)):
        text+=f'compatible{j} : Lower.V.Compatible P{j}.L G\ncompatible{j} = View.compatible {compatible(root,dependencies[j])}\n'
    text+='rows : ∀ i → Lower.V.TreeOK G i (G i) (C i)\n'
    for j in range(len(parts)):
        text+=f'rows ({embedding(paths[j])}) = P{j}.linked G C compatible{j} (λ k → refl) (λ k → refl) i\n'
    j,k=addresses[compact.pack_state(parts[-1][-1]['state'])]
    fin='B.fzero'
    for _ in range(k):fin='B.fsuc ('+fin+')'
    ident=embedding(paths[j], '('+fin+')')
    packed=compact.pack_state(parts[-1][-1]['state'])
    text+=f'''
root : B.Id Shape.shape
root = {ident}
open import Othello.CompactShared6 using (decodeCompactState)
position : State six
position = fromMaybe (initial six) (decodeCompactState "{packed}")
lowerRoot : Proven Fast.fastGame6 white (lowerGoal 4) position
lowerRoot = Lower.V.global-proven G C rows root
open import Game.Soundness using (checkSound)
open import Game.Transfer using (guarantees-transfer)
open import Othello.Proof6 using (fastAgreement)
import Othello.Rules as Rules
originalLower : Guarantees (Rules.game six) white (lowerGoal 4) position
originalLower = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement
  (checkSound Fast.fastGame6 white (lowerGoal 4) position (proj₁ lowerRoot) (proj₂ lowerRoot))
'''
    emit('Assemble',text);targets.append('Assemble')
    hashes={}
    for name,source in sources.items():
        p=check/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
        hashes[name]=hashlib.sha256(source.encode()).hexdigest()
    return dict(rows=53217,parts=267,targets=targets,generated_sha256=hashes,
                total_generated_bytes=sum(len(v.encode()) for v in sources.values()),
                child_proof_imports=False,initial_problem2_proved=False,optimal_initial_pair_proved=False)


def run(args):
    current=Path.cwd().resolve();out=args.output.resolve()
    require(not out.exists() and 'results' in out.parts,'fresh isolated output required');out.mkdir(parents=True)
    machine=assembly6.machine_identity(args.agda)
    require(machine['hostname']=='eapiova' and machine['agda_sha256']==args.expected_agda_sha256,'pinned compiler required')
    historical=args.wire_root.resolve();completed=args.completed_root.resolve();donor=args.donor.resolve()
    sourcesBefore={str(p):source_identity(p) for p in (historical,completed,donor)}
    require(sourcesBefore[str(historical)]['source_sha256']==args.expected_wire_source_sha256,'wire source differs')
    final=json.loads((completed/'results/wire-resume6/report.json').read_text())
    closed_record(json.loads((completed/'results/wire-cut-ply10-resume-20261009.json').read_text()),args.expected_completed_source_sha256)
    require(final['accepted'] and final['completed_targets']==268,'legacy proof not complete')
    donorBefore=assembly6.interfaces(donor)
    generic={n:h for n,h in donorBefore.items() if '/src/Tests/' not in n}
    require(len(generic)==31 and digest_entries(generic)==args.expected_generic_interfaces_sha256,'donor pool differs')
    for name in data_only.borrowed_sources(generic):
        require((current/name).read_bytes()==(donor/name).read_bytes(),'borrowed source differs: '+name)
    wire_path=historical/'results/wire-advance6/lower-ply10.wire'
    raw=wire_path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==args.expected_wire_sha256,'wire differs')
    report=dict(format='othello-indexed-wire-pilot6-v1',created_utc=utc(),status='preparing',accepted=False,
                phases=[],kernel_cpu_seconds=0.,machine=machine,initial_problem2_proved=False,
                optimal_initial_pair_proved=False,production_authorized=False,child_proof_imports=False,
                wire_sha256=args.expected_wire_sha256,borrowed_generic_interfaces_sha256=digest_entries(generic))
    def save():atomic_json(out/'report.json',report)
    def guard():
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used<10*2**30 and free>=100*2**30,'storage gate reached; accepted prefix preserved')
    save();guard();check=out/'check';check.mkdir()
    shutil.copytree(current/'src',check/'src',copy_function=shutil.copy2)
    shutil.copy2(current/'othello.agda-lib',check/'othello.agda-lib')
    for name in data_only.borrowed_sources(generic):
        shutil.copystat(donor/name,check/name)
    report['prepared']=generate(check,wire_path)
    require(report['prepared']['total_generated_bytes']<=16*2**20,'generated source cap reached')
    for name,digest in generic.items():copy_interface(donor/name,check/name,digest)
    source=source_identity(check);report['checked_source']=source;save()
    for j,target in enumerate(report['prepared']['targets']):
        guard();require(report['kernel_cpu_seconds']<args.kernel_cpu_limit,'kernel envelope reached')
        assembly=target=='Assemble'
        require(not any(n.endswith('/src/'+PREFIX.replace('.','/')+'/'+target+'.agdai')
                        for n in assembly6.interfaces(check)),'own target unexpectedly warm')
        flags=['--no-libraries','-i','src','--safe','--without-K','--cubical-compatible','--save-metas']
        command=[args.agda,*flags,f'src/{PREFIX.replace(".","/")}/{target}.agda',
                 '+RTS','-M2600M' if assembly else '-M1350M','-c','-s','-RTS']
        record=run_job('target'+str(j),command,out/'records',root=check,
                       timeout=2*args.part_cpu_limit+60,cpu_limit=min(args.part_cpu_limit,args.kernel_cpu_limit-report['kernel_cpu_seconds']),
                       rss_limit_gib=3 if assembly else 1.5,log_limit_mib=2,expected_source_sha256=source['source_sha256'],
                       metadata=dict(target=target,child_proof_imports=assembly,
                                     cache_policy='own target cold; same-source generic and prior data interfaces reused'))
        report['phases'].append(dict(target=target,record=record));report['kernel_cpu_seconds']+=record['cpu_seconds']
        report.update(status='checking-assembly' if assembly else 'checking-independent-parts',accepted_parts=sum(p['record']['accepted'] for p in report['phases'] if p['target']!='Assemble'))
        cache=assembly6.interfaces(check)
        borrowedOK=all(cache.get(n)==h for n,h in generic.items())
        report['phases'][-1]['borrowed_generic_interfaces_unchanged']=borrowedOK
        report['last_interface_pool_sha256']=digest_entries(cache)
        atomic_json(out/'interface-map.json',cache)
        save();require(record['accepted'] and borrowedOK,'kernel target/cache failed: '+target)
    require(assembly6.interfaces(donor)==donorBefore and all(source_identity(Path(p))==v for p,v in sourcesBefore.items()),'historical evidence changed')
    report.update(status='complete',accepted=True,finished_utc=utc(),descendant_original_lower_checked=True)
    save();return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('wire-root','completed-root','donor','output'):p.add_argument('--'+arg,type=Path,required=True)
    for arg in ('agda','expected-agda-sha256','expected-wire-source-sha256','expected-completed-source-sha256',
                'expected-generic-interfaces-sha256','expected-wire-sha256'):p.add_argument('--'+arg,required=True)
    p.add_argument('--kernel-cpu-limit',type=float,default=3300.)
    p.add_argument('--part-cpu-limit',type=float,default=180.)
    r=run(p.parse_args());print(json.dumps(dict(accepted=r['accepted'],kernel_cpu_seconds=r['kernel_cpu_seconds'],initial_problem2_proved=False)))


if __name__=='__main__':main()
