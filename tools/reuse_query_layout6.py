"""Bounded cost queries reusing completed exact-key prefix subgraphs."""
import argparse
import json
from pathlib import Path

import query_layout6 as q


previous_generated = q.generated
q.base.HELPERS = [*q.base.HELPERS, 'reuse_query_layout6.py']


COMPLETED_HELPER = r'''
/* Exact 59-bit same-goal lookup; active prefix entries are not complete. */
static int completed_canonical(u64 P,u64 O,int turn,int lower,int threshold) {
  u64 key=census_key(P,O,turn);
  u64 h=hashkey(P,O)^((u64)(threshold+36)<<2)^(u64)(turn*2+lower);
  size_t slot=(size_t)h&(prefix_slot_count-1);
  while(prefix_slots[slot]) {
    size_t id=prefix_slots[slot]-1;
    if((prefix[id].key&CENSUS_STATE_MASK)==key &&
       !(prefix[id].key&CENSUS_ACTIVE))return 1;
    slot=(slot+1)&(prefix_slot_count-1);
  }
  return 0;
}
static int completed(u64 P,u64 O,int turn,int lower,int threshold) {
  census_canonical(&P,&O);
  return completed_canonical(P,O,turn,lower,threshold);
}
'''


REUSE_PICK = r'''
static u64 reuse_cost_pick(u64 P,u64 O,u64 moves,int own,int turn,int lower,int threshold) {
  if(!own)return moves&-moves;
  u64 candidates=moves,known=0;
  while(candidates) {
    u64 m=candidates&-candidates;candidates^=m;
    u64 f=gen_flips(P,O,m);
    if(completed(O^f,P^f^m,!turn,lower,threshold))known|=m;
  }
  if(known)return census_pick_move(P,O,known,own);
  return cost_pick_move(P,O,moves,own,turn,lower,threshold);
}
'''


def generated(pins):
    source = previous_generated(pins)
    patches = [
        ('typedef struct {u64 key;uint32_t cost;} CostEntry;',
         COMPLETED_HELPER + '\n'
         'typedef struct {u64 key;uint32_t cost;uint64_t epoch;} CostEntry;'),
        ('static CostEntry *cost_memo;',
         'static CostEntry *cost_memo;\nstatic uint64_t proof_epoch;'),
        ('  census_canonical(&P,&O);\n  u64 key=census_key(P,O,turn);',
         '  census_canonical(&P,&O);\n'
         '  if(completed_canonical(P,O,turn,lower,threshold))return 1;\n'
         '  u64 key=census_key(P,O,turn);'),
        ('int same=(entry->key&COST_VALID) && ((entry->key&~(COST_VALID|COST_EXACT))==key);',
         'int same=(entry->key&COST_VALID) && entry->epoch==proof_epoch && ((entry->key&~(COST_VALID|COST_EXACT))==key);'),
        ('int still_same=(entry->key&COST_VALID) && ((entry->key&~(COST_VALID|COST_EXACT))==key);',
         'int still_same=(entry->key&COST_VALID) && entry->epoch==proof_epoch && ((entry->key&~(COST_VALID|COST_EXACT))==key);'),
        ('entry->key=key|COST_VALID|(answer<limit?COST_EXACT:0);entry->cost=answer;',
         'entry->key=key|COST_VALID|(answer<limit?COST_EXACT:0);entry->cost=answer;entry->epoch=proof_epoch;'),
        ('static const struct {u64 key;int lower,index;} wire_pins[]=',
         REUSE_PICK + '\nstatic const struct {u64 key;int lower,index;} wire_pins[]='),
        ('if(pin<0)return cost_pick_move(P,O,moves,own,turn,lower,threshold);',
         'if(pin<0)return reuse_cost_pick(P,O,moves,own,turn,lower,threshold);'),
        ('    free(cost_memo);cost_memo=NULL;',
         '    free(cost_memo);cost_memo=NULL;proof_epoch=0;'),
    ]
    changed = source
    for old, new in patches:
        assert changed.count(old) == 1, old[:100]
        changed = changed.replace(old, new, 1)

    finalizer = 's->key&=~CENSUS_ACTIVE; wire_finished(id); return id;'
    replacement = 's->key&=~CENSUS_ACTIVE; proof_epoch++; wire_finished(id); return id;'
    assert changed.count(finalizer) == 2
    changed = changed.replace(finalizer, replacement)

    restored = changed.replace(replacement, finalizer)
    for old, new in reversed(patches):
        assert restored.count(new) == 1, new[:100]
        restored = restored.replace(new, old, 1)
    assert restored == source
    return changed


q.base.generated = generated


def prepare(out):
    q.prepare(out)
    plan = json.loads((out/'source-plan.json').read_text())
    plan.update(
        completed_subgraph_preference=True,
        completed_lookup='exact 59-bit canonical key, absolute turn and fixed same-run direction/threshold goal',
        active_prefix_entries_ignored=True,
        cost_cache_epoch_invalidated_on_prefix_completion=True,
        completed_subgraph_cost_unit=1,
        completed_subgraph_cost_semantics='abstract citation unit, not a precise serialized token forecast',
        query_step_cap=q.QUERY_STEPS,
        cost_memo_bytes=96*2**20,
        accepted_proof=False,
        initial_theorem_claim=False,
        production_go=False,
        trust='Untrusted extraction guidance only; completed native subgraphs are never Agda premises')
    q.atomic_json(out/'source-plan.json', plan)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['prepare', 'build', 'fixture', 'lower', 'upper'])
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    if a.mode == 'prepare':
        prepare(out)
    elif a.mode in ['build', 'fixture']:
        getattr(q.base, a.mode)(out)
    else:
        q.install_storage_guard(out)
        q.base.initial(out, a.mode)
