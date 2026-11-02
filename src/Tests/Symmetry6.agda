{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. These import arbitrary-board theorems, rather than turning
-- finite/native rule samples into general transport evidence.
module Tests.Symmetry6 where

open import Prelude
open import Othello.Board
open import Othello.Symmetry6
open import Game.Symmetry

all-actions-invertible : ∀ σ s → transformState (inverse σ) (transformState σ s) ≡ s
all-actions-invertible = transformState-inverse

all-actions-lookup : ∀ σ b q → at {size = six} (transformBoard σ b) (coordinate σ q) ≡ at {size = six} b q
all-actions-lookup = at-forward

all-actions-compose : ∀ σ τ s →
  transformState σ (transformState τ s) ≡ transformState (compose σ τ) s
all-actions-compose = transformState-compose

invalid-tag-rejected : acceptedTag8 8 ≡ false
invalid-tag-rejected = refl
