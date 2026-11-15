{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Structural IDs reuse the existing indexed-checker fixture.
module Tests.Balanced where

open import Prelude
open import Game.Core using (black)
import Game.Balanced as B
import Game.Indexed as Indexed
import Tests.Indexed as Existing

-- Five heterogeneous leaves, including an empty shard, at unequal depths.
shape : B.Shape
shape = B.branch (B.branch (B.leaf 2) (B.leaf 0))
  (B.branch (B.leaf 1) (B.branch (B.leaf 3) (B.leaf 1)))

a b c d e : B.Id shape
a = B.left (B.left (B.row B.fzero))
b = B.left (B.left (B.row (B.fsuc B.fzero)))
c = B.right (B.left (B.row B.fzero))
d = B.right (B.right (B.left (B.row (B.fsuc (B.fsuc B.fzero)))))
e = B.right (B.right (B.right (B.row B.fzero)))

same-leaf-earlier : B.beforeB a b ≡ true
same-leaf-earlier = refl

across-root-earlier : B.beforeB b c ≡ true
across-root-earlier = refl

deeper-earlier : B.beforeB c d ≡ true
deeper-earlier = refl

last-branch-earlier : B.beforeB d e ≡ true
last-branch-earlier = refl

self-rejected : B.beforeB d d ≡ false
self-rejected = B.before-self d

forward-rejected : B.beforeB e a ≡ false
forward-rejected = refl

bounded-row : B.rowFromNat 3 2 ≡ just (B.row (B.fsuc (B.fsuc B.fzero)))
bounded-row = refl

row-at-bound-rejected : B.rowFromNat 3 3 ≡ nothing
row-at-bound-rejected = B.row-at-bound 3

row-above-bound-rejected : B.rowFromNat 3 17 ≡ nothing
row-above-bound-rejected = refl

empty-leaf-rejected : B.rowFromNat 0 0 ≡ nothing
empty-leaf-rejected = refl

global : B.Tree ℕ shape
global = B.join
  (B.join (B.rows (B.cons 0 (B.cons 0 B.nil))) (B.rows B.nil))
  (B.join (B.rows (B.cons 0 B.nil))
    (B.join (B.rows (B.cons 0 (B.cons 0 (B.cons 0 B.nil))))
      (B.rows (B.cons 0 B.nil))))

local : B.Tree (Maybe ℕ) shape
local = B.join
  (B.join (B.rows (B.cons (just 0) (B.cons (just 0) B.nil))) (B.rows B.nil))
  (B.join (B.rows (B.cons nothing B.nil))
    (B.join (B.rows (B.cons nothing (B.cons nothing (B.cons nothing B.nil))))
      (B.rows (B.cons nothing B.nil))))

local-compatible : B.TreeCompatible local global
local-compatible = B.join-compatible
  (B.join-compatible
    (B.rows-compatible (B.cons-compatible refl (B.cons-compatible refl B.empty-compatible)))
    (B.rows-compatible B.empty-compatible))
  (B.join-compatible
    (B.rows-compatible (B.cons-compatible tt B.empty-compatible))
    (B.join-compatible
      (B.rows-compatible
        (B.cons-compatible tt (B.cons-compatible tt (B.cons-compatible tt B.empty-compatible))))
      (B.rows-compatible (B.cons-compatible tt B.empty-compatible))))

indexed-order : Indexed.Order (B.Id shape)
indexed-order = B.order shape

all-accessible : (i : B.Id shape) → Indexed.Acc B.Before i
all-accessible = Indexed.Order.wellFounded indexed-order

module Check = Indexed.Checker indexed-order Existing.states
  Existing.toy black Existing.goal Existing.laws

compatible : Check.Compatible (B.resolve local) (B.lookup global)
compatible = B.resolver-compatible local-compatible

earlier-reference-accepted :
  Check.checkLocal (B.resolve local) b 0 (Indexed.cite a) ≡ true
earlier-reference-accepted = refl

earlier-reference-fact : Check.LocalOK (B.resolve local) b 0 (Indexed.cite a)
earlier-reference-fact = Check.checkLocal-sound (B.resolve local) b 0
  (Indexed.cite a) earlier-reference-accepted

global-reference-fact : Check.TreeOK (B.lookup global) b 0 (Indexed.cite a)
global-reference-fact = Check.lift-local compatible earlier-reference-fact

self-reference-rejected :
  Check.checkLocal (B.resolve local) a 0 (Indexed.cite a) ≡ false
self-reference-rejected = refl

forward-reference-rejected :
  Check.checkLocal (B.resolve local) a 0 (Indexed.cite b) ≡ false
forward-reference-rejected = refl

two-row-cycle-rejected :
  (Check.checkLocal (B.resolve local) a 0 (Indexed.cite b) ∧
   Check.checkLocal (B.resolve local) b 0 (Indexed.cite a)) ≡ false
two-row-cycle-rejected = refl

missing-earlier-reference-rejected :
  Check.checkLocal (B.resolve local) e 0 (Indexed.cite d) ≡ false
missing-earlier-reference-rejected = refl

lookup-deep-row : B.lookup global d ≡ 0
lookup-deep-row = refl

sparse-lookup-missing : B.resolve local d ≡ nothing
sparse-lookup-missing = refl
