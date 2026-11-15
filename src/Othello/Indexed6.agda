{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Compact indexed data is untrusted. Fixed vector sizes and
-- complete parsing prevent missing rows from becoming vacuous acceptances.
module Othello.Indexed6 where

open import Prelude
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Char using (Char; primCharEquality)
open import Agda.Builtin.Nat using (_+_; _*_)
open import Game.Core using (Game; Player)
open import Game.Indexed using (IndexedCertificate; indexedLeaf; indexedSolve;
  indexedChoice; indexedFork; indexedPass; cite; citeBy; Resolver)
import Game.Indexed as I
import Game.Balanced as B
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; six; initial)
open import Othello.CompactShared6 using (readCompactState)
open import Othello.Encode6 using (stateEquality6)
open import Othello.Order using (_≤ᵇ_)

private
  alphabet : List Char
  alphabet = primStringToList "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_"

  rank : Char → List Char → Maybe ℕ
  rank c = go 0
    where
    go : ℕ → List Char → Maybe ℕ
    go n [] = nothing
    go n (d ∷ ds) with primCharEquality c d
    ... | true = just n
    ... | false = go (suc n) ds

  readCode : ℕ → List Char → Maybe (ℕ × List Char)
  readCode bound [] = nothing
  readCode bound (c ∷ cs) with rank c alphabet
  ... | nothing = nothing
  ... | just n with n ≤ᵇ bound
  ... | false = nothing
  ... | true = just (n , cs)

-- Binary path characters a/b are followed by a two-digit base-37 local row.
-- The shape determines the path length; every local index is bounds checked.
readId : (shape : B.Shape) → List Char → Maybe (B.Id shape × List Char)
readId (B.leaf n) cs with readCode 36 cs
... | nothing = nothing
... | just (hi , rest) with readCode 36 rest
... | nothing = nothing
... | just (lo , tail) with B.rowFromNat n (37 * hi + lo)
... | nothing = nothing
... | just i = just (i , tail)
readId (B.branch l r) [] = nothing
readId (B.branch l r) (c ∷ cs) with primCharEquality c 'a'
... | true with readId l cs
... | nothing = nothing
... | just (i , tail) = just (B.left i , tail)
readId (B.branch l r) (c ∷ cs) | false with primCharEquality c 'b'
... | false = nothing
... | true with readId r cs
... | nothing = nothing
... | just (i , tail) = just (B.right i , tail)

private
  numberTail : ℕ → Bool → List Char → Maybe (ℕ × List Char)
  numberTail n seen [] = nothing
  numberTail n seen (c ∷ cs) with primCharEquality c ';'
  ... | true with seen
  ... | true = just (n , cs)
  ... | false = nothing
  numberTail n seen (c ∷ cs) | false with rank c (primStringToList "0123456789")
  ... | nothing = nothing
  ... | just d with (10 * n + d) ≤ᵇ 128
  ... | false = nothing
  ... | true = numberTail (10 * n + d) true cs

  length : ∀ {A : Set} → List A → ℕ
  length [] = zero
  length (_ ∷ xs) = suc (length xs)

