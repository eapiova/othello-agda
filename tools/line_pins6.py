#!/usr/bin/env python3
"""Untrusted canonical move pins for the explicit 16–20 line.

This validates legality and D4 transport only. A future native exporter must
check the bound at every pinned choice and fail closed rather than fall back.
The final Agda skeleton must keep its on-line branches explicit.
"""
import argparse
import json
from pathlib import Path

from census_pilot6 import ccanonical, state
from generate6 import encode_state
import ref
from run_job import atomic_json


def image(s, tag):
    cells=[0]*36
    for r in range(6):
        for c in range(6):
            y,x=(c,r) if tag&4 else (r,c)
            if tag&2: y=5-y
            if tag&1: x=5-x
            cells[y*6+x]=s.cells[r*6+c]
    return ref.State(6,tuple(cells),s.turn)


def plan(document):
    raw=document.get('states'); events=document.get('events')
    if document.get('format')!='othello-line6-v1' or type(raw) is not list or type(events) is not list:
        raise ValueError('wrong line format')
    if len(raw)!=34 or len(events)!=33:
        raise ValueError('requires the complete 33-ply line')
    positions=[state(k[1:],{'b':'black','w':'white'}.get(k[:1])) for k in raw]
    if positions[0]!=ref.initial(6): raise ValueError('wrong initial board')
    pins=dict(lower=[],upper=[])
    for i,(s,t,e) in enumerate(zip(positions,positions[1:],events)):
        children=ref.successors(s); index=e.get('index')
        if (type(index) is not int or not 0<=index<len(children) or children[index]!=t or
                e.get('turn')!=s.turn): raise ValueError('illegal event or index')
        placements=ref.placements(s)
        if not placements:
            if e.get('move')!='pass' or len(children)!=1: raise ValueError('invalid forced pass')
            continue
        q=placements[index][0]
        if e.get('move')!=chr(ord('b')+q[1])+str(q[0]+2): raise ValueError('move label disagrees with index')
        representative=ccanonical(s)
        tag=next(tag for tag in range(8) if image(s,tag)==representative)
        chosen=image(t,tag)
        canonical_index=ref.successors(representative).index(chosen)
        direction='lower' if s.turn==ref.WHITE else 'upper'
        pins[direction].append(dict(ply=i,state=encode_state(representative),
            selected_index=canonical_index,chosen_state=encode_state(chosen),
            canonical_child=encode_state(ccanonical(t))))
    terminal=positions[-1]
    if (ref.successors(terminal) or terminal.cells.count(ref.BLACK)!=16 or
            terminal.cells.count(ref.WHITE)!=20 or terminal.cells.count(ref.EMPTY)!=0):
        raise ValueError('wrong terminal outcome')
    for rows in pins.values():
        if len({row['state'] for row in rows})!=len(rows): raise ValueError('conflicting repeated pin')
    return dict(format='othello-canonical-line-pins6-v1',pins=pins,states=raw,events=events,
        raw_value=4,terminal=dict(black=16,white=20,empty=0),
        bound_validation_required=True,optimality_proved=False,initial_problem2_proved=False,
        scope='legal D4-equivalent line pins; not bound or Agda evidence',
        exporter_requirements=['reject a pinned choice if its bound fails',
            'preserve the canonical child at every own line position',
            'retain on-line skeleton branches explicitly through terminal',
            'kernel-check the actual pair of strategies with jointCheck'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--line',type=Path,default=Path('certificates/six-line.json'))
    p.add_argument('--output',type=Path,required=True); args=p.parse_args()
    report=plan(json.loads(args.line.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True); atomic_json(args.output,report)
    print(json.dumps(dict(pins={k:len(v) for k,v in report['pins'].items()},optimality_proved=False)))


if __name__=='__main__': main()
