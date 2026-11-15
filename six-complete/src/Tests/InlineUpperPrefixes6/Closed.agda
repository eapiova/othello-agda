{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted; literal subtree checks, full cited-map premise remains open.
module Tests.InlineUpperPrefixes6.Closed where
open import Prelude
open import Game.Core using (black; Guarantees)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (upperGoal)
import Othello.Fast6 as Fast
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.InlinePrefix6 as Prefix
import Othello.DirectSymmetry6 as Direct
import Othello.SpliceLine6 as Line
import Tests.InlineUpperPrefixes6.Data as Data
module Check = Prefix.Checking black (upperGoal 4) Direct.upperTransport6
abstract
  upper0 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p0
  upper0 = Check.guarantee Data.L 6530010 Line.p0 0 Data.c0 refl
abstract
  upper1 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p1
  upper1 = Check.guarantee Data.L 6530010 Line.p1 0 Data.c1 refl
abstract
  upper2 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p2
  upper2 = Check.guarantee Data.L 6530009 Line.p2 5 Data.c2 refl
abstract
  upper3 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p3
  upper3 = Check.guarantee Data.L 6530009 Line.p3 5 Data.c3 refl
abstract
  upper4 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p4
  upper4 = Check.guarantee Data.L 6530009 Line.p4 5 Data.c4 refl
abstract
  upper5 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p5
  upper5 = Check.guarantee Data.L 6530009 Line.p5 5 Data.c5 refl
abstract
  upper6 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p6
  upper6 = Check.guarantee Data.L 6388998 Line.p6 0 Data.c6 refl
abstract
  upper7 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p7
  upper7 = Check.guarantee Data.L 6388998 Line.p7 0 Data.c7 refl
abstract
  upper8 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p8
  upper8 = Check.guarantee Data.L 5473883 Line.p8 0 Data.c8 refl
abstract
  upper9 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p9
  upper9 = Check.guarantee Data.L 5473883 Line.p9 0 Data.c9 refl
abstract
  upper10 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p10
  upper10 = Check.guarantee Data.L 5250881 Line.p10 0 Data.c10 refl
abstract
  upper11 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p11
  upper11 = Check.guarantee Data.L 5250881 Line.p11 0 Data.c11 refl
abstract
  upper12 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p12
  upper12 = Check.guarantee Data.L 5250881 Line.p12 0 Data.c12 refl
abstract
  upper13 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p13
  upper13 = Check.guarantee Data.L 5250881 Line.p13 0 Data.c13 refl
abstract
  upper14 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p14
  upper14 = Check.guarantee Data.L 5237222 Line.p14 2 Data.c14 refl
abstract
  upper15 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p15
  upper15 = Check.guarantee Data.L 5237222 Line.p15 2 Data.c15 refl
abstract
  upper16 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p16
  upper16 = Check.guarantee Data.L 5237122 Line.p16 4 Data.c16 refl
abstract
  upper17 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p17
  upper17 = Check.guarantee Data.L 5237122 Line.p17 4 Data.c17 refl
abstract
  upper18 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p18
  upper18 = Check.guarantee Data.L 5237122 Line.p18 4 Data.c18 refl
abstract
  upper19 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p19
  upper19 = Check.guarantee Data.L 5237122 Line.p19 4 Data.c19 refl
abstract
  upper20 : (G : ℕ → Packed.PackedState) → Check.Local.V.Compatible Data.L G →
    (∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (G key))) →
    Guarantees Fast.fastGame6 black (upperGoal 4) Line.p20
  upper20 = Check.guarantee Data.L 5236348 Line.p20 2 Data.c20 refl
