{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Share the fixed lower-goal checker boundary across row parts.
module Othello.SharedInlineSteps6 where

open import Prelude
open import Game.Core using (white)
open import Game.Symmetry using (Proven)
open import Othello.Board using (State; Coord; six)
open import Othello.Statements using (lowerGoal)
open import Othello.DirectSymmetry6 using (lowerTransport6)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.EncodedStepAssembly as Assembly
import Othello.InlineEntries6 as Rules
import Othello.InlineRows6 as Rows
import Othello.RowPacked6 as Packed

private
  module Check = Rows.Checking white (lowerGoal 4) lowerTransport6
  module A = Assembly.Assembly Packed.decode Rules.specializedGame6 white (lowerGoal 4)

Compatible : (ℕ → Maybe Packed.PackedState) → (ℕ → Packed.PackedState) → Set
Compatible = Check.V.Compatible

Step : (ℕ → Packed.PackedState) → ℕ → Set
Step = A.Step

checkRows : ∀ {n} → (ℕ → Maybe Packed.PackedState) →
  (B.Fin n → ℕ) → B.Vec (State six) n →
  B.Vec (D.DirectedCertificate ℕ (Coord six)) n → Bool
checkRows = Check.checkRows

abstract
  steps : ∀ {n} L (embed : B.Fin n → ℕ) (ss : B.Vec (State six) n)
    (cs : B.Vec (D.DirectedCertificate ℕ (Coord six)) n) →
    checkRows L embed ss cs ≡ true →
    (G : ℕ → Packed.PackedState) → Compatible L G →
    (∀ i → Packed.decode (G (embed i)) ≡ B.lookupVec ss i) →
    ∀ i → Step G (embed i)
  steps L embed ss cs accepted G compatible own i earlier =
    subst (Proven Rules.specializedGame6 white (lowerGoal 4)) (sym (own i))
      (Check.V.Old.row-sound (λ j → Packed.decode (G j)) (embed i) earlier
        (Check.linked L embed ss cs accepted G compatible i))
