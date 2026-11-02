{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. A checked inline subtree can prove a literal prefix once its
-- cited global states are proved. No source-map ownership is inferred here.
module Othello.InlinePrefix6 where

open import Prelude
open import Game.Core using (Player; Guarantees)
open import Game.Symmetry using (Proven; CertificateTransport; act; transport)
open import Othello.Board using (State; Coord; six)
import Game.DirectedIndexed as D
import Game.Transfer as Transfer
import Game.Soundness as Sound
import Othello.Fast6 as Fast
import Othello.InlineEntries6 as Rules
import Othello.InlineRows6 as Rows
import Othello.RowPacked6 as Packed

module Checking (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Local = Rows.Checking p goal laws

  private
    to-fast : ∀ s → Proven Rules.specializedGame6 p goal s →
      Proven Fast.fastGame6 p goal s
    to-fast s (certificate , accepted) = certificate ,
      trans (sym (Transfer.check-cong Rules.specializedGame6 Fast.fastGame6
        Rules.agreement p goal s certificate)) accepted

    sound : ∀ s → Proven Fast.fastGame6 p goal s → Guarantees Fast.fastGame6 p goal s
    sound s (certificate , accepted) =
      Sound.checkSound Fast.fastGame6 p goal s certificate accepted

  abstract
    guarantee : ∀ L owner s tag (c : D.DirectedCertificate ℕ (Coord six)) →
      Local.V.checkLocal L owner (act laws tag s) c ≡ true →
      (G : ℕ → Packed.PackedState) → Local.V.Compatible L G →
      (∀ j → Proven Rules.specializedGame6 p goal (Packed.decode (G j))) →
      Guarantees Fast.fastGame6 p goal s
    guarantee L owner s tag c accepted G compatible complete =
      sound s (transport laws tag s (to-fast (act laws tag s)
        (Local.V.Old.row-sound (λ j → Packed.decode (G j)) owner
          (λ j earlier → complete j)
          (Local.V.tree-sound L G owner (act laws tag s) c compatible accepted))))
