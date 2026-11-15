{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted; literal subtree checks, full cited-map premise remains open.
module Tests.InlineLowerPrefixes6.Closed where
open import Prelude
open import Game.Core using (white; Guarantees)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (lowerGoal)
import Othello.Fast6 as Fast
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.InlinePrefix6 as Prefix
import Othello.DirectSymmetry6 as Direct
import Othello.SpliceLine6 as Line
import Tests.InlineLowerPrefixes6.Data as Data
module Check = Prefix.Checking white (lowerGoal 4) Direct.lowerTransport6
abstract
  lower0 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p0
  lower0 = Check.guarantee Data.L 6873046 Line.p0 0 Data.c0 refl
abstract
  lower1 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p1
  lower1 = Check.guarantee Data.L 6873046 Line.p1 0 Data.c1 refl
abstract
  lower2 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p2
  lower2 = Check.guarantee Data.L 6873045 Line.p2 5 Data.c2 refl
abstract
  lower3 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p3
  lower3 = Check.guarantee Data.L 6873045 Line.p3 5 Data.c3 refl
abstract
  lower4 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p4
  lower4 = Check.guarantee Data.L 6873045 Line.p4 5 Data.c4 refl
abstract
  lower5 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p5
  lower5 = Check.guarantee Data.L 5160344 Line.p5 1 Data.c5 refl
abstract
  lower6 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p6
  lower6 = Check.guarantee Data.L 5160344 Line.p6 1 Data.c6 refl
abstract
  lower7 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p7
  lower7 = Check.guarantee Data.L 5160344 Line.p7 1 Data.c7 refl
abstract
  lower8 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p8
  lower8 = Check.guarantee Data.L 5160344 Line.p8 1 Data.c8 refl
abstract
  lower9 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p9
  lower9 = Check.guarantee Data.L 4140150 Line.p9 5 Data.c9 refl
abstract
  lower10 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p10
  lower10 = Check.guarantee Data.L 4140150 Line.p10 5 Data.c10 refl
abstract
  lower11 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p11
  lower11 = Check.guarantee Data.L 4135823 Line.p11 3 Data.c11 refl
abstract
  lower12 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p12
  lower12 = Check.guarantee Data.L 4135823 Line.p12 3 Data.c12 refl
abstract
  lower13 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p13
  lower13 = Check.guarantee Data.L 4121923 Line.p13 7 Data.c13 refl
abstract
  lower14 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p14
  lower14 = Check.guarantee Data.L 4121923 Line.p14 7 Data.c14 refl
abstract
  lower15 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p15
  lower15 = Check.guarantee Data.L 4119184 Line.p15 7 Data.c15 refl
abstract
  lower16 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p16
  lower16 = Check.guarantee Data.L 4119184 Line.p16 7 Data.c16 refl
abstract
  lower17 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p17
  lower17 = Check.guarantee Data.L 4119184 Line.p17 7 Data.c17 refl
abstract
  lower18 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p18
  lower18 = Check.guarantee Data.L 4119184 Line.p18 7 Data.c18 refl
abstract
  lower19 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p19
  lower19 = Check.guarantee Data.L 4118836 Line.p19 3 Data.c19 refl
abstract
  lower20 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 white (lowerGoal 4) Line.p20
  lower20 = Check.guarantee Data.L 4118820 Line.p20 2 Data.c20 refl
