{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Hedberg's argument for a sound reflexive Boolean equality.
module Game.BooleanUIP where

open import Prelude

module Checking {A : Set} (same : A → A → Bool)
  (sound : ∀ x y → same x y ≡ true → x ≡ y)
  (reflexive : ∀ x → same x x ≡ true) where

  private
    false-elim : ∀ {X : Set} → false ≡ true → X
    false-elim ()

    fixed : ∀ {x y : A} → x ≡ y → x ≡ y
    fixed {x} {y} p with same x y in e
    ... | true = sound x y e
    ... | false = false-elim
      (trans (sym e) (trans (sym (cong (same x) p)) (reflexive x)))

    fixed-constant : ∀ {x y : A} (p q : x ≡ y) → fixed p ≡ fixed q
    fixed-constant {x} {y} p q with same x y in e
    ... | true = refl
    ... | false = false-elim
      (trans (sym e) (trans (sym (cong (same x) p)) (reflexive x)))

    inverse-left : ∀ {x y : A} (p : x ≡ y) → trans (sym p) p ≡ refl
    inverse-left refl = refl

    normal : ∀ {x y : A} → x ≡ y → x ≡ y
    normal {x} p = trans (sym (fixed {x} {x} refl)) (fixed p)

    normal-id : ∀ {x y : A} (p : x ≡ y) → normal p ≡ p
    normal-id refl = inverse-left (fixed refl)

  abstract
    unique : ∀ {x y : A} (p q : x ≡ y) → p ≡ q
    unique {x} p q = trans (sym (normal-id p))
      (trans (cong (trans (sym (fixed {x} {x} refl))) (fixed-constant p q))
        (normal-id q))
