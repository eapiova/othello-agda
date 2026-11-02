"""Counts-only sharing-weighted alternative within the original global-reuse scope."""
import argparse
import json
from pathlib import Path

import global_reuse_layout6 as prior
from run_job import atomic_json, utc

base = prior.base
ORIGINAL_GENERATED = prior.generated
base.HELPERS = list(base.HELPERS)+['degree_reuse_layout6.py']

DEGREES = r'''
/* Static candidate indegrees are a heuristic for shared subgraphs, not proof. */
static u64 degree_weight(size_t id) {
  u64 degree=wire_indegree[id];
  return 1+((u64)1048576/(1+degree));
}
static int degree_counts(int lower,int threshold) {
  memset(wire_indegree,0,prefix_count*sizeof(uint32_t));
  for(size_t id=0;id<prefix_count;id++) {
    if((id&4095)==0 && layout_stop())return 0;
    if(prefix[id].key&CENSUS_LEAF)continue;
    u64 P,O;int turn;census_unpack(prefix[id].key,&P,&O,&turn);
    u64 moves=gen_moves(P,O);
    if(!moves) {
      size_t child=wire_lookup(O,P,!turn,lower,threshold);
      if(child==SIZE_MAX || wire_indegree[child]==UINT32_MAX)return 0;
      wire_indegree[child]++;continue;
    }
    int own=turn==lower,pin=own?wire_pin(P,O,turn,lower):-1,index=0;
    while(moves) {
      u64 m=moves&-moves;moves^=m;
      if(own && pin>=0 && pin!=index){index++;continue;}
      u64 f=gen_flips(P,O,m);
      size_t child=wire_lookup(O^f,P^f^m,!turn,lower,threshold);
      if(child==SIZE_MAX) {
        if(!own || pin==index)return 0;
        index++;continue;
      }
      if(wire_indegree[child]==UINT32_MAX)return 0;
      wire_indegree[child]++;index++;
    }
  }
  return !layout_stop();
}
static int degree_true_tree(int lower,int threshold) {
  for(size_t q=0;q<wire_order_count;q++) {
    if((q&4095)==0 && layout_stop())return 0;
    size_t id=wire_order[q];
    u64 count=1;
    if(!(prefix[id].key&CENSUS_LEAF)) {
      size_t children[36];int n=wire_children(id,lower,threshold,children);
      if(!n)return 0;
      for(int j=0;j<n;j++)count=reuse_add(count,prefix[children[j]].tree);
    }
    prefix[id].tree=count;
  }
  return !reuse_overflow && !layout_stop();
}
'''


def replace_once(source, old, new):
    assert source.count(old) == 1, old[:100]
    return source.replace(old, new, 1)


def generated(pins):
    original = ORIGINAL_GENERATED(pins)
    cost, reachable = prior.POSTPROCESS.split('static int reuse_order(', 1)
    patches = [
        ('if(wire_indegree[id]==2)return 1;', 'if(census_selected[id]&128)return 1;'),
        ('if(wire_indegree[id]==1){reuse_failed=1;return 0;}', 'if(census_selected[id]&64){reuse_failed=1;return 0;}'),
        ('wire_indegree[id]=1;', 'census_selected[id]=(census_selected[id]&63)|64;'),
        ('prefix[id].tree=1;', 'prefix[id].tree=degree_weight(id);'),
        ('prefix[id].tree=reuse_add(1,prefix[child].tree);', 'prefix[id].tree=reuse_add(degree_weight(id),prefix[child].tree);'),
        ('u64 total=1,best=UINT64_MAX;', 'u64 total=degree_weight(id),best=UINT64_MAX;'),
        ('census_selected[id]=(unsigned char)best_index;', 'census_selected[id]=(unsigned char)best_index|64;'),
        ('prefix[id].tree=reuse_add(1,best);', 'prefix[id].tree=reuse_add(degree_weight(id),best);'),
        ('wire_indegree[id]=2;return !reuse_overflow;', 'census_selected[id]=(census_selected[id]&63)|128;return !reuse_overflow;'),
        ('  memset(wire_indegree,0,prefix_count*sizeof(uint32_t));\n  for(size_t i=0;i<prefix_count;i++)prefix[i].tree=0;',
         '  if(!degree_counts(lower,threshold))return 0;\n  for(size_t i=0;i<prefix_count;i++){prefix[i].tree=0;census_selected[i]&=63;}'),
        ('  return reuse_cost(0,lower,threshold,0) && !layout_stop();',
         '  int valid=reuse_cost(0,lower,threshold,0) && !layout_stop();\n  for(size_t i=0;i<prefix_count;i++)census_selected[i]&=63;\n  return valid;'),
    ]
    for old, new in patches:
        cost = replace_once(cost, old, new)
    # degree_counts needs no reuse_add; degree_true_tree follows its declaration.
    degree_counts, true_tree = DEGREES.split('static int degree_true_tree(', 1)
    changed_post = degree_counts+cost+'static int reuse_order('+reachable+'\nstatic int degree_true_tree('+true_tree
    changed = replace_once(original, prior.POSTPROCESS, changed_post)
    old = 'reuse_costs(lower,threshold) && reuse_reachable(lower,threshold,&postprocessed_edges)'
    new = old+' && degree_true_tree(lower,threshold)'
    changed = replace_once(changed, old, new)
    assert changed.replace(new, old, 1).replace(changed_post, prior.POSTPROCESS, 1) == original
    return changed


base.generated = generated


def prepare(out):
    prior.prepare(out)
    plan = json.loads((out/'source-plan.json').read_text())
    plan.update(method='Static candidate-indegree weighted global reuse; original min-replies graph unchanged',
        heuristic_objective='Sum of 1+floor(1048576/(1+candidate indegree)) over forcing tree; not minimum DAG',
        true_tree_counts_recomputed_after_selection=True,
        extra_graph_sized_allocations=False,
        original_family_root='results/global-reuse-layout6-20261018',
        original_family_scope_cpu_cap=5650,
        prior_family_combined_cpu_seconds=824.098,
        fixture_is_not_an_initial_board_forecast=True)
    atomic_json(out/'source-plan.json', plan)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'build', 'fixture', 'lower', 'upper'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.mode == 'prepare':
        prepare(out)
    elif args.mode in ['build', 'fixture']:
        getattr(base, args.mode)(out)
    else:
        prior.q.install_storage_guard(out)
        base.initial(out, args.mode)
