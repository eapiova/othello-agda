{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. A closed toy root checks earlier references and terminal fallback.
module Tests.StepAssembly6.Smoke where
open import Game.Core
open import Game.Certificate
open import Game.Symmetry using (Proven)
import Game.StepAssembly as Step
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatOrder as N

game : Game Bool
game = record { turn = λ _ → white ; next = λ { false → true ∷ [] ; true → [] } ; forcedPass = λ _ → false }
module A = Step.Assembly game white (λ _ → true)
values : B.Vec Bool 2
values = B.cons true (B.cons false B.nil)
table : M.Map Bool
table = M.rows 0 2 values
G : ℕ → Bool
G = Laws.totalize table true

accepted : (i : B.Fin 2) → A.Step G (B.finToNat i)
accepted B.fzero earlier = leaf , refl
accepted (B.fsuc B.fzero) earlier with earlier 0 N.zero-before
... | c , ok = choice 0 c , ok

partial : A.Partial G table
partial = A.rows 0 values G accepted
allSteps : ∀ i → A.Step G i
allSteps = A.complete table true (leaf , refl) partial
closedRoot : Proven game white (λ _ → true) false
closedRoot = A.global-proven G allSteps 1
closedFallback : Proven game white (λ _ → true) true
closedFallback = A.global-proven G allSteps 2
