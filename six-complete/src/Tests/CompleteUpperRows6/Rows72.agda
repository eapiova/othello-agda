{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted untrusted certificate source; safe Agda must check this module.
module Tests.CompleteUpperRows6.Rows72 where
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
import Tests.TextUpperPacked6.Group72 as Own
import Tests.CompleteUpperRows6.Body72 as Body
module Parts = Assembly.Assembly black (upperGoal 4)
module Certified = Box.Assembly black (upperGoal 4)
abstract
  source : Rows.A.Partial Global.G (M.rows 720000 10000 (Rows.ps Global.G 720000 10000))
  source = Rows.partial Global.G 720000 10000 (Codec.bodies 10000 Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {G = Global.G} {base = 720000} {n = 10000}
    {xs = Rows.ps Global.G 720000 10000} {target = Own.table}
    (Rows.lookup-ps Global.G 720000 10000) source
    (Range.check-sound 720000 10000 (T.domain Own.table) refl)
  certified : Certified.Certified Global.G Own.table
  certified = Certified.certify Global.G Own.table partial
