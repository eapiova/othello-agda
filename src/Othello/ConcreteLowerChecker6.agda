{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Keep ordinary working states; decode stored codes only in proofs.
module Othello.ConcreteLowerChecker6 where

open import Game.Core
open import Game.Composite using (StateEquality)
open import Game.BooleanSearch using (forcesB)
open import Game.Symmetry using (CertificateTransport; act; acceptedTag)
open import Game.DirectedIndexed using (DirectedCertificate; indexedLeaf; indexedSolve;
  indexedChoice; indexedFork; indexedPass; cite; citeBy; indexedPick; MovePicker; pick)
import Game.DirectedIndexed as D
import Game.Indexed as I

private
  false-elim : ∀ {A : Set} → false ≡ true → A
  false-elim ()

  nothing-elim : ∀ {A B : Set} {x : A} → nothing ≡ just x → B
  nothing-elim ()

  just-injective : ∀ {A : Set} {x y : A} → just x ≡ just y → x ≡ y
  just-injective refl = refl

  and-left : ∀ a b → a ∧ b ≡ true → a ≡ true
  and-left true b checked = refl
  and-left false b ()

  and-right : ∀ a b → a ∧ b ≡ true → b ≡ true
  and-right true b checked = checked
  and-right false b ()


-- Fixed safe instance: there are no game/law/module parameters on recursion.
open import Othello.Board using (State; Coord; six)
open import Othello.Encode6 using (stateEquality6)
open import Othello.Statements using (lowerGoal)
open import Othello.DirectSymmetry6 using (lowerTransport6)
import Othello.InlineEntries6 as New
import Othello.RowPacked6 as Packed
import Othello.AgreedIndexed6 as A
import Game.NatOrder as N

Key : Set
Key = ℕ
S : Set
S = State six
Stored : Set
Stored = Packed.PackedState
Move : Set
Move = Coord six
order : I.Order Key
order = N.order
eq : StateEquality S
eq = stateEquality6
g : Game S
g = New.specializedGame6
p : Player
p = white
goal : S → Bool
goal = lowerGoal 4
module Agreed = A.With New.specializedGame6 New.agreement
laws : CertificateTransport g p goal
laws = Agreed.adapt white (lowerGoal 4) lowerTransport6
picker : MovePicker g Move
picker = New.picker
decode : Stored → S
decode = Packed.decode
matches : S → Stored → Bool
matches = Packed.matches
matches-sound : ∀ s t → matches s t ≡ true → s ≡ decode t
matches-sound = Packed.matches-sound

import Game.EncodedResolver as General
module Generic = General.Checking order eq g p goal laws picker decode matches matches-sound
module Old = Generic.Old

Resolver : Set
Resolver = Key → Maybe Stored

decodeMaybe : Maybe Stored → Maybe S
decodeMaybe nothing = nothing
decodeMaybe (just t) = just (decode t)

decodeResolver : Resolver → Key → Maybe S
decodeResolver L j = decodeMaybe (L j)

mutual
  checkLocal : Resolver → Key → S → DirectedCertificate Key Move → Bool
  checkLocal L owner s indexedLeaf with next g s
  ... | [] = goal s
  ... | x ∷ xs = false
  checkLocal L owner s (indexedSolve fuel) = forcesB fuel g p goal s
  checkLocal L owner s (indexedChoice i c)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | false = false
  ... | x ∷ xs | true with lookup (x ∷ xs) i
  ...   | nothing = false
  ...   | just t = checkLocal L owner t c
  checkLocal L owner s (indexedFork cs)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | true = false
  ... | x ∷ xs | false = checkLocalForest L owner (x ∷ xs) cs
  checkLocal L owner s (indexedPass c) with next g s | forcedPass g s
  ... | [] | b = false
  ... | x ∷ [] | false = false
  ... | x ∷ y ∷ xs | b = false
  ... | x ∷ [] | true = checkLocal L owner x c
  checkLocal L owner s (cite j) with I.beforeB order j owner
  ... | false = false
  ... | true with L j
  ...   | nothing = false
  ...   | just u = matches s u
  checkLocal L owner s (citeBy tag j) with I.beforeB order j owner
  ... | false = false
  ... | true with acceptedTag laws tag
  ...   | false = false
  ...   | true with L j
  ...     | nothing = false
  ...     | just u = matches (act laws tag s) u
  checkLocal L owner s (indexedPick a c)
    with samePlayer (turn g s) p | pick picker s a
  ... | false | mt = false
  ... | true | nothing = false
  ... | true | just t = checkLocal L owner t c

  checkLocalForest : Resolver → Key → List S →
    List (DirectedCertificate Key Move) → Bool
  checkLocalForest L owner [] [] = true
  checkLocalForest L owner [] (c ∷ cs) = false
  checkLocalForest L owner (s ∷ ss) [] = false
  checkLocalForest L owner (s ∷ ss) (c ∷ cs) =
    checkLocal L owner s c ∧ checkLocalForest L owner ss cs


private
  cong₂ : ∀ {X Y Z : Set} (f : X → Y → Z) {x x′ y y′} →
    x ≡ x′ → y ≡ y′ → f x y ≡ f x′ y′
  cong₂ f refl refl = refl

abstract
  mutual
    checkLocal-agree : ∀ L owner s c → checkLocal L owner s c ≡ Generic.checkLocal L owner s c
    checkLocal-agree L owner s indexedLeaf with next g s
    ... | [] = refl
    ... | x ∷ xs = refl
    checkLocal-agree L owner s (indexedSolve fuel) = refl
    checkLocal-agree L owner s (indexedChoice i c)
      with next g s | samePlayer (turn g s) p
    ... | [] | own = refl
    ... | x ∷ xs | false = refl
    ... | x ∷ xs | true with lookup (x ∷ xs) i
    ...   | nothing = refl
    ...   | just t = checkLocal-agree L owner t c
    checkLocal-agree L owner s (indexedFork cs)
      with next g s | samePlayer (turn g s) p
    ... | [] | own = refl
    ... | x ∷ xs | true = refl
    ... | x ∷ xs | false = checkLocalForest-agree L owner (x ∷ xs) cs
    checkLocal-agree L owner s (indexedPass c) with next g s | forcedPass g s
    ... | [] | b = refl
    ... | x ∷ [] | false = refl
    ... | x ∷ y ∷ xs | b = refl
    ... | x ∷ [] | true = checkLocal-agree L owner x c
    checkLocal-agree L owner s (cite j) with I.beforeB order j owner
    ... | false = refl
    ... | true with L j
    ...   | nothing = refl
    ...   | just u = refl
    checkLocal-agree L owner s (citeBy tag j) with I.beforeB order j owner
    ... | false = refl
    ... | true with acceptedTag laws tag
    ...   | false = refl
    ...   | true with L j
    ...     | nothing = refl
    ...     | just u = refl
    checkLocal-agree L owner s (indexedPick a c)
      with samePlayer (turn g s) p | pick picker s a
    ... | false | mt = refl
    ... | true | nothing = refl
    ... | true | just t = checkLocal-agree L owner t c

    checkLocalForest-agree : ∀ L owner ss cs →
      checkLocalForest L owner ss cs ≡ Generic.checkLocalForest L owner ss cs
    checkLocalForest-agree L owner [] [] = refl
    checkLocalForest-agree L owner [] (c ∷ cs) = refl
    checkLocalForest-agree L owner (s ∷ ss) [] = refl
    checkLocalForest-agree L owner (s ∷ ss) (c ∷ cs) =
      cong₂ _∧_ (checkLocal-agree L owner s c) (checkLocalForest-agree L owner ss cs)

Compatible : Resolver → (Key → Stored) → Set
Compatible = Generic.Compatible

abstract
  tree-sound : ∀ L G owner s c → Compatible L G → checkLocal L owner s c ≡ true →
    Old.TreeOK (λ j → decode (G j)) owner s c
  tree-sound L G owner s c compatible checked =
    Generic.tree-sound L G owner s c compatible
      (trans (sym (checkLocal-agree L owner s c)) checked)
