{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Fused row soundness for directed and ordinary certificates.
module Othello.DirectedRows6 where

open import Prelude
open import Game.Core using (Player)
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; Coord; six)
open import Othello.Encode6 using (stateEquality6)
import Game.Balanced as B
import Game.Indexed as I
import Game.DirectedIndexed as D
import Game.NatOrder as N
import Othello.Fast6 as Fast
import Othello.Specialized6 as New
import Othello.DirectMoves6 as Moves
import Othello.AgreedIndexed6 as A
import Othello.NatIndexed6 as Ordinary

module Checking (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Agreed = A.With New.specializedGame6 New.agreement
  module Old = Ordinary.Checking New.specializedGame6 p goal (Agreed.adapt p goal laws)
  module V = D.Checker N.order stateEquality6 New.specializedGame6 p goal
    (Agreed.adapt p goal laws) Moves.picker

  checkRows : ∀ {n} → D.Resolver ℕ (State six) →
    (B.Fin n → ℕ) → B.Vec (State six) n →
    B.Vec (D.DirectedCertificate ℕ (Coord six)) n → Bool
  checkRows L embed B.nil B.nil = true
  checkRows L embed (B.cons s ss) (B.cons c cs) =
    V.checkLocal L (embed B.fzero) s c ∧ checkRows L (λ i → embed (B.fsuc i)) ss cs

  private
    left : ∀ a b → a ∧ b ≡ true → a ≡ true
    left true b e = refl
    left false b ()

    right : ∀ a b → a ∧ b ≡ true → b ≡ true
    right true b e = e
    right false b ()

  checkRows-row : ∀ {n} L embed (ss : B.Vec (State six) n) cs →
    checkRows L embed ss cs ≡ true → ∀ i →
    V.checkLocal L (embed i) (B.lookupVec ss i) (B.lookupVec cs i) ≡ true
  checkRows-row L embed (B.cons s ss) (B.cons c cs) e B.fzero =
    left (V.checkLocal L (embed B.fzero) s c)
      (checkRows L (λ i → embed (B.fsuc i)) ss cs) e
  checkRows-row L embed (B.cons s ss) (B.cons c cs) e (B.fsuc i) =
    checkRows-row L (λ j → embed (B.fsuc j)) ss cs
      (right (V.checkLocal L (embed B.fzero) s c)
        (checkRows L (λ j → embed (B.fsuc j)) ss cs) e) i

  abstract
    linked : ∀ {n} L embed (ss : B.Vec (State six) n) cs →
      checkRows L embed ss cs ≡ true →
      (G : ℕ → State six) → V.Compatible L G → ∀ i →
      V.TreeOK G (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
    linked L embed ss cs accepted G compatible i = V.lift-local compatible
      (V.checkLocal-sound L (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
        (checkRows-row L embed ss cs accepted i))

    ordinary-linked : ∀ {n} L embed (ss : B.Vec (State six) n) cs →
      Old.checkRows L embed ss cs ≡ true →
      (G : ℕ → State six) → Old.V.Compatible L G → ∀ i →
      Old.V.TreeOK G (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
    ordinary-linked L embed ss cs accepted G compatible i = Old.V.lift-local compatible
      (Old.V.checkLocal-sound L (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
        (Old.checkRows-row L embed ss cs accepted i))
