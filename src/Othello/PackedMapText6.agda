{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. A total data decoder; the existing checker validates its uses.
module Othello.PackedMapText6 where

open import Prelude
open import Agda.Builtin.Char using (Char; primCharToNat)
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Nat using (_+_; _*_) renaming (_-_ to _∸_; _==_ to _≡ᵇ_)
open import Othello.Board using (Player; black; white)
import Othello.Finite as F
import Othello.RowPacked6 as P
import Game.NatMap as M
import Game.Balanced as B

private
  key : List Char → Maybe (ℕ × List Char)
  key (a ∷ b ∷ tail) = just
    ((1024 * (primCharToNat a ∸ 16384) + (primCharToNat b ∸ 16384)) , tail)
  key _ = nothing

  code : Char → ℕ
  code c = primCharToNat c ∸ 256

  player : Char → Player
  player c with primCharToNat c ≡ᵇ 87
  ... | true = white
  ... | false = black

  packed : List Char → Maybe (P.PackedState × List Char)
  packed (p ∷ a ∷ b ∷ c ∷ d ∷ e ∷ f ∷ tail) = just
    (P.packed (code a F.∷ code b F.∷ code c F.∷ code d F.∷ code e F.∷ code f F.∷ F.[])
      (player p) , tail)
  packed _ = nothing

  read : ℕ → List Char → Maybe (M.Map P.PackedState × List Char)
  read zero cs = nothing
  read (suc fuel) [] = nothing
  read (suc fuel) (c ∷ cs) with primCharToNat c ∸ 65
  ... | 0 = just (M.absent , cs)
  ... | 1 with key cs
  ...   | nothing = nothing
  ...   | just (pivot , rest) with read fuel rest
  ...     | nothing = nothing
  ...     | just (l , tail) with read fuel tail
  ...       | nothing = nothing
  ...       | just (r , end) = just (M.branch pivot l r , end)
  read (suc fuel) (c ∷ cs) | 17 with key cs
  ... | nothing = nothing
  ... | just (base , rest) with packed rest
  ...   | nothing = nothing
  ...   | just (s , tail) = just (M.rows base 1 (B.cons s B.nil) , tail)
  read (suc fuel) (c ∷ cs) | _ = nothing

  length : ∀ {A : Set} → List A → ℕ
  length [] = zero
  length (_ ∷ xs) = suc (length xs)

  finish : Maybe (M.Map P.PackedState × List Char) → M.Map P.PackedState
  finish (just (table , [])) = table
  finish _ = M.absent

-- Decoding does not assert validity or compatibility with the global map.
-- Both remain obligations of the unchanged sound row checker and assembly.
table : String → M.Map P.PackedState
table text = finish (read (suc (length (primStringToList text))) (primStringToList text))
