"""Untrusted policy minimizing exact forcing-tree size below eight empties."""
import argparse
import json
from pathlib import Path

import memo_reuse_screen6 as common
from run_job import atomic_json, utc

HELPER = r'''
#define COST_BITS 22
#define COST_INF UINT32_MAX
typedef struct {u64 key;uint32_t cost;} CostEntry;
static CostEntry *cost_memo;
static uint32_t forcing_cost(u64 P,u64 O,int turn,int lower,int threshold) {
  if(oracle_stop())return COST_INF;
  nodes++;
  if(!cost_memo) {
    cost_memo=calloc((size_t)1<<COST_BITS,sizeof(CostEntry));
    if(!cost_memo){oracle_aborted=1;return COST_INF;}
  }
  census_canonical(&P,&O);
  u64 key=census_key(P,O,turn);
  size_t slot=(size_t)(hashkey(P,O)^turn)&(((size_t)1<<COST_BITS)-1);
  CostEntry *entry=&cost_memo[slot];
  if(entry->key==(key|(1ULL<<63)))return entry->cost;
  u64 moves=gen_moves(P,O);
  uint32_t answer;
  if(!moves) {
    if(!gen_moves(O,P)) {
      int raw=turn?popc(P)-popc(O):popc(O)-popc(P);
      answer=(lower?raw>=threshold:raw<=threshold)?1:COST_INF;
    } else {
      uint32_t child=forcing_cost(O,P,!turn,lower,threshold);
      answer=child==COST_INF?COST_INF:child+1;
    }
  } else if(turn==lower) {
    uint32_t best=COST_INF;
    while(moves && !oracle_aborted) {
      u64 m=moves&-moves;moves^=m;
      u64 f=gen_flips(P,O,m);
      uint32_t child=forcing_cost(O^f,P^f^m,!turn,lower,threshold);
      if(child<best)best=child;
      if(best==1)break;
    }
    answer=best==COST_INF?COST_INF:best+1;
  } else {
    uint32_t sum=1;
    while(moves && !oracle_aborted) {
      u64 m=moves&-moves;moves^=m;
      u64 f=gen_flips(P,O,m);
      uint32_t child=forcing_cost(O^f,P^f^m,!turn,lower,threshold);
      if(child==COST_INF || child>=COST_INF-sum){sum=COST_INF;break;}
      sum+=child;
    }
    answer=sum;
  }
  if(!oracle_aborted){entry->key=key|(1ULL<<63);entry->cost=answer;}
  return answer;
}
static u64 cost_pick_move(u64 P,u64 O,u64 moves,int own,int turn,int lower,int threshold) {
  if(!own)return moves&-moves;
  if(popc(~(P|O)&REGION)>8)return census_pick_move(P,O,moves,own);
  u64 candidates=moves,best=0;
  uint32_t smallest=COST_INF;
  int best_mobility=100;
  while(candidates && !oracle_aborted) {
    u64 m=candidates&-candidates;candidates^=m;
    u64 f=gen_flips(P,O,m),cp=O^f,co=P^f^m;
    uint32_t cost=forcing_cost(cp,co,!turn,lower,threshold);
    int mobility=popc(gen_moves(cp,co));
    if(cost<smallest || (cost==smallest && cost!=COST_INF && mobility<best_mobility)) {
      best=m;smallest=cost;best_mobility=mobility;
    }
  }
  return best?best:census_pick_move(P,O,moves,own);
}
'''


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    baseline, _ = common.generated()
    patches = [
        (common.base.VISIT, HELPER+'\n'+common.base.VISIT),
        ('u64 m=census_pick_move(P,O,moves,own);',
         'u64 m=cost_pick_move(P,O,moves,own,turn,lower,threshold);'),
        ('    prefix_count=0; prefix_leaves=prefix_edges=prefix_repeats=0;',
         '    free(cost_memo);cost_memo=NULL;\n    prefix_count=0; prefix_leaves=prefix_edges=prefix_repeats=0;'),
        ('size_t bytes=ttn*sizeof(Bucket)+prefix_limit*sizeof(PrefixState)+prefix_slot_count*sizeof(uint32_t)+(emit_states?prefix_limit:0);',
         'size_t bytes=ttn*sizeof(Bucket)+prefix_limit*sizeof(PrefixState)+prefix_slot_count*sizeof(uint32_t)+(emit_states?prefix_limit:0)+((size_t)1<<COST_BITS)*sizeof(CostEntry);')]
    source = baseline
    for old, new in patches:
        assert source.count(old) == 1
        source = source.replace(old, new, 1)
    restored = source
    for old, new in reversed(patches):
        restored = restored.replace(new, old, 1)
    assert restored == baseline
    (out/'baseline.c').write_text(baseline)
    (out/'reuse.c').write_text(source)
    atomic_json(out/'source-plan.json', dict(created_utc=utc(),
        helper_sha256=common.sha(common.__file__), policy_driver_sha256=common.sha(__file__),
        reference_source_sha256=common.sha(common.solve6.SOURCE),
        generator_sha256=common.sha(common.base.__file__),
        baseline_sha256=common.sha(out/'baseline.c'), reuse_sha256=common.sha(out/'reuse.c'),
        reversible_delta=True, solver_rules_tt_bytes_unchanged=True,
        cost_memo_bits=22, cost_memo_bytes=67108864, cutoff_empties=8,
        cost_memo_reset_at_each_frontier=True, allocation_in_native_memory_guard=True,
        policy='Below eight empties, minimize forcing-tree size exactly; minimum replies breaks ties.',
        trust='Untrusted extraction policy; no safe Agda premise'))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['prepare', 'build', 'samples'])
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    out = args.out.resolve()
    if args.mode == 'prepare':
        prepare(out)
    else:
        assert json.loads((out/'source-plan.json').read_text())['policy_driver_sha256'] == common.sha(__file__)
        getattr(common, args.mode)(out)
