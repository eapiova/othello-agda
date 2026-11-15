{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- Generated fixtures, each transition independently checked.
module Tests.PerfectLine6 where

open import Prelude
open import Game.Core using (lookup)
open import Othello.Board
open import Othello.Rules using (successors; forcedPass)
open import Othello.Encode6 using (decodeState)

p0 : State six
p0 = fromMaybe (initial six) (decodeState "b000000000000002100001200000000000000")

p1 : State six
p1 = fromMaybe (initial six) (decodeState "w000000001000001100001200000000000000")

p2 : State six
p2 = fromMaybe (initial six) (decodeState "b000000001000001100022200000000000000")

p3 : State six
p3 = fromMaybe (initial six) (decodeState "w000000001000001100021200001000000000")

p4 : State six
p4 = fromMaybe (initial six) (decodeState "b000000001200002200021200001000000000")

p5 : State six
p5 = fromMaybe (initial six) (decodeState "w000000001200002100021110001000000000")

p6 : State six
p6 = fromMaybe (initial six) (decodeState "b000000001200002220021110001000000000")

p7 : State six
p7 = fromMaybe (initial six) (decodeState "w000100001100002120021110001000000000")

p8 : State six
p8 = fromMaybe (initial six) (decodeState "b002100002200002120021110001000000000")

p9 : State six
p9 = fromMaybe (initial six) (decodeState "w011100001200002120021110001000000000")

p10 : State six
p10 = fromMaybe (initial six) (decodeState "b011100001200002220021210001200000000")

p11 : State six
p11 = fromMaybe (initial six) (decodeState "w011100001100002120021110001100000100")

p12 : State six
p12 = fromMaybe (initial six) (decodeState "b011100001100002120022222001100000100")

p13 : State six
p13 = fromMaybe (initial six) (decodeState "w011100001100011120021222001100000100")

p14 : State six
p14 = fromMaybe (initial six) (decodeState "b011100021100022120021222001100000100")

p15 : State six
p15 = fromMaybe (initial six) (decodeState "w011100021100022111021212001100000100")

p16 : State six
p16 = fromMaybe (initial six) (decodeState "b011100021102022122021212001100000100")

p17 : State six
p17 = fromMaybe (initial six) (decodeState "w011100021112022112021212001100000100")

p18 : State six
p18 = fromMaybe (initial six) (decodeState "b011100021112022112021212002100020100")

p19 : State six
p19 = fromMaybe (initial six) (decodeState "w011100021112012112111212002100020100")

p20 : State six
p20 = fromMaybe (initial six) (decodeState "b011100021112012112111222002200022100")

p21 : State six
p21 = fromMaybe (initial six) (decodeState "w011100021112012112111222002200111100")

p22 : State six
p22 = fromMaybe (initial six) (decodeState "b011100221112022112112222002200111100")

p23 : State six
p23 = fromMaybe (initial six) (decodeState "w011100221112022112111222012200111100")

p24 : State six
p24 = fromMaybe (initial six) (decodeState "b011100221112022112121222222200111100")

p25 : State six
p25 = fromMaybe (initial six) (decodeState "w011100221112022112121222222100111110")

p26 : State six
p26 = fromMaybe (initial six) (decodeState "b011100221112022112121222222220111110")

p27 : State six
p27 = fromMaybe (initial six) (decodeState "w011100211112111112111222221220111110")

p28 : State six
p28 = fromMaybe (initial six) (decodeState "b211100221112112112111222221220111110")

p29 : State six
p29 = fromMaybe (initial six) (decodeState "w211100221112112112111212221111111110")

p30 : State six
p30 = fromMaybe (initial six) (decodeState "b211100221112112112111212221122111112")

p31 : State six
p31 = fromMaybe (initial six) (decodeState "w211100221112112112111212221122111112")

p32 : State six
p32 = fromMaybe (initial six) (decodeState "b222220221222112122111222221122111112")

p33 : State six
p33 = fromMaybe (initial six) (decodeState "w222221221212112122111222221122111112")

start-correct : p0 ≡ initial six
start-correct = refl

edge0 : lookup (successors p0) 0 ≡ just p1
edge0 = refl

edge1 : lookup (successors p1) 2 ≡ just p2
edge1 = refl

edge2 : lookup (successors p2) 2 ≡ just p3
edge2 = refl

edge3 : lookup (successors p3) 1 ≡ just p4
edge3 = refl

edge4 : lookup (successors p4) 4 ≡ just p5
edge4 = refl

edge5 : lookup (successors p5) 2 ≡ just p6
edge5 = refl

edge6 : lookup (successors p6) 0 ≡ just p7
edge6 = refl

edge7 : lookup (successors p7) 0 ≡ just p8
edge7 = refl

edge8 : lookup (successors p8) 0 ≡ just p9
edge8 = refl

edge9 : lookup (successors p9) 2 ≡ just p10
edge9 = refl

edge10 : lookup (successors p10) 7 ≡ just p11
edge10 = refl

edge11 : lookup (successors p11) 1 ≡ just p12
edge11 = refl

edge12 : lookup (successors p12) 2 ≡ just p13
edge12 = refl

edge13 : lookup (successors p13) 1 ≡ just p14
edge13 = refl

edge14 : lookup (successors p14) 3 ≡ just p15
edge14 = refl

edge15 : lookup (successors p15) 2 ≡ just p16
edge15 = refl

edge16 : lookup (successors p16) 1 ≡ just p17
edge16 = refl

edge17 : lookup (successors p17) 1 ≡ just p18
edge17 = refl

edge18 : lookup (successors p18) 2 ≡ just p19
edge18 = refl

edge19 : lookup (successors p19) 5 ≡ just p20
edge19 = refl

edge20 : lookup (successors p20) 4 ≡ just p21
edge20 = refl

edge21 : lookup (successors p21) 1 ≡ just p22
edge21 = refl

edge22 : lookup (successors p22) 1 ≡ just p23
edge22 = refl

edge23 : lookup (successors p23) 2 ≡ just p24
edge23 = refl

edge24 : lookup (successors p24) 3 ≡ just p25
edge24 = refl

edge25 : lookup (successors p25) 3 ≡ just p26
edge25 = refl

edge26 : lookup (successors p26) 0 ≡ just p27
edge26 = refl

edge27 : lookup (successors p27) 0 ≡ just p28
edge27 = refl

edge28 : lookup (successors p28) 0 ≡ just p29
edge28 = refl

edge29 : lookup (successors p29) 2 ≡ just p30
edge29 = refl

edge30 : lookup (successors p30) 0 ≡ just p31
edge30 = refl

edge31 : lookup (successors p31) 0 ≡ just p32
edge31 = refl

edge32 : lookup (successors p32) 0 ≡ just p33
edge32 = refl

data LegalLine : State six → List ℕ → State six → Set where
  finish : ∀ {s} → LegalLine s [] s
  step : ∀ {s i is t u} → lookup (successors s) i ≡ just t → LegalLine t is u → LegalLine s (i ∷ is) u

moveIndices : List ℕ
moveIndices = 0 ∷ 2 ∷ 2 ∷ 1 ∷ 4 ∷ 2 ∷ 0 ∷ 0 ∷ 0 ∷ 2 ∷ 7 ∷ 1 ∷ 2 ∷ 1 ∷ 3 ∷ 2 ∷ 1 ∷ 1 ∷ 2 ∷ 5 ∷ 4 ∷ 1 ∷ 1 ∷ 2 ∷ 3 ∷ 3 ∷ 0 ∷ 0 ∷ 0 ∷ 2 ∷ 0 ∷ 0 ∷ 0 ∷ []

legal-line : LegalLine p0 moveIndices p33
legal-line = step {t = p1} edge0 (step {t = p2} edge1 (step {t = p3} edge2 (step {t = p4} edge3 (step {t = p5} edge4 (step {t = p6} edge5 (step {t = p7} edge6 (step {t = p8} edge7 (step {t = p9} edge8 (step {t = p10} edge9 (step {t = p11} edge10 (step {t = p12} edge11 (step {t = p13} edge12 (step {t = p14} edge13 (step {t = p15} edge14 (step {t = p16} edge15 (step {t = p17} edge16 (step {t = p18} edge17 (step {t = p19} edge18 (step {t = p20} edge19 (step {t = p21} edge20 (step {t = p22} edge21 (step {t = p23} edge22 (step {t = p24} edge23 (step {t = p25} edge24 (step {t = p26} edge25 (step {t = p27} edge26 (step {t = p28} edge27 (step {t = p29} edge28 (step {t = p30} edge29 (step {t = p31} edge30 (step {t = p32} edge31 (step {t = p33} edge32 (finish)))))))))))))))))))))))))))))))))

path : List (State six)
path = p1 ∷ p2 ∷ p3 ∷ p4 ∷ p5 ∷ p6 ∷ p7 ∷ p8 ∷ p9 ∷ p10 ∷ p11 ∷ p12 ∷ p13 ∷ p14 ∷ p15 ∷ p16 ∷ p17 ∷ p18 ∷ p19 ∷ p20 ∷ p21 ∷ p22 ∷ p23 ∷ p24 ∷ p25 ∷ p26 ∷ p27 ∷ p28 ∷ p29 ∷ p30 ∷ p31 ∷ p32 ∷ p33 ∷ []

black-pass : forcedPass p30 ≡ true
black-pass = refl

black-sixteen : discs black p33 ≡ 16
black-sixteen = refl

white-twenty : discs white p33 ≡ 20
white-twenty = refl

no-empty : empties p33 ≡ 0
no-empty = refl

line-terminal : successors p33 ≡ []
line-terminal = refl
