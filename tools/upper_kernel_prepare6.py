"""Untrusted stratified UPPER data; safe uses on one shared packed state map."""
import json
from pathlib import Path
import shutil
import bench6
import compact_shared6 as compact
from compact_global_prepare6 import row_text
from directed_probe6 import converted
from unicode_codec_probe6 import encode
from sparse_citation_pilot6 import tree
from wire_part_samples6 import extract,_records,_fingerprint
from census_pilot6 import ccanonical
from symmetry_stats6 import transform
from provenance import source_identity
from run_job import atomic_json,utc

ROOT=Path(__file__).resolve().parents[1]
PREFIX='Tests.UpperKernelSample6'
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
COMMON='''open import Prelude
import Game.NatMap as M
import Game.Balanced as B
import Othello.RowPacked6 as Packed
import Othello.PackedStatesText6 as Text
'''


def prepare(out):
    out=Path(out);request=json.loads((out/'input-request.json').read_text())
    wire=request['wire'];selected=sorted(request['selection']['selected'])
    sample=extract(Path(wire['path']),expected_sha256=wire['sha256'],expected_rows=wire['rows'],selected=selected,
        max_sample_bytes=24*2**20,max_reference_occurrences=256000,max_unique_references=256000)
    atomic_json(out/'sample.json',sample);sample=json.loads((out/'sample.json').read_text())
    line=json.loads((ROOT/'certificates/six-line.json').read_text())
    prefixes=[];wanted={}
    for i,raw in enumerate(line['states'][:21]):
        literal=bench6.decode(raw);representative=ccanonical(literal)
        tag=next(t for t in range(8) if transform(literal,t)==representative)
        item=dict(ply=i,tag=tag,packed_state=compact.pack_state(representative),key=None)
        prefixes.append(item);wanted.setdefault(item['packed_state'].encode(),[]).append(item)
    buffer=[];needed=set()
    path=Path(wire['path']);identity=_fingerprint(path.stat())
    for rank,state,body,refs in _records(path,wire['sha256'],wire['rows'],identity):
        p=rank//200;buffer.append(state.decode('ascii'))
        if state in wanted:
            needed.add(p)
            for item in wanted[state]:
                assert item['key'] is None,'ambiguous prefix state'
                item['key']=rank
        if len(buffer)==200 or rank+1==wire['rows']:
            if p in needed:sample['states'][str(p)]=dict(rows=len(buffer),text=''.join(buffer))
            buffer=[]
    sample['wire_scans']=3;sample['literal_prefix_index']=prefixes
    atomic_json(out/'sample.json',sample)
    check=out/'check';assert not check.exists()
    folder=check/'src/Tests/UpperKernelSample6';folder.mkdir(parents=True)
    for name in ['ConsecutiveUpperRange6','PackedPrefixBounds6']:
        core=check/'src/Othello'/(name+'.agda');core.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'src/Othello'/(name+'.agda'),core)
    def add(name,body):
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted untrusted data; every game row requires safe checking.\nmodule '+PREFIX+'.'+name+' where\n'+body)
    chunks=sorted(map(int,sample['states']));groups=[chunks[i:i+50] for i in range(0,len(chunks),50)]
    group_of={p:i for i,g in enumerate(groups) for p in g}
    for i,parts in enumerate(groups):
        body=COMMON
        for p in parts:
            item=sample['states'][str(p)];text=row_text(item['text'])
            body+=f'p{p} : B.Vec Packed.PackedState {item["rows"]}\np{p} = Text.states {item["rows"]} '+json.dumps(text,ensure_ascii=False)+'\n'
        table=tree(parts,lambda p:f'(M.rows {200*p} {sample["states"][str(p)]["rows"]} p{p})',
            lambda p,l,r:f'(M.branch {200*p} {l} {r})')
        add('Group'+str(i),body+'table : M.Map Packed.PackedState\ntable = '+table+'\n')
    body=COMMON+'''open import Game.Core using (black)
open import Game.Symmetry using (Proven)
open import Game.Certificate using (leaf)
open import Othello.Statements using (upperGoal)
import Othello.Finite as F
import Othello.InlineEntries6 as Rules
import Game.NatMapLaws as Laws
'''
    for i in range(len(groups)):body+=f'import {PREFIX}.Group{i} as G{i}\n'
    table=tree(list(range(len(groups))),lambda i:f'G{i}.table',
        lambda i,l,r:f'(M.branch {200*groups[i][0]} {l} {r})')
    body+='table : M.Map Packed.PackedState\ntable = '+table+'''
fallback : Packed.PackedState
fallback = Packed.packed (364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ F.[]) black
G : ℕ → Packed.PackedState
G = Laws.totalize table fallback
abstract
  fallback-won : Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode fallback)
  fallback-won = leaf , refl
'''
    add('Root',body)
    body='open import Agda.Builtin.String using (String)\n';counts={};case_meta={}
    for case in sample['cases']:
        p=case['part'];n=case['rows'];base=200*p
        states=[bench6.decode(compact.unpack_state(case['state_text'][13*i:13*(i+1)])) for i in range(n)]
        texts,new=converted(case['body_text'],states,text_output=True)
        assert len(texts)==n
        body+=f'b{p} : String\nb{p} = '+json.dumps(''.join(encode(t) for t in texts),ensure_ascii=False)+'\n'
        for key,value in new.items():counts[key]=counts.get(key,0)+value
        part=COMMON+f'''import Othello.ConsecutivePackedUpper6 as Rows
import Othello.ConsecutiveUpperRange6 as Range
import Othello.UnicodeCompact6 as Codec
import {PREFIX}.Root as Global
import {PREFIX}.Body as Body
import {PREFIX}.Group{group_of[p]} as Own
owned : M.Map Packed.PackedState
owned = M.rows {base} {n} Own.p{p}
abstract
  source : Rows.A.Partial Global.G (M.rows {base} {n} (Rows.ps Global.G {base} {n}))
  source = Rows.partial Global.G {base} {n} (Codec.bodies {n} Body.b{p}) refl
  partial : Rows.A.Partial Global.G owned
  partial = Range.checked {{G = Global.G}} {{base = {base}}} {{n = {n}}}
    {{target = owned}} source refl
'''
        add('Part'+str(p),part)
        case_meta[str(p)]=dict(rows=n,tokens=case['tokens'],counts=new)
    add('Body',body)
    body=COMMON+'''import Othello.ConsecutivePackedUpper6 as Rows
import Tests.UpperKernelSample6.Root as Global
'''
    for p in selected:body+=f'import {PREFIX}.Part{p} as P{p}\n'
    owned=tree(selected,lambda p:f'P{p}.owned',lambda p,l,r:f'(M.branch {200*p} {l} {r})')
    proof=tree(selected,lambda p:f'P{p}.partial',lambda p,l,r:f'(Rows.A.join {200*p} {l} {r})')
    add('All',body+'owned : M.Map Packed.PackedState\nowned = '+owned+'''
abstract
  partial : Rows.A.Partial Global.G owned
  partial = '''+proof+'\n-- Unowned state rows remain obligations; no initial bound is inferred.\n')
    body='''import Othello.PackedPrefixBounds6 as Bridge
import Othello.SpliceLine6 as Line
import Tests.UpperKernelSample6.Root as Global
open import Prelude
'''
    for item in prefixes:
        if item['key'] is not None:
            i=item['ply'];body+=f'w{i} : Bridge.Witness Global.G Line.p{i}\nw{i} = Bridge.at {item["key"]} {item["tag"]} refl\n'
    add('PrefixWitnesses',body+'-- State identities only. The fully proved-map premise remains open.\n')
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        selected_parts=selected,owned_rows=sum(c['rows'] for c in sample['cases']),cases=case_meta,counts=counts,
        represented_state_chunks=len(chunks),represented_state_rows=sum(s['rows'] for s in sample['states'].values()),
        state_data_modules=len(groups),rows_per_lookup_chunk=200,max_state_chunks_per_module=50,
        source_bytes=sum(p.stat().st_size for p in (check/'src').rglob('*.agda')),
        sample_bytes=(out/'sample.json').stat().st_size,whole_authenticated_wire_scans=3,
        literal_prefix_witnesses_found=sum(x['key'] is not None for x in prefixes),
        literal_prefixes_missing_from_wire=[x['ply'] for x in prefixes if x['key'] is None],
        wire_sha256=wire['sha256'],new_native_solver_runs=0,common_encoded_map=True,
        full_workflow_forecast_validated=False,production_go=False,
        initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
