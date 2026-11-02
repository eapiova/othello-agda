{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.BooleanSearch where

open import Game.Core
import Game.Search as Search
open import Game.Certificate using (check)

-- The evaluator carries only Booleans. Singleton compulsory passes consume
-- fuel just like ordinary moves, and zero fuel fails even at a terminal.
mutual
  forcesB : ∀ {S} → ℕ → Game S → Player → (S → Bool) → S → Bool
  forcesB zero g p goal s = false
  forcesB (suc fuel) g p goal s with next g s
  ... | [] = goal s
  ... | x ∷ [] with forcedPass g s
  ...   | true = forcesB fuel g p goal x
  ...   | false = nodeB fuel g p goal s (x ∷ [])
  forcesB (suc fuel) g p goal s | x ∷ y ∷ xs =
    nodeB fuel g p goal s (x ∷ y ∷ xs)

  nodeB : ∀ {S} → ℕ → Game S → Player → (S → Bool) → S → List S → Bool
  nodeB fuel g p goal s ss with samePlayer (turn g s) p
  ... | true = anyB fuel g p goal ss
  ... | false = allB fuel g p goal ss

  anyB : ∀ {S} → ℕ → Game S → Player → (S → Bool) → List S → Bool
  anyB fuel g p goal [] = false
  anyB fuel g p goal (s ∷ ss) with forcesB fuel g p goal s
  ... | true = true
  ... | false = anyB fuel g p goal ss

  allB : ∀ {S} → ℕ → Game S → Player → (S → Bool) → List S → Bool
  allB fuel g p goal [] = true
  allB fuel g p goal (s ∷ ss) with forcesB fuel g p goal s
  ... | false = false
  ... | true = allB fuel g p goal ss

private
  pickedB : ∀ {S} {g : Game S} {p goal ss} →
    Maybe (Search.Pick g p goal ss) → Bool
  pickedB nothing = false
  pickedB (just q) = true

mutual
  forcesB-eq : ∀ {S} (fuel : ℕ) (g : Game S) (p : Player)
    (goal : S → Bool) (s : S) → forcesB fuel g p goal s ≡ Search.forces fuel g p goal s
  forcesB-eq zero g p goal s = refl
  forcesB-eq (suc fuel) g p goal s with next g s in en
  ... | [] = refl
  ... | x ∷ [] with forcedPass g s in ep
  ...   | true = forcesB-eq fuel g p goal x
  ...   | false = nodeB-eq fuel g p goal s x [] en
  forcesB-eq (suc fuel) g p goal s | x ∷ y ∷ xs =
    nodeB-eq fuel g p goal s x (y ∷ xs) en

  nodeB-eq : ∀ {S} (fuel : ℕ) (g : Game S) (p : Player)
    (goal : S → Bool) (s x : S) (xs : List S)
    (en : next g s ≡ x ∷ xs) →
    nodeB fuel g p goal s (x ∷ xs) ≡
    Search.succeeds (Search.searchNode fuel g p goal s x xs en)
  nodeB-eq fuel g p goal s x xs en with samePlayer (turn g s) p in eo
  ... | false = allB-eq fuel g p goal (x ∷ xs)
  ... | true rewrite anyB-eq fuel g p goal (x ∷ xs)
    with Search.searchAny fuel g p goal (x ∷ xs)
  ...   | nothing = refl
  ...   | just q = refl

  anyB-eq : ∀ {S} (fuel : ℕ) (g : Game S) (p : Player)
    (goal : S → Bool) (ss : List S) →
    anyB fuel g p goal ss ≡ pickedB (Search.searchAny fuel g p goal ss)
  anyB-eq fuel g p goal [] = refl
  anyB-eq fuel g p goal (s ∷ ss) rewrite forcesB-eq fuel g p goal s
    with Search.search fuel g p goal s
  ... | r with Search.succeeds r in er
  ...   | true = refl
  ...   | false rewrite anyB-eq fuel g p goal ss
    with Search.searchAny fuel g p goal ss
  ...     | nothing = refl
  ...     | just q = refl

  allB-eq : ∀ {S} (fuel : ℕ) (g : Game S) (p : Player)
    (goal : S → Bool) (ss : List S) →
    allB fuel g p goal ss ≡ Search.ForestOutcome.allSucceed (Search.searchAll fuel g p goal ss)
  allB-eq fuel g p goal [] = refl
  allB-eq fuel g p goal (s ∷ ss) rewrite forcesB-eq fuel g p goal s
    with Search.search fuel g p goal s
  ... | r with Search.succeeds r in er
  ...   | false = refl
  ...   | true = allB-eq fuel g p goal ss

-- The witness is constructed only when a proof uses it. Acceptance evaluates
-- the plain Boolean search, and equality transports it to the existing theorem.
forcesB-sound : ∀ {S} (fuel : ℕ) (g : Game S) (p : Player)
  (goal : S → Bool) (s : S) → forcesB fuel g p goal s ≡ true →
  check g p goal s (Search.witness fuel g p goal s) ≡ true
forcesB-sound fuel g p goal s e = Search.forces-sound fuel g p goal s
  (trans (sym (forcesB-eq fuel g p goal s)) e)
