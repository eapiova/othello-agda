{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.Compiled6 where

open import Prelude
open import Agda.Builtin.String using (String)
open import Othello.Board using (State; six; discs; black; white)
open import Othello.Order using (_+_; _≤ᵇ_)
open import Othello.Fast6 using (fastGame6)
open import Othello.Encode6 using (decodeState; decodeShard)
open import Game.Search using (forces)
open import Game.Composite using (shardOK)

-- lower=true asks White to force raw score >= threshold; otherwise Black
-- forces raw score <= threshold. The signed threshold is (negative,magnitude).
-- This representation avoids a foreign integer constructor at the API boundary.
rawGoal : Bool → Bool → ℕ → State six → Bool
rawGoal true false n s = (discs black s + n) ≤ᵇ discs white s
rawGoal false false n s = discs white s ≤ᵇ (discs black s + n)
rawGoal true true n s = discs black s ≤ᵇ (discs white s + n)
rawGoal false true n s = (discs white s + n) ≤ᵇ discs black s

search80 : String → Bool → Bool → ℕ → Bool
search80 text lower negative magnitude with decodeState text
... | nothing = false
... | just s with lower
... | true = forces 80 fastGame6 white (rawGoal true negative magnitude) s
... | false = forces 80 fastGame6 black (rawGoal false negative magnitude) s

-- Decode every entry, then check every closed certificate through Composite.
-- Empty shards are valid (vacuous); this does not claim a root guarantee.
shardAccepted : String → Bool → Bool → ℕ → Bool
shardAccepted text lower negative magnitude with decodeShard text
... | nothing = false
... | just entries with lower
... | true = shardOK fastGame6 white (rawGoal true negative magnitude) entries
... | false = shardOK fastGame6 black (rawGoal false negative magnitude) entries

corrupt-state : search80 "x" true false 4 ≡ false
corrupt-state = refl

corrupt-shard : shardAccepted "b000" true false 4 ≡ false
corrupt-shard = refl
