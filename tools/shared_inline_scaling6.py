"""Prospective scaling check for one shared fixed lower-goal step boundary."""
import hashlib
import json
from pathlib import Path
import shutil

from directed_scaling6 import profiles
from provenance import source_identity
from run_job import atomic_json, utc
from inline_scaling6 import TRAIN, HOLD, OLD_LOWER_TOKENS

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'Tests.SharedInlineScaling6'
BODY_PREFIX = 'Tests.InlineCompactScaling6'
BOUNDARY_PREFIX = 'Tests.InlineBoundaryScaling6'
DONOR = ROOT/'results/inline-compact-scaling6-20261018'
BASELINE = ROOT/'results/inline-boundary-scaling6-20261018'


def _interface(check, module):
    suffix = Path(*module.split('.')).with_suffix('.agdai')
    matches = [p for p in check.rglob('*.agdai') if p.as_posix().endswith(suffix.as_posix())]
    assert len(matches) == 1, (module, matches)
    return matches[0]


def _part_interface_sizes(check, prefix, parts):
    return {str(part): _interface(check, f'{prefix}.Part{part}.Checked').stat().st_size
            for part in parts}


def emit(check):
    check = Path(check)
    assert not check.exists()
    check.mkdir(parents=True)
    original = json.loads((BASELINE/'comparison-plan.json').read_text())
    header = '''{{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}}
-- AI-assisted existing-row shared-boundary calibration.
module {module} where

open import Prelude
import Game.Balanced as B
import Game.NatMap as M
import Othello.RowPacked6 as Packed
import {states} as Data
import {body} as Body
import Othello.UnicodeCompact6 as Codec
import Othello.SharedInlineSteps6 as Shared

'''
    body = '''abstract
  steps : (G : ℕ → Packed.PackedState) → Shared.Compatible (M.lookup Data.demand) G →
    (∀ i → Packed.decode (G (Data.embed i)) ≡ B.lookupVec Data.ss i) →
    ∀ i → Shared.Step G (Data.embed i)
  steps = Shared.steps (M.lookup Data.demand) Data.embed Data.ss
    (Codec.bodies 200 Body.text) refl
'''
    for part in TRAIN+HOLD:
        module = f'{PREFIX}.Part{part}.Checked'
        text = header.format(module=module,
            states=f'Tests.InlineScaling6.Part{part}.States',
            body=f'{BODY_PREFIX}.Part{part}.TextBodies') + body
        path = check/'src'/(module.replace('.', '/')+'.agda')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    for name, parts in [('Training', TRAIN), ('Holdout', HOLD)]:
        module = f'{PREFIX}.{name}'
        path = check/'src'/(module.replace('.', '/')+'.agda')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'
            '-- AI-assisted repeated-row shared-boundary calibration.\n'
            f'module {module} where\n' +
            ''.join(f'import {PREFIX}.Part{part}.Checked\n' for part in parts))
    core = Path('src/Othello/SharedInlineSteps6.agda')
    (check/core).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/core, check/core)
    atomic_json(check.parent/'comparison-plan.json', dict(created_utc=utc(),
        train=TRAIN, holdout=HOLD,
        excluded_selection_case=original['excluded_selection_case'],
        features=original['features'], donor=str(DONOR), baseline=str(BASELINE),
        previous_scope_roots=original['previous_scope_roots']+[str(BASELINE)],
        model='Checked module CPU plus measured donor TextBodies source CPU; shared fixed theorem reported separately',
        heldout_relative_error_tolerance=original['heldout_relative_error_tolerance'],
        old_lower_tokens=OLD_LOWER_TOKENS, new_distinct_rows=0,
        common_map_join=False, initial_bounds_proved=False,
        full_workflow_forecast_validated=False, mathematical_objective_complete=False))
    return source_identity(check)


def summarize(out, phase):
    out = Path(out)
    assert phase in ('training', 'holdout')
    plan = json.loads((out/'comparison-plan.json').read_text())
    found = profiles(out/'records'/f'tests-sharedinlinescaling6-{phase}.log', PREFIX)
    parts = plan['train'] if phase == 'training' else plan['holdout']
    required = [f'{PREFIX}.Part{part}.Checked' for part in parts]
    assert all(module in found for module in required), set(required)-set(found)
    donor = json.loads((DONOR/('forecast-freeze.json' if phase == 'training'
        else 'holdout-comparison.json')).read_text())
    body_cost = 0
    for part in parts:
        module = f'{BODY_PREFIX}.Part{part}.TextBodies'
        if module in donor['module_profiles']:
            body_cost += donor['module_profiles'][module]
        else:
            assert module in donor['omitted_sub_millisecond_text_modules']
            body_cost += .001
    row_cost = body_cost + sum(found[module] for module in required)
    tokens = sum(plan['features'][str(part)]['tokens'] for part in parts)
    interface_sizes = _part_interface_sizes(out/'check', PREFIX, parts)
    baseline_sizes = _part_interface_sizes(BASELINE/'check', BOUNDARY_PREFIX, parts)
    result = dict(created_utc=utc(), phase=phase, tokens=tokens,
        source_body_and_row_cpu_seconds=row_cost,
        reused_body_source_cpu_seconds=body_cost, body_cost_receipt=str(DONOR),
        module_profiles=found,
        per_part_interface_bytes=interface_sizes,
        baseline_exact_comparable_per_part_interface_bytes=baseline_sizes,
        total_part_interface_bytes=sum(interface_sizes.values()),
        baseline_exact_comparable_total_part_interface_bytes=sum(baseline_sizes.values()),
        shared_interface_bytes=_interface(out/'check', 'Othello.SharedInlineSteps6').stat().st_size,
        baseline_interface_receipt=str(BASELINE),
        state_resolver_source_costs_reused_from='results/inline-scaling6-20261018',
        generic_theorem_receipt='records/othello-sharedinlinesteps6.json',
        initial_bounds_proved=False, full_workflow_forecast_validated=False)
    if phase == 'training':
        assert not (out/'forecast-freeze.json').exists()
        result.update(seconds_per_token=row_cost/tokens,
            old_lower_component_prediction_cpu_seconds=row_cost/tokens*OLD_LOWER_TOKENS,
            frozen_before_holdout=True)
        atomic_json(out/'forecast-freeze.json', result)
    else:
        freeze = out/'forecast-freeze.json'
        pin = json.loads((out/'holdout-freeze-pin.json').read_text())['sha256']
        assert hashlib.sha256(freeze.read_bytes()).hexdigest() == pin
        frozen = json.loads(freeze.read_bytes())
        predicted = frozen['seconds_per_token']*tokens
        error = abs(predicted-row_cost)/row_cost
        result.update(predicted_cpu_seconds=predicted, relative_error=error,
            heldout_component_gate_passed=error<=plan['heldout_relative_error_tolerance'],
            frozen_forecast_sha256=pin)
        atomic_json(out/'holdout-comparison.json', result)
    return result
