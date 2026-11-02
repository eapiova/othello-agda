"""Merge contiguous 200-row wire samples into 1000-row checker units.

The generated data remains untrusted until the shared safe Agda checker accepts
it.  This helper emits sources and summarizes separately launched checks; it
does not run Agda or the native solver.
"""
import hashlib
import json
from pathlib import Path

import bench6
import compact_shared6 as compact
from directed_probe6 import converted
from directed_scaling6 import profiles
import shared_inline_scaling6 as previous
from sparse_citation_pilot6 import tree
from text_map_scaling6 import word
from unicode_codec_probe6 import encode
from provenance import source_identity
from run_job import atomic_json, utc


PREFIX = 'Tests.BigRowsScaling6'
BUNDLES = {
    'TrainLow': list(range(342, 347)),
    'TrainHigh': list(range(17236, 17241)),
    'Hold': list(range(26707, 26712)),
}
TRAIN = ['TrainLow', 'TrainHigh']
HOLD = ['Hold']
ROWS = 1000
TOKEN_CAP = 32000
ORIGINAL_INLINE200_STAGE_CPU_SECONDS = 199.053695
HEADER = ('{-# OPTIONS --safe --without-K --cubical-compatible '
          '-WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n')


def _module_path(check, module, suffix='.agda'):
    return Path(check)/'src'/Path(*module.split('.')).with_suffix(suffix)


def _add(check, module, body):
    path = _module_path(check, module)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HEADER + '-- AI-assisted existing-row 1000-row scaling experiment.\n'
                    + 'module ' + module + ' where\n\n' + body)
    return path


