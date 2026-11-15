{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Incremental capture updates, with arbitrary-board agreement.
-- This module supplies no initial-board bound.
module Othello.Incremental6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (coords; passState; nonempty)
import Othello.Rules as Rules
import Othello.Fast6 as Fast
import Othello.Finite as F
import Othello.Symmetry6 as S
import Game.Core as G
import Game.Transfer as T

private
  change : ∀ {A : Set} → Bool → (A → A) → A → A
  change false f x = x
  change true f x = f x

  lookup-update : ∀ {A : Set} {n} (xs : F.Vec A n) i j f →
    F.lookup (F.updateAt xs j f) i ≡ change (Fast.finEqual i j) f (F.lookup xs i)
  lookup-update (x F.∷ xs) F.zero F.zero f = refl
  lookup-update (x F.∷ xs) F.zero (F.suc j) f = refl
  lookup-update (x F.∷ xs) (F.suc i) F.zero f = refl
  lookup-update (x F.∷ xs) (F.suc i) (F.suc j) f = lookup-update xs i j f

  mark : Player → Cell → Cell
  mark p empty = empty
  mark p blackCell = playerCell p
  mark p whiteCell = playerCell p

  mark-idempotent : ∀ p c → mark p (mark p c) ≡ mark p c
  mark-idempotent p empty = refl
  mark-idempotent black blackCell = refl
  mark-idempotent white blackCell = refl
  mark-idempotent black whiteCell = refl
  mark-idempotent white whiteCell = refl

modify : Board six → Coord six → (Cell → Cell) → Board six
modify b (r , c) f = F.updateAt b r (λ row → F.updateAt row c f)

private
  modify-at : ∀ b q t f →
    at {six} (modify b q f) t ≡ change (Fast.sameCoord6 t q) f (at {six} b t)
  modify-at b (r , c) (r′ , c′) f
    rewrite lookup-update b r′ r (λ row → F.updateAt row c f)
    with Fast.finEqual r′ r
  ... | false = refl
  ... | true = lookup-update (F.lookup b r′) c′ c f

-- Repeated coordinates are harmless: marking is idempotent. Empty cells stay
-- empty, so agreement does not depend on a capture-list validity premise.
flipMany : Board six → Player → List (Coord six) → Board six
flipMany b p [] = b
flipMany b p (q ∷ qs) = modify (flipMany b p qs) q (mark p)

private
  flipMany-at : ∀ b p xs q → at {six} (flipMany b p xs) q ≡
    change (Fast.contains6 q xs) (mark p) (at {six} b q)
  flipMany-at b p [] q = refl
  flipMany-at b p (r ∷ rs) q
    rewrite modify-at (flipMany b p rs) r q (mark p) | flipMany-at b p rs q
    with Fast.sameCoord6 q r | Fast.contains6 q rs
  ... | false | false = refl
  ... | false | true = refl
  ... | true | false = refl
  ... | true | true = mark-idempotent p (at {six} b q)

  change-recolour : ∀ p xs q c → change (Fast.contains6 q xs) (mark p) c ≡
    Fast.recolour6 p xs q c
  change-recolour p xs q empty with Fast.contains6 q xs
  ... | false = refl
  ... | true = refl
  change-recolour p xs q blackCell with Fast.contains6 q xs
  ... | false = refl
  ... | true = refl
  change-recolour p xs q whiteCell with Fast.contains6 q xs
  ... | false = refl
  ... | true = refl

  at-tabulate : ∀ (f : Coord six → Cell) q →
    at {six} (F.tabulate (λ r → F.tabulate (λ c → f (r , c)))) q ≡ f q
  at-tabulate f (r , c) = trans
    (cong (λ row → F.lookup row c)
      (F.lookup-tabulate (λ r → F.tabulate (λ c → f (r , c))) r))
    (F.lookup-tabulate (λ c → f (r , c)) c)

flips-agree : ∀ s xs → flipMany (board s) (toMove s) xs ≡ Fast.flippedCaptured6 s xs
flips-agree s xs = S.board-ext _ _ (λ q → trans
  (flipMany-at (board s) (toMove s) xs q)
  (trans (change-recolour (toMove s) xs q (at {six} (board s) q))
    (sym (at-tabulate (λ q → Fast.recolour6 (toMove s) xs q (at {six} (board s) q)) q))))

candidate : State six → Coord six → List (Coord six) → List (State six) → List (State six)
candidate s q xs tail with sameCell (at {six} (board s) q) empty ∧ nonempty xs
... | false = tail
... | true = state (put {six} (flipMany (board s) (toMove s) xs) q (playerCell (toMove s)))
  (other (toMove s)) ∷ tail

candidate-agrees : ∀ s q xs tail → candidate s q xs tail ≡ Fast.candidate6 s q xs tail
candidate-agrees s q xs tail with sameCell (at {six} (board s) q) empty ∧ nonempty xs
... | false = refl
... | true = cong (λ b → state (put {six} b q (playerCell (toMove s)))
  (other (toMove s)) ∷ tail) (flips-agree s xs)

moves : State six → List (Coord six) → List (State six)
moves s [] = []
moves s (q ∷ qs) = candidate s q (Fast.allCaptures6 s q) (moves s qs)

moves-agree : ∀ s qs → moves s qs ≡ Fast.moves6 s qs
moves-agree s [] = refl
moves-agree s (q ∷ qs) rewrite moves-agree s qs =
  candidate-agrees s q (Fast.allCaptures6 s q) (Fast.moves6 s qs)

successors : State six → List (State six)
successors s = Fast.finish6 s (moves s (coords six)) (moves (passState s) (coords six))

successors-agree : ∀ s → successors s ≡ Fast.fastSuccessors s
successors-agree s rewrite moves-agree s (coords six) | moves-agree (passState s) (coords six) = refl

incrementalGame6 : G.Game (State six)
incrementalGame6 = record { turn = toMove ; next = successors ; forcedPass = Rules.forcedPass }

agreement : T.Agreement incrementalGame6 Fast.fastGame6
agreement = T.agreement successors-agree (λ s → refl) (λ s → refl)
