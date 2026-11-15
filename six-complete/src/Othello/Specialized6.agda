{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted generated geometry, checked against the original rays.
-- This module supplies no initial-board bound.
module Othello.Specialized6 where

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

capturesq00 : Board six → Player → List (Coord six)
capturesq00 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (([]) ∷ ([]) ∷ ((q01 , c01) ∷ (q02 , c02) ∷ (q03 , c03) ∷ (q04 , c04) ∷ (q05 , c05) ∷ []) ∷ ((q11 , c11) ∷ (q22 , c22) ∷ (q33 , c33) ∷ (q44 , c44) ∷ (q55 , c55) ∷ []) ∷ ((q10 , c10) ∷ (q20 , c20) ∷ (q30 , c30) ∷ (q40 , c40) ∷ (q50 , c50) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ [])

capturesq00-correct : ∀ b p → capturesq00 b p ≡ Fast.allCaptures6 (state b p) q00
capturesq00-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q00

capturesq01 : Board six → Player → List (Coord six)
capturesq01 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (([]) ∷ ([]) ∷ ((q02 , c02) ∷ (q03 , c03) ∷ (q04 , c04) ∷ (q05 , c05) ∷ []) ∷ ((q12 , c12) ∷ (q23 , c23) ∷ (q34 , c34) ∷ (q45 , c45) ∷ []) ∷ ((q11 , c11) ∷ (q21 , c21) ∷ (q31 , c31) ∷ (q41 , c41) ∷ (q51 , c51) ∷ []) ∷ ((q10 , c10) ∷ []) ∷ ((q00 , c00) ∷ []) ∷ ([]) ∷ [])

capturesq01-correct : ∀ b p → capturesq01 b p ≡ Fast.allCaptures6 (state b p) q01
capturesq01-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q01

capturesq02 : Board six → Player → List (Coord six)
capturesq02 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (([]) ∷ ([]) ∷ ((q03 , c03) ∷ (q04 , c04) ∷ (q05 , c05) ∷ []) ∷ ((q13 , c13) ∷ (q24 , c24) ∷ (q35 , c35) ∷ []) ∷ ((q12 , c12) ∷ (q22 , c22) ∷ (q32 , c32) ∷ (q42 , c42) ∷ (q52 , c52) ∷ []) ∷ ((q11 , c11) ∷ (q20 , c20) ∷ []) ∷ ((q01 , c01) ∷ (q00 , c00) ∷ []) ∷ ([]) ∷ [])

capturesq02-correct : ∀ b p → capturesq02 b p ≡ Fast.allCaptures6 (state b p) q02
capturesq02-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q02

capturesq03 : Board six → Player → List (Coord six)
capturesq03 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (([]) ∷ ([]) ∷ ((q04 , c04) ∷ (q05 , c05) ∷ []) ∷ ((q14 , c14) ∷ (q25 , c25) ∷ []) ∷ ((q13 , c13) ∷ (q23 , c23) ∷ (q33 , c33) ∷ (q43 , c43) ∷ (q53 , c53) ∷ []) ∷ ((q12 , c12) ∷ (q21 , c21) ∷ (q30 , c30) ∷ []) ∷ ((q02 , c02) ∷ (q01 , c01) ∷ (q00 , c00) ∷ []) ∷ ([]) ∷ [])

capturesq03-correct : ∀ b p → capturesq03 b p ≡ Fast.allCaptures6 (state b p) q03
capturesq03-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q03

capturesq04 : Board six → Player → List (Coord six)
capturesq04 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (([]) ∷ ([]) ∷ ((q05 , c05) ∷ []) ∷ ((q15 , c15) ∷ []) ∷ ((q14 , c14) ∷ (q24 , c24) ∷ (q34 , c34) ∷ (q44 , c44) ∷ (q54 , c54) ∷ []) ∷ ((q13 , c13) ∷ (q22 , c22) ∷ (q31 , c31) ∷ (q40 , c40) ∷ []) ∷ ((q03 , c03) ∷ (q02 , c02) ∷ (q01 , c01) ∷ (q00 , c00) ∷ []) ∷ ([]) ∷ [])

capturesq04-correct : ∀ b p → capturesq04 b p ≡ Fast.allCaptures6 (state b p) q04
capturesq04-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q04

capturesq05 : Board six → Player → List (Coord six)
capturesq05 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (([]) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q15 , c15) ∷ (q25 , c25) ∷ (q35 , c35) ∷ (q45 , c45) ∷ (q55 , c55) ∷ []) ∷ ((q14 , c14) ∷ (q23 , c23) ∷ (q32 , c32) ∷ (q41 , c41) ∷ (q50 , c50) ∷ []) ∷ ((q04 , c04) ∷ (q03 , c03) ∷ (q02 , c02) ∷ (q01 , c01) ∷ (q00 , c00) ∷ []) ∷ ([]) ∷ [])

