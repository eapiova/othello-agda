{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Sparse maps may cite only data found in the exact global map.
module Game.NatMapLaws where

open import Prelude
open import Agda.Builtin.Nat using (_+_; _<_) renaming (_-_ to _∸_)
open import Othello.Order using (_≤_; z≤n; s≤s; ≤-trans; ≤-add-left)
import Game.Balanced as B
import Game.NatMap as M

private
  nothing-elim : ∀ {A : Set} {u : A} {P : Set} → nothing ≡ just u → P
  nothing-elim ()

  just-injective : ∀ {A : Set} {u v : A} → just u ≡ just v → u ≡ v
  just-injective refl = refl

  not-before : ∀ m n → (m < n) ≡ false → n ≤ m
  not-before m zero e = z≤n
  not-before zero (suc n) ()
  not-before (suc m) (suc n) e = s≤s (not-before m n e)

  restore : ∀ {base key} → base ≤ key → base + (key ∸ base) ≡ key
  restore z≤n = refl
  restore (s≤s p) = cong suc (restore p)

  plus-not-before : ∀ base k → (base + k < base) ≡ false
  plus-not-before zero k = refl
  plus-not-before (suc base) k = plus-not-before base k

  plus-minus : ∀ base k → (base + k) ∸ base ≡ k
  plus-minus zero k = refl
  plus-minus (suc base) k = plus-minus base k

  fin-found : ∀ n k {i : B.Fin n} → B.finFromNat n k ≡ just i → B.finToNat i ≡ k
  fin-found zero k ()
  fin-found (suc n) zero refl = refl
  fin-found (suc n) (suc k) e with B.finFromNat n k in found
  ... | nothing = nothing-elim e
  ... | just i with e
  ... | refl = cong suc (fin-found n k found)

rows-roundtrip : ∀ {A n} base (xs : B.Vec A n) i →
  M.lookup (M.rows base n xs) (base + B.finToNat i) ≡ just (B.lookupVec xs i)
rows-roundtrip base xs i rewrite plus-not-before base (B.finToNat i)
  | plus-minus base (B.finToNat i) | B.fin-roundtrip i = refl

-- A successful lookup provides an actual bounded row and its exact numeric key.
-- This is the bridge from independently checked finite vectors to arbitrary IDs.
rows-hit : ∀ {A : Set} base n (xs : B.Vec A n) key {u} →
  M.lookup (M.rows base n xs) key ≡ just u →
  Σ (B.Fin n) (λ i → (key ≡ base + B.finToNat i) × (B.lookupVec xs i ≡ u))
rows-hit base n xs key e with key < base in before
... | true = nothing-elim e
... | false with B.finFromNat n (key ∸ base) in found
... | nothing = nothing-elim e
... | just i = i ,
  (trans (sym (restore (not-before key base before)))
    (cong (λ k → base + k) (sym (fin-found n (key ∸ base) found))) ,
   just-injective e)

Compatible : ∀ {A} → M.Map A → (ℕ → A) → Set
Compatible map G = ∀ key u → M.lookup map key ≡ just u → G key ≡ u

rows-aligned : ∀ {A n} base (xs : B.Vec A n) G →
  Compatible (M.rows base n xs) G → ∀ i →
  G (base + B.finToNat i) ≡ B.lookupVec xs i
rows-aligned base xs G compatible i =
  compatible (base + B.finToNat i) (B.lookupVec xs i) (rows-roundtrip base xs i)

data Included {A : Set} : M.Map A → M.Map A → Set where
  empty : ∀ {large} → Included M.absent large
  same : ∀ {base n} {xs : B.Vec A n} → Included (M.rows base n xs) (M.rows base n xs)
  fork : ∀ {pivot l r ll rr} → Included l ll → Included r rr →
    Included (M.branch pivot l r) (M.branch pivot ll rr)

lookup-included : ∀ {A small large} → Included {A} small large →
  ∀ key u → M.lookup small key ≡ just u → M.lookup large key ≡ just u
lookup-included empty key u ()
lookup-included same key u e = e
lookup-included (fork {pivot} l r) key u e with key < pivot
... | true = lookup-included l key u e
... | false = lookup-included r key u e

restrict : ∀ {A small large G} → Included {A} small large →
  Compatible large G → Compatible small G
restrict included compatible key u e = compatible key u (lookup-included included key u e)

totalize : ∀ {A} → M.Map A → A → ℕ → A
totalize map fallback key = fromMaybe fallback (M.lookup map key)

self-compatible : ∀ {A} (map : M.Map A) fallback → Compatible map (totalize map fallback)
self-compatible map fallback key u e rewrite e = refl

-- Equal domains follow from matching pivots, bases and finite row counts,
-- independently of the contents of either vector.
data Together {A C : Set} : M.Map A → M.Map C → Set where
  empty-pair : Together M.absent M.absent
  rows-pair : ∀ {base n} {xs : B.Vec A n} {ys : B.Vec C n} →
    Together (M.rows base n xs) (M.rows base n ys)
  fork-pair : ∀ {pivot l r ll rr} → Together l ll → Together r rr →
    Together (M.branch pivot l r) (M.branch pivot ll rr)

isJust : ∀ {A : Set} → Maybe A → Bool
isJust nothing = false
isJust (just x) = true

same-domain : ∀ {A C left right} → Together {A} {C} left right →
  ∀ key → isJust (M.lookup left key) ≡ isJust (M.lookup right key)
same-domain empty-pair key = refl
same-domain (rows-pair {base} {n}) key with key < base
... | true = refl
... | false with B.finFromNat n (key ∸ base)
... | nothing = refl
... | just i = refl
same-domain (fork-pair {pivot} l r) key with key < pivot
... | true = same-domain l key
... | false = same-domain r key

-- Numerical branch bounds are checked using builtin comparison; the proof
-- remains symbolic, rather than expanding large integer inequalities.
at-most : ∀ a b → (a < suc b) ≡ true → a ≤ b
at-most zero b e = z≤n
at-most (suc a) zero ()
at-most (suc a) (suc b) e = s≤s (at-most a b e)

private
  less-complete : ∀ {a b} → suc a ≤ b → (a < b) ≡ true
  less-complete {b = zero} ()
  less-complete {a = zero} {suc b} (s≤s p) = refl
  less-complete {a = suc a} {suc b} (s≤s p) = less-complete p

  not-less-complete : ∀ {a b} → b ≤ a → (a < b) ≡ false
  not-less-complete z≤n = refl
  not-less-complete (s≤s p) = not-less-complete p

  rank-bound : ∀ {n} (i : B.Fin n) → suc (B.finToNat i) ≤ n
  rank-bound B.fzero = s≤s z≤n
  rank-bound (B.fsuc i) = s≤s (rank-bound i)

  plus-suc : ∀ a b → a + suc b ≡ suc (a + b)
  plus-suc zero b = refl
  plus-suc (suc a) b = cong suc (plus-suc a b)

  plus-zero : ∀ a → a + zero ≡ a
  plus-zero zero = refl
  plus-zero (suc a) = cong suc (plus-zero a)

  offset-bound : ∀ {n} base (i : B.Fin n) → suc (base + B.finToNat i) ≤ base + n
  offset-bound {n} base i = subst (λ x → x ≤ base + n)
    (plus-suc base (B.finToNat i)) (≤-add-left base (rank-bound i))

  above-base : ∀ base k → base ≤ base + k
  above-base base k = subst (λ x → x ≤ base + k) (plus-zero base)
    (≤-add-left base {zero} {k} z≤n)

data Route {A : Set} : M.Map A → (base n : ℕ) → B.Vec A n → Set where
  here : ∀ {base n xs} → Route (M.rows base n xs) base n xs
  left : ∀ {pivot l r base n xs} → base + n ≤ pivot → Route l base n xs →
    Route (M.branch pivot l r) base n xs
  right : ∀ {pivot l r base n xs} → pivot ≤ base → Route r base n xs →
    Route (M.branch pivot l r) base n xs

lookup-route : ∀ {A map base n} {xs : B.Vec A n} → Route map base n xs →
  ∀ i → M.lookup map (base + B.finToNat i) ≡ just (B.lookupVec xs i)
lookup-route {base = base} {xs = xs} here i = rows-roundtrip base xs i
lookup-route {base = base} (left bound path) i
  rewrite less-complete (≤-trans (offset-bound base i) bound) = lookup-route path i
lookup-route {base = base} (right bound path) i
  rewrite not-less-complete (≤-trans bound (above-base base (B.finToNat i))) = lookup-route path i

route-aligned : ∀ {A map base n} {xs : B.Vec A n} G → Route map base n xs →
  Compatible map G → ∀ i → G (base + B.finToNat i) ≡ B.lookupVec xs i
route-aligned {base = base} {xs = xs} G path compatible i =
  compatible (base + B.finToNat i) (B.lookupVec xs i) (lookup-route path i)

-- Alignment is stronger than lookup compatibility: it names every finite
-- row symbolically and composes as pairs, without embedding a layout in IDs.
Aligned : ∀ {A} → M.Map A → (ℕ → A) → Set
Aligned M.absent G = ⊤
Aligned (M.rows base n xs) G = ∀ i → G (base + B.finToNat i) ≡ B.lookupVec xs i
Aligned (M.branch pivot l r) G = Aligned l G × Aligned r G

aligned-compatible : ∀ {A map G} → Aligned {A} map G → Compatible map G
aligned-compatible {map = M.absent} aligned key u ()
aligned-compatible {map = M.rows base n xs} {G = G} aligned key u hit
  with rows-hit base n xs key hit
... | i , keyEquals , stateEquals =
  trans (cong G keyEquals) (trans (aligned i) stateEquals)
aligned-compatible {map = M.branch pivot l r} (leftAligned , rightAligned) key u hit
  with key < pivot
... | true = aligned-compatible leftAligned key u hit
... | false = aligned-compatible rightAligned key u hit

aligned-restrict : ∀ {A small large G} → Included {A} small large →
  Aligned large G → Aligned small G
aligned-restrict empty aligned = tt
aligned-restrict same aligned = aligned
aligned-restrict (fork l r) (leftAligned , rightAligned) =
  aligned-restrict l leftAligned , aligned-restrict r rightAligned
