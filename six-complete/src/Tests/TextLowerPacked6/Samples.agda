{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted data/proofs; every row ownership remains explicit.
module Tests.TextLowerPacked6.Samples where
open import Prelude
open import Game.Core using (white)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (lowerGoal)
import Othello.RowPacked6 as Packed
import Othello.TextStateMap6 as T
import Othello.TextCertifiedAssembly6 as Assembly
import Othello.InlineEntries6 as Rules
module Parts = Assembly.Assembly white (lowerGoal 4)
import Tests.TextLowerPacked6.Root as Global
import Tests.TextLowerPacked6.Group6 as GT
import Tests.TextLowerPacked6.Group686 as GH
import Tests.TextLowerPacked6.Rows6 as RT
import Tests.TextLowerPacked6.Rows686 as RH
abstract
  training : Parts.Certified Global.G GT.table
  training = Parts.certify Global.G GT.table RT.partial
  heldout : Parts.Certified Global.G GH.table
  heldout = Parts.certify Global.G GH.table RH.partial
