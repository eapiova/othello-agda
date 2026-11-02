#!/usr/bin/env python3
"""UNTRUSTED streaming state-map sources for a full-dimension import pilot.

This reads an already exported, SHA-pinned native wire. It runs no solver or
Agda, checks no game certificate, and supplies no initial-board theorem. Reused
state literals must match the wire exactly; callers must pin and lock their
accepted same-machine source/interface donors separately.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

from compact_shared6 import TRIPLES
from nat_indexed_pilot6 import HEADER
from run_job import atomic_json
from wire_workflow6 import require

MAX_ROWS = 8_000_000
ROWS_PER_PART = 200
MAX_RECORD_BYTES = 1024**2


def _namespace(value):
    require(isinstance(value, str) and len(value) <= 240 and
            re.fullmatch(r'Tests\.[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*){0,13}', value),
            'bounded Tests namespace required')
    return value


def generate(wire, check, *, expected_sha256, expected_rows, expected_parts,
             prefix, reuse=None, map_batch=32, max_source_bytes=256*1024**2):
    """Emit fresh data sources; only safe Agda can accept their later use.

    ``reuse[j]`` is {module, text_sha256}. Its module must export String ``text``.
    The manifest records these external dependencies without copying any cache.
    Bounds here match the measured 200-row layouts, whose token cap never splits
    a full part early. A different partition must use a different converter.
    Failed runs retain their generated prefix with complete=false, never Root.
    """
    _namespace(prefix)
    require(type(expected_rows) is int and 1 <= expected_rows <= MAX_ROWS,
            'bounded full-layout row count required')
    require(type(expected_parts) is int and expected_parts == (expected_rows+199)//200,
            'only contiguous 200-row partition supported')
    require(isinstance(expected_sha256, str) and re.fullmatch('[0-9a-f]{64}', expected_sha256),
            'pinned whole-wire SHA256 required')
    require(type(map_batch) is int and 1 <= map_batch <= 64,
            'map batch must be between one and sixty-four')
    require(type(max_source_bytes) is int and 1 <= max_source_bytes <= 512*1024**2,
            'bounded source output required')
    reuse = {} if reuse is None else dict(reuse)
    for j, item in reuse.items():
        require(type(j) is int and 0 <= j < expected_parts and isinstance(item, dict)
                and set(item) == {'module', 'text_sha256'}, 'invalid reused chunk')
        _namespace(item['module'])
        require(not item['module'].startswith(prefix+'.') and item['module'] != prefix,
                'reuse must be outside the fresh namespace')
        require(isinstance(item['text_sha256'],str) and re.fullmatch('[0-9a-f]{64}',item['text_sha256']),
                'pinned reused state literal required')
    wire, check = Path(wire).absolute(), Path(check).absolute()
    require(wire == wire.resolve() and check == check.resolve()
            and not any(p.is_symlink() for p in (wire,*wire.parents,check,*check.parents)),
            'real nonsymlink paths required')
    require(wire.is_file() and not check.exists() and 'results' in check.parts,
            'existing input and fresh private results root required')
    library=(Path(__file__).resolve().parents[1]/'othello.agda-lib').read_bytes()
    require(len(library)<=max_source_bytes,'source byte cap excludes project library')
    check.mkdir(parents=True)
    (check/'othello.agda-lib').write_bytes(library)
    report = dict(format='othello-full-state-map6-v1', complete=False,
        wire_sha256=expected_sha256, expected_rows=expected_rows,
        expected_parts=expected_parts, prefix=prefix, rows_per_part=200,
        map_batch=map_batch, max_source_bytes=max_source_bytes,
        generated_sha256={'othello.agda-lib':hashlib.sha256(library).hexdigest()},
        generated_bytes=len(library), reused_chunks={},
        agda_checked=False, game_rows_checked=0, initial_problem2_proved=False,
        optimal_initial_pair_proved=False, production_authorized=False)
    metadata = check/'results/full-state-map6.json'
    metadata.parent.mkdir()
    atomic_json(metadata,report)
    folder = 'src/'+prefix.replace('.','/')+'/'
    chunks = []

    def emit(name, body):
        relative=folder+name+'.agda'
        raw=(HEADER+'-- UNTRUSTED state-map data only; no game proof.\nmodule '
             +prefix+'.'+name+' where\n\n'+body).encode()
        require(report['generated_bytes']+len(raw)<=max_source_bytes,
                'source byte cap reached; incomplete prefix preserved')
        path=check/relative;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
        report['generated_sha256'][relative]=hashlib.sha256(raw).hexdigest()
        report['generated_bytes']+=len(raw)

    def chunk(text):
        j=len(chunks);n=len(text)//13
        require(j<expected_parts and n==min(200,expected_rows-200*j),
                'wire partition differs from pinned full layout')
        digest=hashlib.sha256(text.encode()).hexdigest()
        if j in reuse:
            require(reuse[j]['text_sha256']==digest,'reused state literal differs from wire')
            module=reuse[j]['module'];report['reused_chunks'][str(j)]=reuse[j]
        else:
            module=prefix+'.StateData'+str(j)
            emit('StateData'+str(j),'open import Agda.Builtin.String using (String)\n\n'
                 +'text : String\ntext = "'+text+'"\n')
        chunks.append(dict(part=j,rows=n,module=module,text_sha256=digest))

    h=hashlib.sha256();buffer=[];count=0;last_state=None
    alphabet=set(TRIPLES.encode())
    with wire.open('rb') as stream:
        before=os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode),'regular wire input required')
        while True:
            raw=stream.readline(MAX_RECORD_BYTES+1)
            if not raw:break
            require(len(raw)<=MAX_RECORD_BYTES and raw.endswith(b'\n'),
                    'truncated or oversized wire record')
            h.update(raw);fields=raw[:-1].split(b'\t')
            require(len(fields)==3,'wire requires exactly three fields')
            state,body,refs=fields
            require(len(state)==13 and state[:1] in (b'b',b'w')
                    and all(c in alphabet for c in state[1:]),'invalid state literal')
            require(len(refs)%13==0,'invalid wire reference field length')
            count+=1;require(count<=expected_rows,'wire has extra rows')
            last_state=state.decode();buffer.append(last_state)
            if len(buffer)==200:chunk(''.join(buffer));buffer=[]
        after=os.fstat(stream.fileno())
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
            (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns), 'wire changed during conversion')
    require(count==expected_rows and h.hexdigest()==expected_sha256,
            'wire row count or digest differs; prefix is not complete')
    if buffer:chunk(''.join(buffer))
    require(len(chunks)==expected_parts,'missing state chunks')
    maps=[]
    common='import Game.NatMap as M\nopen import Othello.Board using (State; six)\n'

    def map_term(ids):
        if len(ids)==1:
            j=ids[0];return f'(M.rows {200*j} {chunks[j]["rows"]} (Lazy.states {chunks[j]["rows"]} S{j}.text))'
        middle=len(ids)//2
        return f'(M.branch {200*ids[middle]} {map_term(ids[:middle])} {map_term(ids[middle:])})'

    def tree(ids):
        if len(ids)<=map_batch:
            body=common+'import Othello.LazyIndexed6 as Lazy using (states)\n'
            body+=''.join(f'import {chunks[j]["module"]} as S{j} using (text)\n' for j in ids)
            expression=map_term(ids)
        else:
            middle=len(ids)//2;left=tree(ids[:middle]);right=tree(ids[middle:])
            body=common+f'import {prefix}.{left} as L using (stateMap)\nimport {prefix}.{right} as R using (stateMap)\n'
            expression=f'M.branch {200*ids[middle]} L.stateMap R.stateMap'
        name='Map'+str(len(maps));emit(name,body+'\nstateMap : M.Map (State six)\nstateMap = '+expression+'\n')
        maps.append(dict(module=prefix+'.'+name,first_part=ids[0],end_part=ids[-1]+1))
        return name

    top=tree(list(range(expected_parts)))
    emit('Root',common+f'import {prefix}.{top} as Top using (stateMap)\n\nstateMap : M.Map (State six)\nstateMap = Top.stateMap\n')
    report.update(complete=True,wire_sha256=h.hexdigest(),rows=count,parts=len(chunks),
        chunks=chunks,map_modules=maps,root_module=prefix+'.Root',last_encoded_state=last_state,
        borrowed_dependency_interfaces_copied=0)
    atomic_json(metadata,report)
    return report
