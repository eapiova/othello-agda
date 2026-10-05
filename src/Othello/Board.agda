{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Board where

open import Prelude
open import Agda.Builtin.Nat using (_+_) renaming (_==_ to _≡ᵇ_)
open import Agda.Builtin.Int using (pos; negsuc) renaming (Int to ℤ)
open import Othello.Finite as Vec using (Fin; toℕ; Vec; tabulate; lookup; updateAt; foldr)

infixr 5 _∨_
_∨_ : Bool → Bool → Bool
true ∨ b = true
false ∨ b = b

signedDifference : ℕ → ℕ → ℤ
signedDifference n zero = pos n
signedDifference zero (suc n) = negsuc n
signedDifference (suc m) (suc n) = signedDifference m n

open import Game.Player public

data Size : Set where
  four six eight : Size

dimension : Size → ℕ
dimension four = 4
dimension six = 6
dimension eight = 8

data Cell : Set where
  empty blackCell whiteCell : Cell

playerCell : Player → Cell
playerCell black = blackCell
playerCell white = whiteCell

sameCell : Cell → Cell → Bool
sameCell empty empty = true
sameCell blackCell blackCell = true
sameCell whiteCell whiteCell = true
sameCell _ _ = false

Board : Size → Set
Board size = Vec (Vec Cell (dimension size)) (dimension size)

Coord : Size → Set
Coord size = Fin (dimension size) × Fin (dimension size)

record State (size : Size) : Set where
  constructor state
  field
    board : Board size
    toMove : Player
open State public

at : ∀ {size} → Board size → Coord size → Cell
at b (r , c) = lookup (lookup b r) c

put : ∀ {size} → Board size → Coord size → Cell → Board size
put b (r , c) v = updateAt b r (λ row → updateAt row c (λ _ → v))

centre : Size → ℕ
centre four = 1
centre six = 2
centre eight = 3

initialCell : (size : Size) → Coord size → Cell
initialCell size (r , c) with
  ((toℕ r ≡ᵇ centre size) ∧ (toℕ c ≡ᵇ centre size)) ∨
  ((toℕ r ≡ᵇ suc (centre size)) ∧ (toℕ c ≡ᵇ suc (centre size)))
... | true = whiteCell
... | false with
  ((toℕ r ≡ᵇ centre size) ∧ (toℕ c ≡ᵇ suc (centre size))) ∨
  ((toℕ r ≡ᵇ suc (centre size)) ∧ (toℕ c ≡ᵇ centre size))
... | true = blackCell
... | false = empty

initial : (size : Size) → State size
initial size = state (tabulate (λ r → tabulate (λ c → initialCell size (r , c)))) black

indicator : Bool → ℕ
indicator false = 0
indicator true = 1

countBoard : ∀ {size} → (Cell → ℕ) → Board size → ℕ
countBoard f = foldr (λ row n → foldr (λ c m → f c + m) 0 row + n) 0

discs : ∀ {size} → Player → State size → ℕ
discs p s = countBoard (λ c → indicator (sameCell c (playerCell p))) (board s)

score : ∀ {size} → State size → ℤ
score s = signedDifference (discs white s) (discs black s)

emptyCell : Cell → ℕ
emptyCell empty = 1
emptyCell blackCell = 0
emptyCell whiteCell = 0

empties : ∀ {size} → State size → ℕ
empties s = countBoard emptyCell (board s)

occupiedCell : Cell → ℕ
occupiedCell empty = 0
occupiedCell blackCell = 1
occupiedCell whiteCell = 1

occupied : ∀ {size} → State size → ℕ
occupied s = countBoard occupiedCell (board s)
