{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. A sparse numeric resolver contains data, never proof claims.
module Game.NatMap where

open import Prelude
open import Agda.Builtin.Nat using (_<_) renaming (_-_ to _∸_)
import Game.Balanced as B

data Map (A : Set) : Set where
  absent : Map A
  rows : (base n : ℕ) → B.Vec A n → Map A
  branch : ℕ → Map A → Map A → Map A

lookup : ∀ {A} → Map A → ℕ → Maybe A
lookup absent key = nothing
lookup (rows base n xs) key with key < base
... | true = nothing
... | false with B.finFromNat n (key ∸ base)
... | nothing = nothing
... | just i = just (B.lookupVec xs i)
lookup (branch pivot l r) key with key < pivot
... | true = lookup l key
... | false = lookup r key