def _packed_leaf(sample, key):
    chunk = sample['states'][str(key // 200)]
    packed = chunk['text'][13 * (key % 200):13 * (key % 200 + 1)]
    assert len(packed) == 13
    state = bench6.decode(compact.unpack_state(packed))
    codes = [sum(state.cells[6 * row + column] * 3 ** column
                 for column in range(6)) for row in range(6)]
    assert all(0 <= code < 729 for code in codes)
    return ('R' + word(key) + ('B' if state.turn == 1 else 'W')
            + ''.join(chr(256 + code) for code in codes))


def emit(check, sample):
    """Emit exactly three data/checker modules for each frozen bundle."""
    check = Path(check)
    assert not check.exists()
    assert isinstance(sample, dict)
    assert sample.get('format') == 'othello-wire-part-samples6-v1'
    expected = sorted(part for parts in BUNDLES.values() for part in parts)
    assert sample.get('selected') == expected
    cases = {case['part']: case for case in sample['cases']}
    assert sorted(cases) == expected and len(cases) == 15
    check.mkdir(parents=True)

    features = {}
    generated = {}
    for label, parts in BUNDLES.items():
        selected = [cases[part] for part in parts]
        assert all(case['rows'] == 200 for case in selected)
        state_text = ''.join(case['state_text'] for case in selected)
        body_text = ''.join(case['body_text'] for case in selected)
        references = [key for case in selected for key in case['references']]
        assert len(state_text) == 13 * ROWS

        certificates = []
        counts = None
        for case in selected:
            states = [bench6.decode(compact.unpack_state(
                case['state_text'][13 * i:13 * (i + 1)])) for i in range(200)]
            texts, part_counts = converted(case['body_text'], states, text_output=True)
            certificates.extend(encode(text) for text in texts)
            if counts is None:
                counts = {name: 0 for name in part_counts}
            for name, value in part_counts.items():
                counts[name] += value
        assert len(certificates) == ROWS
        assert body_text == ''.join(case['body_text'] for case in selected)
        tokens = sum(case['tokens'] for case in selected)
        assert tokens == sum(value for name, value in counts.items()
                             if name != 'directed_choices')
        assert tokens <= TOKEN_CAP

        keys = sorted(set(references))
        assert keys
        demand_text = tree(keys, lambda key: _packed_leaf(sample, key),
                           lambda pivot, left, right:
                           'B' + word(pivot) + left + right)
        prefix = PREFIX + '.' + label
        base = 200 * parts[0]
        states_body = '''open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.NatMap as M
import Othello.RowPacked6 as Packed
import Othello.PackedMapText6 as Text
import Othello.LazyIndexed6 as Lazy

ss : B.Vec (State six) 1000
ss = Lazy.states 1000 ''' + json.dumps(state_text) + '''
embed : B.Fin 1000 → ℕ
embed i = ''' + str(base) + ''' + B.finToNat i
demand : M.Map Packed.PackedState
demand = Text.table ''' + json.dumps(demand_text, ensure_ascii=False) + '\n'
        body_body = '''open import Agda.Builtin.String using (String)

text : String
text = ''' + json.dumps(''.join(certificates), ensure_ascii=False) + '\n'
        checked_body = '''open import Prelude
import Game.Balanced as B
import Game.NatMap as M
import Othello.RowPacked6 as Packed
import Othello.UnicodeCompact6 as Codec
import Othello.SharedInlineSteps6 as Shared
import ''' + prefix + '''.States as Data
import ''' + prefix + '''.TextBodies as Body

abstract
  steps : (G : ℕ → Packed.PackedState) → Shared.Compatible (M.lookup Data.demand) G →
    (∀ i → Packed.decode (G (Data.embed i)) ≡ B.lookupVec Data.ss i) →
    ∀ i → Shared.Step G (Data.embed i)
  steps = Shared.steps (M.lookup Data.demand) Data.embed Data.ss
    (Codec.bodies 1000 Body.text) refl
'''
        paths = {
            'States': _add(check, prefix + '.States', states_body),
            'TextBodies': _add(check, prefix + '.TextBodies', body_body),
            'Checked': _add(check, prefix + '.Checked', checked_body),
        }
        generated[label] = paths
        features[label] = dict(
            parts=parts, base=base, rows=ROWS, tokens=tokens,
            distinct_references=len(keys), reference_occurrences=len(references),
            counts=counts,
            generated_source_bytes={name: path.stat().st_size
                                    for name, path in paths.items()},
            total_generated_source_bytes=sum(path.stat().st_size
                                             for path in paths.values()))

    for label, bundles in [('Training', TRAIN), ('Holdout', HOLD)]:
        _add(check, PREFIX + '.' + label,
             ''.join('import ' + PREFIX + '.' + bundle + '.Checked\n'
                     for bundle in bundles))

    canonical_sample = json.dumps(sample, sort_keys=True, separators=(',', ':')).encode()
    atomic_json(check.parent/'comparison-plan.json', dict(
        format='othello-big-rows-scaling6-plan-v1', created_utc=utc(),
        prefix=PREFIX, bundles=BUNDLES, train=TRAIN, holdout=HOLD,
        features=features, sample_sha256=hashlib.sha256(canonical_sample).hexdigest(),
        wire_sha256=sample['wire_sha256'], wire_rows=sample['wire_rows'],
        rows_per_bundle=ROWS, token_cap_per_bundle=TOKEN_CAP,
        model='sum States, TextBodies, and Checked CPU divided by certificate tokens',
        heldout_relative_error_tolerance=.30,
        original_inline200_stage_cpu_seconds=ORIGINAL_INLINE200_STAGE_CPU_SECONDS,
        footprint_estimates_are_scenarios_only=True,
        lower_component_scenario_only=True, upper_forecast_published=False,
        new_distinct_common_map_rows=0, initial_bounds_proved=False,
        full_workflow_forecast_validated=False, production_go=False,
        production_authorized=False, mathematical_objective_complete=False))
    return source_identity(check)


def _interfaces(check, modules):
    return {module: previous._interface(check, module).stat().st_size
            for module in modules}


def summarize(out, phase):
    """Summarize a parent-launched training or held-out check."""
    out = Path(out)
    assert phase in ('training', 'holdout')
    plan = json.loads((out/'comparison-plan.json').read_text())
    bundles = plan['train'] if phase == 'training' else plan['holdout']
    found = profiles(out/'records'/f'tests-bigrowsscaling6-{phase}.log', PREFIX)
    per_bundle = {}
    total_cpu = total_tokens = total_source = total_interface = 0
    omitted = []
    for bundle in bundles:
        prefix = PREFIX + '.' + bundle
        names = {kind: prefix + '.' + kind
                 for kind in ('States', 'TextBodies', 'Checked')}
        assert names['Checked'] in found
        costs = {'Checked': found[names['Checked']]}
        for kind in ('States', 'TextBodies'):
            name = names[kind]
            if name in found:
                costs[kind] = found[name]
            else:
                assert previous._interface(out/'check', name).exists()
                costs[kind] = .001
                omitted.append(name)
        interfaces = _interfaces(out/'check', names.values())
        source_bytes = {kind: _module_path(out/'check', name).stat().st_size
                        for kind, name in names.items()}
        feature = plan['features'][bundle]
        assert source_bytes == feature['generated_source_bytes']
        cpu = sum(costs.values())
        interface_bytes = sum(interfaces.values())
        bundle_source = sum(source_bytes.values())
        per_bundle[bundle] = dict(rows=feature['rows'], tokens=feature['tokens'],
            module_cpu_seconds=costs, cpu_seconds=cpu,
            interface_bytes=interfaces, total_interface_bytes=interface_bytes,
            source_bytes=source_bytes, total_source_bytes=bundle_source)
        total_cpu += cpu
        total_tokens += feature['tokens']
        total_source += bundle_source
        total_interface += interface_bytes

    phase_rows = ROWS * len(bundles)
    result = dict(format='othello-big-rows-scaling6-summary-v1',
        created_utc=utc(), phase=phase, bundles=bundles, rows=phase_rows,
        tokens=total_tokens, cpu_seconds=total_cpu,
        seconds_per_token=total_cpu/total_tokens,
        module_profiles=found, per_bundle=per_bundle,
        omitted_sub_millisecond_modules=omitted,
        conservative_seconds_per_omitted_module=.001,
        total_source_bytes=total_source, total_interface_bytes=total_interface,
        footprint_scenarios=dict(
            measured_bundles=dict(rows=phase_rows, source_bytes=total_source,
                                  interface_bytes=total_interface),
            same_mix_lower_component=dict(rows=plan['wire_rows'],
                source_bytes=total_source * plan['wire_rows'] / phase_rows,
                interface_bytes=total_interface * plan['wire_rows'] / phase_rows,
                scenario_only=True)),
        original_inline200_stage_cpu_seconds=plan['original_inline200_stage_cpu_seconds'],
        initial_bounds_proved=False, full_workflow_forecast_validated=False,
        upper_forecast_published=False, production_go=False)
    if phase == 'training':
        assert not (out/'forecast-freeze.json').exists()
        result['frozen_before_holdout'] = True
        atomic_json(out/'forecast-freeze.json', result)
    else:
        freeze = out/'forecast-freeze.json'
        pin = json.loads((out/'holdout-freeze-pin.json').read_text())['sha256']
        assert hashlib.sha256(freeze.read_bytes()).hexdigest() == pin
        frozen = json.loads(freeze.read_text())
        predicted = frozen['seconds_per_token'] * total_tokens
        error = abs(predicted - total_cpu) / total_cpu
        result.update(predicted_cpu_seconds=predicted, relative_error=error,
            heldout_component_gate_passed=error <= plan['heldout_relative_error_tolerance'],
            frozen_forecast_sha256=pin)
        atomic_json(out/'holdout-comparison.json', result)
    return result
