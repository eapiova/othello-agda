{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted generated geometry, checked against the original rays.
-- This module supplies no initial-board bound.
module Othello.LengthRules6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (coords; passState; nonempty)
import Othello.Rules as Rules
import Othello.Fast6 as Fast
import Othello.Finite as F
import Othello.Incremental6 as Incremental
import Othello.CellRays6 as Rays
import Game.Core as G
import Game.Transfer as T

q00 : Coord six
q00 = F.zero , F.zero

q01 : Coord six
q01 = F.zero , (F.suc F.zero)

q02 : Coord six
q02 = F.zero , (F.suc (F.suc F.zero))

q03 : Coord six
q03 = F.zero , (F.suc (F.suc (F.suc F.zero)))

q04 : Coord six
q04 = F.zero , (F.suc (F.suc (F.suc (F.suc F.zero))))

q05 : Coord six
q05 = F.zero , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))

q10 : Coord six
q10 = (F.suc F.zero) , F.zero

q11 : Coord six
q11 = (F.suc F.zero) , (F.suc F.zero)

q12 : Coord six
q12 = (F.suc F.zero) , (F.suc (F.suc F.zero))

q13 : Coord six
q13 = (F.suc F.zero) , (F.suc (F.suc (F.suc F.zero)))

q14 : Coord six
q14 = (F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc F.zero))))

q15 : Coord six
q15 = (F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))

q20 : Coord six
q20 = (F.suc (F.suc F.zero)) , F.zero

q21 : Coord six
q21 = (F.suc (F.suc F.zero)) , (F.suc F.zero)

q22 : Coord six
q22 = (F.suc (F.suc F.zero)) , (F.suc (F.suc F.zero))

q23 : Coord six
q23 = (F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc F.zero)))

q24 : Coord six
q24 = (F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc F.zero))))

q25 : Coord six
q25 = (F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))

q30 : Coord six
q30 = (F.suc (F.suc (F.suc F.zero))) , F.zero

q31 : Coord six
q31 = (F.suc (F.suc (F.suc F.zero))) , (F.suc F.zero)

q32 : Coord six
q32 = (F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc F.zero))

q33 : Coord six
q33 = (F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc F.zero)))

q34 : Coord six
q34 = (F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc F.zero))))

q35 : Coord six
q35 = (F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))

q40 : Coord six
q40 = (F.suc (F.suc (F.suc (F.suc F.zero)))) , F.zero

q41 : Coord six
q41 = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc F.zero)

q42 : Coord six
q42 = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc F.zero))

q43 : Coord six
q43 = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc F.zero)))

q44 : Coord six
q44 = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc F.zero))))

q45 : Coord six
q45 = (F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))

q50 : Coord six
q50 = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , F.zero

q51 : Coord six
q51 = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc F.zero)

q52 : Coord six
q52 = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc F.zero))

q53 : Coord six
q53 = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc F.zero)))

q54 : Coord six
q54 = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc F.zero))))

q55 : Coord six
q55 = (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))

import Othello.Specialized6 as Old
import Othello.LengthRays6 as Lines

private
  append-cong : ∀ {A : Set} {xs ys zs ws : List A} →
    xs ≡ ys → zs ≡ ws → xs ++ zs ≡ ys ++ ws
  append-cong refl refl = refl

