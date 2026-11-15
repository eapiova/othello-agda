{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted data/proofs; global ownership remains explicit.
module Tests.TextUpperPacked6.Compatible where
open import Prelude
open import Game.Core using (black)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (upperGoal)
import Othello.RowPacked6 as Packed
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Assembly
import Othello.InlineEntries6 as Rules
module Parts = Assembly.Assembly black (upperGoal 4)
import Othello.FullUpperAlign6 as Align
import Tests.InlineUpperPrefixes6.Data as PrefixData
import Tests.InlineUpperPrefixes6.Closed as Prefix
import Tests.TextUpperPacked6.Root as Global
module Check = Align.Checking Packed.equal Packed.equal-sound
abstract
  compatible : Prefix.Check.Local.V.Compatible PrefixData.L Global.G
  compatible = Check.compatible-sound PrefixData.demand Global.G refl
