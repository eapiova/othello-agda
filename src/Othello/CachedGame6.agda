{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Ordered game refinement with certified empty-coordinate caches.
module Othello.CachedGame6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (coords; passState; nonempty)
open import Game.Core using (Game; lookup)
open import Game.Symmetry using (CertificateTransport; act)
import Game.MappedTransfer as T
import Game.DirectedIndexed as D
import Othello.EmptyCache6 as S
import Othello.Finite as F
import Othello.LengthRays6 as Lines
import Othello.LengthRules6 as Old
import Othello.LengthMoves6 as Moves
import Othello.Incremental6 as Inc
import Othello.Fast6 as Fast
import Othello.AgreedIndexed6 as A
open Old using (q00; q01; q02; q03; q04; q05; q10; q11; q12; q13; q14; q15; q20; q21; q22; q23; q24; q25; q30; q31; q32; q33; q34; q35; q40; q41; q42; q43; q44; q45; q50; q51; q52; q53; q54; q55)

rays : State six → Coord six → List (Coord six)
rays (state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) = λ
  { (F.zero , F.zero) → (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count5 p c01 c02 c03 c04 c05) (q01 ∷ q02 ∷ q03 ∷ q04 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count5 p c11 c22 c33 c44 c55) (q11 ∷ q22 ∷ q33 ∷ q44 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count5 p c10 c20 c30 c40 c50) (q10 ∷ q20 ∷ q30 ∷ q40 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; (F.zero , (F.suc F.zero)) → (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count4 p c02 c03 c04 c05) (q02 ∷ q03 ∷ q04 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count4 p c12 c23 c34 c45) (q12 ∷ q23 ∷ q34 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count5 p c11 c21 c31 c41 c51) (q11 ∷ q21 ∷ q31 ∷ q41 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c10) (q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c00) (q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; (F.zero , (F.suc (F.suc F.zero))) → (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count3 p c03 c04 c05) (q03 ∷ q04 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count3 p c13 c24 c35) (q13 ∷ q24 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count5 p c12 c22 c32 c42 c52) (q12 ∷ q22 ∷ q32 ∷ q42 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c11 c20) (q11 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c01 c00) (q01 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; (F.zero , (F.suc (F.suc (F.suc F.zero)))) → (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count2 p c04 c05) (q04 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count2 p c14 c25) (q14 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count5 p c13 c23 c33 c43 c53) (q13 ∷ q23 ∷ q33 ∷ q43 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count3 p c12 c21 c30) (q12 ∷ q21 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count3 p c02 c01 c00) (q02 ∷ q01 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; (F.zero , (F.suc (F.suc (F.suc (F.suc F.zero))))) → (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count1 p c05) (q05 ∷ [])) ++ (Lines.prefix (Lines.count1 p c15) (q15 ∷ [])) ++ (Lines.prefix (Lines.count5 p c14 c24 c34 c44 c54) (q14 ∷ q24 ∷ q34 ∷ q44 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count4 p c13 c22 c31 c40) (q13 ∷ q22 ∷ q31 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count4 p c03 c02 c01 c00) (q03 ∷ q02 ∷ q01 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; (F.zero , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) → (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count5 p c15 c25 c35 c45 c55) (q15 ∷ q25 ∷ q35 ∷ q45 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count5 p c14 c23 c32 c41 c50) (q14 ∷ q23 ∷ q32 ∷ q41 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count5 p c04 c03 c02 c01 c00) (q04 ∷ q03 ∷ q02 ∷ q01 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; ((F.suc F.zero) , F.zero) → (Lines.prefix (Lines.count1 p c00) (q00 ∷ [])) ++ (Lines.prefix (Lines.count1 p c01) (q01 ∷ [])) ++ (Lines.prefix (Lines.count5 p c11 c12 c13 c14 c15) (q11 ∷ q12 ∷ q13 ∷ q14 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count4 p c21 c32 c43 c54) (q21 ∷ q32 ∷ q43 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count4 p c20 c30 c40 c50) (q20 ∷ q30 ∷ q40 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; ((F.suc F.zero) , (F.suc F.zero)) → (Lines.prefix (Lines.count1 p c01) (q01 ∷ [])) ++ (Lines.prefix (Lines.count1 p c02) (q02 ∷ [])) ++ (Lines.prefix (Lines.count4 p c12 c13 c14 c15) (q12 ∷ q13 ∷ q14 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count4 p c22 c33 c44 c55) (q22 ∷ q33 ∷ q44 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count4 p c21 c31 c41 c51) (q21 ∷ q31 ∷ q41 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c20) (q20 ∷ [])) ++ (Lines.prefix (Lines.count1 p c10) (q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c00) (q00 ∷ [])) ++ []
  ; ((F.suc F.zero) , (F.suc (F.suc F.zero))) → (Lines.prefix (Lines.count1 p c02) (q02 ∷ [])) ++ (Lines.prefix (Lines.count1 p c03) (q03 ∷ [])) ++ (Lines.prefix (Lines.count3 p c13 c14 c15) (q13 ∷ q14 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count3 p c23 c34 c45) (q23 ∷ q34 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count4 p c22 c32 c42 c52) (q22 ∷ q32 ∷ q42 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c21 c30) (q21 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count2 p c11 c10) (q11 ∷ q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c01) (q01 ∷ [])) ++ []
  ; ((F.suc F.zero) , (F.suc (F.suc (F.suc F.zero)))) → (Lines.prefix (Lines.count1 p c03) (q03 ∷ [])) ++ (Lines.prefix (Lines.count1 p c04) (q04 ∷ [])) ++ (Lines.prefix (Lines.count2 p c14 c15) (q14 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count2 p c24 c35) (q24 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count4 p c23 c33 c43 c53) (q23 ∷ q33 ∷ q43 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count3 p c22 c31 c40) (q22 ∷ q31 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count3 p c12 c11 c10) (q12 ∷ q11 ∷ q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c02) (q02 ∷ [])) ++ []
  ; ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc F.zero))))) → (Lines.prefix (Lines.count1 p c04) (q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c05) (q05 ∷ [])) ++ (Lines.prefix (Lines.count1 p c15) (q15 ∷ [])) ++ (Lines.prefix (Lines.count1 p c25) (q25 ∷ [])) ++ (Lines.prefix (Lines.count4 p c24 c34 c44 c54) (q24 ∷ q34 ∷ q44 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count4 p c23 c32 c41 c50) (q23 ∷ q32 ∷ q41 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count4 p c13 c12 c11 c10) (q13 ∷ q12 ∷ q11 ∷ q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c03) (q03 ∷ [])) ++ []
  ; ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) → (Lines.prefix (Lines.count1 p c05) (q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count4 p c25 c35 c45 c55) (q25 ∷ q35 ∷ q45 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count4 p c24 c33 c42 c51) (q24 ∷ q33 ∷ q42 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count5 p c14 c13 c12 c11 c10) (q14 ∷ q13 ∷ q12 ∷ q11 ∷ q10 ∷ [])) ++ (Lines.prefix (Lines.count1 p c04) (q04 ∷ [])) ++ []
  ; ((F.suc (F.suc F.zero)) , F.zero) → (Lines.prefix (Lines.count2 p c10 c00) (q10 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count2 p c11 c02) (q11 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count5 p c21 c22 c23 c24 c25) (q21 ∷ q22 ∷ q23 ∷ q24 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count3 p c31 c42 c53) (q31 ∷ q42 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count3 p c30 c40 c50) (q30 ∷ q40 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; ((F.suc (F.suc F.zero)) , (F.suc F.zero)) → (Lines.prefix (Lines.count2 p c11 c01) (q11 ∷ q01 ∷ [])) ++ (Lines.prefix (Lines.count2 p c12 c03) (q12 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count4 p c22 c23 c24 c25) (q22 ∷ q23 ∷ q24 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c43 c54) (q32 ∷ q43 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count3 p c31 c41 c51) (q31 ∷ q41 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c30) (q30 ∷ [])) ++ (Lines.prefix (Lines.count1 p c20) (q20 ∷ [])) ++ (Lines.prefix (Lines.count1 p c10) (q10 ∷ [])) ++ []
  ; ((F.suc (F.suc F.zero)) , (F.suc (F.suc F.zero))) → (Lines.prefix (Lines.count2 p c12 c02) (q12 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count2 p c13 c04) (q13 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count3 p c23 c24 c25) (q23 ∷ q24 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c44 c55) (q33 ∷ q44 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c42 c52) (q32 ∷ q42 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c31 c40) (q31 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count2 p c21 c20) (q21 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c11 c00) (q11 ∷ q00 ∷ [])) ++ []
  ; ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc F.zero)))) → (Lines.prefix (Lines.count2 p c13 c03) (q13 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count2 p c14 c05) (q14 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count2 p c24 c25) (q24 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count2 p c34 c45) (q34 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c43 c53) (q33 ∷ q43 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c41 c50) (q32 ∷ q41 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count3 p c22 c21 c20) (q22 ∷ q21 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c12 c01) (q12 ∷ q01 ∷ [])) ++ []
  ; ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc F.zero))))) → (Lines.prefix (Lines.count2 p c14 c04) (q14 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c15) (q15 ∷ [])) ++ (Lines.prefix (Lines.count1 p c25) (q25 ∷ [])) ++ (Lines.prefix (Lines.count1 p c35) (q35 ∷ [])) ++ (Lines.prefix (Lines.count3 p c34 c44 c54) (q34 ∷ q44 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c42 c51) (q33 ∷ q42 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count4 p c23 c22 c21 c20) (q23 ∷ q22 ∷ q21 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c13 c02) (q13 ∷ q02 ∷ [])) ++ []
  ; ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) → (Lines.prefix (Lines.count2 p c15 c05) (q15 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count3 p c35 c45 c55) (q35 ∷ q45 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count3 p c34 c43 c52) (q34 ∷ q43 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count5 p c24 c23 c22 c21 c20) (q24 ∷ q23 ∷ q22 ∷ q21 ∷ q20 ∷ [])) ++ (Lines.prefix (Lines.count2 p c14 c03) (q14 ∷ q03 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc F.zero))) , F.zero) → (Lines.prefix (Lines.count3 p c20 c10 c00) (q20 ∷ q10 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count3 p c21 c12 c03) (q21 ∷ q12 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count5 p c31 c32 c33 c34 c35) (q31 ∷ q32 ∷ q33 ∷ q34 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c52) (q41 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c40 c50) (q40 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; ((F.suc (F.suc (F.suc F.zero))) , (F.suc F.zero)) → (Lines.prefix (Lines.count3 p c21 c11 c01) (q21 ∷ q11 ∷ q01 ∷ [])) ++ (Lines.prefix (Lines.count3 p c22 c13 c04) (q22 ∷ q13 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count4 p c32 c33 c34 c35) (q32 ∷ q33 ∷ q34 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c42 c53) (q42 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c51) (q41 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c40) (q40 ∷ [])) ++ (Lines.prefix (Lines.count1 p c30) (q30 ∷ [])) ++ (Lines.prefix (Lines.count1 p c20) (q20 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc F.zero))) → (Lines.prefix (Lines.count3 p c22 c12 c02) (q22 ∷ q12 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count3 p c23 c14 c05) (q23 ∷ q14 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c34 c35) (q33 ∷ q34 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c43 c54) (q43 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count2 p c42 c52) (q42 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c50) (q41 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count2 p c31 c30) (q31 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count2 p c21 c10) (q21 ∷ q10 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc F.zero)))) → (Lines.prefix (Lines.count3 p c23 c13 c03) (q23 ∷ q13 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count2 p c24 c15) (q24 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count2 p c34 c35) (q34 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c55) (q44 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count2 p c43 c53) (q43 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count2 p c42 c51) (q42 ∷ q51 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c31 c30) (q32 ∷ q31 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count3 p c22 c11 c00) (q22 ∷ q11 ∷ q00 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) → (Lines.prefix (Lines.count3 p c24 c14 c04) (q24 ∷ q14 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c25) (q25 ∷ [])) ++ (Lines.prefix (Lines.count1 p c35) (q35 ∷ [])) ++ (Lines.prefix (Lines.count1 p c45) (q45 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c54) (q44 ∷ q54 ∷ [])) ++ (Lines.prefix (Lines.count2 p c43 c52) (q43 ∷ q52 ∷ [])) ++ (Lines.prefix (Lines.count4 p c33 c32 c31 c30) (q33 ∷ q32 ∷ q31 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count3 p c23 c12 c01) (q23 ∷ q12 ∷ q01 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) → (Lines.prefix (Lines.count3 p c25 c15 c05) (q25 ∷ q15 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count2 p c45 c55) (q45 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c53) (q44 ∷ q53 ∷ [])) ++ (Lines.prefix (Lines.count5 p c34 c33 c32 c31 c30) (q34 ∷ q33 ∷ q32 ∷ q31 ∷ q30 ∷ [])) ++ (Lines.prefix (Lines.count3 p c24 c13 c02) (q24 ∷ q13 ∷ q02 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc F.zero)))) , F.zero) → (Lines.prefix (Lines.count4 p c30 c20 c10 c00) (q30 ∷ q20 ∷ q10 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count4 p c31 c22 c13 c04) (q31 ∷ q22 ∷ q13 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count5 p c41 c42 c43 c44 c45) (q41 ∷ q42 ∷ q43 ∷ q44 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c51) (q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c50) (q50 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc F.zero)) → (Lines.prefix (Lines.count4 p c31 c21 c11 c01) (q31 ∷ q21 ∷ q11 ∷ q01 ∷ [])) ++ (Lines.prefix (Lines.count4 p c32 c23 c14 c05) (q32 ∷ q23 ∷ q14 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count4 p c42 c43 c44 c45) (q42 ∷ q43 ∷ q44 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c52) (q52 ∷ [])) ++ (Lines.prefix (Lines.count1 p c51) (q51 ∷ [])) ++ (Lines.prefix (Lines.count1 p c50) (q50 ∷ [])) ++ (Lines.prefix (Lines.count1 p c40) (q40 ∷ [])) ++ (Lines.prefix (Lines.count1 p c30) (q30 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc F.zero))) → (Lines.prefix (Lines.count4 p c32 c22 c12 c02) (q32 ∷ q22 ∷ q12 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count3 p c33 c24 c15) (q33 ∷ q24 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count3 p c43 c44 c45) (q43 ∷ q44 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c53) (q53 ∷ [])) ++ (Lines.prefix (Lines.count1 p c52) (q52 ∷ [])) ++ (Lines.prefix (Lines.count1 p c51) (q51 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c40) (q41 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count2 p c31 c20) (q31 ∷ q20 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc F.zero)))) → (Lines.prefix (Lines.count4 p c33 c23 c13 c03) (q33 ∷ q23 ∷ q13 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count2 p c34 c25) (q34 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c45) (q44 ∷ q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c54) (q54 ∷ [])) ++ (Lines.prefix (Lines.count1 p c53) (q53 ∷ [])) ++ (Lines.prefix (Lines.count1 p c52) (q52 ∷ [])) ++ (Lines.prefix (Lines.count3 p c42 c41 c40) (q42 ∷ q41 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count3 p c32 c21 c10) (q32 ∷ q21 ∷ q10 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) → (Lines.prefix (Lines.count4 p c34 c24 c14 c04) (q34 ∷ q24 ∷ q14 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c35) (q35 ∷ [])) ++ (Lines.prefix (Lines.count1 p c45) (q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c55) (q55 ∷ [])) ++ (Lines.prefix (Lines.count1 p c54) (q54 ∷ [])) ++ (Lines.prefix (Lines.count1 p c53) (q53 ∷ [])) ++ (Lines.prefix (Lines.count4 p c43 c42 c41 c40) (q43 ∷ q42 ∷ q41 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count4 p c33 c22 c11 c00) (q33 ∷ q22 ∷ q11 ∷ q00 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) → (Lines.prefix (Lines.count4 p c35 c25 c15 c05) (q35 ∷ q25 ∷ q15 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count1 p c55) (q55 ∷ [])) ++ (Lines.prefix (Lines.count1 p c54) (q54 ∷ [])) ++ (Lines.prefix (Lines.count5 p c44 c43 c42 c41 c40) (q44 ∷ q43 ∷ q42 ∷ q41 ∷ q40 ∷ [])) ++ (Lines.prefix (Lines.count4 p c34 c23 c12 c01) (q34 ∷ q23 ∷ q12 ∷ q01 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , F.zero) → (Lines.prefix (Lines.count5 p c40 c30 c20 c10 c00) (q40 ∷ q30 ∷ q20 ∷ q10 ∷ q00 ∷ [])) ++ (Lines.prefix (Lines.count5 p c41 c32 c23 c14 c05) (q41 ∷ q32 ∷ q23 ∷ q14 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count5 p c51 c52 c53 c54 c55) (q51 ∷ q52 ∷ q53 ∷ q54 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc F.zero)) → (Lines.prefix (Lines.count5 p c41 c31 c21 c11 c01) (q41 ∷ q31 ∷ q21 ∷ q11 ∷ q01 ∷ [])) ++ (Lines.prefix (Lines.count4 p c42 c33 c24 c15) (q42 ∷ q33 ∷ q24 ∷ q15 ∷ [])) ++ (Lines.prefix (Lines.count4 p c52 c53 c54 c55) (q52 ∷ q53 ∷ q54 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count1 p c50) (q50 ∷ [])) ++ (Lines.prefix (Lines.count1 p c40) (q40 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc F.zero))) → (Lines.prefix (Lines.count5 p c42 c32 c22 c12 c02) (q42 ∷ q32 ∷ q22 ∷ q12 ∷ q02 ∷ [])) ++ (Lines.prefix (Lines.count3 p c43 c34 c25) (q43 ∷ q34 ∷ q25 ∷ [])) ++ (Lines.prefix (Lines.count3 p c53 c54 c55) (q53 ∷ q54 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count2 p c51 c50) (q51 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count2 p c41 c30) (q41 ∷ q30 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc F.zero)))) → (Lines.prefix (Lines.count5 p c43 c33 c23 c13 c03) (q43 ∷ q33 ∷ q23 ∷ q13 ∷ q03 ∷ [])) ++ (Lines.prefix (Lines.count2 p c44 c35) (q44 ∷ q35 ∷ [])) ++ (Lines.prefix (Lines.count2 p c54 c55) (q54 ∷ q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count3 p c52 c51 c50) (q52 ∷ q51 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count3 p c42 c31 c20) (q42 ∷ q31 ∷ q20 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) → (Lines.prefix (Lines.count5 p c44 c34 c24 c14 c04) (q44 ∷ q34 ∷ q24 ∷ q14 ∷ q04 ∷ [])) ++ (Lines.prefix (Lines.count1 p c45) (q45 ∷ [])) ++ (Lines.prefix (Lines.count1 p c55) (q55 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count4 p c53 c52 c51 c50) (q53 ∷ q52 ∷ q51 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count4 p c43 c32 c21 c10) (q43 ∷ q32 ∷ q21 ∷ q10 ∷ [])) ++ []
  ; ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) → (Lines.prefix (Lines.count5 p c45 c35 c25 c15 c05) (q45 ∷ q35 ∷ q25 ∷ q15 ∷ q05 ∷ [])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count0 p) ([])) ++ (Lines.prefix (Lines.count5 p c54 c53 c52 c51 c50) (q54 ∷ q53 ∷ q52 ∷ q51 ∷ q50 ∷ [])) ++ (Lines.prefix (Lines.count5 p c44 c33 c22 c11 c00) (q44 ∷ q33 ∷ q22 ∷ q11 ∷ q00 ∷ [])) ++ []
  }

