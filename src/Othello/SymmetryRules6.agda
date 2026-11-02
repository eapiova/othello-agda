{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Concrete arbitrary-board rule laws for all eight actions.
module Othello.SymmetryRules6 where

open import Prelude
open import Othello.Board
open import Othello.Rules
open import Othello.Symmetry6
import Othello.Finite as V
open import Agda.Builtin.Nat renaming (_==_ to _≡ᵇ_)

private
  data ⊥ : Set where

  absurd : ∀ {A : Set} → ⊥ → A
  absurd ()

  false≠true : false ≡ true → ⊥
  false≠true ()

  bool-ext : ∀ a b → (a ≡ true → b ≡ true) → (b ≡ true → a ≡ true) → a ≡ b
  bool-ext false false f g = refl
  bool-ext false true f g = absurd (false≠true (g refl))
  bool-ext true false f g = absurd (false≠true (f refl))
  bool-ext true true f g = refl

  ∧-left : ∀ a b → a ∧ b ≡ true → a ≡ true
  ∧-left false b ()
  ∧-left true b p = refl

  ∧-right : ∀ a b → a ∧ b ≡ true → b ≡ true
  ∧-right false b ()
  ∧-right true b p = p

  fin-eq-self : ∀ {n} (i : V.Fin n) → (V.toℕ i ≡ᵇ V.toℕ i) ≡ true
  fin-eq-self V.zero = refl
  fin-eq-self (V.suc i) = fin-eq-self i

  fin-eq-sound : ∀ {n} (i j : V.Fin n) → (V.toℕ i ≡ᵇ V.toℕ j) ≡ true → i ≡ j
  fin-eq-sound V.zero V.zero p = refl
  fin-eq-sound V.zero (V.suc j) ()
  fin-eq-sound (V.suc i) V.zero ()
  fin-eq-sound (V.suc i) (V.suc j) p = cong V.suc (fin-eq-sound i j p)

sameCoord-self : ∀ {size} (q : Coord size) → sameCoord q q ≡ true
sameCoord-self (r , c) rewrite fin-eq-self r | fin-eq-self c = refl

sameCoord-sound : ∀ {size} (q r : Coord size) → sameCoord q r ≡ true → q ≡ r
sameCoord-sound (a , b) (c , d) p
  rewrite fin-eq-sound a c (∧-left (V.toℕ a ≡ᵇ V.toℕ c) (V.toℕ b ≡ᵇ V.toℕ d) p)
        | fin-eq-sound b d (∧-right (V.toℕ a ≡ᵇ V.toℕ c) (V.toℕ b ≡ᵇ V.toℕ d) p) = refl

sameCoord-equivariant : ∀ σ q r →
  sameCoord {size = six} (coordinate σ q) (coordinate σ r) ≡ sameCoord {size = six} q r
sameCoord-equivariant σ q r = bool-ext _ _ backward forward
  where
  forward : sameCoord {size = six} q r ≡ true → sameCoord {size = six} (coordinate σ q) (coordinate σ r) ≡ true
  forward p rewrite sameCoord-sound {size = six} q r p = sameCoord-self {size = six} (coordinate σ r)
  backward : sameCoord {size = six} (coordinate σ q) (coordinate σ r) ≡ true → sameCoord {size = six} q r ≡ true
  backward p = subst (λ x → sameCoord {size = six} q x ≡ true)
    (trans (sym (coordinate-inverse σ q))
      (trans (cong (coordinate (inverse σ)) (sameCoord-sound {size = six} (coordinate σ q) (coordinate σ r) p))
        (coordinate-inverse σ r))) (sameCoord-self {size = six} q)

contains-map : ∀ σ q xs → contains {size = six} (coordinate σ q) (map (coordinate σ) xs) ≡ contains {size = six} q xs
contains-map σ q [] = refl
contains-map σ q (r ∷ rs) rewrite sameCoord-equivariant σ q r | contains-map σ q rs = refl

private
  data Member {A : Set} (x : A) : List A → Set where
    here : ∀ {xs} → Member x (x ∷ xs)
    there : ∀ {y xs} → Member x xs → Member x (y ∷ xs)

  any : ∀ {A : Set} → (A → Bool) → List A → Bool
  any f [] = false
  any f (x ∷ xs) = f x ∨ any f xs

  any-witness : ∀ {A : Set} (f : A → Bool) xs → any f xs ≡ true →
    Σ A (λ x → Member x xs × (f x ≡ true))
  any-witness f [] ()
  any-witness f (x ∷ xs) p with f x in fx
  ... | true = x , (here , fx)
  ... | false with any-witness f xs p
  ... | y , (mem , fy) = y , (there mem , fy)

  any-member : ∀ {A : Set} (f : A → Bool) {x xs} → Member x xs → f x ≡ true → any f xs ≡ true
  any-member f here p rewrite p = refl
  any-member f (there {y = y} mem) p with f y
  ... | true = refl
  ... | false = any-member f mem p

  direction-member : ∀ d → Member d directions
  direction-member north = here
  direction-member northEast = there here
  direction-member east = there (there here)
  direction-member southEast = there (there (there here))
  direction-member south = there (there (there (there here)))
  direction-member southWest = there (there (there (there (there here))))
  direction-member west = there (there (there (there (there (there here)))))
  direction-member northWest = there (there (there (there (there (there (there here))))))

  any-cong : ∀ {A : Set} (f g : A → Bool) xs → (∀ x → f x ≡ g x) → any f xs ≡ any g xs
  any-cong f g [] eq = refl
  any-cong f g (x ∷ xs) eq rewrite eq x | any-cong f g xs eq = refl

  direction-inverse-right : ∀ σ d → direction σ (direction (inverse σ) d) ≡ d
  direction-inverse-right identity north = refl
  direction-inverse-right identity northEast = refl
  direction-inverse-right identity east = refl
  direction-inverse-right identity southEast = refl
  direction-inverse-right identity south = refl
  direction-inverse-right identity southWest = refl
  direction-inverse-right identity west = refl
  direction-inverse-right identity northWest = refl
  direction-inverse-right rotate90 north = refl
  direction-inverse-right rotate90 northEast = refl
  direction-inverse-right rotate90 east = refl
  direction-inverse-right rotate90 southEast = refl
  direction-inverse-right rotate90 south = refl
  direction-inverse-right rotate90 southWest = refl
  direction-inverse-right rotate90 west = refl
  direction-inverse-right rotate90 northWest = refl
  direction-inverse-right rotate180 north = refl
  direction-inverse-right rotate180 northEast = refl
  direction-inverse-right rotate180 east = refl
  direction-inverse-right rotate180 southEast = refl
  direction-inverse-right rotate180 south = refl
  direction-inverse-right rotate180 southWest = refl
  direction-inverse-right rotate180 west = refl
  direction-inverse-right rotate180 northWest = refl
  direction-inverse-right rotate270 north = refl
  direction-inverse-right rotate270 northEast = refl
  direction-inverse-right rotate270 east = refl
  direction-inverse-right rotate270 southEast = refl
  direction-inverse-right rotate270 south = refl
  direction-inverse-right rotate270 southWest = refl
  direction-inverse-right rotate270 west = refl
  direction-inverse-right rotate270 northWest = refl
  direction-inverse-right reflectVertical north = refl
  direction-inverse-right reflectVertical northEast = refl
  direction-inverse-right reflectVertical east = refl
  direction-inverse-right reflectVertical southEast = refl
  direction-inverse-right reflectVertical south = refl
  direction-inverse-right reflectVertical southWest = refl
  direction-inverse-right reflectVertical west = refl
  direction-inverse-right reflectVertical northWest = refl
  direction-inverse-right reflectDiagonal north = refl
  direction-inverse-right reflectDiagonal northEast = refl
  direction-inverse-right reflectDiagonal east = refl
  direction-inverse-right reflectDiagonal southEast = refl
  direction-inverse-right reflectDiagonal south = refl
  direction-inverse-right reflectDiagonal southWest = refl
  direction-inverse-right reflectDiagonal west = refl
  direction-inverse-right reflectDiagonal northWest = refl
  direction-inverse-right reflectHorizontal north = refl
  direction-inverse-right reflectHorizontal northEast = refl
  direction-inverse-right reflectHorizontal east = refl
  direction-inverse-right reflectHorizontal southEast = refl
  direction-inverse-right reflectHorizontal south = refl
  direction-inverse-right reflectHorizontal southWest = refl
  direction-inverse-right reflectHorizontal west = refl
  direction-inverse-right reflectHorizontal northWest = refl
  direction-inverse-right reflectAntiDiagonal north = refl
  direction-inverse-right reflectAntiDiagonal northEast = refl
  direction-inverse-right reflectAntiDiagonal east = refl
  direction-inverse-right reflectAntiDiagonal southEast = refl
  direction-inverse-right reflectAntiDiagonal south = refl
  direction-inverse-right reflectAntiDiagonal southWest = refl
  direction-inverse-right reflectAntiDiagonal west = refl
  direction-inverse-right reflectAntiDiagonal northWest = refl

  any-directions : ∀ σ f → any (λ d → f (direction σ d)) directions ≡ any f directions
  any-directions σ f = bool-ext _ _ forward backward
    where
    forward : any (λ d → f (direction σ d)) directions ≡ true → any f directions ≡ true
    forward p with any-witness (λ d → f (direction σ d)) directions p
    ... | d , (mem , fd) = any-member f (direction-member (direction σ d)) fd
    backward : any f directions ≡ true → any (λ d → f (direction σ d)) directions ≡ true
    backward p with any-witness f directions p
    ... | d , (mem , fd) = any-member (λ e → f (direction σ e))
      (direction-member (direction (inverse σ) d))
      (trans (cong f (direction-inverse-right σ d)) fd)

  nonempty-append : ∀ {A : Set} (xs ys : List A) → nonempty (xs ++ ys) ≡ nonempty xs ∨ nonempty ys
  nonempty-append [] ys = refl
  nonempty-append (x ∷ xs) ys = refl

  nonempty-map : ∀ {A B : Set} (f : A → B) xs → nonempty (map f xs) ≡ nonempty xs
  nonempty-map f [] = refl
  nonempty-map f (x ∷ xs) = refl

  nonempty-concatMap : ∀ {A B : Set} (f : A → List B) xs → nonempty (concatMap f xs) ≡ any (λ x → nonempty (f x)) xs
  nonempty-concatMap f [] = refl
  nonempty-concatMap f (x ∷ xs) rewrite nonempty-append (f x) (concatMap f xs) | nonempty-concatMap f xs = refl

  ∨-assoc : ∀ a b c → (a ∨ b) ∨ c ≡ a ∨ (b ∨ c)
  ∨-assoc false b c = refl
  ∨-assoc true b c = refl

  contains-append : ∀ {size} q (xs ys : List (Coord size)) → contains q (xs ++ ys) ≡ contains q xs ∨ contains q ys
  contains-append q [] ys = refl
  contains-append q (x ∷ xs) ys rewrite contains-append q xs ys = sym (∨-assoc (sameCoord q x) (contains q xs) (contains q ys))

  contains-concatMap : ∀ {A : Set} {size} q (f : A → List (Coord size)) xs →
    contains q (concatMap f xs) ≡ any (λ x → contains q (f x)) xs
  contains-concatMap q f [] = refl
  contains-concatMap q f (x ∷ xs) rewrite contains-append q (f x) (concatMap f xs) | contains-concatMap q f xs = refl

allCaptures-nonempty : ∀ σ s q →
  nonempty (allCaptures {size = six} (transformState σ s) (coordinate σ q)) ≡ nonempty (allCaptures {size = six} s q)
allCaptures-nonempty σ (state b p) q = trans
  (nonempty-concatMap transformed directions)
  (trans (sym (any-directions σ (λ d → nonempty (transformed d))))
    (trans (any-cong (λ d → nonempty (transformed (direction σ d)))
      (λ d → nonempty (original d)) directions
      (λ d → trans (cong nonempty (captures-equivariant σ b p d q)) (nonempty-map (coordinate σ) (original d))))
      (sym (nonempty-concatMap original directions))))
  where
  original = λ d → captures {size = six} b p d q
  transformed = λ d → captures {size = six} (transformBoard σ b) p d (coordinate σ q)

allCaptures-contains : ∀ σ s q r →
  contains {size = six} (coordinate σ r) (allCaptures {size = six} (transformState σ s) (coordinate σ q)) ≡ contains {size = six} r (allCaptures {size = six} s q)
allCaptures-contains σ (state b p) q r = trans
  (contains-concatMap {size = six} (coordinate σ r) transformed directions)
  (trans (sym (any-directions σ (λ d → contains {size = six} (coordinate σ r) (transformed d))))
    (trans (any-cong (λ d → contains {size = six} (coordinate σ r) (transformed (direction σ d)))
      (λ d → contains {size = six} r (original d)) directions
      (λ d → trans (cong (contains {size = six} (coordinate σ r)) (captures-equivariant σ b p d q)) (contains-map σ r (original d))))
      (sym (contains-concatMap {size = six} r original directions))))
  where
  original = λ d → captures {size = six} b p d q
  transformed = λ d → captures {size = six} (transformBoard σ b) p d (coordinate σ q)

legal-equivariant : ∀ σ s q → legal {size = six} (transformState σ s) (coordinate σ q) ≡ legal {size = six} s q
legal-equivariant σ (state b p) q rewrite at-forward σ b q | allCaptures-nonempty σ (state b p) q = refl

private
  choose : ∀ {A : Set} → Bool → A → A → A
  choose false x y = y
  choose true x y = x

  lookup-update : ∀ {A : Set} {n} (xs : V.Vec A n) i j f →
    V.lookup (V.updateAt xs i f) j ≡ choose (V.toℕ j ≡ᵇ V.toℕ i) (f (V.lookup xs j)) (V.lookup xs j)
  lookup-update (x V.∷ xs) V.zero V.zero f = refl
  lookup-update (x V.∷ xs) V.zero (V.suc j) f = refl
  lookup-update (x V.∷ xs) (V.suc i) V.zero f = refl
  lookup-update (x V.∷ xs) (V.suc i) (V.suc j) f = lookup-update xs i j f

  at-put : ∀ (b : Board six) q v r →
    at {size = six} (put {size = six} b q v) r ≡ choose (sameCoord {size = six} r q) v (at {size = six} b r)
  at-put b (r , c) v (r′ , c′)
    rewrite lookup-update b r r′ (λ row → V.updateAt row c (λ _ → v))
    with V.toℕ r′ ≡ᵇ V.toℕ r
  ... | false = refl
  ... | true = lookup-update (V.lookup b r′) c c′ (λ _ → v)

  board-ext-forward : ∀ σ (b c : Board six) →
    (∀ q → at {size = six} b (coordinate σ q) ≡ at {size = six} c (coordinate σ q)) → b ≡ c
  board-ext-forward σ b c eq = board-ext b c (λ r → trans
    (sym (cong (at {size = six} b) (coordinate-inverse-right σ r)))
    (trans (eq (coordinate (inverse σ) r))
      (cong (at {size = six} c) (coordinate-inverse-right σ r))))

put-equivariant : ∀ σ (b : Board six) q v →
  transformBoard σ (put {size = six} b q v) ≡ put {size = six} (transformBoard σ b) (coordinate σ q) v
put-equivariant σ b q v = board-ext-forward σ _ _ equal
  where
  equal : ∀ r → at {size = six} (transformBoard σ (put {size = six} b q v)) (coordinate σ r) ≡
    at {size = six} (put {size = six} (transformBoard σ b) (coordinate σ q) v) (coordinate σ r)
  equal r = trans (at-forward σ (put {size = six} b q v) r)
    (trans (at-put b q v r)
      (sym (trans (at-put (transformBoard σ b) (coordinate σ q) v (coordinate σ r))
        (trans (cong (λ test → choose test v (at {size = six} (transformBoard σ b) (coordinate σ r))) (sameCoord-equivariant σ r q))
          (cong (choose (sameCoord {size = six} r q) v) (at-forward σ b r))))))

private
  at-flipped : ∀ (s : State six) q r → at {size = six} (flippedBoard {size = six} s q) r ≡
    recolour {size = six} (toMove s) (allCaptures {size = six} s q) r (at {size = six} (board s) r)
  at-flipped s q (r , c) = trans
    (cong (λ row → V.lookup row c)
      (V.lookup-tabulate (λ r → V.tabulate (λ c → recolour {size = six} (toMove s)
        (allCaptures {size = six} s q) (r , c) (at {size = six} (board s) (r , c)))) r))
    (V.lookup-tabulate (λ c → recolour {size = six} (toMove s) (allCaptures {size = six} s q)
      (r , c) (at {size = six} (board s) (r , c))) c)

  recolour-covariant : ∀ σ (s : State six) q r c →
    recolour {size = six} (toMove s) (allCaptures {size = six} (transformState σ s) (coordinate σ q)) (coordinate σ r) c ≡
    recolour {size = six} (toMove s) (allCaptures {size = six} s q) r c
  recolour-covariant σ s q r empty = refl
  recolour-covariant σ s q r blackCell rewrite allCaptures-contains σ s q r = refl
  recolour-covariant σ s q r whiteCell rewrite allCaptures-contains σ s q r = refl

flippedBoard-equivariant : ∀ σ (s : State six) q →
  transformBoard σ (flippedBoard {size = six} s q) ≡ flippedBoard {size = six} (transformState σ s) (coordinate σ q)
flippedBoard-equivariant σ (state b p) q = board-ext-forward σ _ _ equal
  where
  equal : ∀ r → at {size = six} (transformBoard σ (flippedBoard {size = six} (state b p) q)) (coordinate σ r) ≡
    at {size = six} (flippedBoard {size = six} (transformState σ (state b p)) (coordinate σ q)) (coordinate σ r)
  equal r = trans (at-forward σ (flippedBoard {size = six} (state b p) q) r)
    (trans (at-flipped (state b p) q r)
      (sym (trans (at-flipped (transformState σ (state b p)) (coordinate σ q) (coordinate σ r))
        (trans (cong (recolour {size = six} p (allCaptures {size = six} (transformState σ (state b p)) (coordinate σ q)) (coordinate σ r)) (at-forward σ b r))
          (recolour-covariant σ (state b p) q r (at {size = six} b r))))))

applyMove-equivariant : ∀ σ (s : State six) q →
  transformState σ (applyMove {size = six} s q) ≡ applyMove {size = six} (transformState σ s) (coordinate σ q)
applyMove-equivariant σ (state b p) q rewrite legal-equivariant σ (state b p) q with legal {size = six} (state b p) q
... | false = refl
... | true = cong (λ c → state c (other p))
  (trans (put-equivariant σ (flippedBoard {size = six} (state b p) q) q (playerCell p))
    (cong (λ c → put {size = six} c (coordinate σ q) (playerCell p)) (flippedBoard-equivariant σ (state b p) q)))