capturesq05-correct : ∀ b p → capturesq05 b p ≡ Fast.allCaptures6 (state b p) q05
capturesq05-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q05

capturesq10 : Board six → Player → List (Coord six)
capturesq10 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q00 , c00) ∷ []) ∷ ((q01 , c01) ∷ []) ∷ ((q11 , c11) ∷ (q12 , c12) ∷ (q13 , c13) ∷ (q14 , c14) ∷ (q15 , c15) ∷ []) ∷ ((q21 , c21) ∷ (q32 , c32) ∷ (q43 , c43) ∷ (q54 , c54) ∷ []) ∷ ((q20 , c20) ∷ (q30 , c30) ∷ (q40 , c40) ∷ (q50 , c50) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ [])

capturesq10-correct : ∀ b p → capturesq10 b p ≡ Fast.allCaptures6 (state b p) q10
capturesq10-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q10

capturesq11 : Board six → Player → List (Coord six)
capturesq11 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q01 , c01) ∷ []) ∷ ((q02 , c02) ∷ []) ∷ ((q12 , c12) ∷ (q13 , c13) ∷ (q14 , c14) ∷ (q15 , c15) ∷ []) ∷ ((q22 , c22) ∷ (q33 , c33) ∷ (q44 , c44) ∷ (q55 , c55) ∷ []) ∷ ((q21 , c21) ∷ (q31 , c31) ∷ (q41 , c41) ∷ (q51 , c51) ∷ []) ∷ ((q20 , c20) ∷ []) ∷ ((q10 , c10) ∷ []) ∷ ((q00 , c00) ∷ []) ∷ [])

capturesq11-correct : ∀ b p → capturesq11 b p ≡ Fast.allCaptures6 (state b p) q11
capturesq11-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q11

capturesq12 : Board six → Player → List (Coord six)
capturesq12 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q02 , c02) ∷ []) ∷ ((q03 , c03) ∷ []) ∷ ((q13 , c13) ∷ (q14 , c14) ∷ (q15 , c15) ∷ []) ∷ ((q23 , c23) ∷ (q34 , c34) ∷ (q45 , c45) ∷ []) ∷ ((q22 , c22) ∷ (q32 , c32) ∷ (q42 , c42) ∷ (q52 , c52) ∷ []) ∷ ((q21 , c21) ∷ (q30 , c30) ∷ []) ∷ ((q11 , c11) ∷ (q10 , c10) ∷ []) ∷ ((q01 , c01) ∷ []) ∷ [])

capturesq12-correct : ∀ b p → capturesq12 b p ≡ Fast.allCaptures6 (state b p) q12
capturesq12-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q12

capturesq13 : Board six → Player → List (Coord six)
capturesq13 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q03 , c03) ∷ []) ∷ ((q04 , c04) ∷ []) ∷ ((q14 , c14) ∷ (q15 , c15) ∷ []) ∷ ((q24 , c24) ∷ (q35 , c35) ∷ []) ∷ ((q23 , c23) ∷ (q33 , c33) ∷ (q43 , c43) ∷ (q53 , c53) ∷ []) ∷ ((q22 , c22) ∷ (q31 , c31) ∷ (q40 , c40) ∷ []) ∷ ((q12 , c12) ∷ (q11 , c11) ∷ (q10 , c10) ∷ []) ∷ ((q02 , c02) ∷ []) ∷ [])

capturesq13-correct : ∀ b p → capturesq13 b p ≡ Fast.allCaptures6 (state b p) q13
capturesq13-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q13

