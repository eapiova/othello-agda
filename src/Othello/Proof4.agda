{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Proof4 where

open import Prelude
open import Game.Core
open import Game.Certificate using (check)
open import Game.Soundness using (checkSound)
open import Othello.Board
open import Othello.Rules using (game)
open import Othello.Statements
open import Othello.Generated4

-- Each refl invokes Agda's evaluator on the supplied data and executable rules.
-- Neither equality is assumed from the external searcher's result.
lowerAccepted :
  check (game four) white (lowerGoal 8) (initial four) lowerCertificate ≡ true
lowerAccepted = refl

upperAccepted :
  check (game four) black (upperGoal 8) (initial four) upperCertificate ≡ true
upperAccepted = refl

lower4 : WhiteGuarantees (game four) (lowerGoal 8) (initial four)
lower4 = checkSound (game four) white (lowerGoal 8) (initial four)
                   lowerCertificate lowerAccepted

upper4 : BlackGuarantees (game four) (upperGoal 8) (initial four)
upper4 = checkSound (game four) black (upperGoal 8) (initial four)
                   upperCertificate upperAccepted

value4 : HasValue four 8
value4 = record { lower = lower4 ; upper = upper4 }

problem1 : Problem1
problem1 = lower-eight-wins lower4
