"""Prospective component calibration for the selected inline checker, not a full forecast."""
import json
import hashlib
from pathlib import Path

import bench6
import compact_shared6 as compact
import completion_batch6 as prior
from directed_probe6 import converted
from direct_rows_probe6 import HEADER, vec
from sparse_citation_pilot6 import tree
from directed_scaling6 import profiles
from provenance import source_identity
from run_job import atomic_json, utc

TRAIN = [342, 10441, 17236, 26707]
HOLD = [4913, 15761, 23417]
PREFIX = 'Tests.InlineScaling6'
OLD_LOWER_TOKENS = 88689949


def emit(check):
    check = Path(check)
    assert not check.exists()
    check.mkdir(parents=True)
    sample_path = prior.OUT/'sample.json'
    sample = json.loads(sample_path.read_text())
    features = {}
    common = '''open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Othello.Board using (State; Coord; six; black; white)
import Othello.Finite as F
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.NatMap as M
import Othello.LazyIndexed6 as Lazy
import Othello.RowPacked6 as Packed
'''

    def add(module, body):
        path = check/'src'/(module.replace('.', '/')+'.agda')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(HEADER+'-- AI-assisted existing-row component calibration.\nmodule '+module+' where\n\n'+body)

    for case in sample['cases']:
        part = case['part']
        if part not in TRAIN+HOLD:
            continue
        prefix = PREFIX+'.Part'+str(part)
        states = [bench6.decode(compact.unpack_state(case['state_text'][13*i:13*i+13])) for i in range(200)]
        literals, counts = converted(case['body_text'], states)
        assert case['tokens'] == sum(v for k, v in counts.items() if k != 'directed_choices')
        keys = sorted(set(case['references']))
        definitions = []
        for key in keys:
            chunk = sample['states'][str(key//200)]
            packed = chunk['text'][13*(key%200):13*(key%200+1)]
            s = bench6.decode(compact.unpack_state(packed))
            codes = [sum(s.cells[6*r+c]*3**c for c in range(6)) for r in range(6)]
            definitions.append(f's{key} : Packed.PackedState\ns{key} = Packed.packed ('+
                ' F.∷ '.join([*map(str, codes), 'F.[]'])+') '+('black' if s.turn == 1 else 'white')+'\n')
        expression = tree(keys, lambda k:f'(M.rows {k} 1 (B.cons s{k} B.nil))',
            lambda pivot,l,r:f'(M.branch {pivot} {l} {r})')
        data = common+'\n'.join(definitions)+'''ss : B.Vec (State six) 200
ss = Lazy.states 200 '''+json.dumps(case['state_text'])+'''
embed : B.Fin 200 → ℕ
embed i = B.finToNat i + '''+str(200*part)+'''
demand : M.Map Packed.PackedState
demand = '''+expression+'\n'
        add(prefix+'.States', data)
        add(prefix+'.LiteralBodies', common+'''bodies : B.Vec (D.DirectedCertificate ℕ (Coord six)) 200
bodies = '''+vec(literals, 'B.cons', 'B.nil')+'\n')
        checked = common+f'''import {prefix}.States as Data
import {prefix}.LiteralBodies as Body
open import Game.Core using (white)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (lowerGoal)
open import Othello.DirectSymmetry6 using (lowerTransport6)
import Othello.InlineRows6 as Rows
import Othello.InlineEntries6 as Rules
import Game.EncodedStepAssembly as Step
module Check = Rows.Checking white (lowerGoal 4) lowerTransport6
module A = Step.Assembly Packed.decode Rules.specializedGame6 white (lowerGoal 4)
abstract
  linked : (G : ℕ → Packed.PackedState) → Check.V.Compatible (M.lookup Data.demand) G → ∀ i →
    Check.V.Old.TreeOK (λ j → Packed.decode (G j)) (Data.embed i)
      (B.lookupVec Data.ss i) (B.lookupVec Body.bodies i)
  linked = Check.linked (M.lookup Data.demand) Data.embed Data.ss Body.bodies refl

  steps : (G : ℕ → Packed.PackedState) → Check.V.Compatible (M.lookup Data.demand) G →
    (∀ i → Packed.decode (G (Data.embed i)) ≡ B.lookupVec Data.ss i) →
    ∀ i → A.Step G (Data.embed i)
  steps G compatible own i earlier =
    subst (Proven Rules.specializedGame6 white (lowerGoal 4)) (sym (own i))
      (Check.V.Old.row-sound (λ j → Packed.decode (G j)) (Data.embed i) earlier
        (linked G compatible i))
'''
        add(prefix+'.Checked', checked)
        features[str(part)] = dict(rows=200, tokens=case['tokens'],
            distinct_references=len(keys), counts=counts,
            literal_body_source_bytes=sum(len(s.encode()) for s in literals))
    assert set(features) == set(map(str, TRAIN+HOLD))
    for name, parts in [('Training', TRAIN), ('Holdout', HOLD)]:
        add(PREFIX+'.'+name, ''.join(f'import {PREFIX}.Part{p}.Checked\n' for p in parts))
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'comparison-plan.json', dict(created_utc=utc(), train=TRAIN,
        holdout=HOLD, excluded_selection_case=33154, features=features,
        sample_sha256=hashlib.sha256(sample_path.read_bytes()).hexdigest(),
        model='sum LiteralBodies+Checked module CPU divided by tokens; States reported separately',
        heldout_relative_error_tolerance=.30, old_lower_tokens=OLD_LOWER_TOKENS,
        new_distinct_rows=0, common_map_join=False, initial_bounds_proved=False,
        full_workflow_forecast_validated=False, mathematical_objective_complete=False))
    return source_identity(check)


def summarize(out, phase):
    out = Path(out)
    plan = json.loads((out/'comparison-plan.json').read_text())
    assert phase in ('training', 'holdout')
    log = out/'records'/('tests-inlinescaling6-'+phase+'.log')
    found = profiles(log, PREFIX)
    parts = plan['train'] if phase == 'training' else plan['holdout']
    required = [f'{PREFIX}.Part{p}.{name}' for p in parts for name in ['States', 'LiteralBodies', 'Checked']]
    assert all(name in found for name in required), set(required)-set(found)
    tokens = sum(plan['features'][str(p)]['tokens'] for p in parts)
    row_cost = sum(found[f'{PREFIX}.Part{p}.{name}'] for p in parts for name in ['LiteralBodies', 'Checked'])
    shared = sum(found[f'{PREFIX}.Part{p}.States'] for p in parts)
    result = dict(created_utc=utc(), phase=phase, tokens=tokens,
        source_body_and_row_cpu_seconds=row_cost, state_resolver_source_cpu_seconds=shared,
        module_profiles=found, initial_bounds_proved=False, full_workflow_forecast_validated=False)
    if phase == 'training':
        assert not (out/'forecast-freeze.json').exists()
        result.update(seconds_per_token=row_cost/tokens,
            old_lower_component_prediction_cpu_seconds=row_cost/tokens*OLD_LOWER_TOKENS,
            frozen_before_holdout=True)
        atomic_json(out/'forecast-freeze.json', result)
    else:
        freeze = out/'forecast-freeze.json'
        before = json.loads((out/'holdout-freeze-pin.json').read_text())
        assert hashlib.sha256(freeze.read_bytes()).hexdigest() == before['sha256']
        frozen = json.loads(freeze.read_text())
        predicted = frozen['seconds_per_token']*tokens
        error = abs(predicted-row_cost)/row_cost
        result.update(predicted_cpu_seconds=predicted, relative_error=error,
            heldout_component_gate_passed=error<=plan['heldout_relative_error_tolerance'],
            frozen_forecast_sha256=before['sha256'])
        atomic_json(out/'holdout-comparison.json', result)
    return result
