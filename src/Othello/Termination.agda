{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Termination where

open import Prelude
open import Othello.Rules
open import Othello.Correctness
open import Othello.Order
import Game.Core as G

-- A pass can occur only before a player with a placement. Charging one unit
-- for the immobile side makes passes decrease without consuming a square.
noMoveBit : ∀ {A : Set} → List A → ℕ
noMoveBit [] = 1
noMoveBit (_ ∷ _) = 0

passBit : ∀ {size} → State size → ℕ
passBit s = noMoveBit (legalMoves s)

double : ℕ → ℕ
double zero = zero
double (suc n) = suc (suc (double n))

measure : ∀ {size} → State size → ℕ
measure s = double (empties s) + passBit s

infix 4 _<_
_<_ : ℕ → ℕ → Set
m < n = suc m ≤ n

≤-step : ∀ {m n} → m ≤ n → m ≤ suc n
≤-step z≤n = z≤n
≤-step (s≤s p) = s≤s (≤-step p)

+-zero : ∀ n → n + zero ≡ n
+-zero zero = refl
+-zero (suc n) = cong suc (+-zero n)

+-one : ∀ n → n + 1 ≡ suc n
+-one zero = refl
+-one (suc n) = cong suc (+-one n)

passBit-bound : ∀ {size} (s : State size) → passBit s ≤ 1
passBit-bound s with legalMoves s
... | [] = ≤-refl 1
... | _ ∷ _ = z≤n

≤-plus-right : ∀ n b → n ≤ n + b
≤-plus-right zero b = z≤n
≤-plus-right (suc n) b = s≤s (≤-plus-right n b)

-- Even allowing the newly immobile side one unit, placing a disc removes
-- two units, so every legal placement strictly decreases the measure.
placement-decreases-measure : ∀ {size} (s : State size) q → legal s q ≡ true →
  measure (applyMove s q) < measure s
placement-decreases-measure s q e = subst
  (λ n → suc (measure (applyMove s q)) ≤ double n + passBit s)
  (placement-decreases-empties s q e)
  (≤-trans upper (≤-plus-right (double (suc (empties (applyMove s q)))) (passBit s)))
  where
  upper : suc (measure (applyMove s q)) ≤ double (suc (empties (applyMove s q)))
  upper = subst (λ n → suc (measure (applyMove s q)) ≤ n)
    (cong suc (+-one (double (empties (applyMove s q)))))
    (s≤s (≤-add-left (double (empties (applyMove s q))) (passBit-bound (applyMove s q))))

map-preimage : ∀ {A B : Set} (f : A → B) {xs y} →
  y ∈ map f xs → Σ A (λ x → x ∈ xs × (f x ≡ y))
map-preimage f {xs = []} ()
map-preimage f {xs = x ∷ xs} here = x , here , refl
map-preimage f {xs = x ∷ xs} (there e) with map-preimage f e
... | y , m , eq = y , there m , eq

-- This theorem covers the actual successor list, including compulsory passes.
successor-decreases : ∀ {size} (s t : State size) →
  t ∈ successors s → measure t < measure s
successor-decreases s t member with legalMoves s in moves
... | q ∷ qs with map-preimage (applyMove s) member
... | r , in-moves , eq = subst
  (λ bit → measure t < double (empties s) + bit) (cong noMoveBit moves)
  (subst (λ u → measure u < measure s) eq
    (placement-decreases-measure s r (legal-complete
      (legalMoves-sound s (subst (λ xs → r ∈ xs) (sym moves) in-moves)))))
successor-decreases s t member | [] with legalMoves (passState s) in passed
... | [] = absurd (none member)
  where
  none : ∀ {A : Set} {x : A} → x ∈ [] → ⊥
  none ()
... | r ∷ rs with member
... | there ()
... | here rewrite moves | passed = subst
  (λ n → suc (double (empties s) + zero) ≤ n)
  (sym (+-one (double (empties s))))
  (subst (λ n → suc n ≤ suc (double (empties s)))
    (sym (+-zero (double (empties s)))) (≤-refl (suc (double (empties s)))))

data Acc {A : Set} (R : A → A → Set) (x : A) : Set where
  acc : ((y : A) → R y x → Acc R y) → Acc R x

≤-pred : ∀ {m n} → suc m ≤ suc n → m ≤ n
≤-pred (s≤s p) = p

bounded-accessible : (n m : ℕ) → m ≤ n → Acc _<_ m
bounded-accessible zero zero bound = acc (λ y → impossible)
  where
  impossible : ∀ {y} → suc y ≤ zero → Acc _<_ y
  impossible ()
bounded-accessible zero (suc m) ()
bounded-accessible (suc n) m bound = acc
  (λ y smaller → bounded-accessible n y (≤-pred (≤-trans smaller bound)))

nat-accessible : (n : ℕ) → Acc _<_ n
nat-accessible n = bounded-accessible n n (≤-refl n)

Successor : ∀ {size} → State size → State size → Set
Successor t s = t ∈ successors s

lift-accessible : ∀ {size} (s : State size) → Acc _<_ (measure s) → Acc Successor s
lift-accessible s (acc descend) = acc
  (λ t member → lift-accessible t (descend (measure t) (successor-decreases s t member)))

-- Actual well-foundedness, rather than a fuel assumption about exploration.
successors-well-founded : ∀ {size} (s : State size) → Acc Successor s
successors-well-founded s = lift-accessible s (nat-accessible (measure s))

lookup-member : ∀ {A : Set} {xs : List A} {i x} → G.lookup xs i ≡ just x → x ∈ xs
lookup-member {xs = []} ()
lookup-member {xs = y ∷ ys} {zero} refl = here
lookup-member {xs = y ∷ ys} {suc i} e = there (lookup-member e)

resolve-member : ∀ {A : Set} (x : A) xs i → G.selected (G.resolve x xs i) ∈ (x ∷ xs)
resolve-member x xs i with G.lookup (x ∷ xs) i in found
... | nothing = here
... | just y = lookup-member {xs = x ∷ xs} {i = i} found

complete-accessible : ∀ {size} (s : State size) → Acc Successor s →
  (p : Player) (σ τ : G.Strategy (State size)) →
  Σ (State size) (λ t → G.CompletedPlay (game size) p σ τ s t)
complete-accessible s (acc descend) p σ τ with successors s in next-e
... | [] = s , G.done next-e
... | x ∷ xs with complete-accessible
  (G.selected (G.resolve x xs (G.decision (game _) p σ τ s)))
  (descend _ (resolve-member x xs (G.decision (game _) p σ τ s)))
  p (G.shift (G.index (G.resolve x xs (G.decision (game _) p σ τ s))) σ)
    (G.shift (G.index (G.resolve x xs (G.decision (game _) p σ τ s))) τ)
... | t , play = t , G.step next-e play

-- Every pair of history-dependent strategies has an actual completed play.
all-strategies-complete : ∀ {size} (s : State size) (p : Player)
  (σ τ : G.Strategy (State size)) →
  Σ (State size) (λ t → G.CompletedPlay (game size) p σ τ s t)
all-strategies-complete s = complete-accessible s (successors-well-founded s)
