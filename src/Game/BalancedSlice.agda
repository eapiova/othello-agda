{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Slicing splits checking work while retaining every original ID.
module Game.BalancedSlice where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
import Game.Balanced as B

prefix : ∀ {n m} → B.Fin n → B.Fin (n + m)
prefix B.fzero = B.fzero
prefix (B.fsuc i) = B.fsuc (prefix i)

suffix : (n : ℕ) → ∀ {m} → B.Fin m → B.Fin (n + m)
suffix zero i = i
suffix (suc n) i = B.fsuc (suffix n i)

data Split (n m : ℕ) (i : B.Fin (n + m)) : Set where
  in-prefix : (j : B.Fin n) → i ≡ prefix j → Split n m i
  in-suffix : (j : B.Fin m) → i ≡ suffix n j → Split n m i

split : (n m : ℕ) (i : B.Fin (n + m)) → Split n m i
split zero m i = in-suffix i refl
split (suc n) m B.fzero = in-prefix B.fzero refl
split (suc n) m (B.fsuc i) with split n m i
... | in-prefix j e = in-prefix (B.fsuc j) (cong B.fsuc e)
... | in-suffix j e = in-suffix j (cong B.fsuc e)

combine : ∀ {n m} (P : B.Fin (n + m) → Set) →
  (∀ i → P (prefix i)) → (∀ i → P (suffix n i)) → ∀ i → P i
combine {n} {m} P first second i with split n m i
... | in-prefix j e = subst P (sym e) (first j)
... | in-suffix j e = subst P (sym e) (second j)

take : ∀ {A : Set} (n : ℕ) {m} → B.Vec A (n + m) → B.Vec A n
take zero xs = B.nil
take (suc n) (B.cons x xs) = B.cons x (take n xs)

drop : ∀ {A : Set} (n : ℕ) {m} → B.Vec A (n + m) → B.Vec A m
drop zero xs = xs
drop (suc n) (B.cons x xs) = drop n xs

lookup-take : ∀ {A : Set} (n : ℕ) {m} (xs : B.Vec A (n + m)) i →
  B.lookupVec xs (prefix i) ≡ B.lookupVec (take n xs) i
lookup-take zero xs ()
lookup-take (suc n) (B.cons x xs) B.fzero = refl
lookup-take (suc n) (B.cons x xs) (B.fsuc i) = lookup-take n xs i

lookup-drop : ∀ {A : Set} (n : ℕ) {m} (xs : B.Vec A (n + m)) i →
  B.lookupVec xs (suffix n i) ≡ B.lookupVec (drop n xs) i
lookup-drop zero xs i = refl
lookup-drop (suc n) (B.cons x xs) i = lookup-drop n xs i
