{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted text-backed state map. Membership has an independent unit domain.
module Othello.TextStateMap6 where

open import Prelude
open import Agda.Builtin.String using (String)
open import Agda.Builtin.Nat using (_<_) renaming (_-_ to _∸_)
import Game.Balanced as B
import Game.NatMap as M
import Othello.RowPacked6 as P
import Othello.DirectPackedText6 as Text

data Map : Set where
  absent : Map
  rows : ℕ → ℕ → String → Map
  branch : ℕ → Map → Map → Map

lookup : Map → ℕ → Maybe P.PackedState
lookup absent key = nothing
lookup (rows base n text) key with key < base
... | true = nothing
... | false with B.finFromNat n (key ∸ base)
...   | nothing = nothing
...   | just i = just (Text.at (key ∸ base) text)
lookup (branch pivot l r) key with key < pivot
... | true = lookup l key
... | false = lookup r key

private
  nothing-elim : ∀ {A B : Set} {u : A} → nothing ≡ just u → B
  nothing-elim ()

  units : (n : ℕ) → B.Vec ⊤ n
  units zero = B.nil
  units (suc n) = B.cons tt (units n)

  units-at : ∀ n (i : B.Fin n) → B.lookupVec (units n) i ≡ tt
  units-at zero ()
  units-at (suc n) B.fzero = refl
  units-at (suc n) (B.fsuc i) = units-at n i

domain : Map → M.Map ⊤
domain absent = M.absent
domain (rows base n text) = M.rows base n (units n)
domain (branch pivot l r) = M.branch pivot (domain l) (domain r)

domain-hit : ∀ table key u → lookup table key ≡ just u → M.lookup (domain table) key ≡ just tt
domain-hit absent key u ()
domain-hit (rows base n text) key u hit with key < base
... | true = nothing-elim hit
... | false with B.finFromNat n (key ∸ base)
...   | nothing = nothing-elim hit
...   | just i = cong just (units-at n i)
domain-hit (branch pivot l r) key u hit with key < pivot
... | true = domain-hit l key u hit
... | false = domain-hit r key u hit

totalize : Map → P.PackedState → ℕ → P.PackedState
totalize table fallback key = fromMaybe fallback (lookup table key)

self-compatible : ∀ table fallback key u → lookup table key ≡ just u → totalize table fallback key ≡ u
self-compatible table fallback key u hit rewrite hit = refl
