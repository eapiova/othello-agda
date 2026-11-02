"""Full compact UPPER state table; two owner batches and conditional closure.

All native bytes remain data. Agda checks each selected game row, the actual
state-map assembly and exact sparse-prefix resolver compatibility.
"""
import json
from pathlib import Path
import shutil
import bench6
import compact_shared6 as compact
from compact_global_prepare6 import row_text
from directed_probe6 import converted
from native_layout_samples6 import convert_body
from packed_wire6 import records
from sparse_citation_pilot6 import tree
from unicode_codec_probe6 import encode
from provenance import source_identity
from run_job import atomic_json,utc

ROOT=Path(__file__).resolve().parents[1]
PREFIX='Tests.FullUpperPacked6'
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
COMMON='''open import Prelude
import Game.NatMap as M
import Game.Balanced as B
import Othello.RowPacked6 as Packed
import Othello.PackedStatesText6 as Text
'''
TRAIN=6;HOLDOUT=652


def prepare(out):
    out=Path(out);request=json.loads((out/'input-request.json').read_text());wire=request['wire']
    assert wire['raw_rows']==6530011 and request['training_group']==TRAIN and request['heldout_group']==HOLDOUT
    check=out/'check';assert not check.exists();folder=check/'src/Tests/FullUpperPacked6';folder.mkdir(parents=True)
    core=check/'src/Game/NatMapCheck.agda';core.parent.mkdir(parents=True)
    shutil.copy2(ROOT/'src/Game/NatMapCheck.agda',core)
    def add(name,body):
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted untrusted data; game proofs need checked rows.\nmodule '+PREFIX+'.'+name+' where\n'+body)
    selected={TRAIN:[],HOLDOUT:[]};wanted=set();buffer=[];chunk_rows={};group_parts=[];group_body=COMMON
    refs_count=0
    for rank,state,body,refs in records(wire):
        part=rank//200;group=rank//10000;buffer.append(state.decode())
        if group in selected:
            references=[refs[i:i+13] for i in range(0,len(refs),13)]
            wanted.update(references);refs_count+=len(references)
            assert len(wanted)<=300000 and refs_count<=1000000
            selected[group].append((rank,state.decode(),body.decode('ascii'),references))
        if len(buffer)==200 or rank+1==wire['raw_rows']:
            n=len(buffer);chunk_rows[part]=n;group_parts.append(part)
            group_body+=f'p{part} : B.Vec Packed.PackedState {n}\np{part} = Text.states {n} '+json.dumps(row_text(''.join(buffer)),ensure_ascii=False)+'\n'
            buffer=[]
            if len(group_parts)==50 or rank+1==wire['raw_rows']:
                expression=tree(group_parts,lambda p:f'(M.rows {200*p} {chunk_rows[p]} p{p})',
                    lambda p,l,r:f'(M.branch {200*p} {l} {r})')
                add('Group'+str(part//50),group_body+'table : M.Map Packed.PackedState\ntable = '+expression+'\n')
                group_parts=[];group_body=COMMON
    assert len(chunk_rows)==32651 and all(len(v)==10000 for v in selected.values())
    found={}
    for rank,state,body,refs in records(wire):
        if state in wanted:
            assert state not in found;found[state]=rank
    assert set(found)==wanted
    group_count=(wire['raw_rows']+9999)//10000
    imports=''.join(f'import {PREFIX}.Group{g} as G{g}\n' for g in range(group_count))
    body=COMMON+'''open import Game.Core using (black)
open import Game.Symmetry using (Proven)
open import Game.Certificate using (leaf)
open import Othello.Statements using (upperGoal)
import Othello.Finite as F
import Othello.InlineEntries6 as Rules
import Game.NatMapLaws as Laws
'''+imports
    table=tree(list(range(group_count)),lambda g:f'G{g}.table',lambda g,l,r:f'(M.branch {10000*g} {l} {r})')
    add('Root',body+'table : M.Map Packed.PackedState\ntable = '+table+'''
fallback : Packed.PackedState
fallback = Packed.packed (364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ F.[]) black
G : ℕ → Packed.PackedState
G = Laws.totalize table fallback
abstract
  fallback-won : Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode fallback)
  fallback-won = leaf , refl
''')
    case_meta={}
    for group,rows in selected.items():
        texts=[];tokens=0;counts={}
        for rank,state,body,refs in rows:
            ids=[found[k] for k in refs];assert all(i<rank for i in ids)
            numeric,n=convert_body(body,ids);tokens+=n
            directed,c=converted(numeric,[bench6.decode(compact.unpack_state(state))],text_output=True)
            texts.append(encode(directed[0]))
            for k,v in c.items():counts[k]=counts.get(k,0)+v
        assert tokens<=500000
        add('Body'+str(group),'open import Agda.Builtin.String using (String)\ntext : String\ntext = '+json.dumps(''.join(texts),ensure_ascii=False)+'\n')
        add('Rows'+str(group),COMMON+f'''import Othello.ConsecutivePackedUpper6 as Rows
import Othello.ConsecutiveUpperRange6 as Range
import Othello.UnicodeCompact6 as Codec
import {PREFIX}.Root as Global
import {PREFIX}.Group{group} as Own
import {PREFIX}.Body{group} as Body
abstract
  partial : Rows.A.Partial Global.G Own.table
  partial = Range.checked {{G = Global.G}} {{base = {10000*group}}} {{n = 10000}}
    {{target = Own.table}}
    (Rows.partial Global.G {10000*group} 10000 (Codec.bodies 10000 Body.text) refl) refl
''')
        case_meta[str(group)]=dict(rows=10000,tokens=tokens,counts=counts)
    body=COMMON+'''import Othello.ConsecutivePackedUpper6 as Rows
import Tests.FullUpperPacked6.Root as Global
'''+imports+'''open import Game.Core using (black)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (upperGoal)
import Othello.InlineEntries6 as Rules
record CheckedParts : Set where
  field
'''
    for g in range(group_count):body+=f'    part{g} : Rows.A.Partial Global.G G{g}.table\n'
    join=tree(list(range(group_count)),lambda g:f'(CheckedParts.part{g} accepted)',
        lambda g,l,r:f'(Rows.A.join {10000*g} {l} {r})')
    body+='''abstract
  assemble : CheckedParts → Rows.A.Partial Global.G Global.table
  assemble accepted = '''+join+'''
  complete : CheckedParts → ∀ key →
    Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (Global.G key))
'''
    body+='''  complete accepted = Rows.A.global-proven Global.G
    (Rows.A.complete Global.table Global.fallback Global.fallback-won (assemble accepted))
-- CheckedParts is an explicit unsupplied premise, not a completed initial bound.
'''
    add('Assembly',body)
    add('Compatible',COMMON+'''import Game.NatMapCheck as Align
import Tests.InlineUpperPrefixes6.Data as PrefixData
import Tests.InlineUpperPrefixes6.Closed as Prefix
import Tests.FullUpperPacked6.Root as Global
module Check = Align.Checking Packed.equal Packed.equal-sound
abstract
  compatible : Prefix.Check.Local.V.Compatible PrefixData.L Global.G
  compatible = Check.compatible-sound PrefixData.demand Global.G refl
''')
    add('Load',COMMON+'''import Othello.ConsecutivePackedUpper6 as Rows
import Tests.FullUpperPacked6.Root as Global
G : ℕ → Packed.PackedState
G = Global.G
''')
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        full_state_rows=wire['raw_rows'],lookup_chunks=len(chunk_rows),data_groups=group_count,
        tested_owner_rows=20000,training_group=TRAIN,heldout_group=HOLDOUT,cases=case_meta,
        reference_occurrences=refs_count,indexed_reference_states=len(found),whole_authenticated_zip_scans=2,
        source_bytes=sum(p.stat().st_size for p in (check/'src').rglob('*.agda')),
        fixed_full_map=True,unowned_groups=group_count-2,new_native_solver_runs=0,
        full_row_coverage_proved=False,initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
