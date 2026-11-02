#!/usr/bin/env python3
"""Counts-only layout after globally reselecting within a completed census DAG.

The native postprocessing is untrusted instrumentation.  It changes neither
the search that constructs the original graph nor any solver decision made
during that search.  It makes no performance or proof claim.
"""
import argparse
import json
from pathlib import Path

import query_layout6 as q
import wire_layout6 as layout
from run_job import atomic_json, utc


base = q.base
HELPERS = list(base.HELPERS)
for name in ('query_layout6.py', 'global_reuse_layout6.py'):
    if name not in HELPERS:
        HELPERS.append(name)
base.HELPERS = HELPERS


POSTPROCESS = r'''
/* Untrusted global reuse pass.  The original census is already complete.
   Reuse PrefixState.tree, wire_indegree and wire_order; allocate no graph-sized
   postprocessing table.  A zero tree value means not computed. */
static int reuse_overflow,reuse_failed;
static u64 reuse_visits;
static u64 reuse_add(u64 a,u64 b) {
  if(UINT64_MAX-a<b){reuse_overflow=1;return UINT64_MAX;}return a+b;
}
/* Memoized DFS handles one-disc placement edges and same-disc pass edges.
   Marks detect unexpected cycles; depth80 exceeds any complete 6x6 play. */
static int reuse_cost(size_t id,int lower,int threshold,int depth) {
  if(id>=prefix_count || depth>80 || reuse_failed)return 0;
  if((reuse_visits++&4095)==0 && layout_stop())return 0;
  if(wire_indegree[id]==2)return 1;
  if(wire_indegree[id]==1){reuse_failed=1;return 0;}
  wire_indegree[id]=1;
  if(prefix[id].key&CENSUS_LEAF)prefix[id].tree=1;
  else {
    u64 P,O;int turn;census_unpack(prefix[id].key,&P,&O,&turn);
    u64 moves=gen_moves(P,O);
    if(!moves){
      size_t child=wire_lookup(O,P,!turn,lower,threshold);
      if(!reuse_cost(child,lower,threshold,depth+1))return 0;
      prefix[id].tree=reuse_add(1,prefix[child].tree);
    }else{
      int own=turn==lower,pin=own?wire_pin(P,O,turn,lower):-1;
      u64 total=1,best=UINT64_MAX;unsigned int best_index=36,index=0;
      while(moves){u64 m=moves&-moves;moves^=m;
        if(own && pin>=0 && pin!=(int)index){index++;continue;}
        u64 f=gen_flips(P,O,m);
        size_t child=wire_lookup(O^f,P^f^m,!turn,lower,threshold);
        if(child==SIZE_MAX){
          if(!own || pin==(int)index)return 0;
          index++;continue;
        }
        if(!reuse_cost(child,lower,threshold,depth+1))return 0;
        u64 cost=prefix[child].tree;
        if(own){if(best_index==36 || cost<best){best=cost;best_index=index;}}
        else total=reuse_add(total,cost);
        index++;
      }
      if(own){
        if(best_index==36 || (pin>=0 && best_index!=(unsigned int)pin))return 0;
        census_selected[id]=(unsigned char)best_index;
        prefix[id].tree=reuse_add(1,best);
      }else prefix[id].tree=total;
    }
  }
  wire_indegree[id]=2;return !reuse_overflow;
}
static int reuse_costs(int lower,int threshold) {
  memset(wire_indegree,0,prefix_count*sizeof(uint32_t));
  for(size_t i=0;i<prefix_count;i++)prefix[i].tree=0;
  reuse_overflow=reuse_failed=0;reuse_visits=0;
  return reuse_cost(0,lower,threshold,0) && !layout_stop();
}
static int reuse_order(size_t id,int lower,int threshold,int depth,u64 *edges) {
  if(id>=prefix_count || depth>80)return 0;
  if((reuse_visits++&4095)==0 && layout_stop())return 0;
  if(wire_indegree[id]==2)return 1;
  if(wire_indegree[id]==1)return 0;
  wire_indegree[id]=1;
  size_t children[36];int n=wire_children(id,lower,threshold,children);
  if(!(prefix[id].key&CENSUS_LEAF) && !n)return 0;
  for(int j=0;j<n;j++){
    if(!reuse_order(children[j],lower,threshold,depth+1,edges))return 0;
    *edges=reuse_add(*edges,1);
  }
  if(reuse_overflow || wire_order_count>=prefix_count)return 0;
  wire_order[wire_order_count++]=(uint32_t)id;wire_indegree[id]=2;return 1;
}
static int reuse_reachable(int lower,int threshold,u64 *edges) {
  memset(wire_indegree,0,prefix_count*sizeof(uint32_t));
  wire_order_count=0;reuse_visits=0;*edges=0;
  if(!reuse_order(0,lower,threshold,0,edges) || layout_stop())return 0;
  /* The following layout indegree pass requires a clean array. */
  memset(wire_indegree,0,prefix_count*sizeof(uint32_t));
  return wire_order_count && wire_order[wire_order_count-1]==0;
}
'''


