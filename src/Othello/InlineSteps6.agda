{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Hide certificate-indexed intermediates behind a generic rule.
module Othello.InlineSteps6 where

open import Prelude
open import Game.Core using (Player)
open import Game.Symmetry using (CertificateTransport; Proven)
open import Othello.Board using (State; Coord; six)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.EncodedStepAssembly as Step
import Othello.Fast6 as Fast
import Othello.InlineEntries6 as Rules
import Othello.InlineRows6 as Rows
import Othello.RowPacked6 as Packed

module Checking (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Check = Rows.Checking p goal laws
  module A = Step.Assembly Packed.decode Rules.specializedGame6 p goal

  abstract
    steps : ∀ {n} L (embed : B.Fin n → ℕ) (ss : B.Vec (State six) n)
      (cs : B.Vec (D.DirectedCertificate ℕ (Coord six)) n) →
      Check.checkRows L embed ss cs ≡ true →
      (G : ℕ → Packed.PackedState) → Check.V.Compatible L G →
      (∀ i → Packed.decode (G (embed i)) ≡ B.lookupVec ss i) →
      ∀ i → A.Step G (embed i)
    steps L embed ss cs accepted G compatible own i earlier =
      subst (Proven Rules.specializedGame6 p goal) (sym (own i))
        (Check.V.Old.row-sound (λ j → Packed.decode (G j)) (embed i) earlier
          (Check.linked L embed ss cs accepted G compatible i))
