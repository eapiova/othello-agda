{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Reuse a checked consecutive 6x6 row on any map contained in
-- the same numeric interval, without rerunning its certificate checker.
module Othello.ConsecutiveRange6 where

open import Prelude
open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
import Game.Balanced as B
import Game.NatMap as M
import Game.StepRangeAssembly as Range
import Othello.ConsecutivePackedRows6 as Consecutive
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed

module Bridge = Range.Assembly Packed.decode Rules.specializedGame6 white (lowerGoal 4)
module A = Consecutive.A

retarget : ∀ {G base n} {target : M.Map Packed.PackedState} →
  A.Partial G (M.rows base n (Consecutive.ps G base n)) →
  Range.Contained base n target →
  A.Partial G target
retarget {G} {base} {n} source inside =
  Bridge.retarget (Consecutive.lookup-ps G base n) source inside

checked : ∀ {G base n} {target : M.Map Packed.PackedState} →
  A.Partial G (M.rows base n (Consecutive.ps G base n)) →
  Range.check base n target ≡ true →
  A.Partial G target
checked {base = base} {n} {target} source accepted =
  retarget source (Range.check-sound base n target accepted)
