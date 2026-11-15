{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted benchmark predicates; raw white-minus-black, no empty-square award.
module Tests.Bench6.Goals where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Game.Core using (black; white)
open import Othello.Board using (State; discs)
open import Othello.Order using (_≤ᵇ_)

-- neg n denotes -n (including an intentionally harmless second spelling of 0).
data Score : Set where
  pos neg : ℕ → Score

lowerGoal upperGoal : ∀ {size} → Score → State size → Bool
lowerGoal (pos n) s = (discs black s + n) ≤ᵇ discs white s
lowerGoal (neg n) s = discs black s ≤ᵇ (discs white s + n)
upperGoal (pos n) s = discs white s ≤ᵇ (discs black s + n)
upperGoal (neg n) s = (discs white s + n) ≤ᵇ discs black s
