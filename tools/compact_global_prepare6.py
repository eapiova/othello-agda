"""Bounded10000-row sample with shared compact state chunks, no native solver."""
import hashlib
import json
from pathlib import Path
import shutil

import bench6
import compact_shared6 as compact
from directed_probe6 import converted
from unicode_codec_probe6 import encode
from sparse_citation_pilot6 import tree
from provenance import source_identity
from run_job import atomic_json,utc
from wire_part_samples6 import extract

ROOT=Path(__file__).resolve().parents[1]
PREFIX='Tests.CompactGlobalBatch6'
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
PARTS=list(range(342,392));BASE=68400;ROWS=10000


def row_text(text):
    assert len(text)%13==0
    reverse={c:n//9+3*((n//3)%3)+9*(n%3) for n,c in enumerate(compact.TRIPLES)}
    values=[]
    for offset in range(0,len(text),13):
        raw=text[offset:offset+13];assert raw[0] in 'bw'
        codes=[reverse[raw[1+2*r]]+27*reverse[raw[2+2*r]] for r in range(6)]
        assert all(0<=n<729 for n in codes)
        values.append(('B' if raw[0]=='b' else 'W')+''.join(chr(256+n) for n in codes))
    return ''.join(values)


def prepare(out):
    out=Path(out);request=json.loads((out/'input-request.json').read_text())
    assert request['selected_parts']==PARTS and not (out/'check').exists()
    sample=extract(Path(request['wire']),expected_sha256=request['wire_sha256'],
        expected_rows=request['wire_rows'],selected=PARTS,max_selected_parts=50,
        max_sample_bytes=8*2**20,max_reference_occurrences=160000,max_unique_references=160000)
    atomic_json(out/'sample.json',sample)
    sample=json.loads((out/'sample.json').read_text())
    assert all(int(part)<392 for part in sample['states']) and len(sample['states'])<=392
    tokens=sum(c['tokens'] for c in sample['cases']);assert tokens<=160000
    check=out/'check';folder=check/'src/Tests/CompactGlobalBatch6';folder.mkdir(parents=True)
    decoder=ROOT/'src/Othello/PackedStatesText6.agda'
    dest=check/'src/Othello/PackedStatesText6.agda';dest.parent.mkdir(parents=True);shutil.copy2(decoder,dest)
    chunks=sorted(int(part) for part in sample['states'])
    groups=[chunks[i:i+50] for i in range(0,len(chunks),50)]
    common='''open import Prelude
import Game.NatMap as M
import Othello.RowPacked6 as Packed
import Othello.PackedStatesText6 as Text
import Game.Balanced as B
'''
    def add(name,body):
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted untrusted data; checked uses required.\nmodule '+PREFIX+'.'+name+' where\n\n'+body)
    for group,parts in enumerate(groups):
        body=common
        for part in parts:
            chunk=sample['states'][str(part)];packed=row_text(chunk['text'])
            assert len(packed)==7*chunk['rows']
            body+=f'p{part} : B.Vec Packed.PackedState {chunk["rows"]}\np{part} = Text.states {chunk["rows"]} '+json.dumps(packed,ensure_ascii=False)+'\n'
        expression=tree(parts,lambda part:f'(M.rows {200*part} {sample["states"][str(part)]["rows"]} p{part})',
            lambda pivot,left,right:f'(M.branch {200*pivot} {left} {right})')
        add('Group'+str(group),body+'table : M.Map Packed.PackedState\ntable = '+expression+'\n')
    root_body=common+'''open import Game.Core using (white)
open import Game.Symmetry using (Proven)
open import Game.Certificate using (leaf)
open import Othello.Statements using (lowerGoal)
import Othello.Finite as F
import Othello.InlineEntries6 as Rules
import Game.NatMapLaws as Laws
'''
    for group in range(len(groups)):root_body+=f'import {PREFIX}.Group{group} as G{group}\n'
    table=tree(list(range(len(groups))),lambda group:f'G{group}.table',
        lambda pivot,left,right:f'(M.branch {200*groups[pivot][0]} {left} {right})')
    root_body+='table : M.Map Packed.PackedState\ntable = '+table+'''
fallback : Packed.PackedState
fallback = Packed.packed (728 F.∷ 728 F.∷ 728 F.∷ 728 F.∷ 728 F.∷ 728 F.∷ F.[]) white
G : ℕ → Packed.PackedState
G = Laws.totalize table fallback
abstract
  fallback-won : Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode fallback)
  fallback-won = leaf , refl
'''
    add('Root',root_body)
    certificates=[];counts=None
    for case in sample['cases']:
        states=[bench6.decode(compact.unpack_state(case['state_text'][13*i:13*(i+1)])) for i in range(case['rows'])]
        texts,new=converted(case['body_text'],states,text_output=True)
        certificates.extend(encode(text) for text in texts)
        if counts is None:counts={key:0 for key in new}
        for key,value in new.items():counts[key]+=value
    assert len(certificates)==ROWS and sum(v for k,v in counts.items() if k!='directed_choices')==tokens
    add('Body','open import Agda.Builtin.String using (String)\ntext : String\ntext = '+json.dumps(''.join(certificates),ensure_ascii=False)+'\n')
    add('Closed','''open import Prelude
import Game.NatMap as M
import Othello.GlobalPackedRows6 as Rows
import Othello.UnicodeCompact6 as Codec
import Tests.CompactGlobalBatch6.Root as Global
import Tests.CompactGlobalBatch6.Body as Body

abstract
  partial : Rows.A.Partial Global.G (M.rows 68400 10000 (Rows.ps Global.G 68400 10000))
  partial = Rows.partial Global.G 68400 10000 (Codec.bodies 10000 Body.text) refl
-- Coverage is partial: all unowned state rows and initial guarantees remain open.
''')
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        copied_core_sha256={'src/Othello/PackedStatesText6.agda':hashlib.sha256(decoder.read_bytes()).hexdigest()},
        owned_rows=ROWS,base=BASE,selected_parts=PARTS,tokens=tokens,counts=counts,
        represented_state_chunks=len(chunks),represented_state_rows=sum(c['rows'] for c in sample['states'].values()),
        state_data_modules=len(groups),rows_per_lookup_chunk=200,max_state_chunks_per_module=50,
        whole_wire_scans=2,wire_sha256=sample['wire_sha256'],wire_input_unchanged=sample['input_unchanged'],
        sample_bytes=(out/'sample.json').stat().st_size,
        source_bytes=sum(p.stat().st_size for p in (check/'src').rglob('*.agda')),
        no_solver=True,full_workflow_forecast_validated=False,production_go=False,
        initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
