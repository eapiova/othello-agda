"""Same old-row calibration, with text local maps and no new semantic claims."""
import json
from pathlib import Path
import shutil

import bench6
import compact_shared6 as compact
import completion_batch6 as batch
import shared_inline_scaling6 as previous
from sparse_citation_pilot6 import tree
from run_job import atomic_json, utc
from provenance import source_identity

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'Tests.TextMapScaling6'
BASELINE = ROOT/'results/shared-inline-scaling6-20261018'


def word(key):
    assert 0 <= key < 20000000
    return chr(16384+key//1024)+chr(16384+key%1024)


def emit(check):
    check = Path(check)
    assert not check.exists()
    sample = json.loads((batch.OUT/'sample.json').read_text())
    old = json.loads((BASELINE/'comparison-plan.json').read_text())
    check.mkdir(parents=True)

    def add(module, body):
        path = check/'src'/(module.replace('.', '/')+'.agda')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
            '-- AI-assisted same-row data representation experiment.\nmodule '+module+' where\n\n'+body)

    for case in sample['cases']:
        part = case['part']
        if part not in old['train']+old['holdout']:
            continue
        keys = sorted(set(case['references']))

        def leaf(key):
            chunk = sample['states'][str(key//200)]['text']
            packed = chunk[13*(key%200):13*(key%200+1)]
            s = bench6.decode(compact.unpack_state(packed))
            codes = [sum(s.cells[6*r+c]*3**c for c in range(6)) for r in range(6)]
            assert all(0 <= code < 729 for code in codes)
            return 'R'+word(key)+('B' if s.turn == 1 else 'W')+''.join(chr(256+c) for c in codes)

        text = tree(keys, leaf, lambda pivot,l,r: 'B'+word(pivot)+l+r)
        prefix = PREFIX+'.Part'+str(part)
        add(prefix+'.States', '''open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.NatMap as M
import Othello.RowPacked6 as Packed
import Othello.PackedMapText6 as Text
import Othello.LazyIndexed6 as Lazy

ss : B.Vec (State six) 200
ss = Lazy.states 200 '''+json.dumps(case['state_text'])+'''
embed : B.Fin 200 → ℕ
embed i = B.finToNat i + '''+str(200*part)+'''
demand : M.Map Packed.PackedState
demand = Text.table '''+json.dumps(text,ensure_ascii=False)+'\n')
        source = BASELINE/'check/src'/('Tests/SharedInlineScaling6/Part'+str(part)+'/Checked.agda')
        body = source.read_text().split(' where\n',1)[1]
        body = body.replace('import Tests.InlineScaling6.Part'+str(part)+'.States as Data',
            'import '+prefix+'.States as Data')
        add(prefix+'.Checked', body.lstrip())
    for label, parts in [('Training',old['train']),('Holdout',old['holdout'])]:
        add(PREFIX+'.'+label, ''.join(f'import {PREFIX}.Part{p}.Checked\n' for p in parts))
    core = Path('src/Othello/PackedMapText6.agda')
    (check/core).parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/core,check/core)
    atomic_json(check.parent/'comparison-plan.json',dict(old,created_utc=utc(),
        baseline=str(BASELINE),model='Text map and own state source plus Checked module CPU and measured donor body cost',
        map_semantics_checked_only_through_existing_sound_row_checker=True,
        whole_map_equality_not_claimed=True))
    return source_identity(check)


def summarize(out, phase):
    import hashlib
    from directed_scaling6 import profiles
    out=Path(out)
    plan=json.loads((out/'comparison-plan.json').read_text())
    parts=plan['train'] if phase=='training' else plan['holdout']
    found=profiles(out/'records'/f'tests-textmapscaling6-{phase}.log',PREFIX)
    body=json.loads((ROOT/'results/inline-compact-scaling6-20261018'/('forecast-freeze.json' if phase=='training' else 'holdout-comparison.json')).read_text())
    body_cost=0
    for part in parts:
        name=f'Tests.InlineCompactScaling6.Part{part}.TextBodies'
        assert name in body['module_profiles'] or name in body['omitted_sub_millisecond_text_modules']
        body_cost+=body['module_profiles'].get(name,.001)
    checked=[f'{PREFIX}.Part{part}.Checked' for part in parts]
    states=[f'{PREFIX}.Part{part}.States' for part in parts]
    assert all(name in found for name in checked)
    assert all(previous._interface(out/'check',name).exists() for name in states)
    row_cost=body_cost+sum(found[name] for name in checked)
    state_cost=sum(found.get(name,.001) for name in states)
    tokens=sum(plan['features'][str(part)]['tokens'] for part in parts)
    result=dict(created_utc=utc(),phase=phase,tokens=tokens,module_profiles=found,
        source_body_and_row_cpu_seconds=row_cost,state_source_module_cpu_seconds=state_cost,
        omitted_sub_millisecond_states=[name for name in states if name not in found],
        omitted_state_allowance_cpu_seconds=.001,
        state_and_body_and_row_cpu_seconds=row_cost+state_cost,
        per_part_interface_bytes=previous._part_interface_sizes(out/'check',PREFIX,parts),
        baseline_per_part_interface_bytes=previous._part_interface_sizes(BASELINE/'check','Tests.SharedInlineScaling6',parts),
        per_part_state_interface_bytes={str(p):previous._interface(out/'check',f'{PREFIX}.Part{p}.States').stat().st_size for p in parts},
        baseline_per_part_state_interface_bytes={str(p):previous._interface(ROOT/'results/inline-scaling6-20261018/check',f'Tests.InlineScaling6.Part{p}.States').stat().st_size for p in parts},
        initial_bounds_proved=False,full_workflow_forecast_validated=False,
        whole_map_equality_not_claimed=True,reused_body_source_cpu_seconds=body_cost)
    if phase=='training':
        assert not (out/'forecast-freeze.json').exists()
        result.update(seconds_per_token=row_cost/tokens,state_and_row_seconds_per_token=(row_cost+state_cost)/tokens,
            frozen_before_holdout=True)
        atomic_json(out/'forecast-freeze.json',result)
    else:
        freeze=out/'forecast-freeze.json'
        pin=json.loads((out/'holdout-freeze-pin.json').read_text())['sha256']
        assert hashlib.sha256(freeze.read_bytes()).hexdigest()==pin
        frozen=json.loads(freeze.read_text());predicted=frozen['state_and_row_seconds_per_token']*tokens
        error=abs(predicted-(row_cost+state_cost))/(row_cost+state_cost)
        result.update(predicted_state_and_row_cpu_seconds=predicted,relative_error=error,
            heldout_component_gate_passed=error<=plan['heldout_relative_error_tolerance'],frozen_forecast_sha256=pin)
        atomic_json(out/'holdout-comparison.json',result)
    return result
