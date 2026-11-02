"""Matched existing-row semantic comparison for numeric owner progression."""
import hashlib
import json
from pathlib import Path
import shutil
from provenance import source_identity
from run_job import atomic_json, utc

ROOT = Path(__file__).resolve().parents[1]


def emit(check, explicit=False):
    check = Path(check)
    assert not check.exists()
    check.mkdir(parents=True)
    module = Path('src/Othello/ContiguousRows6.agda')
    if not explicit:
        (check/module).parent.mkdir(parents=True)
        shutil.copy2(ROOT/module, check/module)
    donor = ROOT/'results/inline-entries-probe6-20261018/check/src/Tests/InlineProbe6/Variant.agda'
    original = donor.read_text()
    baseline = original.replace('Tests.InlineProbe6.Variant', 'Tests.ContiguousRowsProbe6.Baseline')
    variant = baseline.replace('Tests.ContiguousRowsProbe6.Baseline', 'Tests.ContiguousRowsProbe6.Variant')
    variant = variant.replace('import Othello.InlineRows6 as Rows', 'import Othello.ContiguousRows6 as Rows')
    old = 'Check.linked (M.lookup Refs.demand) Original.embed ss Data.newBodies refl'
    assert variant.count(old) == 1
    variant = variant.replace(old, 'Check.linked (M.lookup Refs.demand) 6630800 ss Data.newBodies refl')
    if explicit:
        variant = variant.replace('Tests.ContiguousRowsProbe6.Variant', 'Tests.ContiguousExplicitRowsProbe6.Variant')
        variant = variant.replace('open import Prelude\n', 'open import Prelude\nopen import Agda.Builtin.Nat using (_+_)\n')
        variant = variant.replace('(Original.embed i)', '(6630800 + B.finToNat i)')
    folder = check/('src/Tests/ContiguousExplicitRowsProbe6' if explicit else 'src/Tests/ContiguousRowsProbe6')
    folder.mkdir(parents=True)
    cases = [('Variant', variant)] if explicit else [('Baseline', baseline), ('Variant', variant)]
    for name, text in cases:
        (folder/(name+'.agda')).write_text(text)
    (check/'othello.agda-lib').write_bytes((ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json', dict(created_utc=utc(),
        core_source_sha256=hashlib.sha256((ROOT/module).read_bytes()).hexdigest(),
        core_reused_from_checked_partial=explicit,
        literal_numeric_signature=explicit,
        exact_repeated_rows=200, selection_part=33154, base=6630800,
        unchanged_states_and_bodies=True, semantic_equivalence_pending=True,
        new_distinct_rows=0, initial_bounds_proved=False,
        native_solver_executed=False, mathematical_objective_complete=False))
    return source_identity(check)
