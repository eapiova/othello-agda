"""Extract existing inline UPPER subtrees for literal prefixes; no search."""
import json
from pathlib import Path
import shutil
import bench6
import compact_shared6 as compact
import ref
from compact_global_prepare6 import row_text
from directed_probe6 import converted
from native_layout_samples6 import convert_body
from sparse_citation_pilot6 import tree
from symmetry_stats6 import transform
from unicode_codec_probe6 import encode
from wire_part_samples6 import _records,_fingerprint
from provenance import source_identity
from run_job import atomic_json,utc

ROOT=Path(__file__).resolve().parents[1]
PREFIX='Tests.InlineUpperPrefixes6'
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'


def prepare(out):
    out=Path(out);request=json.loads((out/'input-request.json').read_text())
    wire=request['wire'];path=Path(wire['path']);identity=_fingerprint(path.stat())
    prefixes=json.loads((out.with_name('upper-kernel-probe6-20261018')/'sample.json').read_text())['literal_prefix_index']
    parents={p['key'] for p in prefixes if p['key'] is not None};records={};wanted=set()
    for rank,state,body,refs in _records(path,wire['sha256'],wire['rows'],identity):
        if rank not in parents:continue
        references=[refs[k:k+13] for k in range(0,len(refs),13)]
        wanted.update(references);records[rank]=dict(state=state.decode(),body=body.decode(),references=references)
    assert set(records)==parents and len(records)==8 and len(wanted)<=20000
    found={}
    for rank,state,body,refs in _records(path,wire['sha256'],wire['rows'],identity):
        if state in wanted:
            assert state not in found;found[state]=rank
    assert set(found)==wanted
    literals=[bench6.decode(s) for s in json.loads((ROOT/'certificates/six-line.json').read_text())['states'][:21]]
    targets={}
    for ply,s in enumerate(literals):
        for tag in range(8):targets.setdefault(transform(s,tag),[]).append((ply,tag))
    extracted={}
    for owner,record in sorted(records.items(),reverse=True):
        text=record['body'];references=record['references'];position=reference=0
        def node(s,depth=0):
            nonlocal position,reference
            assert depth<128 and position<len(text)
            start=position;first_ref=reference;tag=text[position];position+=1
            if tag=='L':pass
            elif tag=='K':reference+=1
            elif tag=='R':
                assert compact.COUNTS.index(text[position])<8;position+=1;reference+=1
            elif tag=='P':
                children=ref.successors(s);assert len(children)==1;node(children[0],depth+1)
            else:
                assert tag in 'CF';n=compact.COUNTS.index(text[position]);position+=1
                children=ref.successors(s)
                if tag=='C':assert n<len(children);node(children[n],depth+1)
                else:
                    assert n==len(children)
                    for child in children:node(child,depth+1)
            assert reference<=len(references)
            for ply,sym in targets.get(s,[]):
                if ply not in extracted:
                    ids=[found[k] for k in references[first_ref:reference]]
                    assert all(j<owner for j in ids)
                    numeric,tokens=convert_body(text[start:position],ids)
                    directed,counts=converted(numeric,[s],text_output=True)
                    extracted[ply]=dict(ply=ply,owner=owner,tag=sym,state=compact.pack_state(s),
                        body=encode(directed[0]),tokens=tokens,counts=counts,cited_keys=ids)
        node(bench6.decode(compact.unpack_state(record['state'])))
        assert position==len(text) and reference==len(references)
    atomic_json(out/'extraction.json',dict(created_utc=utc(),parent_rows=sorted(parents),
        distinct_reference_states=len(found),prefixes_found=sorted(extracted),
        missing_prefixes=sorted(set(range(21))-set(extracted)),whole_authenticated_wire_scans=2,
        no_solver=True,untrusted_data_only=True))
    assert set(extracted)==set(range(21)),'Missing inline literal prefix; preserve extracted evidence'
    atomic_json(out/'sample.json',dict(prefixes={str(k):v for k,v in extracted.items()},
        references={str(rank):state.decode() for state,rank in found.items()},wire=wire))
    check=out/'check';assert not check.exists()
    core=check/'src/Othello/InlinePrefix6.agda';core.parent.mkdir(parents=True)
    shutil.copy2(ROOT/'src/Othello/InlinePrefix6.agda',core)
    folder=check/'src/Tests/InlineUpperPrefixes6';folder.mkdir(parents=True)
    def add(name,body):
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted; literal subtree checks, full cited-map premise remains open.\nmodule '+PREFIX+'.'+name+' where\n'+body)
    body='''open import Prelude
import Game.NatMap as M
import Othello.RowPacked6 as Packed
import Othello.PackedStatesText6 as Text
import Othello.UnicodeCompact6 as Codec
import Game.Balanced as B
'''
    keys=sorted(found.values());by_key={rank:state.decode() for state,rank in found.items()}
    for key in keys:body+=f's{key} : B.Vec Packed.PackedState 1\ns{key} = Text.states 1 '+json.dumps(row_text(by_key[key]),ensure_ascii=False)+'\n'
    demand=tree(keys,lambda key:f'(M.rows {key} 1 s{key})',lambda key,l,r:f'(M.branch {key} {l} {r})')
    body+='demand : M.Map Packed.PackedState\ndemand = '+demand+'\nL : ℕ → Maybe Packed.PackedState\nL = M.lookup demand\n'
    for ply in range(21):body+=f'c{ply} : Codec.Certificate\nc{ply} = B.lookupVec (Codec.bodies 1 '+json.dumps(extracted[ply]['body'],ensure_ascii=False)+') B.fzero\n'
    add('Data',body)
    body='''open import Prelude
open import Game.Core using (black; Guarantees)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (upperGoal)
import Othello.Fast6 as Fast
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.InlinePrefix6 as Prefix
import Othello.DirectSymmetry6 as Direct
import Othello.SpliceLine6 as Line
import Tests.InlineUpperPrefixes6.Data as Data
module Check = Prefix.Checking black (upperGoal 4) Direct.upperTransport6
'''
    for ply in range(21):
        item=extracted[ply]
        body+=f'''abstract
  upper{ply} : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p{ply}
  upper{ply} = Check.guarantee Data.L {item['owner']} Line.p{ply} {item['tag']} Data.c{ply} refl
'''
    add('Closed',body)
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        literal_upper_prefixes=21,distinct_reference_states=len(found),
        subtree_tokens=sum(e['tokens'] for e in extracted.values()),
        source_bytes=sum(p.stat().st_size for p in (check/'src').rglob('*.agda')),
        whole_authenticated_wire_scans=2,new_native_solver_runs=0,global_proven_premise_open=True,
        resolver_compatibility_premise_open=True,initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
