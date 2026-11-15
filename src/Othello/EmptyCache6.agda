{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. A checked cache of empty coordinates for six-by-six states.
-- This module proves only cache maintenance; it asserts no game value.
module Othello.EmptyCache6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (coords; passState)
import Othello.Finite as F
import Othello.Fast6 as Fast
import Othello.Incremental6 as Inc
import Othello.Encode6 as Encode
open import Game.Composite using (StateEquality; stateEquality; equal; equal-sound)
import Game.BooleanRecompute as Recompute

not : Bool → Bool
not false = true
not true = false

select : ∀ {A : Set} → (A → Bool) → List A → List A
select f [] = []
select f (x ∷ xs) with f x
... | false = select f xs
... | true = x ∷ select f xs

emptyCoords : Board six → List (Coord six)
emptyCoords b = select (λ q → sameCell (at {six} b q) empty) (coords six)

remove : Coord six → List (Coord six) → List (Coord six)
remove q [] = []
remove q (t ∷ ts) with Fast.sameCoord6 t q
... | false = t ∷ remove q ts
... | true = remove q ts

private
  cong₂ : ∀ {A B C : Set} (f : A → B → C) {x x′ y y′} →
    x ≡ x′ → y ≡ y′ → f x y ≡ f x′ y′
  cong₂ f refl refl = refl

  and-left : ∀ a b → a ∧ b ≡ true → a ≡ true
  and-left true b e = refl
  and-left false b ()

  and-right : ∀ a b → a ∧ b ≡ true → b ≡ true
  and-right true b e = e
  and-right false b ()

  finEqual-sound : ∀ {n} (i j : F.Fin n) → Fast.finEqual i j ≡ true → i ≡ j
  finEqual-sound F.zero F.zero e = refl
  finEqual-sound F.zero (F.suc j) ()
  finEqual-sound (F.suc i) F.zero ()
  finEqual-sound (F.suc i) (F.suc j) e = cong F.suc (finEqual-sound i j e)

  finEqual-refl : ∀ {n} (i : F.Fin n) → Fast.finEqual i i ≡ true
  finEqual-refl F.zero = refl
  finEqual-refl (F.suc i) = finEqual-refl i

  sameCoord6-sound : ∀ q r → Fast.sameCoord6 q r ≡ true → q ≡ r
  sameCoord6-sound (i , j) (k , l) e = cong₂ _,_
    (finEqual-sound i k (and-left (Fast.finEqual i k) (Fast.finEqual j l) e))
    (finEqual-sound j l (and-right (Fast.finEqual i k) (Fast.finEqual j l) e))

  sameCoord6-refl : ∀ q → Fast.sameCoord6 q q ≡ true
  sameCoord6-refl (i , j) rewrite finEqual-refl i | finEqual-refl j = refl

sameListCoords : List (Coord six) → List (Coord six) → Bool
sameListCoords [] [] = true
sameListCoords [] (_ ∷ _) = false
sameListCoords (_ ∷ _) [] = false
sameListCoords (q ∷ qs) (r ∷ rs) = Fast.sameCoord6 q r ∧ sameListCoords qs rs

private
  sameListCoords-sound : ∀ xs ys → sameListCoords xs ys ≡ true → xs ≡ ys
  sameListCoords-sound [] [] e = refl
  sameListCoords-sound [] (y ∷ ys) ()
  sameListCoords-sound (x ∷ xs) [] ()
  sameListCoords-sound (x ∷ xs) (y ∷ ys) e = cong₂ _∷_
    (sameCoord6-sound x y
      (and-left (Fast.sameCoord6 x y) (sameListCoords xs ys) e))
    (sameListCoords-sound xs ys
      (and-right (Fast.sameCoord6 x y) (sameListCoords xs ys) e))

  sameListCoords-refl : ∀ xs → sameListCoords xs xs ≡ true
  sameListCoords-refl [] = refl
  sameListCoords-refl (x ∷ xs)
    rewrite sameCoord6-refl x | sameListCoords-refl xs = refl

  module ListEquality = Recompute.Checking
    sameListCoords sameListCoords-sound sameListCoords-refl

  change : ∀ {A : Set} → Bool → (A → A) → A → A
  change false f x = x
  change true f x = f x

  lookup-update : ∀ {A : Set} {n} (xs : F.Vec A n) i j f →
    F.lookup (F.updateAt xs j f) i ≡
    change (Fast.finEqual i j) f (F.lookup xs i)
  lookup-update (x F.∷ xs) F.zero F.zero f = refl
  lookup-update (x F.∷ xs) F.zero (F.suc j) f = refl
  lookup-update (x F.∷ xs) (F.suc i) F.zero f = refl
  lookup-update (x F.∷ xs) (F.suc i) (F.suc j) f =
    lookup-update xs i j f

  put-at : ∀ b q t c →
    at {six} (put {six} b q c) t ≡
    change (Fast.sameCoord6 t q) (λ _ → c) (at {six} b t)
  put-at b (r , c) (r′ , c′) v
    rewrite lookup-update b r′ r
      (λ row → F.updateAt row c (λ _ → v))
    with Fast.finEqual r′ r
  ... | false = refl
  ... | true = lookup-update (F.lookup b r′) c′ c (λ _ → v)

  at-tabulate : ∀ (f : Coord six → Cell) q →
    at {six} (F.tabulate (λ r → F.tabulate (λ c → f (r , c)))) q ≡ f q
  at-tabulate f (r , c) = trans
    (cong (λ row → F.lookup row c)
      (F.lookup-tabulate (λ r → F.tabulate (λ c → f (r , c))) r))
    (F.lookup-tabulate (λ c → f (r , c)) c)

  empty-recolour : ∀ p xs q c →
    sameCell (Fast.recolour6 p xs q c) empty ≡ sameCell c empty
  empty-recolour p xs q empty = refl
  empty-recolour black xs q blackCell with Fast.contains6 q xs
  ... | false = refl
  ... | true = refl
  empty-recolour white xs q blackCell with Fast.contains6 q xs
  ... | false = refl
  ... | true = refl
  empty-recolour black xs q whiteCell with Fast.contains6 q xs
  ... | false = refl
  ... | true = refl
  empty-recolour white xs q whiteCell with Fast.contains6 q xs
  ... | false = refl
  ... | true = refl

  select-cong : ∀ {A : Set} (f g : A → Bool) →
    (∀ x → f x ≡ g x) → ∀ xs → select f xs ≡ select g xs
  select-cong f g agree [] = refl
  select-cong f g agree (x ∷ xs) rewrite agree x
    with g x
  ... | false = select-cong f g agree xs
  ... | true = cong (λ ys → x ∷ ys) (select-cong f g agree xs)

  flipped-emptyCoords : ∀ b p xs →
    emptyCoords (Fast.flippedCaptured6 (state b p) xs) ≡ emptyCoords b
  flipped-emptyCoords b p xs = select-cong
    (λ q → sameCell (at {six} (Fast.flippedCaptured6 (state b p) xs) q) empty)
    (λ q → sameCell (at {six} b q) empty)
    agree (coords six)
    where
    agree : ∀ q →
      sameCell (at {six} (Fast.flippedCaptured6 (state b p) xs) q) empty ≡
      sameCell (at {six} b q) empty
    agree q = trans
      (cong (λ c → sameCell c empty)
        (at-tabulate
          (λ t → Fast.recolour6 p xs t (at {six} b t)) q))
      (empty-recolour p xs q (at {six} b q))

flipMany-emptyCoords : ∀ b p xs →
  emptyCoords (Inc.flipMany b p xs) ≡ emptyCoords b
flipMany-emptyCoords b p xs = trans
  (cong emptyCoords (Inc.flips-agree (state b p) xs))
  (flipped-emptyCoords b p xs)

private
  put-empty-test : ∀ b q p t →
    sameCell (at {six} (put {six} b q (playerCell p)) t) empty ≡
    sameCell (at {six} b t) empty ∧ not (Fast.sameCoord6 t q)
  put-empty-test b q p t rewrite put-at b q t (playerCell p)
    with Fast.sameCoord6 t q | at {six} b t | p
  ... | false | empty | black = refl
  ... | false | empty | white = refl
  ... | false | blackCell | black = refl
  ... | false | blackCell | white = refl
  ... | false | whiteCell | black = refl
  ... | false | whiteCell | white = refl
  ... | true | empty | black = refl
  ... | true | empty | white = refl
  ... | true | blackCell | black = refl
  ... | true | blackCell | white = refl
  ... | true | whiteCell | black = refl
  ... | true | whiteCell | white = refl

  remove-select : ∀ b q xs →
    select (λ t → sameCell (at {six} b t) empty ∧
      not (Fast.sameCoord6 t q)) xs ≡
    remove q (select (λ t → sameCell (at {six} b t) empty) xs)
  remove-select b q [] = refl
  remove-select b q (t ∷ ts)
    with sameCell (at {six} b t) empty | Fast.sameCoord6 t q in same
  ... | false | false = remove-select b q ts
  ... | false | true = remove-select b q ts
  ... | true | false rewrite same = cong (λ ys → t ∷ ys) (remove-select b q ts)
  ... | true | true rewrite same = remove-select b q ts

emptyCoords-put : ∀ b q p →
  emptyCoords (put {six} b q (playerCell p)) ≡ remove q (emptyCoords b)
emptyCoords-put b q p = trans
  (select-cong
    (λ t → sameCell (at {six} (put {six} b q (playerCell p)) t) empty)
    (λ t → sameCell (at {six} b t) empty ∧
      not (Fast.sameCoord6 t q))
    (put-empty-test b q p) (coords six))
  (remove-select b q (coords six))

record Cached : Set where
  constructor cached
  field
    raw : State six
    vacancies : List (Coord six)
    .valid : emptyCoords (board raw) ≡ vacancies
open Cached public

pack : State six → Cached
pack s = cached s (emptyCoords (board s)) refl

pass : Cached → Cached
pass (cached (state b p) vacancies valid) =
  cached (state b (other p)) vacancies valid

play : Cached → Coord six → List (Coord six) → Cached
play (cached (state b p) vacancies valid) q flips = cached
  (state (put {six} (Inc.flipMany b p flips) q (playerCell p)) (other p))
  (remove q vacancies)
  (trans (emptyCoords-put (Inc.flipMany b p flips) q p)
    (trans (cong (remove q) (flipMany-emptyCoords b p flips))
      (cong (remove q) valid)))

decode : Cached → State six
decode = raw

cache-correct : ∀ x → emptyCoords (board (raw x)) ≡ vacancies x
cache-correct (cached s xs valid) = ListEquality.recompute valid

injective : ∀ x y → raw x ≡ raw y → x ≡ y
injective x@(cached s xs sx) y@(cached .s ys ty) refl
  with trans (sym (cache-correct x)) (cache-correct y)
... | refl = refl

decode-injective : ∀ {x y} → decode x ≡ decode y → x ≡ y
decode-injective {x} {y} = injective x y

equalCached : Cached → Cached → Bool
equalCached x y = equal Encode.stateEquality6 (decode x) (decode y)

equalCached-sound : ∀ x y → equalCached x y ≡ true → x ≡ y
equalCached-sound x y e = decode-injective
  (equal-sound Encode.stateEquality6 (decode x) (decode y) e)

equality : StateEquality Cached
equality = stateEquality equalCached equalCached-sound

play-decodes : ∀ x q flips → decode (play x q flips) ≡
  state (put {six} (Inc.flipMany (board (decode x)) (toMove (decode x)) flips)
    q (playerCell (toMove (decode x)))) (other (toMove (decode x)))
play-decodes (cached (state b p) vacancies valid) q flips = refl

pass-decodes : ∀ x → decode (pass x) ≡
  passState (decode x)
pass-decodes (cached (state b p) vacancies valid) = refl
