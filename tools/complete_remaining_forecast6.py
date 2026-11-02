"""Freeze remaining fixed-map work from measured, independently checked batches.

AI-assisted planning only: no production reservation or mathematical claim.
"""
import json,math,shutil
from pathlib import Path
import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
from run_job import atomic_json,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')


def freeze():
    common.OUT=ROOT/'results/audit-no-output6-20261018'
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}|{Path(e['path']) for e in registry['roots']}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    budget=Ledger.summary(json.loads((ROOT/'results/study6-ledger.json').read_text()))
    assert not budget['outstanding']
    scope_path=BASE/'full-row-storage-recovery6-20261018/closure.json'
    if not scope_path.exists():
        scope_path=BASE/'private-core-package6-20261018/closure.json'
    scope=json.loads(scope_path.read_text())
    assert scope['accepted'] and scope['combined_scope_cpu_seconds']<6000
    slope=0.00018929567729698732;warm=8.5838
    offsets={'upper':13.59055597511358,'lower':13.98323455275462}
    owned={'upper':{6,100,300,500,652},'lower':{6,100,300,686}}
    sides={};total_cpu=total_cache=0
    for side,pilot in [('upper','complete-row-preflight6-20261018'),('lower','complete-lower-batch6-20261018')]:
        index=json.loads((ROOT/('results/complete-'+side+'-row-sources-index6-20261018.json')).read_text())
        manifest=json.loads(Path(index['manifest']).read_text())
        remaining={g:e for g,e in manifest['cases'].items() if int(g) not in owned[side]}
        items=sorted((e['tokens'],int(g)) for g,e in remaining.items())
        batches=[];i,j=0,len(items)-1
        while i<=j:
            tokens,g=items[j];j-=1;groups=[g]
            if i<=j and tokens+items[i][0]<=450000:
                tokens+=items[i][0];groups.append(items[i][1]);i+=1
            batches.append(dict(groups=groups,tokens=tokens))
        assert sorted(g for b in batches for g in b['groups'])==sorted(map(int,remaining))
        assert all(b['tokens']<=450000 for b in batches)
        cpu=sum(warm+len(b['groups'])*(offsets[side]-warm)+slope*b['tokens'] for b in batches)
        lineage=json.loads((BASE/pilot/'row-interface-payload-lineage.json').read_text())
        maximum=max(e['new_bytes'] for e in lineage.values())
        cache=math.ceil(1.05*maximum)*len(remaining)
        sides[side]=dict(remaining_groups=len(remaining),remaining_owner_rows=sum(e['rows'] for e in remaining.values()),
            remaining_tokens=sum(e['tokens'] for e in remaining.values()),batch_count=len(batches),
            batch_token_cap=450000,batches=batches,predicted_checker_cpu_seconds=cpu,
            max_measured_row_frame_bytes=maximum,forecast_row_frame_bytes_with_5_percent_margin=math.ceil(1.05*maximum),
            predicted_new_row_cache_bytes=cache,source_index=index)
        total_cpu+=cpu;total_cache+=cache
    private_path=BASE/'private-core-package6-20261018'
    private_bytes=batch.allocated(private_path)
    private_closure=json.loads((private_path/'closure.json').read_text())
    assert private_closure['accepted'] and private_bytes<2*2**20
    storage=dict(allocated_study_bytes=used,retained_cap_bytes=12*2**30,headroom_bytes=12*2**30-used,
        projected_row_cache_bytes=total_cache,cache_container_and_lineage_overhead_bytes=512*1024,
        future_closed_record_archive_cap_bytes=4*2**20,batch_scratch_cap_bytes=3*2**20,
        final_assembly_interface_cap_bytes=4*2**20,
        private_core_original_allowance_bytes=2*2**20,
        private_core_realized_bytes=private_bytes,
        private_core_package_in_baseline=True,
        private_core_source_package_allowance_bytes=2*2**20-private_bytes,
        stop_reserve_bytes=4*2**20,single_checker_proposal=True,
        grouped_streaming_closed_record_archive_required=True,
        data_only_Body_interface_eviction_after_closed_batch_required=True,
        source_and_all_mathematical_payloads_retained=True)
    storage['projected_peak_additional_bytes']=total_cache+sum(storage[k] for k in [
        'cache_container_and_lineage_overhead_bytes','future_closed_record_archive_cap_bytes','batch_scratch_cap_bytes',
        'final_assembly_interface_cap_bytes','private_core_source_package_allowance_bytes','stop_reserve_bytes'])
    storage['model_fits_current_headroom']=storage['projected_peak_additional_bytes']<storage['headroom_bytes']
    storage['remaining_margin_bytes']=storage['headroom_bytes']-storage['projected_peak_additional_bytes']
    storage.update(root_free_bytes=shutil.disk_usage(ROOT).free,root_floor_bytes=80*2**30)
    result=dict(format='othello-complete-remaining-row-forecast-v1',recorded_utc=utc(),side=sides,
        owned_groups={s:sorted(v) for s,v in owned.items()},
        model=dict(cpu_per_token=slope,offset_cpu_seconds=offsets,warm_import_cpu_seconds=warm,
            upper_batch_error_percent=2.1433705743438574,lower_batch_error_percent=1.851675262721404,
            strict_component_error_gate_percent=30,old_failed_forecasts_retained=True),
        predicted_remaining_checker_cpu_seconds=total_cpu,proposed_production_kernel_reservation_cpu_seconds=50000,
        proposed_outer_cpu_cap_seconds=49500,total_cpu_allocation_unchanged=172800,
        proposed_unused_category_reallocation=dict(compiled_to_kernel_cpu_seconds=8000,native_to_kernel_cpu_seconds=5000,applied=False),
        measured_full_body_layout_peak_rss_gib=4.914501190185547,full_initial_theorem_not_checked=True,
        storage=storage,budget=budget,cumulative_calibration_scope_cpu_seconds=scope['combined_scope_cpu_seconds'],
        cumulative_calibration_scope_cap=6000,production_go=False,
        remaining_action='Implement/audit bounded resumable production harness with real build locks, pinned inputs, grouped closed-record archive, payload-preserving cache compaction and physical guards. Freeze final stage caps and apply recorded category transfer before any production reservation.',
        mathematical_objective_complete=False)
    atomic_json(ROOT/'results/complete-remaining-row-forecast6-20261018.json',result)
    print(json.dumps(dict(cpu_prediction=total_cpu,groups={s:d['remaining_groups'] for s,d in sides.items()},
        batches={s:d['batch_count'] for s,d in sides.items()},storage=storage,global_available_cpu=budget['available_cpu_seconds'])))


if __name__=='__main__':freeze()
