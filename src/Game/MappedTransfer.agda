{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Checked certificates transfer along an exact decoding of
-- successor order, turns, and compulsory-pass status.
module Game.MappedTransfer where

open import Game.Core
open import Game.Certificate
open import Game.Symmetry

mapMaybe : ∀ {S T : Set} → (S → T) → Maybe S → Maybe T
mapMaybe f nothing = nothing
mapMaybe f (just s) = just (f s)

record Refinement {S T : Set} (g : Game S) (h : Game T)
                  (decode : S → T) : Set where
  constructor refinement
  field
    next-maps : ∀ s → map decode (next g s) ≡ next h (decode s)
    turn-maps : ∀ s → turn g s ≡ turn h (decode s)
    pass-maps : ∀ s → forcedPass g s ≡ forcedPass h (decode s)
open Refinement public

abstract
  lookup-map : ∀ {S T : Set} (f : S → T) xs i →
    lookup (map f xs) i ≡ mapMaybe f (lookup xs i)
  lookup-map f [] i = refl
  lookup-map f (x ∷ xs) zero = refl
  lookup-map f (x ∷ xs) (suc i) = lookup-map f xs i

  mutual
    check-maps : ∀ {S T : Set} (g : Game S) (h : Game T)
      (decode : S → T) (e : Refinement g h decode) p goal s c →
      check g p (λ u → goal (decode u)) s c ≡
      check h p goal (decode s) c
    check-maps g h decode e p goal s leaf
      rewrite sym (next-maps e s) with next g s
    ... | [] = refl
    ... | x ∷ xs = refl
    check-maps g h decode e p goal s (choice i c)
      rewrite sym (next-maps e s) | sym (turn-maps e s)
      with next g s | samePlayer (turn g s) p
    ... | [] | own = refl
    ... | x ∷ xs | false = refl
    ... | x ∷ xs | true
      with lookup (x ∷ xs) i | lookup-map decode (x ∷ xs) i
    ... | nothing | mapped rewrite mapped = refl
    ... | just t | mapped rewrite mapped = check-maps g h decode e p goal t c
    check-maps g h decode e p goal s (fork cs)
      rewrite sym (next-maps e s) | sym (turn-maps e s)
      with next g s | samePlayer (turn g s) p
    ... | [] | own = refl
    ... | x ∷ xs | true = refl
    ... | x ∷ xs | false = checkForest-maps g h decode e p goal (x ∷ xs) cs
    check-maps g h decode e p goal s (pass c)
      rewrite sym (next-maps e s) | sym (pass-maps e s)
      with next g s | forcedPass g s
    ... | [] | b = refl
    ... | x ∷ [] | false = refl
    ... | x ∷ y ∷ xs | b = refl
    ... | x ∷ [] | true = check-maps g h decode e p goal x c

    checkForest-maps : ∀ {S T : Set} (g : Game S) (h : Game T)
      (decode : S → T) (e : Refinement g h decode) p goal ss cs →
      checkForest g p (λ u → goal (decode u)) ss cs ≡
      checkForest h p goal (map decode ss) cs
    checkForest-maps g h decode e p goal [] [] = refl
    checkForest-maps g h decode e p goal [] (c ∷ cs) = refl
    checkForest-maps g h decode e p goal (s ∷ ss) [] = refl
    checkForest-maps g h decode e p goal (s ∷ ss) (c ∷ cs)
      rewrite check-maps g h decode e p goal s c |
              checkForest-maps g h decode e p goal ss cs = refl

to-old : ∀ {S T : Set} (g : Game S) (h : Game T) (decode : S → T)
  (e : Refinement g h decode) p goal s →
  Proven g p (λ u → goal (decode u)) s → Proven h p goal (decode s)
to-old g h decode e p goal s (c , checked) =
  c , trans (sym (check-maps g h decode e p goal s c)) checked

from-old : ∀ {S T : Set} (g : Game S) (h : Game T) (decode : S → T)
  (e : Refinement g h decode) p goal s →
  Proven h p goal (decode s) → Proven g p (λ u → goal (decode u)) s
from-old g h decode e p goal s (c , checked) =
  c , trans (check-maps g h decode e p goal s c) checked

module Adapting {S T : Set} (g : Game S) (h : Game T) (decode : S → T)
  (e : Refinement g h decode) (p : Player) (goal : T → Bool)
  (oldLaws : CertificateTransport h p goal) (newAct : ℕ → S → S)
  (action-maps : ∀ tag s →
    decode (newAct tag s) ≡ act oldLaws tag (decode s)) where

  private
    abstract
      transport-new : ∀ tag s →
        Proven g p (λ u → goal (decode u)) (newAct tag s) →
        Proven g p (λ u → goal (decode u)) s
      transport-new tag s proof =
        from-old g h decode e p goal s
          (transport oldLaws tag (decode s)
            (subst (Proven h p goal) (action-maps tag s)
              (to-old g h decode e p goal (newAct tag s) proof)))

  laws : CertificateTransport g p (λ s → goal (decode s))
  laws = record
    { act = newAct
    ; acceptedTag = acceptedTag oldLaws
    ; transport = transport-new
    }
