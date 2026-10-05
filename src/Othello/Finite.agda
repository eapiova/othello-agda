{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Finite where

open import Agda.Builtin.Nat using (Nat) renaming (zero to zeroᴺ; suc to sucᴺ)
open import Agda.Builtin.Equality using (_≡_; refl)
import Agda.Builtin.List as L

data Fin : Nat → Set where
  zero : ∀ {n} → Fin (sucᴺ n)
  suc : ∀ {n} → Fin n → Fin (sucᴺ n)

toℕ : ∀ {n} → Fin n → Nat
toℕ zero = zeroᴺ
toℕ (suc i) = sucᴺ (toℕ i)

infixr 5 _∷_
data Vec (A : Set) : Nat → Set where
  [] : Vec A zeroᴺ
  _∷_ : ∀ {n} → A → Vec A n → Vec A (sucᴺ n)

lookup : ∀ {A : Set} {n : Nat} → Vec A n → Fin n → A
lookup (x ∷ xs) zero = x
lookup (x ∷ xs) (suc i) = lookup xs i

updateAt : ∀ {A : Set} {n : Nat} → Vec A n → Fin n → (A → A) → Vec A n
updateAt (x ∷ xs) zero f = f x ∷ xs
updateAt (x ∷ xs) (suc i) f = x ∷ updateAt xs i f

tabulate : ∀ {A : Set} {n : Nat} → (Fin n → A) → Vec A n
tabulate {n = zeroᴺ} f = []
tabulate {n = sucᴺ n} f = f zero ∷ tabulate (λ i → f (suc i))

foldr : ∀ {A B : Set} {n : Nat} → (A → B → B) → B → Vec A n → B
foldr f z [] = z
foldr f z (x ∷ xs) = f x (foldr f z xs)

toList : ∀ {A : Set} {n : Nat} → Vec A n → L.List A
toList [] = L.[]
toList (x ∷ xs) = x L.∷ toList xs

allFin : (n : Nat) → Vec (Fin n) n
allFin n = tabulate (λ i → i)

private
  cong : ∀ {A B : Set} (f : A → B) {x y} → x ≡ y → f x ≡ f y
  cong f refl = refl

lookup-tabulate : ∀ {A : Set} {n : Nat} (f : Fin n → A) (i : Fin n) → lookup (tabulate f) i ≡ f i
lookup-tabulate f zero = refl
lookup-tabulate f (suc i) = lookup-tabulate (λ j → f (suc j)) i

tabulate-lookup : ∀ {A : Set} {n : Nat} (xs : Vec A n) → tabulate (lookup xs) ≡ xs
tabulate-lookup [] = refl
tabulate-lookup (x ∷ xs) = cong (λ ys → x ∷ ys) (tabulate-lookup xs)

lookup-update-self : ∀ {A : Set} {n : Nat} (xs : Vec A n) (i : Fin n) (f : A → A) →
  lookup (updateAt xs i f) i ≡ f (lookup xs i)
lookup-update-self (x ∷ xs) zero f = refl
lookup-update-self (x ∷ xs) (suc i) f = lookup-update-self xs i f
