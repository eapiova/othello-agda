{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Numeric references use a proved strict, well-founded order.
module Game.NatOrder where

open import Prelude
open import Agda.Builtin.Nat using (_<_)
import Game.Indexed as I

data Before : ℕ → ℕ → Set where
  zero-before : ∀ {n} → Before zero (suc n)
  suc-before : ∀ {m n} → Before m n → Before (suc m) (suc n)

before-sound : ∀ m n → (m < n) ≡ true → Before m n
before-sound zero zero ()
before-sound zero (suc n) e = zero-before
before-sound (suc m) zero ()
before-sound (suc m) (suc n) e = suc-before (before-sound m n e)

private
  zeroAcc : I.Acc Before zero
  zeroAcc = I.acc (λ { _ () })

  sucAcc : ∀ {n} → I.Acc Before n → I.Acc Before (suc n)
  sucAcc {n} (I.acc children) = I.acc preceding
    where
    preceding : ∀ m → Before m (suc n) → I.Acc Before m
    preceding zero zero-before = zeroAcc
    preceding (suc m) (suc-before p) = sucAcc (children m p)

wellFounded : ∀ n → I.Acc Before n
wellFounded zero = zeroAcc
wellFounded (suc n) = sucAcc (wellFounded n)

order : I.Order ℕ
order = record
  { _<_ = Before
  ; beforeB = _<_
  ; before-sound = before-sound
  ; wellFounded = wellFounded
  }
