{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted total decoder. Skip text without constructing earlier states.
module Othello.DirectPackedText6 where

open import Prelude
open import Agda.Builtin.Char using (Char; primCharToNat)
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Nat using (_*_) renaming (_-_ to _∸_; _==_ to _≡ᵇ_)
open import Game.Core using (Player; white; black)
import Othello.Finite as F
import Othello.RowPacked6 as P

private
  drop : ∀ {A : Set} → ℕ → List A → List A
  drop zero xs = xs
  drop (suc n) [] = []
  drop (suc n) (x ∷ xs) = drop n xs

  player : Char → Player
  player c with primCharToNat c ≡ᵇ 87
  ... | true = white
  ... | false = black

  read : List Char → P.PackedState
  read (p ∷ a ∷ b ∷ c ∷ d ∷ e ∷ f ∷ tail) = P.packed
    ((primCharToNat a ∸ 256) F.∷ (primCharToNat b ∸ 256) F.∷
     (primCharToNat c ∸ 256) F.∷ (primCharToNat d ∸ 256) F.∷
     (primCharToNat e ∸ 256) F.∷ (primCharToNat f ∸ 256) F.∷ F.[]) (player p)
  read _ = P.initialPacked

at : ℕ → String → P.PackedState
at index text = read (drop (7 * index) (primStringToList text))
