{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted untrusted certificate source; safe Agda must check this module.
module Tests.CompleteUpperRows6.Rows653 where
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
import Tests.TextUpperPacked6.Group653 as Own
import Tests.CompleteUpperRows6.Body653 as Body
module Parts = Assembly.Assembly black (upperGoal 4)
module Certified = Box.Assembly black (upperGoal 4)
abstract
  source : Rows.A.Partial Global.G (M.rows 6530000 11 (Rows.ps Global.G 6530000 11))
  source = Rows.partial Global.G 6530000 11 (Codec.bodies 11 Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {G = Global.G} {base = 6530000} {n = 11}
    {xs = Rows.ps Global.G 6530000 11} {target = Own.table}
    (Rows.lookup-ps Global.G 6530000 11) source
    (Range.check-sound 6530000 11 (T.domain Own.table) refl)
  certified : Certified.Certified Global.G Own.table
  certified = Certified.certify Global.G Own.table partial
