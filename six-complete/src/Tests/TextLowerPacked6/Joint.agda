{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted data/proofs; every row ownership remains explicit.
module Tests.TextLowerPacked6.Joint where
open import Prelude
open import Game.Core using (white; black)
open import Othello.Statements using (lowerGoal; upperGoal; Problem2)
import Othello.RowPacked6 as Packed
import Othello.TextCertifiedAssembly6 as Box
import Tests.InlineLowerPrefixes6.Joint as PrefixJoint
import Tests.InlineLowerPrefixes6.Closed as LowerPrefix
import Tests.InlineLowerPrefixes6.Data as LowerData
import Tests.InlineUpperPrefixes6.Closed as UpperPrefix
import Tests.InlineUpperPrefixes6.Data as UpperData
import Tests.TextLowerPacked6.Root as Lower
import Tests.TextLowerPacked6.Assembly as LowerAssembly
import Tests.TextLowerPacked6.Compatible as LowerCompatible
import Tests.TextUpperPacked6.Root as Upper
import Tests.ParametricFullUpper6.Assembly as UpperAssembly
import Tests.TextUpperPacked6.Compatible as UpperCompatible
module L = Box.Assembly white (lowerGoal 4)
module U = Box.Assembly black (upperGoal 4)
abstract
  bridge : (GL GU : ℕ → Packed.PackedState) →
    LowerPrefix.Check.Local.V.Compatible LowerData.L GL →
    UpperPrefix.Check.Local.V.Compatible UpperData.L GU →
    L.ProvenMap GL → U.ProvenMap GU → Problem2
  bridge GL GU lc uc lp up =
    PrefixJoint.problem2-from-complete-maps GL GU lc uc (L.at lp) (U.at up)
  complete : LowerAssembly.Actual.CheckedParts → UpperAssembly.Actual.CheckedParts → Problem2
  complete lower upper = bridge Lower.G Upper.G
    LowerCompatible.compatible UpperCompatible.compatible
    (LowerAssembly.complete lower) (UpperAssembly.complete upper)
-- No CheckedParts record is supplied. The initial6x6 theorem is still open.
