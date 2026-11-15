{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.Certificate where

open import Game.Core

data Certificate : Set where
  leaf : Certificate
  choice : ℕ → Certificate → Certificate
  fork : List Certificate → Certificate
  pass : Certificate → Certificate

-- The checker examines only the game, goal, and certificate structure.
-- In particular it never trusts a certificate-supplied state or score.
mutual
  check : ∀ {S} → Game S → Player → (S → Bool) → S → Certificate → Bool
  check g p goal s leaf with next g s
  ... | [] = goal s
  ... | x ∷ xs = false
  check g p goal s (choice i c) with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | false = false
  ... | x ∷ xs | true with lookup (x ∷ xs) i
  ...   | nothing = false
  ...   | just t = check g p goal t c
  check g p goal s (fork cs) with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | true = false
  ... | x ∷ xs | false = checkForest g p goal (x ∷ xs) cs
  check g p goal s (pass c) with next g s | forcedPass g s
  ... | x ∷ [] | true = check g p goal x c
  ... | [] | b = false
  ... | x ∷ [] | false = false
  ... | x ∷ y ∷ xs | b = false

  checkForest : ∀ {S} → Game S → Player → (S → Bool) → List S → List Certificate → Bool
  checkForest g p goal [] [] = true
  checkForest g p goal [] (c ∷ cs) = false
  checkForest g p goal (s ∷ ss) [] = false
  checkForest g p goal (s ∷ ss) (c ∷ cs) =
    check g p goal s c ∧ checkForest g p goal ss cs

-- A decision tree evaluated on a chronological history. Future decisions
-- can differ even when two branches reconverge at the same game state.
advance : Certificate → ℕ → Certificate
advance leaf i = leaf
advance (choice n c) i = c
advance (pass c) i = c
advance (fork cs) i = fromMaybe leaf (lookup cs i)

recommend : Certificate → ℕ
recommend (choice i c) = i
recommend leaf = zero
recommend (fork cs) = zero
recommend (pass c) = zero

certificateStrategy : ∀ {S} → Certificate → Strategy S
certificateStrategy c [] s = recommend c
certificateStrategy c (i ∷ h) s = certificateStrategy (advance c i) h s

choice-shift : ∀ {S} i n c → shift i (certificateStrategy {S} (choice n c)) ≡ certificateStrategy c
choice-shift i n c = refl

pass-shift : ∀ {S} i c → shift i (certificateStrategy {S} (pass c)) ≡ certificateStrategy c
pass-shift i c = refl

fork-shift : ∀ {S} {cs i c} → lookup cs i ≡ just c →
  shift i (certificateStrategy {S} (fork cs)) ≡ certificateStrategy c
fork-shift {cs = cs} {i} e =
  cong certificateStrategy (cong (fromMaybe leaf) e)
