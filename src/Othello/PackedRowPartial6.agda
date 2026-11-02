{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Keep row ownership symbolic until the Partial boundary.
module Othello.PackedRowPartial6 where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Game.Core using (white)
open import Othello.Board using (State; Coord; six)
open import Othello.Statements using (lowerGoal)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.EncodedStepAssembly as Assembly
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.PackedVectors6 as Vectors
import Othello.SharedInlineSteps6 as Shared

module A = Assembly.Assembly Packed.decode Rules.specializedGame6 white (lowerGoal 4)

abstract
  partial : ∀ {n} base (ss : B.Vec (State six) n)
    (cs : B.Vec (D.DirectedCertificate ℕ (Coord six)) n)
    (L : ℕ → Maybe Packed.PackedState) →
    Shared.checkRows L (λ i → base + B.finToNat i) ss cs ≡ true →
    (G : ℕ → Packed.PackedState) → Shared.Compatible L G →
    Laws.Compatible (M.rows base n (Vectors.pack ss)) G →
    A.Partial G (M.rows base n (Vectors.pack ss))
  partial base ss cs L accepted G compatible owned =
    A.rows base (Vectors.pack ss) G
      (Shared.steps L (λ i → base + B.finToNat i) ss cs accepted G compatible
        (Vectors.ownership base ss G owned))