-- Inline syntax matches the established wire except that K/R carry typed IDs.
mutual
  readIndexed : (shape : B.Shape) → ℕ → List Char →
    Maybe (IndexedCertificate (B.Id shape) × List Char)
  readIndexed shape zero cs = nothing
  readIndexed shape (suc fuel) [] = nothing
  readIndexed shape (suc fuel) (c ∷ cs) with primCharEquality c 'L'
  ... | true = just (indexedLeaf , cs)
  ... | false with primCharEquality c 'K'
  ... | true with readId shape cs
  ... | nothing = nothing
  ... | just (i , tail) = just (cite i , tail)
  readIndexed shape (suc fuel) (c ∷ cs) | false | false with primCharEquality c 'R'
  ... | true with readCode 7 cs
  ... | nothing = nothing
  ... | just (tag , rest) with readId shape rest
  ... | nothing = nothing
  ... | just (i , tail) = just (citeBy tag i , tail)
  readIndexed shape (suc fuel) (c ∷ cs) | false | false | false with primCharEquality c 'S'
  ... | true with numberTail 0 false cs
  ... | nothing = nothing
  ... | just (n , tail) = just (indexedSolve n , tail)
  readIndexed shape (suc fuel) (c ∷ cs) | false | false | false | false with primCharEquality c 'P'
  ... | true with readIndexed shape fuel cs
  ... | nothing = nothing
  ... | just (x , tail) = just (indexedPass x , tail)
  readIndexed shape (suc fuel) (c ∷ cs) | false | false | false | false | false with primCharEquality c 'C'
  ... | true with readCode 35 cs
  ... | nothing = nothing
  ... | just (n , rest) with readIndexed shape fuel rest
  ... | nothing = nothing
  ... | just (x , tail) = just (indexedChoice n x , tail)
  readIndexed shape (suc fuel) (c ∷ cs) | false | false | false | false | false | false with primCharEquality c 'F'
  ... | false = nothing
  ... | true with readCode 36 cs
  ... | nothing = nothing
  ... | just (n , rest) with readIndexeds shape fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (indexedFork xs , tail)

  readIndexeds : (shape : B.Shape) → ℕ → ℕ → List Char →
    Maybe (List (IndexedCertificate (B.Id shape)) × List Char)
  readIndexeds shape fuel zero cs = just ([] , cs)
  readIndexeds shape zero (suc n) cs = nothing
  readIndexeds shape (suc fuel) (suc n) cs with readIndexed shape fuel cs
  ... | nothing = nothing
  ... | just (x , rest) with readIndexeds shape fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (x ∷ xs , tail)

private
  readStates : (n : ℕ) → List Char → Maybe (B.Vec (State six) n × List Char)
  readStates zero cs = just (B.nil , cs)
  readStates (suc n) cs with readCompactState cs
  ... | nothing = nothing
  ... | just (s , rest) with readStates n rest
  ... | nothing = nothing
  ... | just (ss , tail) = just (B.cons s ss , tail)

  readBodies : (shape : B.Shape) → ℕ → (n : ℕ) → List Char →
    Maybe (B.Vec (IndexedCertificate (B.Id shape)) n × List Char)
  readBodies shape fuel zero cs = just (B.nil , cs)
  readBodies shape fuel (suc n) cs with readIndexed shape fuel cs
  ... | nothing = nothing
  ... | just (c , rest) with readBodies shape fuel n rest
  ... | nothing = nothing
  ... | just (cs , tail) = just (B.cons c cs , tail)

decodeStates : (n : ℕ) → String → Maybe (B.Vec (State six) n)
decodeStates n text with readStates n (primStringToList text)
... | just (ss , []) = just ss
... | _ = nothing

decodeBodiesChars : (shape : B.Shape) → (n : ℕ) → List Char →
  Maybe (B.Vec (IndexedCertificate (B.Id shape)) n)
decodeBodiesChars shape n chars with readBodies shape (suc (2 * length chars)) n chars
... | just (cs , []) = just cs
... | _ = nothing

decodeBodies : (shape : B.Shape) → (n : ℕ) → String →
  Maybe (B.Vec (IndexedCertificate (B.Id shape)) n)
decodeBodies shape n text = decodeBodiesChars shape n (primStringToList text)

replicate : ∀ {A : Set} → (n : ℕ) → A → B.Vec A n
replicate zero x = B.nil
replicate (suc n) x = B.cons x (replicate n x)

states : (n : ℕ) → String → B.Vec (State six) n
states n text = fromMaybe (replicate n (initial six)) (decodeStates n text)

bodies : (shape : B.Shape) → (n : ℕ) → String →
  B.Vec (IndexedCertificate (B.Id shape)) n
bodies shape n text = fromMaybe (replicate n indexedLeaf) (decodeBodies shape n text)

