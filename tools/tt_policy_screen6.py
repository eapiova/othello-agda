"""Untrusted oracle-move alignment above eight empties; exact cost below."""
import argparse
import json
from pathlib import Path

import memo_reuse_screen6 as common
from run_job import atomic_json, utc

NEW = r'''
  if(popc(~(P|O)&REGION)>8) {
    int target=lower?threshold:-threshold,empties=popc(~(P|O)&REGION);
    TTE *entry=tt_probe(P,O,empties);
    if(!entry || entry->lo<target) {
      native_calls++;
      solve(P,O,target-1,target);
      if(oracle_aborted)return census_pick_move(P,O,moves,own);
      entry=tt_probe(P,O,empties);
    }
    if(entry && entry->lo>=target && entry->move<64) {
      u64 preferred=1ULL<<entry->move;
      if(preferred&moves)return preferred;
    }
    return census_pick_move(P,O,moves,own);
  }
'''


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    previous = Path(__file__).resolve().parents[1]/'results/endgame-cost-screen6-20261018'
    old_plan = json.loads((previous/'source-plan.json').read_text())
    original = previous/'reuse.c'
    assert common.sha(original) == old_plan['reuse_sha256']
    baseline = original.read_text()
    old = '  if(popc(~(P|O)&REGION)>8)return census_pick_move(P,O,moves,own);'
    assert baseline.count(old) == 1
    source = baseline.replace(old, NEW, 1)
    assert source.replace(NEW, old, 1) == baseline
    (out/'baseline.c').write_text(baseline)
    (out/'reuse.c').write_text(source)
    atomic_json(out/'source-plan.json', dict(created_utc=utc(),
        helper_sha256=common.sha(common.__file__), policy_driver_sha256=common.sha(__file__),
        reference_source_sha256=old_plan['reference_source_sha256'],
        generator_sha256=old_plan['generator_sha256'],
        input_c_source=str(original), input_c_sha256=common.sha(original),
        baseline_sha256=common.sha(out/'baseline.c'), reuse_sha256=common.sha(out/'reuse.c'),
        reversible_delta=True, solver_rules_tt_bytes_unchanged=True,
        baseline_policy='Exact small-endgame tree cost, minimum replies above eight empties.',
        new_policy='Exact small-endgame tree cost, threshold-winning oracle TT move above eight empties.',
        trust='Untrusted native policy; no kernel evidence or initial theorem'))


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
