{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Encoded citation lookup, with original working-state judgments.
module Othello.PackedRows6 where

open import Prelude
open import Game.Core using (Player)
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; Coord; six)
open import Othello.Encode6 using (stateEquality6)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Othello.PackedGame6 as Game
import Game.NatOrder as N
import Othello.Fast6 as Fast
import Othello.Specialized6 as New
import Othello.DirectMoves6 as Moves
import Othello.AgreedIndexed6 as A
import Othello.RowPacked6 as Packed

module Checking (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Transport = Game.Transport p goal laws
  module V = D.Checker N.order Packed.equality Game.game p (λ s → goal (Packed.decode s))
    Transport.packedLaws Game.picker

  checkRows : ∀ {n} → (ℕ → Maybe Packed.PackedState) →
    (B.Fin n → ℕ) → B.Vec Packed.PackedState n →
    B.Vec (D.DirectedCertificate ℕ (Coord six)) n → Bool
  checkRows L embed B.nil B.nil = true
  checkRows L embed (B.cons s ss) (B.cons c cs) =
    V.checkLocal L (embed B.fzero) s c ∧ checkRows L (λ i → embed (B.fsuc i)) ss cs

  private
    left : ∀ a b → a ∧ b ≡ true → a ≡ true
    left true b checked = refl
    left false b ()

    right : ∀ a b → a ∧ b ≡ true → b ≡ true
    right true b checked = checked
    right false b ()

  checkRows-row : ∀ {n} L embed (ss : B.Vec Packed.PackedState n) cs →
    checkRows L embed ss cs ≡ true → ∀ i →
    V.checkLocal L (embed i) (B.lookupVec ss i) (B.lookupVec cs i) ≡ true
  checkRows-row L embed (B.cons s ss) (B.cons c cs) checked B.fzero =
    left (V.checkLocal L (embed B.fzero) s c)
      (checkRows L (λ i → embed (B.fsuc i)) ss cs) checked
  checkRows-row L embed (B.cons s ss) (B.cons c cs) checked (B.fsuc i) =
    checkRows-row L (λ j → embed (B.fsuc j)) ss cs
      (right (V.checkLocal L (embed B.fzero) s c)
        (checkRows L (λ j → embed (B.fsuc j)) ss cs) checked) i

  abstract
    linked : ∀ {n} L embed (ss : B.Vec Packed.PackedState n) cs →
      checkRows L embed ss cs ≡ true →
      (G : ℕ → Packed.PackedState) → V.Compatible L G → ∀ i →
      V.TreeOK G (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
    linked L embed ss cs checked G compatible i = V.lift-local compatible
      (V.checkLocal-sound L (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
        (checkRows-row L embed ss cs checked i))
