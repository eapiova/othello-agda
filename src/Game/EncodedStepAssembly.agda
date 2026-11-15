{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Keep encoded states in the global map and decode at its boundary.
module Game.EncodedStepAssembly where

open import Game.Core
open import Agda.Builtin.Nat using (_+_; _<_)
open import Game.Symmetry using (Proven)
import Game.StepAssembly as Step
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws

module Assembly {S E : Set} (decode : E → S)
  (g : Game S) (p : Player) (goal : S → Bool) where

  module A = Step.Assembly g p goal

  Step : (ℕ → E) → ℕ → Set
  Step G = A.Step (λ j → decode (G j))

  Partial : (ℕ → E) → M.Map E → Set
  Partial G table = ∀ key → M.lookup table key ≡ just (G key) → Step G key

  empty : ∀ G → Partial G M.absent
  empty G key ()

  join : ∀ {G l r} pivot → Partial G l → Partial G r →
    Partial G (M.branch pivot l r)
  join pivot left right key hit with key < pivot
  ... | true = left key hit
  ... | false = right key hit

  rows : ∀ {n} base (ss : B.Vec E n) G →
    (∀ i → Step G (base + B.finToNat i)) → Partial G (M.rows base n ss)
  rows {n} base ss G accepted key hit with Laws.rows-hit base n ss key hit
  ... | i , keyEquals , stateEquals = subst (Step G) (sym keyEquals) (accepted i)

  complete : (table : M.Map E) (fallback : E) → Proven g p goal (decode fallback) →
    Partial (Laws.totalize table fallback) table →
    ∀ key → Step (Laws.totalize table fallback) key
  complete table fallback won partial key earlier with M.lookup table key in found
  ... | just s = subst (Proven g p goal)
      (cong (λ value → decode (fromMaybe fallback value)) found)
      (partial key (trans found
        (cong just (sym (Laws.self-compatible table fallback key s found)))) earlier)
  ... | nothing = won

  global-proven : (G : ℕ → E) → (∀ i → Step G i) →
    ∀ i → Proven g p goal (decode (G i))
  global-proven G = A.global-proven (λ j → decode (G j))
