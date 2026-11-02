"""Untrusted bounded forcing-tree search; unknown costs never select a move."""
import argparse
import json
from pathlib import Path
import memo_reuse_screen6 as common
import endgame_cost_screen6 as old
from endgame16_screen6 import samples
from run_job import atomic_json, utc

HELPER = r'''
#define COST_BITS 22
#define COST_INF UINT32_MAX
#define COST_VALID (1ULL<<63)
#define COST_EXACT (1ULL<<62)
typedef struct {u64 key;uint32_t cost;} CostEntry;
static CostEntry *cost_memo;
/* Return min(exact forcing-tree cost,limit); reaching limit means unknown. */
static uint32_t forcing_cost(u64 P,u64 O,int turn,int lower,int threshold,uint32_t limit) {
  if(limit<=1 || oracle_stop())return limit;
  nodes++;
  if(!cost_memo) {
    cost_memo=calloc((size_t)1<<COST_BITS,sizeof(CostEntry));
    if(!cost_memo){oracle_aborted=1;return limit;}
  }
  census_canonical(&P,&O);
  u64 key=census_key(P,O,turn);
  size_t slot=(size_t)(hashkey(P,O)^turn)&(((size_t)1<<COST_BITS)-1);
  CostEntry *entry=&cost_memo[slot];
  int same=(entry->key&COST_VALID) && ((entry->key&~(COST_VALID|COST_EXACT))==key);
  if(same && (entry->key&COST_EXACT))return entry->cost<limit?entry->cost:limit;
  if(same && entry->cost>=limit)return limit;
  u64 moves=gen_moves(P,O);
  uint32_t answer;
  if(!moves) {
    if(!gen_moves(O,P)) {
      int raw=turn?popc(P)-popc(O):popc(O)-popc(P);
      answer=(lower?raw>=threshold:raw<=threshold)?1:limit;
    } else {
      uint32_t child=forcing_cost(O,P,!turn,lower,threshold,limit-1);
      answer=child+1;
    }
  } else if(turn==lower) {
    uint32_t best=limit;
    while(moves && !oracle_aborted) {
      u64 m=moves&-moves;moves^=m;
      u64 f=gen_flips(P,O,m);
      uint32_t child=forcing_cost(O^f,P^f^m,!turn,lower,threshold,best-1);
      if(child+1<best)best=child+1;
      if(best==2)break;
    }
    answer=best;
  } else {
    uint32_t sum=1;
    while(moves && !oracle_aborted) {
      u64 m=moves&-moves;moves^=m;
      u64 f=gen_flips(P,O,m);
      uint32_t child=forcing_cost(O^f,P^f^m,!turn,lower,threshold,limit-sum);
      sum+=child;
      if(sum>=limit){sum=limit;break;}
    }
    answer=sum;
  }
  if(!oracle_aborted) {
    /* Recursive collisions may have replaced the entry; recheck its key. */
    int still_same=(entry->key&COST_VALID) && ((entry->key&~(COST_VALID|COST_EXACT))==key);
    if(answer<limit || !still_same || (!(entry->key&COST_EXACT) && entry->cost<answer)) {
      entry->key=key|COST_VALID|(answer<limit?COST_EXACT:0);entry->cost=answer;
    }
  }
  return answer;
}
static u64 cost_pick_move(u64 P,u64 O,u64 moves,int own,int turn,int lower,int threshold) {
  if(!own)return moves&-moves;
  if(popc(~(P|O)&REGION)>16)return census_pick_move(P,O,moves,own);
  u64 candidates=moves,best=0;
  uint32_t smallest=4096;
  int best_mobility=100;
  while(candidates && !oracle_aborted) {
    u64 m=candidates&-candidates;candidates^=m;
    u64 f=gen_flips(P,O,m),cp=O^f,co=P^f^m;
    uint32_t limit=best?smallest+1:smallest;
    uint32_t cost=forcing_cost(cp,co,!turn,lower,threshold,limit);
    int mobility=popc(gen_moves(cp,co));
    if(cost<smallest || (best && cost==smallest && mobility<best_mobility)) {
      best=m;smallest=cost;best_mobility=mobility;
    }
  }
  return best?best:census_pick_move(P,O,moves,own);
}
'''

def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    previous=Path(__file__).resolve().parents[1]/'results/endgame12-screen6-20261018'
    prior=json.loads((previous/'source-plan.json').read_text())
    source=previous/'reuse.c';assert common.sha(source)==prior['reuse_sha256']
    baseline=source.read_text();original=old.HELPER.replace('>8)return','>12)return')
    assert baseline.count(original)==1
    changed=baseline.replace(original,HELPER,1)
    assert changed.replace(HELPER,original,1)==baseline
    (out/'baseline.c').write_text(baseline);(out/'reuse.c').write_text(changed)
    atomic_json(out/'source-plan.json',dict(created_utc=utc(),
        helper_sha256=common.sha(common.__file__),policy_driver_sha256=common.sha(__file__),
        sample_driver_sha256=common.sha(Path(__file__).with_name('endgame16_screen6.py')),
        input_c_source=str(source),input_c_sha256=common.sha(source),
        baseline_sha256=common.sha(out/'baseline.c'),reuse_sha256=common.sha(out/'reuse.c'),
        baseline_cutoff=12,variant_cutoff=16,cost_cap=4096,cost_memo_bytes=67108864,
        exact_and_lower_bound_cache_distinguished=True,unknown_cost_falls_back_to_original_policy=True,
        reversible_delta=True,solver_rules_tt_bytes_unchanged=True,
        trust='Untrusted extraction policy, no safe Agda premise'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','build','samples']);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve()
    if a.mode=='prepare':prepare(out)
    else:
        plan=json.loads((out/'source-plan.json').read_text())
        assert plan['policy_driver_sha256']==common.sha(__file__)
        assert plan['sample_driver_sha256']==common.sha(Path(__file__).with_name('endgame16_screen6.py'))
        (common.build if a.mode=='build' else samples)(out)
