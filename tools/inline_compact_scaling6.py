"""Prospective compact-body continuation of the same inline calibration scope."""
import json
import hashlib
from pathlib import Path

import bench6
import compact_shared6 as compact
import completion_batch6 as prior
from directed_probe6 import converted
from direct_rows_probe6 import HEADER
from directed_scaling6 import profiles
from unicode_codec_probe6 import encode
from provenance import source_identity
from run_job import atomic_json, utc
from inline_scaling6 import TRAIN, HOLD, OLD_LOWER_TOKENS

PREFIX = 'Tests.InlineCompactScaling6'
OLD_PREFIX = 'Tests.InlineScaling6'
PREVIOUS = prior.ROOT/'results/inline-scaling6-20261018'


def emit(check):
    check = Path(check)
    assert not check.exists()
    check.mkdir(parents=True)
    original = json.loads((PREVIOUS/'comparison-plan.json').read_text())
    sample_path = prior.OUT/'sample.json'
    assert hashlib.sha256(sample_path.read_bytes()).hexdigest() == original['sample_sha256']
    sample = json.loads(sample_path.read_text())
    features = original['features']

    def add(module, body):
        path = check/'src'/(module.replace('.', '/')+'.agda')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(HEADER+'-- AI-assisted compact continuation, same component scope.\nmodule '+module+' where\n\n'+body)

    for case in sample['cases']:
        part = case['part']
        if part not in TRAIN+HOLD:
            continue
        old = OLD_PREFIX+'.Part'+str(part)
        prefix = PREFIX+'.Part'+str(part)
        states = [bench6.decode(compact.unpack_state(case['state_text'][13*i:13*i+13])) for i in range(200)]
        texts, counts = converted(case['body_text'], states, text_output=True)
        assert counts == features[str(part)]['counts']
        text = ''.join(encode(t) for t in texts)
        add(prefix+'.TextBodies', 'open import Agda.Builtin.String using (String)\ntext : String\ntext = '+json.dumps(text, ensure_ascii=False)+'\n')
        previous = PREVIOUS/'check/src'/(old.replace('.', '/')+'/Checked.agda')
        checked = previous.read_text().replace(old, prefix)
        checked = checked.replace('import '+prefix+'.States as Data', 'import '+old+'.States as Data')
        checked = checked.replace('import '+prefix+'.LiteralBodies as Body', 'import '+prefix+'.TextBodies as Body\nimport Othello.UnicodeCompact6 as Codec')
        checked = checked.replace('Body.bodies', '(Codec.bodies 200 Body.text)')
        path = check/'src'/(prefix.replace('.', '/')+'/Checked.agda')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(checked)
        features[str(part)]['compact_utf8_bytes'] = len(text.encode())
        features[str(part)]['compact_characters'] = len(text)
    for name, parts in [('Training', TRAIN), ('Holdout', HOLD)]:
        add(PREFIX+'.'+name, ''.join(f'import {PREFIX}.Part{p}.Checked\n' for p in parts))
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'comparison-plan.json', dict(created_utc=utc(), train=TRAIN,
        holdout=HOLD, excluded_selection_case=33154, features=features,
        sample_sha256=original['sample_sha256'], previous_scope_root=str(PREVIOUS),
        model='sum TextBodies+Checked module CPU divided by tokens; unchanged state/resolver data reused and cost reported in previous calibration',
        heldout_relative_error_tolerance=.30, old_lower_tokens=OLD_LOWER_TOKENS,
        new_distinct_rows=0, common_map_join=False, initial_bounds_proved=False,
        full_workflow_forecast_validated=False, mathematical_objective_complete=False))
    return source_identity(check)


def summarize(out, phase):
    out = Path(out)
    plan = json.loads((out/'comparison-plan.json').read_text())
    found = profiles(out/'records'/('tests-inlinecompactscaling6-'+phase+'.log'), PREFIX)
    parts = plan['train'] if phase == 'training' else plan['holdout']
    omitted = []
    row_cost = 0
    for p in parts:
        for name in ['TextBodies', 'Checked']:
            module = f'{PREFIX}.Part{p}.{name}'
            if module not in found:
                assert name == 'TextBodies'
                assert any((out/'check/_build').rglob(module.replace('.', '/')+'.agdai'))
                omitted.append(module)
            row_cost += found.get(module, .001)
    tokens = sum(plan['features'][str(p)]['tokens'] for p in parts)
    result = dict(created_utc=utc(), phase=phase, tokens=tokens,
        source_body_and_row_cpu_seconds=row_cost, module_profiles=found,
        omitted_sub_millisecond_text_modules=omitted, omitted_module_allowance_cpu_seconds=.001,
        state_resolver_source_costs_reused_from=str(PREVIOUS),
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
        frozen = json.loads(freeze.read_text())
        predicted = frozen['seconds_per_token']*tokens
        error = abs(predicted-row_cost)/row_cost
        result.update(predicted_cpu_seconds=predicted, relative_error=error,
            heldout_component_gate_passed=error<=plan['heldout_relative_error_tolerance'],
            frozen_forecast_sha256=pin)
        atomic_json(out/'holdout-comparison.json', result)
    return result
