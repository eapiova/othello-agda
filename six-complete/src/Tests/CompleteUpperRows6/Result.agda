{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted untrusted certificate source; safe Agda must check this module.
module Tests.CompleteUpperRows6.Result where
open import Othello.Statements using (Problem2)
import Tests.TextLowerPacked6.Joint as Joint
import Tests.CompleteUpperRows6.AllParts as Upper
import Tests.CompleteLowerRows6.AllParts as Lower
abstract
  initial6x6 : Problem2
  initial6x6 = Joint.complete Lower.checked Upper.checked
-- This source asserts no success receipt: all imported rows must first be checked.
