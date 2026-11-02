"""Bound individual cost queries and avoid repeated scans of closed artifacts."""
import argparse
import json
from pathlib import Path
import shutil

import bounded_layout6 as base
import capped_cost_screen6 as cost
from run_job import atomic_json,utc

QUERY_STEPS=100000
original_generated=base.generated
base.HELPERS=[*base.HELPERS,'query_layout6.py']


def generated(pins):
    source=original_generated(pins)
    original=cost.HELPER
    changed=original
    patches=[
        ('static CostEntry *cost_memo;',
         'static CostEntry *cost_memo;\nstatic uint32_t cost_query_steps;\nstatic int cost_query_aborted;'),
        ('  if(limit<=1 || oracle_stop())return limit;',
         '  if(limit<=1)return limit;\n  if(cost_query_aborted || cost_query_steps++>='+str(QUERY_STEPS)+'){cost_query_aborted=1;return limit;}\n  if(oracle_stop())return limit;'),
        ('while(moves && !oracle_aborted)', 'while(moves && !oracle_aborted && !cost_query_aborted)'),
        ('  if(!oracle_aborted) {',
         '  if(cost_query_aborted || oracle_aborted)return limit;\n  if(!oracle_aborted) {'),
        ('    uint32_t cost=forcing_cost(cp,co,!turn,lower,threshold,limit);',
         '    cost_query_steps=0;cost_query_aborted=0;\n    uint32_t cost=forcing_cost(cp,co,!turn,lower,threshold,limit);')]
    for a,b in patches:
        assert changed.count(a)==(2 if a.startswith('while(moves') else 1),a
        changed=changed.replace(a,b)
    restored=changed
    for a,b in reversed(patches):restored=restored.replace(b,a)
    assert restored==original and source.count(original)==1
    return source.replace(original,changed,1)

base.generated=generated


def prepare(out):
    base.prepare(out)
    plan=json.loads((out/'source-plan.json').read_text())
    plan.update(query_step_cap=QUERY_STEPS,aborted_query_results_never_cached_or_selected=True,
        resource_guard='One scan of closed study data, reserve32MiB concurrent artifacts, monitor free disk and own output every3s; no writes outside own output.')
    atomic_json(out/'source-plan.json',plan)


def install_storage_guard(out):
    # All native descendants have / read-only and only this output writable.
    # Reserve32MiB for this <=8MiB output and bounded coordinator artifacts.
    # The diagnostic helper's per-probe output cap is 16MiB. Our 32MiB
    # allowance covers several outputs, so apply it to the aggregate here.
    snapshot=base.resources.storage()
    own=base.resources.batch.allocated(out)
    upper=snapshot['allocated_study_bytes']+own+32*2**20
    assert upper<12*2**30
    assert shutil.disk_usage(base.ROOT).free-32*2**20>=80*2**30
    atomic_json(out/'storage-freeze.json',dict(created_utc=utc(),snapshot=snapshot,
        conservative_allocated_study_upper_bound_bytes=upper,concurrent_artifact_allowance_bytes=32*2**20,
        own_output_cap_bytes=8*2**20,free_disk_floor_gib=80,scope='Closed prior artifacts remain immutable; all writes bounded to own output.'))
    def fast_storage(reserve=0):
        free=shutil.disk_usage(base.ROOT).free
        assert free-reserve>=80*2**30 and upper<12*2**30
        return dict(conservative_allocated_study_upper_bound_bytes=upper,free_bytes=free,reserve=reserve)
    base.resources.storage=fast_storage


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','build','fixture','lower','upper']);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve()
    if a.mode=='prepare':prepare(out)
    elif a.mode in ['build','fixture']:getattr(base,a.mode)(out)
    else:
        install_storage_guard(out)
        base.initial(out,a.mode)
