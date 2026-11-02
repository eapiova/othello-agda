{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Encoded map, earlier reference, and missing-key fallback.
module Tests.StepAssembly6.Encoded where
open import Game.Core
open import Game.Certificate
open import Game.Symmetry using (Proven)
import Game.EncodedStepAssembly as Encoded
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatOrder as N

game : Game Bool
game = record { turn = λ _ → white ; next = λ { false → true ∷ [] ; true → [] } ; forcedPass = λ _ → false }
decode : ℕ → Bool
decode zero = true
decode (suc _) = false
module A = Encoded.Assembly decode game white (λ _ → true)
values : B.Vec ℕ 2
values = B.cons 0 (B.cons 1 B.nil)
table : M.Map ℕ
table = M.rows 0 2 values
G : ℕ → ℕ
G = Laws.totalize table 0

accepted : (i : B.Fin 2) → A.Step G (B.finToNat i)
accepted B.fzero earlier = leaf , refl
accepted (B.fsuc B.fzero) earlier with earlier 0 N.zero-before
... | c , ok = choice 0 c , ok

partial : A.Partial G table
partial = A.rows 0 values G accepted
allSteps : ∀ i → A.Step G i
allSteps = A.complete table 0 (leaf , refl) partial
closedRoot : Proven game white (λ _ → true) false
closedRoot = A.global-proven G allSteps 1
closedFallback : Proven game white (λ _ → true) true
closedFallback = A.global-proven G allSteps 2
