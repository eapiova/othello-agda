{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Every output certificate is rebuilt with checked evidence.
module Game.CertificateTransport where

open import Game.Core
open import Game.Certificate
open import Game.Soundness using (Accepted; CertifiedList; leafOK; choiceOK; forkOK; passOK; accepted)
import Game.Soundness as Sound
open import Game.Symmetry using (Proven; CertificateTransport)
open import Game.Permutation using (Perm; nil; skip; swap; chain; perm-sym; perm-map)

data At {A : Set} (x : A) : List A → Set where
  here : ∀ {xs} → At x (x ∷ xs)
  there : ∀ {y xs} → At x xs → At x (y ∷ xs)

lookup-At : ∀ {A : Set} {x : A} {xs i} → lookup xs i ≡ just x → At x xs
lookup-At {xs = []} ()
lookup-At {xs = y ∷ ys} {zero} refl = here
lookup-At {xs = y ∷ ys} {suc i} e = there (lookup-At e)

At-lookup : ∀ {A : Set} {x : A} {xs} → At x xs → Σ ℕ (λ i → lookup xs i ≡ just x)
At-lookup here = zero , refl
At-lookup (there a) with At-lookup a
... | i , e = suc i , e

map-At : ∀ {A B : Set} (f : A → B) {x xs} → At x xs → At (f x) (map f xs)
map-At f here = here
map-At f (there a) = there (map-At f a)

perm-At : ∀ {A : Set} {x : A} {xs ys} → Perm xs ys → At x xs → At x ys
perm-At nil ()
perm-At (skip p) here = here
perm-At (skip p) (there a) = there (perm-At p a)
perm-At swap here = there here
perm-At swap (there here) = here
perm-At swap (there (there a)) = there (there a)
perm-At (chain p q) a = perm-At q (perm-At p a)

At-nonempty : ∀ {A : Set} {x : A} {ys} → At x ys →
  Σ A (λ y → Σ (List A) (λ zs → ys ≡ y ∷ zs))
At-nonempty here = _ , _ , refl
At-nonempty (there a) = _ , _ , refl

perm-empty : ∀ {A : Set} {ys : List A} → Perm [] ys → ys ≡ []
perm-empty nil = refl
perm-empty (chain p q) rewrite perm-empty p = perm-empty q

perm-single : ∀ {A : Set} {x : A} {ys} → Perm (x ∷ []) ys → ys ≡ x ∷ []
perm-single (skip p) rewrite perm-empty p = refl
perm-single (chain p q) rewrite perm-single p = perm-single q

mutual
  accepted-check : ∀ {S} {g : Game S} {p goal s c} →
    Accepted g p goal s c → check g p goal s c ≡ true
  accepted-check (leafOK en eg) rewrite en = eg
  accepted-check (choiceOK eo en el a) rewrite en | eo | el = accepted-check a
  accepted-check (forkOK eo en as) rewrite en | eo = forest-check as
  accepted-check (passOK ep en a) rewrite en | ep = accepted-check a

  forest-check : ∀ {S} {g : Game S} {p goal ss cs} →
    CertifiedList g p goal ss cs → checkForest g p goal ss cs ≡ true
  forest-check Sound.nil = refl
  forest-check (Sound.cons a as) rewrite accepted-check a | forest-check as = refl

-- Reordering carries certificates together with their state-indexed evidence.
perm-forest : ∀ {S} {g : Game S} {p goal xs ys cs} → Perm xs ys →
  CertifiedList g p goal xs cs →
  Σ (List Certificate) (λ ds → CertifiedList g p goal ys ds)
perm-forest nil Sound.nil = [] , Sound.nil
perm-forest (skip p) (Sound.cons {c = c} a as) with perm-forest p as
... | ds , bs = c ∷ ds , Sound.cons a bs
perm-forest swap (Sound.cons {c = c} a (Sound.cons {c = d} b bs)) =
  d ∷ c ∷ _ , Sound.cons b (Sound.cons a bs)
perm-forest (chain p q) as with perm-forest p as
... | ds , bs = perm-forest q bs

record ActionLaws {S : Set} (g : Game S) (goal : S → Bool) (f : S → S) : Set where
  field
    preserves-turn : ∀ s → turn g (f s) ≡ turn g s
    preserves-pass : ∀ s → forcedPass g (f s) ≡ forcedPass g s
    preserves-goal : ∀ s → goal (f s) ≡ goal s
    successors : ∀ s → Perm (map f (next g s)) (next g (f s))
open ActionLaws public

mutual
  map-accepted : ∀ {S} {g : Game S} {p goal f s c} → ActionLaws g goal f →
    Accepted g p goal s c → Σ Certificate (λ d → Accepted g p goal (f s) d)
  map-accepted {g = g} {f = f} {s = s} laws (leafOK en eg) =
    leaf , leafOK (trans (perm-empty (subst (λ xs → Perm (map f xs) (next g (f s))) en (successors laws s))) refl)
                 (trans (preserves-goal laws s) eg)
  map-accepted {g = g} {p} {goal} {f} {s} laws (choiceOK {x} {xs} {t} {i} eo en el a)
    with map-accepted laws a
       | At-lookup target
       | At-nonempty target
    where
    target : At (f t) (next g (f s))
    target = perm-At (successors laws s)
      (map-At f (subst (λ ss → At t ss) (sym en) (lookup-At {i = i} el)))
  ... | d , b | j , ej | y , ys , ey = choice j d ,
    choiceOK (trans (cong (λ v → samePlayer v p) (preserves-turn laws s)) eo)
             ey (subst (λ ss → lookup ss j ≡ just (f t)) ey ej) b
  map-accepted {g = g} {p} {goal} {f} {s} laws (forkOK {x} {xs} eo en as)
    with map-forest laws as
  ... | cs , bs with perm-forest (subst (λ ss → Perm (map f ss) (next g (f s))) en (successors laws s)) bs
                   | At-nonempty (perm-At (successors laws s)
                       (map-At f (subst (λ ss → At x ss) (sym en) here)))
  ... | ds , ds-ok | y , ys , ey = fork ds ,
    forkOK (trans (cong (λ v → samePlayer v p) (preserves-turn laws s)) eo)
           ey (subst (λ ss → CertifiedList g p goal ss ds) ey ds-ok)
  map-accepted {g = g} {f = f} {s = s} laws (passOK {x} ep en a)
    with map-accepted laws a
  ... | d , b = pass d , passOK (trans (preserves-pass laws s) ep)
    (perm-single (subst (λ ss → Perm (map f ss) (next g (f s))) en (successors laws s))) b

  map-forest : ∀ {S} {g : Game S} {p goal f ss cs} → ActionLaws g goal f →
    CertifiedList g p goal ss cs →
    Σ (List Certificate) (λ ds → CertifiedList g p goal (map f ss) ds)
  map-forest laws Sound.nil = [] , Sound.nil
  map-forest laws (Sound.cons a as) with map-accepted laws a | map-forest laws as
  ... | d , b | ds , bs = d ∷ ds , Sound.cons b bs

-- The input equality comes from the ordinary checker, and the output is a
-- certificate accepted by that same checker after indices/order are changed.
map-proven : ∀ {S} {g : Game S} {p goal f} → ActionLaws g goal f →
  (s : S) → Proven g p goal s → Proven g p goal (f s)
map-proven {g = g} {p} {goal} laws s (c , ok)
  with map-accepted laws (accepted g p goal s c ok)
... | d , a = d , accepted-check a

map-compose : ∀ {A B C : Set} (f : B → C) (h : A → B) xs →
  map f (map h xs) ≡ map (λ x → f (h x)) xs
map-compose f h [] = refl
map-compose f h (x ∷ xs) = cong (f (h x) ∷_) (map-compose f h xs)

map-inverse : ∀ {S : Set} (f h : S → S) → (∀ s → h (f s) ≡ s) →
  ∀ xs → map h (map f xs) ≡ xs
map-inverse f h left [] = refl
map-inverse f h left (x ∷ xs) rewrite left x | map-inverse f h left xs = refl

record BijectiveActionLaws {S : Set} (g : Game S) (goal : S → Bool) (f : S → S) : Set where
  field
    inverse : S → S
    inverse-left : ∀ s → inverse (f s) ≡ s
    inverse-right : ∀ s → f (inverse s) ≡ s
    forward-laws : ActionLaws g goal f
open BijectiveActionLaws public

inverse-laws : ∀ {S} {g : Game S} {goal f} →
  (laws : BijectiveActionLaws g goal f) → ActionLaws g goal (inverse laws)
inverse-laws {g = g} {goal} {f} laws = record
  { preserves-turn = λ s → trans (sym (preserves-turn forward (h s))) (cong (turn g) (inverse-right laws s))
  ; preserves-pass = λ s → trans (sym (preserves-pass forward (h s))) (cong (forcedPass g) (inverse-right laws s))
  ; preserves-goal = λ s → trans (sym (preserves-goal forward (h s))) (cong goal (inverse-right laws s))
  ; successors = λ s → perm-sym
      (subst (λ ys → Perm (next g (h s)) (map h (next g ys))) (inverse-right laws s)
        (subst (λ xs → Perm xs (map h (next g (f (h s)))))
          (map-inverse f h (inverse-left laws) (next g (h s)))
          (perm-map h (successors forward (h s)))))
  }
  where
  h = inverse laws
  forward = forward-laws laws

bijective-transport : ∀ {S} {g : Game S} {p goal f} → BijectiveActionLaws g goal f →
  (s : S) → Proven g p goal (f s) → Proven g p goal s
bijective-transport {g = g} {p} {goal} {f} laws s proof =
  subst (Proven g p goal) (inverse-left laws s) (map-proven (inverse-laws laws) (f s) proof)

permutationTransport : ∀ {S} (g : Game S) p goal (action : ℕ → S → S) →
  (∀ tag → BijectiveActionLaws g goal (action tag)) → CertificateTransport g p goal
permutationTransport g p goal action laws = record
  { act = action
  ; acceptedTag = λ _ → true
  ; transport = λ tag s proof → bijective-transport (laws tag) s proof
  }
