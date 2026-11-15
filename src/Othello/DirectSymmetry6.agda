{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted generated permutations; each equality checks the old D4 action.
module Othello.DirectSymmetry6 where

open import Prelude
open import Othello.Board
open import Game.Symmetry using (CertificateTransport; Proven)
open import Othello.Statements using (lowerGoal; upperGoal)
import Othello.Finite as F
import Othello.Symmetry6 as S
import Othello.SharedSymmetry6 as Old
import Othello.Fast6 as Fast

transformBoard : S.D4 → Board six → Board six
transformBoard S.identity ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) =
  ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[])
transformBoard S.rotate90 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) =
  ((c50 F.∷ c40 F.∷ c30 F.∷ c20 F.∷ c10 F.∷ c00 F.∷ F.[]) F.∷ (c51 F.∷ c41 F.∷ c31 F.∷ c21 F.∷ c11 F.∷ c01 F.∷ F.[]) F.∷ (c52 F.∷ c42 F.∷ c32 F.∷ c22 F.∷ c12 F.∷ c02 F.∷ F.[]) F.∷ (c53 F.∷ c43 F.∷ c33 F.∷ c23 F.∷ c13 F.∷ c03 F.∷ F.[]) F.∷ (c54 F.∷ c44 F.∷ c34 F.∷ c24 F.∷ c14 F.∷ c04 F.∷ F.[]) F.∷ (c55 F.∷ c45 F.∷ c35 F.∷ c25 F.∷ c15 F.∷ c05 F.∷ F.[]) F.∷ F.[])
transformBoard S.rotate180 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) =
  ((c55 F.∷ c54 F.∷ c53 F.∷ c52 F.∷ c51 F.∷ c50 F.∷ F.[]) F.∷ (c45 F.∷ c44 F.∷ c43 F.∷ c42 F.∷ c41 F.∷ c40 F.∷ F.[]) F.∷ (c35 F.∷ c34 F.∷ c33 F.∷ c32 F.∷ c31 F.∷ c30 F.∷ F.[]) F.∷ (c25 F.∷ c24 F.∷ c23 F.∷ c22 F.∷ c21 F.∷ c20 F.∷ F.[]) F.∷ (c15 F.∷ c14 F.∷ c13 F.∷ c12 F.∷ c11 F.∷ c10 F.∷ F.[]) F.∷ (c05 F.∷ c04 F.∷ c03 F.∷ c02 F.∷ c01 F.∷ c00 F.∷ F.[]) F.∷ F.[])
transformBoard S.rotate270 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) =
  ((c05 F.∷ c15 F.∷ c25 F.∷ c35 F.∷ c45 F.∷ c55 F.∷ F.[]) F.∷ (c04 F.∷ c14 F.∷ c24 F.∷ c34 F.∷ c44 F.∷ c54 F.∷ F.[]) F.∷ (c03 F.∷ c13 F.∷ c23 F.∷ c33 F.∷ c43 F.∷ c53 F.∷ F.[]) F.∷ (c02 F.∷ c12 F.∷ c22 F.∷ c32 F.∷ c42 F.∷ c52 F.∷ F.[]) F.∷ (c01 F.∷ c11 F.∷ c21 F.∷ c31 F.∷ c41 F.∷ c51 F.∷ F.[]) F.∷ (c00 F.∷ c10 F.∷ c20 F.∷ c30 F.∷ c40 F.∷ c50 F.∷ F.[]) F.∷ F.[])
transformBoard S.reflectVertical ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) =
  ((c05 F.∷ c04 F.∷ c03 F.∷ c02 F.∷ c01 F.∷ c00 F.∷ F.[]) F.∷ (c15 F.∷ c14 F.∷ c13 F.∷ c12 F.∷ c11 F.∷ c10 F.∷ F.[]) F.∷ (c25 F.∷ c24 F.∷ c23 F.∷ c22 F.∷ c21 F.∷ c20 F.∷ F.[]) F.∷ (c35 F.∷ c34 F.∷ c33 F.∷ c32 F.∷ c31 F.∷ c30 F.∷ F.[]) F.∷ (c45 F.∷ c44 F.∷ c43 F.∷ c42 F.∷ c41 F.∷ c40 F.∷ F.[]) F.∷ (c55 F.∷ c54 F.∷ c53 F.∷ c52 F.∷ c51 F.∷ c50 F.∷ F.[]) F.∷ F.[])
