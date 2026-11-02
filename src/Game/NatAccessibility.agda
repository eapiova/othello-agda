{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.NatAccessibility where
open import Prelude
import Game.Indexed as I
import Game.NatOrder as N
zeroAcc : I.Acc N.Before zero
zeroAcc = N.wellFounded zero
mutual
  raise : ∀ {n} → I.Acc N.Before n → I.Acc N.Before (suc n)
  raise smaller = I.acc (previous smaller)
  previous : ∀ {n} → I.Acc N.Before n → ∀ m → N.Before m (suc n) → I.Acc N.Before m
  previous smaller zero N.zero-before = zeroAcc
  previous (I.acc children) (suc m) (N.suc-before p) = raise (children m p)
wellFounded : ∀ n → I.Acc N.Before n
wellFounded zero = zeroAcc
wellFounded (suc n) = raise (wellFounded n)
zeroFrom : ∀ {n} → I.Acc N.Before (suc n) → I.Acc N.Before zero
zeroFrom (I.acc children) = children zero N.zero-before
