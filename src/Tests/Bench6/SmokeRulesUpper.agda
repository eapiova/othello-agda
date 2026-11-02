{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted generation. Exactly one independent kernel solve fact.
module Tests.Bench6.SmokeRulesUpper where

open import Prelude
open import Game.Core using (white; black)
open import Game.Search using (forces)
open import Othello.Board using (State; six; initial)
open import Othello.Encode6 using (decodeState)
open import Tests.Bench6.Goals
import Othello.Rules as Rules
import Othello.Fast6 as Fast

position : State six
position = fromMaybe (initial six) (decodeState "b111111111111111111111111111111111110")

decoded : decodeState "b111111111111111111111111111111111110" ≡ just position
decoded = refl

accepted : forces 80 (Rules.game six) black (upperGoal (neg 35)) position ≡ true
accepted = refl
