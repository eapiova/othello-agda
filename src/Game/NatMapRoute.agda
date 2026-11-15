{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Compact numeric route guards, checked by builtin comparison.
-- Concrete certificates contain no unary inequality proofs. Conversion to the
-- existing route judgment is proved once, with symbolic bounds.
module Game.NatMapRoute where

open import Prelude
open import Agda.Builtin.Nat using (_+_; _<_)
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws

data Route {A : Set} : M.Map A → (base n : ℕ) → B.Vec A n → Set where
  here : ∀ {base n xs} → Route (M.rows base n xs) base n xs
  left : ∀ {pivot l r base n xs} → (base + n < suc pivot) ≡ true →
    Route l base n xs → Route (M.branch pivot l r) base n xs
  right : ∀ {pivot l r base n xs} → (pivot < suc base) ≡ true →
    Route r base n xs → Route (M.branch pivot l r) base n xs

sound : ∀ {A map base n} {xs : B.Vec A n} → Route map base n xs →
  Laws.Route map base n xs
sound here = Laws.here
sound (left {pivot} {base = base} {n = n} bound path) =
  Laws.left (Laws.at-most (base + n) pivot bound) (sound path)
sound (right {pivot} {base = base} bound path) =
  Laws.right (Laws.at-most pivot base bound) (sound path)

aligned : ∀ {A map base n} {xs : B.Vec A n} (G : ℕ → A) →
  Route map base n xs → Laws.Compatible map G →
  Laws.Aligned (M.rows base n xs) G
aligned G path compatible = Laws.route-aligned G (sound path) compatible

-- Close this interface at Compatible, whose key stays neutral. Instantiating
-- an Aligned equality at a large base plus an unknown Fin can force unary
-- arithmetic in the evaluator; the symbolic proof above needs no such work.
compatible : ∀ {A map base n} {xs : B.Vec A n} (G : ℕ → A) →
  Route map base n xs → Laws.Compatible map G →
  Laws.Compatible (M.rows base n xs) G
compatible G path same = Laws.aligned-compatible (aligned G path same)

join-compatible : ∀ {A l r G} pivot → Laws.Compatible {A} l G →
  Laws.Compatible r G → Laws.Compatible (M.branch pivot l r) G
join-compatible pivot leftOK rightOK key u hit with key < pivot
... | true = leftOK key u hit
... | false = rightOK key u hit
