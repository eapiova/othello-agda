{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.Rules where

open import Prelude
import Agda.Builtin.Int
open import Othello.Finite as F using ()
open import Othello.Board
open import Othello.Rules

positions : ∀ {n} → List (F.Fin n × F.Fin n) → List (ℕ × ℕ)
positions = map (λ q → F.toℕ (proj₁ q) , F.toℕ (proj₂ q))

q00 q02 q11 q13 : Coord four
q00 = F.zero , F.zero
q02 = F.zero , F.suc (F.suc F.zero)
q11 = F.suc F.zero , F.suc F.zero
q13 = F.suc F.zero , F.suc (F.suc (F.suc F.zero))

edgeBoard : State four
edgeBoard = state ((empty F.∷ empty F.∷ empty F.∷ whiteCell F.∷ F.[]) F.∷ (blackCell F.∷ empty F.∷ empty F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ empty F.∷ empty F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ empty F.∷ empty F.∷ empty F.∷ F.[]) F.∷ F.[]) black

cornerBoard : State four
cornerBoard = state ((empty F.∷ whiteCell F.∷ blackCell F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ empty F.∷ empty F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ empty F.∷ empty F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ empty F.∷ empty F.∷ empty F.∷ F.[]) F.∷ F.[]) black

multiBoard : State four
multiBoard = state ((empty F.∷ empty F.∷ empty F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ empty F.∷ whiteCell F.∷ blackCell F.∷ F.[]) F.∷ (empty F.∷ whiteCell F.∷ empty F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ blackCell F.∷ empty F.∷ empty F.∷ F.[]) F.∷ F.[]) black

passBoard : State four
passBoard = state ((empty F.∷ empty F.∷ empty F.∷ blackCell F.∷ F.[]) F.∷ (whiteCell F.∷ whiteCell F.∷ blackCell F.∷ whiteCell F.∷ F.[]) F.∷ (empty F.∷ whiteCell F.∷ whiteCell F.∷ whiteCell F.∷ F.[]) F.∷ (blackCell F.∷ whiteCell F.∷ whiteCell F.∷ whiteCell F.∷ F.[]) F.∷ F.[]) black

mirroredStart : State four
mirroredStart = state ((empty F.∷ empty F.∷ empty F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ blackCell F.∷ whiteCell F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ whiteCell F.∷ blackCell F.∷ empty F.∷ F.[]) F.∷ (empty F.∷ empty F.∷ empty F.∷ empty F.∷ F.[]) F.∷ F.[]) black

initial-four-moves : positions (legalMoves (initial four)) ≡
  (0 , 1) ∷ (1 , 0) ∷ (2 , 3) ∷ (3 , 2) ∷ []
initial-four-moves = refl

initial-eight-moves : positions (legalMoves (initial eight)) ≡
  (2 , 3) ∷ (3 , 2) ∷ (4 , 5) ∷ (5 , 4) ∷ []
initial-eight-moves = refl

-- The standard central discs reflected horizontally, still with Black first.
mirrored-moves : positions (legalMoves mirroredStart) ≡
  (0 , 2) ∷ (1 , 3) ∷ (2 , 0) ∷ (3 , 1) ∷ []
mirrored-moves = refl

no-edge-wrap : legal edgeBoard q02 ≡ false
no-edge-wrap = refl

corner-legal : legal cornerBoard q00 ≡ true
corner-legal = refl

corner-capture : positions (allCaptures cornerBoard q00) ≡ (0 , 1) ∷ []
corner-capture = refl

multiple-capture : positions (allCaptures multiBoard q11) ≡
  (1 , 2) ∷ (2 , 1) ∷ []
multiple-capture = refl

multiple-black : discs black (applyMove multiBoard q11) ≡ 5
multiple-black = refl

multiple-white : discs white (applyMove multiBoard q11) ≡ 0
multiple-white = refl

occupied-rejected : legal multiBoard q13 ≡ false
occupied-rejected = refl

illegal-no-op : applyMove multiBoard q13 ≡ multiBoard
illegal-no-op = refl

pass-forced : forcedPass passBoard ≡ true
pass-forced = refl

pass-has-no-placement : legalMoves passBoard ≡ []
pass-has-no-placement = refl

pass-single-successor : successors passBoard ≡ passState passBoard ∷ []
pass-single-successor = refl

pass-enables-opponent : positions (legalMoves (passState passBoard)) ≡
  (0 , 1) ∷ (0 , 2) ∷ []
pass-enables-opponent = refl

pass-preserves-board : board (passState passBoard) ≡ board passBoard
pass-preserves-board = refl

emptyState : State four
emptyState = state (F.tabulate (λ _ → F.tabulate (λ _ → empty))) black

empty-terminal : successors emptyState ≡ []
empty-terminal = refl

terminal-does-not-pass : forcedPass emptyState ≡ false
terminal-does-not-pass = refl

empty-score : score emptyState ≡ Agda.Builtin.Int.pos 0
empty-score = refl
