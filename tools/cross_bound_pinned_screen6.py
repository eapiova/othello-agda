"""One correction: retain suffix pins while emitting the closed native graphs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import cross_bound_screen6 as base
from run_job import atomic_json, utc

base.PLIES = [20, 18, 16, 14]


def prepare(out):
    base.prepare(out)
    plan = json.loads((out/'source-plan.json').read_text())
    original = (base.DONOR/'census.c').read_text()
    old = 'if(!wire_enabled)return -1;u64 key=census_key(P,O,turn);'
    new = '/* suffix screen: retain existing pins in frontier mode */ u64 key=census_key(P,O,turn);'
    assert original.count(old) == 1
    changed = original.replace(old, new, 1)
    assert changed.count(new) == 1 and changed.replace(new, old, 1) == original
    (out/'census.c').write_text(changed)
    plan.update(native_binary=str(out/'census'), native_binary_sha256=None,
        native_source_sha256=base.sha(out/'census.c'),
        original_native_source_sha256=base.sha(base.DONOR/'census.c'),
        original_native_binary_sha256=base.sha(base.DONOR/'census'),
        suffix_pins_enabled_in_frontier_mode=True,
        only_delta='Apply existing fail-closed line pins also with wire_enabled false',
        prior_scope_roots=['results/cross-bound-screen6-20261018','results/cross-bound-deeper-screen6-20261018'],
        scope_cpu_cap=100)
    plan['helpers']['cross_bound_pinned_screen6.py'] = base.sha(__file__)
    atomic_json(out/'source-plan.json', plan)


def build(out):
    plan = json.loads((out/'source-plan.json').read_text())
    assert plan['native_binary_sha256'] is None
    assert base.sha(out/'census.c') == plan['native_source_sha256']
    assert all(base.sha(base.ROOT/'tools'/n) == h for n, h in plan['helpers'].items())
    before = base.sha(out/'source-plan.json')
    cc = Path(shutil.which('cc')).resolve(strict=True)
    flags = json.loads((base.DONOR/'build.json').read_text())['flags']
    argv = [str(cc), *flags, str(out/'census.c'), '-o', str(out/'census')]
    done = subprocess.run(argv, capture_output=True, text=True, timeout=25)
    assert done.returncode == 0, done.stderr
    plan['native_binary_sha256'] = base.sha(out/'census')
    atomic_json(out/'source-plan.json', plan)
    atomic_json(out/'build.json', dict(created_utc=utc(), command=argv, flags=flags,
        compiler=str(cc), compiler_sha256=base.sha(cc), stderr=done.stderr,
        source_plan_before_binary_hash=before, source_plan_sha256=base.sha(out/'source-plan.json'),
        native_source_sha256=plan['native_source_sha256'], binary_sha256=plan['native_binary_sha256'],
        accepted_proof=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'build', 'run'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.mode == 'prepare':
        prepare(out)
    elif args.mode == 'build':
        build(out)
    else:
        built = json.loads((out/'build.json').read_text())
        assert built['source_plan_sha256'] == base.sha(out/'source-plan.json')
        assert built['native_source_sha256'] == base.sha(out/'census.c')
        assert built['binary_sha256'] == base.sha(out/'census')
        base.run(out)
