{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.DeepPerft where

open import Prelude
open import Othello.Board
open import Tests.Perft

-- OEIS A124004, counting a compulsory pass as a ply.
eight-five : perft 5 (initial eight) ≡ 1396
eight-five = refl

-- Independently computed by the scalar Python reference.
four-five : perft 5 (initial four) ≡ 424
four-five = refl
