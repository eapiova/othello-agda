{-# OPTIONS --safe --without-K --cubical-compatible #-}
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
capturesAt (state b p) (F.zero , F.zero) = New.capturesq00 b p
capturesAt (state b p) (F.zero , (F.suc F.zero)) = New.capturesq01 b p
capturesAt (state b p) (F.zero , (F.suc (F.suc F.zero))) = New.capturesq02 b p
capturesAt (state b p) (F.zero , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq03 b p
capturesAt (state b p) (F.zero , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq04 b p
capturesAt (state b p) (F.zero , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq05 b p
capturesAt (state b p) ((F.suc F.zero) , F.zero) = New.capturesq10 b p
capturesAt (state b p) ((F.suc F.zero) , (F.suc F.zero)) = New.capturesq11 b p
capturesAt (state b p) ((F.suc F.zero) , (F.suc (F.suc F.zero))) = New.capturesq12 b p
capturesAt (state b p) ((F.suc F.zero) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq13 b p
capturesAt (state b p) ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq14 b p
capturesAt (state b p) ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq15 b p
capturesAt (state b p) ((F.suc (F.suc F.zero)) , F.zero) = New.capturesq20 b p
capturesAt (state b p) ((F.suc (F.suc F.zero)) , (F.suc F.zero)) = New.capturesq21 b p
capturesAt (state b p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc F.zero))) = New.capturesq22 b p
capturesAt (state b p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq23 b p
capturesAt (state b p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq24 b p
capturesAt (state b p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq25 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc F.zero))) , F.zero) = New.capturesq30 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc F.zero)) = New.capturesq31 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc F.zero))) = New.capturesq32 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq33 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq34 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq35 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , F.zero) = New.capturesq40 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc F.zero)) = New.capturesq41 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc F.zero))) = New.capturesq42 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq43 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq44 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq45 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , F.zero) = New.capturesq50 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc F.zero)) = New.capturesq51 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc F.zero))) = New.capturesq52 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq53 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq54 b p
capturesAt (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq55 b p

capturesAt-correct : ∀ s q → capturesAt s q ≡ Fast.allCaptures6 s q
capturesAt-correct (state b p) (F.zero , F.zero) = New.capturesq00-correct b p
capturesAt-correct (state b p) (F.zero , (F.suc F.zero)) = New.capturesq01-correct b p
capturesAt-correct (state b p) (F.zero , (F.suc (F.suc F.zero))) = New.capturesq02-correct b p
capturesAt-correct (state b p) (F.zero , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq03-correct b p
capturesAt-correct (state b p) (F.zero , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq04-correct b p
capturesAt-correct (state b p) (F.zero , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq05-correct b p
capturesAt-correct (state b p) ((F.suc F.zero) , F.zero) = New.capturesq10-correct b p
capturesAt-correct (state b p) ((F.suc F.zero) , (F.suc F.zero)) = New.capturesq11-correct b p
capturesAt-correct (state b p) ((F.suc F.zero) , (F.suc (F.suc F.zero))) = New.capturesq12-correct b p
capturesAt-correct (state b p) ((F.suc F.zero) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq13-correct b p
capturesAt-correct (state b p) ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq14-correct b p
capturesAt-correct (state b p) ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq15-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc F.zero)) , F.zero) = New.capturesq20-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc F.zero)) , (F.suc F.zero)) = New.capturesq21-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc F.zero))) = New.capturesq22-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq23-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq24-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq25-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc F.zero))) , F.zero) = New.capturesq30-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc F.zero)) = New.capturesq31-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc F.zero))) = New.capturesq32-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq33-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq34-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq35-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , F.zero) = New.capturesq40-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc F.zero)) = New.capturesq41-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc F.zero))) = New.capturesq42-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq43-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq44-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq45-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , F.zero) = New.capturesq50-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc F.zero)) = New.capturesq51-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc F.zero))) = New.capturesq52-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc F.zero)))) = New.capturesq53-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = New.capturesq54-correct b p
capturesAt-correct (state b p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = New.capturesq55-correct b p

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
everyCoord (F.zero , F.zero) = here
everyCoord (F.zero , (F.suc F.zero)) = there (here)
everyCoord (F.zero , (F.suc (F.suc F.zero))) = there (there (here))
everyCoord (F.zero , (F.suc (F.suc (F.suc F.zero)))) = there (there (there (here)))
everyCoord (F.zero , (F.suc (F.suc (F.suc (F.suc F.zero))))) = there (there (there (there (here))))
everyCoord (F.zero , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = there (there (there (there (there (here)))))
everyCoord ((F.suc F.zero) , F.zero) = there (there (there (there (there (there (here))))))
everyCoord ((F.suc F.zero) , (F.suc F.zero)) = there (there (there (there (there (there (there (here)))))))
everyCoord ((F.suc F.zero) , (F.suc (F.suc F.zero))) = there (there (there (there (there (there (there (there (here))))))))
everyCoord ((F.suc F.zero) , (F.suc (F.suc (F.suc F.zero)))) = there (there (there (there (there (there (there (there (there (here)))))))))
everyCoord ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = there (there (there (there (there (there (there (there (there (there (here))))))))))
everyCoord ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = there (there (there (there (there (there (there (there (there (there (there (here)))))))))))
everyCoord ((F.suc (F.suc F.zero)) , F.zero) = there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))
everyCoord ((F.suc (F.suc F.zero)) , (F.suc F.zero)) = there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))
everyCoord ((F.suc (F.suc F.zero)) , (F.suc (F.suc F.zero))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))
everyCoord ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc F.zero)))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))
everyCoord ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))
everyCoord ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc F.zero))) , F.zero) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc F.zero))) , (F.suc F.zero)) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc F.zero))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc F.zero)))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc F.zero)))) , F.zero) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc F.zero)) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc F.zero))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc F.zero)))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , F.zero) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc F.zero)) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc F.zero))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc F.zero)))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here))))))))))))))))))))))))))))))))))
everyCoord ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (there (here)))))))))))))))))))))))))))))))))))

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
