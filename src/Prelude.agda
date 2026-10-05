{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Prelude where

open import Agda.Primitive public using (Level; _⊔_; lzero; lsuc)
open import Agda.Builtin.Bool public using (Bool; true; false)
open import Agda.Builtin.Nat public using (zero; suc) renaming (Nat to ℕ)
open import Agda.Builtin.List public using (List; []; _∷_)
open import Agda.Builtin.Maybe public using (Maybe; just; nothing)
open import Agda.Builtin.Sigma public using (Σ; _,_) renaming (fst to proj₁; snd to proj₂)
open import Agda.Builtin.Equality public using (_≡_; refl)
open import Agda.Builtin.Unit public using (⊤; tt)

infixr 2 _×_
_×_ : ∀ {a b} → Set a → Set b → Set (a ⊔ b)
A × B = Σ A (λ _ → B)

sym : ∀ {a} {A : Set a} {x y : A} → x ≡ y → y ≡ x
sym refl = refl

trans : ∀ {a} {A : Set a} {x y z : A} → x ≡ y → y ≡ z → x ≡ z
trans refl q = q

cong : ∀ {a b} {A : Set a} {B : Set b} (f : A → B) {x y} → x ≡ y → f x ≡ f y
cong f refl = refl

subst : ∀ {a b} {A : Set a} (P : A → Set b) {x y} → x ≡ y → P x → P y
subst P refl px = px

infixr 6 _∧_
_∧_ : Bool → Bool → Bool
true ∧ b = b
false ∧ b = false

infixr 5 _++_
_++_ : ∀ {a} {A : Set a} → List A → List A → List A
[] ++ ys = ys
(x ∷ xs) ++ ys = x ∷ (xs ++ ys)

map : ∀ {a b} {A : Set a} {B : Set b} → (A → B) → List A → List B
map f [] = []
map f (x ∷ xs) = f x ∷ map f xs

fromMaybe : ∀ {a} {A : Set a} → A → Maybe A → A
fromMaybe fallback nothing = fallback
fromMaybe fallback (just x) = x
