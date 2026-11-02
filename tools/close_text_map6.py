"""Close completed training/holdout receipts; launches no checker."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
from directed_scaling6 import profiles
from provenance import source_identity, digest_entries
from run_job import atomic_json, utc
from study6 import Ledger
from shared_inline_scaling6 import _interface

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/mnt/data/othello-agda-desktop-artifacts-20261018/text-map-holdout6-20261018-fixed')
PRIOR = ROOT/'results/text-map-scaling6-20261018-fixed'


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    job = json.loads((OUT/'job.json').read_text())
    report = json.loads((OUT/'report.json').read_text())
    assert not (OUT/'closure.json').exists()
    assert all(report[k] for k in ['all_phases_accepted', 'p1_unchanged',
                                   'accepted_donors_unchanged', 'source_unchanged'])
    assert source_identity(OUT/'check') == plan['source']
    batch.donor_snapshot({Path(k): tuple(v) for k, v in plan['donors'].items()})
    train = json.loads((OUT/'forecast-freeze.json').read_text())
    assert common.sha(OUT/'forecast-freeze.json') == json.loads((OUT/'holdout-freeze-pin.json').read_text())['sha256']
    comparison = json.loads((OUT/'comparison-plan.json').read_text())
    parts = comparison['holdout']
    prefix = 'Tests.TextMapHoldoutOnly6'
    log = OUT/'records/tests-textmapholdoutonly6-holdout.log'
    found = profiles(log, prefix)
    donor = json.loads((ROOT/'results/inline-compact-scaling6-20261018/holdout-comparison.json').read_text())
    body_cost = 0
    for p in parts:
        name = f'Tests.InlineCompactScaling6.Part{p}.TextBodies'
        assert name in donor['module_profiles'] or name in donor['omitted_sub_millisecond_text_modules']
        body_cost += donor['module_profiles'].get(name, .001)
    checked = [f'{prefix}.Part{p}.Checked' for p in parts]
    states = [f'{prefix}.Part{p}.States' for p in parts]
    assert all(name in found for name in checked)
    assert all(_interface(OUT/'check', name).exists() for name in states)
    row_cost = body_cost+sum(found[name] for name in checked)
    state_cost = sum(found.get(name, .001) for name in states)
    tokens = sum(comparison['features'][str(p)]['tokens'] for p in parts)
    predicted = train['state_and_row_seconds_per_token']*tokens
    error = abs(predicted-row_cost-state_cost)/(row_cost+state_cost)
    hold = dict(created_utc=utc(), phase='holdout', tokens=tokens,
        exact_profile_log=str(log), exact_profile_log_sha256=common.sha(log),
        module_profiles=found, source_body_and_row_cpu_seconds=row_cost,
        state_source_module_cpu_seconds=state_cost, state_and_body_and_row_cpu_seconds=row_cost+state_cost,
        omitted_sub_millisecond_states=[name for name in states if name not in found],
        omitted_state_allowance_cpu_seconds=.001, reused_body_source_cpu_seconds=body_cost,
        predicted_state_and_row_cpu_seconds=predicted, relative_error=error,
        heldout_component_gate_passed=error <= comparison['heldout_relative_error_tolerance'],
        frozen_forecast_sha256=common.sha(OUT/'forecast-freeze.json'),
        per_part_interface_bytes={str(p): _interface(OUT/'check', f'{prefix}.Part{p}.Checked').stat().st_size for p in parts},
        baseline_per_part_interface_bytes={str(p): _interface(ROOT/'results/shared-inline-scaling6-20261018/check', f'Tests.SharedInlineScaling6.Part{p}.Checked').stat().st_size for p in parts},
        per_part_state_interface_bytes={str(p): _interface(OUT/'check', f'{prefix}.Part{p}.States').stat().st_size for p in parts},
        baseline_per_part_state_interface_bytes={str(p): _interface(ROOT/'results/inline-scaling6-20261018/check', f'Tests.InlineScaling6.Part{p}.States').stat().st_size for p in parts},
        initial_bounds_proved=False, full_workflow_forecast_validated=False,
        whole_map_equality_not_claimed=True)
    assert hold['heldout_component_gate_passed']
    atomic_json(OUT/'holdout-comparison.json', hold)
    interfaces = assembly6.interfaces(OUT/'check')
    assert len(interfaces) == 7
    atomic_json(OUT/'interfaces.json', interfaces)
    frozen = OUT/'frozen-tools'
    frozen.mkdir()
    for name, h in plan['helper_sha256'].items():
        assert common.sha(ROOT/'tools'/name) == h
        shutil.copy2(ROOT/'tools'/name, frozen/name)
    shutil.copy2(__file__, frozen/Path(__file__).name)
    ledger = Ledger(ROOT/'results/study6-ledger.json')
    actual = ledger.finish(job['reservation']['reservation_id'], OUT/'records'/(OUT.name+'.json'))
    combined = plan['previous_combined_scope_cpu_seconds']+actual['actual_cpu_seconds']+5
    assert combined <= 200
    counts = json.loads((ROOT/'results/global-upper-layout6-20261018/combined-planning-scenario.json').read_text())
    new_state = sum(train['per_part_state_interface_bytes'].values())+sum(hold['per_part_state_interface_bytes'].values())
    old_state = sum(train['baseline_per_part_state_interface_bytes'].values())+sum(hold['baseline_per_part_state_interface_bytes'].values())
    new_row = sum(train['per_part_interface_bytes'].values())+sum(hold['per_part_interface_bytes'].values())
    old_row = sum(train['baseline_per_part_interface_bytes'].values())+sum(hold['baseline_per_part_interface_bytes'].values())
    scenario = dict(created_utc=utc(), combined_tokens=counts['combined_tokens'],
        lower_state_and_row_component_cpu_seconds=train['state_and_row_seconds_per_token']*counts['lower_tokens'],
        combined_state_and_row_component_cpu_seconds=train['state_and_row_seconds_per_token']*counts['combined_tokens'],
        old_lower_epoch_only=True, upper_slope_not_validated=True, new_policy_epoch_not_validated=True,
        whole_workflow_forecast_validated=False, global_state_map_imports_assembly_and_artifacts_excluded=True,
        seven_state_interface_bytes=new_state, baseline_seven_state_interface_bytes=old_state,
        seven_checked_interface_bytes=new_row, baseline_shared_seven_checked_interface_bytes=old_row,
        state_and_checked_interface_reduction_fraction=1-(new_state+new_row)/(old_state+old_row),
        production_go=False, mathematical_objective_complete=False)
    atomic_json(OUT/'current-counts-scenario.json', scenario)
    journal = subprocess.check_output(['journalctl', '--user', '-u', job['unit'], '--no-pager', '-n', '8', '-o', 'cat'], text=True)
    (OUT/'service-journal.log').write_text(journal)
    assert shutil.disk_usage(ROOT).free-2**20 >= 80*2**30
    archive = OUT/'accepted-conditional-checkpoint.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for rel in ['check/src', 'check/_build', 'check/othello.agda-lib', 'records', 'plan.json',
                    'job.json', 'report.json', 'interfaces.json', 'frozen-tools', 'service-journal.log',
                    'comparison-plan.json', 'forecast-freeze.json', 'holdout-freeze-pin.json',
                    'holdout-comparison.json', 'current-counts-scenario.json']:
            tar.add(OUT/rel, arcname=rel)
        for rel in ['check/src', 'check/_build', 'plan.json', 'closure.json', 'records',
                    'interfaces.json', 'frozen-tools', 'forecast-freeze.json']:
            tar.add(PRIOR/rel, arcname='prior-accepted-training/'+rel)
    summary = Ledger.summary(json.loads(ledger.path.read_text()))
    assert not summary['outstanding']
    storage = json.loads((OUT/'storage-freeze.json').read_text())
    used = storage['prior_allocated_study_bytes']+batch.allocated(OUT)
    assert batch.allocated(OUT) < 12*2**20 and used < 12*2**30
    closure = dict(format='othello-bounded-probe-closure-v1', closed_utc=utc(), accepted=True,
        note='Text maps use unchanged shared checker;800 old training and600 heldout rows accepted. No new common-map coverage.',
        new_interfaces=7, prior_accepted_training_interfaces=10,
        source_sha256=plan['source']['source_sha256'], interface_pool_sha256=digest_entries(interfaces),
        charged_cpu_seconds=actual['actual_cpu_seconds'],
        previous_combined_scope_cpu_seconds=plan['previous_combined_scope_cpu_seconds'],
        new_controller_allowance_seconds=5, combined_scope_cpu_seconds=combined,
        scope_cap_cpu_seconds=200, conditional_existing_rows=1400, new_distinct_rows=0,
        accepted_donors_unchanged=True, p1_unchanged=True,
        archive=str(archive), archive_bytes=archive.stat().st_size, archive_sha256=common.sha(archive),
        closure_builder_sha256=common.sha(__file__),
        retained_study_allocated_bytes_including_all_external_data=used,
        external_inventory='results/study6-external-artifacts-20261018.json',
        ledger_summary=summary, mathematical_objective_complete=False)
    atomic_json(OUT/'closure.json', closure)
    atomic_json(ROOT/'results/text-map-holdout6-20261018-closure-index.json', dict(
        closure=str(OUT/'closure.json'), closure_sha256=common.sha(OUT/'closure.json'),
        physical_external_output_counted=True, mathematical_objective_complete=False))
    print(json.dumps(dict(cpu=actual['actual_cpu_seconds'], combined=combined,
        archive_bytes=archive.stat().st_size, holdout_relative_error=error, scenario=scenario,
        ledger={k:summary[k] for k in ['charged_cpu_seconds','withheld_cpu_seconds','available_cpu_seconds']},
        kernel_available=summary['categories']['kernel']['available_cpu_seconds']), indent=1))


if __name__ == '__main__':
    main()