abstract
  rays-agree : ∀ s q → rays s q ≡ Fast.allCaptures6 s q
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) (F.zero , F.zero) = Old.capturesq00-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) (F.zero , (F.suc F.zero)) = Old.capturesq01-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) (F.zero , (F.suc (F.suc F.zero))) = Old.capturesq02-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) (F.zero , (F.suc (F.suc (F.suc F.zero)))) = Old.capturesq03-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) (F.zero , (F.suc (F.suc (F.suc (F.suc F.zero))))) = Old.capturesq04-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) (F.zero , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = Old.capturesq05-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc F.zero) , F.zero) = Old.capturesq10-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc F.zero) , (F.suc F.zero)) = Old.capturesq11-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc F.zero) , (F.suc (F.suc F.zero))) = Old.capturesq12-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc F.zero) , (F.suc (F.suc (F.suc F.zero)))) = Old.capturesq13-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = Old.capturesq14-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc F.zero) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = Old.capturesq15-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc F.zero)) , F.zero) = Old.capturesq20-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc F.zero)) , (F.suc F.zero)) = Old.capturesq21-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc F.zero))) = Old.capturesq22-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc F.zero)))) = Old.capturesq23-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = Old.capturesq24-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc F.zero)) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = Old.capturesq25-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc F.zero))) , F.zero) = Old.capturesq30-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc F.zero)) = Old.capturesq31-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc F.zero))) = Old.capturesq32-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc F.zero)))) = Old.capturesq33-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = Old.capturesq34-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc F.zero))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = Old.capturesq35-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , F.zero) = Old.capturesq40-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc F.zero)) = Old.capturesq41-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc F.zero))) = Old.capturesq42-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc F.zero)))) = Old.capturesq43-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = Old.capturesq44-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc F.zero)))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = Old.capturesq45-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , F.zero) = Old.capturesq50-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc F.zero)) = Old.capturesq51-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc F.zero))) = Old.capturesq52-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc F.zero)))) = Old.capturesq53-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc F.zero))))) = Old.capturesq54-correct (board s) p
  rays-agree s@(state ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) p) ((F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) , (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))))) = Old.capturesq55-correct (board s) p

