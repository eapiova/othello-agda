{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Missing subtrees occupy one constructor, and compatibility
-- remains symbolic in the eventual global resolver.
module Game.BalancedView where

open import Prelude
import Game.Balanced as B

data View (A : Set) : B.Shape → Set where
  absent : ∀ {shape} → View A shape
  present : ∀ {n} → B.Vec (Maybe A) n → View A (B.leaf n)
  branches : ∀ {l r} → View A l → View A r → View A (B.branch l r)

resolve : ∀ {A shape} → View A shape → B.Id shape → Maybe A
resolve absent i = nothing
resolve (present xs) (B.row i) = B.lookupVec xs i
resolve (branches l r) (B.left i) = resolve l i
resolve (branches l r) (B.right i) = resolve r i

-- A proof part can export this condition for an arbitrary G; it need not
-- import or instantiate all of the global state data to establish the form.
Compatible : ∀ {A shape} → View A shape → (B.Id shape → A) → Set
Compatible absent G = ⊤
Compatible (present xs) G = ∀ i u → B.lookupVec xs i ≡ just u → G (B.row i) ≡ u
Compatible (branches l r) G =
  Compatible l (λ i → G (B.left i)) × Compatible r (λ i → G (B.right i))

compatible : ∀ {A shape} {local : View A shape} {G : B.Id shape → A} →
  Compatible local G → ∀ i u → resolve local i ≡ just u → G i ≡ u
compatible {local = absent} proof i u ()
compatible {local = present xs} proof (B.row i) u e = proof i u e
compatible {local = branches l r} (lp , rp) (B.left i) u e = compatible lp i u e
compatible {local = branches l r} (lp , rp) (B.right i) u e = compatible rp i u e

allStates : ∀ {A n} → B.Vec A n → B.Vec (Maybe A) n
allStates B.nil = B.nil
allStates (B.cons x xs) = B.cons (just x) (allStates xs)

private
  all-lookup : ∀ {A n} (xs : B.Vec A n) i →
    B.lookupVec (allStates xs) i ≡ just (B.lookupVec xs i)
  all-lookup (B.cons x xs) B.fzero = refl
  all-lookup (B.cons x xs) (B.fsuc i) = all-lookup xs i

  just-injective : ∀ {A : Set} {x y : A} → just x ≡ just y → x ≡ y
  just-injective refl = refl

-- This small symbolic lemma supplies compatibility for an entire data leaf
-- without enumerating or reducing any of its boards in an assembly module.
present-compatible : ∀ {A n} (xs : B.Vec A n) (G : B.Id (B.leaf n) → A) →
  (∀ i → G (B.row i) ≡ B.lookupVec xs i) → Compatible (present (allStates xs)) G
present-compatible xs G aligned i u e =
  trans (aligned i) (just-injective (trans (sym (all-lookup xs i)) e))
