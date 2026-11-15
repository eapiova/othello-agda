{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Concrete enumeration, pass, and count laws for all D4 actions.
module Othello.SymmetryEnumeration6 where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Game.Permutation
open import Othello.Board
open import Othello.Rules
open import Othello.Symmetry6
open import Othello.SymmetryRules6
open import Othello.Statements using (lowerGoal; upperGoal)
import Othello.Finite as V
import Othello.Counting as C

-- Each schedule promotes the target cell to the head of the remaining list.
-- Reduction checks the full 36-cell result, independently of any board.
coordinates-perm : ∀ σ → Perm (map (coordinate σ) (coords six)) (coords six)
coordinates-perm identity = perm-reorder (0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ []) _
coordinates-perm rotate90 = perm-reorder (30 ∷ 24 ∷ 18 ∷ 12 ∷ 6 ∷ 0 ∷ 25 ∷ 20 ∷ 15 ∷ 10 ∷ 5 ∷ 0 ∷ 20 ∷ 16 ∷ 12 ∷ 8 ∷ 4 ∷ 0 ∷ 15 ∷ 12 ∷ 9 ∷ 6 ∷ 3 ∷ 0 ∷ 10 ∷ 8 ∷ 6 ∷ 4 ∷ 2 ∷ 0 ∷ 5 ∷ 4 ∷ 3 ∷ 2 ∷ 1 ∷ 0 ∷ []) _
coordinates-perm rotate180 = perm-reorder (35 ∷ 34 ∷ 33 ∷ 32 ∷ 31 ∷ 30 ∷ 29 ∷ 28 ∷ 27 ∷ 26 ∷ 25 ∷ 24 ∷ 23 ∷ 22 ∷ 21 ∷ 20 ∷ 19 ∷ 18 ∷ 17 ∷ 16 ∷ 15 ∷ 14 ∷ 13 ∷ 12 ∷ 11 ∷ 10 ∷ 9 ∷ 8 ∷ 7 ∷ 6 ∷ 5 ∷ 4 ∷ 3 ∷ 2 ∷ 1 ∷ 0 ∷ []) _
coordinates-perm rotate270 = perm-reorder (5 ∷ 10 ∷ 15 ∷ 20 ∷ 25 ∷ 30 ∷ 4 ∷ 8 ∷ 12 ∷ 16 ∷ 20 ∷ 24 ∷ 3 ∷ 6 ∷ 9 ∷ 12 ∷ 15 ∷ 18 ∷ 2 ∷ 4 ∷ 6 ∷ 8 ∷ 10 ∷ 12 ∷ 1 ∷ 2 ∷ 3 ∷ 4 ∷ 5 ∷ 6 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ []) _
coordinates-perm reflectVertical = perm-reorder (5 ∷ 4 ∷ 3 ∷ 2 ∷ 1 ∷ 0 ∷ 5 ∷ 4 ∷ 3 ∷ 2 ∷ 1 ∷ 0 ∷ 5 ∷ 4 ∷ 3 ∷ 2 ∷ 1 ∷ 0 ∷ 5 ∷ 4 ∷ 3 ∷ 2 ∷ 1 ∷ 0 ∷ 5 ∷ 4 ∷ 3 ∷ 2 ∷ 1 ∷ 0 ∷ 5 ∷ 4 ∷ 3 ∷ 2 ∷ 1 ∷ 0 ∷ []) _
coordinates-perm reflectDiagonal = perm-reorder (0 ∷ 5 ∷ 10 ∷ 15 ∷ 20 ∷ 25 ∷ 0 ∷ 4 ∷ 8 ∷ 12 ∷ 16 ∷ 20 ∷ 0 ∷ 3 ∷ 6 ∷ 9 ∷ 12 ∷ 15 ∷ 0 ∷ 2 ∷ 4 ∷ 6 ∷ 8 ∷ 10 ∷ 0 ∷ 1 ∷ 2 ∷ 3 ∷ 4 ∷ 5 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ []) _
coordinates-perm reflectHorizontal = perm-reorder (30 ∷ 30 ∷ 30 ∷ 30 ∷ 30 ∷ 30 ∷ 24 ∷ 24 ∷ 24 ∷ 24 ∷ 24 ∷ 24 ∷ 18 ∷ 18 ∷ 18 ∷ 18 ∷ 18 ∷ 18 ∷ 12 ∷ 12 ∷ 12 ∷ 12 ∷ 12 ∷ 12 ∷ 6 ∷ 6 ∷ 6 ∷ 6 ∷ 6 ∷ 6 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ 0 ∷ []) _
coordinates-perm reflectAntiDiagonal = perm-reorder (35 ∷ 29 ∷ 23 ∷ 17 ∷ 11 ∷ 5 ∷ 29 ∷ 24 ∷ 19 ∷ 14 ∷ 9 ∷ 4 ∷ 23 ∷ 19 ∷ 15 ∷ 11 ∷ 7 ∷ 3 ∷ 17 ∷ 14 ∷ 11 ∷ 8 ∷ 5 ∷ 2 ∷ 11 ∷ 9 ∷ 7 ∷ 5 ∷ 3 ∷ 1 ∷ 5 ∷ 4 ∷ 3 ∷ 2 ∷ 1 ∷ 0 ∷ []) _

private
  perm-select : ∀ {A : Set} (f : A → Bool) {xs ys} → Perm xs ys → Perm (select f xs) (select f ys)
  perm-select f nil = nil
  perm-select f (skip {x = x} p) with f x
  ... | false = perm-select f p
  ... | true = skip (perm-select f p)
  perm-select f (swap {x = x} {y = y} {xs = xs}) with f x in fx | f y in fy
  ... | false | false rewrite fx | fy = perm-refl (select f xs)
  ... | false | true rewrite fx | fy = perm-refl (y ∷ select f xs)
  ... | true | false rewrite fx | fy = perm-refl (x ∷ select f xs)
  ... | true | true rewrite fx | fy = swap
  perm-select f (chain p q) = chain (perm-select f p) (perm-select f q)

  select-map : ∀ {A B : Set} (f : A → B) (p : B → Bool) (q : A → Bool) xs →
    (∀ x → p (f x) ≡ q x) → select p (map f xs) ≡ map f (select q xs)
  select-map f p q [] eq = refl
  select-map f p q (x ∷ xs) eq rewrite eq x with q x
  ... | false = select-map f p q xs eq
  ... | true = cong (λ ys → f x ∷ ys) (select-map f p q xs eq)

  map-compose : ∀ {A B D : Set} (f : B → D) (g : A → B) xs →
    map f (map g xs) ≡ map (λ x → f (g x)) xs
  map-compose f g [] = refl
  map-compose f g (x ∷ xs) = cong (λ ys → f (g x) ∷ ys) (map-compose f g xs)

  map-cong : ∀ {A B : Set} (f g : A → B) xs → (∀ x → f x ≡ g x) → map f xs ≡ map g xs
  map-cong f g [] eq = refl
  map-cong f g (x ∷ xs) eq rewrite eq x | map-cong f g xs eq = refl

  nonempty-perm : ∀ {A : Set} {xs ys : List A} → Perm xs ys → nonempty xs ≡ nonempty ys
  nonempty-perm nil = refl
  nonempty-perm (skip p) = refl
  nonempty-perm swap = refl
  nonempty-perm (chain p q) = trans (nonempty-perm p) (nonempty-perm q)

legalMoves-perm : ∀ σ s → Perm (map (coordinate σ) (legalMoves {size = six} s))
  (legalMoves {size = six} (transformState σ s))
legalMoves-perm σ s = subst (λ xs → Perm xs (legalMoves {size = six} (transformState σ s)))
  (select-map (coordinate σ) (legal {size = six} (transformState σ s)) (legal {size = six} s)
    (coords six) (legal-equivariant σ s))
  (perm-select (legal {size = six} (transformState σ s)) (coordinates-perm σ))

legalMoves-nonempty : ∀ σ s → nonempty (legalMoves {size = six} (transformState σ s)) ≡
  nonempty (legalMoves {size = six} s)
legalMoves-nonempty σ s = trans (sym (nonempty-perm (legalMoves-perm σ s))) map-nonempty
  where
  map-nonempty : nonempty (map (coordinate σ) (legalMoves {size = six} s)) ≡ nonempty (legalMoves {size = six} s)
  map-nonempty with legalMoves {size = six} s
  ... | [] = refl
  ... | q ∷ qs = refl

private
  passFlag : Bool → Bool → Bool
  passFlag false true = true
  passFlag _ _ = false

  forcedPass-normal : ∀ (s : State six) → forcedPass s ≡
    passFlag (nonempty (legalMoves s)) (nonempty (legalMoves (passState s)))
  forcedPass-normal s with legalMoves s | legalMoves (passState s)
  ... | [] | [] = refl
  ... | [] | q ∷ qs = refl
  ... | q ∷ qs | [] = refl
  ... | q ∷ qs | r ∷ rs = refl

  nextForm : State six → Bool → Bool → List (State six)
  nextForm s true b = map (applyMove s) (legalMoves s)
  nextForm s false true = passState s ∷ []
  nextForm s false false = []

  successors-normal : ∀ (s : State six) → successors s ≡
    nextForm s (nonempty (legalMoves s)) (nonempty (legalMoves (passState s)))
  successors-normal s with legalMoves s in lm | legalMoves (passState s) in lp
  ... | [] | [] rewrite lm | lp = refl
  ... | [] | q ∷ qs rewrite lm | lp = refl
  ... | q ∷ qs | [] rewrite lm | lp = refl
  ... | q ∷ qs | r ∷ rs rewrite lm | lp = refl

  passMoves-nonempty : ∀ σ s → nonempty (legalMoves {size = six} (passState (transformState σ s))) ≡
    nonempty (legalMoves {size = six} (passState s))
  passMoves-nonempty σ s = trans (cong (λ t → nonempty (legalMoves {size = six} t))
    (sym (passState-equivariant σ s))) (legalMoves-nonempty σ (passState s))

forcedPass-equivariant : ∀ σ s → forcedPass {size = six} (transformState σ s) ≡ forcedPass {size = six} s
forcedPass-equivariant σ s rewrite forcedPass-normal (transformState σ s) | forcedPass-normal s
  | legalMoves-nonempty σ s | passMoves-nonempty σ s = refl

successors-perm : ∀ σ s → Perm (map (transformState σ) (successors {size = six} s))
  (successors {size = six} (transformState σ s))
successors-perm σ s rewrite successors-normal s | successors-normal (transformState σ s)
  | legalMoves-nonempty σ s | passMoves-nonempty σ s
  with nonempty (legalMoves {size = six} s) | nonempty (legalMoves {size = six} (passState s))
... | false | false = nil
... | false | true = subst (λ t → Perm (t ∷ []) (passState {size = six} (transformState σ s) ∷ []))
  (sym (passState-equivariant σ s)) (skip nil)
... | true | b = subst (λ xs → Perm xs (map (applyMove {size = six} (transformState σ s))
    (legalMoves {size = six} (transformState σ s)))) (sym mapped)
  (perm-map (applyMove {size = six} (transformState σ s)) (legalMoves-perm σ s))
  where
  mapped : map (transformState σ) (map (applyMove {size = six} s) (legalMoves {size = six} s)) ≡
    map (applyMove {size = six} (transformState σ s)) (map (coordinate σ) (legalMoves {size = six} s))
  mapped = trans (map-compose (transformState σ) (applyMove {size = six} s) (legalMoves {size = six} s))
    (trans (map-cong (λ q → transformState σ (applyMove {size = six} s q))
      (λ q → applyMove {size = six} (transformState σ s) (coordinate σ q))
      (legalMoves {size = six} s) (applyMove-equivariant σ s))
      (sym (map-compose (applyMove {size = six} (transformState σ s)) (coordinate σ) (legalMoves {size = six} s))))

terminal-equivariant : ∀ σ s → nonempty (successors {size = six} (transformState σ s)) ≡
  nonempty (successors {size = six} s)
terminal-equivariant σ s = trans (sym (nonempty-perm (successors-perm σ s))) shape
  where
  shape : nonempty (map (transformState σ) (successors {size = six} s)) ≡ nonempty (successors {size = six} s)
  shape with successors {size = six} s
  ... | [] = refl
  ... | t ∷ ts = refl

private
  +-zero : ∀ n → n + zero ≡ n
  +-zero zero = refl
  +-zero (suc n) = cong suc (+-zero n)

  +-assoc : ∀ a b c → (a + b) + c ≡ a + (b + c)
  +-assoc zero b c = refl
  +-assoc (suc a) b c = cong suc (+-assoc a b c)

  +-comm : ∀ a b → a + b ≡ b + a
  +-comm zero b = sym (+-zero b)
  +-comm (suc a) b = trans (cong suc (+-comm a b)) (sym (C.+-suc b a))

  listCount : ∀ {A : Set} → (A → ℕ) → List A → ℕ
  listCount f [] = zero
  listCount f (x ∷ xs) = f x + listCount f xs

  listCount-perm : ∀ {A : Set} (f : A → ℕ) {xs ys} → Perm xs ys → listCount f xs ≡ listCount f ys
  listCount-perm f nil = refl
  listCount-perm f (skip {x = x} p) = cong (λ n → f x + n) (listCount-perm f p)
  listCount-perm f (swap {x = x} {y = y} {xs = xs}) =
    trans (sym (+-assoc (f x) (f y) (listCount f xs)))
      (trans (cong (λ n → n + listCount f xs) (+-comm (f x) (f y)))
        (+-assoc (f y) (f x) (listCount f xs)))
  listCount-perm f (chain p q) = trans (listCount-perm f p) (listCount-perm f q)

  listCount-cong : ∀ {A : Set} (f g : A → ℕ) xs → (∀ x → f x ≡ g x) → listCount f xs ≡ listCount g xs
  listCount-cong f g [] eq = refl
  listCount-cong f g (x ∷ xs) eq rewrite eq x | listCount-cong f g xs eq = refl

  listCount-map : ∀ {A B : Set} (f : B → ℕ) (g : A → B) xs →
    listCount f (map g xs) ≡ listCount (λ x → f (g x)) xs
  listCount-map f g [] = refl
  listCount-map f g (x ∷ xs) = cong (λ n → f (g x) + n) (listCount-map f g xs)

  listCount-append : ∀ {A : Set} (f : A → ℕ) xs ys →
    listCount f (xs ++ ys) ≡ listCount f xs + listCount f ys
  listCount-append f [] ys = refl
  listCount-append f (x ∷ xs) ys = trans (cong (λ n → f x + n) (listCount-append f xs ys))
    (sym (+-assoc (f x) (listCount f xs) (listCount f ys)))

  listCount-concatMap : ∀ {A B : Set} (f : B → ℕ) (g : A → List B) xs →
    listCount f (concatMap g xs) ≡ listCount (λ x → listCount f (g x)) xs
  listCount-concatMap f g [] = refl
  listCount-concatMap f g (x ∷ xs) rewrite listCount-append f (g x) (concatMap g xs)
    | listCount-concatMap f g xs = refl

  listCount-vector : ∀ {A : Set} {n} (f : A → ℕ) (xs : V.Vec A n) →
    listCount f (V.toList xs) ≡ C.count f xs
  listCount-vector f V.[] = refl
  listCount-vector f (x V.∷ xs) = cong (λ n → f x + n) (listCount-vector f xs)

  map-tabulate-list : ∀ {A B : Set} {n} (f : A → B) (g : V.Fin n → A) →
    map f (V.toList (V.tabulate g)) ≡ V.toList (V.tabulate (λ i → f (g i)))
  map-tabulate-list {n = zero} f g = refl
  map-tabulate-list {n = suc n} f g = cong (λ xs → f (g V.zero) ∷ xs)
    (map-tabulate-list f (λ i → g (V.suc i)))

  listCount-fin : ∀ {n} (f : V.Fin n → ℕ) →
    listCount f (V.toList (V.allFin n)) ≡ C.sum (V.tabulate f)
  listCount-fin f = trans (sym (listCount-map (λ x → x) f (V.toList (V.allFin _))))
    (trans (cong (listCount (λ x → x)) (map-tabulate-list f (λ x → x)))
      (listCount-vector (λ x → x) (V.tabulate f)))

  listCount-lookup : ∀ {A : Set} {n} (f : A → ℕ) (xs : V.Vec A n) →
    listCount (λ i → f (V.lookup xs i)) (V.toList (V.allFin n)) ≡ C.count f xs
  listCount-lookup f xs = trans (listCount-fin (λ i → f (V.lookup xs i))) (C.count-tabulate-lookup f xs)

  board-enumeration : ∀ (f : Cell → ℕ) (b : Board six) →
    listCount (λ q → f (at {size = six} b q)) (coords six) ≡ countBoard {size = six} f b
  board-enumeration f b = trans
    (listCount-concatMap (λ q → f (at {size = six} b q))
      (λ r → map (λ c → r , c) (V.toList (V.allFin 6))) (V.toList (V.allFin 6)))
    (trans (listCount-cong
      (λ r → listCount (λ q → f (at {size = six} b q)) (map (λ c → r , c) (V.toList (V.allFin 6))))
      (λ r → C.count f (V.lookup b r)) (V.toList (V.allFin 6))
      (λ r → trans (listCount-map (λ q → f (at {size = six} b q)) (λ c → r , c) (V.toList (V.allFin 6)))
        (listCount-lookup f (V.lookup b r))))
      (listCount-lookup (C.count f) b))

countBoard-invariant : ∀ σ f b → countBoard {size = six} f (transformBoard σ b) ≡ countBoard {size = six} f b
countBoard-invariant σ f b = trans (sym (board-enumeration f (transformBoard σ b)))
  (trans (sym (listCount-perm (λ q → f (at {size = six} (transformBoard σ b) q)) (coordinates-perm σ)))
    (trans (listCount-map (λ q → f (at {size = six} (transformBoard σ b) q)) (coordinate σ) (coords six))
      (trans (listCount-cong (λ q → f (at {size = six} (transformBoard σ b) (coordinate σ q)))
        (λ q → f (at {size = six} b q)) (coords six) (λ q → cong f (at-forward σ b q)))
        (board-enumeration f b))))

discs-invariant : ∀ σ p s → discs {size = six} p (transformState σ s) ≡ discs {size = six} p s
discs-invariant σ p (state b t) = countBoard-invariant σ (λ c → indicator (sameCell c (playerCell p))) b

empties-invariant : ∀ σ s → empties {size = six} (transformState σ s) ≡ empties {size = six} s
empties-invariant σ (state b p) = countBoard-invariant σ emptyCell b

occupied-invariant : ∀ σ s → occupied {size = six} (transformState σ s) ≡ occupied {size = six} s
occupied-invariant σ (state b p) = countBoard-invariant σ occupiedCell b

score-invariant : ∀ σ s → score {size = six} (transformState σ s) ≡ score {size = six} s
score-invariant σ s rewrite discs-invariant σ white s | discs-invariant σ black s = refl

lowerGoal-invariant : ∀ σ v s → lowerGoal {size = six} v (transformState σ s) ≡ lowerGoal {size = six} v s
lowerGoal-invariant σ v s rewrite discs-invariant σ white s | discs-invariant σ black s = refl

upperGoal-invariant : ∀ σ v s → upperGoal {size = six} v (transformState σ s) ≡ upperGoal {size = six} v s
upperGoal-invariant σ v s rewrite discs-invariant σ white s | discs-invariant σ black s = refl

lowerGoal4-invariant : ∀ σ s → lowerGoal {size = six} 4 (transformState σ s) ≡ lowerGoal {size = six} 4 s
lowerGoal4-invariant σ = lowerGoal-invariant σ 4

upperGoal4-invariant : ∀ σ s → upperGoal {size = six} 4 (transformState σ s) ≡ upperGoal {size = six} 4 s
upperGoal4-invariant σ = upperGoal-invariant σ 4