transformBoard S.reflectDiagonal ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) =
  ((c00 F.∷ c10 F.∷ c20 F.∷ c30 F.∷ c40 F.∷ c50 F.∷ F.[]) F.∷ (c01 F.∷ c11 F.∷ c21 F.∷ c31 F.∷ c41 F.∷ c51 F.∷ F.[]) F.∷ (c02 F.∷ c12 F.∷ c22 F.∷ c32 F.∷ c42 F.∷ c52 F.∷ F.[]) F.∷ (c03 F.∷ c13 F.∷ c23 F.∷ c33 F.∷ c43 F.∷ c53 F.∷ F.[]) F.∷ (c04 F.∷ c14 F.∷ c24 F.∷ c34 F.∷ c44 F.∷ c54 F.∷ F.[]) F.∷ (c05 F.∷ c15 F.∷ c25 F.∷ c35 F.∷ c45 F.∷ c55 F.∷ F.[]) F.∷ F.[])
transformBoard S.reflectHorizontal ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) =
  ((c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ F.[])
transformBoard S.reflectAntiDiagonal ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) =
  ((c55 F.∷ c45 F.∷ c35 F.∷ c25 F.∷ c15 F.∷ c05 F.∷ F.[]) F.∷ (c54 F.∷ c44 F.∷ c34 F.∷ c24 F.∷ c14 F.∷ c04 F.∷ F.[]) F.∷ (c53 F.∷ c43 F.∷ c33 F.∷ c23 F.∷ c13 F.∷ c03 F.∷ F.[]) F.∷ (c52 F.∷ c42 F.∷ c32 F.∷ c22 F.∷ c12 F.∷ c02 F.∷ F.[]) F.∷ (c51 F.∷ c41 F.∷ c31 F.∷ c21 F.∷ c11 F.∷ c01 F.∷ F.[]) F.∷ (c50 F.∷ c40 F.∷ c30 F.∷ c20 F.∷ c10 F.∷ c00 F.∷ F.[]) F.∷ F.[])

transformBoard-correct : ∀ sigma b → transformBoard sigma b ≡ S.transformBoard sigma b
transformBoard-correct S.identity ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) = refl
transformBoard-correct S.rotate90 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) = refl
transformBoard-correct S.rotate180 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) = refl
transformBoard-correct S.rotate270 ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) = refl
transformBoard-correct S.reflectVertical ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) = refl
transformBoard-correct S.reflectDiagonal ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) = refl
transformBoard-correct S.reflectHorizontal ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) = refl
transformBoard-correct S.reflectAntiDiagonal ((c00 F.∷ c01 F.∷ c02 F.∷ c03 F.∷ c04 F.∷ c05 F.∷ F.[]) F.∷ (c10 F.∷ c11 F.∷ c12 F.∷ c13 F.∷ c14 F.∷ c15 F.∷ F.[]) F.∷ (c20 F.∷ c21 F.∷ c22 F.∷ c23 F.∷ c24 F.∷ c25 F.∷ F.[]) F.∷ (c30 F.∷ c31 F.∷ c32 F.∷ c33 F.∷ c34 F.∷ c35 F.∷ F.[]) F.∷ (c40 F.∷ c41 F.∷ c42 F.∷ c43 F.∷ c44 F.∷ c45 F.∷ F.[]) F.∷ (c50 F.∷ c51 F.∷ c52 F.∷ c53 F.∷ c54 F.∷ c55 F.∷ F.[]) F.∷ F.[]) = refl

transformState : S.D4 → State six → State six
transformState sigma (state b p) = state (transformBoard sigma b) p

transformState-correct : ∀ sigma s → transformState sigma s ≡ S.transformState sigma s
transformState-correct sigma (state b p) = cong (λ c → state c p) (transformBoard-correct sigma b)

transformTag : ℕ → State six → State six
transformTag tag = transformState (S.fromTag tag)

transformTag-correct : ∀ tag s → transformTag tag s ≡ S.transformTag tag s
transformTag-correct tag s = transformState-correct (S.fromTag tag) s

abstract
  transport-lower : ∀ tag s → Proven Fast.fastGame6 white (lowerGoal 4) (transformTag tag s) →
    Proven Fast.fastGame6 white (lowerGoal 4) s
  transport-lower tag s proof = Old.transport-lower6 tag s
    (subst (Proven Fast.fastGame6 white (lowerGoal 4)) (transformTag-correct tag s) proof)

  transport-upper : ∀ tag s → Proven Fast.fastGame6 black (upperGoal 4) (transformTag tag s) →
    Proven Fast.fastGame6 black (upperGoal 4) s
  transport-upper tag s proof = Old.transport-upper6 tag s
    (subst (Proven Fast.fastGame6 black (upperGoal 4)) (transformTag-correct tag s) proof)

lowerTransport6 : CertificateTransport Fast.fastGame6 white (lowerGoal 4)
lowerTransport6 = record { act = transformTag ; acceptedTag = S.acceptedTag8 ; transport = transport-lower }

upperTransport6 : CertificateTransport Fast.fastGame6 black (upperGoal 4)
upperTransport6 = record { act = transformTag ; acceptedTag = S.acceptedTag8 ; transport = transport-upper }
