#!/usr/bin/env python3
"""Untrusted deterministic 6x6 fixtures and compact certificate data generation."""
from __future__ import annotations
import argparse, hashlib, json, random, time
from pathlib import Path
import ref, generate

ROOT=Path(__file__).resolve().parents[1]
LINE='d3 c5 d6 e3 f5 f4 e2 d2 c2 e6 e7 g5 c4 c3 g4 g3 f3 c7 b5 d7 b7 b3 c6 b6 f7 f6 b4 b2 g6 g7 f2 g2'.split()
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'

def encode_state(s):
    assert s.size==6 and len(s.cells)==36 and s.turn in (ref.BLACK,ref.WHITE)
    return ('b' if s.turn==ref.BLACK else 'w')+''.join(map(str,s.cells))

def encode_local(node):
    kind=node['kind']
    if kind=='leaf': return 'L'
    if kind=='solve': return f"S{node['fuel']};"
    if kind=='choice': return f"C{node['index']};"+encode_local(node['child'])
    if kind=='pass': return 'P'+encode_local(node['child'])
    if kind=='fork': return f"F{len(node['children'])};"+''.join(map(encode_local,node['children']))
    raise ValueError('unknown local certificate')

def replay():
    states=[ref.initial(6)]; indices=[]; events=[]
    for move in LINE:
        s=states[-1]; moves=ref.placements(s)
        if not moves:
            children=ref.successors(s)
            if len(children)!=1: raise ValueError('premature terminal')
            events.append({'move':'pass','turn':s.turn,'index':0}); indices.append(0); states.append(children[0]);s=states[-1];moves=ref.placements(s)
        q=(int(move[1])-2,ord(move[0])-ord('b'))
        i=next((i for i,(p,_) in enumerate(moves) if p==q),None)
        if i is None: raise ValueError(f'illegal {move}')
        events.append({'move':move,'turn':s.turn,'index':i}); indices.append(i); states.append(moves[i][1])
    last=states[-1]
    assert not ref.successors(last) and last.cells.count(ref.BLACK)==16 and last.cells.count(ref.WHITE)==20
    assert len(indices)==33 and events[30]['move']=='pass' and events[30]['turn']==ref.BLACK
    return states,indices,events

def emit_line():
    states,indices,events=replay()
    out=[HEADER+'-- Generated fixtures, each transition independently checked.\nmodule Tests.PerfectLine6 where\n\n',
         'open import Prelude\nopen import Game.Core using (lookup)\nopen import Othello.Board\nopen import Othello.Rules using (successors; forcedPass)\nopen import Othello.Encode6 using (decodeState)\n\n']
    for i,s in enumerate(states): out.append(f'p{i} : State six\np{i} = fromMaybe (initial six) (decodeState "{encode_state(s)}")\n\n')
    out.append('start-correct : p0 ≡ initial six\nstart-correct = refl\n\n')
    for i,index in enumerate(indices):out.append(f'edge{i} : lookup (successors p{i}) {index} ≡ just p{i+1}\nedge{i} = refl\n\n')
    out.append('data LegalLine : State six → List ℕ → State six → Set where\n  finish : ∀ {s} → LegalLine s [] s\n  step : ∀ {s i is t u} → lookup (successors s) i ≡ just t → LegalLine t is u → LegalLine s (i ∷ is) u\n\n')
    nums=' ∷ '.join(map(str,indices))+' ∷ []'
    out.append(f'moveIndices : List ℕ\nmoveIndices = {nums}\n\nlegal-line : LegalLine p0 moveIndices p33\nlegal-line = ')
    out.append(''.join(f'step {{t = p{i+1}}} edge{i} (' for i in range(33))+'finish'+')'*33+'\n\n')
    out.append('path : List (State six)\npath = '+' ∷ '.join(f'p{i}' for i in range(1,34))+' ∷ []\n\n')
    out.append('black-pass : forcedPass p30 ≡ true\nblack-pass = refl\n\nblack-sixteen : discs black p33 ≡ 16\nblack-sixteen = refl\n\nwhite-twenty : discs white p33 ≡ 20\nwhite-twenty = refl\n\nno-empty : empties p33 ≡ 0\nno-empty = refl\n\nline-terminal : successors p33 ≡ []\nline-terminal = refl\n')
    target=ROOT/'src/Tests/PerfectLine6.agda';target.write_text(''.join(out))
    data={'format':'othello-line6-v1','scoring':'white-minus-black','events':events,'states':[encode_state(s) for s in states],
          'plies':33,'placements':32,'terminal':{'black':16,'white':20,'empty':0},'trust':'legal line only; global optimality not asserted'}
    dest=ROOT/'certificates/six-line.json';dest.write_text(json.dumps(data,indent=2)+'\n')
    return {'line_module':str(target.relative_to(ROOT)),'module_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'plies':33}

def samples(count=30,seed=20261005):
    rng=random.Random(seed); buckets={e:{} for e in (8,10,12)}; late={}; games=0
    while any(len(v)<count for v in buckets.values()) or len(late)<1000:
        s=generate.from_scalar(ref.initial(6)); games+=1
        while True:
            scalar=generate.scalar(s); e=scalar.cells.count(ref.EMPTY); key=encode_state(scalar)
            if e in buckets and len(buckets[e])<count:buckets[e].setdefault(key,scalar)
            if e<=10 and len(late)<1000:late.setdefault(key,scalar)
            cs=generate.successors(s)
            if not cs:break
            s=rng.choice(cs)
        if games>10000:raise ValueError('sample generation failed')
    # Every emitted state gets an independent rule comparison, without solving it.
    for s in list(late.values())+[s for group in buckets.values() for s in group.values()]:
        assert ref.successors(s)==tuple(generate.scalar(t) for t in generate.successors(generate.from_scalar(s)))
    document={'format':'othello-six-samples-v1','seed':seed,'games':games,'kernel':{str(e):list(group) for e,group in buckets.items()},'late':list(late)}
    path=ROOT/'certificates/six-samples.json';path.write_text(json.dumps(document,indent=2)+'\n')
    return {'samples':str(path.relative_to(ROOT)),'kernel_count':sum(map(len,buckets.values())),'late_count':len(late),'games':games}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('fixtures','line'));args=p.parse_args()
    result=emit_line()
    if args.command=='fixtures':result.update(samples())
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
