{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted data/proofs; every row ownership remains explicit.
module Tests.TextLowerPacked6.Rows686 where
open import Prelude
open import Game.Core using (white)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (lowerGoal)
import Othello.RowPacked6 as Packed
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Assembly
import Othello.InlineEntries6 as Rules
module Parts = Assembly.Assembly white (lowerGoal 4)
import Game.NatMap as M
import Game.StepRangeAssembly as Range
import Othello.ConsecutivePackedRows6 as Rows
import Othello.UnicodeCompact6 as Codec
import Tests.TextLowerPacked6.Root as Global
import Tests.TextLowerPacked6.Group686 as Own
import Tests.TextLowerPacked6.Body686 as Body
abstract
  source : Rows.A.Partial Global.G (M.rows 6860000 10000 (Rows.ps Global.G 6860000 10000))
  source = Rows.partial Global.G 6860000 10000 (Codec.bodies 10000 Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {G = Global.G} {base = 6860000} {n = 10000}
    {xs = Rows.ps Global.G 6860000 10000} {target = Own.table}
    (Rows.lookup-ps Global.G 6860000 10000) source
    (Range.check-sound 6860000 10000 (T.domain Own.table) refl)
