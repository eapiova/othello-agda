{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted conditional assembly: the caller supplies actual checked roots.
module Othello.SharedProof6 where

open import Prelude
open import Game.Core
open import Game.Certificate using (certificateStrategy)
open import Game.Soundness using (checkSound)
open import Game.Shared using (Proven)
open import Game.Joint
open import Game.Transfer
open import Othello.Board
open import Othello.Encode6 using (stateEquality6)
open import Othello.Statements
open import Othello.Proof6 using (fastAgreement; terminalCounts; counts-sound)
import Othello.Fast6 as Fast
import Othello.Rules as Rules

-- Both guarantees and the completed play use these exact certificates.
problem2-from-proven :
  (lowerRoot : Proven Fast.fastGame6 white (lowerGoal 4) (initial six)) →
  (upperRoot : Proven Fast.fastGame6 black (upperGoal 4) (initial six)) →
  (path : List (State six)) →
  jointCheck stateEquality6 Fast.fastGame6 terminalCounts (initial six)
    (certificateStrategy (proj₁ lowerRoot))
    (certificateStrategy (proj₁ upperRoot)) path ≡ true → Problem2
problem2-from-proven (lowerCertificate , lowerOK) (upperCertificate , upperOK) path jointOK
  with joint-sound stateEquality6 Fast.fastGame6 terminalCounts (initial six)
    (certificateStrategy lowerCertificate) (certificateStrategy upperCertificate) path jointOK
... | t , play , countOK = optimal , t ,
  completedPlay-transfer Fast.fastGame6 (Rules.game six) fastAgreement play ,
  counts-sound t countOK
  where
  lowerBound = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement
    (checkSound Fast.fastGame6 white (lowerGoal 4) (initial six) lowerCertificate lowerOK)
  upperBound = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement
    (checkSound Fast.fastGame6 black (upperGoal 4) (initial six) upperCertificate upperOK)
  optimal : HasValue six 4
  optimal = record { lower = lowerBound ; upper = upperBound }
