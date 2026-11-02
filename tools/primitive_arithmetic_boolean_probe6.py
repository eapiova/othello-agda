"""Emit a matched Boolean-only screen for primitive arithmetic states."""
import hashlib
from pathlib import Path
import shutil

from provenance import source_identity
from run_job import atomic_json, utc


ROOT = Path(__file__).resolve().parents[1]


BASELINE = '''{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted Boolean-only check of the existing 200 rows; no semantic claim.
module Tests.PrimitiveArithmeticBooleanProbe6.Baseline where

open import Prelude
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.NatMap as M
import Othello.LazyIndexed6 as Lazy
import Tests.FullInitialLower6.StateData33154 as Own
import Tests.CompletionBatchLowerA6.Rows33154.Part33154 as Original
open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
open import Othello.DirectSymmetry6 using (lowerTransport6)
import Othello.InlineRows6 as Rows
import Tests.RowPackedProbe6.RefData as Refs
import Tests.DirectedProbe6.Data as Data

module Check = Rows.Checking white (lowerGoal 4) lowerTransport6

ss : B.Vec (State six) 200
ss = Lazy.states 200 Own.text

abstract
  checked : Check.checkRows (M.lookup Refs.demand) Original.embed ss Data.newBodies ≡ true
  checked = refl
'''


VARIANT = '''{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted Boolean-only check of the same existing 200 rows; no soundness,
-- Proven, initial-bound, or mathematical-completion claim follows from it.
module Tests.PrimitiveArithmeticBooleanProbe6.Variant where

open import Prelude
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.NatMap as M
import Othello.LazyIndexed6 as Lazy
import Tests.FullInitialLower6.StateData33154 as Own
import Tests.CompletionBatchLowerA6.Rows33154.Part33154 as Original
import Othello.PrimitiveArithmeticBoolean6 as Check
import Othello.RowPacked6 as P
import Tests.RowPackedProbe6.RefData as Refs
import Tests.DirectedProbe6.Data as Data

packVec : ∀ {n} → B.Vec (State six) n → B.Vec P.PackedState n
packVec B.nil = B.nil
packVec (B.cons s ss) = B.cons (P.encode s) (packVec ss)

ss : B.Vec P.PackedState 200
ss = packVec (Lazy.states 200 Own.text)

abstract
  checked : Check.checkRows (M.lookup Refs.demand) Original.embed ss Data.newBodies ≡ true
  checked = refl
'''


COMPARE = '''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted matched Boolean-only screen; neither import proves soundness.
module Tests.PrimitiveArithmeticBooleanProbe6.Compare where
import Tests.PrimitiveArithmeticBooleanProbe6.Baseline
import Tests.PrimitiveArithmeticBooleanProbe6.Variant
'''


def emit(check):
    check = Path(check)
    assert not check.exists()
    check.mkdir(parents=True)

    rel = Path('src/Othello/PrimitiveArithmeticBoolean6.agda')
    target = check / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / rel, target)

    folder = check / 'src/Tests/PrimitiveArithmeticBooleanProbe6'
    folder.mkdir(parents=True)
    for name, text in [('Baseline', BASELINE), ('Variant', VARIANT), ('Compare', COMPARE)]:
        (folder / (name + '.agda')).write_text(text)

    (check / 'othello.agda-lib').write_bytes((ROOT / 'othello.agda-lib').read_bytes())
    atomic_json(check.parent / 'formal-source-provenance.json', dict(
        format='othello-primitive-arithmetic-boolean6-sources-v1',
        created_utc=utc(),
        boolean_source_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        boolean_only=True,
        semantic_soundness_checked=False,
        conditional_existing_rows=0,
        existing_repeated_boolean_rows=200,
        new_distinct_rows=0,
        initial_bounds_proved=False,
        mathematical_objective_complete=False,
        native_solver_executed=False))
    return source_identity(check)
