{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Keep the generic well-founded closure opaque at concrete maps.
module Game.EncodedMapClosure where

open import Game.Core
open import Game.Symmetry using (Proven)
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.EncodedStepAssembly as Encoded

module Closure {S E : Set} (decode : E → S)
  (g : Game S) (p : Player) (goal : S → Bool) where

  module A = Encoded.Assembly decode g p goal

  abstract
    finish : (table : M.Map E) (fallback : E) → Proven g p goal (decode fallback) →
      A.Partial (Laws.totalize table fallback) table →
      ∀ key → Proven g p goal (decode (Laws.totalize table fallback key))
    finish table fallback won partial = A.global-proven (Laws.totalize table fallback)
      (A.complete table fallback won partial)
