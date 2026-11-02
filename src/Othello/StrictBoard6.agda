{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Eager Cell fields; exact agreement with the original game.
module Othello.StrictBoard6 where

open import Prelude
open import Agda.Builtin.Strict using (primForce; primForceLemma)
open import Othello.Board
open import Game.Core using (Game; lookup)
import Othello.Finite as F
import Othello.Specialized6 as Old
import Othello.DirectMoves6 as Moves
import Othello.Fast6 as Fast
import Game.Transfer as T
import Game.MappedTransfer as Map
import Game.DirectedIndexed as D

forceCells : ∀ {n} {A : Set} → F.Vec Cell n → (F.Vec Cell n → A) → A
forceCells F.[] k = k F.[]
forceCells (c F.∷ cs) k = primForce c (λ d → forceCells cs (λ ds → k (d F.∷ ds)))

forceBoard : ∀ {n} {A : Set} → F.Vec (F.Vec Cell 6) n →
  (F.Vec (F.Vec Cell 6) n → A) → A
forceBoard F.[] k = k F.[]
forceBoard (row F.∷ rows) k = forceCells row (λ r → forceBoard rows (λ rs → k (r F.∷ rs)))

abstract
  forceCells-correct : ∀ {n} {A : Set} (cs : F.Vec Cell n) (k : F.Vec Cell n → A) →
    forceCells cs k ≡ k cs
  forceCells-correct F.[] k = refl
  forceCells-correct (c F.∷ cs) k =
    trans (primForceLemma c (λ d → forceCells cs (λ ds → k (d F.∷ ds))))
      (forceCells-correct cs (λ ds → k (c F.∷ ds)))

  forceBoard-correct : ∀ {n} {A : Set} (b : F.Vec (F.Vec Cell 6) n)
    (k : F.Vec (F.Vec Cell 6) n → A) → forceBoard b k ≡ k b
  forceBoard-correct F.[] k = refl
  forceBoard-correct (row F.∷ rows) k =
    trans (forceCells-correct row (λ r → forceBoard rows (λ rs → k (r F.∷ rs))))
      (forceBoard-correct rows (λ rs → k (row F.∷ rs)))

forceState : State six → State six
forceState (state b p) = forceBoard b (λ c → state c p)

abstract
  forceState-correct : ∀ s → forceState s ≡ s
  forceState-correct (state b p) = forceBoard-correct b (λ c → state c p)

  map-force : ∀ ss → map forceState ss ≡ ss
  map-force [] = refl
  map-force (s ∷ ss) rewrite forceState-correct s | map-force ss = refl

successors : State six → List (State six)
successors s = map forceState (Old.successors s)

specializedGame6 : Game (State six)
specializedGame6 = record { turn = toMove ; next = successors ; forcedPass = Old.forcedPass }

agreement : T.Agreement specializedGame6 Fast.fastGame6
agreement = T.agreement (λ s → trans (map-force (Old.successors s)) (Old.successors-agree s))
  (λ s → refl) Old.forcedPass-agree

pick : State six → Coord six → Maybe (State six)
pick s q = Map.mapMaybe forceState (Moves.pick s q)

private
  nothing-elim : ∀ {A B : Set} {x : A} → nothing ≡ just x → B
  nothing-elim ()

  pick-sound : ∀ s q t → pick s q ≡ just t →
    Σ ℕ (λ i → lookup (successors s) i ≡ just t)
  pick-sound s q t checked with Moves.pick s q in ep
  ... | nothing = nothing-elim checked
  ... | just u with Moves.pick-sound s q u ep
  ...   | i , hit = i , trans (Map.lookup-map forceState (Old.successors s) i)
    (trans (cong (Map.mapMaybe forceState) hit) checked)

picker : D.MovePicker specializedGame6 (Coord six)
picker = D.movePicker pick pick-sound
