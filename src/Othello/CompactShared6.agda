{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Compact, fail-closed wire decoding for shared 6×6 entries.
-- Decoded data remains untrusted and is checked by Game.Shared.checkShardBy.
module Othello.CompactShared6 where

open import Prelude
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Char using (Char; primCharEquality)
open import Agda.Builtin.Nat using (_*_; _+_)
open import Othello.Board
open import Othello.Order using (_≤ᵇ_)
open import Othello.Encode6 using (readPlayer; decodeVec)
open import Game.Shared using (SharedCertificate; sharedLeaf; sharedSolve;
  sharedPass; sharedChoice; sharedFork; known; knownBy; SharedEntry; sharedEntry)
import Othello.Finite as V

private
  rank : Char → List Char → Maybe ℕ
  rank c = go 0
    where
    go : ℕ → List Char → Maybe ℕ
    go n [] = nothing
    go n (d ∷ ds) with primCharEquality c d
    ... | true = just n
    ... | false = go (suc n) ds

  lookup : ∀ {A : Set} → List A → ℕ → Maybe A
  lookup [] n = nothing
  lookup (x ∷ xs) zero = just x
  lookup (x ∷ xs) (suc n) = lookup xs n

  triples : List (V.Vec Cell 3)
  triples =
    (empty V.∷ empty V.∷ empty V.∷ V.[]) ∷
    (empty V.∷ empty V.∷ blackCell V.∷ V.[]) ∷
    (empty V.∷ empty V.∷ whiteCell V.∷ V.[]) ∷
    (empty V.∷ blackCell V.∷ empty V.∷ V.[]) ∷
    (empty V.∷ blackCell V.∷ blackCell V.∷ V.[]) ∷
    (empty V.∷ blackCell V.∷ whiteCell V.∷ V.[]) ∷
    (empty V.∷ whiteCell V.∷ empty V.∷ V.[]) ∷
    (empty V.∷ whiteCell V.∷ blackCell V.∷ V.[]) ∷
    (empty V.∷ whiteCell V.∷ whiteCell V.∷ V.[]) ∷
    (blackCell V.∷ empty V.∷ empty V.∷ V.[]) ∷
    (blackCell V.∷ empty V.∷ blackCell V.∷ V.[]) ∷
    (blackCell V.∷ empty V.∷ whiteCell V.∷ V.[]) ∷
    (blackCell V.∷ blackCell V.∷ empty V.∷ V.[]) ∷
    (blackCell V.∷ blackCell V.∷ blackCell V.∷ V.[]) ∷
    (blackCell V.∷ blackCell V.∷ whiteCell V.∷ V.[]) ∷
    (blackCell V.∷ whiteCell V.∷ empty V.∷ V.[]) ∷
    (blackCell V.∷ whiteCell V.∷ blackCell V.∷ V.[]) ∷
    (blackCell V.∷ whiteCell V.∷ whiteCell V.∷ V.[]) ∷
    (whiteCell V.∷ empty V.∷ empty V.∷ V.[]) ∷
    (whiteCell V.∷ empty V.∷ blackCell V.∷ V.[]) ∷
    (whiteCell V.∷ empty V.∷ whiteCell V.∷ V.[]) ∷
    (whiteCell V.∷ blackCell V.∷ empty V.∷ V.[]) ∷
    (whiteCell V.∷ blackCell V.∷ blackCell V.∷ V.[]) ∷
    (whiteCell V.∷ blackCell V.∷ whiteCell V.∷ V.[]) ∷
    (whiteCell V.∷ whiteCell V.∷ empty V.∷ V.[]) ∷
    (whiteCell V.∷ whiteCell V.∷ blackCell V.∷ V.[]) ∷
    (whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ V.[]) ∷
    []

-- Triple a,b,c has rank 9*a+3*b+c in the 27-character alphabet.
decodeCompactTriple : Char → Maybe (V.Vec Cell 3)
decodeCompactTriple c with rank c (primStringToList "0123456789ABCDEFGHIJKLMNOPQ")
... | nothing = nothing
... | just n = lookup triples n

private
  readTriple : List Char → Maybe (V.Vec Cell 3 × List Char)
  readTriple [] = nothing
  readTriple (c ∷ cs) with decodeCompactTriple c
  ... | nothing = nothing
  ... | just t = just (t , cs)

  readRow : List Char → Maybe (V.Vec Cell 6 × List Char)
  readRow cs with readTriple cs
  ... | nothing = nothing
  ... | just (a V.∷ b V.∷ c V.∷ V.[] , rest) with readTriple rest
  ... | nothing = nothing
  ... | just (d V.∷ e V.∷ f V.∷ V.[] , tail) =
    just (a V.∷ b V.∷ c V.∷ d V.∷ e V.∷ f V.∷ V.[] , tail)

readCompactState : List Char → Maybe (State six × List Char)
readCompactState [] = nothing
readCompactState (c ∷ cs) with readPlayer c | decodeVec 6 readRow cs
... | just p | just (b , rest) = just (state b p , rest)
... | _ | _ = nothing

decodeCompactState : String → Maybe (State six)
decodeCompactState text with readCompactState (primStringToList text)
... | just (s , []) = just s
... | _ = nothing

private
  digit : Char → Maybe ℕ
  digit c = rank c (primStringToList "0123456789")

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

  readBounded : ℕ → List Char → List Char → Maybe (ℕ × List Char)
  readBounded bound alphabet [] = nothing
  readBounded bound alphabet (c ∷ cs) with rank c alphabet
  ... | nothing = nothing
  ... | just n with n ≤ᵇ bound
  ... | false = nothing
  ... | true = just (n , cs)

  counts : List Char
  counts = primStringToList "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_"

  length : ∀ {A : Set} → List A → ℕ
  length [] = 0
  length (_ ∷ xs) = suc (length xs)

-- Tokens: L/K/P unchanged, R[0..7], C[0..35], F[0..36], S[0..128];.
-- Fuel bounds every certificate and entry recursion; unknown data fails closed.
mutual
  readCompactShared : ℕ → List Char → Maybe (SharedCertificate × List Char)
  readCompactShared zero cs = nothing
  readCompactShared (suc fuel) [] = nothing
  readCompactShared (suc fuel) (c ∷ cs) with primCharEquality c 'L'
  ... | true = just (sharedLeaf , cs)
  ... | false with primCharEquality c 'K'
  ... | true = just (known , cs)
  ... | false with primCharEquality c 'S'
  ... | true with readNumber cs
  ... | nothing = nothing
  ... | just (n , tail) = just (sharedSolve n , tail)
  readCompactShared (suc fuel) (c ∷ cs) | false | false | false with primCharEquality c 'P'
  ... | true with readCompactShared fuel cs
  ... | nothing = nothing
  ... | just (x , tail) = just (sharedPass x , tail)
  readCompactShared (suc fuel) (c ∷ cs) | false | false | false | false with primCharEquality c 'C'
  ... | true with readBounded 35 counts cs
  ... | nothing = nothing
  ... | just (n , rest) with readCompactShared fuel rest
  ... | nothing = nothing
  ... | just (x , tail) = just (sharedChoice n x , tail)
  readCompactShared (suc fuel) (c ∷ cs) | false | false | false | false | false with primCharEquality c 'F'
  ... | false with primCharEquality c 'R'
  ... | false = nothing
  ... | true with readBounded 7 (primStringToList "01234567") cs
  ... | nothing = nothing
  ... | just (n , tail) = just (knownBy n , tail)
  readCompactShared (suc fuel) (c ∷ cs) | false | false | false | false | false | true with readBounded 36 counts cs
  ... | nothing = nothing
  ... | just (n , rest) with readCompactShareds fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (sharedFork xs , tail)

  readCompactShareds : ℕ → ℕ → List Char → Maybe (List SharedCertificate × List Char)
  readCompactShareds fuel zero cs = just ([] , cs)
  readCompactShareds zero (suc n) cs = nothing
  readCompactShareds (suc fuel) (suc n) cs with readCompactShared fuel cs
  ... | nothing = nothing
  ... | just (x , rest) with readCompactShareds fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (x ∷ xs , tail)

readCompactSharedEntries : ℕ → List Char → Maybe (List (SharedEntry (State six)))
readCompactSharedEntries fuel [] = just []
readCompactSharedEntries zero (_ ∷ _) = nothing
readCompactSharedEntries (suc fuel) cs@(_ ∷ _) with readCompactState cs
... | nothing = nothing
... | just (s , rest) with readCompactShared fuel rest
... | nothing = nothing
... | just (c , tail) with readCompactSharedEntries fuel tail
... | nothing = nothing
... | just xs = just (sharedEntry s c ∷ xs)

decodeCompactEntries : String → Maybe (List (SharedEntry (State six)))
decodeCompactEntries text = readCompactSharedEntries (suc (2 * length chars)) chars
  where chars = primStringToList text

