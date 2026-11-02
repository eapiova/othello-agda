{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Existing accepted rows are used without changing their checker.
module Tests.NatIndexedRecursion6 where

open import Prelude
open import Game.Core using (white; Guarantees)
open import Game.Symmetry using (Proven)
import Game.NatOrder as N
import Game.NatAccessibility as Access
import Game.NatIndexedRecursion as Rec
import Tests.NatIndexed6 as Old
open import Othello.Encode6 using (stateEquality6)
open import Othello.Board using (six)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.Fast6 as Fast

large-accessibility-computes :
  Access.zeroFrom (Access.wellFounded 7000000) ≡ N.wellFounded 0
large-accessibility-computes = refl

module New = Rec.Checking stateEquality6 Fast.fastGame6 white
  (lowerGoal 4) lowerTransport6

reused-rows : ∀ i → New.V.TreeOK Old.G i (Old.G i) (Old.C i)
reused-rows = Old.rows

proven : Proven Fast.fastGame6 white (lowerGoal 4) (Old.G 3)
proven = New.global-proven Old.G Old.C reused-rows 3

guarantee : Guarantees Fast.fastGame6 white (lowerGoal 4) (Old.G 3)
guarantee = New.global-sound Old.G Old.C reused-rows 3