capturesq14 : Board six → Player → List (Coord six)
capturesq14 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q04 , c04) ∷ []) ∷ ((q05 , c05) ∷ []) ∷ ((q15 , c15) ∷ []) ∷ ((q25 , c25) ∷ []) ∷ ((q24 , c24) ∷ (q34 , c34) ∷ (q44 , c44) ∷ (q54 , c54) ∷ []) ∷ ((q23 , c23) ∷ (q32 , c32) ∷ (q41 , c41) ∷ (q50 , c50) ∷ []) ∷ ((q13 , c13) ∷ (q12 , c12) ∷ (q11 , c11) ∷ (q10 , c10) ∷ []) ∷ ((q03 , c03) ∷ []) ∷ [])

capturesq14-correct : ∀ b p → capturesq14 b p ≡ Fast.allCaptures6 (state b p) q14
capturesq14-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q14

capturesq15 : Board six → Player → List (Coord six)
capturesq15 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q05 , c05) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q25 , c25) ∷ (q35 , c35) ∷ (q45 , c45) ∷ (q55 , c55) ∷ []) ∷ ((q24 , c24) ∷ (q33 , c33) ∷ (q42 , c42) ∷ (q51 , c51) ∷ []) ∷ ((q14 , c14) ∷ (q13 , c13) ∷ (q12 , c12) ∷ (q11 , c11) ∷ (q10 , c10) ∷ []) ∷ ((q04 , c04) ∷ []) ∷ [])

capturesq15-correct : ∀ b p → capturesq15 b p ≡ Fast.allCaptures6 (state b p) q15
capturesq15-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q15

capturesq20 : Board six → Player → List (Coord six)
capturesq20 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q10 , c10) ∷ (q00 , c00) ∷ []) ∷ ((q11 , c11) ∷ (q02 , c02) ∷ []) ∷ ((q21 , c21) ∷ (q22 , c22) ∷ (q23 , c23) ∷ (q24 , c24) ∷ (q25 , c25) ∷ []) ∷ ((q31 , c31) ∷ (q42 , c42) ∷ (q53 , c53) ∷ []) ∷ ((q30 , c30) ∷ (q40 , c40) ∷ (q50 , c50) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ [])

capturesq20-correct : ∀ b p → capturesq20 b p ≡ Fast.allCaptures6 (state b p) q20
capturesq20-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q20

capturesq21 : Board six → Player → List (Coord six)
capturesq21 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q11 , c11) ∷ (q01 , c01) ∷ []) ∷ ((q12 , c12) ∷ (q03 , c03) ∷ []) ∷ ((q22 , c22) ∷ (q23 , c23) ∷ (q24 , c24) ∷ (q25 , c25) ∷ []) ∷ ((q32 , c32) ∷ (q43 , c43) ∷ (q54 , c54) ∷ []) ∷ ((q31 , c31) ∷ (q41 , c41) ∷ (q51 , c51) ∷ []) ∷ ((q30 , c30) ∷ []) ∷ ((q20 , c20) ∷ []) ∷ ((q10 , c10) ∷ []) ∷ [])

capturesq21-correct : ∀ b p → capturesq21 b p ≡ Fast.allCaptures6 (state b p) q21
capturesq21-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q21

capturesq22 : Board six → Player → List (Coord six)
capturesq22 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q12 , c12) ∷ (q02 , c02) ∷ []) ∷ ((q13 , c13) ∷ (q04 , c04) ∷ []) ∷ ((q23 , c23) ∷ (q24 , c24) ∷ (q25 , c25) ∷ []) ∷ ((q33 , c33) ∷ (q44 , c44) ∷ (q55 , c55) ∷ []) ∷ ((q32 , c32) ∷ (q42 , c42) ∷ (q52 , c52) ∷ []) ∷ ((q31 , c31) ∷ (q40 , c40) ∷ []) ∷ ((q21 , c21) ∷ (q20 , c20) ∷ []) ∷ ((q11 , c11) ∷ (q00 , c00) ∷ []) ∷ [])

capturesq22-correct : ∀ b p → capturesq22 b p ≡ Fast.allCaptures6 (state b p) q22
capturesq22-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q22

