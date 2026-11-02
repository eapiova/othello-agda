{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Six-cell rows retain both their cells and checked ternary code.
module Othello.CachedRow6 where

open import Prelude
open import Agda.Builtin.Nat using (_+_; _*_) renaming (_-_ to _∸_; _==_ to _≡ᵇ_)
open import Othello.Board using (Cell)
import Othello.Finite as F
import Othello.RowPacked6 as P
import Othello.RowArithmetic6 as R
import Othello.FiniteCheck6 as Q
import Game.BooleanRecompute as Recover

open R public using (power; cellCode)

record RowCache : Set where
  constructor rowCache
  field
    cells : P.Row
    code : ℕ
    .valid : P.encodeRow cells ≡ code
open RowCache public

pack : P.Row → RowCache
pack row = rowCache row (P.encodeRow row) refl

private
  nat-sound : ∀ m n → (m ≡ᵇ n) ≡ true → m ≡ n
  nat-sound zero zero checked = refl
  nat-sound zero (suc n) ()
  nat-sound (suc m) zero ()
  nat-sound (suc m) (suc n) checked = cong suc (nat-sound m n checked)

  nat-refl : ∀ n → (n ≡ᵇ n) ≡ true
  nat-refl zero = refl
  nat-refl (suc n) = nat-refl n

  module NatRecovery = Recover.Checking _≡ᵇ_ nat-sound nat-refl

cached-code : ∀ r → code r ≡ P.encodeRow (cells r)
cached-code (rowCache row n witness) = NatRecovery.recompute (sym witness)

injective : ∀ r t → cells r ≡ cells t → r ≡ t
injective r@(rowCache row n rn) t@(rowCache .row m tm) refl
  with trans (cached-code r) (sym (cached-code t))
... | refl = refl

knownReplace : ℕ → F.Fin 6 → Cell → Cell → ℕ
knownReplace n i old new =
  n ∸ (cellCode old * power i) + (cellCode new * power i)

private
  replaceCheck : P.Row → F.Fin 6 → Cell → Bool
  replaceCheck row i new =
    knownReplace (P.encodeRow row) i (F.lookup row i) new ≡ᵇ
    P.encodeRow (F.updateAt row i (λ _ → new))

  checks : P.Row → Bool
  checks row = Q.allFin 6 (λ i → Q.allCells (replaceCheck row i))

  abstract
    everyCase : Q.allRows 6 checks ≡ true
    everyCase = refl

  atColumn : ∀ row i → Q.allCells (replaceCheck row i) ≡ true
  atColumn row i = Q.allFin-sound 6
    (λ j → Q.allCells (replaceCheck row j))
    (Q.allRows-sound 6 checks everyCase row) i

abstract
  knownReplace-encode : ∀ row i new →
    knownReplace (P.encodeRow row) i (F.lookup row i) new ≡
    P.encodeRow (F.updateAt row i (λ _ → new))
  knownReplace-encode row i new = nat-sound
    (knownReplace (P.encodeRow row) i (F.lookup row i) new)
    (P.encodeRow (F.updateAt row i (λ _ → new)))
    (Q.allCells-sound (replaceCheck row i) (atColumn row i) new)

private
  update-value : ∀ {A : Set} {n} (xs : F.Vec A n) i (f : A → A) →
    F.updateAt xs i (λ _ → f (F.lookup xs i)) ≡ F.updateAt xs i f
  update-value (x F.∷ xs) F.zero f = refl
  update-value (x F.∷ xs) (F.suc i) f =
    cong (F._∷_ x) (update-value xs i f)

modify : RowCache → F.Fin 6 → (Cell → Cell) → RowCache
modify (rowCache row n witness) i f = rowCache
  (F.updateAt row i f)
  (knownReplace n i (F.lookup row i) (f (F.lookup row i)))
  (trans (cong P.encodeRow (sym (update-value row i f)))
    (trans (sym (knownReplace-encode row i (f (F.lookup row i))))
      (cong (λ k → knownReplace k i (F.lookup row i) (f (F.lookup row i)))
        witness)))

cells-modify : ∀ r i f →
  cells (modify r i f) ≡ F.updateAt (cells r) i f
cells-modify (rowCache row n witness) i f = refl
