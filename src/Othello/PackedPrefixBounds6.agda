{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Conditional bridge from a fully proved packed map to literal
-- trace bounds. A Partial with unowned citations cannot supply its premise.
module Othello.PackedPrefixBounds6 where

open import Prelude
open import Game.Core using (Player; Guarantees; white; black)
open import Game.Symmetry using (Proven)
open import Othello.Board using (State; six)
open import Othello.Statements using (lowerGoal; upperGoal)
import Game.Transfer as Transfer
import Game.Soundness as Sound
import Othello.Fast6 as Fast
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.DirectSymmetry6 as Direct

record Witness (G : ℕ → Packed.PackedState) (s : State six) : Set where
  constructor at
  field
    key tag : ℕ
    state-equality : Packed.decode (G key) ≡ Direct.transformTag tag s

private
  to-fast : ∀ p goal s → Proven Rules.specializedGame6 p goal s →
    Proven Fast.fastGame6 p goal s
  to-fast p goal s (certificate , accepted) = certificate ,
    trans (sym (Transfer.check-cong Rules.specializedGame6 Fast.fastGame6
      Rules.agreement p goal s certificate)) accepted

  sound : ∀ p goal s → Proven Fast.fastGame6 p goal s →
    Guarantees Fast.fastGame6 p goal s
  sound p goal s (certificate , accepted) =
    Sound.checkSound Fast.fastGame6 p goal s certificate accepted

abstract
  lower : ∀ {G} →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    ∀ s → Witness G s → Guarantees Fast.fastGame6 white (lowerGoal 4) s
  lower complete s (at key tag equality) = sound white (lowerGoal 4) s
    (Direct.transport-lower tag s
      (subst (Proven Fast.fastGame6 white (lowerGoal 4)) equality
        (to-fast white (lowerGoal 4) _ (complete key))))

  upper : ∀ {G} →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    ∀ s → Witness G s → Guarantees Fast.fastGame6 black (upperGoal 4) s
  upper complete s (at key tag equality) = sound black (upperGoal 4) s
    (Direct.transport-upper tag s
      (subst (Proven Fast.fastGame6 black (upperGoal 4)) equality
        (to-fast black (upperGoal 4) _ (complete key))))
