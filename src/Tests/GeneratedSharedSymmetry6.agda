{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted untrusted fixture; acceptance checked by the safe kernel.
module Tests.GeneratedSharedSymmetry6 where
open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (white; black; Guarantees)
open import Game.Shared using (SharedEntry; acceptSharedBy; acceptSharedBy-sound)
open import Othello.Board using (State; six; initial)
open import Othello.Encode6 using (decodeState)
open import Othello.Shared6 using (keyed6; decodeSharedEntries)
open import Othello.SharedSymmetry6 using (lowerTransport6; upperTransport6)
open import Othello.Statements using (lowerGoal; upperGoal)
import Othello.Fast6 as Fast

position : State six
position = fromMaybe (initial six) (decodeState "b211100221112112112111212221122111112")

lowerEncoded : String
lowerEncoded = "b001112211122211211212111221122211111PC1;F1;Lb211100221112112112111212221122111112R4;"
lowerEntries : List (SharedEntry (State six))
lowerEntries = fromMaybe [] (decodeSharedEntries lowerEncoded)
lowerDecoded : decodeSharedEntries lowerEncoded ≡ just lowerEntries
lowerDecoded = refl
lowerAccepted : acceptSharedBy keyed6 Fast.fastGame6 white (lowerGoal 4) lowerTransport6 lowerEntries position ≡ true
lowerAccepted = refl
lowerGuaranteed : Guarantees Fast.fastGame6 white (lowerGoal 4) position
lowerGuaranteed = acceptSharedBy-sound keyed6 Fast.fastGame6 white (lowerGoal 4) lowerTransport6 lowerEntries position lowerAccepted

upperEncoded : String
upperEncoded = "b001112211122211211212111221122211111PF2;C0;LC0;Lb211100221112112112111212221122111112R4;"
upperEntries : List (SharedEntry (State six))
upperEntries = fromMaybe [] (decodeSharedEntries upperEncoded)
upperDecoded : decodeSharedEntries upperEncoded ≡ just upperEntries
upperDecoded = refl
upperAccepted : acceptSharedBy keyed6 Fast.fastGame6 black (upperGoal 4) upperTransport6 upperEntries position ≡ true
upperAccepted = refl
upperGuaranteed : Guarantees Fast.fastGame6 black (upperGoal 4) position
upperGuaranteed = acceptSharedBy-sound keyed6 Fast.fastGame6 black (upperGoal 4) upperTransport6 upperEntries position upperAccepted

