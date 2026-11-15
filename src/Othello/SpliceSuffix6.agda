{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Exact literal suffix assembly for the SAME optimal pair.
module Othello.SpliceSuffix6 where

open import Prelude
open import Game.Core using (black; white)
open import Othello.Board using (discs)
import Othello.PathSplice6 as Finish
import Othello.SpliceLine6 as Line
import Othello.SpliceSuffix6.State26 as S26
import Othello.SpliceSuffix6.State27 as S27
import Othello.SpliceSuffix6.State28 as S28
import Othello.SpliceSuffix6.State29 as S29
import Othello.SpliceSuffix6.State30 as S30
import Othello.SpliceSuffix6.State31 as S31
import Othello.SpliceSuffix6.State32 as S32
import Othello.SpliceSuffix6.State33 as S33

module Along = Finish.Along

suffix26 : Along.Trace Line.p26 Line.p33
suffix26 =
  Along.prepend 0 Line.edge26
    (Along.prepend 0 Line.edge27
      (Along.prepend 0 Line.edge28
        (Along.prepend 2 Line.edge29
          (Along.prepend 0 Line.edge30
            (Along.prepend 0 Line.edge31
              (Along.prepend 0 Line.edge32
                (Along.stop Line.terminal)))))))

bounds26 : Along.Bounds suffix26
bounds26 =
  (S26.lower , S26.upper) ,
    ((S27.lower , S27.upper) ,
      ((S28.lower , S28.upper) ,
        ((S29.lower , S29.upper) ,
          ((S30.lower , S30.upper) ,
            ((S31.lower , S31.upper) ,
              ((S32.lower , S32.upper) ,
                (S33.lower , S33.upper)))))))

pair26 : Along.Pair Line.p26 Line.p33
pair26 = Along.assemble suffix26 bounds26

proof16 : discs black Line.p33 ≡ 16
proof16 = refl

proof20 : discs white Line.p33 ≡ 20
proof20 = refl
