{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted same-row data representation experiment.
module Tests.PrivateInline6.Part4913 where

private
  open import Prelude
  import Game.Balanced as B
  import Game.NatMap as M
  import Othello.RowPacked6 as Packed
  import Tests.TextMapHoldoutOnly6.Part4913.States as Data
  import Tests.InlineCompactScaling6.Part4913.TextBodies as Body
  import Othello.UnicodeCompact6 as Codec
  import Othello.SharedInlineSteps6 as Shared

abstract
  steps : (G : ℕ → Packed.PackedState) → Shared.Compatible (M.lookup Data.demand) G →
    (∀ i → Packed.decode (G (Data.embed i)) ≡ B.lookupVec Data.ss i) →
    ∀ i → Shared.Step G (Data.embed i)
  steps = Shared.steps (M.lookup Data.demand) Data.embed Data.ss
    (Codec.bodies 200 Body.text) refl
