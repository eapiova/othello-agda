{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Alignment checks must inspect keys, values and every branch.
module Tests.NatMapCheck where

open import Prelude
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatMapCheck as Check

private
  same : Bool → Bool → Bool
  same true true = true
  same false false = true
  same true false = false
  same false true = false

  same-sound : ∀ x y → same x y ≡ true → x ≡ y
  same-sound true true e = refl
  same-sound false false e = refl
  same-sound true false ()
  same-sound false true ()

module C = Check.Checking same same-sound

values : B.Vec Bool 2
values = B.cons false (B.cons true B.nil)

table : M.Map Bool
table = M.rows 7 2 values

G : ℕ → Bool
G = Laws.totalize table false

accepted : C.checkAligned table G ≡ true
accepted = refl

aligned : Laws.Aligned table G
aligned = C.aligned-sound table G accepted

compatible : Laws.Compatible table G
compatible = C.compatible-sound table G accepted

wrong-value-rejected : C.checkAligned table (λ _ → false) ≡ false
wrong-value-rejected = refl

wrong-base-rejected : C.checkAligned (M.rows 8 2 values) G ≡ false
wrong-base-rejected = refl

hidden-row-rejected :
  C.checkAligned (M.branch 0 (M.rows 0 1 (B.cons true B.nil)) M.absent)
    (λ _ → false) ≡ false
hidden-row-rejected = refl

empty-accepted : C.checkAligned M.absent G ≡ true
empty-accepted = refl
