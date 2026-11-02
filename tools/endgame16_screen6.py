"""Untrusted forcing-tree minimization: compare twelve and sixteen empty cells."""
import argparse
import json
import subprocess
from memo_reuse_screen6 import sha, fixtures
from pathlib import Path

import memo_reuse_screen6 as common
from run_job import atomic_json, utc


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    previous = Path(__file__).resolve().parents[1]/'results/endgame12-screen6-20261018'
    plan = json.loads((previous/'source-plan.json').read_text())
    original = previous/'reuse.c'
    assert common.sha(original) == plan['reuse_sha256']
    baseline = original.read_text()
    old = 'if(popc(~(P|O)&REGION)>12)return census_pick_move(P,O,moves,own);'
    new = 'if(popc(~(P|O)&REGION)>16)return census_pick_move(P,O,moves,own);'
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
        baseline_cutoff=12, variant_cutoff=16, cost_memo_bytes=67108864,
        reversible_delta=True, solver_rules_tt_bytes_unchanged=True,
        trust='Untrusted native policy comparison, no safe Agda premise'))


def samples(out):
    out = Path(out)
    built = json.loads((out/'build.json').read_text())
    plan = json.loads((out/'source-plan.json').read_text())
    assert built['source_plan_sha256'] == sha(out/'source-plan.json') and plan['helper_sha256'] == common.sha(common.__file__)
    results = []
    for ident, state, _ in fixtures.LOWER_CASES:
        case = dict(id=ident, state=state, variants={})
        for name in ['baseline', 'reuse']:
            assert sha(out/name) == built['entries'][name]['binary_sha256']
            argv = [str(out/name), 'frontier', '--position', state[1:], '--turn', 'black',
                    '--direction', 'lower', '--threshold', '4', '--frontier-discs', '36',
                    '--max-states', '1000000', '--max-nodes', '1000000000',
                    '--max-memory-mb', '256', '--max-cpu-seconds', '40',
                    '--tt-bits', '18', '--small', '4', '--deep-order', '5', '--emit-states', '0']
            done = subprocess.run(argv, capture_output=True, text=True, timeout=60)
            counts = json.loads(done.stdout)
            case['variants'][name] = dict(command=argv, exit_code=done.returncode,
                counts=counts, stderr=done.stderr)
            atomic_json(out/'progress.json', dict(cases=results+[case], accepted_proof=False))
            assert done.returncode == 0 and counts['complete'] and counts['root_validated'] and counts['root_holds']
        results.append(case)
    atomic_json(out/'samples.json', dict(format='othello-memo-reuse-screen6-v1',
        created_utc=utc(), cases=results, build_sha256=sha(out/'build.json'),
        policy='Exact forcing-tree cost below12 versus16 empty cells; untrusted policy comparison.',
        accepted_proof=False, new_distinct_rows=0, mathematical_objective_complete=False,
        trust='Untrusted native census, no full-game forecast or proof premise.'))


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
        (common.build if args.mode == 'build' else samples)(out)
