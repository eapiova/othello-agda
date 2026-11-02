"""Fresh group500 on the SAME full UPPER G; measure the full-index preparation route."""
import json,shutil,time
from pathlib import Path
import bench6,compact_shared6 as compact
from directed_probe6 import converted
from native_layout_samples6 import convert_body
from packed_wire6 import records
from unicode_codec_probe6 import encode
from provenance import source_identity
from run_job import atomic_json,utc

ROOT=Path(__file__).resolve().parents[1]
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'


def prepare(out):
    out=Path(out);r=json.loads((out/'input-request.json').read_text());wire=r['wire']
    assert r['selected_group']==500 and wire['raw_rows']==6530011
    check=out/'check';assert not check.exists();folder=check/'src/Tests/TextUpperHoldout6';folder.mkdir(parents=True)
    start=time.process_time();index={}
    for rank,state,_,_ in records(wire):
        assert state not in index and len(index)<6530011;index[state]=rank
    assert len(index)==6530011;index_cpu=time.process_time()-start
    selected=[];start=time.process_time()
    for rank,state,body,refs in records(wire):
        if rank//10000==500:selected.append((rank,state.decode('ascii'),body.decode('ascii'),refs))
    scan_cpu=time.process_time()-start;assert len(selected)==10000
    start=time.process_time();texts=[];tokens=0;counts={}
    for rank,state,body,refs in selected:
        ids=[index[refs[i:i+13]] for i in range(0,len(refs),13)];assert all(j<rank for j in ids)
        numeric,n=convert_body(body,ids);tokens+=n
        directed,new=converted(numeric,[bench6.decode(compact.unpack_state(state))],text_output=True)
        texts.append(encode(directed[0]))
        for k,v in new.items():counts[k]=counts.get(k,0)+v
    transform_cpu=time.process_time()-start;assert tokens<=500000
    def add(name,body):
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted untrusted body; Agda must check every new row.\nmodule Tests.TextUpperHoldout6.'+name+' where\n'+body)
    add('Body500','open import Agda.Builtin.String using (String)\ntext : String\ntext = '+json.dumps(''.join(texts),ensure_ascii=False)+'\n')
    add('Rows500','''open import Prelude
open import Game.Core using (black)
open import Othello.Statements using (upperGoal)
import Game.NatMap as M
import Game.StepRangeAssembly as Range
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Assembly
import Othello.TextCertifiedAssembly6 as Box
import Othello.ConsecutivePackedUpper6 as Rows
import Othello.UnicodeCompact6 as Codec
import Tests.TextUpperPacked6.Root as Global
import Tests.TextUpperPacked6.Group500 as Own
import Tests.TextUpperHoldout6.Body500 as Body
module Parts = Assembly.Assembly black (upperGoal 4)
module Certified = Box.Assembly black (upperGoal 4)
abstract
  source : Rows.A.Partial Global.G (M.rows 5000000 10000 (Rows.ps Global.G 5000000 10000))
  source = Rows.partial Global.G 5000000 10000 (Codec.bodies 10000 Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {G = Global.G} {base = 5000000} {n = 10000}
    {xs = Rows.ps Global.G 5000000 10000} {target = Own.table}
    (Rows.lookup-ps Global.G 5000000 10000) source
    (Range.check-sound 5000000 10000 (T.domain Own.table) refl)
  certified : Certified.Certified Global.G Own.table
  certified = Certified.certify Global.G Own.table partial
''')
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),cases={'500':dict(rows=10000,tokens=tokens,counts=counts)},
        full_index_states=len(index),full_index_cpu_seconds=index_cpu,second_scan_cpu_seconds=scan_cpu,
        selected_body_transformation_cpu_seconds=transform_cpu,full_authenticated_wire_scans=2,
        same_existing_text_upper_G=True,full_body_generation_cost_not_yet_validated=True,
        no_solver_runs=True,initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
