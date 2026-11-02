{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Closed suffix; initial21 state bounds remain explicit inputs.
module Othello.SpliceSuffix21 where

open import Prelude
open import Game.Core using (Guarantees; white; black)
open import Othello.Board using (State; six)
open import Othello.Statements using (lowerGoal; upperGoal; Problem2)
import Othello.Fast6 as Fast
import Othello.PathSplice6 as Finish
import Othello.SpliceLine6 as Line
import Othello.SpliceSuffix6 as Tail
import Othello.SpliceSuffix6.State21 as S21
import Othello.SpliceSuffix6.State22 as S22
import Othello.SpliceSuffix6.State23 as S23
import Othello.SpliceSuffix6.State24 as S24
import Othello.SpliceSuffix6.State25 as S25

module Along = Finish.Along

suffix21 : Along.Trace Line.p21 Line.p33
suffix21 = (Along.prepend 1 Line.edge21 (Along.prepend 1 Line.edge22 (Along.prepend 2 Line.edge23 (Along.prepend 3 Line.edge24 (Along.prepend 3 Line.edge25 Tail.suffix26)))))

bounds21 : Along.Bounds suffix21
bounds21 = ((S21.lower , S21.upper) , ((S22.lower , S22.upper) , ((S23.lower , S23.upper) , ((S24.lower , S24.upper) , ((S25.lower , S25.upper) , Tail.bounds26)))))

pair21 : Along.Pair Line.p21 Line.p33
pair21 = Along.assemble suffix21 bounds21

At : State six → Set
At s = Guarantees Fast.fastGame6 white (lowerGoal 4) s × Guarantees Fast.fastGame6 black (upperGoal 4) s

problem2-from-first21 :
  At Line.p0 →
  At Line.p1 →
  At Line.p2 →
  At Line.p3 →
  At Line.p4 →
  At Line.p5 →
  At Line.p6 →
  At Line.p7 →
  At Line.p8 →
  At Line.p9 →
  At Line.p10 →
  At Line.p11 →
  At Line.p12 →
  At Line.p13 →
  At Line.p14 →
  At Line.p15 →
  At Line.p16 →
  At Line.p17 →
  At Line.p18 →
  At Line.p19 →
  At Line.p20 → Problem2
problem2-from-first21 b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15 b16 b17 b18 b19 b20 =
  Line.problem2-from-prefix-bounds (b0 , (b1 , (b2 , (b3 , (b4 , (b5 , (b6 , (b7 , (b8 , (b9 , (b10 , (b11 , (b12 , (b13 , (b14 , (b15 , (b16 , (b17 , (b18 , (b19 , (b20 , bounds21)))))))))))))))))))))
