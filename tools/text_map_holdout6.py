"""Complete the never-started holdout; reuse exactly checked text-map core."""
import json
from pathlib import Path

import text_map_scaling6 as full
from provenance import source_identity
from run_job import atomic_json

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT/'results/text-map-scaling6-20261018-fixed'
PREFIX = 'Tests.TextMapHoldoutOnly6'


def emit(check):
    check = Path(check)
    assert not check.exists()
    # The previous process stopped in profile collection after Training passed.
    # No Holdout has ever run. Freeze the observed training model before any
    # new source/checker dispatch, with explicit sub-millisecond allowances.
    train = json.loads((PRIOR/'forecast-freeze.json').read_text())
    assert train['frozen_before_holdout']
    plan = json.loads((PRIOR/'comparison-plan.json').read_text())
    for part in plan['holdout']:
        for name in ['States', 'Checked']:
            source = PRIOR/'check/src'/f'Tests/TextMapScaling6/Part{part}/{name}.agda'
            target = check/'src'/f'Tests/TextMapHoldoutOnly6/Part{part}/{name}.agda'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source.read_text().replace('Tests.TextMapScaling6.', PREFIX+'.'))
    target = check/'src/Tests/TextMapHoldoutOnly6/Holdout.agda'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'
        '-- AI-assisted continuation of the SAME held-out data.\nmodule '+PREFIX+'.Holdout where\n'+
        ''.join(f'import {PREFIX}.Part{p}.Checked\n' for p in plan['holdout']))
    atomic_json(check.parent/'comparison-plan.json', plan)
    atomic_json(check.parent/'forecast-freeze.json', train)
    from citation_diagnostic6 import sha
    atomic_json(check.parent/'holdout-freeze-pin.json',dict(sha256=sha(check.parent/'forecast-freeze.json')))
    return source_identity(check)


def summarize(out):
    full.PREFIX = PREFIX
    return full.summarize(out, 'holdout')