capturesq00 : Board six → Player → List (Coord six)
capturesq00 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count5 p c01 c02 c03 c04 c05) (q01 ∷ q02 ∷ q03 ∷ q04 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count5 p c11 c22 c33 c44 c55) (q11 ∷ q22 ∷ q33 ∷ q44 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count5 p c10 c20 c30 c40 c50) (q10 ∷ q20 ∷ q30 ∷ q40 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq00-correct : ∀ b p → capturesq00 b p ≡ Fast.allCaptures6 (state b p) q00
capturesq00-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct5 p q01 q02 q03 q04 q05 c01 c02 c03 c04 c05) (append-cong (Lines.correct5 p q11 q22 q33 q44 q55 c11 c22 c33 c44 c55) (append-cong (Lines.correct5 p q10 q20 q30 q40 q50 c10 c20 c30 c40 c50) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq00-correct b p)

capturesq01 : Board six → Player → List (Coord six)
capturesq01 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count4 p c02 c03 c04 c05) (q02 ∷ q03 ∷ q04 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count4 p c12 c23 c34 c45) (q12 ∷ q23 ∷ q34 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count5 p c11 c21 c31 c41 c51) (q11 ∷ q21 ∷ q31 ∷ q41 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c10) (q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c00) (q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq01-correct : ∀ b p → capturesq01 b p ≡ Fast.allCaptures6 (state b p) q01
capturesq01-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct4 p q02 q03 q04 q05 c02 c03 c04 c05) (append-cong (Lines.correct4 p q12 q23 q34 q45 c12 c23 c34 c45) (append-cong (Lines.correct5 p q11 q21 q31 q41 q51 c11 c21 c31 c41 c51) (append-cong (Lines.correct1 p q10 c10) (append-cong (Lines.correct1 p q00 c00) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq01-correct b p)

capturesq02 : Board six → Player → List (Coord six)
capturesq02 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count3 p c03 c04 c05) (q03 ∷ q04 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count3 p c13 c24 c35) (q13 ∷ q24 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count5 p c12 c22 c32 c42 c52) (q12 ∷ q22 ∷ q32 ∷ q42 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c11 c20) (q11 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c01 c00) (q01 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq02-correct : ∀ b p → capturesq02 b p ≡ Fast.allCaptures6 (state b p) q02
capturesq02-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct3 p q03 q04 q05 c03 c04 c05) (append-cong (Lines.correct3 p q13 q24 q35 c13 c24 c35) (append-cong (Lines.correct5 p q12 q22 q32 q42 q52 c12 c22 c32 c42 c52) (append-cong (Lines.correct2 p q11 q20 c11 c20) (append-cong (Lines.correct2 p q01 q00 c01 c00) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq02-correct b p)

capturesq03 : Board six → Player → List (Coord six)
capturesq03 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count2 p c04 c05) (q04 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count2 p c14 c25) (q14 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count5 p c13 c23 c33 c43 c53) (q13 ∷ q23 ∷ q33 ∷ q43 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count3 p c12 c21 c30) (q12 ∷ q21 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count3 p c02 c01 c00) (q02 ∷ q01 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq03-correct : ∀ b p → capturesq03 b p ≡ Fast.allCaptures6 (state b p) q03
capturesq03-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct2 p q04 q05 c04 c05) (append-cong (Lines.correct2 p q14 q25 c14 c25) (append-cong (Lines.correct5 p q13 q23 q33 q43 q53 c13 c23 c33 c43 c53) (append-cong (Lines.correct3 p q12 q21 q30 c12 c21 c30) (append-cong (Lines.correct3 p q02 q01 q00 c02 c01 c00) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq03-correct b p)

capturesq04 : Board six → Player → List (Coord six)
capturesq04 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count1 p c05) (q05 ∷ [])) ++ (Lines.prefix (Lines.count1 p c15) (q15 ∷ [])) ++ (Lines.prefix (Lines.count5 p c14 c24 c34 c44 c54) (q14 ∷ q24 ∷ q34 ∷ q44 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count4 p c13 c22 c31 c40) (q13 ∷ q22 ∷ q31 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count4 p c03 c02 c01 c00) (q03 ∷ q02 ∷ q01 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq04-correct : ∀ b p → capturesq04 b p ≡ Fast.allCaptures6 (state b p) q04
capturesq04-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct1 p q05 c05) (append-cong (Lines.correct1 p q15 c15) (append-cong (Lines.correct5 p q14 q24 q34 q44 q54 c14 c24 c34 c44 c54) (append-cong (Lines.correct4 p q13 q22 q31 q40 c13 c22 c31 c40) (append-cong (Lines.correct4 p q03 q02 q01 q00 c03 c02 c01 c00) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq04-correct b p)

capturesq05 : Board six → Player → List (Coord six)
capturesq05 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count5 p c15 c25 c35 c45 c55) (q15 ∷ q25 ∷ q35 ∷ q45 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count5 p c14 c23 c32 c41 c50) (q14 ∷ q23 ∷ q32 ∷ q41 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count5 p c04 c03 c02 c01 c00) (q04 ∷ q03 ∷ q02 ∷ q01 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq05-correct : ∀ b p → capturesq05 b p ≡ Fast.allCaptures6 (state b p) q05
capturesq05-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct5 p q15 q25 q35 q45 q55 c15 c25 c35 c45 c55) (append-cong (Lines.correct5 p q14 q23 q32 q41 q50 c14 c23 c32 c41 c50) (append-cong (Lines.correct5 p q04 q03 q02 q01 q00 c04 c03 c02 c01 c00) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq05-correct b p)

capturesq10 : Board six → Player → List (Coord six)
capturesq10 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count1 p c00) (q00 ∷ [])) ++ (Lines.prefix (Lines.count1 p c01) (q01 ∷ [])) ++ (Lines.prefix (Lines.count5 p c11 c12 c13 c14 c15) (q11 ∷ q12 ∷ q13 ∷ q14 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count4 p c21 c32 c43 c54) (q21 ∷ q32 ∷ q43 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count4 p c20 c30 c40 c50) (q20 ∷ q30 ∷ q40 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq10-correct : ∀ b p → capturesq10 b p ≡ Fast.allCaptures6 (state b p) q10
capturesq10-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct1 p q00 c00) (append-cong (Lines.correct1 p q01 c01) (append-cong (Lines.correct5 p q11 q12 q13 q14 q15 c11 c12 c13 c14 c15) (append-cong (Lines.correct4 p q21 q32 q43 q54 c21 c32 c43 c54) (append-cong (Lines.correct4 p q20 q30 q40 q50 c20 c30 c40 c50) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq10-correct b p)

capturesq11 : Board six → Player → List (Coord six)
capturesq11 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count1 p c01) (q01 ∷ [])) ++ (Lines.prefix (Lines.count1 p c02) (q02 ∷ [])) ++ (Lines.prefix (Lines.count4 p c12 c13 c14 c15) (q12 ∷ q13 ∷ q14 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count4 p c22 c33 c44 c55) (q22 ∷ q33 ∷ q44 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count4 p c21 c31 c41 c51) (q21 ∷ q31 ∷ q41 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c20) (q20 ∷ [])) ++ (Lines.prefix (Lines.count1 p c10) (q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c00) (q00 ∷ [])) ++ []

capturesq11-correct : ∀ b p → capturesq11 b p ≡ Fast.allCaptures6 (state b p) q11
capturesq11-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct1 p q01 c01) (append-cong (Lines.correct1 p q02 c02) (append-cong (Lines.correct4 p q12 q13 q14 q15 c12 c13 c14 c15) (append-cong (Lines.correct4 p q22 q33 q44 q55 c22 c33 c44 c55) (append-cong (Lines.correct4 p q21 q31 q41 q51 c21 c31 c41 c51) (append-cong (Lines.correct1 p q20 c20) (append-cong (Lines.correct1 p q10 c10) (append-cong (Lines.correct1 p q00 c00) (refl)))))))))
  (Old.capturesq11-correct b p)

capturesq12 : Board six → Player → List (Coord six)
capturesq12 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count1 p c02) (q02 ∷ [])) ++ (Lines.prefix (Lines.count1 p c03) (q03 ∷ [])) ++ (Lines.prefix (Lines.count3 p c13 c14 c15) (q13 ∷ q14 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count3 p c23 c34 c45) (q23 ∷ q34 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count4 p c22 c32 c42 c52) (q22 ∷ q32 ∷ q42 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c21 c30) (q21 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count2 p c11 c10) (q11 ∷ q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c01) (q01 ∷ [])) ++ []

capturesq12-correct : ∀ b p → capturesq12 b p ≡ Fast.allCaptures6 (state b p) q12
capturesq12-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct1 p q02 c02) (append-cong (Lines.correct1 p q03 c03) (append-cong (Lines.correct3 p q13 q14 q15 c13 c14 c15) (append-cong (Lines.correct3 p q23 q34 q45 c23 c34 c45) (append-cong (Lines.correct4 p q22 q32 q42 q52 c22 c32 c42 c52) (append-cong (Lines.correct2 p q21 q30 c21 c30) (append-cong (Lines.correct2 p q11 q10 c11 c10) (append-cong (Lines.correct1 p q01 c01) (refl)))))))))
  (Old.capturesq12-correct b p)

capturesq13 : Board six → Player → List (Coord six)
capturesq13 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count1 p c03) (q03 ∷ [])) ++ (Lines.prefix (Lines.count1 p c04) (q04 ∷ [])) ++ (Lines.prefix (Lines.count2 p c14 c15) (q14 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count2 p c24 c35) (q24 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count4 p c23 c33 c43 c53) (q23 ∷ q33 ∷ q43 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count3 p c22 c31 c40) (q22 ∷ q31 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count3 p c12 c11 c10) (q12 ∷ q11 ∷ q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c02) (q02 ∷ [])) ++ []

capturesq13-correct : ∀ b p → capturesq13 b p ≡ Fast.allCaptures6 (state b p) q13
capturesq13-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct1 p q03 c03) (append-cong (Lines.correct1 p q04 c04) (append-cong (Lines.correct2 p q14 q15 c14 c15) (append-cong (Lines.correct2 p q24 q35 c24 c35) (append-cong (Lines.correct4 p q23 q33 q43 q53 c23 c33 c43 c53) (append-cong (Lines.correct3 p q22 q31 q40 c22 c31 c40) (append-cong (Lines.correct3 p q12 q11 q10 c12 c11 c10) (append-cong (Lines.correct1 p q02 c02) (refl)))))))))
  (Old.capturesq13-correct b p)

