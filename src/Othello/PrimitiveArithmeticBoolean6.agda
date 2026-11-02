{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted Boolean-only instrumentation. This module supplies no
-- soundness theorem, no Proven value, and no theorem about the initial state.
module Othello.PrimitiveArithmeticBoolean6 where

open import Prelude
open import Game.Core using (Game; white; samePlayer; turn; next; forcedPass; lookup)
open import Game.BooleanSearch using (forcesB)
open import Game.DirectedIndexed using (DirectedCertificate; indexedLeaf; indexedSolve;
  indexedChoice; indexedFork; indexedPass; cite; citeBy; indexedPick)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatOrder as N
open import Othello.Board using (Coord; six)
open import Othello.Rules using (coords)
open import Othello.Statements using (lowerGoal)
import Othello.DirectSymmetry6 as Direct
import Othello.PrimitiveArithmeticState6 as New
import Othello.RowPacked6 as P
import Othello.Symmetry6 as Symmetry

Key : Set
Key = ℕ

Move : Set
Move = Coord six

State : Set
State = P.PackedState

Resolver : Set
Resolver = Key → Maybe State

-- Coordinates retain the standard row-major order used by the source game.
rawMovesFrom : State → List Move → List State
rawMovesFrom s [] = []
rawMovesFrom s (q ∷ qs) with New.pickRaw s q
... | nothing = rawMovesFrom s qs
... | just t = t ∷ rawMovesFrom s qs

rawMoves : State → List State
rawMoves s = rawMovesFrom s (coords six)

nextRaw : State → List State
nextRaw s with rawMoves s
... | x ∷ xs = x ∷ xs
... | [] with rawMoves (New.switchRaw s)
...   | [] = []
...   | x ∷ xs = New.switchRaw s ∷ []

forcedPassRaw : State → Bool
forcedPassRaw s with rawMoves s | rawMoves (New.switchRaw s)
... | [] | [] = false
... | [] | x ∷ xs = true
... | x ∷ xs | opposing = false

game : Game State
game = record
  { turn = P.whose
  ; next = nextRaw
  ; forcedPass = forcedPassRaw
  }

lowerGoal4 : State → Bool
lowerGoal4 s = lowerGoal 4 (P.decode s)

tagAction : ℕ → State → State
tagAction tag s = P.encode (Direct.transformTag tag (P.decode s))

-- This evaluator intentionally has no semantic bridge to the source game.
-- A result of true is only a Boolean measurement of the supplied rows.
mutual
  checkLocal : Resolver → Key → State → DirectedCertificate Key Move → Bool
  checkLocal L owner s indexedLeaf with next game s
  ... | [] = lowerGoal4 s
  ... | x ∷ xs = false
  checkLocal L owner s (indexedSolve fuel) = forcesB fuel game white lowerGoal4 s
  checkLocal L owner s (indexedChoice i c)
    with next game s | samePlayer (turn game s) white
  ... | [] | own = false
  ... | x ∷ xs | false = false
  ... | x ∷ xs | true with lookup (x ∷ xs) i
  ...   | nothing = false
  ...   | just t = checkLocal L owner t c
  checkLocal L owner s (indexedFork cs)
    with next game s | samePlayer (turn game s) white
  ... | [] | own = false
  ... | x ∷ xs | true = false
  ... | x ∷ xs | false = checkLocalForest L owner (x ∷ xs) cs
  checkLocal L owner s (indexedPass c) with next game s | forcedPass game s
  ... | [] | b = false
  ... | x ∷ [] | false = false
  ... | x ∷ y ∷ xs | b = false
  ... | x ∷ [] | true = checkLocal L owner x c
  checkLocal L owner s (cite j) with I.beforeB N.order j owner
  ... | false = false
  ... | true with L j
  ...   | nothing = false
  ...   | just u = P.equal s u
  checkLocal L owner s (citeBy tag j) with I.beforeB N.order j owner
  ... | false = false
  ... | true with Symmetry.acceptedTag8 tag
  ...   | false = false
  ...   | true with L j
  ...     | nothing = false
  ...     | just u = P.equal (tagAction tag s) u
  checkLocal L owner s (indexedPick q c)
    with samePlayer (turn game s) white | New.pickRaw s q
  ... | false | result = false
  ... | true | nothing = false
  ... | true | just t = checkLocal L owner t c

  checkLocalForest : Resolver → Key → List State →
    List (DirectedCertificate Key Move) → Bool
  checkLocalForest L owner [] [] = true
  checkLocalForest L owner [] (c ∷ cs) = false
  checkLocalForest L owner (s ∷ ss) [] = false
  checkLocalForest L owner (s ∷ ss) (c ∷ cs) =
    checkLocal L owner s c ∧ checkLocalForest L owner ss cs

checkRows : ∀ {n} → Resolver → (B.Fin n → Key) → B.Vec State n →
  B.Vec (DirectedCertificate Key Move) n → Bool
checkRows L embed B.nil B.nil = true
checkRows L embed (B.cons s ss) (B.cons c cs) =
  checkLocal L (embed B.fzero) s c ∧
  checkRows L (λ i → embed (B.fsuc i)) ss cs
