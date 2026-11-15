{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted untrusted certificate source; safe Agda must check this module.
module Tests.CompleteLowerRows6.Rows687 where
open import Prelude
open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
import Game.NatMap as M
import Game.StepRangeAssembly as Range
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Assembly
import Othello.TextCertifiedAssembly6 as Box
import Othello.ConsecutivePackedRows6 as Rows
import Othello.UnicodeCompact6 as Codec
import Tests.TextLowerPacked6.Root as Global
import Tests.TextLowerPacked6.Group687 as Own
import Tests.CompleteLowerRows6.Body687 as Body
module Parts = Assembly.Assembly white (lowerGoal 4)
module Certified = Box.Assembly white (lowerGoal 4)
abstract
  source : Rows.A.Partial Global.G (M.rows 6870000 3047 (Rows.ps Global.G 6870000 3047))
  source = Rows.partial Global.G 6870000 3047 (Codec.bodies 3047 Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {G = Global.G} {base = 6870000} {n = 3047}
    {xs = Rows.ps Global.G 6870000 3047} {target = Own.table}
    (Rows.lookup-ps Global.G 6870000 3047) source
    (Range.check-sound 6870000 3047 (T.domain Own.table) refl)
  certified : Certified.Certified Global.G Own.table
  certified = Certified.certify Global.G Own.table partial
