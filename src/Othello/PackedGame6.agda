{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Repack each transition; decoding preserves the original game.
module Othello.PackedGame6 where

open import Prelude
open import Othello.Board using (State; Coord; six; toMove)
open import Game.Core using (Game; Player; lookup)
open import Game.Symmetry using (CertificateTransport; act)
import Game.MappedTransfer as T
import Game.DirectedIndexed as D
import Othello.RowPacked6 as P
import Othello.Specialized6 as Old
import Othello.DirectMoves6 as Moves
import Othello.Fast6 as Fast
import Othello.AgreedIndexed6 as A

successors : P.PackedState → List P.PackedState
successors s = map P.encode (Old.successors (P.decode s))

game : Game P.PackedState
game = record
  { turn = λ s → toMove (P.decode s)
  ; next = successors
  ; forcedPass = λ s → Old.forcedPass (P.decode s)
  }

refinement : T.Refinement game Old.specializedGame6 P.decode
refinement = T.refinement
  (λ s → P.map-decode-encode (Old.successors (P.decode s)))
  (λ s → refl) (λ s → refl)

pick : P.PackedState → Coord six → Maybe P.PackedState
pick s q = T.mapMaybe P.encode (Moves.pick (P.decode s) q)

private
  nothing-elim : ∀ {A B : Set} {x : A} → nothing ≡ just x → B
  nothing-elim ()

pick-sound : ∀ s q t → pick s q ≡ just t →
  Σ ℕ (λ i → lookup (successors s) i ≡ just t)
pick-sound s q t checked with Moves.pick (P.decode s) q in ep
... | nothing = nothing-elim checked
... | just u with Moves.pick-sound (P.decode s) q u ep
...   | i , hit = i , trans
  (T.lookup-map P.encode (Old.successors (P.decode s)) i)
  (trans (cong (T.mapMaybe P.encode) hit) checked)

picker : D.MovePicker game (Coord six)
picker = D.movePicker pick pick-sound

module Transport (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Agreed = A.With Old.specializedGame6 Old.agreement
  oldLaws = Agreed.adapt p goal laws

  action : ℕ → P.PackedState → P.PackedState
  action tag s = P.encode (act oldLaws tag (P.decode s))

  action-maps : ∀ tag s → P.decode (action tag s) ≡ act oldLaws tag (P.decode s)
  action-maps tag s = P.decode-encode (act oldLaws tag (P.decode s))

  module Adapt = T.Adapting game Old.specializedGame6 P.decode refinement
    p goal oldLaws action action-maps

  packedLaws : CertificateTransport game p (λ s → goal (P.decode s))
  packedLaws = Adapt.laws
