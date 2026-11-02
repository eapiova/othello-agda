#!/usr/bin/env python3
"""Independent scalar replay and fail-closed guards for the C wire exporter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

import canonical_census6
import census_wire6 as wire
import compact_shared6 as compact
import global_shared6 as shared
import global_assembly6 as assembly
import ref
from run_job import atomic_json, utc
import solve6
import symmetry_stats6 as symmetry
import test_canonical_census6 as scalar


def decode_state(key):
    return wire.line_pins6.state(key[1:], 'black' if key[0]=='b' else 'white')


def references(text, state):
    """Read citation targets along scalar successors, independently of C."""
    found=set()
    def parse(offset,s):
        token=text[offset];offset+=1
        if token=='K':found.add(s);return offset
        if token=='L':return offset
        if token=='P':return parse(offset,ref.successors(s)[0])
        end=text.index(';',offset);n=int(text[offset:end]);offset=end+1
        if token=='R':found.add(symmetry.transform(s,n));return offset
        children=ref.successors(s)
        if token=='C':return parse(offset,children[n])
        if token!='F' or n!=len(children):raise AssertionError('wrong constructor or reply count')
        for child in children:offset=parse(offset,child)
        return offset
    assert parse(0,state)==len(text)
    return found


def command(binary,case,path):
    return [str(binary),'wire','--position',case['position'],'--turn','white' if case['turn']==ref.WHITE else 'black',
        '--direction',case['direction'],'--threshold',str(case['threshold']),'--frontier-discs','36',
        '--max-states','10000','--max-nodes','10000000','--max-memory-mb','16','--max-cpu-seconds','2',
        '--tt-bits','4','--small','4','--deep-order','5','--emit-states','0',
        '--wire-output',str(path),'--wire-limit-mib','1']


def run(args, *, build_validator=wire.checked_build, source_generator=wire.generated_source,
        max_body_tokens=None, native_options=()):
    built,binary=build_validator(args.build)
    if built.get('pins'):raise ValueError('reference-counter test requires the unpinned build')
    reference_report,reference=canonical_census6.checked_build(args.reference_build)
    source_report=args.output.with_name(args.output.stem+'-scalar.json')
    scalar.run(SimpleNamespace(build=args.reference_build,output=source_report,reference_build=None))
    cases=json.loads(source_report.read_text())['late_cases']
    accepted=failed=entries=tokens=ref_count=0;tags=set()
    directory=args.output.parent/'wire-fixtures';directory.mkdir(parents=True,exist_ok=False)
    for index,case in enumerate(cases):
        path=directory/f'{index}.partial'
        original=command(binary,case,path);argv=[*original,*native_options]
        done=subprocess.run(argv,capture_output=True,text=True,timeout=10)
        result=json.loads(done.stdout)
        baseline=subprocess.run([str(reference),'frontier',*original[2:-4]],
            capture_output=True,text=True,timeout=10)
        # --wire-output and --wire-limit-mib are absent from the baseline.
        assert baseline.returncode==0,baseline.stderr
        comparison=json.loads(baseline.stdout)
        for field in ('complete','root_validated','root_holds','tree_nodes_S','unique_dag_nodes','dag_edges','dedup_hits'):
            assert result[field]==comparison[field],field
        if not case['holds']:
            assert done.returncode!=0 and not result['wire_complete'] and not path.exists();failed+=1;continue
        assert done.returncode==0 and result['wire_complete'],done.stderr
        rows=list(wire.records(path));known=set();known_keys=set();proofs=[]
        root=ref.State(6,tuple(map(int,case['position'])),case['turn'])
        for key,text,cited in rows:
            if max_body_tokens is not None:assert assembly.tokens(text)<=max_body_tokens
            state=decode_state(key)
            assert state not in known and cited <= known_keys
            actual=references(text,state)
            assert {decode_state(r) for r in cited}==actual
            assert actual <= known
            known.add(state);known_keys.add(key);proofs.append((state,text))
            for i,c in enumerate(text):
                if c=='R':tags.add(int(text[i+1:text.index(';',i+1)]))
        assert shared.replay_many(proofs,[root],case['direction'],case['threshold'])
        assert result['wire_bytes']==path.stat().st_size
        actual_tokens=sum(sum(c in 'LCFPKR' for c in text) for _,text,_ in rows)
        assert result['wire_tokens']==actual_tokens
        assert result['wire_records']==len(rows)
        actual_refs=sum(text.count('K')+text.count('R') for _,text,_ in rows)
        assert result['wire_references']==actual_refs
        accepted+=1;entries+=len(rows);tokens+=actual_tokens;ref_count+=actual_refs
    # Explicit pass and all D4 images exercise transported choice indices.
    state=ref.State(6,tuple(map(int,'210222'+'2'*30)),ref.BLACK)
    value=ref.value(state)
    for tag in range(8):
        s=ref.State(6,scalar.image(state.cells,tag),state.turn)
        case=dict(position=''.join(map(str,s.cells)),turn=s.turn,direction='upper',threshold=value)
        path=directory/f'pass{tag}.partial';done=subprocess.run([*command(binary,case,path),*native_options],capture_output=True,text=True,timeout=10)
        result=json.loads(done.stdout);assert result['wire_complete'] and done.returncode==0
        rows=[(decode_state(k),t) for k,t,_ in wire.records(path)]
        assert shared.replay_many(rows,[s],'upper',value)
        assert any('P' in text for _,text in rows)
        for _,text in rows:
            for i,c in enumerate(text):
                if c=='R':tags.add(int(text[i+1:text.index(';',i+1)]))
    # Existing paths cannot be overwritten, truncated graphs cannot emit facts.
    good=next(c for c in cases if c['holds'])
    path=directory/'protected.partial';path.write_bytes(b'unchanged')
    done=subprocess.run(command(binary,good,path),capture_output=True,text=True,timeout=10)
    assert done.returncode!=0 and not json.loads(done.stdout)['wire_complete'] and path.read_bytes()==b'unchanged'
    path=directory/'fuel.partial';argv=command(binary,good,path)
    argv[argv.index('--max-states')+1]='1';argv[argv.index('--max-nodes')+1]='1'
    done=subprocess.run(argv,capture_output=True,text=True,timeout=10)
    assert done.returncode!=0 and not json.loads(done.stdout)['wire_complete'] and not path.exists()
    for options in (['wire'],['wire','--wire-output','x','--emit-states','1'],['wire','--wire-output','x','--wire-limit-mib','0']):
        done=subprocess.run([str(binary),*options],capture_output=True,text=True,timeout=10);assert done.returncode!=0
    # A legal but losing pinned choice must reject the graph. It must never
    # silently choose a different winning move from the existential search.
    bad=None
    for case in cases:
        if case['threshold']!=case['scalar_value'] or not case['holds']:continue
        s=scalar.canonical(ref.State(6,tuple(map(int,case['position'])),case['turn']))
        if s.turn!=(ref.WHITE if case['direction']=='lower' else ref.BLACK):continue
        children=ref.successors(s)
        if not ref.placements(s):continue
        for index,child in enumerate(children):
            v=ref.value(child)
            if (v<case['threshold'] if case['direction']=='lower' else v>case['threshold']):
                bad=(dict(case,position=''.join(map(str,s.cells))),
                     {case['direction']:[dict(state=('w' if s.turn==ref.WHITE else 'b')+''.join(map(str,s.cells)),selected_index=index)]})
                break
        if bad:break
    assert bad is not None,'negative pinned-choice fixture missing'
    bad_case,bad_pins=bad; source=directory/'losing-pin.c';source.write_text(source_generator(solve6.SOURCE.read_text(),bad_pins))
    bad_binary=directory/'losing-pin'
    compiled=subprocess.run([built['compiler'],*solve6.FLAGS,str(source),'-o',str(bad_binary)],capture_output=True,text=True,timeout=30)
    assert compiled.returncode==0,compiled.stderr
    path=directory/'losing-pin.partial'
    done=subprocess.run([*command(bad_binary,bad_case,path),*native_options],capture_output=True,text=True,timeout=10)
    result=json.loads(done.stdout)
    assert result['root_holds'] and not result['complete'] and not result['wire_complete'] and done.returncode!=0 and not path.exists()
    assert build_validator(args.build)[0]==built and tags==set(range(1,8))
    report=dict(format='othello-census-wire6-tests-v1',accepted=True,created_utc=utc(),
        build_sha256=solve6.sha256(args.build/'build.json'),reference_build_sha256=solve6.sha256(args.reference_build/'build.json'),
        reference_counter_cases=len(cases),complete_wire_graphs=accepted,false_bounds_rejected=failed,
        records_replayed=entries,tokens_replayed=tokens,citation_occurrences=ref_count,
        citation_tags=sorted(tags),forced_pass_images=8,invalid_or_protected_cases=5,losing_pin_rejected=True,
        max_body_tokens=max_body_tokens,
        trust='native/scalar validation; no Agda proof premise',production_authorized=False,initial_problem2_proved=False)
    atomic_json(args.output,report);print(json.dumps(report))


def pinned_run(args, *, build_validator=wire.checked_build, max_body_tokens=None, native_options=()):
    built,binary=build_validator(args.build)
    pins=built.get('pins')
    if not pins or built.get('line_sha256')!=solve6.sha256(Path('certificates/six-line.json')):
        raise ValueError('requires the exact legal-line pinned build')
    directory=args.output.parent/'pinned-fixtures';directory.mkdir(parents=True,exist_ok=False)
    count=entries=0;directions=set()
    for direction,rows in pins.items():
        for row in rows:
            root=decode_state(row['state'])
            if root.cells.count(0)>6:continue
            assert ref.value(root)==4
            chosen=ref.successors(root)[row['selected_index']]
            assert ref.value(chosen)==4
            for tag in range(8):
                s=ref.State(6,scalar.image(root.cells,tag),root.turn)
                case=dict(position=''.join(map(str,s.cells)),turn=s.turn,direction=direction,threshold=4)
                path=directory/f'{count}.partial'
                done=subprocess.run([*command(binary,case,path),*native_options],capture_output=True,text=True,timeout=10)
                result=json.loads(done.stdout);assert result['wire_complete'] and done.returncode==0,done.stderr
                records=list(wire.records(path));proofs=[(decode_state(k),t) for k,t,_ in records]
                if max_body_tokens is not None:
                    assert all(assembly.tokens(t)<=max_body_tokens for k,t,_ in records)
                assert shared.replay_many(proofs,[s],direction,4)
                # The canonical own root keeps the specified index, even when
                # another order would also meet the bound.
                text=next(t for k,t,_ in records if k==row['state'])
                assert text.startswith(f"C{row['selected_index']};")
                count+=1;entries+=len(records);directions.add(direction)
    assert count>=32 and directions=={'lower','upper'}
    report=dict(format='othello-census-wire6-pinned-tests-v1',accepted=True,created_utc=utc(),
        build_sha256=solve6.sha256(args.build/'build.json'),line_sha256=built['line_sha256'],
        complete_pinned_graphs=count,records_replayed=entries,directions=sorted(directions),
        scalar_value_at_late_roots=4,all_eight_D4_images=True,
        scope='late line roots only; full initial pinned graph and Agda joint play still unproved',
        production_authorized=False,initial_problem2_proved=False)
    atomic_json(args.output,report);print(json.dumps(report))


class CodecTests(unittest.TestCase):
    def test_stream_rejects_truncated_and_oversized_records(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'wire'
            for raw in (b'wQQQQQQQQQQQQ\tL\t',b'bQQQQQQQQQQQQ\tL\twQ\n',b'bQQQQQQQQQQQQ\tL\t\textra\n'):
                path.write_bytes(raw)
                with self.assertRaises(ValueError):list(wire.records(path))
            path.write_bytes(b'bQQQQQQQQQQQQ\tL\t\n')
            with self.assertRaises(ValueError):list(wire.records(path,max_record_bytes=10))

    def test_pin_validation_rejects_duplicates_and_noncanonical_states(self):
        line=json.loads(Path('certificates/six-line.json').read_text())
        pins=wire.line_pins6.plan(line)['pins']
        first=pins['lower'][0]
        with self.assertRaises(ValueError):wire.pin_source({'lower':[first,first]})
        bad=dict(first,selected_index=36)
        with self.assertRaises(ValueError):wire.pin_source({'lower':[bad]})

    def test_explicit_root_validation_precedes_donor_access(self):
        for position,turn in [('0'*35,'black'),('x'*36,'white'),('initial','red')]:
            with self.assertRaises(ValueError):
                canonical_census6.run(SimpleNamespace(),position=position,turn=turn)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path);p.add_argument('--reference-build',type=Path);p.add_argument('--output',type=Path);p.add_argument('--pinned',action='store_true')
    args=p.parse_args()
    if not args.build:unittest.main(argv=['test_census_wire6'])
    elif args.pinned and args.output:pinned_run(args)
    elif not args.reference_build or not args.output:p.error('native test needs reference-build/output')
    else:run(args)
