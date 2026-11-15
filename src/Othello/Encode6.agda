{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Encode6 where

open import Prelude
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Char using (Char; primCharEquality)
open import Agda.Builtin.Nat using (_+_; _*_)
open import Othello.Board
open import Othello.Order using (_≤ᵇ_)
import Othello.Finite as V
open import Game.Composite using (StateEquality; stateEquality; LocalCertificate;
  localLeaf; solve; localChoice; localFork; localPass; Entry; entry)

private
  left : ∀ a b → a ∧ b ≡ true → a ≡ true
  left true b e = refl
  left false b ()
  right : ∀ a b → a ∧ b ≡ true → b ≡ true
  right true b e = e
  right false b ()
  cong₂ : ∀ {A B C : Set} (f : A → B → C) {a a′ b b′} →
    a ≡ a′ → b ≡ b′ → f a b ≡ f a′ b′
  cong₂ f refl refl = refl

sameVec : ∀ {A n} → (A → A → Bool) → V.Vec A n → V.Vec A n → Bool
sameVec eq V.[] V.[] = true
sameVec eq (x V.∷ xs) (y V.∷ ys) = eq x y ∧ sameVec eq xs ys

sameVec-sound : ∀ {A n} (eq : A → A → Bool) →
  (∀ x y → eq x y ≡ true → x ≡ y) → (xs ys : V.Vec A n) →
  sameVec eq xs ys ≡ true → xs ≡ ys
sameVec-sound eq sound V.[] V.[] e = refl
sameVec-sound eq sound (x V.∷ xs) (y V.∷ ys) e = cong₂ V._∷_
  (sound x y (left (eq x y) (sameVec eq xs ys) e))
  (sameVec-sound eq sound xs ys (right (eq x y) (sameVec eq xs ys) e))

sameCell-sound : ∀ x y → sameCell x y ≡ true → x ≡ y
sameCell-sound empty empty e = refl
sameCell-sound blackCell blackCell e = refl
sameCell-sound whiteCell whiteCell e = refl
sameCell-sound empty blackCell ()
sameCell-sound empty whiteCell ()
sameCell-sound blackCell empty ()
sameCell-sound blackCell whiteCell ()
sameCell-sound whiteCell empty ()
sameCell-sound whiteCell blackCell ()

samePlayer-sound : ∀ p q → samePlayer p q ≡ true → p ≡ q
samePlayer-sound black black e = refl
samePlayer-sound white white e = refl
samePlayer-sound black white ()
samePlayer-sound white black ()

eqState : State six → State six → Bool
eqState (state b p) (state c q) = sameVec (sameVec sameCell) b c ∧ samePlayer p q

eqState-sound : ∀ s t → eqState s t ≡ true → s ≡ t
eqState-sound (state b p) (state c q) e = cong₂ state
  (sameVec-sound (sameVec sameCell) (sameVec-sound sameCell sameCell-sound) b c
    (left (sameVec (sameVec sameCell) b c) (samePlayer p q) e))
  (samePlayer-sound p q (right (sameVec (sameVec sameCell) b c) (samePlayer p q) e))

stateEquality6 : StateEquality (State six)
stateEquality6 = stateEquality eqState eqState-sound

-- Every decoder fails closed. Encodings are untrusted inputs, not solver claims.
decodeCell : Char → Maybe Cell
decodeCell c with primCharEquality c '0'
... | true = just empty
... | false with primCharEquality c '1'
... | true = just blackCell
... | false with primCharEquality c '2'
... | true = just whiteCell
... | false = nothing

decodeVec : ∀ {A : Set} → (n : ℕ) → (List Char → Maybe (A × List Char)) →
  List Char → Maybe (V.Vec A n × List Char)
decodeVec zero read cs = just (V.[] , cs)
decodeVec (suc n) read cs with read cs
... | nothing = nothing
... | just (x , rest) with decodeVec n read rest
... | nothing = nothing
... | just (xs , tail) = just (x V.∷ xs , tail)

readCell : List Char → Maybe (Cell × List Char)
readCell [] = nothing
readCell (c ∷ cs) with decodeCell c
... | nothing = nothing
... | just x = just (x , cs)

readBoard : List Char → Maybe (Board six × List Char)
readBoard = decodeVec 6 (decodeVec 6 readCell)

readPlayer : Char → Maybe Player
readPlayer c with primCharEquality c 'b'
... | true = just black
... | false with primCharEquality c 'w'
... | true = just white
... | false = nothing

readState : List Char → Maybe (State six × List Char)
readState [] = nothing
readState (c ∷ cs) with readPlayer c | readBoard cs
... | just p | just (b , rest) = just (state b p , rest)
... | _ | _ = nothing

decodeState : String → Maybe (State six)
decodeState text with readState (primStringToList text)
... | just (s , []) = just s
... | _ = nothing

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

mutual
  readLocal : ℕ → List Char → Maybe (LocalCertificate × List Char)
  readLocal zero cs = nothing
  readLocal (suc fuel) [] = nothing
  readLocal (suc fuel) (c ∷ cs) with primCharEquality c 'L'
  ... | true = just (localLeaf , cs)
  ... | false with primCharEquality c 'S'
  ... | true with readNumber cs
  ... | nothing = nothing
  ... | just (n , tail) = just (solve n , tail)
  readLocal (suc fuel) (c ∷ cs) | false | false with primCharEquality c 'P'
  ... | true with readLocal fuel cs
  ... | nothing = nothing
  ... | just (x , tail) = just (localPass x , tail)
  readLocal (suc fuel) (c ∷ cs) | false | false | false with primCharEquality c 'C'
  ... | true with readNumber cs
  ... | nothing = nothing
  ... | just (n , rest) with readLocal fuel rest
  ... | nothing = nothing
  ... | just (x , tail) = just (localChoice n x , tail)
  readLocal (suc fuel) (c ∷ cs) | false | false | false | false with primCharEquality c 'F'
  ... | false = nothing
  ... | true with readNumber cs
  ... | nothing = nothing
  ... | just (n , rest) with readLocals fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (localFork xs , tail)

  readLocals : ℕ → ℕ → List Char → Maybe (List LocalCertificate × List Char)
  readLocals fuel zero cs = just ([] , cs)
  readLocals zero (suc n) cs = nothing
  readLocals (suc fuel) (suc n) cs with readLocal fuel cs
  ... | nothing = nothing
  ... | just (x , rest) with readLocals fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (x ∷ xs , tail)

decodeLocal : String → Maybe LocalCertificate
decodeLocal text with readLocal (suc (2 * length chars)) chars
  where chars = primStringToList text
... | just (c , []) = just c
... | _ = nothing

readEntries : ℕ → List Char → Maybe (List (Entry (State six)))
readEntries fuel [] = just []
readEntries zero (_ ∷ _) = nothing
readEntries (suc fuel) cs@(_ ∷ _) with readState cs
... | nothing = nothing
... | just (s , rest) with readLocal fuel rest
... | nothing = nothing
... | just (c , tail) with readEntries fuel tail
... | nothing = nothing
... | just xs = just (entry s c ∷ xs)

decodeShard : String → Maybe (List (Entry (State six)))
decodeShard text = readEntries (suc (2 * length chars)) chars
  where chars = primStringToList text
