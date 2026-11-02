{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. The two winning strategies follow exactly one common legal line.
module Game.PathSplice where

open import Game.Core
import Game.StrategySplice as Splice

module Along {S : Set} (g : Game S) (whiteGoal blackGoal : S → Bool) where

  data Trace (s : S) : S → Set where
    stop : next g s ≡ [] → Trace s s
    move : ∀ {x xs u t} (i : ℕ) → next g s ≡ x ∷ xs →
      lookup (x ∷ xs) i ≡ just u → Trace u t → Trace s t

  private
    nothing-elim : ∀ {A B : Set} {x : A} → nothing ≡ just x → B
    nothing-elim ()

  prepend : ∀ {s u t} i → lookup (next g s) i ≡ just u → Trace u t → Trace s t
  prepend {s} i hit tail with next g s in en
  ... | [] = nothing-elim hit
  ... | x ∷ xs = move i en hit tail

  Bounds : ∀ {s t} → Trace s t → Set
  Bounds {s} (stop terminal) = Guarantees g white whiteGoal s × Guarantees g black blackGoal s
  Bounds {s} (move i en el tail) =
    (Guarantees g white whiteGoal s × Guarantees g black blackGoal s) × Bounds tail

  Pair : S → S → Set
  Pair s t = Σ (Guarantees g white whiteGoal s) (λ w →
    Σ (Guarantees g black blackGoal s) (λ b →
      CompletedPlay g white (forcing w) (forcing b) s t))

  private
    same-decision : ∀ b i → chooseDecision b i i ≡ i
    same-decision true i = refl
    same-decision false i = refl

  assemble : ∀ {s t} (line : Trace s t) → Bounds line → Pair s t
  assemble (stop terminal) (w , b) = w , b , done terminal
  assemble {s} {t} (move {x} {xs} {u} i en el tail) ((oldW , oldB) , bounds)
    with assemble tail bounds
  ... | w , b , q = newW , newB , stepAt en
      (same-decision (samePlayer (turn g s) white) i) el resumed
    where
    newW = Splice.attach g white whiteGoal s u i en el oldW w
    newB = Splice.attach g black blackGoal s u i en el oldB b
    resumed : CompletedPlay g white (shift i (forcing newW)) (shift i (forcing newB)) u t
    resumed = subst (λ σ → CompletedPlay g white σ (shift i (forcing newB)) u t)
      (sym (Splice.shift-path i (forcing w) (forcing oldW)))
      (subst (λ τ → CompletedPlay g white (forcing w) τ u t)
        (sym (Splice.shift-path i (forcing b) (forcing oldB))) q)
