{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Compact indexed data is untrusted. Fixed vector sizes and
-- complete parsing prevent missing rows from becoming vacuous acceptances.
module Othello.NatIndexed6 where

open import Prelude
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Char using (Char; primCharEquality)
open import Agda.Builtin.Nat using (_+_; _*_; _<_)
open import Game.Core using (Game; Player)
open import Game.Indexed using (IndexedCertificate; indexedLeaf; indexedSolve;
  indexedChoice; indexedFork; indexedPass; cite; citeBy; Resolver)
import Game.Indexed as I
import Game.Balanced as B
import Game.NatOrder as N
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; six; initial)
open import Othello.Indexed6 public using (decodeStates; states; replicate)
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

-- Numeric IDs are base-37 digits terminated by a semicolon. The size cap
-- limits parser work; successful checks still require decreasing references,
-- an actual resolver hit, and sound equality of the complete game state.
private
  idTail : ℕ → Bool → List Char → Maybe (ℕ × List Char)
  idTail n seen [] = nothing
  idTail n seen (c ∷ cs) with primCharEquality c ';'
  ... | true with seen
  ... | true = just (n , cs)
  ... | false = nothing
  idTail n seen (c ∷ cs) | false with rank c alphabet
  ... | nothing = nothing
  ... | just d with (37 * n + d) < 20000000
  ... | false = nothing
  ... | true = idTail (37 * n + d) true cs

readId : List Char → Maybe (ℕ × List Char)
readId = idTail 0 false

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
  readIndexed : ℕ → List Char →
    Maybe (IndexedCertificate (ℕ) × List Char)
  readIndexed zero cs = nothing
  readIndexed (suc fuel) [] = nothing
  readIndexed (suc fuel) (c ∷ cs) with primCharEquality c 'L'
  ... | true = just (indexedLeaf , cs)
  ... | false with primCharEquality c 'K'
  ... | true with readId cs
  ... | nothing = nothing
  ... | just (i , tail) = just (cite i , tail)
  readIndexed (suc fuel) (c ∷ cs) | false | false with primCharEquality c 'R'
  ... | true with readCode 7 cs
  ... | nothing = nothing
  ... | just (tag , rest) with readId rest
  ... | nothing = nothing
  ... | just (i , tail) = just (citeBy tag i , tail)
  readIndexed (suc fuel) (c ∷ cs) | false | false | false with primCharEquality c 'S'
  ... | true with numberTail 0 false cs
  ... | nothing = nothing
  ... | just (n , tail) = just (indexedSolve n , tail)
  readIndexed (suc fuel) (c ∷ cs) | false | false | false | false with primCharEquality c 'P'
  ... | true with readIndexed fuel cs
  ... | nothing = nothing
  ... | just (x , tail) = just (indexedPass x , tail)
  readIndexed (suc fuel) (c ∷ cs) | false | false | false | false | false with primCharEquality c 'C'
  ... | true with readCode 35 cs
  ... | nothing = nothing
  ... | just (n , rest) with readIndexed fuel rest
  ... | nothing = nothing
  ... | just (x , tail) = just (indexedChoice n x , tail)
  readIndexed (suc fuel) (c ∷ cs) | false | false | false | false | false | false with primCharEquality c 'F'
  ... | false = nothing
  ... | true with readCode 36 cs
  ... | nothing = nothing
  ... | just (n , rest) with readIndexeds fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (indexedFork xs , tail)

  readIndexeds : ℕ → ℕ → List Char →
    Maybe (List (IndexedCertificate (ℕ)) × List Char)
  readIndexeds fuel zero cs = just ([] , cs)
  readIndexeds zero (suc n) cs = nothing
  readIndexeds (suc fuel) (suc n) cs with readIndexed fuel cs
  ... | nothing = nothing
  ... | just (x , rest) with readIndexeds fuel n rest
  ... | nothing = nothing
  ... | just (xs , tail) = just (x ∷ xs , tail)

private
  readBodies : ℕ → (n : ℕ) → List Char →
    Maybe (B.Vec (IndexedCertificate (ℕ)) n × List Char)
  readBodies fuel zero cs = just (B.nil , cs)
  readBodies fuel (suc n) cs with readIndexed fuel cs
  ... | nothing = nothing
  ... | just (c , rest) with readBodies fuel n rest
  ... | nothing = nothing
  ... | just (cs , tail) = just (B.cons c cs , tail)

decodeBodiesChars : (n : ℕ) → List Char →
  Maybe (B.Vec (IndexedCertificate (ℕ)) n)
decodeBodiesChars n chars with readBodies (suc (2 * length chars)) n chars
... | just (cs , []) = just cs
... | _ = nothing

decodeBodies : (n : ℕ) → String →
  Maybe (B.Vec (IndexedCertificate (ℕ)) n)
decodeBodies n text = decodeBodiesChars n (primStringToList text)

bodies : (n : ℕ) → String →
  B.Vec (IndexedCertificate (ℕ)) n
bodies n text = fromMaybe (replicate n indexedLeaf) (decodeBodies n text)

module Checking (g : Game (State six)) (p : Player)
  (goal : State six → Bool) (laws : CertificateTransport g p goal) where

  module V = I.Checker N.order stateEquality6 g p goal laws

  checkRows : ∀ {n} → Resolver (ℕ) (State six) →
    (B.Fin n → ℕ) → B.Vec (State six) n →
    B.Vec (IndexedCertificate (ℕ)) n → Bool
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

  checkPart : ∀ {n} → Resolver (ℕ) (State six) →
    (B.Fin n → ℕ) → String → String → Bool
  checkPart {n} L embed stateText bodyText with
    decodeStates n stateText | decodeBodies n bodyText
  ... | just ss | just cs = checkRows L embed ss cs
  ... | _ | _ = false

  -- Defaults make data total, but malformed data can never supply this fact.
  checkPart-row : ∀ {n} L embed stateText bodyText →
    checkPart {n} L embed stateText bodyText ≡ true → ∀ i →
    V.checkLocal L (embed i) (B.lookupVec (states n stateText) i)
      (B.lookupVec (bodies n bodyText) i) ≡ true
  checkPart-row {n} L embed stateText bodyText e with
    decodeStates n stateText in es | decodeBodies n bodyText in ec
  ... | nothing | x = false-elim e
  ... | just ss | nothing = false-elim e
  ... | just ss | just cs rewrite es | ec = checkRows-row L embed ss cs e

  -- Keep this fact polymorphic until the final assembly. Proof parts import
  -- only their own bodies and the state data actually used in their checks.
  linkPart : ∀ {n} L embed stateText bodyText →
    checkPart {n} L embed stateText bodyText ≡ true →
    (G : ℕ → State six) →
    (C : ℕ → IndexedCertificate (ℕ)) →
    V.Compatible L G →
    (∀ i → G (embed i) ≡ B.lookupVec (states n stateText) i) →
    (∀ i → C (embed i) ≡ B.lookupVec (bodies n bodyText) i) →
    ∀ i → V.TreeOK G (embed i) (G (embed i)) (C (embed i))
  linkPart {n} L embed stateText bodyText accepted G C compatible sameState sameBody i =
    subst (λ s → V.TreeOK G (embed i) s (C (embed i))) (sym (sameState i))
      (subst (λ c → V.TreeOK G (embed i)
          (B.lookupVec (states n stateText) i) c) (sym (sameBody i))
        (V.lift-local compatible
          (V.checkLocal-sound L (embed i)
            (B.lookupVec (states n stateText) i)
            (B.lookupVec (bodies n bodyText) i)
            (checkPart-row L embed stateText bodyText accepted i))))
