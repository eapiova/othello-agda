{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Concrete, proved D4 certificate transport for both bounds.
module Othello.SharedSymmetry6 where

open import Prelude
open import Game.Core using (white; black; next)
open import Game.Permutation using (Perm)
open import Game.Symmetry using (CertificateTransport; Proven)
import Game.CertificateTransport as T
open import Othello.Board using (State; six)
open import Othello.Statements using (lowerGoal; upperGoal)
import Othello.Symmetry6 as S
import Othello.SymmetryEnumeration6 as E
import Othello.Fast6 as F
import Othello.Rules as R

-- Fast6 has the same ordered successors as the rules. Symmetry changes that
-- order, so a permutation is required rather than equality of successor lists.
fast-successors-perm : ∀ σ s →
  Perm (map (S.transformState σ) (next F.fastGame6 s))
       (next F.fastGame6 (S.transformState σ s))
fast-successors-perm σ s =
  subst (λ xs → Perm xs (next F.fastGame6 (S.transformState σ s)))
    (sym (cong (map (S.transformState σ)) (F.next6-correct s)))
    (subst (λ ys → Perm (map (S.transformState σ) (R.successors s)) ys)
      (sym (F.next6-correct (S.transformState σ s))) (E.successors-perm σ s))

action-laws : (goal : State six → Bool) →
  (∀ σ s → goal (S.transformState σ s) ≡ goal s) →
  (σ : S.D4) → T.BijectiveActionLaws F.fastGame6 goal (S.transformState σ)
action-laws goal invariant σ = record
  { inverse = S.transformState (S.inverse σ)
  ; inverse-left = S.transformState-inverse σ
  ; inverse-right = λ s → trans
      (sym (cong (λ τ → S.transformState τ (S.transformState (S.inverse σ) s))
        (S.inverse-involutive σ))) (S.transformState-inverse (S.inverse σ) s)
  ; forward-laws = record
      { preserves-turn = S.turn-preserved σ
      ; preserves-pass = E.forcedPass-equivariant σ
      ; preserves-goal = invariant σ
      ; successors = fast-successors-perm σ
      }
  }

-- Only the action and tag test are computational. Keep already checked
-- certificate reconstruction opaque when clients assemble guarantees.
abstract
  transport-lower6 : ∀ tag s → Proven F.fastGame6 white (lowerGoal 4) (S.transformTag tag s) →
    Proven F.fastGame6 white (lowerGoal 4) s
  transport-lower6 tag = T.bijective-transport
    (action-laws (lowerGoal 4) E.lowerGoal4-invariant (S.fromTag tag))

  transport-upper6 : ∀ tag s → Proven F.fastGame6 black (upperGoal 4) (S.transformTag tag s) →
    Proven F.fastGame6 black (upperGoal 4) s
  transport-upper6 tag = T.bijective-transport
    (action-laws (upperGoal 4) E.upperGoal4-invariant (S.fromTag tag))

lowerTransport6 : CertificateTransport F.fastGame6 white (lowerGoal 4)
lowerTransport6 = record
  { act = S.transformTag
  ; acceptedTag = S.acceptedTag8
  ; transport = transport-lower6
  }

upperTransport6 : CertificateTransport F.fastGame6 black (upperGoal 4)
upperTransport6 = record
  { act = S.transformTag
  ; acceptedTag = S.acceptedTag8
  ; transport = transport-upper6
  }
