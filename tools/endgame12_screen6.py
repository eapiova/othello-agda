"""Untrusted forcing-tree minimization: compare eight and twelve empty cells."""
import argparse
import json
from pathlib import Path

import memo_reuse_screen6 as common
from run_job import atomic_json, utc


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    previous = Path(__file__).resolve().parents[1]/'results/endgame-cost-screen6-20261018'
    plan = json.loads((previous/'source-plan.json').read_text())
    original = previous/'reuse.c'
    assert common.sha(original) == plan['reuse_sha256']
    baseline = original.read_text()
    old = 'if(popc(~(P|O)&REGION)>8)return census_pick_move(P,O,moves,own);'
    new = 'if(popc(~(P|O)&REGION)>12)return census_pick_move(P,O,moves,own);'
    assert baseline.count(old) == 1
    changed = baseline.replace(old, new, 1)
    assert changed.replace(new, old, 1) == baseline
    (out/'baseline.c').write_text(baseline)
    (out/'reuse.c').write_text(changed)
    atomic_json(out/'source-plan.json', dict(created_utc=utc(),
        helper_sha256=common.sha(common.__file__), policy_driver_sha256=common.sha(__file__),
        reference_source_sha256=plan['reference_source_sha256'], generator_sha256=plan['generator_sha256'],
        input_c_source=str(original), input_c_sha256=common.sha(original),
        baseline_sha256=common.sha(out/'baseline.c'), reuse_sha256=common.sha(out/'reuse.c'),
        baseline_cutoff=8, variant_cutoff=12, cost_memo_bytes=67108864,
        reversible_delta=True, solver_rules_tt_bytes_unchanged=True,
        trust='Untrusted native policy comparison, no safe Agda premise'))


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
