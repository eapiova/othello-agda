"""Reuse the exact accepted native binary for the missing UPPER layout count.

Counts are untrusted extraction evidence, never a proof premise or production GO.
The original global-reuse family cap remains5650 CPU seconds.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import shutil

import global_reuse_layout6 as original
from run_job import atomic_json, utc

base = original.base
ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT/'results/global-reuse-layout6-20261018'
EXTRAS = ['path-splice-probe6-20261018*', 'step-assembly-probe6-20261018*',
    'encoded-step-assembly-probe6-20261018*', 'query-layout6-20261018*',
    'reuse-query-layout6-20261018*', 'global-reuse-layout6-20261018*',
    'historical-query-layout6-20261018*', 'cross-bound*6-20261018*',
    'inline-scaling6-20261018*', 'inline-compact-scaling6-20261018*',
    'inline-boundary-scaling6-20261018*', 'degree-reuse-layout6-20261018*',
    'primitive-arithmetic-probe6-20261018*', 'primitive-arithmetic-boolean-probe6-20261018*',
    'contiguous-rows-probe6-20261018*', 'contiguous-explicit-rows-probe6-20261018*']


def prepare(out):
    assert not out.exists()
    old = json.loads((DONOR/'closure.json').read_text())
    degree = json.loads((ROOT/'results/degree-reuse-layout6-20261018/closure.json').read_text())
    assert old['lower_counts_complete'] and not old['accepted_proof']
    assert degree['family_cap_cpu_seconds'] == 5650
    prior = degree['combined_family_cpu_seconds']
    assert prior+2750+300 <= 5650
    base.checked(DONOR)
    snapshot = base.resources.storage()
    roots = {p for pattern in EXTRAS for p in (ROOT/'results').glob(pattern)}
    extra_bytes = sum(base.resources.batch.allocated(p) for p in roots)
    used = snapshot['allocated_study_bytes']+extra_bytes
    assert used+16*2**20 < 12*2**30
    assert shutil.disk_usage(ROOT).free-16*2**20 >= 80*2**30
    out.mkdir(parents=True)
    copied = {}
    for name in ['census', 'census.c', 'source-plan.json', 'build.json', 'fixture.json']:
        shutil.copy2(DONOR/name, out/name)
        copied[name] = base.sha(out/name)
        assert copied[name] == base.sha(DONOR/name)
    base.checked(out)
    history = json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    atomic_json(out/'storage-freeze.json', dict(created_utc=utc(), legacy_snapshot=snapshot,
        extra_roots=[str(p) for p in sorted(roots)], extra_allocated_bytes=extra_bytes,
        prior_allocated_study_bytes=used, own_output_cap_bytes=8*2**20,
        free_disk_floor_gib=80, retained_study_cap_gib=12))
    atomic_json(out/'continuation-plan.json', dict(created_utc=utc(),
        original_family_root=str(DONOR), original_family_cpu_cap=5650,
        previous_combined_family_cpu_seconds=prior,
        native_reservation_seconds=2750, native_cpu_cap_seconds=2500,
        outer_cpu_cap_seconds=2600, new_controller_allowance_seconds=300,
        combined_reserved_family_envelope_seconds=prior+2750+300,
        hard_memory_gib=9, swap_bytes=0, core_bytes=0,
        reused_build_without_new_compilation=True, copied_exact_artifacts=copied,
        original_build_command_paths_retained_as_evidence=True,
        fresh_helper_sha256={Path(__file__).name: base.sha(__file__)},
        p1_files=history['p1_files'], all34_line_state_ownership_cuts='OPEN',
        counts_only=True, wire_export_allowed=False, accepted_proof=False,
        production_go=False, mathematical_objective_complete=False))


def run(out):
    plan = json.loads((out/'continuation-plan.json').read_text())
    assert all(base.sha(ROOT/'tools'/n) == h for n, h in plan['fresh_helper_sha256'].items())
    assert all(base.sha(out/n) == h for n, h in plan['copied_exact_artifacts'].items())
    assert all(base.sha(ROOT/n) == h for n, h in plan['p1_files'].items())
    group = Path('/sys/fs/cgroup')/next(line[3:].lstrip('/') for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
    assert (group/'memory.max').read_text().strip() == str(9*2**30)
    assert (group/'memory.swap.max').read_text().strip() == '0'
    assert resource.getrlimit(resource.RLIMIT_CORE) == (0, 0)
    frozen = json.loads((out/'storage-freeze.json').read_text())

    def storage(reserve=0):
        own = base.resources.batch.allocated(out)
        free = shutil.disk_usage(ROOT).free
        assert own+reserve <= 16*2**20 and own <= 8*2**20
        assert frozen['prior_allocated_study_bytes']+own+reserve < 12*2**30
        assert free-reserve >= 80*2**30
        available = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
        assert available >= 2*2**30
        return dict(allocated_study_bytes=frozen['prior_allocated_study_bytes']+own,
            own_output_bytes=own, free_bytes=free, reserved_bytes=reserve)

    base.resources.storage = storage
    storage(8*2**20)
    failure = None
    try:
        base.initial(out, 'upper')
    except Exception as error:
        failure = repr(error)
    p1 = all(base.sha(ROOT/n) == h for n, h in plan['p1_files'].items())
    exact = all(base.sha(out/n) == h for n, h in plan['copied_exact_artifacts'].items())
    helpers = all(base.sha(ROOT/'tools'/n) == h for n, h in plan['fresh_helper_sha256'].items())
    result_path = out/'upper.json'
    complete = result_path.exists() and json.loads(result_path.read_text())['complete']
    atomic_json(out/'report.json', dict(created_utc=utc(), upper_counts_complete=complete,
        p1_unchanged=p1, borrowed_exact_artifacts_unchanged=exact,
        fresh_helpers_unchanged=helpers, failure=failure,
        accepted_proof=False, new_distinct_rows=0,
        mathematical_objective_complete=False))
    assert p1 and exact and helpers and complete and failure is None, 'Upper count incomplete; retain receipt, no complete forecast'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'run'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    (prepare if args.mode == 'prepare' else run)(out)
