"""Same held-out component calibration, with a generic certificate boundary."""
import hashlib
import json
from pathlib import Path
import shutil

from directed_scaling6 import profiles
from provenance import source_identity
from run_job import atomic_json, utc
from inline_scaling6 import TRAIN, HOLD, OLD_LOWER_TOKENS

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'Tests.InlineBoundaryScaling6'
DONOR_PREFIX = 'Tests.InlineCompactScaling6'
DONOR = ROOT/'results/inline-compact-scaling6-20261018'


def emit(check):
    check = Path(check)
    assert not check.exists()
    check.mkdir(parents=True)
    original = json.loads((DONOR/'comparison-plan.json').read_text())
    for part in TRAIN+HOLD:
        old = DONOR_PREFIX+'.Part'+str(part)
        prefix = PREFIX+'.Part'+str(part)
        previous = DONOR/'check/src'/(old.replace('.', '/')+'/Checked.agda')
        source = previous.read_text()
        header = source.split('abstract\n', 1)[0].replace(old+'.Checked', prefix+'.Checked')
        header = header.replace('import Othello.InlineRows6 as Rows', 'import Othello.InlineSteps6 as Rows')
        body = '''abstract
  steps : (G : ℕ → Packed.PackedState) → Check.Check.V.Compatible (M.lookup Data.demand) G →
    (∀ i → Packed.decode (G (Data.embed i)) ≡ B.lookupVec Data.ss i) →
    ∀ i → A.Step G (Data.embed i)
  steps = Check.steps (M.lookup Data.demand) Data.embed Data.ss (Codec.bodies 200 Body.text) refl
'''
        path = check/'src'/(prefix.replace('.', '/')+'/Checked.agda')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(header+body)
    for name, parts in [('Training', TRAIN), ('Holdout', HOLD)]:
        path = check/'src'/(PREFIX.replace('.', '/')+'/'+name+'.agda')
        path.write_text('{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'
            '-- AI-assisted repeated-row boundary calibration.\nmodule '+PREFIX+'.'+name+' where\n'+
            ''.join(f'import {PREFIX}.Part{p}.Checked\n' for p in parts))
    module = Path('src/Othello/InlineSteps6.agda')
    (check/module).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/module, check/module)
    atomic_json(check.parent/'comparison-plan.json', dict(created_utc=utc(), train=TRAIN,
        holdout=HOLD, excluded_selection_case=33154, features=original['features'],
        donor=str(DONOR), previous_scope_roots=['results/inline-scaling6-20261018',str(DONOR)],
        model='Checked module CPU plus measured donor TextBodies source CPU; generic theorem reported separately',
        heldout_relative_error_tolerance=.30, old_lower_tokens=OLD_LOWER_TOKENS,
        new_distinct_rows=0, common_map_join=False, initial_bounds_proved=False,
        full_workflow_forecast_validated=False, mathematical_objective_complete=False))
    return source_identity(check)


def summarize(out, phase):
    out = Path(out)
    plan = json.loads((out/'comparison-plan.json').read_text())
    found = profiles(out/'records'/('tests-inlineboundaryscaling6-'+phase+'.log'), PREFIX)
    parts = plan['train'] if phase == 'training' else plan['holdout']
    donor = json.loads((DONOR/('forecast-freeze.json' if phase == 'training' else 'holdout-comparison.json')).read_text())
    body_cost = 0
    row_cost = 0
    for part in parts:
        row_cost += found[f'{PREFIX}.Part{part}.Checked']
        module = f'{DONOR_PREFIX}.Part{part}.TextBodies'
        if module in donor['module_profiles']:
            body_cost += donor['module_profiles'][module]
        else:
            assert module in donor['omitted_sub_millisecond_text_modules']
            body_cost += .001
    row_cost += body_cost
    tokens = sum(plan['features'][str(part)]['tokens'] for part in parts)
    result = dict(created_utc=utc(), phase=phase, tokens=tokens,
        source_body_and_row_cpu_seconds=row_cost, reused_body_source_cpu_seconds=body_cost,
        body_cost_receipt=str(DONOR), module_profiles=found,
        state_resolver_source_costs_reused_from='results/inline-scaling6-20261018',
        generic_theorem_receipt='records/othello-inlinesteps6.json',
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
