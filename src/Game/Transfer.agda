{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.Transfer where

open import Game.Core
open import Game.Certificate

-- Agreement is pointwise, so no equality of functions is assumed.
record Agreement {S : Set} (g h : Game S) : Set where
  constructor agreement
  field
    next-agrees : ∀ s → next g s ≡ next h s
    turn-agrees : ∀ s → turn g s ≡ turn h s
    pass-agrees : ∀ s → forcedPass g s ≡ forcedPass h s
open Agreement public

mutual
  check-cong : ∀ {S} (g h : Game S) → Agreement g h →
    ∀ p goal s c → check g p goal s c ≡ check h p goal s c
  check-cong g h e p goal s leaf rewrite next-agrees e s with next h s
  ... | [] = refl
  ... | x ∷ xs = refl
  check-cong g h e p goal s (choice i c)
    rewrite next-agrees e s | turn-agrees e s
    with next h s | samePlayer (turn h s) p
  ... | [] | own = refl
  ... | x ∷ xs | false = refl
  ... | x ∷ xs | true with lookup (x ∷ xs) i
  ... | nothing = refl
  ... | just t = check-cong g h e p goal t c
  check-cong g h e p goal s (fork cs)
    rewrite next-agrees e s | turn-agrees e s
    with next h s | samePlayer (turn h s) p
  ... | [] | own = refl
  ... | x ∷ xs | true = refl
  ... | x ∷ xs | false = checkForest-cong g h e p goal (x ∷ xs) cs
  check-cong g h e p goal s (pass c)
    rewrite next-agrees e s | pass-agrees e s
    with next h s | forcedPass h s
  ... | [] | b = refl
  ... | x ∷ [] | false = refl
  ... | x ∷ y ∷ xs | b = refl
  ... | x ∷ [] | true = check-cong g h e p goal x c

  checkForest-cong : ∀ {S} (g h : Game S) → Agreement g h →
    ∀ p goal ss cs → checkForest g p goal ss cs ≡ checkForest h p goal ss cs
  checkForest-cong g h e p goal [] [] = refl
  checkForest-cong g h e p goal [] (c ∷ cs) = refl
  checkForest-cong g h e p goal (s ∷ ss) [] = refl
  checkForest-cong g h e p goal (s ∷ ss) (c ∷ cs)
    rewrite check-cong g h e p goal s c | checkForest-cong g h e p goal ss cs = refl

decision-cong : ∀ {S} (g h : Game S) → Agreement g h →
  ∀ p σ τ s → decision g p σ τ s ≡ decision h p σ τ s
decision-cong g h e p σ τ s rewrite turn-agrees e s = refl

completedPlay-transfer : ∀ {S} (g h : Game S) → Agreement g h →
  ∀ {p σ τ s t} → CompletedPlay g p σ τ s t → CompletedPlay h p σ τ s t
completedPlay-transfer g h e (done en) = done (trans (sym (next-agrees e _)) en)
completedPlay-transfer g h e {p} {σ} {τ} {s} {t} (step {x} {xs} en q) =
  step (trans (sym (next-agrees e s)) en)
    (subst (λ m → CompletedPlay h p (shift (index m) σ) (shift (index m) τ)
      (selected m) t)
      (cong (resolve x xs) (decision-cong g h e p σ τ s))
      (completedPlay-transfer g h e q))

guarantees-transfer : ∀ {S} (g h : Game S) → Agreement g h →
  ∀ {p goal s} → Guarantees g p goal s → Guarantees h p goal s
guarantees-transfer g h e (guarantee σ responds) = guarantee σ
  (λ τ → let result = responds τ in proj₁ result ,
    completedPlay-transfer g h e (proj₁ (proj₂ result)) , proj₂ (proj₂ result))

agreement-sym : ∀ {S} {g h : Game S} → Agreement g h → Agreement h g
agreement-sym e = agreement (λ s → sym (next-agrees e s))
  (λ s → sym (turn-agrees e s)) (λ s → sym (pass-agrees e s))