module Checking (shape : B.Shape) (g : Game (State six)) (p : Player)
  (goal : State six → Bool) (laws : CertificateTransport g p goal) where

  module V = I.Checker (B.order shape) stateEquality6 g p goal laws

  checkRows : ∀ {n} → Resolver (B.Id shape) (State six) →
    (B.Fin n → B.Id shape) → B.Vec (State six) n →
    B.Vec (IndexedCertificate (B.Id shape)) n → Bool
  checkRows L embed B.nil B.nil = true
  checkRows L embed (B.cons s ss) (B.cons c cs) =
    V.checkLocal L (embed B.fzero) s c ∧
      checkRows L (λ i → embed (B.fsuc i)) ss cs

  private
    and-left : ∀ a b → a ∧ b ≡ true → a ≡ true
    and-left true b e = refl
    and-left false b ()

    and-right : ∀ a b → a ∧ b ≡ true → b ≡ true
    and-right true b e = e
    and-right false b ()

    false-elim : ∀ {A : Set} → false ≡ true → A
    false-elim ()

  checkRows-row : ∀ {n} L embed (ss : B.Vec (State six) n) cs →
    checkRows L embed ss cs ≡ true → ∀ i →
    V.checkLocal L (embed i) (B.lookupVec ss i) (B.lookupVec cs i) ≡ true
  checkRows-row L embed (B.cons s ss) (B.cons c cs) e B.fzero =
    and-left (V.checkLocal L (embed B.fzero) s c)
      (checkRows L (λ i → embed (B.fsuc i)) ss cs) e
  checkRows-row L embed (B.cons s ss) (B.cons c cs) e (B.fsuc i) =
    checkRows-row L (λ j → embed (B.fsuc j)) ss cs
      (and-right (V.checkLocal L (embed B.fzero) s c)
        (checkRows L (λ j → embed (B.fsuc j)) ss cs) e) i

  checkPart : ∀ {n} → Resolver (B.Id shape) (State six) →
    (B.Fin n → B.Id shape) → String → String → Bool
  checkPart {n} L embed stateText bodyText with
    decodeStates n stateText | decodeBodies shape n bodyText
  ... | just ss | just cs = checkRows L embed ss cs
  ... | _ | _ = false

  -- Defaults make data total, but malformed data can never supply this fact.
  checkPart-row : ∀ {n} L embed stateText bodyText →
    checkPart {n} L embed stateText bodyText ≡ true → ∀ i →
    V.checkLocal L (embed i) (B.lookupVec (states n stateText) i)
      (B.lookupVec (bodies shape n bodyText) i) ≡ true
  checkPart-row {n} L embed stateText bodyText e with
    decodeStates n stateText in es | decodeBodies shape n bodyText in ec
  ... | nothing | x = false-elim e
  ... | just ss | nothing = false-elim e
  ... | just ss | just cs rewrite es | ec = checkRows-row L embed ss cs e

  -- Keep this fact polymorphic until the final assembly. Proof parts import
  -- only their own bodies and the state data actually used in their checks.
  linkPart : ∀ {n} L embed stateText bodyText →
    checkPart {n} L embed stateText bodyText ≡ true →
    (G : B.Id shape → State six) →
    (C : B.Id shape → IndexedCertificate (B.Id shape)) →
    V.Compatible L G →
    (∀ i → G (embed i) ≡ B.lookupVec (states n stateText) i) →
    (∀ i → C (embed i) ≡ B.lookupVec (bodies shape n bodyText) i) →
    ∀ i → V.TreeOK G (embed i) (G (embed i)) (C (embed i))
  linkPart {n} L embed stateText bodyText accepted G C compatible sameState sameBody i =
    subst (λ s → V.TreeOK G (embed i) s (C (embed i))) (sym (sameState i))
      (subst (λ c → V.TreeOK G (embed i)
          (B.lookupVec (states n stateText) i) c) (sym (sameBody i))
        (V.lift-local compatible
          (V.checkLocal-sound L (embed i)
            (B.lookupVec (states n stateText) i)
            (B.lookupVec (bodies shape n bodyText) i)
            (checkPart-row L embed stateText bodyText accepted i))))
