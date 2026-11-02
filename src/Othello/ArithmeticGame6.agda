{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Arithmetic transitions with an exact decoding refinement.
module Othello.ArithmeticGame6 where

open import Prelude
open import Othello.Board using (State; Coord; six; toMove)
open import Othello.Rules using (coords; passState)
open import Game.Core using (Game; Player; lookup)
open import Game.Symmetry using (CertificateTransport; act)
import Game.MappedTransfer as T
import Game.DirectedIndexed as D
import Othello.ArithmeticState6 as S
import Othello.RowPacked6 as P
import Othello.Specialized6 as Old
import Othello.DirectMoves6 as Moves
import Othello.Incremental6 as Inc
import Othello.Fast6 as Fast
import Othello.AgreedIndexed6 as A

prepend : Maybe S.Coded → List S.Coded → List S.Coded
prepend nothing tail = tail
prepend (just s) tail = s ∷ tail

moves : S.Coded → List (Coord six) → List S.Coded
moves s [] = []
moves s (q ∷ qs) = prepend (S.pick s q) (moves s qs)

finish : S.Coded → List S.Coded → List S.Coded → List S.Coded
finish s [] [] = []
finish s [] (_ ∷ _) = S.pass s ∷ []
finish s (t ∷ ts) opposing = t ∷ ts

successors : S.Coded → List S.Coded
successors s = finish s (moves s (coords six)) (moves (S.pass s) (coords six))

passShape : List S.Coded → List S.Coded → Bool
passShape [] [] = false
passShape [] (_ ∷ _) = true
passShape (_ ∷ _) opposing = false

forcedPass : S.Coded → Bool
forcedPass s = passShape (moves s (coords six)) (moves (S.pass s) (coords six))

private
  prepend-maps : ∀ m tail → map S.decode (prepend m tail) ≡
    Moves.prepend (T.mapMaybe S.decode m) (map S.decode tail)
  prepend-maps nothing tail = refl
  prepend-maps (just s) tail = refl

  moves-picks : ∀ s qs → map S.decode (moves s qs) ≡ Moves.pickList (S.decode s) qs
  moves-picks s [] = refl
  moves-picks s (q ∷ qs) rewrite prepend-maps (S.pick s q) (moves s qs)
    | S.pick-decodes s q | moves-picks s qs = refl

  finish-maps : ∀ s ss opposing → map S.decode (finish s ss opposing) ≡
    Fast.finish6 (S.decode s) (map S.decode ss) (map S.decode opposing)
  finish-maps s [] [] = refl
  finish-maps s [] (_ ∷ _) = refl
  finish-maps s (_ ∷ _) opposing = refl

  passShape-maps : ∀ ss opposing → passShape ss opposing ≡
    Old.passShape (map S.decode ss) (map S.decode opposing)
  passShape-maps [] [] = refl
  passShape-maps [] (_ ∷ _) = refl
  passShape-maps (_ ∷ _) opposing = refl

abstract
  moves-maps : ∀ s → map S.decode (moves s (coords six)) ≡ Old.moves (S.decode s)
  moves-maps s = trans (moves-picks s (coords six))
    (trans (Moves.pickList-agrees (S.decode s) (coords six))
      (trans (Inc.moves-agree (S.decode s) (coords six)) (sym (Old.moves-agree (S.decode s)))))

  successors-maps : ∀ s → map S.decode (successors s) ≡ Old.successors (S.decode s)
  successors-maps s rewrite finish-maps s (moves s (coords six)) (moves (S.pass s) (coords six))
    | moves-maps s | moves-maps (S.pass s) = refl

  pass-maps : ∀ s → forcedPass s ≡ Old.forcedPass (S.decode s)
  pass-maps s rewrite passShape-maps (moves s (coords six)) (moves (S.pass s) (coords six))
    | moves-maps s | moves-maps (S.pass s) = refl

game : Game S.Coded
game = record { turn = λ s → toMove (S.decode s) ; next = successors ; forcedPass = forcedPass }

refinement : T.Refinement game Old.specializedGame6 S.decode
refinement = T.refinement successors-maps (λ s → refl) pass-maps

private
  moves-hit : ∀ s q qs t → Moves.Member q qs → S.pick s q ≡ just t →
    Σ ℕ (λ i → lookup (moves s qs) i ≡ just t)
  moves-hit s q (.q ∷ qs) t Moves.here checked rewrite checked = zero , refl
  moves-hit s q (x ∷ qs) t (Moves.there member) checked with S.pick s x
  ... | nothing = moves-hit s q qs t member checked
  ... | just u with moves-hit s q qs t member checked
  ...   | i , hit = suc i , hit

  finish-hit : ∀ s ss opposing i t → lookup ss i ≡ just t →
    lookup (finish s ss opposing) i ≡ just t
  finish-hit s [] opposing i t ()
  finish-hit s (x ∷ xs) opposing i t hit = hit

  pick-sound : ∀ s q t → S.pick s q ≡ just t →
    Σ ℕ (λ i → lookup (successors s) i ≡ just t)
  pick-sound s q t checked with moves-hit s q (coords six) t (Moves.everyCoord q) checked
  ... | i , hit = i , finish-hit s (moves s (coords six)) (moves (S.pass s) (coords six)) i t hit

picker : D.MovePicker game (Coord six)
picker = D.movePicker S.pick pick-sound

module Transport (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Agreed = A.With Old.specializedGame6 Old.agreement
  oldLaws : CertificateTransport Old.specializedGame6 p goal
  oldLaws = Agreed.adapt p goal laws

  action : ℕ → S.Coded → S.Coded
  action tag s = S.pack (act oldLaws tag (S.decode s))

  action-maps : ∀ tag s → S.decode (action tag s) ≡ act oldLaws tag (S.decode s)
  action-maps tag s = P.decode-encode (act oldLaws tag (S.decode s))

  module Adapt = T.Adapting game Old.specializedGame6 S.decode refinement
    p goal oldLaws action action-maps

  arithmeticLaws : CertificateTransport game p (λ s → goal (S.decode s))
  arithmeticLaws = Adapt.laws
