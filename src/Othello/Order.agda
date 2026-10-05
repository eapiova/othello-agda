{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Order where

open import Prelude
open import Agda.Builtin.Nat public using (_+_)

infix 4 _≤_ _≤ᵇ_
data _≤_ : ℕ → ℕ → Set where
  z≤n : ∀ {n} → zero ≤ n
  s≤s : ∀ {m n} → m ≤ n → suc m ≤ suc n

_≤ᵇ_ : ℕ → ℕ → Bool
zero ≤ᵇ n = true
suc m ≤ᵇ zero = false
suc m ≤ᵇ suc n = m ≤ᵇ n

≤ᵇ-sound : ∀ {m n} → (m ≤ᵇ n) ≡ true → m ≤ n
≤ᵇ-sound {zero} e = z≤n
≤ᵇ-sound {suc m} {zero} ()
≤ᵇ-sound {suc m} {suc n} e = s≤s (≤ᵇ-sound e)

≤ᵇ-complete : ∀ {m n} → m ≤ n → (m ≤ᵇ n) ≡ true
≤ᵇ-complete z≤n = refl
≤ᵇ-complete (s≤s p) = ≤ᵇ-complete p

≤-refl : ∀ n → n ≤ n
≤-refl zero = z≤n
≤-refl (suc n) = s≤s (≤-refl n)

≤-trans : ∀ {a b c} → a ≤ b → b ≤ c → a ≤ c
≤-trans z≤n q = z≤n
≤-trans (s≤s p) (s≤s q) = s≤s (≤-trans p q)

≤-antisym : ∀ {a b} → a ≤ b → b ≤ a → a ≡ b
≤-antisym z≤n z≤n = refl
≤-antisym (s≤s p) (s≤s q) = cong suc (≤-antisym p q)

≤-cancel-left : ∀ a {b c} → a + b ≤ a + c → b ≤ c
≤-cancel-left zero p = p
≤-cancel-left (suc a) (s≤s p) = ≤-cancel-left a p

≤-add-left : ∀ a {b c} → b ≤ c → a + b ≤ a + c
≤-add-left zero p = p
≤-add-left (suc a) p = s≤s (≤-add-left a p)

one≤plus-eight : ∀ n → suc n ≤ n + 8
one≤plus-eight zero = s≤s z≤n
one≤plus-eight (suc n) = s≤s (one≤plus-eight n)
