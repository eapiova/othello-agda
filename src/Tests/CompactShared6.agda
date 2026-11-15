{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Compact wire tested against existing generated kernel fixtures.
module Tests.CompactShared6 where

open import Prelude
open import Agda.Builtin.Char using (Char)
open import Agda.Builtin.String using (String; primStringToList)
open import Game.Core using (white; black)
open import Game.Shared using (SharedEntry; acceptSharedBy; sharedChoice; sharedLeaf; sharedSolve)
open import Othello.Board using (State; Cell; six)
open import Othello.Encode6 using (decodeState; decodeVec; readCell)
open import Othello.Shared6 using (keyed6; decodeSharedEntries)
open import Othello.CompactShared6
open import Othello.SharedSymmetry6 using (lowerTransport6; upperTransport6)
open import Othello.Statements using (lowerGoal; upperGoal)
import Othello.Finite as V
import Othello.Fast6 as Fast
import Tests.GeneratedSharedSymmetry6 as Fixture

private
  plainTriple : String → Maybe (V.Vec Cell 3)
  plainTriple text with decodeVec 3 readCell (primStringToList text)
  ... | just (cells , []) = just cells
  ... | _ = nothing

  ternaryTriples : List String
  ternaryTriples = "000" ∷ "001" ∷ "002" ∷ "010" ∷ "011" ∷ "012" ∷ "020" ∷ "021" ∷ "022" ∷ "100" ∷ "101" ∷ "102" ∷ "110" ∷ "111" ∷ "112" ∷ "120" ∷ "121" ∷ "122" ∷ "200" ∷ "201" ∷ "202" ∷ "210" ∷ "211" ∷ "212" ∷ "220" ∷ "221" ∷ "222" ∷ []

all-triples-decoded :
  map decodeCompactTriple (primStringToList "0123456789ABCDEFGHIJKLMNOPQ") ≡
  map plainTriple ternaryTriples
all-triples-decoded = refl

compact-player-and-board :
  decodeCompactState "bM9PEEEDNPHDE" ≡ just Fixture.position
compact-player-and-board = refl

white-player-and-board :
  decodeCompactState "w000000000000" ≡ decodeState "w000000000000000000000000000000000000"
white-player-and-board = refl

-- The old fixture is imported once; only its compact representation is new.
lowerWire upperWire : String
lowerWire = "b1EMHMMNDPHMDPC1F1LbM9PEEEDNPHDER4"
upperWire = "b1EMHMMNDPHMDPF2C0LC0LbM9PEEEDNPHDER4"

lowerEntries upperEntries : List (SharedEntry (State six))
lowerEntries = fromMaybe [] (decodeCompactEntries lowerWire)
upperEntries = fromMaybe [] (decodeCompactEntries upperWire)

lower-decoded-equal :
  decodeCompactEntries lowerWire ≡ decodeSharedEntries Fixture.lowerEncoded
lower-decoded-equal = refl

upper-decoded-equal :
  decodeCompactEntries upperWire ≡ decodeSharedEntries Fixture.upperEncoded
upper-decoded-equal = refl

lower-shared-equivalent :
  acceptSharedBy keyed6 Fast.fastGame6 white (lowerGoal 4) lowerTransport6 lowerEntries Fixture.position ≡
  acceptSharedBy keyed6 Fast.fastGame6 white (lowerGoal 4) lowerTransport6 Fixture.lowerEntries Fixture.position
lower-shared-equivalent = refl

upper-shared-equivalent :
  acceptSharedBy keyed6 Fast.fastGame6 black (upperGoal 4) upperTransport6 upperEntries Fixture.position ≡
  acceptSharedBy keyed6 Fast.fastGame6 black (upperGoal 4) upperTransport6 Fixture.upperEntries Fixture.position
upper-shared-equivalent = refl

lower-accepted :
  acceptSharedBy keyed6 Fast.fastGame6 white (lowerGoal 4) lowerTransport6 lowerEntries Fixture.position ≡ true
lower-accepted = refl

upper-accepted :
  acceptSharedBy keyed6 Fast.fastGame6 black (upperGoal 4) upperTransport6 upperEntries Fixture.position ≡ true
upper-accepted = refl

missing-reference-rejected :
  acceptSharedBy keyed6 Fast.fastGame6 white (lowerGoal 4) lowerTransport6
    (fromMaybe [] (decodeCompactEntries "bM9PEEEDNPHDER4")) Fixture.position ≡ false
missing-reference-rejected = refl

private
  malformedStates : List String
  malformedStates = "" ∷ "b00000000000" ∷ "b0000000000000" ∷
    "x000000000000" ∷ "bR00000000000" ∷ "b_00000000000" ∷ []

invalid-short-extra-states :
  map decodeCompactState malformedStates ≡
  nothing ∷ nothing ∷ nothing ∷ nothing ∷ nothing ∷ nothing ∷ []
invalid-short-extra-states = refl

private
  malformedEntries : List String
  malformedEntries =
    "b000000000000X" ∷ "b000000000000P" ∷
    "b000000000000R8" ∷ "b000000000000R1;" ∷
    "b000000000000C_L" ∷ "b000000000000C0" ∷
    "b000000000000F2L" ∷ "b000000000000Fa" ∷
    "b000000000000S129;" ∷ "b000000000000S;" ∷
    "b000000000000S1" ∷ "b000000000000Lx" ∷
    "b000000000000Lb00000000000L" ∷ []

malformed-certificates-and-entries :
  map decodeCompactEntries malformedEntries ≡
  nothing ∷ nothing ∷ nothing ∷ nothing ∷ nothing ∷ nothing ∷
  nothing ∷ nothing ∷ nothing ∷ nothing ∷ nothing ∷ nothing ∷ nothing ∷ []
malformed-certificates-and-entries = refl

empty-shard : decodeCompactEntries "" ≡ just []
empty-shard = refl

zero-fuel-rejected : readCompactShared 0 (primStringToList "L") ≡ nothing
zero-fuel-rejected = refl

boundary-choice :
  readCompactShared 4 (primStringToList "CZL") ≡
  just (sharedChoice 35 sharedLeaf , [])
boundary-choice = refl

boundary-solve :
  readCompactShared 4 (primStringToList "S128;") ≡
  just (sharedSolve 128 , [])
boundary-solve = refl
