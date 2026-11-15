{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. IDs retain bounded local rows and structural shard paths.
module Game.Balanced where

open import Prelude
import Game.Indexed as Indexed

data Shape : Set where
  leaf : ℕ → Shape
  branch : Shape → Shape → Shape

data Fin : ℕ → Set where
  fzero : ∀ {n} → Fin (suc n)
  fsuc : ∀ {n} → Fin n → Fin (suc n)

data Id : Shape → Set where
  row : ∀ {n} → Fin n → Id (leaf n)
  left : ∀ {l r} → Id l → Id (branch l r)
  right : ∀ {l r} → Id r → Id (branch l r)

mapMaybe : ∀ {A B : Set} → (A → B) → Maybe A → Maybe B
mapMaybe f nothing = nothing
mapMaybe f (just x) = just (f x)

-- Both the bound and the input decrease; no out-of-range value is clamped.
finFromNat : (n : ℕ) → ℕ → Maybe (Fin n)
finFromNat zero k = nothing
finFromNat (suc n) zero = just fzero
finFromNat (suc n) (suc k) = mapMaybe fsuc (finFromNat n k)

rowFromNat : (n : ℕ) → ℕ → Maybe (Id (leaf n))
rowFromNat n k = mapMaybe row (finFromNat n k)

finToNat : ∀ {n} → Fin n → ℕ
finToNat fzero = zero
finToNat (fsuc i) = suc (finToNat i)

fin-roundtrip : ∀ {n} (i : Fin n) → finFromNat n (finToNat i) ≡ just i
fin-roundtrip fzero = refl
fin-roundtrip (fsuc i) rewrite fin-roundtrip i = refl

row-roundtrip : ∀ {n} (i : Fin n) →
  rowFromNat n (finToNat i) ≡ just (row i)
row-roundtrip i rewrite fin-roundtrip i = refl

fin-at-bound : (n : ℕ) → finFromNat n n ≡ nothing
fin-at-bound zero = refl
fin-at-bound (suc n) rewrite fin-at-bound n = refl

row-at-bound : (n : ℕ) → rowFromNat n n ≡ nothing
row-at-bound n rewrite fin-at-bound n = refl

data FinBefore : ∀ {n} → Fin n → Fin n → Set where
  zero-before : ∀ {n} {j : Fin n} → FinBefore fzero (fsuc j)
  suc-before : ∀ {n} {i j : Fin n} → FinBefore i j → FinBefore (fsuc i) (fsuc j)

finBeforeB : ∀ {n} → Fin n → Fin n → Bool
finBeforeB fzero fzero = false
finBeforeB fzero (fsuc j) = true
finBeforeB (fsuc i) fzero = false
finBeforeB (fsuc i) (fsuc j) = finBeforeB i j

finBefore-sound : ∀ {n} (i j : Fin n) → finBeforeB i j ≡ true → FinBefore i j
finBefore-sound fzero fzero ()
finBefore-sound fzero (fsuc j) e = zero-before
finBefore-sound (fsuc i) fzero ()
finBefore-sound (fsuc i) (fsuc j) e = suc-before (finBefore-sound i j e)

data Before : ∀ {s} → Id s → Id s → Set where
  row-before : ∀ {n} {i j : Fin n} → FinBefore i j → Before (row i) (row j)
  left-before : ∀ {l r} {i j : Id l} → Before i j →
    Before {branch l r} (left i) (left j)
  across : ∀ {l r} {i : Id l} {j : Id r} → Before (left i) (right j)
  right-before : ∀ {l r} {i j : Id r} → Before i j →
    Before {branch l r} (right i) (right j)

beforeB : ∀ {s} → Id s → Id s → Bool
beforeB (row i) (row j) = finBeforeB i j
beforeB (left i) (left j) = beforeB i j
beforeB (left i) (right j) = true
beforeB (right i) (left j) = false
beforeB (right i) (right j) = beforeB i j

before-sound : ∀ {s} (i j : Id s) → beforeB i j ≡ true → Before i j
before-sound (row i) (row j) e = row-before (finBefore-sound i j e)
before-sound (left i) (left j) e = left-before (before-sound i j e)
before-sound (left i) (right j) e = across
before-sound (right i) (left j) ()
before-sound (right i) (right j) e = right-before (before-sound i j e)

finBefore-self : ∀ {n} (i : Fin n) → finBeforeB i i ≡ false
finBefore-self fzero = refl
finBefore-self (fsuc i) = finBefore-self i

before-self : ∀ {s} (i : Id s) → beforeB i i ≡ false
before-self (row i) = finBefore-self i
before-self (left i) = before-self i
before-self (right i) = before-self i

private
  finZeroAcc : ∀ {n} → Indexed.Acc FinBefore (fzero {n})
  finZeroAcc = Indexed.acc (λ { _ () })

  finSucAcc : ∀ {n} {i : Fin n} → Indexed.Acc FinBefore i →
    Indexed.Acc FinBefore (fsuc i)
  finSucAcc {i = i} (Indexed.acc children) = Indexed.acc preceding
    where
    preceding : ∀ j → FinBefore j (fsuc i) → Indexed.Acc FinBefore j
    preceding fzero zero-before = finZeroAcc
    preceding (fsuc j) (suc-before p) = finSucAcc (children j p)

  finAcc : ∀ {n} (i : Fin n) → Indexed.Acc FinBefore i
  finAcc fzero = finZeroAcc
  finAcc (fsuc i) = finSucAcc (finAcc i)

  rowAcc : ∀ {n} {i : Fin n} → Indexed.Acc FinBefore i →
    Indexed.Acc Before (row i)
  rowAcc {i = i} (Indexed.acc children) = Indexed.acc preceding
    where
    preceding : ∀ j → Before j (row i) → Indexed.Acc Before j
    preceding (row j) (row-before p) = rowAcc (children j p)

  leftAcc : ∀ {l r} {i : Id l} → Indexed.Acc Before i →
    Indexed.Acc Before (left {r = r} i)
  leftAcc {l = l} {r = r} {i = i} (Indexed.acc children) = Indexed.acc preceding
    where
    preceding : (j : Id (branch l r)) → Before j (left i) → Indexed.Acc Before j
    preceding (left j) (left-before p) = leftAcc (children j p)
    preceding (right j) ()

  rightAcc : ∀ {l r} {i : Id r} → ((j : Id l) → Indexed.Acc Before j) →
    Indexed.Acc Before i → Indexed.Acc Before (right {l = l} i)
  rightAcc {l = l} {r = r} {i = i} earlier (Indexed.acc children) = Indexed.acc preceding
    where
    preceding : (j : Id (branch l r)) → Before j (right i) → Indexed.Acc Before j
    preceding (left j) across = leftAcc (earlier j)
    preceding (right j) (right-before p) = rightAcc earlier (children j p)

-- This theorem follows the shape, then bounded leaf rows. It does not flatten
-- shard/row pairs into a unary global rank. Balance is chosen by the producer.
wellFounded : (s : Shape) → (i : Id s) → Indexed.Acc Before i
wellFounded (leaf n) (row i) = rowAcc (finAcc i)
wellFounded (branch l r) (left i) = leftAcc (wellFounded l i)
wellFounded (branch l r) (right i) = rightAcc (wellFounded l) (wellFounded r i)

order : (s : Shape) → Indexed.Order (Id s)
order s = record
  { _<_ = Before
  ; beforeB = beforeB
  ; before-sound = before-sound
  ; wellFounded = wellFounded s
  }

data Vec (A : Set) : ℕ → Set where
  nil : Vec A zero
  cons : ∀ {n} → A → Vec A n → Vec A (suc n)

lookupVec : ∀ {A n} → Vec A n → Fin n → A
lookupVec nil ()
lookupVec (cons x xs) fzero = x
lookupVec (cons x xs) (fsuc i) = lookupVec xs i

data Tree (A : Set) : Shape → Set where
  rows : ∀ {n} → Vec A n → Tree A (leaf n)
  join : ∀ {l r} → Tree A l → Tree A r → Tree A (branch l r)

lookup : ∀ {A s} → Tree A s → Id s → A
lookup (rows xs) (row i) = lookupVec xs i
lookup (join l r) (left i) = lookup l i
lookup (join l r) (right i) = lookup r i

resolve : ∀ {A s} → Tree (Maybe A) s → Indexed.Resolver (Id s) A
resolve = lookup

Agreement : ∀ {A : Set} → Maybe A → A → Set
Agreement nothing y = ⊤
Agreement (just x) y = y ≡ x

data RowsCompatible {A : Set} : ∀ {n} → Vec (Maybe A) n → Vec A n → Set where
  empty-compatible : RowsCompatible nil nil
  cons-compatible : ∀ {n x y} {xs : Vec (Maybe A) n} {ys : Vec A n} →
    Agreement x y → RowsCompatible xs ys → RowsCompatible (cons x xs) (cons y ys)

-- Compatibility composes independently checked leaves and branches. Missing
-- sparse entries need no equality evidence and cannot resolve a reference.
data TreeCompatible {A : Set} : ∀ {s} → Tree (Maybe A) s → Tree A s → Set where
  rows-compatible : ∀ {n} {xs : Vec (Maybe A) n} {ys : Vec A n} →
    RowsCompatible xs ys → TreeCompatible (rows xs) (rows ys)
  join-compatible : ∀ {l r} {ll : Tree (Maybe A) l} {lr : Tree (Maybe A) r}
    {gl : Tree A l} {gr : Tree A r} → TreeCompatible ll gl → TreeCompatible lr gr →
    TreeCompatible (join ll lr) (join gl gr)

private
  agreement-sound : ∀ {A : Set} (x : Maybe A) y u →
    Agreement x y → x ≡ just u → y ≡ u
  agreement-sound nothing y u a ()
  agreement-sound (just x) y u a refl = a

  rows-compatible-sound : ∀ {A n} {xs : Vec (Maybe A) n} {ys : Vec A n} →
    RowsCompatible xs ys → ∀ i u → lookupVec xs i ≡ just u → lookupVec ys i ≡ u
  rows-compatible-sound empty-compatible ()
  rows-compatible-sound (cons-compatible a rest) fzero u e = agreement-sound _ _ u a e
  rows-compatible-sound (cons-compatible a rest) (fsuc i) u e =
    rows-compatible-sound rest i u e

resolver-compatible : ∀ {A s} {local : Tree (Maybe A) s} {global : Tree A s} →
  TreeCompatible local global → ∀ i u → resolve local i ≡ just u → lookup global i ≡ u
resolver-compatible (rows-compatible proof) (row i) u e = rows-compatible-sound proof i u e
resolver-compatible (join-compatible lp rp) (left i) u e = resolver-compatible lp i u e
resolver-compatible (join-compatible lp rp) (right i) u e = resolver-compatible rp i u e
