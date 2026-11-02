{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Cached working boards with six-Nat stored citation values.
module Othello.RowCacheRows6 where

open import Prelude
open import Game.Core using (Player)
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; Coord; six)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.EncodedResolver as Encoded
import Game.NatOrder as N
import Othello.Fast6 as Fast
import Othello.RowCacheGame6 as New
import Othello.RowCacheState6 as Cache
import Othello.RowPacked6 as Packed

decode : Packed.PackedState → Cache.CachedState
decode t = Cache.pack (Packed.decode t)

matches : Cache.CachedState → Packed.PackedState → Bool
matches s t = Cache.matches s t

matches-sound : ∀ s t → matches s t ≡ true → s ≡ decode t
matches-sound s t checked = Cache.injective s (decode t)
  (trans (Cache.matches-sound s t checked) (sym (Cache.decode-pack (Packed.decode t))))

module Checking (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Transport = New.Transport p goal laws
  module V = Encoded.Checking N.order Cache.equality New.game p (λ s → goal (Cache.decode s))
    Transport.cachedLaws New.picker decode matches matches-sound

  checkRows : ∀ {n} → (ℕ → Maybe Packed.PackedState) →
    (B.Fin n → ℕ) → B.Vec Cache.CachedState n →
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

  checkRows-row : ∀ {n} L embed (ss : B.Vec Cache.CachedState n) cs →
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
    linked : ∀ {n} L embed (ss : B.Vec Cache.CachedState n) cs →
      checkRows L embed ss cs ≡ true →
      (G : ℕ → Packed.PackedState) → V.Compatible L G → ∀ i →
      V.Old.TreeOK (λ j → decode (G j)) (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
    linked L embed ss cs checked G compatible i =
      V.tree-sound L G (embed i) (B.lookupVec ss i) (B.lookupVec cs i) compatible
        (checkRows-row L embed ss cs checked i)
