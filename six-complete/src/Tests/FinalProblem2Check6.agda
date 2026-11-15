{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted final safe checker wrapper.
module Tests.FinalProblem2Check6 where
open import Othello.Statements using (Problem2)
import Tests.CompleteUpperRows6.Result as Result

initial6x6 : Problem2
initial6x6 = Result.initial6x6
