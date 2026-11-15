{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Force numeric state fields once after each transition.
module Othello.StrictPackedGame6 where

open import Prelude
open import Othello.Board using (State; Coord; six)
open import Game.Core using (Game; Player; lookup)
open import Game.Symmetry using (CertificateTransport; act)
import Game.MappedTransfer as T
import Game.DirectedIndexed as D
import Othello.RowPacked6 as P
import Othello.PackedGame6 as Base
import Othello.StrictPacked6 as Strict
import Othello.Fast6 as Fast

game : Game P.PackedState
game = record
  { turn = Game.turn Base.game
  ; next = λ s → map Strict.forcePacked (Base.successors s)
  ; forcedPass = Game.forcedPass Base.game
  }

private
  map-id : ∀ {A : Set} (xs : List A) → map (λ x → x) xs ≡ xs
  map-id [] = refl
  map-id (x ∷ xs) rewrite map-id xs = refl

  map-force : ∀ ss → map Strict.forcePacked ss ≡ ss
  map-force [] = refl
  map-force (s ∷ ss) rewrite Strict.forcePacked-correct s | map-force ss = refl

  next-maps : ∀ s → map (λ x → x) (Game.next game s) ≡ Base.successors s
  next-maps s = trans (map-id _) (map-force (Base.successors s))

refinement : T.Refinement game Base.game (λ s → s)
refinement = T.refinement next-maps (λ s → refl) (λ s → refl)

pick : P.PackedState → Coord six → Maybe P.PackedState
pick s q = T.mapMaybe Strict.forcePacked (Base.pick s q)

private
  nothing-elim : ∀ {A B : Set} {x : A} → nothing ≡ just x → B
  nothing-elim ()

  pick-sound : ∀ s q t → pick s q ≡ just t →
    Σ ℕ (λ i → lookup (Game.next game s) i ≡ just t)
  pick-sound s q t checked with Base.pick s q in ep
  ... | nothing = nothing-elim checked
  ... | just u with D.pick-sound Base.picker s q u ep
  ...   | i , hit = i , trans
    (T.lookup-map Strict.forcePacked (Base.successors s) i)
    (trans (cong (T.mapMaybe Strict.forcePacked) hit) checked)

picker : D.MovePicker game (Coord six)
picker = D.movePicker pick pick-sound

module Transport (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Old = Base.Transport p goal laws
  module Adapt = T.Adapting game Base.game (λ s → s) refinement p
    (λ s → goal (P.decode s)) Old.packedLaws Old.action (λ tag s → refl)

  packedLaws : CertificateTransport game p (λ s → goal (P.decode s))
  packedLaws = Adapt.laws
