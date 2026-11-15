{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Large numeric offsets with a symbolic row index.
module Tests.NatMapRoute where

open import Prelude
open import Agda.Builtin.Nat using (_<_)
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatMapRoute as R

values : B.Vec Bool 2
values = B.cons false (B.cons true B.nil)

local : M.Map Bool
local = M.rows 6873000 2 values

full : M.Map Bool
full = M.branch 6873000 M.absent (M.branch 6873002 local M.absent)

path : R.Route full 6873000 2 values
path = R.right refl (R.left refl R.here)

symbolic : ∀ G → Laws.Compatible full G → Laws.Aligned local G
symbolic G agree = R.aligned G path agree

-- This is a closed map compatibility theorem, not an assumed correspondence.
closed : Laws.Compatible local (Laws.totalize full false)
closed = R.compatible (Laws.totalize full false) path
  (Laws.self-compatible full false)

wrong-left-guard : (6873000 < 6873000) ≡ false
wrong-left-guard = refl

data Empty : Set where

-- A hidden or incorrectly routed row cannot provide a route certificate.
hidden-impossible : R.Route (M.branch 0 local M.absent) 6873000 2 values → Empty
hidden-impossible (R.left () path)
hidden-impossible (R.right bound ())
