"""Untrusted census policy preferring already completed same-goal subgraphs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import canonical_census6 as base
import shared_study6 as fixtures
import solve6
from run_job import atomic_json, utc

HELPER = r'''
/* Exact-key same-run memo membership, never a probabilistic fingerprint. */
static int reuse_complete(u64 P,u64 O,int turn,int lower,int threshold) {
  census_canonical(&P,&O);
  u64 key=census_key(P,O,turn);
  u64 h=hashkey(P,O)^((u64)(threshold+36)<<2)^(u64)(turn*2+lower);
  size_t slot=(size_t)h&(prefix_slot_count-1);
  while(prefix_slots[slot]) {
    size_t id=prefix_slots[slot]-1;
    if((prefix[id].key&CENSUS_STATE_MASK)==key)
      return !(prefix[id].key&CENSUS_ACTIVE);
    slot=(slot+1)&(prefix_slot_count-1);
  }
  return 0;
}
static u64 reuse_pick_move(u64 P,u64 O,u64 moves,int own,int turn,int lower,int threshold) {
  if(!own)return moves&-moves;
  u64 candidates=moves,known=0;
  while(candidates) {
    u64 m=candidates&-candidates;candidates^=m;
    u64 f=gen_flips(P,O,m);
    if(reuse_complete(O^f,P^f^m,!turn,lower,threshold))known|=m;
  }
  return census_pick_move(P,O,known?known:moves,own);
}
'''


def generated():
    ordinary = base.generated_source(solve6.SOURCE.read_text(), 'min-replies', compact=True)
    old = 'u64 m=census_pick_move(P,O,moves,own);'
    new = 'u64 m=reuse_pick_move(P,O,moves,own,turn,lower,threshold);'
    assert ordinary.count(base.VISIT) == ordinary.count(old) == 1
    changed = ordinary.replace(base.VISIT, HELPER+'\n'+base.VISIT, 1).replace(old, new, 1)
    assert changed.replace(HELPER+'\n', '', 1).replace(new, old, 1) == ordinary
    return ordinary, changed


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    ordinary, changed = generated()
    (out/'baseline.c').write_text(ordinary)
    (out/'reuse.c').write_text(changed)
    atomic_json(out/'source-plan.json', dict(
        created_utc=utc(), helper_sha256=sha(__file__), reference_source_sha256=sha(solve6.SOURCE),
        generator_sha256=sha(base.__file__), baseline_sha256=sha(out/'baseline.c'),
        reuse_sha256=sha(out/'reuse.c'), reversible_delta=True,
        solver_rules_tt_bytes_unchanged=True, trust='untrusted policy experiment'))


def build(out):
    out = Path(out)
    plan = json.loads((out/'source-plan.json').read_text())
    assert plan['helper_sha256'] == sha(__file__)
    cc = Path(shutil.which('cc')).resolve(strict=True)
    entries = {}
    for name in ['baseline', 'reuse']:
        assert sha(out/(name+'.c')) == plan[name+'_sha256']
        assert not (out/name).exists()
        argv = [str(cc), *solve6.FLAGS, str(out/(name+'.c')), '-o', str(out/name)]
        done = subprocess.run(argv, capture_output=True, text=True, timeout=15)
        assert done.returncode == 0, done.stderr
        entries[name] = dict(binary_sha256=sha(out/name), command=argv, stderr=done.stderr)
    atomic_json(out/'build.json', dict(created_utc=utc(), compiler=str(cc),
        compiler_sha256=sha(cc), flags=list(solve6.FLAGS), entries=entries,
        source_plan_sha256=sha(out/'source-plan.json'), accepted_proof=False))


def samples(out):
    out = Path(out)
    built = json.loads((out/'build.json').read_text())
    plan = json.loads((out/'source-plan.json').read_text())
    assert built['source_plan_sha256'] == sha(out/'source-plan.json') and plan['helper_sha256'] == sha(__file__)
    results = []
    for ident, state, _ in fixtures.LOWER_CASES:
        case = dict(id=ident, state=state, variants={})
        for name in ['baseline', 'reuse']:
            assert sha(out/name) == built['entries'][name]['binary_sha256']
            argv = [str(out/name), 'frontier', '--position', state[1:], '--turn', 'black',
                    '--direction', 'lower', '--threshold', '4', '--frontier-discs', '36',
                    '--max-states', '1000000', '--max-nodes', '1000000000',
                    '--max-memory-mb', '256', '--max-cpu-seconds', '12',
                    '--tt-bits', '18', '--small', '4', '--deep-order', '5', '--emit-states', '0']
            done = subprocess.run(argv, capture_output=True, text=True, timeout=22)
            counts = json.loads(done.stdout)
            case['variants'][name] = dict(command=argv, exit_code=done.returncode,
                counts=counts, stderr=done.stderr)
            atomic_json(out/'progress.json', dict(cases=results+[case], accepted_proof=False))
            assert done.returncode == 0 and counts['complete'] and counts['root_validated'] and counts['root_holds']
        results.append(case)
    atomic_json(out/'samples.json', dict(format='othello-memo-reuse-screen6-v1',
        created_utc=utc(), cases=results, build_sha256=sha(out/'build.json'),
        policy='Prefer completed exact-key same-run child memos, then minimum replies.',
        accepted_proof=False, new_distinct_rows=0, mathematical_objective_complete=False,
        trust='Untrusted native census, no full-game forecast or proof premise.'))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['prepare', 'build', 'samples'])
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    globals()[args.mode](args.out.resolve())
