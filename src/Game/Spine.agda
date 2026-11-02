{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Explicit strategy paths retain their computational structure
-- while already checked certificates can stay opaque in other branches.
module Game.Spine where

open import Game.Core
open import Game.Certificate
open import Game.Symmetry using (Proven)

module Paths {S : Set} (g : Game S) (p : Player) (goal : S → Bool) where

  -- Every branch is still justified by the ordinary game rules. A plug is
  -- an actual accepted certificate for that branch's exact state.
  mutual
    data Spine (s : S) : Set where
      finish : next g s ≡ [] → goal s ≡ true → Spine s
      plug : Proven g p goal s → Spine s
      pick : ∀ {x xs t i} → samePlayer (turn g s) p ≡ true →
        next g s ≡ x ∷ xs → lookup (x ∷ xs) i ≡ just t →
        Spine t → Spine s
      split : ∀ {x xs} → samePlayer (turn g s) p ≡ false →
        next g s ≡ x ∷ xs → Branches (x ∷ xs) → Spine s
      forced : ∀ {t} → forcedPass g s ≡ true → next g s ≡ t ∷ [] →
        Spine t → Spine s

    data Branches : List S → Set where
      nil : Branches []
      cons : ∀ {s ss} → Spine s → Branches ss → Branches (s ∷ ss)

  -- The explicit constructors compute without examining their rule proofs.
  -- Only entering a plug needs the corresponding imported certificate.
  mutual
    certificate : ∀ {s} → Spine s → Certificate
    certificate (finish en eg) = leaf
    certificate (plug proof) = proj₁ proof
    certificate (pick {i = i} eo en el child) = choice i (certificate child)
    certificate (split eo en children) = fork (certificates children)
    certificate (forced ep en child) = pass (certificate child)

    certificates : ∀ {ss} → Branches ss → List Certificate
    certificates nil = []
    certificates (cons child children) = certificate child ∷ certificates children

  mutual
    certificate-sound : ∀ {s} (spine : Spine s) →
      check g p goal s (certificate spine) ≡ true
    certificate-sound (finish en eg) rewrite en = eg
    certificate-sound (plug proof) = proj₂ proof
    certificate-sound (pick eo en el child) rewrite en | eo | el =
      certificate-sound child
    certificate-sound (split eo en children) rewrite en | eo =
      certificates-sound children
    certificate-sound (forced ep en child) rewrite en | ep =
      certificate-sound child

    certificates-sound : ∀ {ss} (children : Branches ss) →
      checkForest g p goal ss (certificates children) ≡ true
    certificates-sound nil = refl
    certificates-sound (cons child children)
      rewrite certificate-sound child = certificates-sound children

  proven : ∀ {s} → Spine s → Proven g p goal s
  proven spine = certificate spine , certificate-sound spine
