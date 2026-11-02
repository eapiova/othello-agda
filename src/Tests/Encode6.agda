{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.Encode6 where
open import Prelude
open import Othello.Encode6
open import Othello.Board
open import Game.Composite

bad-turn : decodeState "x000000000000000000000000000000000000" ≡ nothing
bad-turn = refl
bad-cell : decodeState "b00000000000000000000000000000000000x" ≡ nothing
bad-cell = refl
short-board : decodeState "b000" ≡ nothing
short-board = refl
trailing-state : decodeState "b000000000000000000000000000000000000x" ≡ nothing
trailing-state = refl
empty-number : decodeLocal "S;" ≡ nothing
empty-number = refl
oversized-number : decodeLocal "S129;" ≡ nothing
oversized-number = refl
trailing-certificate : decodeLocal "LL" ≡ nothing
trailing-certificate = refl
short-fork : decodeLocal "F2;L" ≡ nothing
short-fork = refl
unknown-constructor : decodeLocal "X" ≡ nothing
unknown-constructor = refl
read-solve : decodeLocal "S80;" ≡ just (solve 80)
read-solve = refl
read-choice-pass : decodeLocal "C0;PL" ≡ just (localChoice 0 (localPass localLeaf))
read-choice-pass = refl
read-fork : decodeLocal "F2;LL" ≡ just (localFork (localLeaf ∷ localLeaf ∷ []))
read-fork = refl
bad-shard : decodeShard "b000" ≡ nothing
bad-shard = refl
