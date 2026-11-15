{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Literal trace only; prefix winning guarantees remain inputs.
module Othello.SpliceLine6 where
open import Prelude
open import Game.Core using (lookup)
open import Othello.Board
open import Othello.Encode6 using (decodeState)
open import Othello.Statements using (Problem2)
import Othello.Fast6 as Fast
import Othello.PathSplice6 as Finish
module Along = Finish.Along

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

edge0 : lookup (Fast.fastSuccessors p0) 0 ≡ just p1
edge0 = refl

edge1 : lookup (Fast.fastSuccessors p1) 2 ≡ just p2
edge1 = refl

edge2 : lookup (Fast.fastSuccessors p2) 2 ≡ just p3
edge2 = refl

edge3 : lookup (Fast.fastSuccessors p3) 1 ≡ just p4
edge3 = refl

edge4 : lookup (Fast.fastSuccessors p4) 4 ≡ just p5
edge4 = refl

edge5 : lookup (Fast.fastSuccessors p5) 2 ≡ just p6
edge5 = refl

edge6 : lookup (Fast.fastSuccessors p6) 0 ≡ just p7
edge6 = refl

edge7 : lookup (Fast.fastSuccessors p7) 0 ≡ just p8
edge7 = refl

edge8 : lookup (Fast.fastSuccessors p8) 0 ≡ just p9
edge8 = refl

edge9 : lookup (Fast.fastSuccessors p9) 2 ≡ just p10
edge9 = refl

edge10 : lookup (Fast.fastSuccessors p10) 7 ≡ just p11
edge10 = refl

edge11 : lookup (Fast.fastSuccessors p11) 1 ≡ just p12
edge11 = refl

edge12 : lookup (Fast.fastSuccessors p12) 2 ≡ just p13
edge12 = refl

edge13 : lookup (Fast.fastSuccessors p13) 1 ≡ just p14
edge13 = refl

edge14 : lookup (Fast.fastSuccessors p14) 3 ≡ just p15
edge14 = refl

edge15 : lookup (Fast.fastSuccessors p15) 2 ≡ just p16
edge15 = refl

edge16 : lookup (Fast.fastSuccessors p16) 1 ≡ just p17
edge16 = refl

edge17 : lookup (Fast.fastSuccessors p17) 1 ≡ just p18
edge17 = refl

edge18 : lookup (Fast.fastSuccessors p18) 2 ≡ just p19
edge18 = refl

edge19 : lookup (Fast.fastSuccessors p19) 5 ≡ just p20
edge19 = refl

edge20 : lookup (Fast.fastSuccessors p20) 4 ≡ just p21
edge20 = refl

edge21 : lookup (Fast.fastSuccessors p21) 1 ≡ just p22
edge21 = refl

edge22 : lookup (Fast.fastSuccessors p22) 1 ≡ just p23
edge22 = refl

edge23 : lookup (Fast.fastSuccessors p23) 2 ≡ just p24
edge23 = refl

edge24 : lookup (Fast.fastSuccessors p24) 3 ≡ just p25
edge24 = refl

edge25 : lookup (Fast.fastSuccessors p25) 3 ≡ just p26
edge25 = refl

edge26 : lookup (Fast.fastSuccessors p26) 0 ≡ just p27
edge26 = refl

edge27 : lookup (Fast.fastSuccessors p27) 0 ≡ just p28
edge27 = refl

edge28 : lookup (Fast.fastSuccessors p28) 0 ≡ just p29
edge28 = refl

edge29 : lookup (Fast.fastSuccessors p29) 2 ≡ just p30
edge29 = refl

edge30 : lookup (Fast.fastSuccessors p30) 0 ≡ just p31
edge30 = refl

edge31 : lookup (Fast.fastSuccessors p31) 0 ≡ just p32
edge31 = refl

edge32 : lookup (Fast.fastSuccessors p32) 0 ≡ just p33
edge32 = refl

terminal : Fast.fastSuccessors p33 ≡ []
terminal = refl

line : Along.Trace (initial six) p33
line = Along.prepend {s = p0} {u = p1} {t = p33} 0 edge0 (Along.prepend {s = p1} {u = p2} {t = p33} 2 edge1 (Along.prepend {s = p2} {u = p3} {t = p33} 2 edge2 (Along.prepend {s = p3} {u = p4} {t = p33} 1 edge3 (Along.prepend {s = p4} {u = p5} {t = p33} 4 edge4 (Along.prepend {s = p5} {u = p6} {t = p33} 2 edge5 (Along.prepend {s = p6} {u = p7} {t = p33} 0 edge6 (Along.prepend {s = p7} {u = p8} {t = p33} 0 edge7 (Along.prepend {s = p8} {u = p9} {t = p33} 0 edge8 (Along.prepend {s = p9} {u = p10} {t = p33} 2 edge9 (Along.prepend {s = p10} {u = p11} {t = p33} 7 edge10 (Along.prepend {s = p11} {u = p12} {t = p33} 1 edge11 (Along.prepend {s = p12} {u = p13} {t = p33} 2 edge12 (Along.prepend {s = p13} {u = p14} {t = p33} 1 edge13 (Along.prepend {s = p14} {u = p15} {t = p33} 3 edge14 (Along.prepend {s = p15} {u = p16} {t = p33} 2 edge15 (Along.prepend {s = p16} {u = p17} {t = p33} 1 edge16 (Along.prepend {s = p17} {u = p18} {t = p33} 1 edge17 (Along.prepend {s = p18} {u = p19} {t = p33} 2 edge18 (Along.prepend {s = p19} {u = p20} {t = p33} 5 edge19 (Along.prepend {s = p20} {u = p21} {t = p33} 4 edge20 (Along.prepend {s = p21} {u = p22} {t = p33} 1 edge21 (Along.prepend {s = p22} {u = p23} {t = p33} 1 edge22 (Along.prepend {s = p23} {u = p24} {t = p33} 2 edge23 (Along.prepend {s = p24} {u = p25} {t = p33} 3 edge24 (Along.prepend {s = p25} {u = p26} {t = p33} 3 edge25 (Along.prepend {s = p26} {u = p27} {t = p33} 0 edge26 (Along.prepend {s = p27} {u = p28} {t = p33} 0 edge27 (Along.prepend {s = p28} {u = p29} {t = p33} 0 edge28 (Along.prepend {s = p29} {u = p30} {t = p33} 2 edge29 (Along.prepend {s = p30} {u = p31} {t = p33} 0 edge30 (Along.prepend {s = p31} {u = p32} {t = p33} 0 edge31 (Along.prepend {s = p32} {u = p33} {t = p33} 0 edge32 (Along.stop terminal)))))))))))))))))))))))))))))))))

-- This function does not supply the still missing prefix guarantees.
problem2-from-prefix-bounds : Along.Bounds line → Problem2
problem2-from-prefix-bounds bounds = Finish.problem2-from-prefix-bounds line bounds (refl , refl)
