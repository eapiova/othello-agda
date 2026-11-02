{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Keep ordinary working states; decode stored codes only in proofs.
module Game.EncodedResolver where

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

module Checking {Key S Stored Move : Set} (order : I.Order Key) (eq : StateEquality S)
  (g : Game S) (p : Player) (goal : S → Bool)
  (laws : CertificateTransport g p goal) (picker : MovePicker g Move)
  (decode : Stored → S) (matches : S → Stored → Bool)
  (matches-sound : ∀ s t → matches s t ≡ true → s ≡ decode t) where

  module Old = D.Checker order eq g p goal laws picker

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

  mutual
    checkLocal-sound : ∀ L owner s c → checkLocal L owner s c ≡ true →
      Old.LocalOK (decodeResolver L) owner s c
    checkLocal-sound L owner s indexedLeaf e with next g s in en
    ... | [] = Old.ok-leaf en e
    ... | x ∷ xs = false-elim e
    checkLocal-sound L owner s (indexedSolve fuel) e = Old.ok-solve e
    checkLocal-sound L owner s (indexedChoice i c) e
      with next g s in en | samePlayer (turn g s) p in eo
    ... | [] | own = false-elim e
    ... | x ∷ xs | false = false-elim e
    ... | x ∷ xs | true with lookup (x ∷ xs) i in el
    ...   | nothing = false-elim e
    ...   | just t = Old.ok-choice eo en el (checkLocal-sound L owner t c e)
    checkLocal-sound L owner s (indexedFork cs) e
      with next g s in en | samePlayer (turn g s) p in eo
    ... | [] | own = false-elim e
    ... | x ∷ xs | true = false-elim e
    ... | x ∷ xs | false = Old.ok-fork eo en
      (checkLocalForest-sound L owner (x ∷ xs) cs e)
    checkLocal-sound L owner s (indexedPass c) e
      with next g s in en | forcedPass g s in ep
    ... | [] | b = false-elim e
    ... | x ∷ [] | false = false-elim e
    ... | x ∷ y ∷ xs | b = false-elim e
    ... | x ∷ [] | true = Old.ok-pass ep en (checkLocal-sound L owner x c e)
    checkLocal-sound L owner s (cite j) e with I.beforeB order j owner in eb
    ... | false = false-elim e
    ... | true with L j in el
    ...   | nothing = false-elim e
    ...   | just u = Old.ok-cite (I.before-sound order j owner eb) (cong decodeMaybe el)
      (matches-sound s u e)
    checkLocal-sound L owner s (citeBy tag j) e with I.beforeB order j owner in eb
    ... | false = false-elim e
    ... | true with acceptedTag laws tag in et
    ...   | false = false-elim e
    ...   | true with L j in el
    ...     | nothing = false-elim e
    ...     | just u = Old.ok-citeBy (I.before-sound order j owner eb) et (cong decodeMaybe el)
      (matches-sound (act laws tag s) u e)
    checkLocal-sound L owner s (indexedPick a c) e
      with samePlayer (turn g s) p in eo | pick picker s a in ep
    ... | false | mt = false-elim e
    ... | true | nothing = false-elim e
    ... | true | just t = Old.ok-pick eo ep (checkLocal-sound L owner t c e)

    checkLocalForest-sound : ∀ L owner ss cs →
      checkLocalForest L owner ss cs ≡ true → Old.ForestOK (decodeResolver L) owner ss cs
    checkLocalForest-sound L owner [] [] e = Old.ok-nil
    checkLocalForest-sound L owner [] (c ∷ cs) ()
    checkLocalForest-sound L owner (s ∷ ss) [] ()
    checkLocalForest-sound L owner (s ∷ ss) (c ∷ cs) e =
      Old.ok-cons (checkLocal-sound L owner s c
        (and-left (checkLocal L owner s c) (checkLocalForest L owner ss cs) e))
        (checkLocalForest-sound L owner ss cs
          (and-right (checkLocal L owner s c) (checkLocalForest L owner ss cs) e))

  Compatible : Resolver → (Key → Stored) → Set
  Compatible L G = ∀ j u → L j ≡ just u → G j ≡ u

  decoded-compatible : ∀ {L G} → Compatible L G →
    Old.Compatible (decodeResolver L) (λ j → decode (G j))
  decoded-compatible {L} {G} compatible j s hit with L j in el
  ... | nothing = nothing-elim hit
  ... | just u = trans (cong decode (compatible j u el)) (just-injective hit)

  abstract
    tree-sound : ∀ L G owner s c → Compatible L G → checkLocal L owner s c ≡ true →
      Old.TreeOK (λ j → decode (G j)) owner s c
    tree-sound L G owner s c compatible checked =
      Old.lift-local (decoded-compatible compatible) (checkLocal-sound L owner s c checked)
