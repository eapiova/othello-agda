"""Resume a closed partial source ZIP; all reused/new sources remain unproved.

One authenticated full state index, then one authenticated streaming conversion.
Only a single10000-owner group is retained while its source is emitted.
"""
import hashlib,json,stat,struct,time,zipfile
from pathlib import Path
import bench6,compact_shared6 as compact
from directed_probe6 import converted
from native_layout_samples6 import convert_body
from unicode_codec_probe6 import encode
from packed_wire6 import records as zip_records
from wire_part_samples6 import _records,_fingerprint
from provenance import digest_entries
from run_job import atomic_json,utc

HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'


def prepare(out):
    out=Path(out);request=json.loads((out/'input-request.json').read_text());bound=request['bound']
    assert bound in ['upper','lower']
    upper=bound=='upper';total=6530011 if upper else 6873047;groups=(total+9999)//10000
    owned={6,500,652} if upper else {6,686}
    side=bound.title();prefix='Tests.Complete'+side+'Rows6';data='Tests.Text'+side+'Packed6'
    player='black' if upper else 'white';goal='upperGoal' if upper else 'lowerGoal'
    rows_module='ConsecutivePackedUpper6' if upper else 'ConsecutivePackedRows6'
    def records():
        if upper:
            yield from zip_records(request['wire'])
        else:
            path=Path(request['wire']);identity=tuple(request['wire_fingerprint'])
            assert _fingerprint(path.stat())==identity and path.stat().st_size==498606513
            yield from _records(path,request['wire_sha256'],total,identity)
    start=time.process_time();index={}
    for rank,state,_,_ in records():
        assert len(index)<total and state not in index;index[state]=rank
    assert len(index)==total
    index_cpu=time.process_time()-start
    archive=Path(request['resume_archive']);assert archive.is_file();entries={};cases={};text_buffer=[];token_buffer=0;count_buffer={}
    total_tokens=total_emitted_tokens=0;conversion_cpu=0.0;source_bytes=0;written_groups=0
    parent_hash=hashlib.sha256(archive.read_bytes()).hexdigest()
    assert parent_hash==request['partial_archive_sha256']
    with zipfile.ZipFile(archive) as saved:
        names=saved.namelist();assert len(names)==len(set(names))
        bodies={int(n[4:-5]) for n in names if n.startswith('Body') and n.endswith('.agda')}
        rows={int(n[4:-5]) for n in names if n.startswith('Rows') and n.endswith('.agda')}
        assert bodies==rows and len(names)==2*len(bodies) and bodies.isdisjoint(owned)
        for info in saved.infolist():
            raw=saved.read(info.filename)
            tag,size,mtime=struct.unpack('<HHQ',info.extra)
            assert tag==0xa6da and size==8
            entries[info.filename]=dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=info.external_attr>>16,mtime_ns=mtime)
            source_bytes+=len(raw)
            if info.filename.startswith('Body'):
                g=int(info.filename[4:-5]);text=json.loads(raw.decode().split('text = ',1)[1])
                tags={ch:text.count(ch) for ch in 'ABCDEFGH'}
                counts=dict(choices=tags['F']+tags['G'],directed_choices=tags['G'],leaves=tags['A'],
                    citations=tags['B']+tags['C'],forks=tags['H'],passes=tags['E'],solve=tags['D'])
                assert counts['solve']==0
                tokens=sum(tags.values());n=min(10000,total-10000*g)
                cases[str(g)]=dict(base=10000*g,rows=n,tokens=tokens,counts=counts,reused_partial_source=True)
                total_emitted_tokens+=tokens;written_groups+=1
        reused=set(bodies)
    atomic_json(out/'reused-entry-lineage.json',dict(parent_archive_sha256=parent_hash,
        entries=dict(entries),groups=sorted(reused),source_bytes=source_bytes,
        tokens_counted_from_fixed_width_body_tags=True,source_values_not_yet_Agda_checked=True))
    timestamp=time.time_ns();start=time.process_time()
    def add(saved,name,body):
        nonlocal source_bytes
        raw=(HEADER+'-- AI-assisted untrusted certificate source; safe Agda must check this module.\nmodule '+prefix+'.'+name+' where\n'+body).encode()
        assert len(raw)<=16*2**20
        filename=name+'.agda';assert filename not in entries
        info=zipfile.ZipInfo(filename);info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16
        info.extra=struct.pack('<HHQ',0xa6da,8,timestamp)
        saved.writestr(info,raw,compress_type=zipfile.ZIP_ZSTANDARD,compresslevel=19)
        entries[filename]=dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=stat.S_IFREG|0o644,mtime_ns=timestamp)
        source_bytes+=len(raw)
    with zipfile.ZipFile(archive,'a') as saved:
        for rank,state,body,refs in records():
            group=rank//10000
            if group not in owned and group not in reused:
                before=time.process_time()
                ids=[index[refs[j:j+13]] for j in range(0,len(refs),13)];assert all(j<rank for j in ids)
                numeric,tokens=convert_body(body.decode('ascii'),ids)
                directed,counts=converted(numeric,[bench6.decode(compact.unpack_state(state.decode('ascii')))],text_output=True)
                assert counts.get('solve',0)==0
                text_buffer.append(encode(directed[0]));token_buffer+=tokens
                for key,value in counts.items():count_buffer[key]=count_buffer.get(key,0)+value
                conversion_cpu+=time.process_time()-before
                assert len(text_buffer)<=10000 and token_buffer<=1000000
            if (rank+1)%10000==0 or rank+1==total:
                if group not in owned and group not in reused:
                    n=min(10000,total-10000*group);base=10000*group
                    assert len(text_buffer)==n
                    add(saved,'Body'+str(group),'open import Agda.Builtin.String using (String)\ntext : String\ntext = '+json.dumps(''.join(text_buffer),ensure_ascii=False)+'\n')
                    add(saved,'Rows'+str(group),f'''open import Prelude
open import Game.Core using ({player})
open import Othello.Statements using ({goal})
import Game.NatMap as M
import Game.StepRangeAssembly as Range
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Assembly
import Othello.TextCertifiedAssembly6 as Box
import Othello.{rows_module} as Rows
import Othello.UnicodeCompact6 as Codec
import {data}.Root as Global
import {data}.Group{group} as Own
import {prefix}.Body{group} as Body
module Parts = Assembly.Assembly {player} ({goal} 4)
module Certified = Box.Assembly {player} ({goal} 4)
abstract
  source : Rows.A.Partial Global.G (M.rows {base} {n} (Rows.ps Global.G {base} {n}))
  source = Rows.partial Global.G {base} {n} (Codec.bodies {n} Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {{G = Global.G}} {{base = {base}}} {{n = {n}}}
    {{xs = Rows.ps Global.G {base} {n}}} {{target = Own.table}}
    (Rows.lookup-ps Global.G {base} {n}) source
    (Range.check-sound {base} {n} (T.domain Own.table) refl)
  certified : Certified.Certified Global.G Own.table
  certified = Certified.certify Global.G Own.table partial
''')
                    cases[str(group)]=dict(base=base,rows=n,tokens=token_buffer,counts=count_buffer)
                    total_emitted_tokens+=token_buffer;written_groups+=1
                # Already checked groups are authenticated by the whole scan but not converted again.
                text_buffer=[];token_buffer=0;count_buffer={}
                if group%10==0 or rank+1==total:
                    atomic_json(out/'progress.json',dict(updated_utc=utc(),scanned_rows=rank+1,total_rows=total,
                        emitted_groups=written_groups,emitted_tokens=total_emitted_tokens,archive_bytes_so_far=archive.stat().st_size,
                        no_new_game_row_checks=True,mathematical_objective_complete=False))
        assert written_groups==groups-len(owned)
        closure='Tests.ParametricFullUpper6.Assembly' if upper else 'Tests.TextLowerPacked6.Assembly'
        body=f'''open import Prelude
open import Game.Core using ({player})
open import Othello.Statements using ({goal})
import Othello.RowPacked6 as Packed
import Othello.TextCertifiedAssembly6 as Box
import {data}.Root as Global
import {closure} as Closure
module Parts = Box.Assembly {player} ({goal} 4)
'''
        for g in range(groups):body+=f'import {data}.Group{g} as G{g}\n'
        for g in range(groups):
            if g not in owned:body+=f'import {prefix}.Rows{g} as P{g}\n'
        if upper:
            body+='import Tests.ParametricFullUpper6.Samples as Old\nimport Tests.TextUpperHoldout6.Rows500 as Existing500\n'
        else:body+='import Tests.TextLowerPacked6.Samples as Old\n'
        body+='''module Generic (G : ℕ → Packed.PackedState) where
  module Target = Closure.Generic G
  abstract
    assemble :
'''
        for g in range(groups):body+=f'      Parts.Certified G G{g}.table →\n'
        body+='      Target.CheckedParts\n    assemble '+' '.join('p'+str(g) for g in range(groups))+' = record\n      { '
        body+='\n      ; '.join(f'part{g} = p{g}' for g in range(groups))+'\n      }\n'
        body+='''module Actual = Generic Global.G
abstract
  checked : Closure.Actual.CheckedParts
  checked = Actual.assemble
'''
        for g in range(groups):
            value=('Old.part6' if g==6 else 'Old.part652' if g==652 else 'Existing500.certified') if upper and g in owned else ('Old.training' if g==6 else 'Old.heldout') if not upper and g in owned else f'P{g}.certified'
            body+='    '+value+'\n'
        add(saved,'AllParts',body)
        if upper:
            add(saved,'Result','''open import Othello.Statements using (Problem2)
import Tests.TextLowerPacked6.Joint as Joint
import Tests.CompleteUpperRows6.AllParts as Upper
import Tests.CompleteLowerRows6.AllParts as Lower
abstract
  initial6x6 : Problem2
  initial6x6 = Joint.complete Lower.checked Upper.checked
-- This source asserts no success receipt: all imported rows must first be checked.
''')
    assert source_bytes<512*2**20 and len(entries)<2000
    # Independently read all emitted text back. This is integrity, not a mathematical check.
    with zipfile.ZipFile(archive) as saved:
        assert set(saved.namelist())==set(entries)
        for name,e in entries.items():assert hashlib.sha256(saved.read(name)).hexdigest()==e['sha256']
    h=hashlib.sha256()
    with archive.open('rb') as stream:
        for block in iter(lambda:stream.read(2**20),b''):h.update(block)
    source_hash=digest_entries({n:e['sha256'] for n,e in entries.items()})
    manifest=dict(format='othello-complete-row-source-package-v1',finished_utc=utc(),bound=bound,prefix=prefix,
        archive=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=h.hexdigest(),entries=entries,
        source_identity=dict(source_sha256=source_hash,agda_source_sha256=source_hash,source_files=len(entries),revision=None,dirty=None),
        interfaces={},interface_pool_sha256=digest_entries({}),raw_bytes=source_bytes,
        source_module_count=len(entries),full_state_rows=total,total_group_fields=groups,already_owned_groups=sorted(owned),
        emitted_new_group_fields=written_groups,emitted_owner_rows=total-len(owned)*10000,
        emitted_tokens=total_emitted_tokens,cases=cases,index_states=len(index),index_cpu_seconds=index_cpu,
        selected_conversion_cpu_seconds=conversion_cpu,second_scan_conversion_compression_cpu_seconds=time.process_time()-start,
        authenticated_full_wire_scans=2,input_unchanged=True,streamed_groups_instead_of_whole_body_corpus=True,
        new_native_solver_runs=0,new_game_row_checks=0,checked_full_map_records_not_yet_inhabited=True,
        recovered_partial_archive_sha256=parent_hash,reused_group_count=len(reused),
        reused_source_bytes_preserved=True,original_failed_cpu_not_reset=True,
        production_go=False,mathematical_objective_complete=False)
    atomic_json(out/'archive-manifest.json',manifest)


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