capturesq23 : Board six → Player → List (Coord six)
capturesq23 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q13 , c13) ∷ (q03 , c03) ∷ []) ∷ ((q14 , c14) ∷ (q05 , c05) ∷ []) ∷ ((q24 , c24) ∷ (q25 , c25) ∷ []) ∷ ((q34 , c34) ∷ (q45 , c45) ∷ []) ∷ ((q33 , c33) ∷ (q43 , c43) ∷ (q53 , c53) ∷ []) ∷ ((q32 , c32) ∷ (q41 , c41) ∷ (q50 , c50) ∷ []) ∷ ((q22 , c22) ∷ (q21 , c21) ∷ (q20 , c20) ∷ []) ∷ ((q12 , c12) ∷ (q01 , c01) ∷ []) ∷ [])

capturesq23-correct : ∀ b p → capturesq23 b p ≡ Fast.allCaptures6 (state b p) q23
capturesq23-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q23

capturesq24 : Board six → Player → List (Coord six)
capturesq24 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q14 , c14) ∷ (q04 , c04) ∷ []) ∷ ((q15 , c15) ∷ []) ∷ ((q25 , c25) ∷ []) ∷ ((q35 , c35) ∷ []) ∷ ((q34 , c34) ∷ (q44 , c44) ∷ (q54 , c54) ∷ []) ∷ ((q33 , c33) ∷ (q42 , c42) ∷ (q51 , c51) ∷ []) ∷ ((q23 , c23) ∷ (q22 , c22) ∷ (q21 , c21) ∷ (q20 , c20) ∷ []) ∷ ((q13 , c13) ∷ (q02 , c02) ∷ []) ∷ [])

capturesq24-correct : ∀ b p → capturesq24 b p ≡ Fast.allCaptures6 (state b p) q24
capturesq24-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q24

capturesq25 : Board six → Player → List (Coord six)
capturesq25 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q15 , c15) ∷ (q05 , c05) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q35 , c35) ∷ (q45 , c45) ∷ (q55 , c55) ∷ []) ∷ ((q34 , c34) ∷ (q43 , c43) ∷ (q52 , c52) ∷ []) ∷ ((q24 , c24) ∷ (q23 , c23) ∷ (q22 , c22) ∷ (q21 , c21) ∷ (q20 , c20) ∷ []) ∷ ((q14 , c14) ∷ (q03 , c03) ∷ []) ∷ [])

capturesq25-correct : ∀ b p → capturesq25 b p ≡ Fast.allCaptures6 (state b p) q25
capturesq25-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q25

capturesq30 : Board six → Player → List (Coord six)
capturesq30 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q20 , c20) ∷ (q10 , c10) ∷ (q00 , c00) ∷ []) ∷ ((q21 , c21) ∷ (q12 , c12) ∷ (q03 , c03) ∷ []) ∷ ((q31 , c31) ∷ (q32 , c32) ∷ (q33 , c33) ∷ (q34 , c34) ∷ (q35 , c35) ∷ []) ∷ ((q41 , c41) ∷ (q52 , c52) ∷ []) ∷ ((q40 , c40) ∷ (q50 , c50) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ [])

capturesq30-correct : ∀ b p → capturesq30 b p ≡ Fast.allCaptures6 (state b p) q30
capturesq30-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q30

capturesq31 : Board six → Player → List (Coord six)
capturesq31 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q21 , c21) ∷ (q11 , c11) ∷ (q01 , c01) ∷ []) ∷ ((q22 , c22) ∷ (q13 , c13) ∷ (q04 , c04) ∷ []) ∷ ((q32 , c32) ∷ (q33 , c33) ∷ (q34 , c34) ∷ (q35 , c35) ∷ []) ∷ ((q42 , c42) ∷ (q53 , c53) ∷ []) ∷ ((q41 , c41) ∷ (q51 , c51) ∷ []) ∷ ((q40 , c40) ∷ []) ∷ ((q30 , c30) ∷ []) ∷ ((q20 , c20) ∷ []) ∷ [])

capturesq31-correct : ∀ b p → capturesq31 b p ≡ Fast.allCaptures6 (state b p) q31
capturesq31-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q31

