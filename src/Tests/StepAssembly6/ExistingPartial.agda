{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. The SAME2600-row Partial, with unowned citations still open.
module Tests.StepAssembly6.ExistingPartial where

open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.Fast6 as Fast
import Othello.StepFromNatAssembly6 as Bridge
import Tests.CompletionBatchLowerACombined6.Root as Existing

module B = Bridge.Assembly Fast.fastGame6 white (lowerGoal 4) lowerTransport6

abstract
  partial : B.New.Partial Existing.G Existing.ownedStates
  partial = B.from-partial Existing.G Existing.C Existing.ownedStates Existing.partial

-- This does not prove missing rows, a complete initial bound or the SAME pair.
