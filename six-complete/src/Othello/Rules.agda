{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Rules where

open import Prelude
open import Agda.Builtin.Nat renaming (_==_ to _≡ᵇ_)
open import Othello.Finite as Fin using (Fin; toℕ)
open import Othello.Finite as Vec using (allFin; toList; tabulate)

concatMap : ∀ {A B : Set} → (A → List B) → List A → List B
concatMap f [] = []
concatMap f (x ∷ xs) = f x ++ concatMap f xs

open import Othello.Board public
open import Game.Core using (Game)

natFin : (n m : ℕ) → Maybe (Fin n)
natFin zero m = nothing
natFin (suc n) zero = just Fin.zero
natFin (suc n) (suc m) with natFin n m
... | nothing = nothing
... | just i = just (Fin.suc i)

data Delta : Set where
  down same up : Delta

data Direction : Set where
  north northEast east southEast south southWest west northWest : Direction

deltas : Direction → Delta × Delta
deltas north = up , same
deltas northEast = up , down
deltas east = same , down
deltas southEast = down , down
deltas south = down , same
deltas southWest = down , up
deltas west = same , up
deltas northWest = up , up

directions : List Direction
directions = north ∷ northEast ∷ east ∷ southEast ∷ south ∷ southWest ∷ west ∷ northWest ∷ []

axis : ∀ {n} → Delta → Fin n → Maybe (Fin n)
axis same i = just i
axis {n} down i = natFin n (suc (toℕ i))
axis up Fin.zero = nothing
axis {n} up (Fin.suc i) = natFin n (toℕ i)

step : ∀ {size} → Direction → Coord size → Maybe (Coord size)
step d (r , c) with axis (proj₁ (deltas d)) r | axis (proj₂ (deltas d)) c
... | just r′ | just c′ = just (r′ , c′)
... | _ | _ = nothing

-- Fuel is the board dimension: a straight ray has at most n - 1 squares.
rayFrom : ∀ {size} → ℕ → Direction → Coord size → List (Coord size)
rayFrom zero d q = []
rayFrom (suc n) d q with step d q
... | nothing = []
... | just q′ = q′ ∷ rayFrom n d q′

ray : ∀ {size} → Direction → Coord size → List (Coord size)
ray {size} = rayFrom (dimension size)

-- A tail succeeds exactly when zero or more opponents end at a friendly disc.
prependCapture : ∀ {size} → Coord size → Maybe (List (Coord size)) → Maybe (List (Coord size))
prependCapture q nothing = nothing
prependCapture q (just xs) = just (q ∷ xs)

scanStep : ∀ {size} → Player → Coord size → Cell → Maybe (List (Coord size)) → Maybe (List (Coord size))
scanStep p q empty tail = nothing
scanStep black q blackCell tail = just []
scanStep white q whiteCell tail = just []
scanStep black q whiteCell tail = prependCapture q tail
scanStep white q blackCell tail = prependCapture q tail

scan : ∀ {size} → Board size → Player → List (Coord size) → Maybe (List (Coord size))
scan b p [] = nothing
scan b p (q ∷ qs) = scanStep p q (at b q) (scan b p qs)

captures : ∀ {size} → Board size → Player → Direction → Coord size → List (Coord size)
captures b p d q with ray d q
... | [] = []
... | r ∷ rs with sameCell (at b r) (playerCell (other p))
... | false = []
... | true with scan b p rs
... | nothing = []
... | just xs = r ∷ xs

allCaptures : ∀ {size} → State size → Coord size → List (Coord size)
allCaptures s q = concatMap (λ d → captures (board s) (toMove s) d q) directions

nonempty : ∀ {A : Set} → List A → Bool
nonempty [] = false
nonempty (_ ∷ _) = true

legal : ∀ {size} → State size → Coord size → Bool
legal s q = sameCell (at (board s) q) empty ∧ nonempty (allCaptures s q)

coords : (size : Size) → List (Coord size)
coords size = concatMap (λ r → map (λ c → r , c) (toList (allFin (dimension size))))
  (toList (allFin (dimension size)))

select : ∀ {A : Set} → (A → Bool) → List A → List A
select f [] = []
select f (x ∷ xs) with f x
... | false = select f xs
... | true = x ∷ select f xs

legalMoves : ∀ {size} → State size → List (Coord size)
legalMoves {size} s = select (legal s) (coords size)

sameCoord : ∀ {size} → Coord size → Coord size → Bool
sameCoord (r , c) (r′ , c′) = (toℕ r ≡ᵇ toℕ r′) ∧ (toℕ c ≡ᵇ toℕ c′)

contains : ∀ {size} → Coord size → List (Coord size) → Bool
contains q [] = false
contains q (r ∷ rs) = sameCoord q r ∨ contains q rs

recolour : ∀ {size} → Player → List (Coord size) → Coord size → Cell → Cell
recolour p xs q empty = empty
recolour p xs q blackCell with contains q xs
... | false = blackCell
... | true = playerCell p
recolour p xs q whiteCell with contains q xs
... | false = whiteCell
... | true = playerCell p

flippedBoard : ∀ {size} → State size → Coord size → Board size
flippedBoard s q = tabulate (λ r → tabulate (λ c →
  recolour (toMove s) (allCaptures s q) (r , c) (at (board s) (r , c))))

-- Illegal input is a no-op. Legal inputs flip all rays using the original board.
applyMove : ∀ {size} → State size → Coord size → State size
applyMove s q with legal s q
... | false = s
... | true = state (put (flippedBoard s q) q (playerCell (toMove s))) (other (toMove s))

passState : ∀ {size} → State size → State size
passState s = state (board s) (other (toMove s))

forcedPass : ∀ {size} → State size → Bool
forcedPass s with legalMoves s | legalMoves (passState s)
... | [] | [] = false
... | [] | (_ ∷ _) = true
... | (_ ∷ _) | _ = false

successors : ∀ {size} → State size → List (State size)
successors s with legalMoves s
... | q ∷ qs = map (applyMove s) (q ∷ qs)
... | [] with legalMoves (passState s)
... | [] = []
... | _ ∷ _ = passState s ∷ []

game : (size : Size) → Game (State size)
game size = record { turn = toMove ; next = successors ; forcedPass = forcedPass }