def generated(pins):
    original = layout.generated_source(layout.wire.solve6.SOURCE.read_text(), pins)
    report_head = '''static int wire_report(int complete,u64 rootP,u64 rootO,int rootTurn,int lower,int threshold) {
  if(!wire_enabled)return 1;
  int valid=complete && frontier_discs==36 && wire_order_count==prefix_count;
  size_t bytes=0,records=0;u64 tokens=0,references=0;'''
    new_head = '''static int wire_report(int complete,u64 rootP,u64 rootO,int rootTurn,int lower,int threshold) {
  if(!wire_enabled)return 1;
  size_t original_order_count=wire_order_count;
  int valid=complete && frontier_discs==36 && original_order_count==prefix_count;
  size_t bytes=0,records=0;u64 tokens=0,references=0;
  u64 postprocessed_edges=0;
  if(valid)valid=reuse_costs(lower,threshold) && reuse_reachable(lower,threshold,&postprocessed_edges);
  int postprocess_complete=valid;
  printf(",\\\"original_graph_nodes\\\":%zu,\\\"original_completion_order_nodes\\\":%zu",prefix_count,original_order_count);
  printf(",\\\"postprocess_complete\\\":%s,\\\"postprocessed_graph_nodes\\\":%zu,\\\"postprocessed_graph_edges\\\":%llu,\\\"postprocessed_tree_nodes\\\":%llu,\\\"postprocess_overflow\\\":%s",
    postprocess_complete?"true":"false",postprocess_complete?wire_order_count:0,
    (unsigned long long)(postprocess_complete?postprocessed_edges:0),
    (unsigned long long)(postprocess_complete?prefix[0].tree:0),reuse_overflow?"true":"false");'''
    indegrees = '''  if(valid)for(size_t i=0;i<prefix_count;i++){
    if((i&4095)==0 && layout_stop()){valid=0;break;}
    size_t children[36];int n=wire_children(i,lower,threshold,children);
    if(!(prefix[i].key&CENSUS_LEAF) && !n){valid=0;break;}
    for(int j=0;j<n;j++){size_t c=children[j];
      if(c==SIZE_MAX || c==i || wire_indegree[c]==UINT32_MAX){valid=0;break;}
      wire_indegree[c]++;}if(!valid)break;
  }'''
    reachable_indegrees = '''  if(valid)for(size_t q=0;q<wire_order_count;q++){
    if((q&4095)==0 && layout_stop()){valid=0;break;}
    size_t i=wire_order[q],children[36];int n=wire_children(i,lower,threshold,children);
    if(!(prefix[i].key&CENSUS_LEAF) && !n){valid=0;break;}
    for(int j=0;j<n;j++){size_t c=children[j];
      if(c==SIZE_MAX || c==i || wire_indegree[c]==UINT32_MAX){valid=0;break;}
      wire_indegree[c]++;}if(!valid)break;
  }'''
    patches = [
        ('static int wire_report(', POSTPROCESS + '\nstatic int wire_report('),
        (report_head, new_head),
        (indegrees, reachable_indegrees),
    ]
    changed = original
    for old, new in patches:
        if changed.count(old) != 1:
            raise ValueError('unexpected global-reuse source: ' + old[:80])
        changed = changed.replace(old, new, 1)
    restored = changed
    for old, new in reversed(patches):
        if restored.count(new) != 1:
            raise ValueError('ambiguous reversible global-reuse delta')
        restored = restored.replace(new, old, 1)
    if restored != original:
        raise ValueError('global-reuse delta changes unrelated source')
    return changed


base.generated = generated


def prepare(out):
    base.prepare(out)
    plan = json.loads((out / 'source-plan.json').read_text())
    for name in ('cutoff_empties', 'cost_cap', 'cost_memo_bytes'):
        plan.pop(name, None)
    plan.update(
        method='complete original min-replies graph, then global same-goal reuse DP and reachable layout',
        original_graph_policy='pinned min-replies census, unchanged',
        postprocess_graph_allocations='none; reuses prefix.tree, wire_indegree and wire_order',
        cost_search='memoized DFS over existing same-goal keys, no oracle queries',
        depth_guard=80,
        active_recursion_cycle_check=True,
        heuristic_objective='forcing-tree size in the existing state set, not minimum DAG size',
        all_34_line_state_cuts='OPEN obligation; ordinary fail-closed move pins remain active',
        no_performance_or_proof_claim=True,
        native_output_requires_postprocess_complete=True,
        accepted_proof=False,
        production_go=False,
        initial_theorem=False,
    )
    atomic_json(out / 'source-plan.json', plan)


def accepted(result):
    return base_accepted(result) and result['counts'].get('postprocess_complete') is True


base_accepted = base.accepted
base.accepted = accepted


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'build', 'fixture', 'lower', 'upper'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    if args.mode == 'prepare':
        prepare(output)
    elif args.mode in ('build', 'fixture'):
        getattr(base, args.mode)(output)
    else:
        q.install_storage_guard(output)
        base.initial(output, args.mode)
