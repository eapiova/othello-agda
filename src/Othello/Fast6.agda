{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Fast6 where

open import Prelude
open import Agda.Builtin.Nat renaming (_==_ to _≡ᵇ_)
open import Othello.Rules hiding (forcedPass)
import Othello.Rules as Rules
import Othello.Finite as F
open import Othello.Rays6
import Game.Core as G

-- Compare finite indices directly, avoiding conversion to unary naturals.
finEqual : ∀ {n} → F.Fin n → F.Fin n → Bool
finEqual F.zero F.zero = true
finEqual F.zero (F.suc j) = false
finEqual (F.suc i) F.zero = false
finEqual (F.suc i) (F.suc j) = finEqual i j

finEqual-correct : ∀ {n} (i j : F.Fin n) → finEqual i j ≡ (F.toℕ i ≡ᵇ F.toℕ j)
finEqual-correct F.zero F.zero = refl
finEqual-correct F.zero (F.suc j) = refl
finEqual-correct (F.suc i) F.zero = refl
finEqual-correct (F.suc i) (F.suc j) = finEqual-correct i j

sameCoord6 : Coord six → Coord six → Bool
sameCoord6 (r , c) (r′ , c′) = finEqual r r′ ∧ finEqual c c′

sameCoord6-correct : ∀ q r → sameCoord6 q r ≡ sameCoord {six} q r
sameCoord6-correct (r , c) (r′ , c′)
  rewrite finEqual-correct r r′ | finEqual-correct c c′ = refl

contains6 : Coord six → List (Coord six) → Bool
contains6 q [] = false
contains6 q (r ∷ rs) = sameCoord6 q r ∨ contains6 q rs

contains6-correct : ∀ q xs → contains6 q xs ≡ contains {six} q xs
contains6-correct q [] = refl
contains6-correct q (r ∷ rs)
  rewrite sameCoord6-correct q r | contains6-correct q rs = refl

recolour6 : Player → List (Coord six) → Coord six → Cell → Cell
recolour6 p xs q empty = empty
recolour6 p xs q blackCell with contains6 q xs
... | false = blackCell
... | true = playerCell p
recolour6 p xs q whiteCell with contains6 q xs
... | false = whiteCell
... | true = playerCell p

recolour6-correct : ∀ p xs q c → recolour6 p xs q c ≡ recolour {six} p xs q c
recolour6-correct p xs q empty = refl
recolour6-correct p xs q blackCell rewrite contains6-correct q xs with contains {six} q xs
... | false = refl
... | true = refl
recolour6-correct p xs q whiteCell rewrite contains6-correct q xs with contains {six} q xs
... | false = refl
... | true = refl

capturesOn : Board six → Player → List (Coord six) → List (Coord six)
capturesOn b p [] = []
capturesOn b p (r ∷ rs) with sameCell (at {six} b r) (playerCell (other p))
... | false = []
... | true with scan {six} b p rs
... | nothing = []
... | just xs = r ∷ xs

capturesOn-correct : (b : Board six) (p : Player) (d : Direction) (q : Coord six) → capturesOn b p (ray {six} d q) ≡ captures {six} b p d q
capturesOn-correct b p d q with ray {six} d q
... | [] = refl
... | r ∷ rs with sameCell (at {six} b r) (playerCell (other p))
... | false = refl
... | true with scan {six} b p rs
... | nothing = refl
... | just xs = refl

captures6 : Board six → Player → Direction → Coord six → List (Coord six)
captures6 b p d q = capturesOn b p (ray6 d q)

captures6-correct : ∀ b p d q → captures6 b p d q ≡ captures {six} b p d q
captures6-correct b p d q rewrite ray6-correct d q = capturesOn-correct b p d q

concatMap-cong : ∀ {A B : Set} (f g : A → List B) →
  (∀ x → f x ≡ g x) → ∀ xs → concatMap f xs ≡ concatMap g xs
concatMap-cong f g e [] = refl
concatMap-cong f g e (x ∷ xs) rewrite e x | concatMap-cong f g e xs = refl

allCaptures6 : State six → Coord six → List (Coord six)
allCaptures6 s q = concatMap (λ d → captures6 (board s) (toMove s) d q) directions

allCaptures6-correct : ∀ s q → allCaptures6 s q ≡ allCaptures s q
allCaptures6-correct s q = concatMap-cong _ _
  (λ d → captures6-correct (board s) (toMove s) d q) directions

tabulate-cong : ∀ {A : Set} {n} (f g : F.Fin n → A) →
  (∀ i → f i ≡ g i) → F.tabulate f ≡ F.tabulate g
tabulate-cong {n = zero} f g e = refl
tabulate-cong {n = suc n} f g e rewrite e F.zero |
  tabulate-cong (λ i → f (F.suc i)) (λ i → g (F.suc i)) (λ i → e (F.suc i)) = refl

-- xs is a real helper argument, shared before entering either tabulation.
flippedCaptured6 : State six → List (Coord six) → Board six
flippedCaptured6 s xs = F.tabulate (λ r → F.tabulate (λ c →
  recolour6 (toMove s) xs (r , c) (at {six} (board s) (r , c))))

flippedCaptured6-correct : ∀ s q → flippedCaptured6 s (allCaptures s q) ≡ flippedBoard s q
flippedCaptured6-correct s q = tabulate-cong _ _ (λ r →
  tabulate-cong _ _ (λ c → recolour6-correct (toMove s) (allCaptures s q)
    (r , c) (at {six} (board s) (r , c))))

-- The candidate receives one capture list and uses it for legality and flips.
candidate6 : State six → Coord six → List (Coord six) → List (State six) → List (State six)
candidate6 s q xs tail with sameCell (at {six} (board s) q) empty ∧ nonempty xs
... | false = tail
... | true = state (put {six} (flippedCaptured6 s xs) q (playerCell (toMove s)))
  (other (toMove s)) ∷ tail

candidateSpec : State six → Coord six → List (State six) → List (State six)
candidateSpec s q tail with legal s q
... | false = tail
... | true = applyMove s q ∷ tail

candidate6-correct : ∀ s q tail →
  candidate6 s q (allCaptures6 s q) tail ≡ candidateSpec s q tail
candidate6-correct s q tail rewrite allCaptures6-correct s q with legal s q in eq
... | false = refl
... | true rewrite eq | flippedCaptured6-correct s q = refl

moves6 : State six → List (Coord six) → List (State six)
moves6 s [] = []
moves6 s (q ∷ qs) = candidate6 s q (allCaptures6 s q) (moves6 s qs)

movesSpec-step : ∀ s q qs →
  candidateSpec s q (map (applyMove s) (select (legal s) qs)) ≡
  map (applyMove s) (select (legal s) (q ∷ qs))
movesSpec-step s q qs with legal s q
... | false = refl
... | true = refl

moves6-correct : ∀ s qs → moves6 s qs ≡ map (applyMove s) (select (legal s) qs)
moves6-correct s [] = refl
moves6-correct s (q ∷ qs) rewrite moves6-correct s qs =
  trans (candidate6-correct s q _) (movesSpec-step s q qs)

finish6 : State six → List (State six) → List (State six) → List (State six)
finish6 s (x ∷ xs) opposing = x ∷ xs
finish6 s [] [] = []
finish6 s [] (x ∷ xs) = passState s ∷ []

fastSuccessors : State six → List (State six)
fastSuccessors s = finish6 s (moves6 s (coords six)) (moves6 (passState s) (coords six))

finish6-correct : ∀ s → finish6 s (map (applyMove s) (legalMoves s))
  (map (applyMove (passState s)) (legalMoves (passState s))) ≡ successors s
finish6-correct s with legalMoves s
... | q ∷ qs = refl
... | [] with legalMoves (passState s)
... | [] = refl
... | q ∷ qs = refl

successors6-correct : ∀ s → fastSuccessors s ≡ Rules.successors s
successors6-correct s rewrite moves6-correct s (coords six) |
  moves6-correct (passState s) (coords six) = finish6-correct s

fastGame6 : G.Game (State six)
fastGame6 = record { turn = toMove ; next = fastSuccessors ; forcedPass = Rules.forcedPass }

next6-correct : ∀ s → G.next fastGame6 s ≡ G.next (game six) s
next6-correct = successors6-correct

turn6-correct : ∀ s → G.turn fastGame6 s ≡ G.turn (game six) s
turn6-correct s = refl

forcedPass6-correct : ∀ s → G.forcedPass fastGame6 s ≡ G.forcedPass (game six) s
forcedPass6-correct s = refl
