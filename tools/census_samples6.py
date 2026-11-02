#!/usr/bin/env python3
"""Bounded native statistics and complete descendant samples; never proof input."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import canonical_census6 as base
import solve6
from run_job import atomic_json, utc

SEED = 2026100802
MAX_OUTPUT = 16*1024*1024

EXTRA = r'''
static int sample_enabled, sample_cap=50000, sample_wanted=8;
static uint32_t *sample_indegree, *sample_list;
static unsigned char *sample_marks;
static size_t sample_output_bytes;
static u64 sample_rng=2026100802ULL;
static u64 sample_random(void) { sample_rng^=sample_rng<<13;sample_rng^=sample_rng>>7;sample_rng^=sample_rng<<17;return sample_rng; }
static size_t sample_extra(size_t n) { return n*sizeof(uint32_t)+(n+7)/8+(size_t)sample_cap*sizeof(uint32_t); }
static size_t sample_lookup(u64 P,u64 O,int turn,int lower,int threshold,int *d4) {
  u64 p=P,o=O;census_canonical(&P,&O);*d4=(p!=P || o!=O);
  u64 key=census_key(P,O,turn);
  size_t slot=(size_t)(hashkey(P,O)^((u64)(threshold+36)<<2)^(u64)(turn*2+lower))&(prefix_slot_count-1);
  while(prefix_slots[slot]) { size_t id=prefix_slots[slot]-1;
    if((prefix[id].key&CENSUS_STATE_MASK)==key) return id;
    slot=(slot+1)&(prefix_slot_count-1);
  } return SIZE_MAX;
}
static int sample_children(size_t id,int lower,int threshold,size_t out[36],int transforms[36]) {
  if(prefix[id].key&CENSUS_LEAF) return 0;
  u64 P,O;int turn;census_unpack(prefix[id].key,&P,&O,&turn);
  u64 moves=gen_moves(P,O);int n=0,index=0;
  if(!moves) { out[0]=sample_lookup(O,P,!turn,lower,threshold,&transforms[0]);return 1; }
  while(moves) {u64 m=moves&-moves;moves^=m;
    if(turn!=lower || index==census_selected[id]) {u64 f=gen_flips(P,O,m);
      out[n]=sample_lookup(O^f,P^f^m,!turn,lower,threshold,&transforms[n]);n++;}
    index++;
  } return n;
}
static int sample_row(char *buf,size_t size,size_t id,int lower,int threshold) {
  u64 P,O;int turn;char pos[37];census_unpack(prefix[id].key,&P,&O,&turn);encode(P,O,turn,pos);
  return snprintf(buf,size,"{\"position\":\"%s\",\"turn\":\"%s\",\"direction\":\"%s\",\"threshold\":%d,\"leaf\":%s,\"selected_index\":%d,\"global_indegree\":%u}",pos,turn?"white":"black",lower?"lower":"upper",threshold,(prefix[id].key&CENSUS_LEAF)?"true":"false",census_selected[id]==36?-1:census_selected[id],sample_indegree[id]);
}
static void sample_report(int complete,int lower,int threshold) {
  if(!sample_enabled) return;
  if(!complete || frontier_discs!=36) {printf(",\"sampling_complete\":false,\"samples\":[]");return;}
  u64 kinds[4]={0},discs[37]={0},entries=0,refs=0,d4=0,edges=0;
  size_t candidates[128],seen=0,cn=0;
  int valid=1;
  for(size_t i=0;i<prefix_count;i++) {
    if((i&4095)==0 && oracle_stop()) {valid=0;break;}
    u64 P,O;int turn;census_unpack(prefix[i].key,&P,&O,&turn);int occupied=popc(P|O);discs[occupied]++;
    int kind=(prefix[i].key&CENSUS_LEAF)?0:!gen_moves(P,O)?1:turn==lower?2:3;kinds[kind]++;
    size_t children[36];int transforms[36];int n=sample_children(i,lower,threshold,children,transforms);
    if(kind!=0 && n==0) {valid=0;break;}
    for(int j=0;j<n;j++) {size_t child=children[j];if(child==SIZE_MAX || child==i || sample_indegree[child]==UINT32_MAX) {valid=0;break;}
      sample_indegree[child]++;edges++;d4+=transforms[j];}
    if(!valid) break;
    if(occupied==22 || occupied==24 || prefix_count<=50000) {seen++;if(cn<128)candidates[cn++]=i;else {size_t k=sample_random()%seen;if(k<128)candidates[k]=i;}}
  }
  if(!valid) {printf(",\"sampling_complete\":false,\"samples\":[]");return;}
  for(size_t i=0;i<prefix_count;i++) if(!(prefix[i].key&CENSUS_LEAF) && sample_indegree[i]>=2) {entries++;refs+=sample_indegree[i];}
  u64 leaf_occurrences=(prefix_count && (prefix[0].key&CENSUS_LEAF))?1:0, r_nonidentity=0;
  for(size_t i=0;i<prefix_count;i++) {
    if((i&4095)==0 && oracle_stop()) {valid=0;break;}
    if(prefix[i].key&CENSUS_LEAF) leaf_occurrences+=sample_indegree[i];
    size_t children[36];int transforms[36];int n=sample_children(i,lower,threshold,children,transforms);
    for(int j=0;j<n;j++) if(!(prefix[children[j]].key&CENSUS_LEAF) && sample_indegree[children[j]]>=2) r_nonidentity+=transforms[j];
  }
  if(!valid) {printf(",\"sampling_complete\":false,\"samples\":[]");return;}
  /* Existing layered grammar: each nonterminal body once, terminal leaves
     inline per incoming edge, shared citations R(identity)=1/R(D4)=2.
     Root/shared state literals cost 13 bytes and no declaration token. */
  u64 tokens=kinds[1]+kinds[2]+kinds[3]+leaf_occurrences+refs;
  u64 ascii=kinds[1]+2*(kinds[2]+kinds[3])+leaf_occurrences+refs+r_nonidentity+13*(entries+1);
  printf(",\"sampling_complete\":true,\"statistics\":{\"node_kinds\":{\"leaf\":%llu,\"pass\":%llu,\"forcing\":%llu,\"opponent\":%llu},\"disc_histogram\":[",(unsigned long long)kinds[0],(unsigned long long)kinds[1],(unsigned long long)kinds[2],(unsigned long long)kinds[3]);
  for(int i=0;i<=36;i++)printf("%s%llu",i?",":"",(unsigned long long)discs[i]);
  printf("],\"sharing_entries\":%llu,\"reference_edges\":%llu,\"nonidentity_D4_edges\":%llu,\"chosen_edges\":%llu,\"leaf_occurrences\":%llu,\"nonidentity_D4_citation_edges\":%llu,\"ideal_grammar_tokens\":%llu,\"ideal_grammar_ascii_bytes\":%llu,\"indegree_histogram\":[",(unsigned long long)entries,(unsigned long long)refs,(unsigned long long)d4,(unsigned long long)edges,(unsigned long long)leaf_occurrences,(unsigned long long)r_nonidentity,(unsigned long long)tokens,(unsigned long long)ascii);
  /* Exact bins 0..35 and >=36, with maximum recorded. */
  u64 hist[37]={0};uint32_t maxdeg=0;
  for(size_t i=0;i<prefix_count;i++){uint32_t d=sample_indegree[i];hist[d<36?d:36]++;if(d>maxdeg)maxdeg=d;}
  for(int i=0;i<=36;i++)printf("%s%llu",i?",":"",(unsigned long long)hist[i]);
  printf("],\"indegree_last_bin\":\"at-least-36\",\"max_indegree\":%u},\"samples\":[",maxdeg);
  int emitted=0,too_large=0,byte_rejected=0,attempts=0;
  for(size_t a=0;a<cn && emitted<sample_wanted;a++) {
    if(oracle_stop())break;attempts++;
    memset(sample_marks,0,(prefix_count+7)/8);size_t root=candidates[a],count=1;sample_list[0]=(uint32_t)root;sample_marks[root/8]|=1<<(root%8);int ok=1;
    for(size_t q=0;q<count && ok;q++) {if((q&1023)==0 && oracle_stop()){ok=0;break;}
      size_t child[36];int tr[36];int n=sample_children(sample_list[q],lower,threshold,child,tr);
      for(int j=0;j<n;j++){size_t c=child[j];if(c==SIZE_MAX){ok=0;break;}if(!(sample_marks[c/8]&(1<<(c%8)))){
        if(count==(size_t)sample_cap){ok=0;break;}sample_marks[c/8]|=1<<(c%8);sample_list[count++]=(uint32_t)c;}}
    }
    if(!ok){too_large++;continue;}
    char row[256],header[512],pos[37];u64 P,O;int turn;census_unpack(prefix[root].key,&P,&O,&turn);encode(P,O,turn,pos);
    int h=snprintf(header,sizeof(header),"%s{\"root_position\":\"%s\",\"root_turn\":\"%s\",\"direction\":\"%s\",\"threshold\":%d,\"complete\":true,\"root_validated\":true,\"root_holds\":true,\"frontier_discs\":36,\"tree_nodes_S\":%llu,\"unique_dag_nodes\":%zu,\"states\":[",emitted?",":"",pos,turn?"white":"black",lower?"lower":"upper",threshold,(unsigned long long)prefix[root].tree,count);
    size_t bytes=(size_t)h+2;
    for(size_t q=0;q<count;q++)bytes+=(size_t)sample_row(row,sizeof(row),sample_list[q],lower,threshold)+(q?1:0);
    if(sample_output_bytes+bytes>16*1024*1024-16384){byte_rejected++;continue;}
    fputs(header,stdout);for(size_t q=0;q<count;q++){sample_row(row,sizeof(row),sample_list[q],lower,threshold);printf("%s%s",q?",":"",row);}printf("]}");sample_output_bytes+=bytes;emitted++;
  }
  printf("],\"sample_seed\":2026100802,\"sample_attempts\":%d,\"sample_too_large\":%d,\"sample_byte_rejected\":%d,\"sample_json_bytes\":%zu,\"sample_output_cap\":16777216,\"sample_node_cap\":%d,\"sample_cpu_exhausted\":%s",attempts,too_large,byte_rejected,sample_output_bytes,sample_cap,oracle_aborted?"true":"false");
}
'''

WRAPPER = r'''
#undef main
int main(int argc,char **argv) {
  if(argc<2 || strcmp(argv[1],"sample")) return samples_original_main(argc,argv);
  sample_enabled=1;argv[1]="frontier";int write=2;
  for(int i=2;i<argc;i++) {
    if(!strcmp(argv[i],"--sample-cap") || !strcmp(argv[i],"--sample-count")) {
      int iscap=!strcmp(argv[i],"--sample-cap");if(++i==argc)return error("missing sample option");
      if(!integer(argv[i],1,iscap?50000:8,iscap?&sample_cap:&sample_wanted))return error("invalid sample option");
    } else {if(!strcmp(argv[i],"--emit-states") && i+1<argc && strcmp(argv[i+1],"0"))return error("sample forbids whole graph dump");argv[write++]=argv[i];}
  }
  return samples_original_main(write,argv);
}
'''

def generated_source(raw):
    source=base.generated_source(raw,'min-replies',True)
    patches=[('static int run_frontier(',EXTRA+'\nstatic int run_frontier('),
      ('(emit_states?prefix_limit:0)','((emit_states||sample_enabled)?prefix_limit:0)+(sample_enabled?sample_extra(prefix_limit):0)'),
      ('(emit_states?(size_t)max_states:0)','((emit_states||sample_enabled)?(size_t)max_states:0)+(sample_enabled?sample_extra((size_t)max_states):0)'),
      ('census_selected=emit_states?calloc(prefix_limit,1):NULL;', 'census_selected=(emit_states||sample_enabled)?calloc(prefix_limit,1):NULL;\n    if(sample_enabled){sample_indegree=calloc(prefix_limit,sizeof(uint32_t));sample_marks=calloc((prefix_limit+7)/8,1);sample_list=calloc((size_t)sample_cap,sizeof(uint32_t));}\n    if(sample_enabled && (!sample_indegree || !sample_marks || !sample_list))return error("cannot allocate sample tables");'),
      ('(emit_states && !census_selected)','((emit_states||sample_enabled) && !census_selected)'),
      ('    if(emit_states) {','    sample_report(complete,lower,threshold);\n    if(emit_states) {'),
      ('free(census_selected);','free(census_selected); free(sample_indegree); free(sample_marks); free(sample_list); sample_indegree=NULL; sample_marks=NULL; sample_list=NULL;'),
      ('integer(v,1,200000000,&max_states)','integer(v,1,160000000,&max_states)'),
      ('int main(int argc,char **argv) {','int samples_original_main(int argc,char **argv) {')]
    for old,new in patches:
        if source.count(old)!=1: raise ValueError('instrumentation layout differs: '+old)
        source=source.replace(old,new,1)
    restored=source
    for old,new in reversed(patches): restored=restored.replace(new,old,1)
    if restored!=base.generated_source(raw,'min-replies',True):raise ValueError('unrelated source changed')
    return source+WRAPPER


def build(args):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=out/'census.c';source.write_text(generated_source(solve6.SOURCE.read_text()))
    cc=Path(shutil.which('cc')).resolve(strict=True);binary=out/'census'
    command=[str(cc),*solve6.FLAGS,str(source),'-o',str(binary)]
    done=subprocess.run(command,capture_output=True,text=True,timeout=30)
    if done.returncode:raise ValueError(done.stderr)
    report=dict(format='othello-census-samples6-build-v1',status='complete',created_utc=utc(),reference_source_sha256=solve6.sha256(solve6.SOURCE),source_sha256=solve6.sha256(source),binary=str(binary),binary_sha256=solve6.sha256(binary),compiler=str(cc),compiler_sha256=solve6.sha256(cc),flags=list(solve6.FLAGS),command=command,compile_stderr=done.stderr,solver_rules_tt_bytes_unchanged=True,witness_policy='min-replies',compact_memo=True,memo_state_bytes=24,production_authorized=False,trust='untrusted native experiment; no Agda proof premise')
    atomic_json(out/'build.json',report);print(json.dumps(report))


def checked_build(path):
    path=path.resolve();r=json.loads((path/'build.json').read_text());binary=Path(r['binary'])
    expected=generated_source(solve6.SOURCE.read_text()).encode()
    if r['format']!='othello-census-samples6-build-v1' or r['status']!='complete' or not r['solver_rules_tt_bytes_unchanged'] or r['reference_source_sha256']!=solve6.sha256(solve6.SOURCE) or r['source_sha256']!=hashlib.sha256(expected).hexdigest() or (path/'census.c').read_bytes()!=expected or r['binary_sha256']!=solve6.sha256(binary):raise ValueError('source/binary provenance changed')
    return r,binary


def run(args):
    # Reuse the donor validation and protection of the canonical runner. Its
    # subprocess boundary is wrapped locally to select bounded sample mode.
    if not 1<=args.max_states<=160000000:raise ValueError('sample state ceiling exceeded')
    original_run=base.subprocess.run
    def bounded(command,**kw):
        if len(command)>1 and command[1]=='frontier':
            command=[command[0],'sample',*command[2:],'--sample-cap',str(args.sample_cap),'--sample-count',str(args.sample_count)]
        done=original_run(command,**kw)
        if len(done.stdout.encode())>MAX_OUTPUT:raise ValueError('sample output cap exceeded')
        # canonical.run protects donor provenance but expects a short count row.
        payload=json.loads(done.stdout)
        samples=payload.pop('samples',[]);stats=payload.pop('statistics',None)
        artifact=dict(format='othello-census-samples6-v1',samples=samples,statistics=stats,native_census=payload,exact_native_output_bytes=len(done.stdout.encode()),output_cap=MAX_OUTPUT,build_sha256=solve6.sha256(args.build/'build.json'),production_authorized=False,initial_problem2_proved=False,trust='native experiment; no Agda proof premise')
        encoded=(json.dumps(artifact,separators=(',',':'))+'\n').encode()
        if len(encoded)>MAX_OUTPUT:raise ValueError('sample JSON artifact cap exceeded')
        args.samples_output.parent.mkdir(parents=True,exist_ok=True)
        temporary=args.samples_output.with_name(args.samples_output.name+'.tmp')
        temporary.write_bytes(encoded);temporary.replace(args.samples_output)
        done.stdout=json.dumps(payload)
        return done
    # Inject only the native invocation. Changing subprocess.run globally would
    # also intercept the service-status and source-provenance commands.
    base.run(args,build_validator=checked_build,execute_native=bounded)
    report=json.loads(args.output.read_text())
    report['format']='othello-census-samples6-run-v1'
    report['command']=[report['command'][0],'sample',*report['command'][2:],
                       '--sample-cap',str(args.sample_cap),'--sample-count',str(args.sample_count)]
    report['samples_output']=str(args.samples_output.resolve())
    report['samples_output_sha256']=solve6.sha256(args.samples_output)
    report['exact_samples_output_bytes']=args.samples_output.stat().st_size
    report['sampling_scope']='completed descendant graphs from 22/24-disc roots; full-graph indegrees; bounded 128 candidates; no truncated samples'
    report['ideal_grammar']='root/shared nonterminal state literals=13 bytes; each nonterminal body once; terminal leaves inline per edge; C/F=2, P/L/K=1, R(identity)=1, R(nonidentity D4)=2; no declaration token'
    atomic_json(args.output,report)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('build','test','run'));p.add_argument('--output',type=Path,required=True)
    p.add_argument('--build',type=Path);p.add_argument('--tests',type=Path);p.add_argument('--donor',type=Path);p.add_argument('--reference-build',type=Path)
    p.add_argument('--samples-output',type=Path);p.add_argument('--max-states',type=int,default=100000000);p.add_argument('--native-cpu',type=int,default=1500)
    p.add_argument('--direction',choices=('lower','upper'),default='lower');p.add_argument('--sample-cap',type=int,default=50000);p.add_argument('--sample-count',type=int,default=8)
    a=p.parse_args()
    if not 1<=a.native_cpu<=7200 or not 1<=a.sample_cap<=50000 or not 1<=a.sample_count<=8:p.error('invalid native/sample caps')
    if a.mode=='build':build(a)
    elif a.mode=='test':
        import test_census_samples6 as tests
        if not a.build or not a.reference_build:p.error('test requires build/reference-build')
        tests.run(a)
    else:
        if not all((a.build,a.tests,a.donor,a.samples_output)):p.error('run requires build/tests/donor/samples-output')
        run(a)

if __name__=='__main__':main()
