{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Counting where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
import Othello.Finite as F
open F using (Fin; Vec; lookup; updateAt; tabulate; foldr)

count : ∀ {A : Set} {n : ℕ} → (A → ℕ) → Vec A n → ℕ
count f = foldr (λ x k → f x + k) zero

sum : ∀ {n} → Vec ℕ n → ℕ
sum = count (λ x → x)

+-suc : ∀ a b → a + suc b ≡ suc (a + b)
+-suc zero b = refl
+-suc (suc a) b = cong suc (+-suc a b)

private
  cong₂ : ∀ {A B C : Set} (f : A → B → C) {a a′ b b′} →
    a ≡ a′ → b ≡ b′ → f a b ≡ f a′ b′
  cong₂ f refl refl = refl

count-tabulate-cong : ∀ {n} (f g : Fin n → ℕ) →
  ((i : Fin n) → f i ≡ g i) → sum (tabulate f) ≡ sum (tabulate g)
count-tabulate-cong {zero} f g equal = refl
count-tabulate-cong {suc n} f g equal = cong₂ _+_ (equal F.zero)
  (count-tabulate-cong (λ i → f (F.suc i)) (λ i → g (F.suc i))
    (λ i → equal (F.suc i)))

sum-tabulate-cong : ∀ {n} (f g : Fin n → ℕ) →
  ((i : Fin n) → f i ≡ g i) → sum (tabulate f) ≡ sum (tabulate g)
sum-tabulate-cong = count-tabulate-cong

count-tabulate-lookup : ∀ {A : Set} {n} (f : A → ℕ) (xs : Vec A n) →
  sum (tabulate (λ i → f (lookup xs i))) ≡ count f xs
count-tabulate-lookup f F.[] = refl
count-tabulate-lookup f (x F.∷ xs) = cong (λ k → f x + k) (count-tabulate-lookup f xs)

sum-tabulate-lookup : ∀ {A : Set} {n} (f : A → ℕ) (xs : Vec A n) →
  sum (tabulate (λ i → f (lookup xs i))) ≡ count f xs
sum-tabulate-lookup = count-tabulate-lookup

replace-decreases : ∀ {A : Set} {n} (f : A → ℕ) (xs : Vec A n)
  (i : Fin n) (v : A) → suc (f v) ≡ f (lookup xs i) →
  suc (count f (updateAt xs i (λ _ → v))) ≡ count f xs
replace-decreases f (x F.∷ xs) F.zero v decrease =
  cong (λ k → k + count f xs) decrease
replace-decreases f (x F.∷ xs) (F.suc i) v decrease =
  trans (sym (+-suc (f x) (count f (updateAt xs i (λ _ → v)))))
    (cong (λ k → f x + k) (replace-decreases f xs i v decrease))

replace-increases : ∀ {A : Set} {n} (f : A → ℕ) (xs : Vec A n)
  (i : Fin n) (v : A) → f v ≡ suc (f (lookup xs i)) →
  count f (updateAt xs i (λ _ → v)) ≡ suc (count f xs)
replace-increases f (x F.∷ xs) F.zero v increase =
  cong (λ k → k + count f xs) increase
replace-increases f (x F.∷ xs) (F.suc i) v increase =
  trans (cong (λ k → f x + k) (replace-increases f xs i v increase))
    (+-suc (f x) (count f xs))

-- Lift an inner cell-count fact through an outer transformation of a row.
update-decreases : ∀ {A : Set} {n} (f : A → ℕ) (xs : Vec A n)
  (i : Fin n) (change : A → A) →
  suc (f (change (lookup xs i))) ≡ f (lookup xs i) →
  suc (count f (updateAt xs i change)) ≡ count f xs
update-decreases f (x F.∷ xs) F.zero change decrease =
  cong (λ k → k + count f xs) decrease
update-decreases f (x F.∷ xs) (F.suc i) change decrease =
  trans (sym (+-suc (f x) (count f (updateAt xs i change))))
    (cong (λ k → f x + k) (update-decreases f xs i change decrease))

update-increases : ∀ {A : Set} {n} (f : A → ℕ) (xs : Vec A n)
  (i : Fin n) (change : A → A) →
  f (change (lookup xs i)) ≡ suc (f (lookup xs i)) →
  count f (updateAt xs i change) ≡ suc (count f xs)
update-increases f (x F.∷ xs) F.zero change increase =
  cong (λ k → k + count f xs) increase
update-increases f (x F.∷ xs) (F.suc i) change increase =
  trans (cong (λ k → f x + k) (update-increases f xs i change increase))
    (+-suc (f x) (count f xs))
