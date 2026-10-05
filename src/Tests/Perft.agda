{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.Perft where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Othello.Board
open import Othello.Rules using (successors)
open import Tests.Rules using (passBoard; emptyState)

-- Passing is one ply. A terminal board has no positive-depth continuations.
mutual
  perft : ∀ {size} → ℕ → State size → ℕ
  perft zero s = 1
  perft (suc n) s = children n (successors s)

  children : ∀ {size} → ℕ → List (State size) → ℕ
  children n [] = 0
  children n (s ∷ ss) = perft n s + children n ss

eight-zero : perft 0 (initial eight) ≡ 1
eight-zero = refl

eight-one : perft 1 (initial eight) ≡ 4
eight-one = refl

eight-two : perft 2 (initial eight) ≡ 12
eight-two = refl

eight-three : perft 3 (initial eight) ≡ 56
eight-three = refl

eight-four : perft 4 (initial eight) ≡ 244
eight-four = refl

four-one : perft 1 (initial four) ≡ 4
four-one = refl

four-two : perft 2 (initial four) ≡ 12
four-two = refl

four-three : perft 3 (initial four) ≡ 44
four-three = refl

four-four : perft 4 (initial four) ≡ 128
four-four = refl

pass-one-ply : perft 1 passBoard ≡ 1
pass-one-ply = refl

terminal-positive-depth : perft 1 emptyState ≡ 0
terminal-positive-depth = refl
