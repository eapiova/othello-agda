{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Proof6 where

open import Prelude
open import Agda.Builtin.Nat renaming (_==_ to _≡ᵇ_)
open import Game.Core
open import Game.Certificate using (certificateStrategy)
open import Game.Composite
open import Game.Joint
open import Game.Transfer
open import Othello.Board
open import Othello.Rules using (game)
open import Othello.Fast6
open import Othello.Encode6 using (stateEquality6)
open import Othello.Statements

fastAgreement : Agreement fastGame6 (game six)
fastAgreement = agreement next6-correct turn6-correct forcedPass6-correct

terminalCounts : State six → Bool
terminalCounts s = (discs black s ≡ᵇ 16) ∧ (discs white s ≡ᵇ 20)

private
  natEquality-sound : ∀ n m → (n ≡ᵇ m) ≡ true → n ≡ m
  natEquality-sound zero zero e = refl
  natEquality-sound zero (suc m) ()
  natEquality-sound (suc n) zero ()
  natEquality-sound (suc n) (suc m) e = cong suc (natEquality-sound n m e)
  left : ∀ a b → a ∧ b ≡ true → a ≡ true
  left true b e = refl
  left false b ()
  right : ∀ a b → a ∧ b ≡ true → b ≡ true
  right true b e = e
  right false b ()

counts-sound : ∀ s → terminalCounts s ≡ true →
  (discs black s ≡ 16) × (discs white s ≡ 20)
counts-sound s e =
  natEquality-sound (discs black s) 16 (left _ _ e) ,
  natEquality-sound (discs white s) 20 (right _ _ e)

strategy6 : Shards (State six) → Player → (State six → Bool) → Skeleton → Strategy (State six)
strategy6 tables p goal skeleton = certificateStrategy
  (flatten tables fastGame6 p goal (initial six) skeleton)

-- Conditional assembly is safe: the arguments are kernel-checking obligations,
-- not external oracle assumptions. This module declares no global solution.
problem2-from : (lowerTables upperTables : Shards (State six)) →
  (lowerSkeleton upperSkeleton : Skeleton) → (path : List (State six)) →
  itemsOK fastGame6 white (lowerGoal 4) lowerTables ≡ true →
  itemsOK fastGame6 black (upperGoal 4) upperTables ≡ true →
  checkComposite stateEquality6 lowerTables fastGame6 white (lowerGoal 4)
    (initial six) lowerSkeleton ≡ true →
  checkComposite stateEquality6 upperTables fastGame6 black (upperGoal 4)
    (initial six) upperSkeleton ≡ true →
  jointCheck stateEquality6 fastGame6 terminalCounts (initial six)
    (strategy6 lowerTables white (lowerGoal 4) lowerSkeleton)
    (strategy6 upperTables black (upperGoal 4) upperSkeleton) path ≡ true →
  Problem2
problem2-from lowerTables upperTables lowerSkeleton upperSkeleton path
  lowerOK upperOK lowerRoot upperRoot jointOK with
  joint-sound stateEquality6 fastGame6 terminalCounts (initial six)
    (strategy6 lowerTables white (lowerGoal 4) lowerSkeleton)
    (strategy6 upperTables black (upperGoal 4) upperSkeleton) path jointOK
... | t , play , countOK = optimal , t ,
  completedPlay-transfer fastGame6 (game six) fastAgreement play , counts-sound t countOK
  where
  lowerBound = guarantees-transfer fastGame6 (game six) fastAgreement
    (compositionSound stateEquality6 lowerTables fastGame6 white (lowerGoal 4)
      (initial six) lowerSkeleton lowerOK lowerRoot)
  upperBound = guarantees-transfer fastGame6 (game six) fastAgreement
    (compositionSound stateEquality6 upperTables fastGame6 black (upperGoal 4)
      (initial six) upperSkeleton upperOK upperRoot)
  optimal : HasValue six 4
  optimal = record { lower = lowerBound ; upper = upperBound }