capturesq14 : Board six → Player → List (Coord six)
capturesq14 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count1 p c04) (q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c05) (q05 ∷ [])) ++ (Lines.prefix (Lines.count1 p c15) (q15 ∷ [])) ++ (Lines.prefix (Lines.count1 p c25) (q25 ∷ [])) ++ (Lines.prefix (Lines.count4 p c24 c34 c44 c54) (q24 ∷ q34 ∷ q44 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count4 p c23 c32 c41 c50) (q23 ∷ q32 ∷ q41 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count4 p c13 c12 c11 c10) (q13 ∷ q12 ∷ q11 ∷ q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c03) (q03 ∷ [])) ++ []

capturesq14-correct : ∀ b p → capturesq14 b p ≡ Fast.allCaptures6 (state b p) q14
capturesq14-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct1 p q04 c04) (append-cong (Lines.correct1 p q05 c05) (append-cong (Lines.correct1 p q15 c15) (append-cong (Lines.correct1 p q25 c25) (append-cong (Lines.correct4 p q24 q34 q44 q54 c24 c34 c44 c54) (append-cong (Lines.correct4 p q23 q32 q41 q50 c23 c32 c41 c50) (append-cong (Lines.correct4 p q13 q12 q11 q10 c13 c12 c11 c10) (append-cong (Lines.correct1 p q03 c03) (refl)))))))))
  (Old.capturesq14-correct b p)

capturesq15 : Board six → Player → List (Coord six)
capturesq15 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count1 p c05) (q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count4 p c25 c35 c45 c55) (q25 ∷ q35 ∷ q45 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count4 p c24 c33 c42 c51) (q24 ∷ q33 ∷ q42 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count5 p c14 c13 c12 c11 c10) (q14 ∷ q13 ∷ q12 ∷ q11 ∷ q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c04) (q04 ∷ [])) ++ []

capturesq15-correct : ∀ b p → capturesq15 b p ≡ Fast.allCaptures6 (state b p) q15
capturesq15-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct1 p q05 c05) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct4 p q25 q35 q45 q55 c25 c35 c45 c55) (append-cong (Lines.correct4 p q24 q33 q42 q51 c24 c33 c42 c51) (append-cong (Lines.correct5 p q14 q13 q12 q11 q10 c14 c13 c12 c11 c10) (append-cong (Lines.correct1 p q04 c04) (refl)))))))))
  (Old.capturesq15-correct b p)

capturesq20 : Board six → Player → List (Coord six)
capturesq20 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count2 p c10 c00) (q10 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count2 p c11 c02) (q11 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count5 p c21 c22 c23 c24 c25) (q21 ∷ q22 ∷ q23 ∷ q24 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count3 p c31 c42 c53) (q31 ∷ q42 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count3 p c30 c40 c50) (q30 ∷ q40 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq20-correct : ∀ b p → capturesq20 b p ≡ Fast.allCaptures6 (state b p) q20
capturesq20-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct2 p q10 q00 c10 c00) (append-cong (Lines.correct2 p q11 q02 c11 c02) (append-cong (Lines.correct5 p q21 q22 q23 q24 q25 c21 c22 c23 c24 c25) (append-cong (Lines.correct3 p q31 q42 q53 c31 c42 c53) (append-cong (Lines.correct3 p q30 q40 q50 c30 c40 c50) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq20-correct b p)

capturesq21 : Board six → Player → List (Coord six)
capturesq21 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count2 p c11 c01) (q11 ∷ q01 ∷ [])) ++ (Lines.prefix (Lines.count2 p c12 c03) (q12 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count4 p c22 c23 c24 c25) (q22 ∷ q23 ∷ q24 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c43 c54) (q32 ∷ q43 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count3 p c31 c41 c51) (q31 ∷ q41 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c30) (q30 ∷ [])) ++ (Lines.prefix (Lines.count1 p c20) (q20 ∷ [])) ++ (Lines.prefix (Lines.count1 p c10) (q10 ∷ [])) ++ []

capturesq21-correct : ∀ b p → capturesq21 b p ≡ Fast.allCaptures6 (state b p) q21
capturesq21-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct2 p q11 q01 c11 c01) (append-cong (Lines.correct2 p q12 q03 c12 c03) (append-cong (Lines.correct4 p q22 q23 q24 q25 c22 c23 c24 c25) (append-cong (Lines.correct3 p q32 q43 q54 c32 c43 c54) (append-cong (Lines.correct3 p q31 q41 q51 c31 c41 c51) (append-cong (Lines.correct1 p q30 c30) (append-cong (Lines.correct1 p q20 c20) (append-cong (Lines.correct1 p q10 c10) (refl)))))))))
  (Old.capturesq21-correct b p)

capturesq22 : Board six → Player → List (Coord six)
capturesq22 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count2 p c12 c02) (q12 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count2 p c13 c04) (q13 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count3 p c23 c24 c25) (q23 ∷ q24 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c44 c55) (q33 ∷ q44 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c42 c52) (q32 ∷ q42 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c31 c40) (q31 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count2 p c21 c20) (q21 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c11 c00) (q11 ∷ q00 ∷ [])) ++ []

capturesq22-correct : ∀ b p → capturesq22 b p ≡ Fast.allCaptures6 (state b p) q22
capturesq22-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct2 p q12 q02 c12 c02) (append-cong (Lines.correct2 p q13 q04 c13 c04) (append-cong (Lines.correct3 p q23 q24 q25 c23 c24 c25) (append-cong (Lines.correct3 p q33 q44 q55 c33 c44 c55) (append-cong (Lines.correct3 p q32 q42 q52 c32 c42 c52) (append-cong (Lines.correct2 p q31 q40 c31 c40) (append-cong (Lines.correct2 p q21 q20 c21 c20) (append-cong (Lines.correct2 p q11 q00 c11 c00) (refl)))))))))
  (Old.capturesq22-correct b p)