capturesq32 : Board six → Player → List (Coord six)
capturesq32 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q22 , c22) ∷ (q12 , c12) ∷ (q02 , c02) ∷ []) ∷ ((q23 , c23) ∷ (q14 , c14) ∷ (q05 , c05) ∷ []) ∷ ((q33 , c33) ∷ (q34 , c34) ∷ (q35 , c35) ∷ []) ∷ ((q43 , c43) ∷ (q54 , c54) ∷ []) ∷ ((q42 , c42) ∷ (q52 , c52) ∷ []) ∷ ((q41 , c41) ∷ (q50 , c50) ∷ []) ∷ ((q31 , c31) ∷ (q30 , c30) ∷ []) ∷ ((q21 , c21) ∷ (q10 , c10) ∷ []) ∷ [])

capturesq32-correct : ∀ b p → capturesq32 b p ≡ Fast.allCaptures6 (state b p) q32
capturesq32-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q32

capturesq33 : Board six → Player → List (Coord six)
capturesq33 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q23 , c23) ∷ (q13 , c13) ∷ (q03 , c03) ∷ []) ∷ ((q24 , c24) ∷ (q15 , c15) ∷ []) ∷ ((q34 , c34) ∷ (q35 , c35) ∷ []) ∷ ((q44 , c44) ∷ (q55 , c55) ∷ []) ∷ ((q43 , c43) ∷ (q53 , c53) ∷ []) ∷ ((q42 , c42) ∷ (q51 , c51) ∷ []) ∷ ((q32 , c32) ∷ (q31 , c31) ∷ (q30 , c30) ∷ []) ∷ ((q22 , c22) ∷ (q11 , c11) ∷ (q00 , c00) ∷ []) ∷ [])

capturesq33-correct : ∀ b p → capturesq33 b p ≡ Fast.allCaptures6 (state b p) q33
capturesq33-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q33

capturesq34 : Board six → Player → List (Coord six)
capturesq34 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q24 , c24) ∷ (q14 , c14) ∷ (q04 , c04) ∷ []) ∷ ((q25 , c25) ∷ []) ∷ ((q35 , c35) ∷ []) ∷ ((q45 , c45) ∷ []) ∷ ((q44 , c44) ∷ (q54 , c54) ∷ []) ∷ ((q43 , c43) ∷ (q52 , c52) ∷ []) ∷ ((q33 , c33) ∷ (q32 , c32) ∷ (q31 , c31) ∷ (q30 , c30) ∷ []) ∷ ((q23 , c23) ∷ (q12 , c12) ∷ (q01 , c01) ∷ []) ∷ [])

capturesq34-correct : ∀ b p → capturesq34 b p ≡ Fast.allCaptures6 (state b p) q34
capturesq34-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q34

capturesq35 : Board six → Player → List (Coord six)
capturesq35 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q25 , c25) ∷ (q15 , c15) ∷ (q05 , c05) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q45 , c45) ∷ (q55 , c55) ∷ []) ∷ ((q44 , c44) ∷ (q53 , c53) ∷ []) ∷ ((q34 , c34) ∷ (q33 , c33) ∷ (q32 , c32) ∷ (q31 , c31) ∷ (q30 , c30) ∷ []) ∷ ((q24 , c24) ∷ (q13 , c13) ∷ (q02 , c02) ∷ []) ∷ [])

capturesq35-correct : ∀ b p → capturesq35 b p ≡ Fast.allCaptures6 (state b p) q35
capturesq35-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q35

capturesq40 : Board six → Player → List (Coord six)
capturesq40 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q30 , c30) ∷ (q20 , c20) ∷ (q10 , c10) ∷ (q00 , c00) ∷ []) ∷ ((q31 , c31) ∷ (q22 , c22) ∷ (q13 , c13) ∷ (q04 , c04) ∷ []) ∷ ((q41 , c41) ∷ (q42 , c42) ∷ (q43 , c43) ∷ (q44 , c44) ∷ (q45 , c45) ∷ []) ∷ ((q51 , c51) ∷ []) ∷ ((q50 , c50) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ [])

capturesq40-correct : ∀ b p → capturesq40 b p ≡ Fast.allCaptures6 (state b p) q40
capturesq40-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q40

