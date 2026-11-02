"""Matched arithmetic decoding test, preserving the original arithmetic scope."""
import hashlib
import json
from pathlib import Path
import shutil
from provenance import source_identity
from run_job import atomic_json, utc

ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT/'results/erased-arithmetic-probe6-20261018'
PREFIX = 'Tests.PrimitiveArithmeticProbe6'


def emit(check):
    check = Path(check)
    assert not check.exists()
    check.mkdir(parents=True)
    pins = {}
    for kind in ['State', 'Game', 'Rows']:
        rel = Path(f'src/Othello/PrimitiveArithmetic{kind}6.agda')
        target = check/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/rel, target)
        pins[str(ROOT/rel)] = hashlib.sha256(target.read_bytes()).hexdigest()
    old = DONOR/'check/src/Tests/ErasedArithmeticProbe6'
    folder = check/'src/Tests/PrimitiveArithmeticProbe6'
    folder.mkdir(parents=True)
    source = (old/'Variant.agda').read_text()
    baseline = source.replace('module Tests.ErasedArithmeticProbe6.Variant where', 'module '+PREFIX+'.Baseline where')
    variant = source.replace('Tests.ErasedArithmeticProbe6','Tests.PrimitiveArithmeticProbe6').replace('ErasedArithmetic','PrimitiveArithmetic')
    refs = (old/'RefData.agda').read_text().replace('ErasedArithmetic','PrimitiveArithmetic')
    for name, text in [('RefData', refs), ('Baseline', baseline), ('Variant', variant)]:
        (folder/(name+'.agda')).write_text(text)
    (check/'othello.agda-lib').write_bytes((ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json', dict(created_utc=utc(),
        copied_core_sha256=pins, existing_rows=200, new_distinct_rows=0,
        original_scope_root=str(DONOR), original_scope_cpu_cap=200,
        prior_actual_cpu_seconds=58.034395, original_shared_allowance_seconds=20,
        native_solver_executed=False, unsafe_irrelevance_flags=False,
        semantic_equivalence_requires_successful_safe_check=True,
        mathematical_objective_complete=False))
    return source_identity(check)
