{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Reuse checked ordinary rows without a body map in the result.
module Othello.StepFromNatAssembly6 where

open import Prelude
open import Game.Core using (Game; Player)
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; six)
open import Othello.Encode6 using (stateEquality6)
import Game.Indexed as I
import Game.NatMap as M
import Game.StepAssembly as Step
import Othello.NatAssembly6 as Nat

module Assembly (g : Game (State six)) (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport g p goal) where

  module Old = Nat.Assembly g p goal laws
  module New = Step.Assembly g p goal
  module Rows = New.Ordinary stateEquality6 laws

  from-partial : (G : ℕ → State six) (C : ℕ → I.IndexedCertificate ℕ)
    (table : M.Map (State six)) → Old.Partial G C table → New.Partial G table
  from-partial G C table accepted key hit =
    Rows.from-row G key (accepted key hit)
