{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Exhaustive Boolean quantifiers with constructive soundness.
module Othello.FiniteCheck6 where

open import Prelude
open import Othello.Board using (Cell; empty; blackCell; whiteCell)
import Othello.Finite as F

left : ∀ a b → a ∧ b ≡ true → a ≡ true
left true b e = refl
left false b ()

right : ∀ a b → a ∧ b ≡ true → b ≡ true
right true b e = e
right false b ()

allCells : (Cell → Bool) → Bool
allCells f = f empty ∧ (f blackCell ∧ f whiteCell)

allCells-sound : ∀ f → allCells f ≡ true → ∀ c → f c ≡ true
allCells-sound f e empty = left (f empty) (f blackCell ∧ f whiteCell) e
allCells-sound f e blackCell = left (f blackCell) (f whiteCell)
  (right (f empty) (f blackCell ∧ f whiteCell) e)
allCells-sound f e whiteCell = right (f blackCell) (f whiteCell)
  (right (f empty) (f blackCell ∧ f whiteCell) e)

allFin : (n : ℕ) → (F.Fin n → Bool) → Bool
allFin zero f = true
allFin (suc n) f = f F.zero ∧ allFin n (λ i → f (F.suc i))

allFin-sound : ∀ n f → allFin n f ≡ true → ∀ i → f i ≡ true
allFin-sound (suc n) f e F.zero = left (f F.zero) (allFin n (λ i → f (F.suc i))) e
allFin-sound (suc n) f e (F.suc i) = allFin-sound n (λ j → f (F.suc j))
  (right (f F.zero) (allFin n (λ j → f (F.suc j))) e) i

allRows : (n : ℕ) → (F.Vec Cell n → Bool) → Bool
allRows zero f = f F.[]
allRows (suc n) f = allCells (λ c → allRows n (λ row → f (c F.∷ row)))

allRows-sound : ∀ n f → allRows n f ≡ true → ∀ row → f row ≡ true
allRows-sound zero f e F.[] = e
allRows-sound (suc n) f e (c F.∷ row) =
  allRows-sound n (λ tail → f (c F.∷ tail))
    (allCells-sound (λ d → allRows n (λ tail → f (d F.∷ tail))) e c) row
