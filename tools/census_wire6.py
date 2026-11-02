#!/usr/bin/env python3
"""Untrusted, bounded child-first compact certificate export from native C.

The native graph stays in fixed-size C tables. Each output record is
compact-state TAB compact-certificate TAB concatenated compact-citations LF.
Only a complete export is renamed from .partial. Nothing here supplies an
Agda premise; every emitted record still needs the safe certificate checker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import canonical_census6 as base
import compact_shared6 as compact
import line_pins6
from run_job import atomic_json, utc
import solve6

DECLARATIONS = r'''
static int wire_enabled;
static const char *wire_path;
static size_t wire_byte_limit=16*1024*1024, wire_record_limit=1024*1024;
static uint32_t *wire_order, *wire_indegree;
static size_t wire_order_count;
static void wire_finished(size_t id) {
  if(wire_enabled) wire_order[wire_order_count++]=(uint32_t)id;
}
'''

EMITTER = r'''
static const unsigned char wire_inverse[8]={0,1,2,3,4,6,5,7};
static const unsigned char wire_agda_tag[8]={0,4,6,2,7,1,3,5};
static const char wire_counts[]="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_";
static int wire_canonical(u64 *P,u64 *O) {
  u64 p=*P,o=*O,bp=p,bo=o;int tag=0;
  for(int i=1;i<8;i++){u64 q=census_image(p,i),r=census_image(o,i);
    if(q<bp || (q==bp && r<bo)){bp=q;bo=r;tag=i;}}
  *P=bp;*O=bo;return tag;
}
static size_t wire_lookup(u64 P,u64 O,int turn,int lower,int threshold) {
  census_canonical(&P,&O);u64 key=census_key(P,O,turn);
  size_t slot=(size_t)(hashkey(P,O)^((u64)(threshold+36)<<2)^(u64)(turn*2+lower))&(prefix_slot_count-1);
  while(prefix_slots[slot]){size_t id=prefix_slots[slot]-1;
    if((prefix[id].key&CENSUS_STATE_MASK)==key)return id;
    slot=(slot+1)&(prefix_slot_count-1);}
  return SIZE_MAX;
}
static void wire_state(u64 P,u64 O,int turn,char out[14]) {
  char raw[37];encode(P,O,turn,raw);out[0]=turn?'w':'b';
  for(int j=0;j<12;j++)out[j+1]=wire_counts[9*(raw[3*j]-'0')+3*(raw[3*j+1]-'0')+raw[3*j+2]-'0'];
  out[13]=0;
}
/* Keep certificate and citation buffers bounded independently of the graph. */
typedef struct {char *data;size_t n,capacity,tokens;int ok;} WireBuffer;
static void wire_append(WireBuffer *b,const char *s,size_t n) {
  if(!b->ok)return;
  if(n>wire_record_limit-b->n){b->ok=0;return;}
  size_t want=b->n+n;
  if(want>b->capacity){size_t cap=b->capacity?b->capacity:256;
    while(cap<want && cap<wire_record_limit)cap*=2;
    if(cap>wire_record_limit)cap=wire_record_limit;
    char *p=realloc(b->data,cap);if(!p){b->ok=0;return;}b->data=p;b->capacity=cap;}
  memcpy(b->data+b->n,s,n);b->n+=n;
}
static void wire_char(WireBuffer *b,char c){wire_append(b,&c,1);}
static int wire_children(size_t id,int lower,int threshold,size_t children[36]) {
  if(prefix[id].key&CENSUS_LEAF)return 0;
  u64 P,O;int turn;census_unpack(prefix[id].key,&P,&O,&turn);
  u64 moves=gen_moves(P,O);int n=0,index=0;
  if(!moves){children[0]=wire_lookup(O,P,!turn,lower,threshold);return 1;}
  while(moves){u64 m=moves&-moves;moves^=m;
    if(turn!=lower || index==census_selected[id]){u64 f=gen_flips(P,O,m);
      children[n++]=wire_lookup(O^f,P^f^m,!turn,lower,threshold);}index++;}
  return n;
}
static void wire_body(u64 P,u64 O,int turn,int lower,int threshold,int top,int fuel,
                      WireBuffer *body,WireBuffer *refs) {
  if(!body->ok || !refs->ok)return;
  if(!fuel || oracle_stop()){body->ok=0;return;}
  u64 cp=P,co=O;int tag=wire_canonical(&cp,&co);
  size_t id=wire_lookup(cp,co,turn,lower,threshold);
  if(id==SIZE_MAX){body->ok=0;return;}
  body->tokens++;
  if(prefix[id].key&CENSUS_LEAF){wire_char(body,'L');return;}
  if(!top && (id==0 || wire_indegree[id]>=2)){
    if(tag){wire_char(body,'R');wire_char(body,'0'+wire_agda_tag[tag]);}
    else wire_char(body,'K');
    char packed[14];wire_state(cp,co,turn,packed);wire_append(refs,packed,13);return;
  }
  u64 moves=gen_moves(P,O);
  if(!moves){wire_char(body,'P');wire_body(O,P,!turn,lower,threshold,0,fuel-1,body,refs);return;}
  if(turn==lower){
    u64 canonical_moves=gen_moves(cp,co);unsigned int index=census_selected[id];
    if(index>= (unsigned int)popc(canonical_moves)){body->ok=0;return;}
    while(index--)canonical_moves^=canonical_moves&-canonical_moves;
    u64 m=census_image(canonical_moves&-canonical_moves,wire_inverse[tag]);
    if(!(moves&m) || (m&(m-1))){body->ok=0;return;}
    int actual_index=popc(moves&(m-1));u64 f=gen_flips(P,O,m);
    wire_char(body,'C');wire_char(body,wire_counts[actual_index]);
    wire_body(O^f,P^f^m,!turn,lower,threshold,0,fuel-1,body,refs);
  }else{
    wire_char(body,'F');wire_char(body,wire_counts[popc(moves)]);
    while(moves && body->ok && refs->ok){u64 m=moves&-moves;moves^=m;u64 f=gen_flips(P,O,m);
      wire_body(O^f,P^f^m,!turn,lower,threshold,0,fuel-1,body,refs);}
  }
}
static int wire_record(FILE *f,u64 P,u64 O,int turn,WireBuffer *body,WireBuffer *refs,
                       size_t *bytes,size_t *records) {
  size_t n=13+body->n+refs->n+3;char packed[14];
  if(!body->ok || !refs->ok || n>wire_record_limit || n>wire_byte_limit-*bytes)return 0;
  wire_state(P,O,turn,packed);
  if(fwrite(packed,1,13,f)!=13 || fputc('\t',f)==EOF ||
     (body->n && fwrite(body->data,1,body->n,f)!=body->n) || fputc('\t',f)==EOF ||
     (refs->n && fwrite(refs->data,1,refs->n,f)!=refs->n) || fputc('\n',f)==EOF)return 0;
  *bytes+=n;(*records)++;return 1;
}
static int wire_report(int complete,u64 rootP,u64 rootO,int rootTurn,int lower,int threshold) {
  if(!wire_enabled)return 1;
  int valid=complete && frontier_discs==36 && wire_order_count==prefix_count;
  size_t bytes=0,records=0;u64 tokens=0,references=0;
  if(valid)for(size_t i=0;i<prefix_count;i++){
    if((i&4095)==0 && oracle_stop()){valid=0;break;}
    size_t children[36];int n=wire_children(i,lower,threshold,children);
    if(!(prefix[i].key&CENSUS_LEAF) && !n){valid=0;break;}
    for(int j=0;j<n;j++){size_t c=children[j];
      if(c==SIZE_MAX || c==i || wire_indegree[c]==UINT32_MAX){valid=0;break;}
      wire_indegree[c]++;}if(!valid)break;
  }
  FILE *out=valid?fopen(wire_path,"wbx"):NULL;if(valid && !out)valid=0;
  WireBuffer body={.ok=1},refs={.ok=1};
  if(valid)for(size_t q=0;q<wire_order_count;q++){
    size_t id=wire_order[q];if(id!=0 && ((prefix[id].key&CENSUS_LEAF) || wire_indegree[id]<2))continue;
    u64 P,O;int turn;census_unpack(prefix[id].key,&P,&O,&turn);body.n=refs.n=0;body.tokens=0;
    wire_body(P,O,turn,lower,threshold,1,80,&body,&refs);
    if(!wire_record(out,P,O,turn,&body,&refs,&bytes,&records)){valid=0;break;}
    references+=refs.n/13;
    tokens+=body.tokens;
  }
  u64 cp=rootP,co=rootO;int rootTag=wire_canonical(&cp,&co);
  if(valid && rootTag){body.n=refs.n=0;wire_char(&body,'R');wire_char(&body,'0'+wire_agda_tag[rootTag]);
    char packed[14];wire_state(cp,co,rootTurn,packed);wire_append(&refs,packed,13);
    if(!wire_record(out,rootP,rootO,rootTurn,&body,&refs,&bytes,&records))valid=0;
    else{tokens++;references++;}}
  free(body.data);free(refs.data);
  if(out && fclose(out)!=0)valid=0;
  if(oracle_aborted)valid=0;
  printf(",\"wire_complete\":%s,\"wire_records\":%zu,\"wire_bytes\":%zu,\"wire_tokens\":%llu,\"wire_references\":%llu,\"wire_byte_limit\":%zu,\"wire_record_limit\":%zu",
    valid?"true":"false",records,bytes,(unsigned long long)tokens,(unsigned long long)references,wire_byte_limit,wire_record_limit);
  return valid;
}
'''

WRAPPER = r'''
#undef main
int main(int argc,char **argv) {
  if(argc<2 || strcmp(argv[1],"wire"))return wire_original_main(argc,argv);
  wire_enabled=1;argv[1]="frontier";int write=2;
  for(int i=2;i<argc;i++){
    if(!strcmp(argv[i],"--wire-output")){if(++i==argc || wire_path)return error("one wire output required");wire_path=argv[i];}
    else if(!strcmp(argv[i],"--wire-limit-mib")){int cap;if(++i==argc || !integer(argv[i],1,512,&cap))return error("invalid wire byte cap");wire_byte_limit=(size_t)cap*1024*1024;}
    else{if(!strcmp(argv[i],"--emit-states") && i+1<argc && strcmp(argv[i+1],"0"))return error("wire forbids JSON graph dump");argv[write++]=argv[i];}
  }
  if(!wire_path)return error("wire output required");
  return wire_original_main(write,argv);
}
'''


def pin_source(pins):
    """C-only choice hints; a pinned failure cannot fall back to another move."""
    rows = []
    for direction, items in (pins or {}).items():
        if direction not in ('lower', 'upper'):
            raise ValueError('invalid pinned direction')
        for item in items:
            s = line_pins6.state(item['state'][1:], 'black' if item['state'][0]=='b' else 'white')
            if s != line_pins6.ccanonical(s) or s.turn != (2 if direction=='lower' else 1):
                raise ValueError('pin must be a canonical own-turn state')
            i = item['selected_index']
            if type(i) is not int or not 0 <= i < 36:
                raise ValueError('invalid pinned index')
            mover_cells = [0 if c==0 else 1 if c==s.turn else 2 for c in s.cells]
            key = sum(c*3**j for j,c in enumerate(mover_cells)) | ((s.turn==2)<<58)
            rows.append((key, int(direction=='lower'), i))
    if len({(k,l) for k,l,i in rows}) != len(rows):
        raise ValueError('duplicate pinned state')
    data = ','.join(f'{{{k}ULL,{l},{i}}}' for k,l,i in rows) or '{0,0,0}'
    return (f'static const struct {{u64 key;int lower,index;}} wire_pins[]={{ {data} }};\n'
        f'static const size_t wire_pin_count={len(rows)};\n' + r'''
static int wire_pin(u64 P,u64 O,int turn,int lower) {
  if(!wire_enabled)return -1;u64 key=census_key(P,O,turn);
  for(size_t j=0;j<wire_pin_count;j++)if(wire_pins[j].key==key && wire_pins[j].lower==lower)return wire_pins[j].index;
  return -1;
}
static u64 wire_pick(u64 P,u64 O,u64 moves,int own,int turn,int lower) {
  int pin=own?wire_pin(P,O,turn,lower):-1;
  if(pin<0)return census_pick_move(P,O,moves,own);
  if(pin>=popc(moves)){prefix_incomplete=1;return 0;}
  while(pin--)moves^=moves&-moves;return moves&-moves;
}
''')


def generated_source(raw, pins=None):
    source = base.generated_source(raw, 'min-replies', True)
    # All changes stay in census instrumentation; original rules/solver/TT
    # definitions remain byte-identical, as enforced by the base generator.
    patches = [
        (base.COMPACT_STATE, DECLARATIONS + base.COMPACT_STATE),
        (base.VISIT, pin_source(pins) + '\n' + base.VISIT),
        ('s->key&=~CENSUS_ACTIVE; return id;', 's->key&=~CENSUS_ACTIVE; wire_finished(id); return id;'),
        ('  s->key&=~CENSUS_ACTIVE; return id;', '  s->key&=~CENSUS_ACTIVE; wire_finished(id); return id;'),
        ('u64 m=census_pick_move(P,O,moves,own); moves^=m;',
         'u64 m=wire_pick(P,O,moves,own,turn,lower); if(!m)break; moves^=m;'),
        ('      if(oracle_aborted) { prefix_incomplete=1; break; }',
         '      if(own && wire_pin(P,O,turn,lower)>=0 && !selected) {prefix_incomplete=1;break;}\n      if(oracle_aborted) { prefix_incomplete=1; break; }'),
        ('static int integer(', EMITTER + '\nstatic int integer('),
        ('(emit_states?prefix_limit:0)', '((emit_states||wire_enabled)?prefix_limit:0)+(wire_enabled?2*prefix_limit*sizeof(uint32_t):0)'),
        ('(emit_states?(size_t)max_states:0)', '((emit_states||wire_enabled)?(size_t)max_states:0)+(wire_enabled?2*(size_t)max_states*sizeof(uint32_t):0)'),
        ('census_selected=emit_states?calloc(prefix_limit,1):NULL;',
         'census_selected=(emit_states||wire_enabled)?calloc(prefix_limit,1):NULL;\n    if(wire_enabled){wire_order=calloc(prefix_limit,sizeof(uint32_t));wire_indegree=calloc(prefix_limit,sizeof(uint32_t));wire_order_count=0;}\n    if(wire_enabled && (!wire_order || !wire_indegree))return error("cannot allocate wire tables");'),
        ('(emit_states && !census_selected)', '((emit_states||wire_enabled) && !census_selected)'),
        ('    if(emit_states) {', '    int wire_ok=wire_report(complete,P,O,white_turn,lower,threshold);\n    if(emit_states) {'),
        ('free(census_selected);', 'free(census_selected);free(wire_order);free(wire_indegree);wire_order=NULL;wire_indegree=NULL;'),
        ('    return complete ? 0 : 1;', '    return complete && wire_ok ? 0 : 1;'),
        ('    run_frontier(P,O,white_turn,direction,threshold,max_states,max_nodes,max_memory_mb,max_cpu_seconds,emit_states,ttbits,start);',
         '    int wire_rc=run_frontier(P,O,white_turn,direction,threshold,max_states,max_nodes,max_memory_mb,max_cpu_seconds,emit_states,ttbits,start);'),
        ('    free(tt); return 0;\n  } else\n  if (!strcmp(cmd,"tt-selftest"))',
         '    free(tt); return wire_enabled?wire_rc:0;\n  } else\n  if (!strcmp(cmd,"tt-selftest"))'),
        ('int main(int argc,char **argv) {', 'int wire_original_main(int argc,char **argv) {')]
    # The terminal and nonterminal finalizers share a substring. Replace the
    # longer line first, then the exact terminal line rather than double-patching.
    patches[2:4] = [
        ('\n    s->key&=~CENSUS_ACTIVE; return id;', '\n    s->key&=~CENSUS_ACTIVE; wire_finished(id); return id;'),
        ('\n  s->key&=~CENSUS_ACTIVE; return id;', '\n  s->key&=~CENSUS_ACTIVE; wire_finished(id); return id;')]
    for old,new in patches:
        if source.count(old) != 1:
            raise ValueError('wire instrumentation layout differs: '+old[:80])
        source = source.replace(old,new,1)
    restored = source
    for old,new in reversed(patches):
        restored = restored.replace(new,old,1)
    if restored != base.generated_source(raw, 'min-replies', True):
        raise ValueError('wire delta changes unrelated source bytes')
    return source + WRAPPER


def build(args):
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    line = json.loads(args.line.read_text()) if args.line else None
    pins = line_pins6.plan(line)['pins'] if line else None
    source = output/'census.c'; source.write_text(generated_source(solve6.SOURCE.read_text(), pins))
    cc = Path(shutil.which('cc')).resolve(strict=True); binary = output/'census'
    command = [str(cc), *solve6.FLAGS, str(source), '-o', str(binary)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if done.returncode: raise ValueError(done.stderr)
    report = dict(format='othello-census-wire6-build-v1', status='complete', created_utc=utc(),
        reference_source_sha256=solve6.sha256(solve6.SOURCE), source_sha256=solve6.sha256(source),
        binary=str(binary), binary_sha256=solve6.sha256(binary), compiler=str(cc),
        compiler_sha256=solve6.sha256(cc), flags=list(solve6.FLAGS), command=command,
        compile_stderr=done.stderr, pins=pins, line_sha256=solve6.sha256(args.line) if args.line else None,
        solver_rules_tt_bytes_unchanged=True, witness_policy='min-replies with fail-closed optional line pins',
        compact_memo=True, production_authorized=False, initial_problem2_proved=False)
    atomic_json(output/'build.json', report)
    print(json.dumps(dict(status='complete', binary_sha256=report['binary_sha256'])))


def checked_build(path):
    path=path.resolve(); report=json.loads((path/'build.json').read_text())
    expected=generated_source(solve6.SOURCE.read_text(),report.get('pins')).encode()
    binary=Path(report['binary'])
    if (report.get('format')!='othello-census-wire6-build-v1' or report.get('status')!='complete' or
            report.get('solver_rules_tt_bytes_unchanged') is not True or
            report['reference_source_sha256']!=solve6.sha256(solve6.SOURCE) or
            report['source_sha256']!=hashlib.sha256(expected).hexdigest() or
            (path/'census.c').read_bytes()!=expected or report['binary_sha256']!=solve6.sha256(binary)):
        raise ValueError('wire build provenance changed')
    return report,binary


def records(path, *, max_record_bytes=1048576):
    """Stream bounded records, rejecting malformed keys, grammar and refs."""
    with path.open('rb') as stream:
        while raw:=stream.readline(max_record_bytes+1):
            if len(raw)>max_record_bytes or not raw.endswith(b'\n'):
                raise ValueError('oversized or truncated wire record')
            pieces=raw[:-1].decode('ascii').split('\t')
            if len(pieces)!=3: raise ValueError('invalid wire record fields')
            packed, certificate, refs=pieces
            key=compact.unpack_state(packed); text=compact.unpack_certificate(certificate)
            if len(refs)%13: raise ValueError('truncated wire references')
            yield key,text,{compact.unpack_state(refs[j:j+13]) for j in range(0,len(refs),13)}


def run(args, *, build_validator=None, extra_native_options=()):
    """Reuse exact donor provenance, with native output kept behind a cap."""
    output=args.wire_output.resolve()
    if output.exists() or 'results' not in output.parts or not 1<=args.wire_limit_mib<=512:
        raise ValueError('requires a fresh bounded results artifact')
    partial=output.with_name(output.name+'.partial')
    if partial.exists():raise ValueError('partial artifact already exists')
    output.parent.mkdir(parents=True,exist_ok=True); args.output.parent.mkdir(parents=True,exist_ok=True)
    root=args.root_key
    if root=='initial':position,turn='initial','black'
    else:
        compact.pack_state(root)
        position,turn=root[1:],'black' if root[0]=='b' else 'white'
    executed=[]
    def native(command,**kwargs):
        command=[command[0],'wire',*command[2:],'--wire-output',str(partial),
            '--wire-limit-mib',str(args.wire_limit_mib),*extra_native_options]
        executed.extend(command)
        return subprocess.run(command,**kwargs)
    base.run(args,build_validator=checked_build if build_validator is None else build_validator,
        execute_native=native,position=position,turn=turn)
    report=json.loads(args.output.read_text()); counts=report['counts']
    complete=(report['native_complete'] and counts.get('wire_complete') is True and
              partial.is_file() and partial.stat().st_size==counts['wire_bytes'] and
              partial.stat().st_size<=args.wire_limit_mib*1024**2)
    report.update(format='othello-census-wire6-run-v1',command=executed,root_key=root,
        status='complete-untrusted-wire' if complete else 'incomplete-untrusted-wire',
        wire_complete=complete,wire_output=str(output if complete else partial),
        wire_output_sha256=solve6.sha256(partial) if partial.is_file() else None,
        pins_require_kernel_line_validation=True,initial_problem2_proved=False,
        production_authorized=False)
    if complete:partial.rename(output)
    atomic_json(args.output,report)
    return complete


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('mode',choices=('build','run'))
    p.add_argument('--output',type=Path,required=True); p.add_argument('--line',type=Path)
    p.add_argument('--build',type=Path);p.add_argument('--tests',type=Path);p.add_argument('--donor',type=Path)
    p.add_argument('--root-key',default='initial');p.add_argument('--wire-output',type=Path)
    p.add_argument('--wire-limit-mib',type=int,default=16);p.add_argument('--max-states',type=int,default=1000000)
    p.add_argument('--native-cpu',type=int,default=120);p.add_argument('--direction',choices=('lower','upper'),default='lower')
    args=p.parse_args()
    if args.mode=='build':build(args)
    elif not all((args.build,args.tests,args.donor,args.wire_output)):p.error('run requires build/tests/donor/wire-output')
    elif not 1<=args.native_cpu<=7200:p.error('invalid native CPU cap')
    else:raise SystemExit(0 if run(args) else 1)
