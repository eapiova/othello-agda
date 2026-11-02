{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Checked suffix20 is not an initial6x6 theorem.
module Othello.SpliceSuffix20 where

open import Prelude
import Othello.PathSplice6 as Finish
import Othello.SpliceLine6 as Line
import Othello.SpliceSuffix6 as Tail
import Othello.SpliceSuffix6.State20Boolean as S20
import Othello.SpliceSuffix6.State21 as S21
import Othello.SpliceSuffix6.State22 as S22
import Othello.SpliceSuffix6.State23 as S23
import Othello.SpliceSuffix6.State24 as S24
import Othello.SpliceSuffix6.State25 as S25

module Along = Finish.Along

suffix20 : Along.Trace Line.p20 Line.p33
suffix20 = (Along.prepend 4 Line.edge20 (Along.prepend 1 Line.edge21 (Along.prepend 1 Line.edge22 (Along.prepend 2 Line.edge23 (Along.prepend 3 Line.edge24 (Along.prepend 3 Line.edge25 Tail.suffix26))))))

bounds20 : Along.Bounds suffix20
bounds20 = ((S20.lower , S20.upper) , ((S21.lower , S21.upper) , ((S22.lower , S22.upper) , ((S23.lower , S23.upper) , ((S24.lower , S24.upper) , ((S25.lower , S25.upper) , Tail.bounds26))))))

pair20 : Along.Pair Line.p20 Line.p33
pair20 = Along.assemble suffix20 bounds20