capturesq23 : Board six → Player → List (Coord six)
capturesq23 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count2 p c13 c03) (q13 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count2 p c14 c05) (q14 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count2 p c24 c25) (q24 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count2 p c34 c45) (q34 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c43 c53) (q33 ∷ q43 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c41 c50) (q32 ∷ q41 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count3 p c22 c21 c20) (q22 ∷ q21 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c12 c01) (q12 ∷ q01 ∷ [])) ++ []

capturesq23-correct : ∀ b p → capturesq23 b p ≡ Fast.allCaptures6 (state b p) q23
capturesq23-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct2 p q13 q03 c13 c03) (append-cong (Lines.correct2 p q14 q05 c14 c05) (append-cong (Lines.correct2 p q24 q25 c24 c25) (append-cong (Lines.correct2 p q34 q45 c34 c45) (append-cong (Lines.correct3 p q33 q43 q53 c33 c43 c53) (append-cong (Lines.correct3 p q32 q41 q50 c32 c41 c50) (append-cong (Lines.correct3 p q22 q21 q20 c22 c21 c20) (append-cong (Lines.correct2 p q12 q01 c12 c01) (refl)))))))))
  (Old.capturesq23-correct b p)

capturesq24 : Board six → Player → List (Coord six)
capturesq24 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count2 p c14 c04) (q14 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c15) (q15 ∷ [])) ++ (Lines.prefix (Lines.count1 p c25) (q25 ∷ [])) ++ (Lines.prefix (Lines.count1 p c35) (q35 ∷ [])) ++ (Lines.prefix (Lines.count3 p c34 c44 c54) (q34 ∷ q44 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c42 c51) (q33 ∷ q42 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count4 p c23 c22 c21 c20) (q23 ∷ q22 ∷ q21 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c13 c02) (q13 ∷ q02 ∷ [])) ++ []

capturesq24-correct : ∀ b p → capturesq24 b p ≡ Fast.allCaptures6 (state b p) q24
capturesq24-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct2 p q14 q04 c14 c04) (append-cong (Lines.correct1 p q15 c15) (append-cong (Lines.correct1 p q25 c25) (append-cong (Lines.correct1 p q35 c35) (append-cong (Lines.correct3 p q34 q44 q54 c34 c44 c54) (append-cong (Lines.correct3 p q33 q42 q51 c33 c42 c51) (append-cong (Lines.correct4 p q23 q22 q21 q20 c23 c22 c21 c20) (append-cong (Lines.correct2 p q13 q02 c13 c02) (refl)))))))))
  (Old.capturesq24-correct b p)

capturesq25 : Board six → Player → List (Coord six)
capturesq25 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count2 p c15 c05) (q15 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count3 p c35 c45 c55) (q35 ∷ q45 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count3 p c34 c43 c52) (q34 ∷ q43 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count5 p c24 c23 c22 c21 c20) (q24 ∷ q23 ∷ q22 ∷ q21 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c14 c03) (q14 ∷ q03 ∷ [])) ++ []

capturesq25-correct : ∀ b p → capturesq25 b p ≡ Fast.allCaptures6 (state b p) q25
capturesq25-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct2 p q15 q05 c15 c05) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct3 p q35 q45 q55 c35 c45 c55) (append-cong (Lines.correct3 p q34 q43 q52 c34 c43 c52) (append-cong (Lines.correct5 p q24 q23 q22 q21 q20 c24 c23 c22 c21 c20) (append-cong (Lines.correct2 p q14 q03 c14 c03) (refl)))))))))
  (Old.capturesq25-correct b p)

capturesq30 : Board six → Player → List (Coord six)
capturesq30 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count3 p c20 c10 c00) (q20 ∷ q10 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count3 p c21 c12 c03) (q21 ∷ q12 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count5 p c31 c32 c33 c34 c35) (q31 ∷ q32 ∷ q33 ∷ q34 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c52) (q41 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c40 c50) (q40 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq30-correct : ∀ b p → capturesq30 b p ≡ Fast.allCaptures6 (state b p) q30
capturesq30-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct3 p q20 q10 q00 c20 c10 c00) (append-cong (Lines.correct3 p q21 q12 q03 c21 c12 c03) (append-cong (Lines.correct5 p q31 q32 q33 q34 q35 c31 c32 c33 c34 c35) (append-cong (Lines.correct2 p q41 q52 c41 c52) (append-cong (Lines.correct2 p q40 q50 c40 c50) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq30-correct b p)

capturesq31 : Board six → Player → List (Coord six)
capturesq31 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count3 p c21 c11 c01) (q21 ∷ q11 ∷ q01 ∷ [])) ++ (Lines.prefix (Lines.count3 p c22 c13 c04) (q22 ∷ q13 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count4 p c32 c33 c34 c35) (q32 ∷ q33 ∷ q34 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c42 c53) (q42 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c51) (q41 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c40) (q40 ∷ [])) ++ (Lines.prefix (Lines.count1 p c30) (q30 ∷ [])) ++ (Lines.prefix (Lines.count1 p c20) (q20 ∷ [])) ++ []

capturesq31-correct : ∀ b p → capturesq31 b p ≡ Fast.allCaptures6 (state b p) q31
capturesq31-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct3 p q21 q11 q01 c21 c11 c01) (append-cong (Lines.correct3 p q22 q13 q04 c22 c13 c04) (append-cong (Lines.correct4 p q32 q33 q34 q35 c32 c33 c34 c35) (append-cong (Lines.correct2 p q42 q53 c42 c53) (append-cong (Lines.correct2 p q41 q51 c41 c51) (append-cong (Lines.correct1 p q40 c40) (append-cong (Lines.correct1 p q30 c30) (append-cong (Lines.correct1 p q20 c20) (refl)))))))))
  (Old.capturesq31-correct b p)

capturesq32 : Board six → Player → List (Coord six)
capturesq32 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count3 p c22 c12 c02) (q22 ∷ q12 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count3 p c23 c14 c05) (q23 ∷ q14 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c34 c35) (q33 ∷ q34 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c43 c54) (q43 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count2 p c42 c52) (q42 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c50) (q41 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count2 p c31 c30) (q31 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count2 p c21 c10) (q21 ∷ q10 ∷ [])) ++ []

