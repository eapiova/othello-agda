{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. A symmetry citation must transport checked evidence; a
-- geometric permutation or a successful native sample alone is insufficient.
module Game.Symmetry where

open import Game.Core
open import Game.Certificate
open import Game.Soundness using (checkSound)

-- Kept here independently of Game.Shared to avoid an import cycle.
Proven : ∀ {S} → Game S → Player → (S → Bool) → S → Set
Proven g p goal s = Σ Certificate (λ c → check g p goal s c ≡ true)

record CertificateTransport {S : Set} (g : Game S) (p : Player)
                            (goal : S → Bool) : Set where
  field
    act : ℕ → S → S
    acceptedTag : ℕ → Bool
    -- The returned certificate may have different choice indices and fork
    -- order. Reusing the input certificate would need stronger ordered laws.
    transport : ∀ tag s → Proven g p goal (act tag s) → Proven g p goal s
open CertificateTransport public

identityTransport : ∀ {S} (g : Game S) p goal → CertificateTransport g p goal
identityTransport g p goal = record
  { act = λ _ s → s
  ; acceptedTag = λ _ → true
  ; transport = λ _ _ proof → proof
  }

transportSound : ∀ {S} {g : Game S} {p goal}
  (laws : CertificateTransport g p goal) tag s →
  Proven g p goal (act laws tag s) → Guarantees g p goal s
transportSound {g = g} {p} {goal} laws tag s proof
  with transport laws tag s proof
... | c , ok = checkSound g p goal s c ok
