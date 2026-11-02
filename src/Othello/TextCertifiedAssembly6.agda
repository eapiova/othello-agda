{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted proof containers keep concrete lookup functions out of field
-- normalization. Their only constructor still requires the complete Partial.
module Othello.TextCertifiedAssembly6 where

open import Prelude
open import Game.Core using (Player)
open import Game.Symmetry using (Proven)
open import Othello.Board using (State; six)
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Old

module Assembly (p : Player) (goal : State six → Bool) where
  module A = Old.Assembly p goal

  data Certified (G : ℕ → Packed.PackedState) (table : T.Map) : Set where
    certified : A.Partial G table → Certified G table

  certify : ∀ G table → A.Partial G table → Certified G table
  certify G table proof = certified proof

  data ProvenMap (G : ℕ → Packed.PackedState) : Set where
    proven-map : (∀ key → Proven Rules.specializedGame6 p goal (Packed.decode (G key))) → ProvenMap G

  at : ∀ {G} → ProvenMap G → ∀ key → Proven Rules.specializedGame6 p goal (Packed.decode (G key))
  at (proven-map proof) = proof

  abstract
    join : ∀ {G l r} pivot → Certified G l → Certified G r → Certified G (T.branch pivot l r)
    join {G} {l} {r} pivot (certified left) (certified right) =
      certified (A.join {G = G} {l = l} {r = r} pivot left right)

    finish : (table : T.Map) (fallback : Packed.PackedState) →
      Proven Rules.specializedGame6 p goal (Packed.decode fallback) →
      Certified (T.totalize table fallback) table →
      ProvenMap (T.totalize table fallback)
    finish table fallback won (certified proof) = proven-map (A.finish table fallback won proof)
