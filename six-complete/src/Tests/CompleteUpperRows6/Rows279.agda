{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted untrusted certificate source; safe Agda must check this module.
module Tests.CompleteUpperRows6.Rows279 where
open import Prelude
open import Game.Core using (black)
open import Othello.Statements using (upperGoal)
import Game.NatMap as M
import Game.StepRangeAssembly as Range
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Assembly
import Othello.TextCertifiedAssembly6 as Box
import Othello.ConsecutivePackedUpper6 as Rows
import Othello.UnicodeCompact6 as Codec
import Tests.TextUpperPacked6.Root as Global
import Tests.TextUpperPacked6.Group279 as Own
import Tests.CompleteUpperRows6.Body279 as Body
module Parts = Assembly.Assembly black (upperGoal 4)
module Certified = Box.Assembly black (upperGoal 4)
abstract
  source : Rows.A.Partial Global.G (M.rows 2790000 10000 (Rows.ps Global.G 2790000 10000))
  source = Rows.partial Global.G 2790000 10000 (Codec.bodies 10000 Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {G = Global.G} {base = 2790000} {n = 10000}
    {xs = Rows.ps Global.G 2790000 10000} {target = Own.table}
    (Rows.lookup-ps Global.G 2790000 10000) source
    (Range.check-sound 2790000 10000 (T.domain Own.table) refl)
  certified : Certified.Certified Global.G Own.table
  certified = Certified.certify Global.G Own.table partial
