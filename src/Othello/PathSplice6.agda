{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Conditional SAME-pair assembly, generic in the legal trace.
module Othello.PathSplice6 where

open import Prelude
open import Game.Core
open import Game.Transfer using (Agreement; guarantees-transfer; completedPlay-transfer)
import Game.Transfer as Transfer
import Game.PathSplice as Splice
open import Othello.Board
open import Othello.Statements
import Othello.Rules as Rules
import Othello.Fast6 as Fast

module Along = Splice.Along Fast.fastGame6 (lowerGoal 4) (upperGoal 4)

agreement : Agreement Fast.fastGame6 (Rules.game six)
agreement = Transfer.agreement Fast.next6-correct Fast.turn6-correct Fast.forcedPass6-correct

private
  finish : ∀ t → (discs black t ≡ 16) × (discs white t ≡ 20) →
    Along.Pair (initial six) t → Problem2
  finish t counts (w , b , play) = optimal , t ,
    completedPlay-transfer Fast.fastGame6 (Rules.game six) agreement play , counts
    where
    optimal : HasValue six 4
    optimal = record
      { lower = guarantees-transfer Fast.fastGame6 (Rules.game six) agreement w
      ; upper = guarantees-transfer Fast.fastGame6 (Rules.game six) agreement b }

-- Every prefix guarantee is still an argument, not an initial-game theorem.
problem2-from-prefix-bounds : ∀ {t} (line : Along.Trace (initial six) t) →
  Along.Bounds line → (discs black t ≡ 16) × (discs white t ≡ 20) → Problem2
problem2-from-prefix-bounds {t} line bounds counts = finish t counts (Along.assemble line bounds)
