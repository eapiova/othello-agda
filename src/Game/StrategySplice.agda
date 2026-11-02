{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Follow one winning continuation; retain an old strategy off it.
module Game.StrategySplice where

open import Game.Core
open import Agda.Builtin.Nat using () renaming (_==_ to _≡ᵇ_)

patch : ∀ {S} → ℕ → Strategy S → Strategy S → Strategy S
patch i child old [] s = i
patch i child old (j ∷ h) s = chooseDecision (j ≡ᵇ i) (child h s) (old (j ∷ h) s)

private
  nat-refl : ∀ i → (i ≡ᵇ i) ≡ true
  nat-refl zero = refl
  nat-refl (suc i) = nat-refl i

  nat-sound : ∀ j i → (j ≡ᵇ i) ≡ true → j ≡ i
  nat-sound zero zero e = refl
  nat-sound zero (suc i) ()
  nat-sound (suc j) zero ()
  nat-sound (suc j) (suc i) e = cong suc (nat-sound j i e)

  just-injective : ∀ {S : Set} {s t : S} → just s ≡ just t → s ≡ t
  just-injective refl = refl

  shift-yes : ∀ {S} j i (child old : Strategy S) → (j ≡ᵇ i) ≡ true →
    shift j (patch i child old) ≡ child
  shift-yes j i child old e = cong
    (λ b → λ h s → chooseDecision b (child h s) (old (j ∷ h) s)) e

  shift-no : ∀ {S} j i (child old : Strategy S) → (j ≡ᵇ i) ≡ false →
    shift j (patch i child old) ≡ shift j old
  shift-no j i child old e = cong
    (λ b → λ h s → chooseDecision b (child h s) (old (j ∷ h) s)) e

  tail-opponent : ∀ {S} {g : Game S} {p σ τ s t x xs} →
    (en : next g s ≡ x ∷ xs) → samePlayer (turn g s) p ≡ false →
    CompletedPlay g p σ τ s t →
    let m = resolve x xs (τ [] s) in
    CompletedPlay g p (shift (index m) σ) (shift (index m) τ) (selected m) t
  tail-opponent en eo (done et) with trans (sym en) et
  ... | ()
  tail-opponent {g = g} {p} {σ} {τ} {s} {t} {x} {xs} en eo (step en′ q)
    with trans (sym en) en′
  ... | refl = subst
    (λ m → CompletedPlay g p (shift (index m) σ) (shift (index m) τ) (selected m) t)
    (cong (resolve x xs) (decision-opponent {g = g} {p} {σ} {τ} {s} eo)) q

shift-path : ∀ {S} i (child old : Strategy S) → shift i (patch i child old) ≡ child
shift-path i child old = shift-yes i i child old (nat-refl i)

attach : ∀ {S} (g : Game S) p goal s t {x xs} i →
  next g s ≡ x ∷ xs → lookup (x ∷ xs) i ≡ just t →
  Guarantees g p goal s → Guarantees g p goal t → Guarantees g p goal s
attach {S} g p goal s t {x} {xs} i en el old child = guarantee strategy response
  where
  strategy : Strategy S
  strategy = patch i (forcing child) (forcing old)

  response : (τ : Strategy S) →
    Σ S (λ u → CompletedPlay g p strategy τ s u × (goal u ≡ true))
  response τ with samePlayer (turn g s) p in eo
  ... | true with responds child (shift i τ)
  ...   | u , q , won = u , stepAt en
      (decision-own {g = g} {p} {σ = strategy} {τ} {s} eo) el
      (subst (λ σ → CompletedPlay g p σ (shift i τ) t u)
        (sym (shift-path i (forcing child) (forcing old))) q) , won
  response τ | false with index (resolve x xs (τ [] s)) ≡ᵇ i in ei
  ... | true with responds child (shift (index (resolve x xs (τ [] s))) τ)
  ...   | u , q , won = u , stepFrom en
      (decision-opponent {g = g} {p} {σ = strategy} {τ} {s} eo) resumed , won
      where
      m = resolve x xs (τ [] s)
      same : selected m ≡ t
      same = just-injective (trans (sym (resolve-valid x xs (τ [] s)))
        (trans (cong (lookup (x ∷ xs)) (nat-sound (index m) i ei)) el))
      resumed : CompletedPlay g p (shift (index m) strategy) (shift (index m) τ) (selected m) u
      resumed = subst (λ σ → CompletedPlay g p σ (shift (index m) τ) (selected m) u)
        (sym (shift-yes (index m) i (forcing child) (forcing old) ei))
        (subst (λ z → CompletedPlay g p (forcing child) (shift (index m) τ) z u) (sym same) q)
  response τ | false | false with responds old τ
  ... | u , q , won = u , stepFrom en
      (decision-opponent {g = g} {p} {σ = strategy} {τ} {s} eo)
      (subst (λ σ → CompletedPlay g p σ (shift (index m) τ) (selected m) u)
        (sym (shift-no (index m) i (forcing child) (forcing old) ei))
        (tail-opponent en eo q)) , won
      where
      m = resolve x xs (τ [] s)
