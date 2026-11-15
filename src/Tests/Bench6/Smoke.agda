{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.Bench6.Smoke where
open import Prelude
open import Tests.Bench6.Goals
open import Tests.Bench6.SmokeRulesLower using (position)
import Tests.Bench6.SmokeRulesUpper
import Tests.Bench6.SmokeFastLower
import Tests.Bench6.SmokeFastUpper

negative-too-high : lowerGoal (neg 34) position ≡ false
negative-too-high = refl
negative-too-low : upperGoal (neg 36) position ≡ false
negative-too-low = refl
zero-too-high : lowerGoal (pos 0) position ≡ false
zero-too-high = refl
positive-upper : upperGoal (pos 4) position ≡ true
positive-upper = refl
