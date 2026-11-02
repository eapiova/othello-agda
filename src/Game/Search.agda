{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.Search where

open import Game.Core
open import Game.Certificate

-- Fuel is a bound on visited plies, including compulsory passes. Exhaustion
-- fails even at a terminal state. Both list folds stop at the first decision.
record Outcome {S : Set} (g : Game S) (p : Player)
               (goal : S → Bool) (s : S) : Set where
  constructor outcome
  field
    succeeds : Bool
    evidence : Certificate
    evidenceOK : succeeds ≡ true → check g p goal s evidence ≡ true
open Outcome public

record ForestOutcome {S : Set} (g : Game S) (p : Player)
                     (goal : S → Bool) (ss : List S) : Set where
  constructor forestOutcome
  field
    allSucceed : Bool
    evidences : List Certificate
    evidencesOK : allSucceed ≡ true → checkForest g p goal ss evidences ≡ true
open ForestOutcome

record Pick {S : Set} (g : Game S) (p : Player)
            (goal : S → Bool) (ss : List S) : Set where
  constructor pick
  field
    pickedIndex : ℕ
    pickedState : S
    pickedEvidence : Certificate
    pickedLookup : lookup ss pickedIndex ≡ just pickedState
    pickedOK : check g p goal pickedState pickedEvidence ≡ true
open Pick

private
  terminalOutcome : ∀ {S} {g : Game S} {p goal s} →
    next g s ≡ [] → Outcome g p goal s
  terminalOutcome {g = g} {p} {goal} {s} en =
    outcome (goal s) leaf valid
    where
    valid : goal s ≡ true → check g p goal s leaf ≡ true
    valid e rewrite en = e

  passOutcome : ∀ {S} {g : Game S} {p goal s x} →
    next g s ≡ x ∷ [] → forcedPass g s ≡ true →
    Outcome g p goal x → Outcome g p goal s
  passOutcome {g = g} {p} {goal} {s} en ep r =
    outcome (succeeds r) (pass (evidence r)) valid
    where
    valid : succeeds r ≡ true → check g p goal s (pass (evidence r)) ≡ true
    valid e rewrite en | ep = evidenceOK r e

  ownOutcome : ∀ {S} {g : Game S} {p goal s x xs} →
    next g s ≡ x ∷ xs → samePlayer (turn g s) p ≡ true →
    Maybe (Pick g p goal (x ∷ xs)) → Outcome g p goal s
  ownOutcome en eo nothing = outcome false leaf (λ ())
  ownOutcome {g = g} {p} {goal} {s} en eo (just q) =
    outcome true (choice (pickedIndex q) (pickedEvidence q)) valid
    where
    valid : true ≡ true →
      check g p goal s (choice (pickedIndex q) (pickedEvidence q)) ≡ true
    valid e rewrite en | eo | pickedLookup q = pickedOK q

  opposingOutcome : ∀ {S} {g : Game S} {p goal s x xs} →
    next g s ≡ x ∷ xs → samePlayer (turn g s) p ≡ false →
    ForestOutcome g p goal (x ∷ xs) → Outcome g p goal s
  opposingOutcome {g = g} {p} {goal} {s} en eo r =
    outcome (allSucceed r) (fork (evidences r)) valid
    where
    valid : allSucceed r ≡ true → check g p goal s (fork (evidences r)) ≡ true
    valid e rewrite en | eo = evidencesOK r e

  prependForest : ∀ {S} {g : Game S} {p goal s ss} →
    (r : Outcome g p goal s) → succeeds r ≡ true →
    ForestOutcome g p goal ss → ForestOutcome g p goal (s ∷ ss)
  prependForest {g = g} {p} {goal} {s} {ss} r er rs =
    forestOutcome (allSucceed rs) (evidence r ∷ evidences rs) valid
    where
    valid : allSucceed rs ≡ true →
      checkForest g p goal (s ∷ ss) (evidence r ∷ evidences rs) ≡ true
    valid e rewrite evidenceOK r er = evidencesOK rs e

mutual
  search : ∀ {S} → ℕ → (g : Game S) → (p : Player) →
    (goal : S → Bool) → (s : S) → Outcome g p goal s
  search zero g p goal s = outcome false leaf (λ ())
  search (suc fuel) g p goal s with next g s in en
  ... | [] = terminalOutcome en
  ... | x ∷ [] with forcedPass g s in ep
  ...   | true = passOutcome en ep (search fuel g p goal x)
  ...   | false = searchNode fuel g p goal s x [] en
  search (suc fuel) g p goal s | x ∷ y ∷ xs =
    searchNode fuel g p goal s x (y ∷ xs) en

  searchNode : ∀ {S} → ℕ → (g : Game S) → (p : Player) →
    (goal : S → Bool) → (s x : S) → (xs : List S) →
    next g s ≡ x ∷ xs → Outcome g p goal s
  searchNode fuel g p goal s x xs en with samePlayer (turn g s) p in eo
  ... | true = ownOutcome en eo (searchAny fuel g p goal (x ∷ xs))
  ... | false = opposingOutcome en eo (searchAll fuel g p goal (x ∷ xs))

  searchAny : ∀ {S} → ℕ → (g : Game S) → (p : Player) →
    (goal : S → Bool) → (ss : List S) → Maybe (Pick g p goal ss)
  searchAny fuel g p goal [] = nothing
  searchAny fuel g p goal (s ∷ ss) with search fuel g p goal s
  ... | r with succeeds r in er
  ...   | true = just (pick zero s (evidence r) refl (evidenceOK r er))
  ...   | false with searchAny fuel g p goal ss
  ...     | nothing = nothing
  ...     | just q = just (pick (suc (pickedIndex q)) (pickedState q)
                          (pickedEvidence q) (pickedLookup q) (pickedOK q))

  searchAll : ∀ {S} → ℕ → (g : Game S) → (p : Player) →
    (goal : S → Bool) → (ss : List S) → ForestOutcome g p goal ss
  searchAll fuel g p goal [] = forestOutcome true [] (λ e → refl)
  searchAll fuel g p goal (s ∷ ss) with search fuel g p goal s
  ... | r with succeeds r in er
  ...   | false = forestOutcome false [] (λ ())
  ...   | true = prependForest r er (searchAll fuel g p goal ss)

forces : ∀ {S} → ℕ → Game S → Player → (S → Bool) → S → Bool
forces fuel g p goal s = succeeds (search fuel g p goal s)

witness : ∀ {S} → ℕ → Game S → Player → (S → Bool) → S → Certificate
witness fuel g p goal s = evidence (search fuel g p goal s)

forces-sound : ∀ {S} (fuel : ℕ) (g : Game S) (p : Player)
  (goal : S → Bool) (s : S) → forces fuel g p goal s ≡ true →
  check g p goal s (witness fuel g p goal s) ≡ true
forces-sound fuel g p goal s = evidenceOK (search fuel g p goal s)
