"""Untrusted same-memo preference, then largest observed fail-soft margin."""
import argparse
import json
from pathlib import Path

import memo_reuse_screen6 as common
from run_job import atomic_json, utc

MARGIN = r'''
  if(known)return census_pick_move(P,O,known,own);
  int target=lower?threshold:-threshold,best_margin=-65,best_mobility=100;
  u64 best=0;
  candidates=moves;
  while(candidates) {
    u64 m=candidates&-candidates;candidates^=m;
    u64 f=gen_flips(P,O,m),cp=O^f,co=P^f^m;
    native_calls++;
    int margin=-solve(cp,co,-target,-target+1);
    if(oracle_aborted)return m;
    int mobility=popc(gen_moves(cp,co));
    if(margin>=target && (margin>best_margin ||
        (margin==best_margin && mobility<best_mobility))) {
      best=m;best_margin=margin;best_mobility=mobility;
    }
  }
  return best?best:census_pick_move(P,O,moves,own);
'''


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    baseline, _ = common.generated()
    old_return = '  return census_pick_move(P,O,known?known:moves,own);'
    assert common.HELPER.count(old_return) == 1
    helper = common.HELPER.replace(old_return, MARGIN)
    old = 'u64 m=census_pick_move(P,O,moves,own);'
    new = 'u64 m=reuse_pick_move(P,O,moves,own,turn,lower,threshold);'
    source = baseline.replace(common.base.VISIT, helper+'\n'+common.base.VISIT, 1).replace(old, new, 1)
    assert source.replace(helper+'\n', '', 1).replace(new, old, 1) == baseline
    (out/'baseline.c').write_text(baseline)
    (out/'reuse.c').write_text(source)
    atomic_json(out/'source-plan.json', dict(created_utc=utc(),
        helper_sha256=common.sha(common.__file__), policy_driver_sha256=common.sha(__file__),
        reference_source_sha256=common.sha(common.solve6.SOURCE),
        generator_sha256=common.sha(common.base.__file__),
        baseline_sha256=common.sha(out/'baseline.c'), reuse_sha256=common.sha(out/'reuse.c'),
        reversible_delta=True, solver_rules_tt_bytes_unchanged=True,
        policy='Completed exact-key memo preference, then largest null-window fail-soft winning margin; minimum replies breaks ties.',
        trust='Untrusted census policy; no safe Agda premise'))


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