capturesq32-correct : ∀ b p → capturesq32 b p ≡ Fast.allCaptures6 (state b p) q32
capturesq32-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct3 p q22 q12 q02 c22 c12 c02) (append-cong (Lines.correct3 p q23 q14 q05 c23 c14 c05) (append-cong (Lines.correct3 p q33 q34 q35 c33 c34 c35) (append-cong (Lines.correct2 p q43 q54 c43 c54) (append-cong (Lines.correct2 p q42 q52 c42 c52) (append-cong (Lines.correct2 p q41 q50 c41 c50) (append-cong (Lines.correct2 p q31 q30 c31 c30) (append-cong (Lines.correct2 p q21 q10 c21 c10) (refl)))))))))
  (Old.capturesq32-correct b p)

capturesq33 : Board six → Player → List (Coord six)
capturesq33 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count3 p c23 c13 c03) (q23 ∷ q13 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count2 p c24 c15) (q24 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count2 p c34 c35) (q34 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c55) (q44 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count2 p c43 c53) (q43 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count2 p c42 c51) (q42 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c31 c30) (q32 ∷ q31 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count3 p c22 c11 c00) (q22 ∷ q11 ∷ q00 ∷ [])) ++ []

capturesq33-correct : ∀ b p → capturesq33 b p ≡ Fast.allCaptures6 (state b p) q33
capturesq33-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct3 p q23 q13 q03 c23 c13 c03) (append-cong (Lines.correct2 p q24 q15 c24 c15) (append-cong (Lines.correct2 p q34 q35 c34 c35) (append-cong (Lines.correct2 p q44 q55 c44 c55) (append-cong (Lines.correct2 p q43 q53 c43 c53) (append-cong (Lines.correct2 p q42 q51 c42 c51) (append-cong (Lines.correct3 p q32 q31 q30 c32 c31 c30) (append-cong (Lines.correct3 p q22 q11 q00 c22 c11 c00) (refl)))))))))
  (Old.capturesq33-correct b p)

capturesq34 : Board six → Player → List (Coord six)
capturesq34 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count3 p c24 c14 c04) (q24 ∷ q14 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c25) (q25 ∷ [])) ++ (Lines.prefix (Lines.count1 p c35) (q35 ∷ [])) ++ (Lines.prefix (Lines.count1 p c45) (q45 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c54) (q44 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count2 p c43 c52) (q43 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count4 p c33 c32 c31 c30) (q33 ∷ q32 ∷ q31 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count3 p c23 c12 c01) (q23 ∷ q12 ∷ q01 ∷ [])) ++ []

capturesq34-correct : ∀ b p → capturesq34 b p ≡ Fast.allCaptures6 (state b p) q34
capturesq34-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct3 p q24 q14 q04 c24 c14 c04) (append-cong (Lines.correct1 p q25 c25) (append-cong (Lines.correct1 p q35 c35) (append-cong (Lines.correct1 p q45 c45) (append-cong (Lines.correct2 p q44 q54 c44 c54) (append-cong (Lines.correct2 p q43 q52 c43 c52) (append-cong (Lines.correct4 p q33 q32 q31 q30 c33 c32 c31 c30) (append-cong (Lines.correct3 p q23 q12 q01 c23 c12 c01) (refl)))))))))
  (Old.capturesq34-correct b p)

capturesq35 : Board six → Player → List (Coord six)
capturesq35 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count3 p c25 c15 c05) (q25 ∷ q15 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count2 p c45 c55) (q45 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c53) (q44 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count5 p c34 c33 c32 c31 c30) (q34 ∷ q33 ∷ q32 ∷ q31 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count3 p c24 c13 c02) (q24 ∷ q13 ∷ q02 ∷ [])) ++ []

capturesq35-correct : ∀ b p → capturesq35 b p ≡ Fast.allCaptures6 (state b p) q35
capturesq35-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct3 p q25 q15 q05 c25 c15 c05) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct2 p q45 q55 c45 c55) (append-cong (Lines.correct2 p q44 q53 c44 c53) (append-cong (Lines.correct5 p q34 q33 q32 q31 q30 c34 c33 c32 c31 c30) (append-cong (Lines.correct3 p q24 q13 q02 c24 c13 c02) (refl)))))))))
  (Old.capturesq35-correct b p)

capturesq40 : Board six → Player → List (Coord six)
capturesq40 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count4 p c30 c20 c10 c00) (q30 ∷ q20 ∷ q10 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count4 p c31 c22 c13 c04) (q31 ∷ q22 ∷ q13 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count5 p c41 c42 c43 c44 c45) (q41 ∷ q42 ∷ q43 ∷ q44 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c51) (q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c50) (q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq40-correct : ∀ b p → capturesq40 b p ≡ Fast.allCaptures6 (state b p) q40
capturesq40-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct4 p q30 q20 q10 q00 c30 c20 c10 c00) (append-cong (Lines.correct4 p q31 q22 q13 q04 c31 c22 c13 c04) (append-cong (Lines.correct5 p q41 q42 q43 q44 q45 c41 c42 c43 c44 c45) (append-cong (Lines.correct1 p q51 c51) (append-cong (Lines.correct1 p q50 c50) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq40-correct b p)

capturesq41 : Board six → Player → List (Coord six)
capturesq41 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count4 p c31 c21 c11 c01) (q31 ∷ q21 ∷ q11 ∷ q01 ∷ [])) ++ (Lines.prefix (Lines.count4 p c32 c23 c14 c05) (q32 ∷ q23 ∷ q14 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count4 p c42 c43 c44 c45) (q42 ∷ q43 ∷ q44 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c52) (q52 ∷ [])) ++ (Lines.prefix (Lines.count1 p c51) (q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c50) (q50 ∷ [])) ++ (Lines.prefix (Lines.count1 p c40) (q40 ∷ [])) ++ (Lines.prefix (Lines.count1 p c30) (q30 ∷ [])) ++ []

capturesq41-correct : ∀ b p → capturesq41 b p ≡ Fast.allCaptures6 (state b p) q41
capturesq41-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct4 p q31 q21 q11 q01 c31 c21 c11 c01) (append-cong (Lines.correct4 p q32 q23 q14 q05 c32 c23 c14 c05) (append-cong (Lines.correct4 p q42 q43 q44 q45 c42 c43 c44 c45) (append-cong (Lines.correct1 p q52 c52) (append-cong (Lines.correct1 p q51 c51) (append-cong (Lines.correct1 p q50 c50) (append-cong (Lines.correct1 p q40 c40) (append-cong (Lines.correct1 p q30 c30) (refl)))))))))
  (Old.capturesq41-correct b p)

