"""Counts-only initial layout using capped cost search and fail-closed line pins."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import threading
import os
import signal

import wire_layout6 as layout
import census_wire6 as wire
import canonical_census6 as base
import capped_cost_screen6 as cost
import shared_study6 as fixtures
import citation_diagnostic6 as resources
from run_job import atomic_json, utc

ROOT=Path(__file__).resolve().parents[1]
LINE=ROOT/'certificates/six-line.json'
DONOR=Path('/home/eapiova/projects/othello-agda/runs/six-native-lower20-resume-20261006')
WARM=DONOR/'results/native6/warm-2.tt'
WARM_SHA='7886f35fc835b64ad458e7ccb91475200bf44e4065e8d707d1a6ebcee61497d8'
HELPERS=['bounded_layout6.py','wire_layout6.py','wire_cuts6.py','census_wire6.py','canonical_census6.py','capped_cost_screen6.py','line_pins6.py','solve6.py','ref.py','generate6.py','census_pilot6.py','memo_reuse_screen6.py','endgame16_screen6.py','endgame_cost_screen6.py','run_job.py','study6.py','citation_diagnostic6.py']

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while b:=f.read(2**20):h.update(b)
    return h.hexdigest()

def generated(pins):
    original=layout.generated_source(wire.solve6.SOURCE.read_text(),pins)
    marker='static const struct {u64 key;int lower,index;} wire_pins[]='
    patches=[
        (marker,cost.HELPER+'\n'+marker),
        ('static u64 wire_pick(u64 P,u64 O,u64 moves,int own,int turn,int lower) {','static u64 wire_pick(u64 P,u64 O,u64 moves,int own,int turn,int lower,int threshold) {'),
        ('if(pin<0)return census_pick_move(P,O,moves,own);','if(pin<0)return cost_pick_move(P,O,moves,own,turn,lower,threshold);'),
        ('u64 m=wire_pick(P,O,moves,own,turn,lower);','u64 m=wire_pick(P,O,moves,own,turn,lower,threshold);'),
        ('    prefix_count=0; prefix_leaves=prefix_edges=prefix_repeats=0;','    free(cost_memo);cost_memo=NULL;\n    prefix_count=0; prefix_leaves=prefix_edges=prefix_repeats=0;')]
    for line in original.splitlines():
        if line.lstrip().startswith(('size_t bytes=ttn*sizeof(Bucket)','size_t requested=ttn*sizeof(Bucket)')):
            assert line.endswith(';')
            patches.append((line,line[:-1]+'+((size_t)1<<COST_BITS)*sizeof(CostEntry);'))
    assert len(patches)==7
    changed=original
    for a,b in patches:
        assert changed.count(a)==1,a[:80]
        changed=changed.replace(a,b,1)
    restored=changed
    for a,b in reversed(patches):restored=restored.replace(b,a,1)
    assert restored==original
    return changed

def prepare(out):
    out.mkdir(parents=True,exist_ok=False)
    pins=wire.line_pins6.plan(json.loads(LINE.read_text()))['pins']
    (out/'census.c').write_text(generated(pins))
    atomic_json(out/'source-plan.json',dict(created_utc=utc(),pins=pins,line_sha256=sha(LINE),
        source_sha256=sha(out/'census.c'),reference_source_sha256=sha(wire.solve6.SOURCE),
        helpers={n:sha(ROOT/'tools'/n) for n in HELPERS},
        original_rules_solver_tt_unchanged=True,fail_closed_line_pins=True,
        cutoff_empties=16,cost_cap=4096,cost_memo_bytes=67108864,
        counts_only=True,wire_export_allowed=False,accepted_proof=False))

def checked(out,need_binary=True):
    plan=json.loads((out/'source-plan.json').read_text())
    assert sha(LINE)==plan['line_sha256'] and sha(wire.solve6.SOURCE)==plan['reference_source_sha256']
    assert all(sha(ROOT/'tools'/n)==h for n,h in plan['helpers'].items())
    assert sha(out/'census.c')==plan['source_sha256']
    assert (out/'census.c').read_text()==generated(plan['pins'])
    if need_binary:
        built=json.loads((out/'build.json').read_text())
        assert built['source_plan_sha256']==sha(out/'source-plan.json') and sha(out/'census')==built['binary_sha256']
    return plan

def build(out):
    checked(out,False)
    cc=Path(shutil.which('cc')).resolve(strict=True)
    argv=[str(cc),*wire.solve6.FLAGS,str(out/'census.c'),'-o',str(out/'census')]
    done=subprocess.run(argv,capture_output=True,text=True,timeout=25)
    assert done.returncode==0,done.stderr
    atomic_json(out/'build.json',dict(created_utc=utc(),command=argv,compiler=str(cc),compiler_sha256=sha(cc),
        flags=list(wire.solve6.FLAGS),source_plan_sha256=sha(out/'source-plan.json'),binary_sha256=sha(out/'census'),stderr=done.stderr,accepted_proof=False))

def command(out,position,turn,direction,cpu,states,ttbits=18,warm=False):
    args=[str(out/'census'),'layout','--position',position,'--turn',turn,'--direction',direction,
        '--threshold','4','--frontier-discs','36','--max-states',str(states),'--max-nodes','1000000000000',
        '--max-memory-mb','8192' if warm else '256','--max-cpu-seconds',str(cpu),
        '--tt-bits',str(ttbits),'--small','4','--deep-order','5','--emit-states','0',
        '--counts-only','--layout-limit-mib','128','--layout-max-entries','200','--layout-max-tokens','32000',
        '--layout-max-records','20000000','--wire-inline-limit','256','--wire-record-limit','1048576','--wire-body-fuel','80']
    if warm:args+=['--load-tt',str(WARM)]
    return args

def execute(argv,timeout):
    done=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    assert len(done.stdout)<2**20
    counts=json.loads(done.stdout)
    return dict(command=argv,exit_code=done.returncode,counts=counts,stderr=done.stderr)

def accepted(result):
    c=result['counts']
    return result['exit_code']==0 and all(c.get(k) is True for k in ['complete','root_validated','root_holds','layout_complete','layout_counts_only']) and 'states' not in c

def fixture(out):
    checked(out)
    ident,state,_=fixtures.LOWER_CASES[0]
    entries=[]
    for pos,turn,direction in [(state[1:],'black','lower'),(json.loads(LINE.read_text())['states'][26][1:],'black' if json.loads(LINE.read_text())['states'][26][0]=='b' else 'white','upper')]:
        result=execute(command(out,pos,turn,direction,40,1000000),65)
        entries.append(result);atomic_json(out/'fixture-progress.json',dict(entries=entries,accepted_proof=False))
        assert accepted(result),'native layout fixture not complete'
    atomic_json(out/'fixture.json',dict(created_utc=utc(),entries=entries,accepted_proof=False,mathematical_objective_complete=False))

def warm_provenance():
    receipt=DONOR/'results/native-lower20-resume-20261006.json'
    side=Path(str(WARM)+'.json');metadata=json.loads(side.read_text());record=json.loads(receipt.read_text())
    binary=DONOR/'results/native6/solve6';source=DONOR/'tools/native6/solve6.c'
    assert record['accepted'] and record['source_unchanged'] and record['expected_source_matches']
    assert metadata['format']=='native6-tt-v1' and metadata['config']==dict(tt_bits=25,small=4,deep_order=5)
    assert metadata['cache_sha256']==WARM_SHA and metadata['cache_bytes']==WARM.stat().st_size and sha(WARM)==WARM_SHA
    assert metadata['build']['binary_sha256']==sha(binary) and metadata['build']['source_sha256']==sha(source)==sha(wire.solve6.SOURCE)
    return {str(p):sha(p) for p in [receipt,side,binary,source]}

def initial(out,direction):
    checked(out)
    assert json.loads((out/'fixture.json').read_text())['entries'] and all(accepted(x) for x in json.loads((out/'fixture.json').read_text())['entries'])
    pins=warm_provenance();stop=threading.Event();errors=[]
    def watch():
        while not stop.wait(3):
            try:
                resources.storage(8*2**20)
                assert resources.batch.allocated(out)<8*2**20
                assert shutil.disk_usage(ROOT).free-8*2**20>=80*2**30
            except BaseException as e:
                errors.append(str(e));atomic_json(out/'resource-stop.json',dict(reason=str(e),utc=utc()));os.kill(os.getpid(),signal.SIGTERM);return
    thread=threading.Thread(target=watch,daemon=True);thread.start()
    try:
        argv=command(out,'initial','black',direction,2500,100000000,25,True)
        atomic_json(out/(direction+'-request.json'),dict(created_utc=utc(),command=argv,warm_sha256=WARM_SHA,warm_guards=pins,counts_only=True,accepted_proof=False))
        result=execute(argv,3100)
    finally:stop.set();thread.join()
    assert not errors and all(sha(Path(n))==h for n,h in pins.items()) and sha(WARM)==WARM_SHA
    atomic_json(out/(direction+'.json'),dict(created_utc=utc(),result=result,complete=accepted(result),warm_unchanged=True,counts_only=True,accepted_proof=False,mathematical_objective_complete=False))
    assert accepted(result),'initial counts censored; retain prefix, no complete forecast'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','build','fixture','lower','upper']);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve()
    if a.mode in ['prepare','build','fixture']:globals()[a.mode](out)
    else:initial(out,a.mode)
