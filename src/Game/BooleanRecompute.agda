{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Recover decidable equality from an irrelevant witness.
module Game.BooleanRecompute where

open import Prelude

module Checking {A : Set} (same : A → A → Bool)
  (sound : ∀ x y → same x y ≡ true → x ≡ y)
  (reflexive : ∀ x → same x x ≡ true) where

  private
    absurd : ∀ {X : Set} → .(false ≡ true) → X
    absurd ()

  recompute : ∀ {x y : A} → .(x ≡ y) → x ≡ y
  recompute {x} {y} witness with same x y in e
  ... | true = sound x y e
  ... | false = absurd
    (trans (sym e) (trans (sym (cong (same x) witness)) (reflexive x)))