plain : State six → List (Coord six) → (Coord six → List (Coord six)) → List (State six)
plain s [] cap = []
plain s (q ∷ qs) cap = Inc.candidate s q (cap q) (plain s qs cap)

loop : S.Cached → List (Coord six) → (Coord six → List (Coord six)) → List S.Cached
loop s [] cap = []
loop s (q ∷ qs) cap with sameCell (at {six} (board (S.raw s)) q) empty ∧ nonempty (cap q)
... | false = loop s qs cap
... | true = S.play s q (cap q) ∷ loop s qs cap

moves : S.Cached → List S.Cached
moves s = loop s (S.vacancies s) (rays (S.raw s))

private
  cong₂ : ∀ {X Y Z : Set} (f : X → Y → Z) {x x′ y y′} →
    x ≡ x′ → y ≡ y′ → f x y ≡ f x′ y′
  cong₂ f refl refl = refl

  loop-maps : ∀ s qs cap → map S.raw (loop s qs cap) ≡ plain (S.raw s) qs cap
  loop-maps s [] cap = refl
  loop-maps s (q ∷ qs) cap
    with sameCell (at {six} (board (S.raw s)) q) empty ∧ nonempty (cap q)
  ... | false = loop-maps s qs cap
  ... | true = cong₂ _∷_ (S.play-decodes s q (cap q)) (loop-maps s qs cap)

  plain-filter : ∀ s qs cap →
    plain s (S.select (λ q → sameCell (at {six} (board s) q) empty) qs) cap ≡ plain s qs cap
  plain-filter s [] cap = refl
  plain-filter s (q ∷ qs) cap with sameCell (at {six} (board s) q) empty in emptyChecked
  ... | false = plain-filter s qs cap
  ... | true with nonempty (cap q) in nonemptyChecked
  ...   | false rewrite emptyChecked | nonemptyChecked = plain-filter s qs cap
  ...   | true rewrite emptyChecked | nonemptyChecked = cong (λ tail → state
    (put {six} (Inc.flipMany (board s) (toMove s) (cap q)) q (playerCell (toMove s)))
    (other (toMove s)) ∷ tail) (plain-filter s qs cap)

  plain-rays : ∀ s qs → plain s qs (rays s) ≡ Inc.moves s qs
  plain-rays s [] = refl
  plain-rays s (q ∷ qs) rewrite rays-agree s q | plain-rays s qs = refl

