{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.Soundness where

open import Game.Core
open import Game.Certificate

private
  false-elim : ∀ {A : Set} → false ≡ true → A
  false-elim ()

  ∧-left : ∀ a b → a ∧ b ≡ true → a ≡ true
  ∧-left true b e = refl
  ∧-left false b ()

  ∧-right : ∀ a b → a ∧ b ≡ true → b ≡ true
  ∧-right true b e = e
  ∧-right false b ()

-- The semantic evidence extracted from the structural checker includes
-- actual successor coverage, ownership, and genuine terminality.
mutual
  data Accepted {S : Set} (g : Game S) (p : Player) (goal : S → Bool)
                (s : S) : Certificate → Set where
    leafOK : next g s ≡ [] → goal s ≡ true → Accepted g p goal s leaf
    choiceOK : ∀ {x xs t i c} → samePlayer (turn g s) p ≡ true →
      next g s ≡ x ∷ xs → lookup (x ∷ xs) i ≡ just t →
      Accepted g p goal t c → Accepted g p goal s (choice i c)
    forkOK : ∀ {x xs cs} → samePlayer (turn g s) p ≡ false →
      next g s ≡ x ∷ xs → CertifiedList g p goal (x ∷ xs) cs →
      Accepted g p goal s (fork cs)
    passOK : ∀ {x c} → forcedPass g s ≡ true → next g s ≡ x ∷ [] →
      Accepted g p goal x c → Accepted g p goal s (pass c)

  data CertifiedList {S : Set} (g : Game S) (p : Player) (goal : S → Bool) :
                     List S → List Certificate → Set where
    nil : CertifiedList g p goal [] []
    cons : ∀ {s ss c cs} → Accepted g p goal s c → CertifiedList g p goal ss cs →
      CertifiedList g p goal (s ∷ ss) (c ∷ cs)

mutual
  accepted : ∀ {S} (g : Game S) (p : Player) (goal : S → Bool) (s : S) (c : Certificate) →
    check g p goal s c ≡ true → Accepted g p goal s c
  accepted g p goal s leaf e with next g s in en
  ... | [] = leafOK en e
  ... | x ∷ xs = false-elim e
  accepted g p goal s (choice i c) e with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = false-elim e
  ... | x ∷ xs | false = false-elim e
  ... | x ∷ xs | true with lookup (x ∷ xs) i in el
  ...   | nothing = false-elim e
  ...   | just t = choiceOK eo en el (accepted g p goal t c e)
  accepted g p goal s (fork cs) e with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = false-elim e
  ... | x ∷ xs | true = false-elim e
  ... | x ∷ xs | false = forkOK eo en (acceptedForest g p goal (x ∷ xs) cs e)
  accepted g p goal s (pass c) e with next g s in en | forcedPass g s in ep
  ... | [] | b = false-elim e
  ... | x ∷ [] | false = false-elim e
  ... | x ∷ y ∷ xs | b = false-elim e
  ... | x ∷ [] | true = passOK ep en (accepted g p goal x c e)

  acceptedForest : ∀ {S} (g : Game S) (p : Player) (goal : S → Bool)
    (ss : List S) (cs : List Certificate) →
    checkForest g p goal ss cs ≡ true → CertifiedList g p goal ss cs
  acceptedForest g p goal [] [] e = nil
  acceptedForest g p goal [] (c ∷ cs) ()
  acceptedForest g p goal (s ∷ ss) [] ()
  acceptedForest g p goal (s ∷ ss) (c ∷ cs) e =
    cons (accepted g p goal s c (∧-left (check g p goal s c) (checkForest g p goal ss cs) e))
         (acceptedForest g p goal ss cs (∧-right (check g p goal s c) (checkForest g p goal ss cs) e))

mutual
  -- This constructs a genuinely completed play for each opponent. Recursive
  -- calls strictly follow the finite accepted certificate, so termination
  -- needs no premise that all plays of the underlying game are finite.
  acceptedPlay : ∀ {S} {g : Game S} {p goal s c} → Accepted g p goal s c →
    (τ : Strategy S) →
    Σ S (λ t → CompletedPlay g p (certificateStrategy c) τ s t × (goal t ≡ true))
  acceptedPlay (leafOK en eg) τ = _ , done en , eg
  acceptedPlay {g = g} {p} {s = s} (choiceOK {i = i} {c = c} eo en el a) τ
    with acceptedPlay a (shift i τ)
  ... | t , q , eg = t , stepAt en (decision-own {g = g} {p = p} {σ = certificateStrategy (choice i c)} {τ = τ} {s = s} eo) el q , eg
  acceptedPlay {g = g} {p} {s = s} {c = fork cs} (forkOK {x} {xs} eo en as) τ
    with forestPlay as (index (resolve x xs (τ [] s)))
                      (selected (resolve x xs (τ [] s)))
                      (resolve-valid x xs (τ [] s))
                      (shift (index (resolve x xs (τ [] s))) τ)
  ... | c , el , t , q , eg = t , stepFrom en ed child , eg
    where
    i = index (resolve x xs (τ [] s))
    y = selected (resolve x xs (τ [] s))
    ed : decision g p (certificateStrategy (fork cs)) τ s ≡ τ [] s
    ed = decision-opponent {g = g} {p = p} {σ = certificateStrategy (fork cs)} {τ = τ} {s = s} eo
    child : CompletedPlay g p (shift i (certificateStrategy (fork cs))) (shift i τ) y t
    child = subst (λ σ → CompletedPlay g p σ (shift i τ) y t)
                  (sym (fork-shift {cs = cs} {i = i} {c = c} el)) q
  acceptedPlay (passOK ep en a) τ with acceptedPlay a (shift zero τ)
  ... | t , q , eg = t , stepOnly en q , eg

  forestPlay : ∀ {S} {g : Game S} {p goal ss cs} →
    CertifiedList g p goal ss cs → (i : ℕ) → (s : S) → lookup ss i ≡ just s →
    (τ : Strategy S) →
    Σ Certificate (λ c → lookup cs i ≡ just c ×
      Σ S (λ t → CompletedPlay g p (certificateStrategy c) τ s t × (goal t ≡ true)))
  forestPlay nil i s () τ
  forestPlay (cons {c = c} a as) zero s e τ with e
  ... | refl = c , refl , acceptedPlay a τ
  forestPlay (cons a as) (suc i) s e τ = forestPlay as i s e τ

checkSound : ∀ {S} (g : Game S) (p : Player) (goal : S → Bool) (s : S) (c : Certificate) →
  check g p goal s c ≡ true → Guarantees g p goal s
checkSound g p goal s c e = guarantee (certificateStrategy c) (acceptedPlay (accepted g p goal s c e))
