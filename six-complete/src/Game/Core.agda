{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.Core where

open import Prelude public
open import Game.Player public

record Game (S : Set) : Set where
  field
    turn : S → Player
    next : S → List S
    forcedPass : S → Bool
open Game public

-- Histories are chronological lists of actual successor indices. Strategies
-- may depend on both the entire history and the current position.
Strategy : Set → Set
Strategy S = List ℕ → S → ℕ

shift : ∀ {S} → ℕ → Strategy S → Strategy S
shift i σ h s = σ (i ∷ h) s

lookup : ∀ {A : Set} → List A → ℕ → Maybe A
lookup [] i = nothing
lookup (x ∷ xs) zero = just x
lookup (x ∷ xs) (suc i) = lookup xs i

record Selection (S : Set) : Set where
  constructor selection
  field
    index : ℕ
    selected : S
open Selection public

-- The fallback is the head of the original list, even when a large index
-- has traversed past several elements.
resolved : ∀ {S} → S → ℕ → Maybe S → Selection S
resolved x i (just y) = selection i y
resolved x i nothing = selection zero x

resolve : ∀ {S} (x : S) (xs : List S) → ℕ → Selection S
resolve x xs i = resolved x i (lookup (x ∷ xs) i)

resolve-inRange : ∀ {S} {x y : S} {xs i} → lookup (x ∷ xs) i ≡ just y →
                  resolve x xs i ≡ selection i y
resolve-inRange {x = x} {i = i} e = cong (resolved x i) e

resolve-index : ∀ {S} {x y : S} {xs i} → lookup (x ∷ xs) i ≡ just y →
                index (resolve x xs i) ≡ i
resolve-index {x = x} {xs = xs} {i = i} e = cong index (resolve-inRange {x = x} {xs = xs} {i = i} e)

resolve-selected : ∀ {S} {x y : S} {xs i} → lookup (x ∷ xs) i ≡ just y →
                   selected (resolve x xs i) ≡ y
resolve-selected {x = x} {xs = xs} {i = i} e = cong selected (resolve-inRange {x = x} {xs = xs} {i = i} e)

resolve-valid : ∀ {S} (x : S) (xs : List S) (i : ℕ) →
  lookup (x ∷ xs) (index (resolve x xs i)) ≡ just (selected (resolve x xs i))
resolve-valid x xs i with lookup (x ∷ xs) i in e
... | just y = e
... | nothing = refl

decision : ∀ {S} → Game S → Player → Strategy S → Strategy S → S → ℕ
chooseDecision : Bool → ℕ → ℕ → ℕ
chooseDecision true own opposing = own
chooseDecision false own opposing = opposing

decision g p σ τ s = chooseDecision (samePlayer (turn g s) p) (σ [] s) (τ [] s)

-- At each step, strategies are restricted to the observed prefix. This is
-- equivalent to passing the growing chronological history explicitly.
data CompletedPlay {S : Set} (g : Game S) (p : Player)
                   (σ τ : Strategy S) (s : S) : S → Set where
  done : next g s ≡ [] → CompletedPlay g p σ τ s s
  step : ∀ {x xs t} (legal : next g s ≡ x ∷ xs) →
    let move = resolve x xs (decision g p σ τ s) in
    CompletedPlay g p (shift (index move) σ) (shift (index move) τ)
                     (selected move) t →
    CompletedPlay g p σ τ s t

terminal : ∀ {S} {g : Game S} {p σ τ s t} →
           CompletedPlay g p σ τ s t → next g t ≡ []
terminal (done e) = e
terminal (step e play) = terminal play

history : ∀ {S} {g : Game S} {p σ τ s t} →
          CompletedPlay g p σ τ s t → List ℕ
history (done e) = []
history {g = g} {p} {σ} {τ} {s} (step {x} {xs} e play) =
  index (resolve x xs (decision g p σ τ s)) ∷ history play

-- Two completed plays against the same strategies have the same endpoint.
play-deterministic : ∀ {S} {g : Game S} {p σ τ s t u} →
  CompletedPlay g p σ τ s t → CompletedPlay g p σ τ s u → t ≡ u
play-deterministic (done e) (done f) = refl
play-deterministic (done e) (step f q) with trans (sym e) f
... | ()
play-deterministic (step e q) (done f) with trans (sym e) f
... | ()
play-deterministic (step e q) (step f r) with trans (sym e) f
... | refl = play-deterministic q r

record Guarantees {S : Set} (g : Game S) (p : Player)
                  (goal : S → Bool) (s : S) : Set where
  constructor guarantee
  field
    forcing : Strategy S
    responds : (opposing : Strategy S) →
      Σ S (λ t → CompletedPlay g p forcing opposing s t × (goal t ≡ true))
open Guarantees public

WhiteGuarantees : ∀ {S} → Game S → (S → Bool) → S → Set
WhiteGuarantees g = Guarantees g white

BlackGuarantees : ∀ {S} → Game S → (S → Bool) → S → Set
BlackGuarantees g = Guarantees g black

-- A convenient form of step for a strategy index certified to be in range.
stepAt : ∀ {S} {g : Game S} {p σ τ s x xs i y t} →
  next g s ≡ x ∷ xs → decision g p σ τ s ≡ i →
  lookup (x ∷ xs) i ≡ just y →
  CompletedPlay g p (shift i σ) (shift i τ) y t →
  CompletedPlay g p σ τ s t
stepAt {g = g} {p} {σ} {τ} {x = x} {xs} {t = t} en ed el q =
  step en (subst (λ m → CompletedPlay g p (shift (index m) σ) (shift (index m) τ)
                                       (selected m) t)
                 (sym (trans (cong (resolve x xs) ed) (resolve-inRange el))) q)

-- A compulsory singleton successor is followed regardless of either
-- strategy's natural-number recommendation.
stepOnly : ∀ {S} {g : Game S} {p σ τ s x t} →
  next g s ≡ x ∷ [] →
  CompletedPlay g p (shift zero σ) (shift zero τ) x t →
  CompletedPlay g p σ τ s t
stepOnly {g = g} {p} {σ} {τ} {s} {x} {t} en q =
  step en (subst (λ m → CompletedPlay g p (shift (index m) σ) (shift (index m) τ)
                                       (selected m) t)
                 (sym (only (decision g p σ τ s))) q)
  where
  only : (i : ℕ) → resolve x [] i ≡ selection zero x
  only zero = refl
  only (suc i) = refl

decision-own : ∀ {S} {g : Game S} {p σ τ s} →
  samePlayer (turn g s) p ≡ true → decision g p σ τ s ≡ σ [] s
decision-own {g = g} {p} {σ} {τ} {s} e = cong (λ b → chooseDecision b (σ [] s) (τ [] s)) e

decision-opponent : ∀ {S} {g : Game S} {p σ τ s} →
  samePlayer (turn g s) p ≡ false → decision g p σ τ s ≡ τ [] s
decision-opponent {g = g} {p} {σ} {τ} {s} e = cong (λ b → chooseDecision b (σ [] s) (τ [] s)) e

-- The analogous form accepts an arbitrary recommendation and records its
-- normalized actual index, including the fallback case.
stepFrom : ∀ {S} {g : Game S} {p σ τ s x xs i t} →
  next g s ≡ x ∷ xs → decision g p σ τ s ≡ i →
  let move = resolve x xs i in
  CompletedPlay g p (shift (index move) σ) (shift (index move) τ) (selected move) t →
  CompletedPlay g p σ τ s t
stepFrom {g = g} {p} {σ} {τ} {x = x} {xs} {t = t} en ed q =
  step en (subst (λ m → CompletedPlay g p (shift (index m) σ) (shift (index m) τ)
                                       (selected m) t)
                 (sym (cong (resolve x xs) ed)) q)

-- Exchanging the forcing and opposing roles does not change actual moves.
decision-swap : ∀ {S} (g : Game S) (p : Player) (σ τ : Strategy S) (s : S) →
  decision g p σ τ s ≡ decision g (other p) τ σ s
decision-swap g p σ τ s with turn g s | p
... | black | black = refl
... | black | white = refl
... | white | black = refl
... | white | white = refl

swapPlay : ∀ {S} {g : Game S} {p σ τ s t} →
  CompletedPlay g p σ τ s t → CompletedPlay g (other p) τ σ s t
swapPlay (done e) = done e
swapPlay {g = g} {p} {σ} {τ} {s} {t} (step {x} {xs} en q) =
  step en (subst (λ m → CompletedPlay g (other p) (shift (index m) τ) (shift (index m) σ)
                                                (selected m) t)
                 (cong (resolve x xs) (decision-swap g p σ τ s)) (swapPlay q))