abstract
  moves-maps : ∀ s → map S.raw (moves s) ≡ Old.moves (S.raw s)
  moves-maps s = trans (loop-maps s (S.vacancies s) (rays (S.raw s)))
    (trans (cong (λ qs → plain (S.raw s) qs (rays (S.raw s))) (sym (S.cache-correct s)))
      (trans (plain-filter (S.raw s) (coords six) (rays (S.raw s)))
        (trans (plain-rays (S.raw s) (coords six))
          (trans (Inc.moves-agree (S.raw s) (coords six)) (sym (Old.moves-agree (S.raw s)))))))

finish : S.Cached → List S.Cached → List S.Cached → List S.Cached
finish s [] [] = []
finish s [] (_ ∷ _) = S.pass s ∷ []
finish s (t ∷ ts) opposing = t ∷ ts

passShape : List S.Cached → List S.Cached → Bool
passShape [] [] = false
passShape [] (_ ∷ _) = true
passShape (_ ∷ _) opposing = false

successors : S.Cached → List S.Cached
successors s = finish s (moves s) (moves (S.pass s))

forcedPass : S.Cached → Bool
forcedPass s = passShape (moves s) (moves (S.pass s))

private
  finish-maps : ∀ s ss opposing → map S.raw (finish s ss opposing) ≡
    Fast.finish6 (S.raw s) (map S.raw ss) (map S.raw opposing)
  finish-maps s [] [] = refl
  finish-maps s [] (_ ∷ _) = cong (λ t → t ∷ []) (S.pass-decodes s)
  finish-maps s (_ ∷ _) opposing = refl

  passShape-maps : ∀ ss opposing → passShape ss opposing ≡
    Old.passShape (map S.raw ss) (map S.raw opposing)
  passShape-maps [] [] = refl
  passShape-maps [] (_ ∷ _) = refl
  passShape-maps (_ ∷ _) opposing = refl

