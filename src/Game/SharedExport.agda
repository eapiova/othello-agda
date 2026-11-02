{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. A Boolean coverage check transfers proved facts to a literal
-- export trie without comparing two entire computed tries by equality.
module Game.SharedExport where

open import Game.Core
open import Game.Shared

private
  left : ∀ a b → a ∧ b ≡ true → a ≡ true
  left true b e = refl
  left false b ()

  right : ∀ a b → a ∧ b ≡ true → b ≡ true
  right true b e = e
  right false b ()

coveredValue : ∀ {S} → Keyed S → Trie S → Maybe S → Bool
coveredValue k source nothing = true
coveredValue k source (just s) = knownIn k source s

covered : ∀ {S} → Keyed S → Trie S → Trie S → Bool
covered k source tip = true
covered k source (node m l r) =
  coveredValue k source m ∧ (covered k source l ∧ covered k source r)

private
  value-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal source m →
    AllT (Proven g p goal) source → coveredValue k source m ≡ true →
    AllM (Proven g p goal) m
  value-sound k g p goal source nothing inv e = tt
  value-sound k g p goal source (just s) inv e =
    knownIn-sound k g p goal source s inv e

covered-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal source target →
  AllT (Proven g p goal) source → covered k source target ≡ true →
  AllT (Proven g p goal) target
covered-sound k g p goal source tip inv e = tt
covered-sound k g p goal source (node m l r) inv e =
  value-sound k g p goal source m inv
    (left (coveredValue k source m) rest e) ,
  (covered-sound k g p goal source l inv
    (left (covered k source l) (covered k source r) parts) ,
   covered-sound k g p goal source r inv
    (right (covered k source l) (covered k source r) parts))
  where
  rest = covered k source l ∧ covered k source r
  parts = right (coveredValue k source m) rest e
