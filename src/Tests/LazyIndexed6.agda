{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Complete own syntax remains mandatory under lazy data lookup.
module Tests.LazyIndexed6 where

open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (white)
open import Othello.Board using (State; six)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Game.Balanced as B
import Game.NatMap as M
import Othello.Fast6 as Fast
import Othello.Indexed6 as Original
import Othello.LazyIndexed6 as Lazy

module Check = Lazy.Checking Fast.fastGame6 white (lowerGoal 4) lowerTransport6

text : String
text = "wQQQQQQQQQQQQwQQQQQQQQQQQQ"

table : M.Map (State six)
table = M.rows 0 2 (Lazy.states 2 text)

embed : B.Fin 2 → ℕ
embed = B.finToNat

same-valid-vector : Lazy.states 2 text ≡ Original.states 2 text
same-valid-vector = refl

accepted-leaves : Check.checkPart (M.lookup table) embed text "LL" ≡ true
accepted-leaves = refl

accepted-citation : Check.checkPart (M.lookup table) embed text "LK0;" ≡ true
accepted-citation = refl

bad-later-state : Lazy.validStates 2 "wQQQQQQQQQQQQzQQQQQQQQQQQQ" ≡ false
bad-later-state = refl

missing-state : Check.checkPart (M.lookup table) embed "wQQQQQQQQQQQQ" "LL" ≡ false
missing-state = refl

extra-state : Check.checkPart (M.lookup table) embed "wQQQQQQQQQQQQwQQQQQQQQQQQQwQQQQQQQQQQQQ" "LL" ≡ false
extra-state = refl

malformed-own-state : Check.checkPart (M.lookup table) embed "wQQQQQQQQQQQQwQQQQQQQQQQQZ" "LL" ≡ false
malformed-own-state = refl

missing-body : Check.checkPart (M.lookup table) embed text "L" ≡ false
missing-body = refl

self-citation : Check.checkPart (M.lookup table) embed text "K0;L" ≡ false
self-citation = refl

future-citation : Check.checkPart (M.lookup table) embed text "K1;L" ≡ false
future-citation = refl

missing-citation : Check.checkPart (M.lookup table) embed text "LK2;" ≡ false
missing-citation = refl
