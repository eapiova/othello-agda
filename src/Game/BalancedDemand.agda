{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Sparse alignment requirements compose without inspecting data.
module Game.BalancedDemand where

open import Prelude
import Game.Balanced as B
import Game.BalancedView as View

data Demand (A : Set) : B.Shape → Set where
  absent : ∀ {shape} → Demand A shape
  need : ∀ {n} → B.Vec A n → Demand A (B.leaf n)
  branches : ∀ {l r} → Demand A l → Demand A r → Demand A (B.branch l r)

Aligned : ∀ {A shape} → Demand A shape → (B.Id shape → A) → Set
Aligned absent G = ⊤
Aligned (need xs) G = ∀ i → G (B.row i) ≡ B.lookupVec xs i
Aligned (branches l r) G =
  Aligned l (λ i → G (B.left i)) × Aligned r (λ i → G (B.right i))

data Included {A : Set} : ∀ {shape} → Demand A shape → Demand A shape → Set where
  empty : ∀ {shape} {d : Demand A shape} → Included absent d
  same : ∀ {n} {xs : B.Vec A n} → Included (need xs) (need xs)
  fork : ∀ {l r} {dl el : Demand A l} {dr er : Demand A r} →
    Included dl el → Included dr er → Included (branches dl dr) (branches el er)

restrict : ∀ {A shape} {small large : Demand A shape} {G : B.Id shape → A} →
  Included small large → Aligned large G → Aligned small G
restrict empty proof = tt
restrict same proof = proof
restrict (fork l r) (lp , rp) = restrict l lp , restrict r rp

asView : ∀ {A shape} → Demand A shape → View.View A shape
asView absent = View.absent
asView (need xs) = View.present (View.allStates xs)
asView (branches l r) = View.branches (asView l) (asView r)

aligned-view : ∀ {A shape} {d : Demand A shape} {G : B.Id shape → A} →
  Aligned d G → View.Compatible (asView d) G
aligned-view {d = absent} proof = tt
aligned-view {d = need xs} {G = G} proof = View.present-compatible xs G proof
aligned-view {d = branches l r} (lp , rp) = aligned-view lp , aligned-view rp

replicate : ∀ {A : Set} → (n : ℕ) → A → B.Vec A n
replicate zero x = B.nil
replicate (suc n) x = B.cons x (replicate n x)

defaults : ∀ {A : Set} → (shape : B.Shape) → A → B.Tree A shape
defaults (B.leaf n) x = B.rows (replicate n x)
defaults (B.branch l r) x = B.join (defaults l x) (defaults r x)

-- Missing leaves have ordinary default data. They supply no row acceptance;
-- a final global theorem must still justify every typed ID independently.
totalize : ∀ {A shape} → Demand A shape → A → B.Tree A shape
totalize {shape = shape} absent x = defaults shape x
totalize (need xs) x = B.rows xs
totalize (branches l r) x = B.join (totalize l x) (totalize r x)

self-aligned : ∀ {A shape} (d : Demand A shape) x →
  Aligned d (B.lookup (totalize d x))
self-aligned absent x = tt
self-aligned (need xs) x = λ i → refl
self-aligned (branches l r) x = self-aligned l x , self-aligned r x
