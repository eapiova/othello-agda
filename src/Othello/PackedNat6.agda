{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Integer codes are untrusted data, decoded to ordinary boards.
-- Certificate checking and the initial-state equality remain obligations.
module Othello.PackedNat6 where

open import Prelude
open import Agda.Builtin.Nat using (div-helper; mod-helper)
open import Othello.Board
import Othello.Finite as F
import Game.Balanced as B

private
  -- 3^(6*r+c)-1. Literal branches avoid rebuilding a numeric lookup table.
  power : Coord six → ℕ
  power (F.zero , F.zero) = 0
  power (F.zero , F.suc F.zero) = 2
  power (F.zero , F.suc (F.suc F.zero)) = 8
  power (F.zero , F.suc (F.suc (F.suc F.zero))) = 26
  power (F.zero , F.suc (F.suc (F.suc (F.suc F.zero)))) = 80
  power (F.zero , F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) = 242
  power (F.suc F.zero , F.zero) = 728
  power (F.suc F.zero , F.suc F.zero) = 2186
  power (F.suc F.zero , F.suc (F.suc F.zero)) = 6560
  power (F.suc F.zero , F.suc (F.suc (F.suc F.zero))) = 19682
  power (F.suc F.zero , F.suc (F.suc (F.suc (F.suc F.zero)))) = 59048
  power (F.suc F.zero , F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) = 177146
  power (F.suc (F.suc F.zero) , F.zero) = 531440
  power (F.suc (F.suc F.zero) , F.suc F.zero) = 1594322
  power (F.suc (F.suc F.zero) , F.suc (F.suc F.zero)) = 4782968
  power (F.suc (F.suc F.zero) , F.suc (F.suc (F.suc F.zero))) = 14348906
  power (F.suc (F.suc F.zero) , F.suc (F.suc (F.suc (F.suc F.zero)))) = 43046720
  power (F.suc (F.suc F.zero) , F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) = 129140162
  power (F.suc (F.suc (F.suc F.zero)) , F.zero) = 387420488
  power (F.suc (F.suc (F.suc F.zero)) , F.suc F.zero) = 1162261466
  power (F.suc (F.suc (F.suc F.zero)) , F.suc (F.suc F.zero)) = 3486784400
  power (F.suc (F.suc (F.suc F.zero)) , F.suc (F.suc (F.suc F.zero))) = 10460353202
  power (F.suc (F.suc (F.suc F.zero)) , F.suc (F.suc (F.suc (F.suc F.zero)))) = 31381059608
  power (F.suc (F.suc (F.suc F.zero)) , F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) = 94143178826
  power (F.suc (F.suc (F.suc (F.suc F.zero))) , F.zero) = 282429536480
  power (F.suc (F.suc (F.suc (F.suc F.zero))) , F.suc F.zero) = 847288609442
  power (F.suc (F.suc (F.suc (F.suc F.zero))) , F.suc (F.suc F.zero)) = 2541865828328
  power (F.suc (F.suc (F.suc (F.suc F.zero))) , F.suc (F.suc (F.suc F.zero))) = 7625597484986
  power (F.suc (F.suc (F.suc (F.suc F.zero))) , F.suc (F.suc (F.suc (F.suc F.zero)))) = 22876792454960
  power (F.suc (F.suc (F.suc (F.suc F.zero))) , F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) = 68630377364882
  power (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))) , F.zero) = 205891132094648
  power (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))) , F.suc F.zero) = 617673396283946
  power (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))) , F.suc (F.suc F.zero)) = 1853020188851840
  power (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))) , F.suc (F.suc (F.suc F.zero))) = 5559060566555522
  power (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))) , F.suc (F.suc (F.suc (F.suc F.zero)))) = 16677181699666568
  power (F.suc (F.suc (F.suc (F.suc (F.suc F.zero)))) , F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) = 50031545098999706

  cell : ℕ → Cell
  cell zero = empty
  cell (suc zero) = blackCell
  cell (suc (suc n)) = whiteCell

  player : ℕ → Player
  player zero = black
  player (suc n) = white

  digit : ℕ → Coord six → Cell
  digit n q = cell (mod-helper 0 2 (div-helper 0 (power q) n (power q)) 2)

decode : ℕ → State six
decode n = state
  (F.tabulate (λ r → F.tabulate (λ c → digit (div-helper 0 1 n 1) (r , c))))
  (player (mod-helper 0 1 n 1))

states : ∀ {n} → B.Vec ℕ n → B.Vec (State six) n
states B.nil = B.nil
states (B.cons code codes) = B.cons (decode code) (states codes)
