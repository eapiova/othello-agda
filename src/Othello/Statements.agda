{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Statements where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Game.Core
open import Othello.Board
open import Othello.Rules using (game)
open import Othello.Order

-- These inequalities characterize a nonnegative raw disc difference exactly,
-- without saturating natural subtraction or awarding unoccupied squares.
lowerGoal : ∀ {size} → ℕ → State size → Bool
lowerGoal v s = (discs black s + v) ≤ᵇ discs white s

upperGoal : ∀ {size} → ℕ → State size → Bool
upperGoal v s = discs white s ≤ᵇ (discs black s + v)

winGoal : ∀ {size} → State size → Bool
winGoal s = suc (discs black s) ≤ᵇ discs white s

record HasValue (size : Size) (v : ℕ) : Set where
  field
    lower : WhiteGuarantees (game size) (lowerGoal v) (initial size)
    upper : BlackGuarantees (game size) (upperGoal v) (initial size)
open HasValue public

Problem1 : Set
Problem1 = WhiteGuarantees (game four) winGoal (initial four)

-- A value of +4 alone does not fix the two separate terminal disc counts.
-- This statement retains an optimal strategy pair and its 16–20 outcome.
Problem2 : Set
Problem2 = Σ (HasValue six 4) (λ optimal →
  Σ (State six) (λ t →
    CompletedPlay (game six) white (forcing (lower optimal))
      (forcing (upper optimal)) (initial six) t ×
    ((discs black t ≡ 16) × (discs white t ≡ 20))))

Problem3 : Set
Problem3 = HasValue eight 0

-- Problems 2 and 3 are types only; this module asserts no inhabitants.

lower-eight-wins :
  WhiteGuarantees (game four) (lowerGoal 8) (initial four) → Problem1
lower-eight-wins lowerBound = record
  { forcing = forcing lowerBound
  ; responds = λ opposing → strengthen opposing (responds lowerBound opposing)
  }
  where
  strengthen : (opposing : Strategy (State four)) → Σ (State four) (λ t →
    CompletedPlay (game four) white (forcing lowerBound) opposing (initial four) t ×
    (lowerGoal 8 t ≡ true)) →
    Σ (State four) (λ t →
    CompletedPlay (game four) white (forcing lowerBound) opposing (initial four) t ×
    (winGoal t ≡ true))
  strengthen opposing (t , (play , accepted)) = t , (play ,
    ≤ᵇ-complete (≤-trans (one≤plus-eight (discs black t)) (≤ᵇ-sound accepted)))
