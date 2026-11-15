{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Two independent parts compose into a complete late-position
-- theorem, including checked terminal data for IDs outside the finite map.
module Tests.NatAssembly6 where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Agda.Builtin.String using (String)
open import Game.Core using (white; Guarantees; next)
open import Game.Symmetry using (Proven)
open import Game.Soundness using (checkSound)
open import Game.Transfer using (guarantees-transfer)
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.Balanced as B
import Othello.NatIndexed6 as D
import Othello.NatAssembly6 as Assembly
import Othello.Fast6 as Fast
import Othello.Rules as Rules
open import Othello.Board using (State; six; initial)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
open import Othello.CompactShared6 using (decodeCompactState)
open import Othello.Proof6 using (fastAgreement)

module A = Assembly.Assembly Fast.fastGame6 white (lowerGoal 4) lowerTransport6

stateText0 stateText1 bodyText0 bodyText1 : String
stateText0 = "b1EMHMMNDPHMDb1EMHMMNDPHMD"
stateText1 = "bM9PEEEDNPHDEbM9PEEEDNPHDE"
bodyText0 = "PC1F1LK0;"
bodyText1 = "R41;K2;"

ss0 ss1 : B.Vec (State six) 2
ss0 = D.states 2 stateText0
ss1 = D.states 2 stateText1
cs0 cs1 : B.Vec (I.IndexedCertificate ℕ) 2
cs0 = D.bodies 2 bodyText0
cs1 = D.bodies 2 bodyText1

statesMap : M.Map (State six)
statesMap = M.branch 2 (M.rows 0 2 ss0) (M.rows 2 2 ss1)
bodiesMap : M.Map (I.IndexedCertificate ℕ)
bodiesMap = M.branch 2 (M.rows 0 2 cs0) (M.rows 2 2 cs1)

fallback : State six
fallback = fromMaybe (initial six) (decodeCompactState "wQQQQQQQQQQQQ")

terminal : next Fast.fastGame6 fallback ≡ []
terminal = refl
won : lowerGoal 4 fallback ≡ true
won = refl

G : ℕ → State six
G = Laws.totalize statesMap fallback
C : ℕ → I.IndexedCertificate ℕ
C = Laws.totalize bodiesMap I.indexedLeaf

local0 : M.Map (State six)
local0 = M.branch 2 (M.rows 0 2 ss0) M.absent
L0 L1 : I.Resolver ℕ (State six)
L0 = M.lookup local0
L1 = M.lookup statesMap

included0 : Laws.Included local0 statesMap
included0 = Laws.fork Laws.same Laws.empty

abstract
  accepted0 : A.Lower.checkPart {2} L0 (λ i → 0 + B.finToNat i) stateText0 bodyText0 ≡ true
  accepted0 = refl
  accepted1 : A.Lower.checkPart {2} L1 (λ i → 2 + B.finToNat i) stateText1 bodyText1 ≡ true
  accepted1 = refl

  partial0 : A.Partial G C (M.rows 0 2 ss0)
  partial0 = A.linkedRows {n = 2} 0 L0 stateText0 bodyText0 accepted0 G C
    (Laws.restrict {small = local0} {large = statesMap} {G = G} included0
      (Laws.self-compatible statesMap fallback))
    statesMap bodiesMap
    (Laws.left (Laws.at-most 2 2 refl) Laws.here)
    (Laws.left (Laws.at-most 2 2 refl) Laws.here)
    (Laws.self-compatible statesMap fallback) (Laws.self-compatible bodiesMap I.indexedLeaf)

  partial1 : A.Partial G C (M.rows 2 2 ss1)
  partial1 = A.linkedRows {n = 2} 2 L1 stateText1 bodyText1 accepted1 G C
    (Laws.self-compatible statesMap fallback) statesMap bodiesMap
    (Laws.right (Laws.at-most 2 2 refl) Laws.here)
    (Laws.right (Laws.at-most 2 2 refl) Laws.here)
    (Laws.self-compatible statesMap fallback) (Laws.self-compatible bodiesMap I.indexedLeaf)

  rows : ∀ key → A.Lower.V.TreeOK G key (G key) (C key)
  rows = A.complete statesMap bodiesMap
    (Laws.fork-pair Laws.rows-pair Laws.rows-pair) fallback terminal won
    (A.join 2 partial0 partial1)

  rootProof : Proven Fast.fastGame6 white (lowerGoal 4) (G 3)
  rootProof = A.Lower.V.global-proven G C rows 3

original : Guarantees (Rules.game six) white (lowerGoal 4) (G 3)
original = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement
  (checkSound Fast.fastGame6 white (lowerGoal 4) (G 3) (proj₁ rootProof) (proj₂ rootProof))

outsideIsCheckedTerminal : G 50000 ≡ fallback
outsideIsCheckedTerminal = refl

malformedPartRejected : A.Lower.checkPart {2} L0 (λ i → 0 + B.finToNat i)
  stateText0 "PC1F1L" ≡ false
malformedPartRejected = refl