abstract
  successors-maps : ∀ s → map S.raw (successors s) ≡ Old.successors (S.raw s)
  successors-maps s = trans (finish-maps s (moves s) (moves (S.pass s)))
    (cong₂ (Fast.finish6 (S.raw s)) (moves-maps s)
      (trans (moves-maps (S.pass s)) (cong Old.moves (S.pass-decodes s))))

  pass-maps : ∀ s → forcedPass s ≡ Old.forcedPass (S.raw s)
  pass-maps s = trans (passShape-maps (moves s) (moves (S.pass s)))
    (cong₂ Old.passShape (moves-maps s)
      (trans (moves-maps (S.pass s)) (cong Old.moves (S.pass-decodes s))))

game : Game S.Cached
game = record { turn = λ s → toMove (S.raw s) ; next = successors ; forcedPass = forcedPass }

refinement : T.Refinement game Old.specializedGame6 S.raw
refinement = T.refinement successors-maps (λ s → refl) pass-maps

pick : S.Cached → Coord six → Maybe S.Cached
pick s q with sameCell (at {six} (board (S.raw s)) q) empty ∧ nonempty (Moves.capturesAt (S.raw s) q)
... | false = nothing
... | true = just (S.play s q (Moves.capturesAt (S.raw s) q))

private
  pick-maps : ∀ s q → T.mapMaybe S.raw (pick s q) ≡ Moves.pick (S.raw s) q
  pick-maps s q with sameCell (at {six} (board (S.raw s)) q) empty ∧ nonempty (Moves.capturesAt (S.raw s) q)
  ... | false = refl
  ... | true = cong just (S.play-decodes s q (Moves.capturesAt (S.raw s) q))

  just-injective : ∀ {X : Set} {x y : X} → just x ≡ just y → x ≡ y
  just-injective refl = refl

  lookup-injective : ∀ xs i t → lookup (map S.raw xs) i ≡ just (S.raw t) → lookup xs i ≡ just t
  lookup-injective [] i t ()
  lookup-injective (x ∷ xs) zero t checked = cong just (S.injective x t (just-injective checked))
  lookup-injective (x ∷ xs) (suc i) t checked = lookup-injective xs i t checked

  pick-sound : ∀ s q t → pick s q ≡ just t → Σ ℕ (λ i → lookup (successors s) i ≡ just t)
  pick-sound s q t checked with Moves.pick-sound (S.raw s) q (S.raw t)
    (trans (sym (pick-maps s q)) (cong (T.mapMaybe S.raw) checked))
  ... | i , hit = i , lookup-injective (successors s) i t
    (trans (cong (λ xs → lookup xs i) (successors-maps s)) hit)

picker : D.MovePicker game (Coord six)
picker = D.movePicker pick pick-sound

module Transport (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Agreed = A.With Old.specializedGame6 Old.agreement
  oldLaws : CertificateTransport Old.specializedGame6 p goal
  oldLaws = Agreed.adapt p goal laws

  action : ℕ → S.Cached → S.Cached
  action tag s = S.pack (act oldLaws tag (S.raw s))

  module Adapt = T.Adapting game Old.specializedGame6 S.raw refinement
    p goal oldLaws action (λ tag s → refl)

  cachedLaws : CertificateTransport game p (λ s → goal (S.raw s))
  cachedLaws = Adapt.laws
