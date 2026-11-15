{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Encoded citation lookup, with original working-state judgments.
module Othello.InlineRows6 where

open import Prelude
open import Game.Core using (Player)
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; Coord; six)
open import Othello.Encode6 using (stateEquality6)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.EncodedResolver as Encoded
import Game.NatOrder as N
import Othello.Fast6 as Fast
import Othello.InlineEntries6 as New
import Othello.LengthMoves6 as Moves
import Othello.AgreedIndexed6 as A
import Othello.RowPacked6 as Packed

module Checking (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Agreed = A.With New.specializedGame6 New.agreement
  module V = Encoded.Checking N.order stateEquality6 New.specializedGame6 p goal
    (Agreed.adapt p goal laws) New.picker Packed.decode Packed.matches Packed.matches-sound

  checkRows : ∀ {n} → (ℕ → Maybe Packed.PackedState) →
    (B.Fin n → ℕ) → B.Vec (State six) n →
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

  checkRows-row : ∀ {n} L embed (ss : B.Vec (State six) n) cs →
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
    linked : ∀ {n} L embed (ss : B.Vec (State six) n) cs →
      checkRows L embed ss cs ≡ true →
      (G : ℕ → Packed.PackedState) → V.Compatible L G → ∀ i →
      V.Old.TreeOK (λ j → Packed.decode (G j)) (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
    linked L embed ss cs checked G compatible i =
      V.tree-sound L G (embed i) (B.lookupVec ss i) (B.lookupVec cs i) compatible
        (checkRows-row L embed ss cs checked i)
