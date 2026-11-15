{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted. Reuse both accepted10000-row Parts; no Boolean rerun.
module Tests.ParametricFullUpper6.Samples where
open import Game.Core using (black)
open import Othello.Statements using (upperGoal)
import Othello.TextCertifiedAssembly6 as Box
import Tests.TextUpperPacked6.Root as Global
import Tests.TextUpperPacked6.Group6 as G6
import Tests.TextUpperPacked6.Group652 as G652
import Tests.TextUpperPacked6.Rows6 as P6
import Tests.TextUpperPacked6.Rows652 as P652
module Parts = Box.Assembly black (upperGoal 4)
abstract
  part6 : Parts.Certified Global.G G6.table
  part6 = Parts.certify Global.G G6.table P6.partial
  part652 : Parts.Certified Global.G G652.table
  part652 = Parts.certify Global.G G652.table P652.partial
