{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Kernel-evaluated local guarantees for the literal SAME-pair suffix.
module Othello.SpliceSuffix6.State23 where

open import Prelude
open import Game.Core using (Guarantees; white; black)
open import Game.Soundness using (checkSound)
open import Othello.Statements using (lowerGoal; upperGoal)
import Game.Search as Search
import Othello.Fast6 as Fast
import Othello.SpliceLine6 as Line

abstract
  lowerAccepted :
    Search.forces 21 Fast.fastGame6 white (lowerGoal 4) Line.p23 ≡ true
  lowerAccepted = refl

  upperAccepted :
    Search.forces 21 Fast.fastGame6 black (upperGoal 4) Line.p23 ≡ true
  upperAccepted = refl

  lower : Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p23
  lower = checkSound Fast.fastGame6 white (lowerGoal 4) Line.p23
    (Search.witness 21 Fast.fastGame6 white (lowerGoal 4) Line.p23)
    (Search.forces-sound 21 Fast.fastGame6 white (lowerGoal 4) Line.p23
      lowerAccepted)

  upper : Guarantees Fast.fastGame6 black (upperGoal 4) Line.p23
  upper = checkSound Fast.fastGame6 black (upperGoal 4) Line.p23
    (Search.witness 21 Fast.fastGame6 black (upperGoal 4) Line.p23)
    (Search.forces-sound 21 Fast.fastGame6 black (upperGoal 4) Line.p23
      upperAccepted)
