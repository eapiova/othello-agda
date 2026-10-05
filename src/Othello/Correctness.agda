{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Othello.Correctness where

open import Prelude
open import Othello.Board
open import Othello.Rules
open import Othello.Finite as Fin using (Fin; toℕ)

-- These relations describe the discs themselves, rather than the Boolean
-- implementation. A bracket consists of at least one opponent, followed by
-- zero or more opponents and a friendly endpoint on the geometric ray.
data BracketTail {size} (b : Board size) (p : Player) :
  List (Coord size) → List (Coord size) → Set where
  endpoint : ∀ {q qs} → at b q ≡ playerCell p →
    BracketTail b p (q ∷ qs) []
  opponent : ∀ {q qs xs} → at b q ≡ playerCell (other p) →
    BracketTail b p qs xs → BracketTail b p (q ∷ qs) (q ∷ xs)

data Bracket {size} (b : Board size) (p : Player) (d : Direction)
  (q : Coord size) : List (Coord size) → Set where
  bracket : ∀ {r rs xs} → ray d q ≡ r ∷ rs →
    at b r ≡ playerCell (other p) → BracketTail b p rs xs →
    Bracket b p d q (r ∷ xs)

record Legal {size} (s : State size) (q : Coord size) : Set where
  constructor legalWitness
  field
    vacant : at (board s) q ≡ empty
    bracketed : Σ Direction (λ d → Σ (List (Coord size))
      (λ xs → Bracket (board s) (toMove s) d q xs))
open Legal public

cell-reflects : ∀ {c d} → sameCell c d ≡ true → c ≡ d
cell-reflects {empty} {empty} refl = refl
cell-reflects {blackCell} {blackCell} refl = refl
cell-reflects {whiteCell} {whiteCell} refl = refl
cell-reflects {empty} {blackCell} ()
cell-reflects {empty} {whiteCell} ()
cell-reflects {blackCell} {empty} ()
cell-reflects {blackCell} {whiteCell} ()
cell-reflects {whiteCell} {empty} ()
cell-reflects {whiteCell} {blackCell} ()

cell-self : ∀ c → sameCell c c ≡ true
cell-self empty = refl
cell-self blackCell = refl
cell-self whiteCell = refl

other-not-self : ∀ p → sameCell (playerCell (other p)) (playerCell p) ≡ false
other-not-self black = refl
other-not-self white = refl

data ⊥ : Set where

absurd : ∀ {A : Set} → ⊥ → A
absurd ()

nothing-not-just : ∀ {A : Set} {x : A} → nothing ≡ just x → ⊥
nothing-not-just ()

false-not-true : false ≡ true → ⊥
false-not-true ()

just-injective : ∀ {A : Set} {x y : A} → just x ≡ just y → x ≡ y
just-injective refl = refl

scan-sound : ∀ {size} (b : Board size) p qs xs →
  scan b p qs ≡ just xs → BracketTail b p qs xs
scan-sound b p [] xs e = absurd (nothing-not-just e)
scan-sound b p (q ∷ qs) xs e with at b q in cell
... | empty = absurd (nothing-not-just e)
... | blackCell with p
... | black = subst (BracketTail b black (q ∷ qs)) (just-injective e) (endpoint cell)
... | white with scan b white qs in rest
... | nothing = absurd (nothing-not-just e)
... | just ys = subst (BracketTail b white (q ∷ qs)) (just-injective e)
  (opponent cell (scan-sound b white qs ys rest))
scan-sound b p (q ∷ qs) xs e | whiteCell with p
... | white = subst (BracketTail b white (q ∷ qs)) (just-injective e) (endpoint cell)
... | black with scan b black qs in rest
... | nothing = absurd (nothing-not-just e)
... | just ys = subst (BracketTail b black (q ∷ qs)) (just-injective e)
  (opponent cell (scan-sound b black qs ys rest))

scan-complete : ∀ {size} {b : Board size} {p qs xs} →
  BracketTail b p qs xs → scan b p qs ≡ just xs
scan-complete {p = black} (endpoint {q} e) rewrite e = refl
scan-complete {p = white} (endpoint {q} e) rewrite e = refl
scan-complete {p = black} (opponent {q} e tail) rewrite e | scan-complete tail = refl
scan-complete {p = white} (opponent {q} e tail) rewrite e | scan-complete tail = refl

captures-sound : ∀ {size} (b : Board size) p d q →
  nonempty (captures b p d q) ≡ true →
  Σ (List (Coord size)) (λ xs → Bracket b p d q xs)
captures-sound b p d q e with ray d q in ray-e
... | [] = absurd (false-not-true e)
... | r ∷ rs with sameCell (at b r) (playerCell (other p)) in opp
... | false = absurd (false-not-true e)
... | true with scan b p rs in scan-e
... | nothing = absurd (false-not-true e)
... | just xs = (r ∷ xs) , bracket ray-e (cell-reflects opp) (scan-sound b p rs xs scan-e)

captures-complete : ∀ {size} {b : Board size} {p d q xs} →
  Bracket b p d q xs → captures b p d q ≡ xs
captures-complete {p = black} (bracket ray-e opp tail)
  rewrite ray-e | opp | scan-complete tail = refl
captures-complete {p = white} (bracket ray-e opp tail)
  rewrite ray-e | opp | scan-complete tail = refl

bracket-nonempty : ∀ {size} {b : Board size} {p d q xs} →
  Bracket b p d q xs → nonempty xs ≡ true
bracket-nonempty (bracket _ _ _) = refl

infix 4 _∈_
data _∈_ {A : Set} (x : A) : List A → Set where
  here : ∀ {xs} → x ∈ (x ∷ xs)
  there : ∀ {y xs} → x ∈ xs → x ∈ (y ∷ xs)

append-left : ∀ {A : Set} {x : A} {xs} ys → x ∈ xs → x ∈ (xs ++ ys)
append-left ys here = here
append-left ys (there e) = there (append-left ys e)

append-right : ∀ {A : Set} {x : A} xs {ys} → x ∈ ys → x ∈ (xs ++ ys)
append-right [] e = e
append-right (_ ∷ xs) e = there (append-right xs e)

map-member : ∀ {A B : Set} (f : A → B) {x xs} → x ∈ xs → f x ∈ map f xs
map-member f here = here
map-member f (there e) = there (map-member f e)

concatMap-member : ∀ {A B : Set} (f : A → List B) {x y xs} →
  x ∈ xs → y ∈ f x → y ∈ concatMap f xs
concatMap-member f here e = append-left _ e
concatMap-member f (there m) e = append-right _ (concatMap-member f m e)

concatMap-nonempty : ∀ {A B : Set} (f : A → List B) xs →
  nonempty (concatMap f xs) ≡ true →
  Σ A (λ x → x ∈ xs × (nonempty (f x) ≡ true))
concatMap-nonempty f [] ()
concatMap-nonempty f (x ∷ xs) e with f x in fx
... | y ∷ ys = x , here , cong nonempty fx
... | [] with concatMap-nonempty f xs e
... | y , m , ne = y , there m , ne

nonempty-append-left : ∀ {A : Set} (xs ys : List A) →
  nonempty xs ≡ true → nonempty (xs ++ ys) ≡ true
nonempty-append-left [] ys ()
nonempty-append-left (_ ∷ _) ys e = refl

nonempty-append-right : ∀ {A : Set} (xs ys : List A) →
  nonempty ys ≡ true → nonempty (xs ++ ys) ≡ true
nonempty-append-right [] ys e = e
nonempty-append-right (_ ∷ _) ys e = refl

concatMap-nonempty-member : ∀ {A B : Set} (f : A → List B) {x xs} →
  x ∈ xs → nonempty (f x) ≡ true → nonempty (concatMap f xs) ≡ true
concatMap-nonempty-member f here e = nonempty-append-left _ _ e
concatMap-nonempty-member f (there m) e =
  nonempty-append-right _ _ (concatMap-nonempty-member f m e)

direction-member : ∀ d → d ∈ directions
direction-member north = here
direction-member northEast = there here
direction-member east = there (there here)
direction-member southEast = there (there (there here))
direction-member south = there (there (there (there here)))
direction-member southWest = there (there (there (there (there here))))
direction-member west = there (there (there (there (there (there here)))))
direction-member northWest = there (there (there (there (there (there (there here))))))

and-true-left : ∀ a b → a ∧ b ≡ true → a ≡ true
and-true-left false b ()
and-true-left true b e = refl

and-true-right : ∀ a b → a ∧ b ≡ true → b ≡ true
and-true-right false b ()
and-true-right true b e = e

legal-sound : ∀ {size} (s : State size) q → legal s q ≡ true → Legal s q
legal-sound s q e with concatMap-nonempty
  (λ d → captures (board s) (toMove s) d q) directions
  (and-true-right _ _ e)
... | d , m , ne = legalWitness (cell-reflects (and-true-left _ _ e))
  (d , captures-sound (board s) (toMove s) d q ne)

legal-complete : ∀ {size} {s : State size} {q} → Legal s q → legal s q ≡ true
legal-complete {s = s} {q} (legalWitness vacant (d , xs , bracketed))
  rewrite vacant = concatMap-nonempty-member
    (λ d → captures (board s) (toMove s) d q) (direction-member d)
    (trans (cong nonempty (captures-complete bracketed)) (bracket-nonempty bracketed))

select-sound : ∀ {A : Set} (f : A → Bool) {x xs} →
  x ∈ select f xs → x ∈ xs × (f x ≡ true)
select-sound f {xs = []} ()
select-sound f {xs = y ∷ ys} m with f y in fy
... | false = let result = select-sound f m in there (proj₁ result) , proj₂ result
... | true with m
... | here = here , fy
... | there in-rest = let result = select-sound f in-rest in there (proj₁ result) , proj₂ result

select-complete : ∀ {A : Set} (f : A → Bool) {x xs} →
  x ∈ xs → f x ≡ true → x ∈ select f xs
select-complete f {xs = y ∷ ys} m fx with f y in fy
... | false with m
... | here = absurd (false-not-true (trans (sym fy) fx))
... | there in-ys = select-complete f in-ys fx
select-complete f {xs = y ∷ ys} m fx | true with m
... | here = here
... | there in-ys = there (select-complete f in-ys fx)

-- Enumeration completeness is completed below from the finite enumeration.

tabulate-member : ∀ {A : Set} {n} (f : Fin n → A) i →
  f i ∈ Fin.toList (Fin.tabulate f)
tabulate-member f Fin.zero = here
tabulate-member f (Fin.suc i) = there (tabulate-member (λ j → f (Fin.suc j)) i)

coords-complete : ∀ {size} (q : Coord size) → q ∈ coords size
coords-complete {size} (r , c) = concatMap-member
  (λ r → map (λ c → r , c) (Fin.toList (Fin.allFin (dimension size))))
  (tabulate-member (λ i → i) r)
  (map-member (λ c → r , c) (tabulate-member (λ i → i) c))

legalMoves-sound : ∀ {size} (s : State size) {q} → q ∈ legalMoves s → Legal s q
legalMoves-sound {size} s {q} m = legal-sound s q
  (proj₂ (select-sound (legal s) {xs = coords size} m))

legalMoves-complete : ∀ {size} {s : State size} {q} → Legal s q → q ∈ legalMoves s
legalMoves-complete {s = s} {q} proof =
  select-complete (legal s) (coords-complete q) (legal-complete proof)

open import Agda.Builtin.Nat using (_+_)
open import Othello.Counting

cong₂ : ∀ {A B C : Set} (f : A → B → C) {a a′ b b′} →
  a ≡ a′ → b ≡ b′ → f a b ≡ f a′ b′
cong₂ f refl refl = refl

count-tabulate : ∀ {A : Set} {n} (f : A → ℕ) (g : Fin n → A) →
  count f (Fin.tabulate g) ≡ sum (Fin.tabulate (λ i → f (g i)))
count-tabulate {n = zero} f g = refl
count-tabulate {n = suc n} f g = cong (λ k → f (g Fin.zero) + k)
  (count-tabulate f (λ i → g (Fin.suc i)))

empty-player : ∀ p → emptyCell (playerCell p) ≡ zero
empty-player black = refl
empty-player white = refl

occupied-player : ∀ p → occupiedCell (playerCell p) ≡ 1
occupied-player black = refl
occupied-player white = refl

recolour-empty-count : ∀ {size} p xs (q : Coord size) c →
  emptyCell (recolour p xs q c) ≡ emptyCell c
recolour-empty-count p xs q empty = refl
recolour-empty-count p xs q blackCell with contains q xs
... | false = refl
... | true = empty-player p
recolour-empty-count p xs q whiteCell with contains q xs
... | false = refl
... | true = empty-player p

recolour-occupied-count : ∀ {size} p xs (q : Coord size) c →
  occupiedCell (recolour p xs q c) ≡ occupiedCell c
recolour-occupied-count p xs q empty = refl
recolour-occupied-count p xs q blackCell with contains q xs
... | false = refl
... | true = occupied-player p
recolour-occupied-count p xs q whiteCell with contains q xs
... | false = refl
... | true = occupied-player p

flip-count : ∀ {size} (f : Cell → ℕ) →
  (∀ p xs (q : Coord size) c → f (recolour p xs q c) ≡ f c) →
  (s : State size) (q : Coord size) → countBoard f (flippedBoard s q) ≡ countBoard f (board s)
flip-count f invariant s q = trans (count-tabulate (count f) rows)
  (trans (sum-tabulate-cong (λ r → count f (rows r))
    (λ r → count f (Fin.lookup (board s) r)) row-equal)
    (count-tabulate-lookup (count f) (board s)))
  where
  rows = λ r → Fin.tabulate (λ c → recolour (toMove s) (allCaptures s q)
    (r , c) (at (board s) (r , c)))
  row-equal = λ r → trans (count-tabulate f (λ c → recolour (toMove s)
      (allCaptures s q) (r , c) (at (board s) (r , c))))
    (trans (sum-tabulate-cong
      (λ c → f (recolour (toMove s) (allCaptures s q) (r , c) (at (board s) (r , c))))
      (λ c → f (at (board s) (r , c)))
      (λ c → invariant (toMove s) (allCaptures s q) (r , c) (at (board s) (r , c))))
      (count-tabulate-lookup f (Fin.lookup (board s) r)))

flipped-vacant : ∀ {size} (s : State size) q → at (board s) q ≡ empty →
  at (flippedBoard s q) q ≡ empty
flipped-vacant s (r , c) vacancy = trans
  (cong (λ row → Fin.lookup row c) (Fin.lookup-tabulate _ r))
  (trans (Fin.lookup-tabulate _ c)
    (cong (recolour (toMove s) (allCaptures s (r , c)) (r , c)) vacancy))

update-as-replace : ∀ {A : Set} {n} (xs : Fin.Vec A n) i f →
  Fin.updateAt xs i f ≡ Fin.updateAt xs i (λ _ → f (Fin.lookup xs i))
update-as-replace (x Fin.∷ xs) Fin.zero f = refl
update-as-replace (x Fin.∷ xs) (Fin.suc i) f =
  cong (λ ys → x Fin.∷ ys) (update-as-replace xs i f)

put-decreases : ∀ {size} (b : Board size) (q : Coord size) p →
  at b q ≡ empty → suc (countBoard emptyCell (put b q (playerCell p))) ≡ countBoard emptyCell b
put-decreases b (r , c) p vacancy = trans
  (cong (λ rows → suc (countBoard emptyCell rows)) (update-as-replace b r _))
  (replace-decreases (count emptyCell) b r
    (Fin.updateAt (Fin.lookup b r) c (λ _ → playerCell p))
    (replace-decreases emptyCell (Fin.lookup b r) c (playerCell p)
      (trans (cong suc (empty-player p)) (sym (cong emptyCell vacancy)))))

put-increases : ∀ {size} (b : Board size) (q : Coord size) p →
  at b q ≡ empty → countBoard occupiedCell (put b q (playerCell p)) ≡ suc (countBoard occupiedCell b)
put-increases b (r , c) p vacancy = trans
  (cong (countBoard occupiedCell) (update-as-replace b r _))
  (replace-increases (count occupiedCell) b r
    (Fin.updateAt (Fin.lookup b r) c (λ _ → playerCell p))
    (replace-increases occupiedCell (Fin.lookup b r) c (playerCell p)
      (trans (occupied-player p) (sym (cong (λ x → suc (occupiedCell x)) vacancy)))))

placement-decreases-empties : ∀ {size} (s : State size) q → legal s q ≡ true →
  suc (empties (applyMove s q)) ≡ empties s
placement-decreases-empties s q legal-e with legal s q in computed
... | false = absurd (false-not-true legal-e)
... | true = trans (put-decreases (flippedBoard s q) q (toMove s)
  (flipped-vacant s q (vacant (legal-sound s q computed))))
  (flip-count emptyCell recolour-empty-count s q)

placement-increases-occupied : ∀ {size} (s : State size) q → legal s q ≡ true →
  occupied (applyMove s q) ≡ suc (occupied s)
placement-increases-occupied s q legal-e with legal s q in computed
... | false = absurd (false-not-true legal-e)
... | true = trans (put-increases (flippedBoard s q) q (toMove s)
  (flipped-vacant s q (vacant (legal-sound s q computed))))
  (cong suc (flip-count occupiedCell recolour-occupied-count s q))

-- No transport or resizing is involved: every constructor returns precisely
-- the same nested finite-vector type as the input.
applyMove-board-shape : ∀ {size} (s : State size) q →
  Fin.Vec (Fin.Vec Cell (dimension size)) (dimension size)
applyMove-board-shape s q = board (applyMove s q)
