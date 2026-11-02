"""Historical heuristic costs with persistent memo; native graph validation is unchanged."""
import argparse
import json
from pathlib import Path
import shutil

import reuse_query_layout6 as reuse
from run_job import atomic_json, utc

base = reuse.q.base
base.HELPERS = [*base.HELPERS, 'historical_query_layout6.py']
previous_generated = reuse.generated
previous_command = base.command


def generated(pins):
    original = previous_generated(pins)
    patches = [
        ('#define COST_BITS 22', '#define COST_BITS 24'),
        ('typedef struct {u64 key;uint32_t cost;uint64_t epoch;} CostEntry;',
         'typedef struct {u64 key;uint32_t cost;} CostEntry;'),
        ('static uint64_t proof_epoch;\n', ''),
        ('entry->epoch==proof_epoch && ', ''),
        ('entry->epoch=proof_epoch;', ''),
        ('proof_epoch=0;', ''),
        ('proof_epoch++; ', ''),
        ('/* Return min(exact forcing-tree cost,limit); reaching limit means unknown. */',
         '/* Historical witness-cost guidance, not exact current minima.\n'
         '   Stale pruning may miss improvements; selected moves still require bound_holds. */'),
        ('size_t id=prefix_count++; prefix_slots[slot]=(uint32_t)(id+1);',
         'size_t id=prefix_count++; prefix_slots[slot]=(uint32_t)(id+1);\n'
         '  if((id&65535)==0)fprintf(stderr,"censored prefix states=%zu native_cpu=%.3f\\n",prefix_count,(double)(clock()-oracle_start)/CLOCKS_PER_SEC);'),
    ]
    changed = original
    for old, new in patches:
        expected = 2 if old in ('entry->epoch==proof_epoch && ', 'proof_epoch++; ') else 1
        assert changed.count(old) == expected, old
        changed = changed.replace(old, new)
    assert 'proof_epoch' not in changed and 'entry->epoch' not in changed
    # Removal patches overlap empty strings, so reversibility is checked by
    # reconstructing the exact expected delta from the unchanged pinned input.
    expected = original
    for old, new in patches:
        expected = expected.replace(old, new)
    assert changed == expected
    return changed


base.generated = generated


def command(*args, **kwargs):
    argv = previous_command(*args, **kwargs)
    index = argv.index('--max-memory-mb')+1
    if argv[index] == '256':
        argv[index] = '512'
    return argv


base.command = command


def prepare(out):
    reuse.prepare(out)
    plan = json.loads((out/'source-plan.json').read_text())
    plan.update(cost_memo_bytes=256*2**20, cost_cache_epoch_invalidated_on_prefix_completion=False,
        cost_estimates='Historical heuristic upper estimates and stale pruning hints; no exact-current-cost claim',
        stale_pruning_can_miss_better_moves=True, native_bound_and_leaf_validation_unchanged=True,
        query_step_cap=100000, fixture_native_memory_mib=512,
        progress_is_censored_and_never_a_complete_forecast=True,
        accepted_proof=False, initial_theorem_claim=False, production_go=False)
    atomic_json(out/'source-plan.json', plan)


def install_storage_guard(out):
    snapshot = base.resources.storage()
    omitted = []
    for pattern in ['path-splice-probe6-20261018*', 'step-assembly-probe6-20261018*',
                    'encoded-step-assembly-probe6-20261018*', 'query-layout6-20261018*',
                    'reuse-query-layout6-20261018*', 'global-reuse-layout6-20261018*',
                    'inline-scaling6-20261018*', 'inline-compact-scaling6-20261018*']:
        omitted.extend((base.ROOT/'results').glob(pattern))
    omitted_bytes = sum(base.resources.batch.allocated(p) for p in set(omitted))
    upper = snapshot['allocated_study_bytes']+omitted_bytes+base.resources.batch.allocated(out)+32*2**20
    assert upper < 12*2**30 and shutil.disk_usage(base.ROOT).free-16*2**20 >= 80*2**30
    atomic_json(out/'storage-freeze.json', dict(created_utc=utc(), snapshot=snapshot,
        omitted_roots=[str(p) for p in sorted(set(omitted))], omitted_allocated_bytes=omitted_bytes,
        conservative_allocated_study_upper_bound_bytes=upper,
        fresh_growth_allowance_bytes=32*2**20, own_output_cap_bytes=8*2**20,
        free_disk_floor_gib=80, scope='Prior roots immutable; future writes bounded to own output and coordinator metadata'))

    def fast_storage(reserve=0):
        free = shutil.disk_usage(base.ROOT).free
        assert free-reserve >= 80*2**30 and upper < 12*2**30
        return dict(conservative_allocated_study_upper_bound_bytes=upper, free_bytes=free, reserve=reserve)
    base.resources.storage = fast_storage


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'build', 'fixture', 'lower', 'upper'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.mode == 'prepare':
        prepare(out)
    elif args.mode in ['build', 'fixture']:
        getattr(base, args.mode)(out)
    else:
        install_storage_guard(out)
        # Keep inherited command caps below the original phase maxima.
        native_command = base.command
        phase_cap = 1450 if args.mode == 'lower' else 1550
        def bounded_command(*pos, **kw):
            argv = native_command(*pos, **kw)
            if '--load-tt' in argv:
                argv[argv.index('--max-cpu-seconds')+1] = str(phase_cap)
            return argv
        base.command = bounded_command
        base.initial(out, args.mode)
