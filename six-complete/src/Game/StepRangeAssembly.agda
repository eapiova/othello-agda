{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Retarget an already checked consecutive row to maps whose
-- successful numeric keys stay inside that row.
module Game.StepRangeAssembly where

open import Prelude
open import Agda.Builtin.Nat using (_+_; _<_) renaming (_-_ to _∸_)
open import Game.Core using (Game; Player)
open import Othello.Order using
  (_≤_; z≤n; s≤s; ≤-trans; ≤-cancel-left; ≤-add-left)
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.EncodedStepAssembly as Encoded

-- The bounds are Boolean guards so concrete chunk witnesses remain compact.
-- Branch pivots do not need ordering hypotheses: lookup itself chooses a side.
data Contained {A : Set} (base n : ℕ) : M.Map A → Set where
  empty-range : Contained base n M.absent
  rows-range : ∀ {rowBase rowCount} {xs : B.Vec A rowCount} →
    (base < suc rowBase) ≡ true →
    (rowBase + rowCount < suc (base + n)) ≡ true →
    Contained base n (M.rows rowBase rowCount xs)
  branch-range : ∀ {pivot l r} → Contained base n l → Contained base n r →
    Contained base n (M.branch pivot l r)

private
  left : ∀ a b → a ∧ b ≡ true → a ≡ true
  left true b accepted = refl
  left false b ()

  right : ∀ a b → a ∧ b ≡ true → b ≡ true
  right true b accepted = accepted
  right false b ()

-- This check inspects only map constructors and numeric row bounds. It never
-- traverses a row vector or evaluates a game state.
check : ∀ {A : Set} → (base n : ℕ) → M.Map A → Bool
check base n M.absent = true
check base n (M.rows rowBase rowCount xs) =
  (base < suc rowBase) ∧ (rowBase + rowCount < suc (base + n))
check base n (M.branch pivot l r) = check base n l ∧ check base n r

check-sound : ∀ {A : Set} base n (table : M.Map A) →
  check base n table ≡ true → Contained base n table
check-sound base n M.absent accepted = empty-range
check-sound base n (M.rows rowBase rowCount xs) accepted = rows-range
  (left (base < suc rowBase) (rowBase + rowCount < suc (base + n)) accepted)
  (right (base < suc rowBase) (rowBase + rowCount < suc (base + n)) accepted)
check-sound base n (M.branch pivot l r) accepted = branch-range
  (check-sound base n l (left (check base n l) (check base n r) accepted))
  (check-sound base n r (right (check base n l) (check base n r) accepted))

private
  restore : ∀ {base key} → base ≤ key → base + (key ∸ base) ≡ key
  restore z≤n = refl
  restore (s≤s bound) = cong suc (restore bound)

  plus-zero : ∀ a → a + zero ≡ a
  plus-zero zero = refl
  plus-zero (suc a) = cong suc (plus-zero a)

  plus-suc : ∀ a b → a + suc b ≡ suc (a + b)
  plus-suc zero b = refl
  plus-suc (suc a) b = cong suc (plus-suc a b)

  above-base : ∀ base k → base ≤ base + k
  above-base base k = subst (λ x → x ≤ base + k) (plus-zero base)
    (≤-add-left base {zero} {k} z≤n)

  rank-bound : ∀ {n} (i : B.Fin n) → suc (B.finToNat i) ≤ n
  rank-bound B.fzero = s≤s z≤n
  rank-bound (B.fsuc i) = s≤s (rank-bound i)

  offset-bound : ∀ {n} base (i : B.Fin n) →
    suc (base + B.finToNat i) ≤ base + n
  offset-bound {n} base i = subst (λ x → x ≤ base + n)
    (plus-suc base (B.finToNat i)) (≤-add-left base (rank-bound i))

  fin-complete : ∀ {n k} → suc k ≤ n →
    Σ (B.Fin n) (λ i → B.finToNat i ≡ k)
  fin-complete {zero} ()
  fin-complete {suc n} {zero} bound = B.fzero , refl
  fin-complete {suc n} {suc k} (s≤s bound) with fin-complete bound
  ... | i , equality = B.fsuc i , cong suc equality

  between-fin : ∀ {base n key} → base ≤ key → suc key ≤ base + n →
    Σ (B.Fin n) (λ i → key ≡ base + B.finToNat i)
  between-fin {base} {n} {key} lower upper
    with fin-complete
      (≤-cancel-left base
        (subst (λ x → x ≤ base + n)
          (sym (trans (plus-suc base (key ∸ base))
            (cong suc (restore lower)))) upper))
  ... | i , equality = i , trans (sym (restore lower))
    (cong (λ k → base + k) (sym equality))

-- A successful lookup in a contained map has a symbolic Fin index in the
-- checked consecutive row. Values are irrelevant to this domain statement.
locate : ∀ {A : Set} {base n} {table : M.Map A} →
  Contained base n table → ∀ key u → M.lookup table key ≡ just u →
  Σ (B.Fin n) (λ i → key ≡ base + B.finToNat i)
locate empty-range key u ()
locate {base = base} {n} (rows-range lower upper) key u hit
  with Laws.rows-hit _ _ _ key hit
... | i , keyEquals , valueEquals = between-fin
  (subst (λ x → base ≤ x) (sym keyEquals)
    (≤-trans (Laws.at-most base _ lower)
      (above-base _ (B.finToNat i))))
  (subst (λ x → x ≤ base + n) (cong suc (sym keyEquals))
    (≤-trans (offset-bound _ i) (Laws.at-most _ (base + n) upper)))
locate (branch-range {pivot} leftRange rightRange) key u hit with key < pivot
... | true = locate leftRange key u hit
... | false = locate rightRange key u hit

module Assembly {S E : Set} (decode : E → S)
  (g : Game S) (p : Player) (goal : S → Bool) where

  module A = Encoded.Assembly decode g p goal

  -- Reuse the source Partial at its symbolic row key. The alignment proof
  -- supplies the exact source lookup; no certificate checker is rerun.
  retarget : ∀ {G : ℕ → E} {base n} {xs : B.Vec E n} {target : M.Map E} →
    (∀ i → B.lookupVec xs i ≡ G (base + B.finToNat i)) →
    A.Partial G (M.rows base n xs) →
    Contained base n target →
    A.Partial G target
  retarget {G} {base} {xs = xs} aligned source inside key hit
    with locate inside key (G key) hit
  ... | i , keyEquals = subst (A.Step G) (sym keyEquals)
    (source (base + B.finToNat i)
      (trans (Laws.rows-roundtrip base xs i) (cong just (aligned i))))
