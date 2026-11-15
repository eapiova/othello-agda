{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Small independent rows exercise rule checks, resolver checks,
-- tagged transport, and the well-founded global soundness interface.
module Tests.Indexed where

open import Game.Core
open import Game.Certificate using (leaf; choice; check)
open import Game.Composite using (StateEquality)
open import Game.Symmetry using (Proven; CertificateTransport; transport)
open import Game.Indexed

data ID : Set where
  first second third : ID

before : ID → ID → Bool
before first second = true
before first third = true
before second third = true
before _ _ = false

Precedes : ID → ID → Set
Precedes j i = before j i ≡ true

first-accessible : Acc Precedes first
first-accessible = acc preceding
  where
  preceding : ∀ j → Precedes j first → Acc Precedes j
  preceding first ()
  preceding second ()
  preceding third ()

second-accessible : Acc Precedes second
second-accessible = acc preceding
  where
  preceding : ∀ j → Precedes j second → Acc Precedes j
  preceding first e = first-accessible
  preceding second ()
  preceding third ()

third-accessible : Acc Precedes third
third-accessible = acc preceding
  where
  preceding : ∀ j → Precedes j third → Acc Precedes j
  preceding first e = first-accessible
  preceding second e = second-accessible
  preceding third ()

ids : Order ID
ids = record
  { _<_ = Precedes
  ; beforeB = before
  ; before-sound = λ j i e → e
  ; wellFounded = λ { first → first-accessible ; second → second-accessible ; third → third-accessible }
  }

-- States 0/1 are win/lose, 2/3 are mirrored choices, 4 is an opponent
-- fork, and 5 is a compulsory pass. Higher states are losing terminals.
moves : ℕ → List ℕ
moves 2 = 0 ∷ 1 ∷ []
moves 3 = 1 ∷ 0 ∷ []
moves 4 = 0 ∷ 0 ∷ []
moves 5 = 0 ∷ []
moves _ = []

player : ℕ → Player
player 4 = white
player _ = black

isPass : ℕ → Bool
isPass 5 = true
isPass _ = false

toy : Game ℕ
toy = record { turn = player ; next = moves ; forcedPass = isPass }

goal : ℕ → Bool
goal zero = true
goal (suc n) = false

eqNat : ℕ → ℕ → Bool
eqNat zero zero = true
eqNat zero (suc n) = false
eqNat (suc m) zero = false
eqNat (suc m) (suc n) = eqNat m n

eqNat-sound : ∀ m n → eqNat m n ≡ true → m ≡ n
eqNat-sound zero zero e = refl
eqNat-sound zero (suc n) ()
eqNat-sound (suc m) zero ()
eqNat-sound (suc m) (suc n) e = cong suc (eqNat-sound m n e)

states : StateEquality ℕ
states = record { equal = eqNat ; equal-sound = eqNat-sound }

mirror : ℕ → ℕ
mirror 2 = 3
mirror 3 = 2
mirror n = n

mirror-proven : ∀ s → Proven toy black goal (mirror s) → Proven toy black goal s
mirror-proven 0 proof = proof
mirror-proven 1 proof = proof
mirror-proven 2 proof = choice 0 leaf , refl
mirror-proven 3 proof = choice 1 leaf , refl
mirror-proven (suc (suc (suc (suc n)))) proof = proof

toyAct : ℕ → ℕ → ℕ
toyAct zero s = s
toyAct (suc tag) s = mirror s

validTag : ℕ → Bool
validTag zero = true
validTag (suc zero) = true
validTag (suc (suc tag)) = false

toyTransport : ∀ tag s → Proven toy black goal (toyAct tag s) → Proven toy black goal s
toyTransport zero s proof = proof
toyTransport (suc tag) s proof = mirror-proven s proof

laws : CertificateTransport toy black goal
laws = record { act = toyAct ; acceptedTag = validTag ; transport = toyTransport }

module Toy = Checker ids states toy black goal laws

empty : Resolver ID ℕ
empty j = nothing

winResolver : Resolver ID ℕ
winResolver first = just 0
winResolver second = just 0
winResolver third = just 0

sourceResolver : Resolver ID ℕ
sourceResolver first = just 3
sourceResolver second = nothing
sourceResolver third = nothing

leaf-accepted : Toy.checkLocal empty first 0 indexedLeaf ≡ true
leaf-accepted = refl

premature-leaf-rejected : Toy.checkLocal empty first 2 indexedLeaf ≡ false
premature-leaf-rejected = refl

false-goal-rejected : Toy.checkLocal empty first 1 indexedLeaf ≡ false
false-goal-rejected = refl

zero-fuel-rejected : Toy.checkLocal empty first 0 (indexedSolve 0) ≡ false
zero-fuel-rejected = refl

terminal-solve-accepted : Toy.checkLocal empty first 0 (indexedSolve 1) ≡ true
terminal-solve-accepted = refl

choice-solve-accepted : Toy.checkLocal empty first 2 (indexedSolve 2) ≡ true
choice-solve-accepted = refl

choice-accepted : Toy.checkLocal empty first 2 (indexedChoice 0 indexedLeaf) ≡ true
choice-accepted = refl

wrong-player-rejected : Toy.checkLocal empty first 4 (indexedChoice 0 indexedLeaf) ≡ false
wrong-player-rejected = refl

illegal-index-rejected : Toy.checkLocal empty first 2 (indexedChoice 2 indexedLeaf) ≡ false
illegal-index-rejected = refl

complete-fork-accepted :
  Toy.checkLocal empty first 4 (indexedFork (indexedLeaf ∷ indexedLeaf ∷ [])) ≡ true
complete-fork-accepted = refl

missing-reply-rejected : Toy.checkLocal empty first 4 (indexedFork (indexedLeaf ∷ [])) ≡ false
missing-reply-rejected = refl

extra-reply-rejected :
  Toy.checkLocal empty first 4 (indexedFork (indexedLeaf ∷ indexedLeaf ∷ indexedLeaf ∷ [])) ≡ false
extra-reply-rejected = refl

own-fork-rejected :
  Toy.checkLocal empty first 2 (indexedFork (indexedLeaf ∷ indexedLeaf ∷ [])) ≡ false
own-fork-rejected = refl

forced-pass-accepted : Toy.checkLocal empty first 5 (indexedPass indexedLeaf) ≡ true
forced-pass-accepted = refl

voluntary-pass-rejected : Toy.checkLocal empty first 2 (indexedPass indexedLeaf) ≡ false
voluntary-pass-rejected = refl

exact-reference-accepted : Toy.checkLocal winResolver second 0 (cite first) ≡ true
exact-reference-accepted = refl

absent-reference-rejected : Toy.checkLocal empty second 0 (cite first) ≡ false
absent-reference-rejected = refl

wrong-state-rejected : Toy.checkLocal winResolver second 1 (cite first) ≡ false
wrong-state-rejected = refl

self-reference-rejected : Toy.checkLocal winResolver second 0 (cite second) ≡ false
self-reference-rejected = refl

forward-reference-rejected : Toy.checkLocal winResolver first 0 (cite second) ≡ false
forward-reference-rejected = refl

-- A proposed first↔second cycle cannot pass the first row's guard.
cycle-edge-rejected : Toy.checkLocal winResolver first 0 (citeBy 0 second) ≡ false
cycle-edge-rejected = refl

inline-earlier-reference-accepted :
  Toy.checkLocal winResolver second 2 (indexedChoice 0 (cite first)) ≡ true
inline-earlier-reference-accepted = refl

inline-owner-retained :
  Toy.checkLocal winResolver second 2 (indexedChoice 0 (cite second)) ≡ false
inline-owner-retained = refl

tagged-reference-accepted : Toy.checkLocal sourceResolver second 2 (citeBy 1 first) ≡ true
tagged-reference-accepted = refl

invalid-tag-rejected : Toy.checkLocal sourceResolver second 2 (citeBy 2 first) ≡ false
invalid-tag-rejected = refl

wrong-transformed-state-rejected : Toy.checkLocal winResolver second 2 (citeBy 1 first) ≡ false
wrong-transformed-state-rejected = refl

untransformed-reference-rejected : Toy.checkLocal sourceResolver second 2 (cite first) ≡ false
untransformed-reference-rejected = refl

-- The checker-derived judgment needs only sourceResolver's data. No proof
-- of the cited first row occurs in this independently accepted fact.
independent-local-fact : Toy.LocalOK sourceResolver second 2 (citeBy 1 first)
independent-local-fact =
  Toy.checkLocal-sound sourceResolver second 2 (citeBy 1 first) tagged-reference-accepted

-- The mirrored source choice must be reindexed by certificate transport.
source-choice-fails-at-target : check toy black goal 2 (choice 1 leaf) ≡ false
source-choice-fails-at-target = refl

transported-choice-valid :
  check toy black goal 2 (proj₁ (transport laws 1 2 (choice 1 leaf , refl))) ≡ true
transported-choice-valid = refl

G : ID → ℕ
G first = 3
G second = 2
G third = 2

C : ID → IndexedCertificate ID
C first = indexedChoice 1 indexedLeaf
C second = citeBy 1 first
C third = cite second

-- Each local resolver exports only the state the corresponding row needs.
L : ID → Resolver ID ℕ
L first j = nothing
L second j = sourceResolver j
L third first = nothing
L third second = just 2
L third third = nothing

compatible : ∀ i → Toy.Compatible (L i) G
compatible first j u ()
compatible second first u refl = refl
compatible second second u ()
compatible second third u ()
compatible third first u ()
compatible third second u refl = refl
compatible third third u ()

row-accepted : ∀ i → Toy.checkLocal (L i) i (G i) (C i) ≡ true
row-accepted first = refl
row-accepted second = refl
row-accepted third = refl

rows : ∀ i → Toy.TreeOK G i (G i) (C i)
rows i = Toy.lift-local (compatible i)
  (Toy.checkLocal-sound (L i) i (G i) (C i) (row-accepted i))

global-example : Proven toy black goal 2
global-example = Toy.localRows-proven G C L compatible row-accepted third

global-example-guarantee : Guarantees toy black goal 2
global-example-guarantee = Toy.global-sound G C rows third
