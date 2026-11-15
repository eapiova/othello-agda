{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- Each shard is checked independently; no native oracle is imported.
module Othello.Proof6.Upper0 where

open import Prelude
open import Game.Core using (black)
open import Game.Composite using (Entry; shardOK)
open import Othello.Board using (State; six)
open import Othello.Encode6 using (decodeShard)
open import Othello.Fast6 using (fastGame6)
open import Othello.Statements using (upperGoal)
open import Othello.Data6.Upper0 using (encoded)

entries : List (Entry (State six))
entries = fromMaybe [] (decodeShard encoded)

decoded : decodeShard encoded ≡ just entries
decoded = refl

abstract
  accepted : shardOK fastGame6 black (upperGoal 4) entries ≡ true
  accepted = refl
