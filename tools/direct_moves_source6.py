"""AI-assisted source-only generator; safe Agda must check every theorem."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def generate():
    def fin(n):
        return 'F.zero' if n==0 else '(F.suc '+fin(n-1)+')'
    source='''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted directed legal moves. No initial-board bound is supplied.
module Othello.DirectMoves6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (coords; passState; nonempty)
open import Game.Core using (lookup)
import Othello.Finite as F
import Othello.Fast6 as Fast
import Othello.Incremental6 as Inc
import Othello.Specialized6 as New
import Game.DirectedIndexed as Directed

capturesAt : State six → Coord six → List (Coord six)
'''
    for r in range(6):
        for c in range(6):
            source+=f'capturesAt (state b p) ({fin(r)} , {fin(c)}) = New.capturesq{r}{c} b p\n'
    source+='\ncapturesAt-correct : ∀ s q → capturesAt s q ≡ Fast.allCaptures6 s q\n'
    for r in range(6):
        for c in range(6):
            source+=f'capturesAt-correct (state b p) ({fin(r)} , {fin(c)}) = New.capturesq{r}{c}-correct b p\n'
    source+='''
pickWith : State six → Coord six → List (Coord six) → Maybe (State six)
pickWith s q caps with sameCell (at {six} (board s) q) empty ∧ nonempty caps
... | false = nothing
... | true = just (state (put {six} (Inc.flipMany (board s) (toMove s) caps) q (playerCell (toMove s)))
  (other (toMove s)))

pick : State six → Coord six → Maybe (State six)
pick s q = pickWith s q (capturesAt s q)

pick-agrees : ∀ s q → pick s q ≡ pickWith s q (Fast.allCaptures6 s q)
pick-agrees s q = cong (pickWith s q) (capturesAt-correct s q)

prepend : Maybe (State six) → List (State six) → List (State six)
prepend nothing tail = tail
prepend (just s) tail = s ∷ tail

candidate-pick : ∀ s q caps tail →
  Inc.candidate s q caps tail ≡ prepend (pickWith s q caps) tail
candidate-pick s q caps tail with sameCell (at {six} (board s) q) empty ∧ nonempty caps
... | false = refl
... | true = refl

pickList : State six → List (Coord six) → List (State six)
pickList s [] = []
pickList s (q ∷ qs) = prepend (pick s q) (pickList s qs)

pickList-agrees : ∀ s qs → pickList s qs ≡ Inc.moves s qs
pickList-agrees s [] = refl
pickList-agrees s (q ∷ qs) rewrite pick-agrees s q | pickList-agrees s qs =
  sym (candidate-pick s q (Fast.allCaptures6 s q) (Inc.moves s qs))

data Member {A : Set} (x : A) : List A → Set where
  here : ∀ {xs} → Member x (x ∷ xs)
  there : ∀ {y xs} → Member x xs → Member x (y ∷ xs)

everyCoord : ∀ q → Member q (coords six)
'''
    for r in range(6):
        for c in range(6):
            proof='here'
            for _ in range(6*r+c):proof='there ('+proof+')'
            source+=f'everyCoord ({fin(r)} , {fin(c)}) = {proof}\n'
    source+='''
pickList-hit : ∀ s q qs t → Member q qs → pick s q ≡ just t →
  Σ ℕ (λ i → lookup (pickList s qs) i ≡ just t)
pickList-hit s q (.q ∷ qs) t here checked rewrite checked = zero , refl
pickList-hit s q (x ∷ qs) t (there member) checked with pick s x
... | nothing = pickList-hit s q qs t member checked
... | just u with pickList-hit s q qs t member checked
...   | i , hit = suc i , hit

moves-hit : ∀ s q t → pick s q ≡ just t →
  Σ ℕ (λ i → lookup (Inc.moves s (coords six)) i ≡ just t)
moves-hit s q t checked with pickList-hit s q (coords six) t (everyCoord q) checked
... | i , hit = i , trans
  (cong (λ ss → lookup ss i) (sym (pickList-agrees s (coords six)))) hit

finish-hit : ∀ s ss opposing i t → lookup ss i ≡ just t →
  lookup (Fast.finish6 s ss opposing) i ≡ just t
finish-hit s [] opposing i t ()
finish-hit s (x ∷ xs) opposing i t hit = hit

pick-sound : ∀ s q t → pick s q ≡ just t →
  Σ ℕ (λ i → lookup (New.successors s) i ≡ just t)
pick-sound s q t checked with moves-hit s q t checked
... | i , hit = i , trans
  (cong (λ ss → lookup ss i)
    (trans (New.successors-agree s) (sym (Inc.successors-agree s))))
  (finish-hit s (Inc.moves s (coords six)) (Inc.moves (passState s) (coords six)) i t hit)

picker : Directed.MovePicker New.specializedGame6 (Coord six)
picker = Directed.movePicker pick pick-sound
'''
    (ROOT/'src/Othello/DirectMoves6.agda').write_text(source)


if __name__=='__main__':
    generate()
