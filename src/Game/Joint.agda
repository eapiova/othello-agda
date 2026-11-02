{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.Joint where

open import Game.Core
open import Game.Composite using (StateEquality; equal; equal-sound)

-- Literal intermediate states bound each reduction to one transition.
-- The strategies, rather than a supplied move list, select every actual move.
jointCheck : ∀ {S} → StateEquality S → Game S → (S → Bool) →
  S → Strategy S → Strategy S → List S → Bool
jointCheck eq g goal s whiteStrategy blackStrategy [] with next g s
... | [] = goal s
... | _ ∷ _ = false
jointCheck eq g goal s whiteStrategy blackStrategy (t ∷ ts) with next g s
... | [] = false
... | x ∷ xs =
  equal eq (selected move) t ∧
  jointCheck eq g goal t (shift (index move) whiteStrategy)
    (shift (index move) blackStrategy) ts
  where move = resolve x xs (decision g white whiteStrategy blackStrategy s)

private
  left : ∀ a b → a ∧ b ≡ true → a ≡ true
  left true b e = refl
  left false b ()
  right : ∀ a b → a ∧ b ≡ true → b ≡ true
  right true b e = e
  right false b ()

joint-sound : ∀ {S} (eq : StateEquality S) (g : Game S) goal s σW σB path →
  jointCheck eq g goal s σW σB path ≡ true →
  Σ S (λ t → CompletedPlay g white σW σB s t × (goal t ≡ true))
joint-sound eq g goal s σW σB [] e with next g s in en
... | [] = s , done en , e
... | _ ∷ _ with e
... | ()
joint-sound eq g goal s σW σB (t ∷ ts) e with next g s in en
... | [] with e
... | ()
joint-sound eq g goal s σW σB (t ∷ ts) e | x ∷ xs with
  joint-sound eq g goal t (shift (index move) σW) (shift (index move) σB) ts
    (right (equal eq (selected move) t) rest e)
  where
  move = resolve x xs (decision g white σW σB s)
  rest = jointCheck eq g goal t (shift (index move) σW) (shift (index move) σB) ts
... | u , play , eg = u , step en child , eg
  where
  move = resolve x xs (decision g white σW σB s)
  rest = jointCheck eq g goal t (shift (index move) σW) (shift (index move) σB) ts
  same : selected move ≡ t
  same = equal-sound eq (selected move) t (left (equal eq (selected move) t) rest e)
  child : CompletedPlay g white (shift (index move) σW) (shift (index move) σB)
    (selected move) u
  child = subst (λ z → CompletedPlay g white (shift (index move) σW)
    (shift (index move) σB) z u) (sym same) play
