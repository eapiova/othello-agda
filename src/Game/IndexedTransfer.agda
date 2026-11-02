{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Pointwise agreement transports Boolean indexed checking.
module Game.IndexedTransfer where

open import Prelude
open import Game.Core
open import Game.Composite using (StateEquality; equal)
open import Game.Symmetry using (CertificateTransport; act; acceptedTag)
import Game.Indexed as I
import Game.BooleanSearch as F
import Game.Transfer as T

mutual
  forces-agree : ∀ {S} (fuel : ℕ) (g h : Game S) → T.Agreement g h →
    ∀ p goal s → F.forcesB fuel g p goal s ≡ F.forcesB fuel h p goal s
  forces-agree zero g h agreement p goal s = refl
  forces-agree (suc fuel) g h agreement p goal s
    rewrite T.next-agrees agreement s with next h s
  ... | [] = refl
  ... | x ∷ [] rewrite T.pass-agrees agreement s with forcedPass h s
  ...   | true = forces-agree fuel g h agreement p goal x
  ...   | false = node-agree fuel g h agreement p goal s (x ∷ [])
  forces-agree (suc fuel) g h agreement p goal s | x ∷ y ∷ xs =
    node-agree fuel g h agreement p goal s (x ∷ y ∷ xs)

  node-agree : ∀ {S} (fuel : ℕ) (g h : Game S) → T.Agreement g h →
    ∀ p goal s ss → F.nodeB fuel g p goal s ss ≡ F.nodeB fuel h p goal s ss
  node-agree fuel g h agreement p goal s ss
    rewrite T.turn-agrees agreement s with samePlayer (turn h s) p
  ... | true = any-agree fuel g h agreement p goal ss
  ... | false = all-agree fuel g h agreement p goal ss

  any-agree : ∀ {S} (fuel : ℕ) (g h : Game S) → T.Agreement g h →
    ∀ p goal ss → F.anyB fuel g p goal ss ≡ F.anyB fuel h p goal ss
  any-agree fuel g h agreement p goal [] = refl
  any-agree fuel g h agreement p goal (s ∷ ss)
    rewrite forces-agree fuel g h agreement p goal s with F.forcesB fuel h p goal s
  ... | true = refl
  ... | false = any-agree fuel g h agreement p goal ss

  all-agree : ∀ {S} (fuel : ℕ) (g h : Game S) → T.Agreement g h →
    ∀ p goal ss → F.allB fuel g p goal ss ≡ F.allB fuel h p goal ss
  all-agree fuel g h agreement p goal [] = refl
  all-agree fuel g h agreement p goal (s ∷ ss)
    rewrite forces-agree fuel g h agreement p goal s with F.forcesB fuel h p goal s
  ... | false = refl
  ... | true = all-agree fuel g h agreement p goal ss

module Comparing {Key S : Set} (order : I.Order Key) (equality : StateEquality S)
  (g h : Game S) (p : Player) (goal : S → Bool)
  (leftLaws : CertificateTransport g p goal) (rightLaws : CertificateTransport h p goal)
  (agreement : T.Agreement g h)
  (acts-agree : ∀ tag s → act leftLaws tag s ≡ act rightLaws tag s)
  (tags-agree : ∀ tag → acceptedTag leftLaws tag ≡ acceptedTag rightLaws tag) where

  module Left = I.Checker order equality g p goal leftLaws
  module Right = I.Checker order equality h p goal rightLaws

  mutual
    local-agrees : ∀ L owner s c → Left.checkLocal L owner s c ≡ Right.checkLocal L owner s c
    local-agrees L owner s I.indexedLeaf rewrite T.next-agrees agreement s with next h s
    ... | [] = refl
    ... | x ∷ xs = refl
    local-agrees L owner s (I.indexedSolve fuel) = forces-agree fuel g h agreement p goal s
    local-agrees L owner s (I.indexedChoice i c)
      rewrite T.next-agrees agreement s | T.turn-agrees agreement s
      with next h s | samePlayer (turn h s) p
    ... | [] | own = refl
    ... | x ∷ xs | false = refl
    ... | x ∷ xs | true with lookup (x ∷ xs) i
    ...   | nothing = refl
    ...   | just t = local-agrees L owner t c
    local-agrees L owner s (I.indexedFork cs)
      rewrite T.next-agrees agreement s | T.turn-agrees agreement s
      with next h s | samePlayer (turn h s) p
    ... | [] | own = refl
    ... | x ∷ xs | true = refl
    ... | x ∷ xs | false = forest-agrees L owner (x ∷ xs) cs
    local-agrees L owner s (I.indexedPass c)
      rewrite T.next-agrees agreement s | T.pass-agrees agreement s
      with next h s | forcedPass h s
    ... | [] | b = refl
    ... | x ∷ [] | false = refl
    ... | x ∷ y ∷ xs | b = refl
    ... | x ∷ [] | true = local-agrees L owner x c
    local-agrees L owner s (I.cite j) with I.beforeB order j owner
    ... | false = refl
    ... | true with L j
    ...   | nothing = refl
    ...   | just u = refl
    local-agrees L owner s (I.citeBy tag j) with I.beforeB order j owner
    ... | false = refl
    ... | true rewrite tags-agree tag with acceptedTag rightLaws tag
    ...   | false = refl
    ...   | true with L j
    ...     | nothing = refl
    ...     | just u = cong (λ t → equal equality t u) (acts-agree tag s)

    forest-agrees : ∀ L owner ss cs →
      Left.checkLocalForest L owner ss cs ≡ Right.checkLocalForest L owner ss cs
    forest-agrees L owner [] [] = refl
    forest-agrees L owner [] (_ ∷ _) = refl
    forest-agrees L owner (_ ∷ _) [] = refl
    forest-agrees L owner (s ∷ ss) (c ∷ cs)
      rewrite local-agrees L owner s c | forest-agrees L owner ss cs = refl
