{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Cells and their ternary codes are updated together.
module Othello.RowCacheState6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (passState)
import Othello.Finite as F
import Othello.CachedRow6 as C
import Othello.RowPacked6 as P
import Othello.Incremental6 as Inc
open import Game.Composite using (StateEquality; stateEquality)

private
  cong₂ : ∀ {X Y Z : Set} (f : X → Y → Z) {x x′ y y′} →
    x ≡ x′ → y ≡ y′ → f x y ≡ f x′ y′
  cong₂ f refl refl = refl

cellRows : ∀ {n} → F.Vec C.RowCache n → F.Vec P.Row n
cellRows F.[] = F.[]
cellRows (r F.∷ rs) = C.cells r F.∷ cellRows rs

codeRows : ∀ {n} → F.Vec C.RowCache n → F.Vec ℕ n
codeRows F.[] = F.[]
codeRows (r F.∷ rs) = C.code r F.∷ codeRows rs

packRows : ∀ {n} → F.Vec P.Row n → F.Vec C.RowCache n
packRows F.[] = F.[]
packRows (r F.∷ rs) = C.pack r F.∷ packRows rs

record CachedState : Set where
  constructor cachedState
  field
    rows : F.Vec C.RowCache 6
    whose : Player
open CachedState public

decode : CachedState → State six
decode s = state (cellRows (rows s)) (whose s)

pack : State six → CachedState
pack (state b p) = cachedState (packRows b) p

encode : CachedState → P.PackedState
encode s = P.packed (codeRows (rows s)) (whose s)

private
  cells-pack : ∀ {n} (rs : F.Vec P.Row n) → cellRows (packRows rs) ≡ rs
  cells-pack F.[] = refl
  cells-pack (r F.∷ rs) = cong (F._∷_ r) (cells-pack rs)

  codes-correct : ∀ {n} (rs : F.Vec C.RowCache n) → codeRows rs ≡ P.encodeRows (cellRows rs)
  codes-correct F.[] = refl
  codes-correct (r F.∷ rs) = cong₂ F._∷_ (C.cached-code r) (codes-correct rs)

  head : ∀ {A : Set} {n} → F.Vec A (suc n) → A
  head (x F.∷ xs) = x

  tail : ∀ {A : Set} {n} → F.Vec A (suc n) → F.Vec A n
  tail (x F.∷ xs) = xs

  rows-injective : ∀ {n} (rs ts : F.Vec C.RowCache n) → cellRows rs ≡ cellRows ts → rs ≡ ts
  rows-injective F.[] F.[] eq = refl
  rows-injective (r F.∷ rs) (t F.∷ ts) eq = cong₂ F._∷_
    (C.injective r t (cong head eq)) (rows-injective rs ts (cong tail eq))

abstract
  decode-pack : ∀ s → decode (pack s) ≡ s
  decode-pack (state b p) = cong (λ b → state b p) (cells-pack b)

  encode-agrees : ∀ s → encode s ≡ P.encode (decode s)
  encode-agrees s = cong (λ rs → P.packed rs (whose s)) (codes-correct (rows s))

  decode-encoded : ∀ s → P.decode (encode s) ≡ decode s
  decode-encoded s = trans (cong P.decode (encode-agrees s)) (P.decode-encode (decode s))

  injective : ∀ s t → decode s ≡ decode t → s ≡ t
  injective s t eq = cong₂ cachedState (rows-injective (rows s) (rows t) (cong board eq)) (cong toMove eq)

equal : CachedState → CachedState → Bool
equal s t = P.equal (encode s) (encode t)

equal-sound : ∀ s t → equal s t ≡ true → s ≡ t
equal-sound s t checked = injective s t
  (trans (sym (decode-encoded s)) (trans (cong P.decode (P.equal-sound (encode s) (encode t) checked)) (decode-encoded t)))

equality : StateEquality CachedState
equality = stateEquality equal equal-sound

matches : CachedState → P.PackedState → Bool
matches s t = P.equal (encode s) t

matches-sound : ∀ s t → matches s t ≡ true → decode s ≡ P.decode t
matches-sound s t checked = trans (sym (decode-encoded s))
  (cong P.decode (P.equal-sound (encode s) t checked))

modifyRows : ∀ {n} → F.Vec C.RowCache n → F.Fin n → F.Fin 6 → (Cell → Cell) → F.Vec C.RowCache n
modifyRows rs r c f = F.updateAt rs r (λ row → C.modify row c f)

private
  cells-modifyRows : ∀ {n} (rs : F.Vec C.RowCache n) r c f →
    cellRows (modifyRows rs r c f) ≡ F.updateAt (cellRows rs) r (λ row → F.updateAt row c f)
  cells-modifyRows (row F.∷ rs) F.zero c f = cong (λ x → x F.∷ cellRows rs) (C.cells-modify row c f)
  cells-modifyRows (row F.∷ rs) (F.suc r) c f = cong (F._∷_ (C.cells row)) (cells-modifyRows rs r c f)

mark : Player → Cell → Cell
mark p empty = empty
mark p blackCell = playerCell p
mark p whiteCell = playerCell p

flipRows : F.Vec C.RowCache 6 → Player → List (Coord six) → F.Vec C.RowCache 6
flipRows rs p [] = rs
flipRows rs p ((r , c) ∷ qs) = modifyRows (flipRows rs p qs) r c (mark p)

private
  update-cong : ∀ {A : Set} {n} (xs : F.Vec A n) i {f g : A → A} →
    (∀ x → f x ≡ g x) → F.updateAt xs i f ≡ F.updateAt xs i g
  update-cong (x F.∷ xs) F.zero eq = cong (λ y → y F.∷ xs) (eq x)
  update-cong (x F.∷ xs) (F.suc i) eq = cong (F._∷_ x) (update-cong xs i eq)

  modify-cong : ∀ b q {f g : Cell → Cell} →
    (∀ c → f c ≡ g c) → Inc.modify b q f ≡ Inc.modify b q g
  modify-cong b (r , c) eq = update-cong b r (λ row → update-cong row c eq)

  cells-flip : ∀ rs p qs → cellRows (flipRows rs p qs) ≡ Inc.flipMany (cellRows rs) p qs
  cells-flip rs p [] = refl
  cells-flip rs p ((r , c) ∷ qs) = trans (cells-modifyRows (flipRows rs p qs) r c (mark p))
    (trans (cong (λ b → Inc.modify b (r , c) (mark p)) (cells-flip rs p qs))
      (modify-cong (Inc.flipMany (cellRows rs) p qs) (r , c)
        (λ { empty → refl ; blackCell → refl ; whiteCell → refl })))

play : CachedState → Coord six → List (Coord six) → CachedState
play s (r , c) caps = cachedState
  (modifyRows (flipRows (rows s) (whose s) caps) r c (λ _ → playerCell (whose s))) (other (whose s))

abstract
  play-decodes : ∀ s q caps → decode (play s q caps) ≡
    state (put {six} (Inc.flipMany (board (decode s)) (toMove (decode s)) caps) q
      (playerCell (toMove (decode s)))) (other (toMove (decode s)))
  play-decodes s (r , c) caps = cong (λ b → state b (other (whose s)))
    (trans (cells-modifyRows (flipRows (rows s) (whose s) caps) r c (λ _ → playerCell (whose s)))
      (cong (λ b → put {six} b (r , c) (playerCell (whose s))) (cells-flip (rows s) (whose s) caps)))

pass : CachedState → CachedState
pass s = cachedState (rows s) (other (whose s))

pass-decodes : ∀ s → decode (pass s) ≡ passState (decode s)
pass-decodes s = refl
