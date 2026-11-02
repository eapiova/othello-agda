{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.Permutation where

open import Prelude

data Perm {A : Set} : List A → List A → Set where
  nil : Perm [] []
  skip : ∀ {x xs ys} → Perm xs ys → Perm (x ∷ xs) (x ∷ ys)
  swap : ∀ {x y xs} → Perm (x ∷ y ∷ xs) (y ∷ x ∷ xs)
  chain : ∀ {xs ys zs} → Perm xs ys → Perm ys zs → Perm xs zs

perm-refl : ∀ {A : Set} (xs : List A) → Perm xs xs
perm-refl [] = nil
perm-refl (x ∷ xs) = skip (perm-refl xs)

perm-sym : ∀ {A : Set} {xs ys : List A} → Perm xs ys → Perm ys xs
perm-sym nil = nil
perm-sym (skip p) = skip (perm-sym p)
perm-sym swap = swap
perm-sym (chain p q) = chain (perm-sym q) (perm-sym p)

perm-map : ∀ {A B : Set} (f : A → B) {xs ys} → Perm xs ys → Perm (map f xs) (map f ys)
perm-map f nil = nil
perm-map f (skip p) = skip (perm-map f p)
perm-map f swap = swap
perm-map f (chain p q) = chain (perm-map f p) (perm-map f q)

-- An executable sequence of adjacent swaps. Concrete callers can provide
-- a finite schedule and let the kernel check the resulting list.
promote : ∀ {A : Set} → ℕ → List A → List A
promote zero xs = xs
promote (suc n) [] = []
promote (suc n) (x ∷ xs) with promote n xs
... | [] = x ∷ []
... | y ∷ ys = y ∷ x ∷ ys

perm-promote : ∀ {A : Set} n (xs : List A) → Perm xs (promote n xs)
perm-promote zero xs = perm-refl xs
perm-promote (suc n) [] = nil
perm-promote (suc n) (x ∷ xs) with promote n xs | perm-promote n xs
... | [] | p = skip p
... | y ∷ ys | p = chain (skip p) swap

reorder : ∀ {A : Set} → List ℕ → List A → List A
reorder [] xs = xs
reorder (n ∷ ns) xs with promote n xs
... | [] = []
... | x ∷ ys = x ∷ reorder ns ys

perm-reorder : ∀ {A : Set} ns (xs : List A) → Perm xs (reorder ns xs)
perm-reorder [] xs = perm-refl xs
perm-reorder (n ∷ ns) xs with promote n xs | perm-promote n xs
... | [] | p = p
... | x ∷ ys | p = chain p (skip (perm-reorder ns ys))
