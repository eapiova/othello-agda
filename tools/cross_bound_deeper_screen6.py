"""One deeper closed-suffix continuation inside the original cross-bound scope."""
import argparse
import json
from pathlib import Path
import cross_bound_screen6 as base
from run_job import atomic_json

base.PLIES = [20, 18, 16, 14]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'run'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.mode == 'prepare':
        base.prepare(out)
        plan = json.loads((out/'source-plan.json').read_text())
        plan['helpers']['cross_bound_deeper_screen6.py'] = base.sha(__file__)
        plan['prior_scope_root'] = str(base.ROOT/'results/cross-bound-screen6-20261018')
        plan['scope_cpu_cap'] = 100
        atomic_json(out/'source-plan.json', plan)
    else:
        base.run(out)
