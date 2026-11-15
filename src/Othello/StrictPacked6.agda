{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Eager numeric fields, using Agda's checked strict primitive.
module Othello.StrictPacked6 where

open import Prelude
open import Agda.Builtin.Strict using (primForce; primForceLemma)
import Othello.Finite as F
import Othello.RowPacked6 as P

forceRows : ∀ {n} {A : Set} → F.Vec ℕ n → (F.Vec ℕ n → A) → A
forceRows F.[] k = k F.[]
forceRows (n F.∷ ns) k = primForce n (λ m → forceRows ns (λ ms → k (m F.∷ ms)))

abstract
  forceRows-correct : ∀ {n} {A : Set} (xs : F.Vec ℕ n) (k : F.Vec ℕ n → A) →
    forceRows xs k ≡ k xs
  forceRows-correct F.[] k = refl
  forceRows-correct (n F.∷ ns) k
    rewrite primForceLemma n (λ m → forceRows ns (λ ms → k (m F.∷ ms))) =
      forceRows-correct ns (λ ms → k (n F.∷ ms))

forcePacked : P.PackedState → P.PackedState
forcePacked (P.packed rows p) = forceRows rows (λ ns → P.packed ns p)

abstract
  forcePacked-correct : ∀ s → forcePacked s ≡ s
  forcePacked-correct (P.packed rows p) = forceRows-correct rows (λ ns → P.packed ns p)
