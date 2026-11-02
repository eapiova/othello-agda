#!/usr/bin/env python3
"""Stream a bounded native wire into safe Agda shards and check a real root.

Native data is independently replayed with scalar rules while streaming.
Generated modules remain in results. The existing safe shard checker checks
every entry, citation, export shape and original-rule guarantee again.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import census_pilot6 as pilot
import census_wire6 as wire
import compact_shared6 as compact
import explicit_exports6
from generate6 import encode_state
import global_assembly6 as assembly
import ref
from run_job import atomic_json
import shared6
import symmetry_stats6 as symmetry

FORMAT='othello-wire-pilot6-v1'
PREFIX='Tests.WirePilot6'


def state(key):
    symmetry.validate_key(key)
    return ref.State(6,tuple(map(int,key[1:])),ref.BLACK if key[0]=='b' else ref.WHITE)


def validate_entry(key,text,cited,known,direction):
    """Exact rules, chosen index, all replies, pass and cited full states."""
    target=shared6.forcing_player(direction);found=set()
    def parse(offset,s,fuel):
        if not fuel or offset>=len(text):raise ValueError('truncated or excessive certificate')
        token=text[offset];offset+=1
        if token=='K':
            name=encode_state(s)
            if name not in known:raise ValueError('missing or forward identity citation')
            found.add(name);return offset
        if token=='R':
            end=text.index(';',offset);tag=int(text[offset:end])
            if not 0<=tag<8:raise ValueError('invalid D4 citation tag')
            name=encode_state(symmetry.transform(s,tag))
            if name not in known:raise ValueError('missing or forward D4 citation')
            found.add(name);return end+1
        children=ref.successors(s)
        if token=='L':
            if children or not shared6.score_ok(s,direction,4):raise ValueError('wrong terminal goal')
            return offset
        if token=='P':
            if ref.placements(s) or len(children)!=1:raise ValueError('incorrect forced pass')
            return parse(offset,children[0],fuel-1)
        if token not in 'CF':raise ValueError('unsupported wire constructor')
        end=text.index(';',offset);n=int(text[offset:end]);offset=end+1
        if token=='C':
            if not ref.placements(s) or s.turn!=target or not 0<=n<len(children):
                raise ValueError('wrong chosen move or player')
            return parse(offset,children[n],fuel-1)
        if not ref.placements(s) or s.turn==target or not children or n!=len(children):
            raise ValueError('missing opponent reply or incorrect fork')
        for child in children:offset=parse(offset,child,fuel-1)
        return offset
    if key in known or parse(0,state(key),80)!=len(text) or found!=cited:
        raise ValueError('duplicate entry, trailing data or dishonest citation list')


def emit(args):
    output=args.output.resolve()
    if output.exists() or 'results' not in output.parts:raise ValueError('fresh isolated results output required')
    raw=args.report.read_bytes();native=json.loads(raw)
    if (native.get('format')!='othello-census-wire6-run-v1' or
            native.get('wire_complete') is not True or native.get('native_complete') is not True or
            native.get('status')!='complete-untrusted-wire' or
            not native.get('donor_unchanged') or not native.get('table_unchanged') or
            wire.solve6.sha256(args.wire)!=native['wire_output_sha256']):
        raise ValueError('requires a complete immutable wire and protected donor')
    direction=native['request']['direction']
    if direction not in ('lower','upper') or native['request']['threshold']!=4:
        raise ValueError('wrong bound')
    root=native['root_key']
    if root=='initial':root=encode_state(ref.initial(6))
    state(root)
    output.mkdir(parents=True);owners={};parts=[];ancestors=[];targets=[];hashes={};part=[];count=0
    namespace=PREFIX+'.'+direction.capitalize();source_bytes=0
    def save(name,text):
        nonlocal source_bytes
        source_bytes+=len(text.encode())
        if source_bytes>getattr(args,'max_total_source_bytes',8388608):raise ValueError('total source byte cap')
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        hashes[name]=hashlib.sha256(text.encode()).hexdigest()
    def flush():
        nonlocal part,count
        if not part:return
        index=len(parts)
        source,deps,wire_bytes=assembly.part_source(index,part,owners,direction)
        # Already kernel-tested compact table representation: dummy L tokens
        # parse states only; they never replace the actual entry certificates.
        source=explicit_exports6.pack_tables(source)
        source=source.replace('  shape = refl\n','  shape = refl {x = states}\n')
        source=pilot.private_source(source.replace(assembly.PREFIX,namespace))
        if len(source.encode())>args.max_source_bytes:raise ValueError('source byte cap')
        closure=set(deps)
        for dep in deps:closure.update(ancestors[dep])
        ancestors.append(closure)
        path='src/'+namespace.replace('.','/')+f'/Part{index}.agda'
        save(path,source)
        cited={r for e in part for r in e['references'] if owners[r]!=index}
        targets.append(dict(path=path,kind='part',root_index=0,part=index,
            entries=len(part),tokens=count,compact_bytes=wire_bytes,source_bytes=len(source.encode()),
            dependencies=deps,imported_citations=len(cited),transitive_parts=len(closure),
            transitive_entries=sum(parts[j] for j in closure)))
        parts.append(len(part));part=[];count=0
    for key,text,cited in wire.records(args.wire):
        if len(owners)>=args.max_records:raise ValueError('bounded pilot record cap')
        validate_entry(key,text,cited,owners,direction)
        size=assembly.tokens(text)
        if size>args.max_tokens:raise ValueError('one entry exceeds token cap')
        if part and (count+size>args.max_tokens or len(part)>=args.max_entries):flush()
        owners[key]=len(parts)
        part.append(dict(state=key,certificate=text,references=sorted(cited)));count+=size
    flush()
    if root not in owners or len(owners)!=native['counts']['wire_records']:
        raise ValueError('missing requested root or record count differs')
    # No unreachable suffix may hide a wrong declared root. Native wire order
    # ends with the actual requested root, including an orientation alias.
    if key!=root:raise ValueError('wire ends at a different root')
    path='src/'+namespace.replace('.','/')+'/Check.agda'
    source=pilot.private_source(assembly.assembly_source([root],owners,direction).replace(assembly.PREFIX,namespace))
    save(path,source);owner=owners[root];closure=ancestors[owner]|{owner}
    targets.append(dict(path=path,kind='assembly',root_index=0,source_bytes=len(source.encode()),
        transitive_parts=len(closure),transitive_entries=sum(parts[j] for j in closure)))
    report=dict(format=FORMAT,status='emitted-unchecked',accepted=False,roots=[dict(index=0,phase='training',key=root,
        direction=direction,native_nodes=native['counts']['unique_dag_nodes'],entries=len(owners),
        checked_tokens=sum(t['tokens'] for t in targets if t['kind']=='part'))],targets=targets,generated_hashes=hashes,
        native_report_sha256=hashlib.sha256(raw).hexdigest(),wire_sha256=native['wire_output_sha256'],
        scalar_replay_complete=True,packed_export_tables=True,max_tokens=args.max_tokens,max_entries=args.max_entries,
        scope='one bounded conditional root; no full initial theorem or production GO',
        total_generated_source_bytes=source_bytes,initial_theorem_proved=False,production_authorized=False)
    atomic_json(output/'plan.json',report)
    print(json.dumps(dict(status=report['status'],entries=len(owners),parts=len(parts),root=root)))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    e=sub.add_parser('emit')
    for name in ('wire','report','output'):e.add_argument('--'+name,type=Path,required=True)
    e.add_argument('--max-tokens',type=int,default=32000);e.add_argument('--max-entries',type=int,default=500)
    e.add_argument('--max-records',type=int,default=20000);e.add_argument('--max-source-bytes',type=int,default=1048576)
    e.add_argument('--max-total-source-bytes',type=int,default=8388608)
    c=sub.add_parser('check')
    for name in ('prepared','donor','output'):c.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-plan-sha256','expected-hostname','expected-agda-sha256','expected-donor-source-sha256','expected-generic-interfaces-sha256'):
        c.add_argument('--'+name,required=True)
    c.add_argument('--kernel-cpu-budget',type=float,default=1200);c.add_argument('--part-cpu-limit',type=float,default=120)
    c.add_argument('--assembly-cpu-limit',type=float,default=180)
    args=p.parse_args()
    if args.command=='emit':
        if any(not 0<v<=2000000 for v in (args.max_tokens,args.max_entries,args.max_records,args.max_source_bytes)):
            p.error('invalid bounded pilot caps')
        if not 0<args.max_total_source_bytes<=33554432:p.error('invalid total source byte cap')
        emit(args);return 0
    args.phase='training';args.forecast=None;args.training_report=None;args.expected_forecast_sha256=None
    return 0 if pilot.check(args,required_roots=1,expected_format=FORMAT) else 1


if __name__=='__main__':raise SystemExit(main())
