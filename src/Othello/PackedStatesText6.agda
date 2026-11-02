{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted total data decoder. Game/ownership assertions need safe checking.
module Othello.PackedStatesText6 where

open import Prelude
open import Agda.Builtin.Char using (Char; primCharToNat)
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Nat renaming (_-_ to _∸_; _==_ to _≡ᵇ_)
open import Othello.Board using (Player; black; white)
import Othello.Finite as F
import Othello.RowPacked6 as P
import Game.Balanced as B

private
  code : Char → ℕ
  code c = primCharToNat c ∸ 256

  player : Char → Player
  player c with primCharToNat c ≡ᵇ 87
  ... | true = white
  ... | false = black

  read : (n : ℕ) → List Char → B.Vec P.PackedState n
  read zero cs = B.nil
  read (suc n) (p ∷ a ∷ b ∷ c ∷ d ∷ e ∷ f ∷ tail) =
    B.cons (P.packed
      (code a F.∷ code b F.∷ code c F.∷ code d F.∷ code e F.∷ code f F.∷ F.[])
      (player p)) (read n tail)
  read (suc n) _ = B.cons P.initialPacked (read n [])

states : (n : ℕ) → String → B.Vec P.PackedState n
states n text = read n (primStringToList text)
