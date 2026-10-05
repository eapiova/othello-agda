{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Value where

open import Prelude
open import Game.Core
open import Othello.Board
open import Othello.Rules using (game)
open import Othello.Order
open import Othello.Statements
open import Agda.Builtin.Nat using (_+_)
open import Agda.Builtin.Int using (pos)

-- Pair White's lower-bound strategy with Black's upper-bound strategy.
-- Both guarantees produce terminal plays for this very same strategy pair;
-- determinism identifies their endpoints, so the bounds meet on one score.
value-ordered : ∀ {size} {v w : ℕ} → HasValue size v → HasValue size w → v ≤ w
value-ordered {size} {v} {w} optimalV optimalW
  with responds (lower optimalV) (forcing (upper optimalW))
     | responds (upper optimalW) (forcing (lower optimalV))
... | t , (whitePlay , lowerBound) | u , (blackPlay , upperBound) =
  ≤-cancel-left (discs black t)
    (≤-trans (≤ᵇ-sound lowerBound)
      (≤ᵇ-sound (subst (λ endpoint → upperGoal w endpoint ≡ true)
        (sym (play-deterministic whitePlay (swapPlay blackPlay))) upperBound)))

value-unique : ∀ {size} {v w : ℕ} → HasValue size v → HasValue size w → v ≡ w
value-unique optimalV optimalW =
  ≤-antisym (value-ordered optimalV optimalW) (value-ordered optimalW optimalV)

-- The two strategies meet in a completed play whose raw score is exactly v.
value-realized : ∀ {size v} (optimal : HasValue size v) →
  Σ (State size) (λ t →
    CompletedPlay (game size) white (forcing (lower optimal))
      (forcing (upper optimal)) (initial size) t ×
    (discs white t ≡ discs black t + v))
value-realized {size} {v} optimal
  with responds (lower optimal) (forcing (upper optimal))
     | responds (upper optimal) (forcing (lower optimal))
... | t , (whitePlay , lowerBound) | u , (blackPlay , upperBound) =
  t , whitePlay , ≤-antisym
    (≤ᵇ-sound (subst (λ endpoint → upperGoal v endpoint ≡ true)
      (sym (play-deterministic whitePlay (swapPlay blackPlay))) upperBound))
    (≤ᵇ-sound lowerBound)

signed-add : ∀ b v → signedDifference (b + v) b ≡ pos v
signed-add zero v = refl
signed-add (suc b) v = signed-add b v

value-score : ∀ {size v} {t : State size} →
  discs white t ≡ discs black t + v → score t ≡ pos v
value-score {v = v} {t} e = trans
  (cong (λ w → signedDifference w (discs black t)) e)
  (signed-add (discs black t) v)
