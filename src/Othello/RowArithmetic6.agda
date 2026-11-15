{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted exhaustive proofs for arithmetic on packed 6-cell rows.
module Othello.RowArithmetic6 where

open import Prelude
open import Agda.Builtin.Nat
  using (_+_; _*_; div-helper; mod-helper)
  renaming (_-_ to _∸_)
open import Othello.Board
import Othello.Finite as F
import Othello.RowPacked6 as Packed

power : F.Fin 6 → ℕ
power F.zero = 1
power (F.suc F.zero) = 3
power (F.suc (F.suc F.zero)) = 9
power (F.suc (F.suc (F.suc F.zero))) = 27
power (F.suc (F.suc (F.suc (F.suc F.zero)))) = 81
power (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) = 243

cellCode : Cell → ℕ
cellCode empty = 0
cellCode blackCell = 1
cellCode whiteCell = 2

cell : ℕ → Cell
cell zero = empty
cell (suc zero) = blackCell
cell (suc (suc n)) = whiteCell

oldDigit : ℕ → F.Fin 6 → ℕ
oldDigit n i = mod-helper 0 2
  (div-helper 0 (power i ∸ 1) n (power i ∸ 1)) 2

read : ℕ → F.Fin 6 → Cell
read n i = cell (oldDigit n i)

replace : ℕ → F.Fin 6 → Cell → ℕ
replace n i c =
  (n ∸ (oldDigit n i * power i)) + (cellCode c * power i)

import Othello.FiniteCheck6 as Q
import Othello.Encode6 as E
open import Agda.Builtin.Nat using () renaming (_==_ to _≡ᵇ_)

private
  nat-sound : ∀ m n → (m ≡ᵇ n) ≡ true → m ≡ n
  nat-sound zero zero e = refl
  nat-sound zero (suc n) ()
  nat-sound (suc m) zero ()
  nat-sound (suc m) (suc n) e = cong suc (nat-sound m n e)

  readCheck : Packed.Row → F.Fin 6 → Bool
  readCheck row i = sameCell (read (Packed.encodeRow row) i) (F.lookup row i)

  replaceCheck : Packed.Row → F.Fin 6 → Cell → Bool
  replaceCheck row i c = replace (Packed.encodeRow row) i c ≡ᵇ
    Packed.encodeRow (F.updateAt row i (λ _ → c))

  checks : Packed.Row → Bool
  checks row = Q.allFin 6 (λ i → readCheck row i ∧ Q.allCells (replaceCheck row i))

  abstract
    everyCase : Q.allRows 6 checks ≡ true
    everyCase = refl

  atColumn : ∀ row i → readCheck row i ∧ Q.allCells (replaceCheck row i) ≡ true
  atColumn row i = Q.allFin-sound 6 (λ j → readCheck row j ∧ Q.allCells (replaceCheck row j))
    (Q.allRows-sound 6 checks everyCase row) i

abstract
  read-encode : ∀ (row : F.Vec Cell 6) (i : F.Fin 6) →
    read (Packed.encodeRow row) i ≡ F.lookup row i
  read-encode row i = E.sameCell-sound (read (Packed.encodeRow row) i) (F.lookup row i)
    (Q.left (readCheck row i) (Q.allCells (replaceCheck row i)) (atColumn row i))

  replace-encode : ∀ (row : F.Vec Cell 6) (i : F.Fin 6) (c : Cell) →
    replace (Packed.encodeRow row) i c ≡
    Packed.encodeRow (F.updateAt row i (λ _ → c))
  replace-encode row i c = nat-sound (replace (Packed.encodeRow row) i c)
    (Packed.encodeRow (F.updateAt row i (λ _ → c)))
    (Q.allCells-sound (replaceCheck row i)
      (Q.right (readCheck row i) (Q.allCells (replaceCheck row i)) (atColumn row i)) c)
