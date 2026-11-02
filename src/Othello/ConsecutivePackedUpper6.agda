{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Check consecutive owners directly, without nested Fin embeddings.
module Othello.ConsecutivePackedUpper6 where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Game.Core using (black)
open import Othello.Board using (Coord; six)
open import Othello.Statements using (upperGoal)
open import Othello.DirectSymmetry6 using (upperTransport6)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.NatMap as M
import Game.EncodedStepAssembly as Assembly
import Othello.InlineEntries6 as Rules
import Othello.InlineRows6 as Rows
import Othello.RowPacked6 as Packed

private
  module Local = Rows.Checking black (upperGoal 4) upperTransport6

module A = Assembly.Assembly Packed.decode Rules.specializedGame6 black (upperGoal 4)

resolver : (ℕ → Packed.PackedState) → ℕ → Maybe Packed.PackedState
resolver G j = just (G j)

private
  compatible : ∀ G → Local.V.Compatible (resolver G) G
  compatible G j .(G j) refl = refl

  left : ∀ a b → a ∧ b ≡ true → a ≡ true
  left true b checked = refl
  left false b ()

  right : ∀ a b → a ∧ b ≡ true → b ≡ true
  right true b checked = checked
  right false b ()

  plus-zero : ∀ base → base + zero ≡ base
  plus-zero zero = refl
  plus-zero (suc base) = cong suc (plus-zero base)

  plus-suc : ∀ base k → base + suc k ≡ suc (base + k)
  plus-suc zero k = refl
  plus-suc (suc base) k = cong suc (plus-suc base k)

ps : (ℕ → Packed.PackedState) → (base n : ℕ) → B.Vec Packed.PackedState n
ps G base zero = B.nil
ps G base (suc n) = B.cons (G base) (ps G (suc base) n)

checkRows : ∀ G base n → B.Vec (D.DirectedCertificate ℕ (Coord six)) n → Bool
checkRows G base zero B.nil = true
checkRows G base (suc n) (B.cons c cs) =
  Local.V.checkLocal (resolver G) base (Packed.decode (G base)) c ∧
  checkRows G (suc base) n cs

abstract
  lookup-ps : ∀ G base n (i : B.Fin n) →
    B.lookupVec (ps G base n) i ≡ G (base + B.finToNat i)
  lookup-ps G base zero ()
  lookup-ps G base (suc n) B.fzero = cong G (sym (plus-zero base))
  lookup-ps G base (suc n) (B.fsuc i) = trans
    (lookup-ps G (suc base) n i) (cong G (sym (plus-suc base (B.finToNat i))))

  row : ∀ G base c →
    Local.V.checkLocal (resolver G) base (Packed.decode (G base)) c ≡ true →
    A.Step G base
  row G base c checked earlier =
    Local.V.Old.row-sound (λ j → Packed.decode (G j)) base earlier
      (Local.V.tree-sound (resolver G) G base (Packed.decode (G base)) c
        (compatible G) checked)

  steps : ∀ G base n cs → checkRows G base n cs ≡ true →
    (i : B.Fin n) → A.Step G (base + B.finToNat i)
  steps G base zero B.nil accepted ()
  steps G base (suc n) (B.cons c cs) accepted B.fzero =
    subst (A.Step G) (sym (plus-zero base))
      (row G base c (left
        (Local.V.checkLocal (resolver G) base (Packed.decode (G base)) c)
        (checkRows G (suc base) n cs) accepted))
  steps G base (suc n) (B.cons c cs) accepted (B.fsuc i) =
    subst (A.Step G) (sym (plus-suc base (B.finToNat i)))
      (steps G (suc base) n cs (right
        (Local.V.checkLocal (resolver G) base (Packed.decode (G base)) c)
        (checkRows G (suc base) n cs) accepted) i)

  partial : ∀ G base n cs → checkRows G base n cs ≡ true →
    A.Partial G (M.rows base n (ps G base n))
  partial G base n cs accepted = A.rows base (ps G base n) G
    (steps G base n cs accepted)