capturesq42 : Board six → Player → List (Coord six)
capturesq42 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count4 p c32 c22 c12 c02) (q32 ∷ q22 ∷ q12 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c24 c15) (q33 ∷ q24 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count3 p c43 c44 c45) (q43 ∷ q44 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c53) (q53 ∷ [])) ++ (Lines.prefix (Lines.count1 p c52) (q52 ∷ [])) ++ (Lines.prefix (Lines.count1 p c51) (q51 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c40) (q41 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count2 p c31 c20) (q31 ∷ q20 ∷ [])) ++ []

capturesq42-correct : ∀ b p → capturesq42 b p ≡ Fast.allCaptures6 (state b p) q42
capturesq42-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct4 p q32 q22 q12 q02 c32 c22 c12 c02) (append-cong (Lines.correct3 p q33 q24 q15 c33 c24 c15) (append-cong (Lines.correct3 p q43 q44 q45 c43 c44 c45) (append-cong (Lines.correct1 p q53 c53) (append-cong (Lines.correct1 p q52 c52) (append-cong (Lines.correct1 p q51 c51) (append-cong (Lines.correct2 p q41 q40 c41 c40) (append-cong (Lines.correct2 p q31 q20 c31 c20) (refl)))))))))
  (Old.capturesq42-correct b p)

capturesq43 : Board six → Player → List (Coord six)
capturesq43 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count4 p c33 c23 c13 c03) (q33 ∷ q23 ∷ q13 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count2 p c34 c25) (q34 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c45) (q44 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c54) (q54 ∷ [])) ++ (Lines.prefix (Lines.count1 p c53) (q53 ∷ [])) ++ (Lines.prefix (Lines.count1 p c52) (q52 ∷ [])) ++ (Lines.prefix (Lines.count3 p c42 c41 c40) (q42 ∷ q41 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c21 c10) (q32 ∷ q21 ∷ q10 ∷ [])) ++ []

capturesq43-correct : ∀ b p → capturesq43 b p ≡ Fast.allCaptures6 (state b p) q43
capturesq43-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct4 p q33 q23 q13 q03 c33 c23 c13 c03) (append-cong (Lines.correct2 p q34 q25 c34 c25) (append-cong (Lines.correct2 p q44 q45 c44 c45) (append-cong (Lines.correct1 p q54 c54) (append-cong (Lines.correct1 p q53 c53) (append-cong (Lines.correct1 p q52 c52) (append-cong (Lines.correct3 p q42 q41 q40 c42 c41 c40) (append-cong (Lines.correct3 p q32 q21 q10 c32 c21 c10) (refl)))))))))
  (Old.capturesq43-correct b p)

capturesq44 : Board six → Player → List (Coord six)
capturesq44 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count4 p c34 c24 c14 c04) (q34 ∷ q24 ∷ q14 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c35) (q35 ∷ [])) ++ (Lines.prefix (Lines.count1 p c45) (q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c55) (q55 ∷ [])) ++ (Lines.prefix (Lines.count1 p c54) (q54 ∷ [])) ++ (Lines.prefix (Lines.count1 p c53) (q53 ∷ [])) ++ (Lines.prefix (Lines.count4 p c43 c42 c41 c40) (q43 ∷ q42 ∷ q41 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count4 p c33 c22 c11 c00) (q33 ∷ q22 ∷ q11 ∷ q00 ∷ [])) ++ []

capturesq44-correct : ∀ b p → capturesq44 b p ≡ Fast.allCaptures6 (state b p) q44
capturesq44-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct4 p q34 q24 q14 q04 c34 c24 c14 c04) (append-cong (Lines.correct1 p q35 c35) (append-cong (Lines.correct1 p q45 c45) (append-cong (Lines.correct1 p q55 c55) (append-cong (Lines.correct1 p q54 c54) (append-cong (Lines.correct1 p q53 c53) (append-cong (Lines.correct4 p q43 q42 q41 q40 c43 c42 c41 c40) (append-cong (Lines.correct4 p q33 q22 q11 q00 c33 c22 c11 c00) (refl)))))))))
  (Old.capturesq44-correct b p)

capturesq45 : Board six → Player → List (Coord six)
capturesq45 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count4 p c35 c25 c15 c05) (q35 ∷ q25 ∷ q15 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count1 p c55) (q55 ∷ [])) ++ (Lines.prefix (Lines.count1 p c54) (q54 ∷ [])) ++ (Lines.prefix (Lines.count5 p c44 c43 c42 c41 c40) (q44 ∷ q43 ∷ q42 ∷ q41 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count4 p c34 c23 c12 c01) (q34 ∷ q23 ∷ q12 ∷ q01 ∷ [])) ++ []

capturesq45-correct : ∀ b p → capturesq45 b p ≡ Fast.allCaptures6 (state b p) q45
capturesq45-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct4 p q35 q25 q15 q05 c35 c25 c15 c05) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct1 p q55 c55) (append-cong (Lines.correct1 p q54 c54) (append-cong (Lines.correct5 p q44 q43 q42 q41 q40 c44 c43 c42 c41 c40) (append-cong (Lines.correct4 p q34 q23 q12 q01 c34 c23 c12 c01) (refl)))))))))
  (Old.capturesq45-correct b p)

capturesq50 : Board six → Player → List (Coord six)
capturesq50 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count5 p c40 c30 c20 c10 c00) (q40 ∷ q30 ∷ q20 ∷ q10 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count5 p c41 c32 c23 c14 c05) (q41 ∷ q32 ∷ q23 ∷ q14 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count5 p c51 c52 c53 c54 c55) (q51 ∷ q52 ∷ q53 ∷ q54 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []

capturesq50-correct : ∀ b p → capturesq50 b p ≡ Fast.allCaptures6 (state b p) q50
capturesq50-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct5 p q40 q30 q20 q10 q00 c40 c30 c20 c10 c00) (append-cong (Lines.correct5 p q41 q32 q23 q14 q05 c41 c32 c23 c14 c05) (append-cong (Lines.correct5 p q51 q52 q53 q54 q55 c51 c52 c53 c54 c55) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (refl)))))))))
  (Old.capturesq50-correct b p)

