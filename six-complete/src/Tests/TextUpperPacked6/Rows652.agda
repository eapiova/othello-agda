{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted data/proofs; global ownership remains explicit.
module Tests.TextUpperPacked6.Rows652 where
open import Prelude
open import Game.Core using (black)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (upperGoal)
import Othello.RowPacked6 as Packed
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Assembly
import Othello.InlineEntries6 as Rules
module Parts = Assembly.Assembly black (upperGoal 4)
import Game.NatMap as M
import Game.StepRangeAssembly as Range
import Othello.ConsecutivePackedUpper6 as Rows
import Othello.UnicodeCompact6 as Codec
import Tests.TextUpperPacked6.Root as Global
import Tests.TextUpperPacked6.Group652 as Own
import Tests.TextUpperPacked6.Body652 as Body
abstract
  source : Rows.A.Partial Global.G (M.rows 6520000 10000 (Rows.ps Global.G 6520000 10000))
  source = Rows.partial Global.G 6520000 10000 (Codec.bodies 10000 Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {G = Global.G} {base = 6520000} {n = 10000}
    {xs = Rows.ps Global.G 6520000 10000} {target = Own.table}
    (Rows.lookup-ps Global.G 6520000 10000) source
    (Range.check-sound 6520000 10000 (T.domain Own.table) refl)
