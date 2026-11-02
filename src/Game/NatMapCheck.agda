{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Boolean row alignment is accepted only through its soundness proof.
module Game.NatMapCheck where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws

module Checking {A : Set} (equal : A → A → Bool)
  (equal-sound : ∀ x y → equal x y ≡ true → x ≡ y) where

  private
    left : ∀ a b → a ∧ b ≡ true → a ≡ true
    left true b e = refl
    left false b ()

    right : ∀ a b → a ∧ b ≡ true → b ≡ true
    right true b e = e
    right false b ()

  checkRows : ∀ {n} → (B.Fin n → ℕ) → (ℕ → A) → B.Vec A n → Bool
  checkRows embed G B.nil = true
  checkRows embed G (B.cons x xs) =
    equal (G (embed B.fzero)) x ∧
    checkRows (λ i → embed (B.fsuc i)) G xs

  checkRows-sound : ∀ {n} embed G (xs : B.Vec A n) →
    checkRows embed G xs ≡ true → ∀ i → G (embed i) ≡ B.lookupVec xs i
  checkRows-sound embed G B.nil e ()
  checkRows-sound embed G (B.cons x xs) e B.fzero =
    equal-sound (G (embed B.fzero)) x
      (left (equal (G (embed B.fzero)) x)
        (checkRows (λ i → embed (B.fsuc i)) G xs) e)
  checkRows-sound embed G (B.cons x xs) e (B.fsuc i) =
    checkRows-sound (λ j → embed (B.fsuc j)) G xs
      (right (equal (G (embed B.fzero)) x)
        (checkRows (λ j → embed (B.fsuc j)) G xs) e) i

  -- Check both branches, including rows hidden by an unusual pivot. This is
  -- the stronger Aligned judgment, not merely agreement on reachable lookups.
  checkAligned : M.Map A → (ℕ → A) → Bool
  checkAligned M.absent G = true
  checkAligned (M.rows base n xs) G =
    checkRows (λ i → base + B.finToNat i) G xs
  checkAligned (M.branch pivot l r) G = checkAligned l G ∧ checkAligned r G

  aligned-sound : ∀ map G → checkAligned map G ≡ true → Laws.Aligned map G
  aligned-sound M.absent G e = tt
  aligned-sound (M.rows base n xs) G e =
    checkRows-sound (λ i → base + B.finToNat i) G xs e
  aligned-sound (M.branch pivot l r) G e =
    aligned-sound l G (left (checkAligned l G) (checkAligned r G) e) ,
    aligned-sound r G (right (checkAligned l G) (checkAligned r G) e)

  compatible-sound : ∀ map G → checkAligned map G ≡ true → Laws.Compatible map G
  compatible-sound map G e = Laws.aligned-compatible {map = map} {G = G} (aligned-sound map G e)
