{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted; literal subtree checks, full cited-map premise remains open.
module Tests.InlineLowerPrefixes6.Joint where
open import Prelude
open import Game.Core using (white; black)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (lowerGoal; upperGoal; Problem2)
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.SpliceSuffix21 as Suffix
import Tests.InlineLowerPrefixes6.Closed as Lower
import Tests.InlineLowerPrefixes6.Data as LowerData
import Tests.InlineUpperPrefixes6.Closed as Upper
import Tests.InlineUpperPrefixes6.Data as UpperData
abstract
  problem2-from-complete-maps : (GL GU : ℕ → Packed.PackedState) →
    Lower.Check.Local.V.Compatible LowerData.L GL →
    Upper.Check.Local.V.Compatible UpperData.L GU →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (GL key))) →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (GU key))) → Problem2
  problem2-from-complete-maps GL GU compatibleLower compatibleUpper provenLower provenUpper =
    Suffix.problem2-from-first21
      (Lower.lower0 GL compatibleLower provenLower , Upper.upper0 GU compatibleUpper provenUpper)
      (Lower.lower1 GL compatibleLower provenLower , Upper.upper1 GU compatibleUpper provenUpper)
      (Lower.lower2 GL compatibleLower provenLower , Upper.upper2 GU compatibleUpper provenUpper)
      (Lower.lower3 GL compatibleLower provenLower , Upper.upper3 GU compatibleUpper provenUpper)
      (Lower.lower4 GL compatibleLower provenLower , Upper.upper4 GU compatibleUpper provenUpper)
      (Lower.lower5 GL compatibleLower provenLower , Upper.upper5 GU compatibleUpper provenUpper)
      (Lower.lower6 GL compatibleLower provenLower , Upper.upper6 GU compatibleUpper provenUpper)
      (Lower.lower7 GL compatibleLower provenLower , Upper.upper7 GU compatibleUpper provenUpper)
      (Lower.lower8 GL compatibleLower provenLower , Upper.upper8 GU compatibleUpper provenUpper)
      (Lower.lower9 GL compatibleLower provenLower , Upper.upper9 GU compatibleUpper provenUpper)
      (Lower.lower10 GL compatibleLower provenLower , Upper.upper10 GU compatibleUpper provenUpper)
      (Lower.lower11 GL compatibleLower provenLower , Upper.upper11 GU compatibleUpper provenUpper)
      (Lower.lower12 GL compatibleLower provenLower , Upper.upper12 GU compatibleUpper provenUpper)
      (Lower.lower13 GL compatibleLower provenLower , Upper.upper13 GU compatibleUpper provenUpper)
      (Lower.lower14 GL compatibleLower provenLower , Upper.upper14 GU compatibleUpper provenUpper)
      (Lower.lower15 GL compatibleLower provenLower , Upper.upper15 GU compatibleUpper provenUpper)
      (Lower.lower16 GL compatibleLower provenLower , Upper.upper16 GU compatibleUpper provenUpper)
      (Lower.lower17 GL compatibleLower provenLower , Upper.upper17 GU compatibleUpper provenUpper)
      (Lower.lower18 GL compatibleLower provenLower , Upper.upper18 GU compatibleUpper provenUpper)
      (Lower.lower19 GL compatibleLower provenLower , Upper.upper19 GU compatibleUpper provenUpper)
      (Lower.lower20 GL compatibleLower provenLower , Upper.upper20 GU compatibleUpper provenUpper)
-- Both fully proved global maps and both exact resolver compatibilities are still required.
