{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Kernel-evaluated local guarantees for the literal SAME-pair suffix.
module Othello.SpliceSuffix6.State20Boolean where

open import Prelude
open import Game.Core using (Guarantees; white; black)
open import Game.Soundness using (checkSound)
open import Othello.Statements using (lowerGoal; upperGoal)
import Game.Search as Search
import Game.BooleanSearch as BoolSearch
import Othello.Fast6 as Fast
import Othello.SpliceLine6 as Line

abstract
  lowerAccepted :
    BoolSearch.forcesB 27 Fast.fastGame6 white (lowerGoal 4) Line.p20 ≡ true
  lowerAccepted = refl

  upperAccepted :
    BoolSearch.forcesB 27 Fast.fastGame6 black (upperGoal 4) Line.p20 ≡ true
  upperAccepted = refl

  lower : Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p20
  lower = checkSound Fast.fastGame6 white (lowerGoal 4) Line.p20
    (Search.witness 27 Fast.fastGame6 white (lowerGoal 4) Line.p20)
    (BoolSearch.forcesB-sound 27 Fast.fastGame6 white (lowerGoal 4) Line.p20
      lowerAccepted)

  upper : Guarantees Fast.fastGame6 black (upperGoal 4) Line.p20
  upper = checkSound Fast.fastGame6 black (upperGoal 4) Line.p20
    (Search.witness 27 Fast.fastGame6 black (upperGoal 4) Line.p20)
    (BoolSearch.forcesB-sound 27 Fast.fastGame6 black (upperGoal 4) Line.p20
      upperAccepted)
