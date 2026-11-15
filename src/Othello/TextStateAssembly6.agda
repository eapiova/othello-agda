{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Close text-map rows using the existing checked numeric Steps.
module Othello.TextStateAssembly6 where

open import Prelude
open import Game.Core using (Player)
open import Game.Symmetry using (Proven)
open import Agda.Builtin.Nat using (_+_; _<_)
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.StepRangeAssembly as Range
import Game.EncodedStepAssembly as Encoded
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.TextStateMap6 as T

module Assembly (p : Player) (goal : State six → Bool) where
  module A = Encoded.Assembly Packed.decode Rules.specializedGame6 p goal

  Partial : (ℕ → Packed.PackedState) → T.Map → Set
  Partial G table = ∀ key → T.lookup table key ≡ just (G key) → A.Step G key

  join : ∀ {G l r} pivot → Partial G l → Partial G r → Partial G (T.branch pivot l r)
  join pivot left right key hit with key < pivot
  ... | true = left key hit
  ... | false = right key hit

  abstract
    from-rows : ∀ {G base n} {xs : B.Vec Packed.PackedState n} {target} →
      (∀ i → B.lookupVec xs i ≡ G (base + B.finToNat i)) →
      A.Partial G (M.rows base n xs) → Range.Contained base n (T.domain target) → Partial G target
    from-rows {G} {base} {xs = xs} {target = target} aligned source inside key hit
      with Range.locate inside key tt (T.domain-hit target key (G key) hit)
    ... | i , equality = subst (A.Step G) (sym equality)
      (source (base + B.finToNat i)
        (trans (Laws.rows-roundtrip base xs i) (cong just (aligned i))))

    complete : (table : T.Map) (fallback : Packed.PackedState) →
      Proven Rules.specializedGame6 p goal (Packed.decode fallback) →
      Partial (T.totalize table fallback) table → ∀ key → A.Step (T.totalize table fallback) key
    complete table fallback won partial key earlier with T.lookup table key in found
    ... | just s = subst (Proven Rules.specializedGame6 p goal)
      (cong (λ value → Packed.decode (fromMaybe fallback value)) found)
      (partial key (trans found (cong just (sym (T.self-compatible table fallback key s found)))) earlier)
    ... | nothing = won

    finish : (table : T.Map) (fallback : Packed.PackedState) →
      Proven Rules.specializedGame6 p goal (Packed.decode fallback) →
      Partial (T.totalize table fallback) table →
      ∀ key → Proven Rules.specializedGame6 p goal (Packed.decode (T.totalize table fallback key))
    finish table fallback won partial = A.global-proven (T.totalize table fallback)
      (complete table fallback won partial)