capturesq51 : Board six → Player → List (Coord six)
capturesq51 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count5 p c41 c31 c21 c11 c01) (q41 ∷ q31 ∷ q21 ∷ q11 ∷ q01 ∷ [])) ++ (Lines.prefix (Lines.count4 p c42 c33 c24 c15) (q42 ∷ q33 ∷ q24 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count4 p c52 c53 c54 c55) (q52 ∷ q53 ∷ q54 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count1 p c50) (q50 ∷ [])) ++ (Lines.prefix (Lines.count1 p c40) (q40 ∷ [])) ++ []

capturesq51-correct : ∀ b p → capturesq51 b p ≡ Fast.allCaptures6 (state b p) q51
capturesq51-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct5 p q41 q31 q21 q11 q01 c41 c31 c21 c11 c01) (append-cong (Lines.correct4 p q42 q33 q24 q15 c42 c33 c24 c15) (append-cong (Lines.correct4 p q52 q53 q54 q55 c52 c53 c54 c55) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct1 p q50 c50) (append-cong (Lines.correct1 p q40 c40) (refl)))))))))
  (Old.capturesq51-correct b p)

capturesq52 : Board six → Player → List (Coord six)
capturesq52 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count5 p c42 c32 c22 c12 c02) (q42 ∷ q32 ∷ q22 ∷ q12 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count3 p c43 c34 c25) (q43 ∷ q34 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count3 p c53 c54 c55) (q53 ∷ q54 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count2 p c51 c50) (q51 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c30) (q41 ∷ q30 ∷ [])) ++ []

capturesq52-correct : ∀ b p → capturesq52 b p ≡ Fast.allCaptures6 (state b p) q52
capturesq52-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct5 p q42 q32 q22 q12 q02 c42 c32 c22 c12 c02) (append-cong (Lines.correct3 p q43 q34 q25 c43 c34 c25) (append-cong (Lines.correct3 p q53 q54 q55 c53 c54 c55) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct2 p q51 q50 c51 c50) (append-cong (Lines.correct2 p q41 q30 c41 c30) (refl)))))))))
  (Old.capturesq52-correct b p)

capturesq53 : Board six → Player → List (Coord six)
capturesq53 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count5 p c43 c33 c23 c13 c03) (q43 ∷ q33 ∷ q23 ∷ q13 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c35) (q44 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c54 c55) (q54 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count3 p c52 c51 c50) (q52 ∷ q51 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count3 p c42 c31 c20) (q42 ∷ q31 ∷ q20 ∷ [])) ++ []

capturesq53-correct : ∀ b p → capturesq53 b p ≡ Fast.allCaptures6 (state b p) q53
capturesq53-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct5 p q43 q33 q23 q13 q03 c43 c33 c23 c13 c03) (append-cong (Lines.correct2 p q44 q35 c44 c35) (append-cong (Lines.correct2 p q54 q55 c54 c55) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct3 p q52 q51 q50 c52 c51 c50) (append-cong (Lines.correct3 p q42 q31 q20 c42 c31 c20) (refl)))))))))
  (Old.capturesq53-correct b p)

capturesq54 : Board six → Player → List (Coord six)
capturesq54 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count5 p c44 c34 c24 c14 c04) (q44 ∷ q34 ∷ q24 ∷ q14 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c45) (q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c55) (q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count4 p c53 c52 c51 c50) (q53 ∷ q52 ∷ q51 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count4 p c43 c32 c21 c10) (q43 ∷ q32 ∷ q21 ∷ q10 ∷ [])) ++ []

capturesq54-correct : ∀ b p → capturesq54 b p ≡ Fast.allCaptures6 (state b p) q54
capturesq54-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct5 p q44 q34 q24 q14 q04 c44 c34 c24 c14 c04) (append-cong (Lines.correct1 p q45 c45) (append-cong (Lines.correct1 p q55 c55) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct4 p q53 q52 q51 q50 c53 c52 c51 c50) (append-cong (Lines.correct4 p q43 q32 q21 q10 c43 c32 c21 c10) (refl)))))))))
  (Old.capturesq54-correct b p)

capturesq55 : Board six → Player → List (Coord six)
capturesq55 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p =
  (Lines.prefix (Lines.count5 p c45 c35 c25 c15 c05) (q45 ∷ q35 ∷ q25 ∷ q15 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count5 p c54 c53 c52 c51 c50) (q54 ∷ q53 ∷ q52 ∷ q51 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count5 p c44 c33 c22 c11 c00) (q44 ∷ q33 ∷ q22 ∷ q11 ∷ q00 ∷ [])) ++ []

capturesq55-correct : ∀ b p → capturesq55 b p ≡ Fast.allCaptures6 (state b p) q55
capturesq55-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = trans
  (append-cong (Lines.correct5 p q45 q35 q25 q15 q05 c45 c35 c25 c15 c05) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct0 p) (append-cong (Lines.correct5 p q54 q53 q52 q51 q50 c54 c53 c52 c51 c50) (append-cong (Lines.correct5 p q44 q33 q22 q11 q00 c44 c33 c22 c11 c00) (refl)))))))))
  (Old.capturesq55-correct b p)

candidateCell : State six → Coord six → Cell → List (Coord six) → List (State six) → List (State six)
candidateCell s q c xs tail with sameCell c empty ∧ nonempty xs
... | false = tail
... | true = state (put {six} (Incremental.flipMany (board s) (toMove s) xs) q (playerCell (toMove s)))
  (other (toMove s)) ∷ tail

candidateCell-correct : ∀ s q xs tail →
  candidateCell s q (at {six} (board s) q) xs tail ≡ Incremental.candidate s q xs tail
candidateCell-correct s q xs tail with sameCell (at {six} (board s) q) empty ∧ nonempty xs
... | false = refl
... | true = refl

record Entry : Set where
  constructor entry
  field
    coord : Coord six
    cell : Cell
    captures : List (Coord six)

movesEntries : State six → List Entry → List (State six)
movesEntries s [] = []
movesEntries s (entry q c caps ∷ rest) = candidateCell s q c caps (movesEntries s rest)

data EntriesOK (s : State six) : List Entry → List (Coord six) → Set where
  ok-nil : EntriesOK s [] []
  ok-cons : ∀ {q c caps rest qs} → c ≡ at {six} (board s) q →
    caps ≡ Fast.allCaptures6 s q → EntriesOK s rest qs →
    EntriesOK s (entry q c caps ∷ rest) (q ∷ qs)

