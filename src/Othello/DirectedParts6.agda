{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted strict syntax gate, followed by the sound directed row checker.
module Othello.DirectedParts6 where

open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (Player)
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; six)
import Game.Balanced as B
import Othello.Fast6 as Fast
import Othello.DirectedCompact6 as Codec
import Othello.DirectedRows6 as Rows
import Othello.LazyIndexed6 as Lazy

validBodies : ℕ → String → Bool
validBodies n text with Codec.decodeBodies n text
... | nothing = false
... | just cs = true

module Checking (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module R = Rows.Checking p goal laws

  checkPart : ∀ {n} → (ℕ → Maybe (State six)) → (B.Fin n → ℕ) → String → String → Bool
  checkPart {n} L embed stateText bodyText = Lazy.validStates n stateText ∧
    (validBodies n bodyText ∧ R.checkRows L embed (Lazy.states n stateText) (Codec.bodies n bodyText))

  private
    right : ∀ a b → a ∧ b ≡ true → b ≡ true
    right true b e = e
    right false b ()

  literalCheck : ∀ {n} → (ℕ → Maybe (State six)) → (B.Fin n → ℕ) → String →
    B.Vec Codec.Certificate n → Bool
  literalCheck {n} L embed stateText cs = Lazy.validStates n stateText ∧
    R.checkRows L embed (Lazy.states n stateText) cs

  abstract
    literalLinked : ∀ {n} L embed stateText (cs : B.Vec Codec.Certificate n) →
      literalCheck L embed stateText cs ≡ true →
      (G : ℕ → State six) → R.V.Compatible L G → ∀ i →
      R.V.TreeOK G (embed i) (B.lookupVec (Lazy.states n stateText) i) (B.lookupVec cs i)
    literalLinked {n} L embed stateText cs checked = R.linked L embed (Lazy.states n stateText) cs
      (right (Lazy.validStates n stateText) _ checked)

    linked : ∀ {n} L embed stateText bodyText →
      checkPart {n} L embed stateText bodyText ≡ true →
      (G : ℕ → State six) → R.V.Compatible L G → ∀ i →
      R.V.TreeOK G (embed i) (B.lookupVec (Lazy.states n stateText) i)
        (B.lookupVec (Codec.bodies n bodyText) i)
    linked {n} L embed stateText bodyText checked =
      R.linked L embed (Lazy.states n stateText) (Codec.bodies n bodyText)
        (right (validBodies n bodyText) _ (right (Lazy.validStates n stateText) _ checked))
