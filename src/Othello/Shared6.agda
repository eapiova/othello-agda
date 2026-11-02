{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Keys and fail-closed decoders for layered 6×6 certificates.
-- Keys only route trie lookups; citations are confirmed by eqState-sound.
module Othello.Shared6 where

open import Prelude
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Char using (Char; primCharEquality)
open import Agda.Builtin.Nat using (_*_; _+_)
open import Othello.Board
open import Othello.Order using (_≤ᵇ_)
import Othello.Finite as V
open import Othello.Encode6 using (stateEquality6; readState)
open import Game.Shared

cellBits : Cell → List Bool → List Bool
cellBits empty rest = false ∷ false ∷ rest
cellBits blackCell rest = false ∷ true ∷ rest
cellBits whiteCell rest = true ∷ false ∷ rest

rowBits : ∀ {n} → V.Vec Cell n → List Bool → List Bool
rowBits V.[] rest = rest
rowBits (c V.∷ cs) rest = cellBits c (rowBits cs rest)

boardBits : ∀ {n m} → V.Vec (V.Vec Cell m) n → List Bool
boardBits V.[] = []
boardBits (r V.∷ rs) = rowBits r (boardBits rs)

playerBit : Player → Bool
playerBit black = false
playerBit white = true

key6 : State six → List Bool
key6 (state b p) = playerBit p ∷ boardBits b

keyed6 : Keyed (State six)
keyed6 = keyed key6 stateEquality6

private
  digit : Char → Maybe ℕ
  digit c = go 0 ('0' ∷ '1' ∷ '2' ∷ '3' ∷ '4' ∷ '5' ∷ '6' ∷ '7' ∷ '8' ∷ '9' ∷ [])
    where
    go : ℕ → List Char → Maybe ℕ
    go n [] = nothing
    go n (d ∷ ds) with primCharEquality c d
    ... | true = just n
    ... | false = go (suc n) ds

  numberTail : ℕ → Bool → List Char → Maybe (ℕ × List Char)
  numberTail n seen [] = nothing
  numberTail n seen (c ∷ cs) with primCharEquality c ';'
  ... | true with seen
  ... | true = just (n , cs)
  ... | false = nothing
  numberTail n seen (c ∷ cs) | false with digit c
  ... | nothing = nothing
  ... | just d with (10 * n + d) ≤ᵇ 128
  ... | false = nothing
  ... | true = numberTail (10 * n + d) true cs

  readNumber : List Char → Maybe (ℕ × List Char)
  readNumber = numberTail 0 false

  length : ∀ {A : Set} → List A → ℕ
  length [] = 0
  length (_ ∷ xs) = suc (length xs)

-- Tokens: L leaf, Sn; solve, Pc pass, Cn;c choice, Fn;c… fork, K exact-state known, Rn; symmetry reference (0–7).
mutual
  readShared : ℕ → List Char → Maybe (SharedCertificate × List Char)
  readShared zero cs = nothing
  readShared (suc fuel) [] = nothing
  readShared (suc fuel) (c ∷ cs) with primCharEquality c 'L'
  ... | true = just (sharedLeaf , cs)
  ... | false with primCharEquality c 'K'
  ... | true = just (known , cs)
  ... | false with primCharEquality c 'S'
  ... | true with readNumber cs
  ... | nothing = nothing
  ... | just (n , tail) = just (sharedSolve n , tail)
  readShared (suc fuel) (c ∷ cs) | false | false | false with primCharEquality c 'P'
  ... | true with readShared fuel cs
  ... | nothing = nothing
  ... | just (x , tail) = just (sharedPass x , tail)
  readShared (suc fuel) (c ∷ cs) | false | false | false | false with primCharEquality c 'C'
  ... | true with readNumber cs
  ... | nothing = nothing
  ... | just (n , rest) with readShared fuel rest
  ... | nothing = nothing
  ... | just (x , tail) = just (sharedChoice n x , tail)
  readShared (suc fuel) (c ∷ cs) | false | false | false | false | false with primCharEquality c 'F'
  ... | false with primCharEquality c 'R'
  ... | false = nothing
  ... | true with readNumber cs
  ... | nothing = nothing
  ... | just (n , tail) with n ≤ᵇ 7
  ... | false = nothing
  ... | true = just (knownBy n , tail)
  readShared (suc fuel) (c ∷ cs) | false | false | false | false | false | true with readNumber cs
  ... | nothing = nothing
  ... | just (n , rest) with readShareds fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (sharedFork xs , tail)

  readShareds : ℕ → ℕ → List Char → Maybe (List SharedCertificate × List Char)
  readShareds fuel zero cs = just ([] , cs)
  readShareds zero (suc n) cs = nothing
  readShareds (suc fuel) (suc n) cs with readShared fuel cs
  ... | nothing = nothing
  ... | just (x , rest) with readShareds fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (x ∷ xs , tail)

readSharedEntries : ℕ → List Char → Maybe (List (SharedEntry (State six)))
readSharedEntries fuel [] = just []
readSharedEntries zero (_ ∷ _) = nothing
readSharedEntries (suc fuel) cs@(_ ∷ _) with readState cs
... | nothing = nothing
... | just (s , rest) with readShared fuel rest
... | nothing = nothing
... | just (c , tail) with readSharedEntries fuel tail
... | nothing = nothing
... | just xs = just (sharedEntry s c ∷ xs)

-- Entries are concatenated as state-then-certificate, in citation order.
decodeSharedEntries : String → Maybe (List (SharedEntry (State six)))
decodeSharedEntries text = readSharedEntries (suc (2 * length chars)) chars
  where chars = primStringToList text