capturesq41 : Board six → Player → List (Coord six)
capturesq41 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q31 , c31) ∷ (q21 , c21) ∷ (q11 , c11) ∷ (q01 , c01) ∷ []) ∷ ((q32 , c32) ∷ (q23 , c23) ∷ (q14 , c14) ∷ (q05 , c05) ∷ []) ∷ ((q42 , c42) ∷ (q43 , c43) ∷ (q44 , c44) ∷ (q45 , c45) ∷ []) ∷ ((q52 , c52) ∷ []) ∷ ((q51 , c51) ∷ []) ∷ ((q50 , c50) ∷ []) ∷ ((q40 , c40) ∷ []) ∷ ((q30 , c30) ∷ []) ∷ [])

capturesq41-correct : ∀ b p → capturesq41 b p ≡ Fast.allCaptures6 (state b p) q41
capturesq41-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q41

capturesq42 : Board six → Player → List (Coord six)
capturesq42 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q32 , c32) ∷ (q22 , c22) ∷ (q12 , c12) ∷ (q02 , c02) ∷ []) ∷ ((q33 , c33) ∷ (q24 , c24) ∷ (q15 , c15) ∷ []) ∷ ((q43 , c43) ∷ (q44 , c44) ∷ (q45 , c45) ∷ []) ∷ ((q53 , c53) ∷ []) ∷ ((q52 , c52) ∷ []) ∷ ((q51 , c51) ∷ []) ∷ ((q41 , c41) ∷ (q40 , c40) ∷ []) ∷ ((q31 , c31) ∷ (q20 , c20) ∷ []) ∷ [])

capturesq42-correct : ∀ b p → capturesq42 b p ≡ Fast.allCaptures6 (state b p) q42
capturesq42-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q42

capturesq43 : Board six → Player → List (Coord six)
capturesq43 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q33 , c33) ∷ (q23 , c23) ∷ (q13 , c13) ∷ (q03 , c03) ∷ []) ∷ ((q34 , c34) ∷ (q25 , c25) ∷ []) ∷ ((q44 , c44) ∷ (q45 , c45) ∷ []) ∷ ((q54 , c54) ∷ []) ∷ ((q53 , c53) ∷ []) ∷ ((q52 , c52) ∷ []) ∷ ((q42 , c42) ∷ (q41 , c41) ∷ (q40 , c40) ∷ []) ∷ ((q32 , c32) ∷ (q21 , c21) ∷ (q10 , c10) ∷ []) ∷ [])

capturesq43-correct : ∀ b p → capturesq43 b p ≡ Fast.allCaptures6 (state b p) q43
capturesq43-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q43

capturesq44 : Board six → Player → List (Coord six)
capturesq44 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q34 , c34) ∷ (q24 , c24) ∷ (q14 , c14) ∷ (q04 , c04) ∷ []) ∷ ((q35 , c35) ∷ []) ∷ ((q45 , c45) ∷ []) ∷ ((q55 , c55) ∷ []) ∷ ((q54 , c54) ∷ []) ∷ ((q53 , c53) ∷ []) ∷ ((q43 , c43) ∷ (q42 , c42) ∷ (q41 , c41) ∷ (q40 , c40) ∷ []) ∷ ((q33 , c33) ∷ (q22 , c22) ∷ (q11 , c11) ∷ (q00 , c00) ∷ []) ∷ [])

capturesq44-correct : ∀ b p → capturesq44 b p ≡ Fast.allCaptures6 (state b p) q44
capturesq44-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q44

capturesq45 : Board six → Player → List (Coord six)
capturesq45 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q35 , c35) ∷ (q25 , c25) ∷ (q15 , c15) ∷ (q05 , c05) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q55 , c55) ∷ []) ∷ ((q54 , c54) ∷ []) ∷ ((q44 , c44) ∷ (q43 , c43) ∷ (q42 , c42) ∷ (q41 , c41) ∷ (q40 , c40) ∷ []) ∷ ((q34 , c34) ∷ (q23 , c23) ∷ (q12 , c12) ∷ (q01 , c01) ∷ []) ∷ [])

capturesq45-correct : ∀ b p → capturesq45 b p ≡ Fast.allCaptures6 (state b p) q45
capturesq45-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q45

