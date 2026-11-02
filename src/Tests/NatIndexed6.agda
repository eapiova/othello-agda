{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Numeric references are checked independently of native solvers.
module Tests.NatIndexed6 where

open import Prelude
open import Agda.Builtin.Nat using (_<_)
import Game.NatOrder as N
import Game.NatMap as M
import Game.Balanced as B
import Game.Indexed as I
open import Game.Core using (white; Guarantees)
open import Game.Symmetry using (Proven)
open import Game.Soundness using (checkSound)
open import Othello.Board using (State; six)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.Fast6 as Fast
import Othello.NatIndexed6 as D

module Lower = D.Checking Fast.fastGame6 white (lowerGoal 4) lowerTransport6

large-numeric-order : (50000 < 50001) ≡ true
large-numeric-order = refl

self-order-rejected : (50000 < 50000) ≡ false
self-order-rejected = refl

states : B.Vec (State six) 4
states = D.states 4 "b1EMHMMNDPHMDb1EMHMMNDPHMDbM9PEEEDNPHDEbM9PEEEDNPHDE"

-- The state text below is generated from the already checked late fixture.
-- A final theorem uses the data exactly as checked, through this resolver.
G : ℕ → State six
G zero = B.lookupVec states B.fzero
G (suc zero) = B.lookupVec states (B.fsuc B.fzero)
G (suc (suc zero)) = B.lookupVec states (B.fsuc (B.fsuc B.fzero))
G (suc (suc (suc n))) = B.lookupVec states (B.fsuc (B.fsuc (B.fsuc B.fzero)))

C : ℕ → I.IndexedCertificate ℕ
C zero = I.indexedPass (I.indexedChoice 1 (I.indexedFork (I.indexedLeaf ∷ [])))
C (suc zero) = I.cite 0
C (suc (suc zero)) = I.citeBy 4 1
C (suc (suc (suc n))) = I.cite 2

abstract
  rows : ∀ i → Lower.V.TreeOK G i (G i) (C i)
  rows zero = Lower.V.checkLocal-sound (I.globalResolver G) 0 (G 0) (C 0) refl
  rows (suc zero) = Lower.V.checkLocal-sound (I.globalResolver G) 1 (G 1) (C 1) refl
  rows (suc (suc zero)) = Lower.V.checkLocal-sound (I.globalResolver G) 2 (G 2) (C 2) refl
  rows (suc (suc (suc n))) =
    Lower.V.checkLocal-sound (I.globalResolver G) (suc (suc (suc n)))
      (G (suc (suc (suc n)))) (C (suc (suc (suc n)))) refl

  lateLower : Proven Fast.fastGame6 white (lowerGoal 4) (G 3)
  lateLower = Lower.V.global-proven G C rows 3

lateGuarantee : Guarantees Fast.fastGame6 white (lowerGoal 4) (G 3)
lateGuarantee = checkSound Fast.fastGame6 white (lowerGoal 4) (G 3)
  (proj₁ lateLower) (proj₂ lateLower)

self-citation-rejected : Lower.V.checkLocal (I.globalResolver G) 1 (G 1) (I.cite 1) ≡ false
self-citation-rejected = refl

future-citation-rejected : Lower.V.checkLocal (I.globalResolver G) 1 (G 1) (I.cite 2) ≡ false
future-citation-rejected = refl

missing-citation-rejected : Lower.V.checkLocal (λ _ → nothing) 1 (G 1) (I.cite 0) ≡ false
missing-citation-rejected = refl

missing-terminator-rejected : D.readId ('0' ∷ []) ≡ nothing
missing-terminator-rejected = refl

empty-id-rejected : D.readId (';' ∷ []) ≡ nothing
empty-id-rejected = refl

malformed-body-rejected : D.decodeBodies 1 "K0" ≡ nothing
malformed-body-rejected = refl

bad-symmetry-tag-rejected : D.decodeBodies 1 "R80;" ≡ nothing
bad-symmetry-tag-rejected = refl

missing-reply-rejected : Lower.V.checkLocal (I.globalResolver G) 0 (G 0)
  (I.indexedPass (I.indexedChoice 1 (I.indexedFork []))) ≡ false
missing-reply-rejected = refl

outside-map-rejected : M.lookup (M.rows 100 4 states) 99 ≡ nothing
outside-map-rejected = refl

past-map-rejected : M.lookup (M.rows 100 4 states) 104 ≡ nothing
past-map-rejected = refl
