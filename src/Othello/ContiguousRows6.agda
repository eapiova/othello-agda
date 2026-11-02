{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Increment the numeric owner instead of composing Fin embeddings.
module Othello.ContiguousRows6 where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Game.Core using (Player)
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; Coord; six)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Othello.Fast6 as Fast
import Othello.InlineRows6 as Rows
import Othello.RowPacked6 as Packed

private
  plus-zero : ∀ n → n + zero ≡ n
  plus-zero zero = refl
  plus-zero (suc n) = cong suc (plus-zero n)

  shift : ∀ n k → n + suc k ≡ (n + 1) + k
  shift zero k = refl
  shift (suc n) k = cong suc (shift n k)

  left : ∀ a b → a ∧ b ≡ true → a ≡ true
  left true b checked = refl
  left false b ()

  right : ∀ a b → a ∧ b ≡ true → b ≡ true
  right true b checked = checked
  right false b ()

module Checking (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Old = Rows.Checking p goal laws
  module V = Old.V

  checkRows : ∀ {n} → (ℕ → Maybe Packed.PackedState) → ℕ →
    B.Vec (State six) n → B.Vec (D.DirectedCertificate ℕ (Coord six)) n → Bool
  checkRows L base B.nil B.nil = true
  checkRows L base (B.cons s ss) (B.cons c cs) =
    V.checkLocal L base s c ∧ checkRows L (base + 1) ss cs

  row : ∀ {n} L base (ss : B.Vec (State six) n) cs →
    checkRows L base ss cs ≡ true → ∀ i →
    V.checkLocal L (base + B.finToNat i) (B.lookupVec ss i) (B.lookupVec cs i) ≡ true
  row L base (B.cons s ss) (B.cons c cs) accepted B.fzero =
    subst (λ owner → V.checkLocal L owner s c ≡ true) (sym (plus-zero base))
      (left (V.checkLocal L base s c) (checkRows L (base + 1) ss cs) accepted)
  row L base (B.cons s ss) (B.cons c cs) accepted (B.fsuc i) =
    subst (λ owner → V.checkLocal L owner (B.lookupVec ss i) (B.lookupVec cs i) ≡ true)
      (sym (shift base (B.finToNat i)))
      (row L (base + 1) ss cs
        (right (V.checkLocal L base s c) (checkRows L (base + 1) ss cs) accepted) i)

  abstract
    linked : ∀ {n} L base (ss : B.Vec (State six) n) cs →
      checkRows L base ss cs ≡ true →
      (G : ℕ → Packed.PackedState) → V.Compatible L G → ∀ i →
      V.Old.TreeOK (λ j → Packed.decode (G j)) (base + B.finToNat i)
        (B.lookupVec ss i) (B.lookupVec cs i)
    linked L base ss cs accepted G compatible i =
      V.tree-sound L G (base + B.finToNat i) (B.lookupVec ss i) (B.lookupVec cs i)
        compatible (row L base ss cs accepted i)
