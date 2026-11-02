#!/usr/bin/env python3
"""Scalar closure, differential counters and fail-closed sampling checks."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import canonical_census6
import census_samples6
import test_canonical_census6 as scalar
import ref
import solve6
from run_job import atomic_json, utc

COUNTERS=('root_validated','root_holds','complete','tree_nodes_S','unique_dag_nodes','frontier_distinct_L','hint_occurrences_H','dag_edges','dedup_hits','count_overflow','states')

def argv(binary,case,command='frontier',cap=50000):
    turn='white' if case['turn']==ref.WHITE else 'black'
    result=[str(binary),command,'--position',case['position'],'--turn',turn,'--direction',case['direction'],'--threshold',str(case['threshold']),'--frontier-discs','36','--max-states','10000','--max-nodes','10000000','--max-memory-mb','16','--max-cpu-seconds','2','--tt-bits','4','--small','4','--deep-order','5','--emit-states','0' if command=='sample' else '1']
    if command=='sample':result+=['--sample-cap',str(cap),'--sample-count','8']
    return result

def invoke(command):
    done=subprocess.run(command,capture_output=True,text=True,timeout=10)
    assert done.returncode==0,done.stderr
    assert len(done.stdout.encode())<=census_samples6.MAX_OUTPUT
    return json.loads(done.stdout),len(done.stdout.encode())

def independently_count(sample):
    rows={ref.State(6,tuple(map(int,r['position'])),ref.BLACK if r['turn']=='black' else ref.WHITE):r for r in sample['states']}
    root=scalar.canonical(ref.State(6,tuple(map(int,sample['root_position'])),ref.BLACK if sample['root_turn']=='black' else ref.WHITE))
    active=set();memo={}
    def count(state):
        state=scalar.canonical(state)
        if state in memo:return memo[state]
        assert state not in active;active.add(state)
        row=rows[state];children=ref.successors(state)
        own=state.turn==(ref.WHITE if sample['direction']=='lower' else ref.BLACK)
        if own and ref.placements(state):children=[children[row['selected_index']]]
        total=1+sum(count(child) for child in children)
        active.remove(state);memo[state]=total;return total
    assert count(root)==sample['tree_nodes_S'];assert len(memo)==sample['unique_dag_nodes']==len(rows)

def ideal_compact_statistics(native,case):
    """Independent C-representative formatter for the layered compact wire.

    State literals use 13 characters; only lengths are relevant here. Symbols
    match the compact constructor widths, including identity R and D4 R0.
    """
    rows={ref.State(6,tuple(map(int,r['position'])),ref.BLACK if r['turn']=='black' else ref.WHITE):r for r in native['states']}
    indegree={s:0 for s in rows};edges=[];kind={}
    for state,row in rows.items():
        children=ref.successors(state)
        placements=ref.placements(state)
        own=state.turn==(ref.WHITE if case['direction']=='lower' else ref.BLACK)
        kind[state]='L' if row['leaf'] else 'P' if not placements else 'C' if own else 'F'
        if row['leaf']:children=[]
        elif own and placements:children=[children[row['selected_index']]]
        for child in children:
            canonical=scalar.canonical(child);indegree[canonical]+=1
            edges.append((state,canonical,child!=canonical))
    shared={s for s in rows if kind[s]!='L' and indegree[s]>=2}
    root=scalar.canonical(ref.State(6,tuple(map(int,case['position'])),case['turn']))
    fragments=['0'*13 for _ in range(len(shared)+1)]
    tokens=0
    for state in rows:
        if kind[state]!='L':fragments.append(kind[state]+('0' if kind[state] in ('C','F') else ''));tokens+=1
    leaves=1 if kind[root]=='L' else 0
    for _,child,transform in edges:
        if kind[child]=='L':leaves+=1
        elif child in shared:fragments.append('R0' if transform else 'R');tokens+=1
    fragments+=['L']*leaves;tokens+=leaves
    return tokens,len(''.join(fragments)),leaves,sum(c in shared and t for _,c,t in edges),indegree


def run(args):
    built,binary=census_samples6.checked_build(args.build)
    _,reference=canonical_census6.checked_build(args.reference_build)
    scalar_output=args.output.with_name(args.output.stem+'-scalar.json')
    scalar.run(SimpleNamespace(build=args.build,output=scalar_output,reference_build=None),build_validator=census_samples6.checked_build)
    scalar_report=json.loads(scalar_output.read_text());cases=scalar_report['late_cases']
    comparisons=samples_checked=0;pass_samples=0;false_cases=0;tiny_rejections=0
    for case in cases:
        native,_=invoke(argv(binary,case));baseline,_=invoke(argv(reference,case))
        for key in COUNTERS:assert native[key]==baseline[key],key
        comparisons+=1
        sampled,size=invoke(argv(binary,case,'sample'))
        for key in COUNTERS:
            if key!='states':assert sampled[key]==native[key],key
        if not case['holds']:
            assert not sampled['complete'] and sampled['samples']==[];false_cases+=1;continue
        assert sampled['sampling_complete']
        stats=sampled['statistics'];assert sum(stats['node_kinds'].values())==native['unique_dag_nodes']
        assert sum(stats['disc_histogram'])==native['unique_dag_nodes'];assert stats['chosen_edges']==native['dag_edges']
        tokens,ascii_bytes,leaves,citations,degrees=ideal_compact_statistics(native,case)
        assert stats['ideal_grammar_tokens']==tokens
        assert stats['ideal_grammar_ascii_bytes']==ascii_bytes
        assert stats['leaf_occurrences']==leaves
        assert stats['nonidentity_D4_citation_edges']==citations
        assert sampled['sample_json_bytes']<=size<=census_samples6.MAX_OUTPUT
        for sample in sampled['samples']:
            assert sample['complete'] and sample['root_holds'] and sample['root_validated']
            assert all(type(r['global_indegree']) is int and r['global_indegree'] >= 0 for r in sample['states'])
            for row in sample['states']:
                s=ref.State(6,tuple(map(int,row['position'])),ref.BLACK if row['turn']=='black' else ref.WHITE)
                assert row['global_indegree']==degrees[s]
            root=ref.State(6,tuple(map(int,sample['root_position'])),ref.BLACK if sample['root_turn']=='black' else ref.WHITE)
            scalar.replay(sample,root,case['direction'],case['threshold']);independently_count(sample);samples_checked+=1
            pass_samples+=sum(not r['leaf'] and not ref.placements(ref.State(6,tuple(map(int,r['position'])),ref.BLACK if r['turn']=='black' else ref.WHITE)) for r in sample['states'])
        tiny,_=invoke(argv(binary,case,'sample',1))
        for sample in tiny['samples']:
            assert sample['unique_dag_nodes']==1
            root=ref.State(6,tuple(map(int,sample['root_position'])),ref.BLACK if sample['root_turn']=='black' else ref.WHITE)
            scalar.replay(sample,root,case['direction'],case['threshold']);independently_count(sample)
        tiny_rejections+=tiny['sample_too_large']
    # Explicit reachable-by-rules forced-pass fixture, independent of random walks.
    state=ref.State(6,tuple(map(int,'210222'+'2'*30)),ref.BLACK)
    assert not ref.placements(state) and ref.successors(state)
    ref.value.cache_clear();value=ref.value(state)
    for direction in ('lower','upper'):
        case=dict(position=''.join(map(str,state.cells)),turn=state.turn,direction=direction,threshold=value)
        sampled,_=invoke(argv(binary,case,'sample'))
        assert sampled['samples']
        for sample in sampled['samples']:
            root=ref.State(6,tuple(map(int,sample['root_position'])),ref.BLACK if sample['root_turn']=='black' else ref.WHITE)
            scalar.replay(sample,root,direction,value);independently_count(sample)
        assert sampled['statistics']['node_kinds']['pass']>=1;pass_samples+=1
    invalid=[['sample','--sample-cap','0'],['sample','--sample-cap','50001'],['sample','--sample-count','9'],['sample','--sample-cap'],['sample','--emit-states','1'],['sample','--max-states','160000001'],['sample','--position','x'*36],['sample','--max-memory-mb','1','--max-states','100000'],['sample','--max-states','1','--max-nodes','1','--max-cpu-seconds','1','--tt-bits','4']]
    for options in invalid:
        done=subprocess.run([str(binary),*options],capture_output=True,text=True,timeout=10)
        if done.stdout.startswith('{'):
            payload=json.loads(done.stdout);assert not payload['complete'];assert payload.get('samples',[])==[]
        else:assert done.returncode!=0
    assert comparisons==72 and false_cases and samples_checked and tiny_rejections and pass_samples
    assert census_samples6.checked_build(args.build)[0]==built
    report=dict(format='othello-census-samples6-tests-v1',accepted=True,created_utc=utc(),build_sha256=solve6.sha256(args.build/'build.json'),reference_build_sha256=solve6.sha256(args.reference_build/'build.json'),scalar_tests_sha256=solve6.sha256(scalar_output),exact_reference_graph_comparisons=comparisons,complete_sample_closures_replayed=samples_checked,forced_pass_rows=pass_samples,false_bound_cases=false_cases,tiny_cap_rejected_attempts=tiny_rejections,invalid_or_fuel_cases=len(invalid),production_authorized=False,trust='untrusted native differential tests; no Agda proof premise')
    atomic_json(args.output,report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--reference-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);run(p.parse_args())