capturesq50 : Board six → Player → List (Coord six)
capturesq50 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q40 , c40) ∷ (q30 , c30) ∷ (q20 , c20) ∷ (q10 , c10) ∷ (q00 , c00) ∷ []) ∷ ((q41 , c41) ∷ (q32 , c32) ∷ (q23 , c23) ∷ (q14 , c14) ∷ (q05 , c05) ∷ []) ∷ ((q51 , c51) ∷ (q52 , c52) ∷ (q53 , c53) ∷ (q54 , c54) ∷ (q55 , c55) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ([]) ∷ [])

capturesq50-correct : ∀ b p → capturesq50 b p ≡ Fast.allCaptures6 (state b p) q50
capturesq50-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q50

capturesq51 : Board six → Player → List (Coord six)
capturesq51 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q41 , c41) ∷ (q31 , c31) ∷ (q21 , c21) ∷ (q11 , c11) ∷ (q01 , c01) ∷ []) ∷ ((q42 , c42) ∷ (q33 , c33) ∷ (q24 , c24) ∷ (q15 , c15) ∷ []) ∷ ((q52 , c52) ∷ (q53 , c53) ∷ (q54 , c54) ∷ (q55 , c55) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q50 , c50) ∷ []) ∷ ((q40 , c40) ∷ []) ∷ [])

capturesq51-correct : ∀ b p → capturesq51 b p ≡ Fast.allCaptures6 (state b p) q51
capturesq51-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q51

capturesq52 : Board six → Player → List (Coord six)
capturesq52 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q42 , c42) ∷ (q32 , c32) ∷ (q22 , c22) ∷ (q12 , c12) ∷ (q02 , c02) ∷ []) ∷ ((q43 , c43) ∷ (q34 , c34) ∷ (q25 , c25) ∷ []) ∷ ((q53 , c53) ∷ (q54 , c54) ∷ (q55 , c55) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q51 , c51) ∷ (q50 , c50) ∷ []) ∷ ((q41 , c41) ∷ (q30 , c30) ∷ []) ∷ [])

capturesq52-correct : ∀ b p → capturesq52 b p ≡ Fast.allCaptures6 (state b p) q52
capturesq52-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q52

capturesq53 : Board six → Player → List (Coord six)
capturesq53 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q43 , c43) ∷ (q33 , c33) ∷ (q23 , c23) ∷ (q13 , c13) ∷ (q03 , c03) ∷ []) ∷ ((q44 , c44) ∷ (q35 , c35) ∷ []) ∷ ((q54 , c54) ∷ (q55 , c55) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q52 , c52) ∷ (q51 , c51) ∷ (q50 , c50) ∷ []) ∷ ((q42 , c42) ∷ (q31 , c31) ∷ (q20 , c20) ∷ []) ∷ [])

capturesq53-correct : ∀ b p → capturesq53 b p ≡ Fast.allCaptures6 (state b p) q53
capturesq53-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q53

capturesq54 : Board six → Player → List (Coord six)
capturesq54 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q44 , c44) ∷ (q34 , c34) ∷ (q24 , c24) ∷ (q14 , c14) ∷ (q04 , c04) ∷ []) ∷ ((q45 , c45) ∷ []) ∷ ((q55 , c55) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q53 , c53) ∷ (q52 , c52) ∷ (q51 , c51) ∷ (q50 , c50) ∷ []) ∷ ((q43 , c43) ∷ (q32 , c32) ∷ (q21 , c21) ∷ (q10 , c10) ∷ []) ∷ [])

capturesq54-correct : ∀ b p → capturesq54 b p ≡ Fast.allCaptures6 (state b p) q54
capturesq54-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q54

capturesq55 : Board six → Player → List (Coord six)
capturesq55 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays p
  (((q45 , c45) ∷ (q35 , c35) ∷ (q25 , c25) ∷ (q15 , c15) ∷ (q05 , c05) ∷ []) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ([]) ∷ ((q54 , c54) ∷ (q53 , c53) ∷ (q52 , c52) ∷ (q51 , c51) ∷ (q50 , c50) ∷ []) ∷ ((q44 , c44) ∷ (q33 , c33) ∷ (q22 , c22) ∷ (q11 , c11) ∷ (q00 , c00) ∷ []) ∷ [])

capturesq55-correct : ∀ b p → capturesq55 b p ≡ Fast.allCaptures6 (state b p) q55
capturesq55-correct b@((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p = Rays.capturesRays-correct (state b p) q55

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