movesEntries-correct : ∀ s es qs → EntriesOK s es qs → movesEntries s es ≡ Incremental.moves s qs
movesEntries-correct s [] [] ok-nil = refl
movesEntries-correct s (entry q c caps ∷ rest) (.q ∷ qs) (ok-cons ce cape restOK)
  rewrite ce | cape | movesEntries-correct s rest qs restOK =
    candidateCell-correct s q (Fast.allCaptures6 s q) (Incremental.moves s qs)

entries : State six → List Entry
entries (state b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) =
  (entry q00 c00 (capturesq00 b p)) ∷ (entry q01 c01 (capturesq01 b p)) ∷ (entry q02 c02 (capturesq02 b p)) ∷ (entry q03 c03 (capturesq03 b p)) ∷ (entry q04 c04 (capturesq04 b p)) ∷ (entry q05 c05 (capturesq05 b p)) ∷ (entry q10 c10 (capturesq10 b p)) ∷ (entry q11 c11 (capturesq11 b p)) ∷ (entry q12 c12 (capturesq12 b p)) ∷ (entry q13 c13 (capturesq13 b p)) ∷ (entry q14 c14 (capturesq14 b p)) ∷ (entry q15 c15 (capturesq15 b p)) ∷ (entry q20 c20 (capturesq20 b p)) ∷ (entry q21 c21 (capturesq21 b p)) ∷ (entry q22 c22 (capturesq22 b p)) ∷ (entry q23 c23 (capturesq23 b p)) ∷ (entry q24 c24 (capturesq24 b p)) ∷ (entry q25 c25 (capturesq25 b p)) ∷ (entry q30 c30 (capturesq30 b p)) ∷ (entry q31 c31 (capturesq31 b p)) ∷ (entry q32 c32 (capturesq32 b p)) ∷ (entry q33 c33 (capturesq33 b p)) ∷ (entry q34 c34 (capturesq34 b p)) ∷ (entry q35 c35 (capturesq35 b p)) ∷ (entry q40 c40 (capturesq40 b p)) ∷ (entry q41 c41 (capturesq41 b p)) ∷ (entry q42 c42 (capturesq42 b p)) ∷ (entry q43 c43 (capturesq43 b p)) ∷ (entry q44 c44 (capturesq44 b p)) ∷ (entry q45 c45 (capturesq45 b p)) ∷ (entry q50 c50 (capturesq50 b p)) ∷ (entry q51 c51 (capturesq51 b p)) ∷ (entry q52 c52 (capturesq52 b p)) ∷ (entry q53 c53 (capturesq53 b p)) ∷ (entry q54 c54 (capturesq54 b p)) ∷ (entry q55 c55 (capturesq55 b p)) ∷ []

entries-correct : ∀ s → EntriesOK s (entries s) (coords six)
entries-correct (state b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) =
  ok-cons refl (capturesq00-correct b p) (ok-cons refl (capturesq01-correct b p) (ok-cons refl (capturesq02-correct b p) (ok-cons refl (capturesq03-correct b p) (ok-cons refl (capturesq04-correct b p) (ok-cons refl (capturesq05-correct b p) (ok-cons refl (capturesq10-correct b p) (ok-cons refl (capturesq11-correct b p) (ok-cons refl (capturesq12-correct b p) (ok-cons refl (capturesq13-correct b p) (ok-cons refl (capturesq14-correct b p) (ok-cons refl (capturesq15-correct b p) (ok-cons refl (capturesq20-correct b p) (ok-cons refl (capturesq21-correct b p) (ok-cons refl (capturesq22-correct b p) (ok-cons refl (capturesq23-correct b p) (ok-cons refl (capturesq24-correct b p) (ok-cons refl (capturesq25-correct b p) (ok-cons refl (capturesq30-correct b p) (ok-cons refl (capturesq31-correct b p) (ok-cons refl (capturesq32-correct b p) (ok-cons refl (capturesq33-correct b p) (ok-cons refl (capturesq34-correct b p) (ok-cons refl (capturesq35-correct b p) (ok-cons refl (capturesq40-correct b p) (ok-cons refl (capturesq41-correct b p) (ok-cons refl (capturesq42-correct b p) (ok-cons refl (capturesq43-correct b p) (ok-cons refl (capturesq44-correct b p) (ok-cons refl (capturesq45-correct b p) (ok-cons refl (capturesq50-correct b p) (ok-cons refl (capturesq51-correct b p) (ok-cons refl (capturesq52-correct b p) (ok-cons refl (capturesq53-correct b p) (ok-cons refl (capturesq54-correct b p) (ok-cons refl (capturesq55-correct b p) (ok-nil))))))))))))))))))))))))))))))))))))

moves : State six → List (State six)
moves s = movesEntries s (entries s)

moves-agree : ∀ s → moves s ≡ Fast.moves6 s (coords six)
moves-agree s = trans (movesEntries-correct s (entries s) (coords six) (entries-correct s))
  (Incremental.moves-agree s (coords six))

successors : State six → List (State six)
successors s = Fast.finish6 s (moves s) (moves (passState s))

successors-agree : ∀ s → successors s ≡ Fast.fastSuccessors s
successors-agree s rewrite moves-agree s | moves-agree (passState s) = refl

passShape : List (State six) → List (State six) → Bool
passShape [] [] = false
passShape [] (_ ∷ _) = true
passShape (_ ∷ _) opposing = false

forcedPass : State six → Bool
forcedPass s = passShape (moves s) (moves (passState s))

passShape-correct : ∀ s →
  passShape (map (Rules.applyMove s) (Rules.legalMoves s))
    (map (Rules.applyMove (passState s)) (Rules.legalMoves (passState s))) ≡ Rules.forcedPass s
passShape-correct s with Rules.legalMoves s | Rules.legalMoves (passState s)
... | [] | [] = refl
... | [] | (_ ∷ _) = refl
... | (_ ∷ _) | [] = refl
... | (_ ∷ _) | (_ ∷ _) = refl

forcedPass-agree : ∀ s → forcedPass s ≡ Rules.forcedPass s
forcedPass-agree s rewrite moves-agree s | moves-agree (passState s)
  | Fast.moves6-correct s (coords six) | Fast.moves6-correct (passState s) (coords six) = passShape-correct s

specializedGame6 : G.Game (State six)
specializedGame6 = record { turn = toMove ; next = successors ; forcedPass = forcedPass }

agreement : T.Agreement specializedGame6 Fast.fastGame6
agreement = T.agreement successors-agree (λ s → refl) forcedPass-agree
