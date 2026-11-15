{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Pack finite state rows while preserving their exact decoding.
module Othello.PackedVectors6 where

open import Prelude
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
open import Agda.Builtin.Nat using (_+_)
import Othello.RowPacked6 as P

pack : ∀ {n} → B.Vec (State six) n → B.Vec P.PackedState n
pack B.nil = B.nil
pack (B.cons s ss) = B.cons (P.encode s) (pack ss)

decode-lookup : ∀ {n} (ss : B.Vec (State six) n) (i : B.Fin n) →
  P.decode (B.lookupVec (pack ss) i) ≡ B.lookupVec ss i
decode-lookup B.nil ()
decode-lookup (B.cons s ss) B.fzero = P.decode-encode s
decode-lookup (B.cons s ss) (B.fsuc i) = decode-lookup ss i

abstract
  ownership : ∀ {n} base (ss : B.Vec (State six) n) G →
    Laws.Compatible (M.rows base n (pack ss)) G → ∀ i →
    P.decode (G (base + B.finToNat i)) ≡ B.lookupVec ss i
  ownership base ss G compatible i = trans
    (cong P.decode (Laws.rows-aligned base (pack ss) G compatible i))
    (decode-lookup ss i)
