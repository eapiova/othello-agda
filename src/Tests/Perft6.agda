{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.Perft6 where

open import Prelude
open import Othello.Board using (six; initial)
open import Tests.Perft using (perft)

-- Independent native and scalar counts are recorded outside the proof.
-- These closed kernel checks use the original, size-generic rules.
six-zero : perft 0 (initial six) ≡ 1
six-zero = refl

six-one : perft 1 (initial six) ≡ 4
six-one = refl

six-two : perft 2 (initial six) ≡ 12
six-two = refl

six-three : perft 3 (initial six) ≡ 56
six-three = refl

six-four : perft 4 (initial six) ≡ 244
six-four = refl
