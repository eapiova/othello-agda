#!/usr/bin/env python3
"""Experimental native census with canonical positions before move selection.

The original solver/rules/TT code stays byte-identical. Generated C lives in
ignored results. All counts are untrusted, capped, and excluded from proofs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from full_dag_census6 import EXPECTED_TT, LABEL
from provenance import source_identity
from rewrite_dedup6 import closed
from run_job import atomic_json, utc
import solve6

D4 = r'''
/* Experimental census-only D4 normalization; solver and TT keys unchanged. */
static u64 census_horizontal(u64 x) {
  x=((x>>1)&0x5555555555555555ULL)|((x&0x5555555555555555ULL)<<1);
  x=((x>>2)&0x3333333333333333ULL)|((x&0x3333333333333333ULL)<<2);
  return ((x>>4)&0x0f0f0f0f0f0f0f0fULL)|((x&0x0f0f0f0f0f0f0f0fULL)<<4);
}
static u64 census_transpose(u64 x) {
  u64 t=(x^(x>>7))&0x00aa00aa00aa00aaULL; x^=t^(t<<7);
  t=(x^(x>>14))&0x0000cccc0000ccccULL; x^=t^(t<<14);
  t=(x^(x>>28))&0x00000000f0f0f0f0ULL; return x^t^(t<<28);
}
static u64 census_image(u64 x,int i) {
  if(i&4) x=census_transpose(x);
  if(i&2) x=__builtin_bswap64(x);
  if(i&1) x=census_horizontal(x);
  return x;
}
static void census_canonical(u64 *P,u64 *O) {
  u64 p=*P,o=*O,bp=p,bo=o;
  for(int i=1;i<8;i++) {
    u64 q=census_image(p,i),r=census_image(o,i);
    if(q<bp || (q==bp && r<bo)) {bp=q;bo=r;}
  }
  *P=bp;*O=bo;
}
'''

MIN_REPLIES = r'''
/* Census witness policy only. Every proposed choice still needs bound_holds. */
static u64 census_pick_move(u64 P,u64 O,u64 moves,int own) {
  if(!own) return moves&-moves;
  u64 best=0;int best_score=-10000;
  const u64 corners=(1ULL<<9)|(1ULL<<14)|(1ULL<<49)|(1ULL<<54);
  while(moves) {
    u64 m=moves&-moves;moves^=m;u64 f=gen_flips(P,O,m);
    int score=-4*popc(gen_moves(O^f,P^f^m)) + ((m&corners)?1:0);
    if(score>best_score) {best_score=score;best=m;}
  }
  return best;
}
'''

DRIVER = r'''
#undef main
int main(int argc,char **argv) {
  if(argc!=3 || strcmp(argv[1],"canonical")) return census_original_main(argc,argv);
  if(strlen(argv[2])!=36) return error("requires 36 cells");
  u64 P=0,O=0; REGION=0;
  for(int i=0;i<36;i++) {
    u64 m=1ULL<<sq(i); REGION|=m;
    if(argv[2][i]=='1') P|=m;
    else if(argv[2][i]=='2') O|=m;
    else if(argv[2][i]!='0') return error("invalid cell");
  }
  printf("{\"orbit\":[");
  for(int t=0;t<8;t++) {
    u64 p=census_image(P,t),o=census_image(O,t); char pos[37];encode(p,o,0,pos);
    printf("%s{\"position\":\"%s\",\"children\":[",t?",":"",pos);
    u64 moves=gen_moves(p,o);int first=1;
    if(!moves && gen_moves(o,p)) {printf("\"%s\"",pos);first=0;}
    while(moves) {
      u64 m=moves&-moves;moves^=m;u64 f=gen_flips(p,o,m);
      encode(p^f^m,o^f,0,pos);printf("%s\"%s\"",first?"":",",pos);first=0;
    }
    printf("]}");
  }
  census_canonical(&P,&O);char pos[37];encode(P,O,0,pos);
  printf("],\"canonical\":\"%s\"}\n",pos);return 0;
}
'''

VISIT = 'static size_t visit_prefix(u64 P,u64 O,int turn,int lower,int threshold) {\n'
MARKER = 'typedef struct {\n  u64 P, O, tree, hints;'
MOVE = '      u64 m=moves & -moves; moves^=m; u64 f=gen_flips(P,O,m);'
ORDERED_MOVE = ('      u64 m=census_pick_move(P,O,moves,own); moves^=m; '
                'u64 f=gen_flips(P,O,m);\n'
                '      index=popc(gen_moves(P,O)&(m-1));')

COMPACT_STATE = r'''typedef struct {
  u64 key, tree, hints;
} PrefixState;
/* 3^36 < 2^58. Bit 58 records the absolute player to move; the
 * threshold/direction are constant during a run_frontier invocation.
 * All 59 key bits are compared, so no fingerprint collision is accepted. */
#define CENSUS_STATE_MASK ((1ULL<<59)-1)
#define CENSUS_ACTIVE (1ULL<<63)
#define CENSUS_LEAF (1ULL<<62)
static unsigned char *census_selected;
static uint32_t census_row[4096];
static int census_row_ready;
static u64 census_key(u64 P,u64 O,int turn) {
  if(!census_row_ready) {
    for(int i=0;i<4096;i++) {
      uint32_t row=0,weight=1;
      for(int c=0;c<6;c++,weight*=3)
        row+=weight*((i&(1<<c))?1:((i&(1<<(c+6)))?2:0));
      census_row[i]=row;
    }
    census_row_ready=1;
  }
  u64 key=0,weight=1;
  for(int r=0;r<6;r++,weight*=729) {
    unsigned int p=(P>>(8*(r+1)+1))&63,o=(O>>(8*(r+1)+1))&63;
    key+=weight*census_row[p|(o<<6)];
  }
  return key|((u64)turn<<58);
}
static void census_unpack(u64 key,u64 *P,u64 *O,int *turn) {
  *P=*O=0;*turn=(int)((key>>58)&1);key&=(1ULL<<58)-1;
  for(int i=0;i<36;i++,key/=3) {
    if(key%3==1) *P|=1ULL<<sq(i);
    else if(key%3==2) *O|=1ULL<<sq(i);
  }
}
'''

COMPACT_VISIT = r'''static size_t visit_prefix(u64 P,u64 O,int turn,int lower,int threshold) {
  census_canonical(&P,&O);
  if (prefix_incomplete || oracle_stop()) { prefix_incomplete=1; return SIZE_MAX; }
  u64 key=census_key(P,O,turn);
  u64 h=hashkey(P,O) ^ ((u64)(threshold+36)<<2) ^ (u64)(turn*2+lower);
  size_t slot=(size_t)h & (prefix_slot_count-1);
  while (prefix_slots[slot]) {
    size_t id=prefix_slots[slot]-1; PrefixState *s=&prefix[id];
    if((s->key&CENSUS_STATE_MASK)==key) {
      prefix_repeats++;
      if(s->key&CENSUS_ACTIVE) prefix_incomplete=1;
      return id;
    }
    slot=(slot+1)&(prefix_slot_count-1);
  }
  if(prefix_count==prefix_limit) { prefix_incomplete=1; return SIZE_MAX; }
  size_t id=prefix_count++; prefix_slots[slot]=(uint32_t)(id+1);
  PrefixState *s=&prefix[id];
  *s=(PrefixState){.key=key|CENSUS_ACTIVE,.tree=1,.hints=0};
  if(census_selected) census_selected[id]=36;
  u64 moves=gen_moves(P,O);
  int terminal=!moves && !gen_moves(O,P);
  if(terminal || popc(P|O)>=frontier_discs) {
    s->key|=CENSUS_LEAF; prefix_leaves++;
    if(terminal) { int raw=turn ? popc(P)-popc(O) : popc(O)-popc(P);
      if (!(lower ? raw>=threshold : raw<=threshold)) prefix_incomplete=1; }
    s->key&=~CENSUS_ACTIVE; return id;
  }
  if(!moves) {
    prefix_edges++;
    size_t child=visit_prefix(O,P,!turn,lower,threshold);
    if(child!=SIZE_MAX) { s->tree=add_count(s->tree,prefix[child].tree); s->hints=prefix[child].hints; }
  } else {
    int own=turn==lower, selected=0;
    while(moves && !prefix_incomplete) {
      u64 m=census_pick_move(P,O,moves,own); moves^=m; u64 f=gen_flips(P,O,m);
      int index=popc(gen_moves(P,O)&(m-1));
      u64 cp=O^f, co=P^f^m;
      if(!own || bound_holds(cp,co,!turn,lower,threshold)) {
        if(own) { if(census_selected) census_selected[id]=(unsigned char)index; s->hints=1; selected=1; }
        prefix_edges++;
        size_t child=visit_prefix(cp,co,!turn,lower,threshold);
        if(child!=SIZE_MAX) { s->tree=add_count(s->tree,prefix[child].tree); s->hints=add_count(s->hints,prefix[child].hints); }
        if(own) break;
      }
      if(oracle_aborted) { prefix_incomplete=1; break; }
    }
    if(own && !selected) prefix_incomplete=1;
  }
  s->key&=~CENSUS_ACTIVE; return id;
}
'''


def compact_memo(source):
    """Change census storage/CLI only; keep solver, rules and full-key TT intact."""
    start = source.index(MARKER)
    end = source.index('static PrefixState *prefix;', start)
    visit_start = source.index(VISIT)
    visit_end = source.index('static int integer(', visit_start)
    patches = [(source[start:end], COMPACT_STATE),
               (source[visit_start:visit_end], COMPACT_VISIT + '\n'),
               ('prefix_slot_count*sizeof(uint32_t);',
                'prefix_slot_count*sizeof(uint32_t)+(emit_states?prefix_limit:0);'),
               ('slots*sizeof(uint32_t);', 'slots*sizeof(uint32_t)+(emit_states?(size_t)max_states:0);'),
               ('    if(!prefix || !prefix_slots)',
                '    census_selected=emit_states?calloc(prefix_limit,1):NULL;\n'
                '    if(!prefix || !prefix_slots || (emit_states && !census_selected))'),
               ('char pos[37]; PrefixState *s=&prefix[i]; encode(s->P,s->O,s->turn,pos);',
                'char pos[37]; PrefixState *s=&prefix[i]; u64 p,o;int turn; '
                'census_unpack(s->key,&p,&o,&turn); encode(p,o,turn,pos);'),
               ('i?",":"",pos,s->turn?"white":"black",s->lower?"lower":"upper",s->threshold,s->leaf?"true":"false",s->selected);',
                'i?",":"",pos,turn?"white":"black",lower?"lower":"upper",threshold,'
                '(s->key&CENSUS_LEAF)?"true":"false",census_selected[i]==36?-1:census_selected[i]);'),
               ('free(prefix); free(prefix_slots); prefix=NULL; prefix_slots=NULL;',
                'free(prefix); free(prefix_slots); free(census_selected); '
                'census_selected=NULL; prefix=NULL; prefix_slots=NULL;'),
               ('integer(v,1,100000000,&max_states)', 'integer(v,1,200000000,&max_states)')]
    changed = source
    for old,new in patches:
        if changed.count(old) != 1:
            raise ValueError('compact census layout differs: '+old[:80])
        changed = changed.replace(old,new,1)
    restored = changed
    for old,new in reversed(patches):
        restored = restored.replace(new,old,1)
    if restored != source:
        raise ValueError('compact delta changes unrelated source bytes')
    return changed


def generated_source(base, policy='row-major', compact=False):
    if policy not in ('row-major', 'min-replies'):
        raise ValueError('unsupported census witness policy')
    if base.count(VISIT) != 1 or base.count(MARKER) != 1:
        raise ValueError('original census source layout differs')
    addition = D4 + (MIN_REPLIES if policy == 'min-replies' else '')
    changed = base.replace(MARKER, addition+'\n'+MARKER, 1).replace(
        VISIT, VISIT+'  census_canonical(&P,&O);\n', 1)
    if policy == 'min-replies':
        if changed.count(MOVE) != 1:
            raise ValueError('census move-selection source layout differs')
        changed = changed.replace(MOVE, ORDERED_MOVE, 1)
    restored = changed.replace(addition+'\n', '', 1).replace(
        VISIT+'  census_canonical(&P,&O);\n', VISIT, 1)
    if policy == 'min-replies':
        restored = restored.replace(ORDERED_MOVE, MOVE, 1)
    if restored != base:
        raise ValueError('a solver/rules/TT byte would change')
    result = '#define main census_original_main\n'+changed+DRIVER
    if compact:
        if policy != 'min-replies':
            raise ValueError('compact census requires the measured min-replies policy')
        result = compact_memo(result)
    return result


def build(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    raw = solve6.SOURCE.read_text()
    source = output/'census.c'; source.write_text(generated_source(raw, args.policy, args.compact))
    cc = Path(shutil.which('cc')).resolve(strict=True)
    binary = output/'census'
    command = [str(cc), *solve6.FLAGS, str(source), '-o', str(binary)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if completed.returncode:
        raise ValueError('experimental compilation failed: '+completed.stderr)
    report = dict(format='othello-canonical-census6-build-v1', status='complete', created_utc=utc(),
        reference_source_sha256=solve6.sha256(solve6.SOURCE), source_sha256=solve6.sha256(source),
        compiler=str(cc), compiler_sha256=solve6.sha256(cc), flags=list(solve6.FLAGS),
        binary=str(binary), binary_sha256=solve6.sha256(binary), command=command,
        compile_stderr=completed.stderr, solver_rules_tt_bytes_unchanged=True,
        witness_policy=args.policy,
        compact_memo=args.compact,
        memo_state_bytes=24 if args.compact else 48,
        delta='D4 normalization before census memoization and existential move selection; '+args.policy+' witness policy; test-only canonical command'+('; full 59-bit ternary memo keys and 200-million-state CLI ceiling' if args.compact else ''),
        trust='untrusted native experiment; no Agda proof premise', production_authorized=False)
    atomic_json(output/'build.json', report)
    print(json.dumps(report))


def checked_build(path):
    r = json.loads((path/'build.json').read_text())
    binary = Path(r['binary'])
    expected = generated_source(solve6.SOURCE.read_text(), r.get('witness_policy', 'row-major'),
                                r.get('compact_memo', False)).encode()
    if (r['status'] != 'complete' or not r['solver_rules_tt_bytes_unchanged'] or
            r['reference_source_sha256'] != solve6.sha256(solve6.SOURCE) or
            r['source_sha256'] != hashlib.sha256(expected).hexdigest() or
            (path/'census.c').read_bytes() != expected or r['binary_sha256'] != solve6.sha256(binary)):
        raise ValueError('generated source or experimental binary changed')
    return r, binary


def run(args, *, build_validator=None, execute_native=None, position='initial', turn='black'):
    if (position != 'initial' and (type(position) is not str or len(position) != 36 or
            any(c not in '012' for c in position))) or turn not in ('black','white'):
        raise ValueError('invalid explicit census root')
    verify_build = checked_build if build_validator is None else build_validator
    built, binary = verify_build(args.build.resolve())
    guards = json.loads(args.tests.read_text())
    if not guards['accepted'] or guards['build_sha256'] != solve6.sha256(args.build/'build.json'):
        raise ValueError('requires the matching native differential tests')
    donor = args.donor.resolve(); closed(LABEL)
    identity = source_identity(donor)
    record = json.loads((donor/'results'/(LABEL+'.json')).read_text())
    table = donor/'results/native6/warm-2.tt'; sidecar = Path(str(table)+'.json')
    metadata = json.loads(sidecar.read_text()); original_binary = donor/'results/native6/solve6'
    if (donor.name != 'six-'+LABEL or not record['accepted'] or not record['source_unchanged'] or
            identity['source_sha256'] != record['source_sha256'] or
            metadata['config'] != dict(tt_bits=25, small=4, deep_order=5) or
            metadata['build']['source_sha256'] != built['reference_source_sha256'] or
            metadata['build']['binary_sha256'] != solve6.sha256(original_binary) or
            metadata['cache_sha256'] != EXPECTED_TT or solve6.sha256(table) != EXPECTED_TT):
        raise ValueError('original full-key TT/source/config provenance differs')
    protected = {str(sidecar): solve6.sha256(sidecar), str(original_binary): solve6.sha256(original_binary),
                 str(args.build/'build.json'): solve6.sha256(args.build/'build.json'),
                 str(args.tests): solve6.sha256(args.tests)}
    maximum = 200000000 if built.get('compact_memo', False) else 100000000
    if not 1 <= args.max_states <= maximum:
        raise ValueError('requested census size exceeds the matching binary ceiling')
    options = {'position': position, 'turn': turn, 'direction': args.direction, 'threshold': 4,
        'frontier-discs': 36, 'max-states': args.max_states, 'max-nodes': 1000000000000,
        'max-memory-mb': 8192, 'max-cpu-seconds': args.native_cpu, 'tt-bits': 25, 'small': 4,
        'deep-order': 5, 'emit-states': 0, 'load-tt': str(table)}
    command = [str(binary), 'frontier']
    for key, value in options.items(): command += ['--'+key, str(value)]
    report = dict(format='othello-canonical-census6-v1', status='running', created_utc=utc(),
        build=built, tests_sha256=solve6.sha256(args.tests), protected=protected,
        witness_policy=built.get('witness_policy', 'row-major'),
        donor_source=identity, table_sha256=EXPECTED_TT, request=options, command=command,
        compatible_tt_scope='solver/rules/TT source bytes and host-ABI header unchanged; native hints only',
        production_authorized=False, initial_problem2_proved=False, states_emitted=False)
    atomic_json(args.output, report)
    execute = subprocess.run if execute_native is None else execute_native
    done = execute(command, capture_output=True, text=True, timeout=args.native_cpu+150)
    if len(done.stdout)>1024**2: raise ValueError('unexpected state dump')
    counts = json.loads(done.stdout)
    if 'states' in counts or counts['unique_dag_nodes']>args.max_states:
        raise ValueError('counts-only census scope differs')
    complete = bool(done.returncode==0 and counts['complete'] and counts['root_holds'] and
        counts['root_validated'] and not counts['oracle_aborted'] and not counts['count_overflow'])
    if (source_identity(donor)!=identity or solve6.sha256(table)!=EXPECTED_TT or
            any(solve6.sha256(Path(p))!=d for p,d in protected.items()) or
            verify_build(args.build.resolve())[0]!=built):
        raise ValueError('original donor, tests or experimental binary changed')
    report.update(status='complete-native-census' if complete else 'censored-native-census',
        counts=counts, native_complete=complete, exit_code=done.returncode, stderr=done.stderr,
        finished_utc=utc(), donor_unchanged=True, table_unchanged=True,
        partial_counts_are_lower_bounds=not complete, incomplete_count_extrapolated=False)
    atomic_json(args.output, report)
    print(json.dumps({k:report[k] for k in ('status','native_complete','production_authorized')}))
    print(json.dumps(counts))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('build','run'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--build',type=Path); parser.add_argument('--tests',type=Path)
    parser.add_argument('--donor',type=Path)
    parser.add_argument('--policy',choices=('row-major','min-replies'),default='row-major')
    parser.add_argument('--compact',action='store_true')
    parser.add_argument('--max-states',type=int,default=100000000)
    parser.add_argument('--direction',choices=('lower','upper'),default='lower')
    parser.add_argument('--native-cpu',type=int,default=750)
    args=parser.parse_args()
    if not 1 <= args.native_cpu <= 7200:
        parser.error('native CPU cap must be between 1 and 7200 seconds')
    if args.mode=='build': build(args)
    else:
        if args.build is None or args.tests is None or args.donor is None: parser.error('run requires build/tests/donor')
        run(args)
