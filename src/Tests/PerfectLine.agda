{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.PerfectLine where

open import Prelude
open import Game.Core using (lookup)
open import Othello.Finite as V using ()
open import Othello.Board
open import Othello.Rules using (successors; forcedPass)

-- Literal intermediate boards keep every reflected check to a single ply.
-- They are untrusted fixtures: every transition below is checked by Agda.

p0 : State four
p0 = state ((empty V.∷ empty V.∷ empty V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ whiteCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ blackCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ empty V.∷ empty V.∷ empty V.∷ V.[]) V.∷ V.[]) black

p1 : State four
p1 = state ((empty V.∷ blackCell V.∷ empty V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ blackCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ blackCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ empty V.∷ empty V.∷ empty V.∷ V.[]) V.∷ V.[]) white

p2 : State four
p2 = state ((whiteCell V.∷ blackCell V.∷ empty V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ whiteCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ blackCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ empty V.∷ empty V.∷ empty V.∷ V.[]) V.∷ V.[]) black

p3 : State four
p3 = state ((whiteCell V.∷ blackCell V.∷ empty V.∷ empty V.∷ V.[]) V.∷ (blackCell V.∷ blackCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ blackCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ empty V.∷ empty V.∷ empty V.∷ V.[]) V.∷ V.[]) white

p4 : State four
p4 = state ((whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (blackCell V.∷ blackCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ blackCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ empty V.∷ empty V.∷ empty V.∷ V.[]) V.∷ V.[]) black

p5 : State four
p5 = state ((whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (blackCell V.∷ blackCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ blackCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ empty V.∷ empty V.∷ blackCell V.∷ V.[]) V.∷ V.[]) white

p6 : State four
p6 = state ((whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (whiteCell V.∷ blackCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ empty V.∷ empty V.∷ blackCell V.∷ V.[]) V.∷ V.[]) black

p7 : State four
p7 = state ((whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ blackCell V.∷ V.[]) V.∷ (whiteCell V.∷ whiteCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (whiteCell V.∷ blackCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ empty V.∷ empty V.∷ blackCell V.∷ V.[]) V.∷ V.[]) white

p8 : State four
p8 = state ((whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ blackCell V.∷ V.[]) V.∷ (whiteCell V.∷ whiteCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (whiteCell V.∷ whiteCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (empty V.∷ whiteCell V.∷ empty V.∷ blackCell V.∷ V.[]) V.∷ V.[]) black

p9 : State four
p9 = state ((whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ blackCell V.∷ V.[]) V.∷ (whiteCell V.∷ whiteCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (whiteCell V.∷ blackCell V.∷ blackCell V.∷ empty V.∷ V.[]) V.∷ (blackCell V.∷ whiteCell V.∷ empty V.∷ blackCell V.∷ V.[]) V.∷ V.[]) white

p10 : State four
p10 = state ((whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ blackCell V.∷ V.[]) V.∷ (whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (whiteCell V.∷ whiteCell V.∷ whiteCell V.∷ empty V.∷ V.[]) V.∷ (blackCell V.∷ whiteCell V.∷ whiteCell V.∷ blackCell V.∷ V.[]) V.∷ V.[]) black

start-correct : p0 ≡ initial four
start-correct = refl

line : List ℕ
line = 0 ∷ 0 ∷ 0 ∷ 0 ∷ 3 ∷ 0 ∷ 0 ∷ 2 ∷ 0 ∷ 2 ∷ []

data PlacementLine : State four → List ℕ → State four → Set where
  finish : ∀ {s} → PlacementLine s [] s
  place : ∀ {s i is t u} → forcedPass s ≡ false →
    lookup (successors s) i ≡ just t → PlacementLine t is u →
    PlacementLine s (i ∷ is) u

edge0 : lookup (successors p0) 0 ≡ just p1
edge0 = refl

no-pass0 : forcedPass p0 ≡ false
no-pass0 = refl

edge1 : lookup (successors p1) 0 ≡ just p2
edge1 = refl

no-pass1 : forcedPass p1 ≡ false
no-pass1 = refl

edge2 : lookup (successors p2) 0 ≡ just p3
edge2 = refl

no-pass2 : forcedPass p2 ≡ false
no-pass2 = refl

edge3 : lookup (successors p3) 0 ≡ just p4
edge3 = refl

no-pass3 : forcedPass p3 ≡ false
no-pass3 = refl

edge4 : lookup (successors p4) 3 ≡ just p5
edge4 = refl

no-pass4 : forcedPass p4 ≡ false
no-pass4 = refl

edge5 : lookup (successors p5) 0 ≡ just p6
edge5 = refl

no-pass5 : forcedPass p5 ≡ false
no-pass5 = refl

edge6 : lookup (successors p6) 0 ≡ just p7
edge6 = refl

no-pass6 : forcedPass p6 ≡ false
no-pass6 = refl

edge7 : lookup (successors p7) 2 ≡ just p8
edge7 = refl

no-pass7 : forcedPass p7 ≡ false
no-pass7 = refl

edge8 : lookup (successors p8) 0 ≡ just p9
edge8 = refl

no-pass8 : forcedPass p8 ≡ false
no-pass8 = refl

edge9 : lookup (successors p9) 2 ≡ just p10
edge9 = refl

no-pass9 : forcedPass p9 ≡ false
no-pass9 = refl

path : PlacementLine p0 line p10
path =
  place {t = p1} no-pass0 edge0 (place {t = p2} no-pass1 edge1 (place {t = p3} no-pass2 edge2 (place {t = p4} no-pass3 edge3 (place {t = p5} no-pass4 edge4 (place {t = p6} no-pass5 edge5 (place {t = p7} no-pass6 edge6 (place {t = p8} no-pass7 edge7 (place {t = p9} no-pass8 edge8 (place {t = p10} no-pass9 edge9 (finish))))))))))

legal-line : PlacementLine (initial four) line p10
legal-line = subst (λ s → PlacementLine s line p10) start-correct path

black-three : discs black p10 ≡ 3
black-three = refl

white-eleven : discs white p10 ≡ 11
white-eleven = refl

two-empty : empties p10 ≡ 2
two-empty = refl

line-terminal : successors p10 ≡ []
line-terminal = refl
