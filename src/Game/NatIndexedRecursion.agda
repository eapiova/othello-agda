{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Reuse the existing row judgments with a non-strict accessibility proof.
module Game.NatIndexedRecursion where

open import Prelude
open import Game.Core
open import Game.Composite using (StateEquality)
open import Game.Symmetry using (Proven; CertificateTransport)
open import Game.Soundness using (checkSound)
import Game.Indexed as I
import Game.NatOrder as N
import Game.NatAccessibility as Access

module Checking {S : Set} (eq : StateEquality S) (g : Game S) (p : Player)
  (goal : S → Bool) (laws : CertificateTransport g p goal) where

  -- Exactly the old order and checker: accepted TreeOK facts do not change.
  module V = I.Checker N.order eq g p goal laws

  global-proven : (G : ℕ → S) (C : ℕ → I.IndexedCertificate ℕ) →
    (∀ i → V.TreeOK G i (G i) (C i)) → ∀ i → Proven g p goal (G i)
  global-proven G C rows i = prove i (Access.wellFounded i)
    where
    prove : ∀ j → I.Acc N.Before j → Proven g p goal (G j)
    prove j (I.acc children) = V.row-sound G j
      (λ k earlier → prove k (children k earlier)) (rows j)

  global-sound : (G : ℕ → S) (C : ℕ → I.IndexedCertificate ℕ) →
    (∀ i → V.TreeOK G i (G i) (C i)) → ∀ i → Guarantees g p goal (G i)
  global-sound G C rows i with global-proven G C rows i
  ... | certificate , accepted = checkSound g p goal (G i) certificate accepted
