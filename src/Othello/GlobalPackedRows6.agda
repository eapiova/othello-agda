{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Reconstruct each checked row directly from the global packed map.
module Othello.GlobalPackedRows6 where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Game.Core using (white)
open import Othello.Board using (State; Coord; six)
open import Othello.Statements using (lowerGoal)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.NatMap as M
import Game.EncodedStepAssembly as Assembly
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.SharedInlineSteps6 as Shared

module A = Assembly.Assembly Packed.decode Rules.specializedGame6 white (lowerGoal 4)

module Vec where
  tabulate : ∀ {A : Set} {n} → (B.Fin n → A) → B.Vec A n
  tabulate {n = zero} f = B.nil
  tabulate {n = suc n} f = B.cons (f B.fzero)
    (tabulate (λ i → f (B.fsuc i)))

  lookup-tabulate : ∀ {A : Set} {n} (f : B.Fin n → A) i →
    B.lookupVec (tabulate f) i ≡ f i
  lookup-tabulate f B.fzero = refl
  lookup-tabulate f (B.fsuc i) = lookup-tabulate (λ j → f (B.fsuc j)) i

vec-map : ∀ {A C : Set} {n} → (A → C) → B.Vec A n → B.Vec C n
vec-map f B.nil = B.nil
vec-map f (B.cons x xs) = B.cons (f x) (vec-map f xs)

lookup-map : ∀ {A C : Set} {n} (f : A → C) (xs : B.Vec A n) i →
  B.lookupVec (vec-map f xs) i ≡ f (B.lookupVec xs i)
lookup-map f B.nil ()
lookup-map f (B.cons x xs) B.fzero = refl
lookup-map f (B.cons x xs) (B.fsuc i) = lookup-map f xs i

ps : (G : ℕ → Packed.PackedState) → (base n : ℕ) →
  B.Vec Packed.PackedState n
ps G base n = Vec.tabulate (λ i → G (base + B.finToNat i))

ss : (G : ℕ → Packed.PackedState) → (base n : ℕ) →
  B.Vec (State six) n
ss G base n = vec-map Packed.decode (ps G base n)

resolver : (ℕ → Packed.PackedState) → ℕ → Maybe Packed.PackedState
resolver G j = just (G j)

embed : ∀ {n} → ℕ → B.Fin n → ℕ
embed base i = base + B.finToNat i

resolver-compatible : ∀ G → Shared.Compatible (resolver G) G
resolver-compatible G j .(G j) refl = refl

decoded-lookup : ∀ G base n (i : B.Fin n) →
  Packed.decode (G (base + B.finToNat i)) ≡
  B.lookupVec (ss G base n) i
decoded-lookup G base n i = sym
  (trans (lookup-map Packed.decode (ps G base n) i)
    (cong Packed.decode
      (Vec.lookup-tabulate (λ j → G (base + B.finToNat j)) i)))

checkRows : ∀ G base n →
  B.Vec (D.DirectedCertificate ℕ (Coord six)) n → Bool
checkRows G base n cs =
  Shared.checkRows (resolver G) (embed base) (ss G base n) cs

abstract
  partial : ∀ G base n (cs : B.Vec (D.DirectedCertificate ℕ (Coord six)) n) →
    checkRows G base n cs ≡ true →
    A.Partial G (M.rows base n (ps G base n))
  partial G base n cs accepted =
    A.rows base (ps G base n) G
      (Shared.steps (resolver G) (embed base) (ss G base n) cs accepted G
        (resolver-compatible G) (decoded-lookup G base n))
