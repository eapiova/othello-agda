{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.BooleanSearch6 where

open import Game.BooleanSearch
open import Game.Core
import Game.Search as Search

private
  successors : ℕ → List ℕ
  successors 2 = 1 ∷ 0 ∷ []
  successors 3 = 0 ∷ 1 ∷ []
  successors 4 = 0 ∷ []
  successors 5 = 0 ∷ 1 ∷ []
  successors _ = []

  isPass : ℕ → Bool
  isPass 4 = true
  isPass _ = false

  tiny : Game ℕ
  tiny = record { turn = λ _ → white ; next = successors ; forcedPass = isPass }

  wins : ℕ → Bool
  wins zero = true
  wins (suc _) = false

-- Own choices may succeed after a failed first child, while opposing
-- choices require every child. A pass consumes one unit of fuel.
positive : forcesB 2 tiny white wins 2 ≡ true
positive = refl

negative : forcesB 2 tiny black wins 3 ≡ false
negative = refl

own-first-success : forcesB 2 tiny white wins 5 ≡ true
own-first-success = refl

opposing-first-failure : forcesB 2 tiny black wins 2 ≡ false
opposing-first-failure = refl

pass-positive : forcesB 2 tiny black wins 4 ≡ true
pass-positive = refl

pass-exhausted : forcesB 1 tiny white wins 4 ≡ false
pass-exhausted = refl

zero-terminal : forcesB 0 tiny white wins 0 ≡ false
zero-terminal = refl

terminal-positive : forcesB 1 tiny white wins 0 ≡ true
terminal-positive = refl

terminal-negative : forcesB 1 tiny white wins 1 ≡ false
terminal-negative = refl

agrees : ∀ fuel p s → forcesB fuel tiny p wins s ≡ Search.forces fuel tiny p wins s
agrees fuel p s = forcesB-eq fuel tiny p wins s
