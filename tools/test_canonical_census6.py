#!/usr/bin/env python3
"""Independent scalar tests for the experimental canonical native census."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import subprocess

from canonical_census6 import checked_build
import ref
from run_job import atomic_json, utc
import solve6


def image(cells, t):
    result = [0]*36
    for r in range(6):
        for c in range(6):
            y,x = (c,r) if t&4 else (r,c)
            if t&2: y=5-y
            if t&1: x=5-x
            result[y*6+x] = cells[r*6+c]
    return tuple(result)


def canonical(state):
    own = state.turn
    def key(cells):
        p=sum(1<<((i//6+1)*8+i%6+1) for i,c in enumerate(cells) if c==own)
        o=sum(1<<((i//6+1)*8+i%6+1) for i,c in enumerate(cells) if c not in (0,own))
        return p,o
    return ref.State(6,min((image(state.cells,t) for t in range(8)),key=key),state.turn)


def replay(native, root, direction, threshold):
    rows = {ref.State(6,tuple(map(int,p['position'])),ref.BLACK if p['turn']=='black' else ref.WHITE):p
            for p in native['states']}
    if len(rows)!=len(native['states']): raise AssertionError('duplicate canonical state')
    visited, active = set(), set()
    def check(s):
        s=canonical(s)
        if s in visited: return
        if s in active: raise AssertionError('cyclic graph')
        active.add(s);row=rows[s];children=ref.successors(s)
        if row['leaf']:
            assert not children
            assert ref.score(s)>=threshold if direction=='lower' else ref.score(s)<=threshold
        else:
            assert children
            own = s.turn == (ref.WHITE if direction=='lower' else ref.BLACK)
            if own and ref.placements(s):
                index=row['selected_index'];assert 0<=index<len(children);check(children[index])
            else:
                for child in children: check(child)
        active.remove(s);visited.add(s)
    check(root)
    assert len(visited)==len(rows)


def run(args, build_validator=checked_build):
    built,binary=build_validator(args.build.resolve())
    reference = None
    reference_build = getattr(args, 'reference_build', None)
    if reference_build is not None:
        reference_report, reference = checked_build(reference_build.resolve())
        assert not reference_report.get('compact_memo', False)
        assert reference_report['witness_policy'] == built['witness_policy']
    states=[ref.State(6,tuple(1 if i==j else 0 for i in range(36)),ref.BLACK) for j in range(36)]
    states += [ref.State(6,tuple(2 if i==j else 0 for i in range(36)),ref.BLACK) for j in range(36)]
    states += [ref.State(6,tuple(map(int,'210222'+'2'*30)),ref.BLACK)]
    late=[];rng=random.Random(2026100801)
    for _ in range(12):
        state=ref.initial(6)
        for ply in range(80):
            if ply%4==0: states.append(state._replace(turn=ref.BLACK))
            children=ref.successors(state)
            if not children: break
            if state.cells.count(0)<=4:
                late.append(state);break
            state=rng.choice(children)
    for state in states:
        position=''.join(map(str,state.cells))
        result=json.loads(subprocess.check_output([str(binary),'canonical',position],text=True))
        expected=[image(state.cells,t) for t in range(8)]
        assert [p['position'] for p in result['orbit']]==[''.join(map(str,c)) for c in expected]
        assert result['canonical']==''.join(map(str,canonical(state).cells))
        for row,cells in zip(result['orbit'],expected):
            scalar=ref.State(6,cells,ref.BLACK)
            assert row['children']==[''.join(map(str,c.cells)) for c in ref.successors(scalar)]
    cases=[]
    for state in late:
        ref.value.cache_clear();value=ref.value(state)
        for direction in ('lower','upper'):
            for threshold in (value-1,value,value+1):
                argv=[str(binary),'frontier','--position',''.join(map(str,state.cells)),
                    '--turn','white' if state.turn==ref.WHITE else 'black',
                    '--direction',direction,'--threshold',str(threshold),
                    '--frontier-discs','36','--max-states','10000','--max-nodes','10000000',
                    '--max-memory-mb','16','--max-cpu-seconds','2','--tt-bits','4',
                    '--small','4','--deep-order','5','--emit-states','1']
                done=subprocess.run(argv,capture_output=True,text=True,timeout=10)
                assert done.returncode==0,done.stderr
                native=json.loads(done.stdout)
                if reference is not None:
                    comparison = subprocess.run([str(reference), *argv[1:]],
                                                capture_output=True, text=True, timeout=10)
                    assert comparison.returncode == 0, comparison.stderr
                    baseline = json.loads(comparison.stdout)
                    for key in ('root_validated', 'root_holds', 'complete', 'tree_nodes_S',
                                'unique_dag_nodes', 'frontier_distinct_L', 'hint_occurrences_H',
                                'dag_edges', 'dedup_hits', 'count_overflow', 'states'):
                        assert native[key] == baseline[key], key
                holds=value>=threshold if direction=='lower' else value<=threshold
                assert native['root_validated'] and native['root_holds']==holds
                if holds:
                    assert native['complete'];replay(native,state,direction,threshold)
                cases.append(dict(direction=direction,threshold=threshold,holds=holds,
                    nodes=native['unique_dag_nodes'],position=''.join(map(str,state.cells)),
                    turn=state.turn,scalar_value=value))
    assert len(late)==12 and len(cases)==72
    assert build_validator(args.build.resolve())[0]==built
    report=dict(format='othello-canonical-census6-tests-v1',accepted=True,created_utc=utc(),
        seed=2026100801,build_sha256=solve6.sha256(args.build/'build.json'),
        tested_positions=len(states),tested_images=8*len(states),late_cases=cases,
        coverage='72 basis boards, reachable boards, forced pass, all D4 moves/flips; 72 scalar threshold/graph replays',
        compact_memo=built.get('compact_memo', False),
        reference_build_sha256=(solve6.sha256(reference_build/'build.json')
                                if reference_build is not None else None),
        exact_reference_graph_comparisons=len(cases) if reference is not None else 0,
        trust='untrusted differential testing; no Agda proof premise',production_authorized=False)
    atomic_json(args.output,report)
    print(json.dumps({k:report[k] for k in ('accepted','tested_positions','tested_images')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference-build',type=Path)
    run(parser.parse_args())
