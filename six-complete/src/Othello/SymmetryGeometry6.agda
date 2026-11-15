{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Exhaustive finite tables; each equation is kernel checked.
module Othello.SymmetryGeometry6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (Direction; north; northEast; east; southEast;
  south; southWest; west; northWest; step; Delta; down; same; up; deltas; axis)
import Othello.Finite as V

data D4 : Set where
  identity rotate90 rotate180 rotate270 reflectVertical reflectDiagonal
    reflectHorizontal reflectAntiDiagonal : D4

mirror : V.Fin 6 → V.Fin 6
mirror (V.zero) = V.suc (V.suc (V.suc (V.suc (V.suc (V.zero)))))
mirror (V.suc (V.zero)) = V.suc (V.suc (V.suc (V.suc (V.zero))))
mirror (V.suc (V.suc (V.zero))) = V.suc (V.suc (V.suc (V.zero)))
mirror (V.suc (V.suc (V.suc (V.zero)))) = V.suc (V.suc (V.zero))
mirror (V.suc (V.suc (V.suc (V.suc (V.zero))))) = V.suc (V.zero)
mirror (V.suc (V.suc (V.suc (V.suc (V.suc (V.zero)))))) = V.zero

mirror-involutive : ∀ i → mirror (mirror i) ≡ i
mirror-involutive (V.zero) = refl
mirror-involutive (V.suc (V.zero)) = refl
mirror-involutive (V.suc (V.suc (V.zero))) = refl
mirror-involutive (V.suc (V.suc (V.suc (V.zero)))) = refl
mirror-involutive (V.suc (V.suc (V.suc (V.suc (V.zero))))) = refl
mirror-involutive (V.suc (V.suc (V.suc (V.suc (V.suc (V.zero)))))) = refl

coordinate : D4 → Coord six → Coord six
coordinate identity (r , c) = r , c
coordinate rotate90 (r , c) = c , mirror r
coordinate rotate180 (r , c) = mirror r , mirror c
coordinate rotate270 (r , c) = mirror c , r
coordinate reflectVertical (r , c) = r , mirror c
coordinate reflectDiagonal (r , c) = c , r
coordinate reflectHorizontal (r , c) = mirror r , c
coordinate reflectAntiDiagonal (r , c) = mirror c , mirror r

inverse : D4 → D4
inverse identity = identity
inverse rotate90 = rotate270
inverse rotate180 = rotate180
inverse rotate270 = rotate90
inverse reflectVertical = reflectVertical
inverse reflectDiagonal = reflectDiagonal
inverse reflectHorizontal = reflectHorizontal
inverse reflectAntiDiagonal = reflectAntiDiagonal

inverse-involutive : ∀ σ → inverse (inverse σ) ≡ σ
inverse-involutive identity = refl
inverse-involutive rotate90 = refl
inverse-involutive rotate180 = refl
inverse-involutive rotate270 = refl
inverse-involutive reflectVertical = refl
inverse-involutive reflectDiagonal = refl
inverse-involutive reflectHorizontal = refl
inverse-involutive reflectAntiDiagonal = refl

coordinate-inverse : ∀ σ q → coordinate (inverse σ) (coordinate σ q) ≡ q
coordinate-inverse identity (r , c) = refl
coordinate-inverse rotate90 (r , c) rewrite mirror-involutive r = refl
coordinate-inverse rotate180 (r , c) rewrite mirror-involutive r | mirror-involutive c = refl
coordinate-inverse rotate270 (r , c) rewrite mirror-involutive c = refl
coordinate-inverse reflectVertical (r , c) rewrite mirror-involutive c = refl
coordinate-inverse reflectDiagonal (r , c) = refl
coordinate-inverse reflectHorizontal (r , c) rewrite mirror-involutive r = refl
coordinate-inverse reflectAntiDiagonal (r , c) rewrite mirror-involutive r | mirror-involutive c = refl

coordinate-inverse-right : ∀ σ q → coordinate σ (coordinate (inverse σ) q) ≡ q
coordinate-inverse-right σ q = trans
  (sym (cong (λ τ → coordinate τ (coordinate (inverse σ) q)) (inverse-involutive σ)))
  (coordinate-inverse (inverse σ) q)

compose : D4 → D4 → D4
compose identity identity = identity
compose identity rotate90 = rotate90
compose identity rotate180 = rotate180
compose identity rotate270 = rotate270
compose identity reflectVertical = reflectVertical
compose identity reflectDiagonal = reflectDiagonal
compose identity reflectHorizontal = reflectHorizontal
compose identity reflectAntiDiagonal = reflectAntiDiagonal
compose rotate90 identity = rotate90
compose rotate90 rotate90 = rotate180
compose rotate90 rotate180 = rotate270
compose rotate90 rotate270 = identity
compose rotate90 reflectVertical = reflectAntiDiagonal
compose rotate90 reflectDiagonal = reflectVertical
compose rotate90 reflectHorizontal = reflectDiagonal
compose rotate90 reflectAntiDiagonal = reflectHorizontal
compose rotate180 identity = rotate180
compose rotate180 rotate90 = rotate270
compose rotate180 rotate180 = identity
compose rotate180 rotate270 = rotate90
compose rotate180 reflectVertical = reflectHorizontal
compose rotate180 reflectDiagonal = reflectAntiDiagonal
compose rotate180 reflectHorizontal = reflectVertical
compose rotate180 reflectAntiDiagonal = reflectDiagonal
compose rotate270 identity = rotate270
compose rotate270 rotate90 = identity
compose rotate270 rotate180 = rotate90
compose rotate270 rotate270 = rotate180
compose rotate270 reflectVertical = reflectDiagonal
compose rotate270 reflectDiagonal = reflectHorizontal
compose rotate270 reflectHorizontal = reflectAntiDiagonal
compose rotate270 reflectAntiDiagonal = reflectVertical
compose reflectVertical identity = reflectVertical
compose reflectVertical rotate90 = reflectDiagonal
compose reflectVertical rotate180 = reflectHorizontal
compose reflectVertical rotate270 = reflectAntiDiagonal
compose reflectVertical reflectVertical = identity
compose reflectVertical reflectDiagonal = rotate90
compose reflectVertical reflectHorizontal = rotate180
compose reflectVertical reflectAntiDiagonal = rotate270
compose reflectDiagonal identity = reflectDiagonal
compose reflectDiagonal rotate90 = reflectHorizontal
compose reflectDiagonal rotate180 = reflectAntiDiagonal
compose reflectDiagonal rotate270 = reflectVertical
compose reflectDiagonal reflectVertical = rotate270
compose reflectDiagonal reflectDiagonal = identity
compose reflectDiagonal reflectHorizontal = rotate90
compose reflectDiagonal reflectAntiDiagonal = rotate180
compose reflectHorizontal identity = reflectHorizontal
compose reflectHorizontal rotate90 = reflectAntiDiagonal
compose reflectHorizontal rotate180 = reflectVertical
compose reflectHorizontal rotate270 = reflectDiagonal
compose reflectHorizontal reflectVertical = rotate180
compose reflectHorizontal reflectDiagonal = rotate270
compose reflectHorizontal reflectHorizontal = identity
compose reflectHorizontal reflectAntiDiagonal = rotate90
compose reflectAntiDiagonal identity = reflectAntiDiagonal
compose reflectAntiDiagonal rotate90 = reflectVertical
compose reflectAntiDiagonal rotate180 = reflectDiagonal
compose reflectAntiDiagonal rotate270 = reflectHorizontal
compose reflectAntiDiagonal reflectVertical = rotate90
compose reflectAntiDiagonal reflectDiagonal = rotate180
compose reflectAntiDiagonal reflectHorizontal = rotate270
compose reflectAntiDiagonal reflectAntiDiagonal = identity

coordinate-compose : ∀ σ τ q →
  coordinate σ (coordinate τ q) ≡ coordinate (compose σ τ) q
coordinate-compose identity identity (r , c) = refl
coordinate-compose identity rotate90 (r , c) = refl
coordinate-compose identity rotate180 (r , c) = refl
coordinate-compose identity rotate270 (r , c) = refl
coordinate-compose identity reflectVertical (r , c) = refl
coordinate-compose identity reflectDiagonal (r , c) = refl
coordinate-compose identity reflectHorizontal (r , c) = refl
coordinate-compose identity reflectAntiDiagonal (r , c) = refl
coordinate-compose rotate90 identity (r , c) = refl
coordinate-compose rotate90 rotate90 (r , c) = refl
coordinate-compose rotate90 rotate180 (r , c) rewrite mirror-involutive r = refl
coordinate-compose rotate90 rotate270 (r , c) rewrite mirror-involutive c = refl
coordinate-compose rotate90 reflectVertical (r , c) = refl
coordinate-compose rotate90 reflectDiagonal (r , c) = refl
coordinate-compose rotate90 reflectHorizontal (r , c) rewrite mirror-involutive r = refl
coordinate-compose rotate90 reflectAntiDiagonal (r , c) rewrite mirror-involutive c = refl
coordinate-compose rotate180 identity (r , c) = refl
coordinate-compose rotate180 rotate90 (r , c) rewrite mirror-involutive r = refl
coordinate-compose rotate180 rotate180 (r , c) rewrite mirror-involutive r | mirror-involutive c = refl
coordinate-compose rotate180 rotate270 (r , c) rewrite mirror-involutive c = refl
coordinate-compose rotate180 reflectVertical (r , c) rewrite mirror-involutive c = refl
coordinate-compose rotate180 reflectDiagonal (r , c) = refl
coordinate-compose rotate180 reflectHorizontal (r , c) rewrite mirror-involutive r = refl
coordinate-compose rotate180 reflectAntiDiagonal (r , c) rewrite mirror-involutive c | mirror-involutive r = refl
coordinate-compose rotate270 identity (r , c) = refl
coordinate-compose rotate270 rotate90 (r , c) rewrite mirror-involutive r = refl
coordinate-compose rotate270 rotate180 (r , c) rewrite mirror-involutive c = refl
coordinate-compose rotate270 rotate270 (r , c) = refl
coordinate-compose rotate270 reflectVertical (r , c) rewrite mirror-involutive c = refl
coordinate-compose rotate270 reflectDiagonal (r , c) = refl
coordinate-compose rotate270 reflectHorizontal (r , c) = refl
coordinate-compose rotate270 reflectAntiDiagonal (r , c) rewrite mirror-involutive r = refl
coordinate-compose reflectVertical identity (r , c) = refl
coordinate-compose reflectVertical rotate90 (r , c) rewrite mirror-involutive r = refl
coordinate-compose reflectVertical rotate180 (r , c) rewrite mirror-involutive c = refl
coordinate-compose reflectVertical rotate270 (r , c) = refl
coordinate-compose reflectVertical reflectVertical (r , c) rewrite mirror-involutive c = refl
coordinate-compose reflectVertical reflectDiagonal (r , c) = refl
coordinate-compose reflectVertical reflectHorizontal (r , c) = refl
coordinate-compose reflectVertical reflectAntiDiagonal (r , c) rewrite mirror-involutive r = refl
coordinate-compose reflectDiagonal identity (r , c) = refl
coordinate-compose reflectDiagonal rotate90 (r , c) = refl
coordinate-compose reflectDiagonal rotate180 (r , c) = refl
coordinate-compose reflectDiagonal rotate270 (r , c) = refl
coordinate-compose reflectDiagonal reflectVertical (r , c) = refl
coordinate-compose reflectDiagonal reflectDiagonal (r , c) = refl
coordinate-compose reflectDiagonal reflectHorizontal (r , c) = refl
coordinate-compose reflectDiagonal reflectAntiDiagonal (r , c) = refl
coordinate-compose reflectHorizontal identity (r , c) = refl
coordinate-compose reflectHorizontal rotate90 (r , c) = refl
coordinate-compose reflectHorizontal rotate180 (r , c) rewrite mirror-involutive r = refl
coordinate-compose reflectHorizontal rotate270 (r , c) rewrite mirror-involutive c = refl
coordinate-compose reflectHorizontal reflectVertical (r , c) = refl
coordinate-compose reflectHorizontal reflectDiagonal (r , c) = refl
coordinate-compose reflectHorizontal reflectHorizontal (r , c) rewrite mirror-involutive r = refl
coordinate-compose reflectHorizontal reflectAntiDiagonal (r , c) rewrite mirror-involutive c = refl
coordinate-compose reflectAntiDiagonal identity (r , c) = refl
coordinate-compose reflectAntiDiagonal rotate90 (r , c) rewrite mirror-involutive r = refl
coordinate-compose reflectAntiDiagonal rotate180 (r , c) rewrite mirror-involutive c | mirror-involutive r = refl
coordinate-compose reflectAntiDiagonal rotate270 (r , c) rewrite mirror-involutive c = refl
coordinate-compose reflectAntiDiagonal reflectVertical (r , c) rewrite mirror-involutive c = refl
coordinate-compose reflectAntiDiagonal reflectDiagonal (r , c) = refl
coordinate-compose reflectAntiDiagonal reflectHorizontal (r , c) rewrite mirror-involutive r = refl
coordinate-compose reflectAntiDiagonal reflectAntiDiagonal (r , c) rewrite mirror-involutive r | mirror-involutive c = refl

inverse-compose : ∀ σ τ → inverse (compose σ τ) ≡ compose (inverse τ) (inverse σ)
inverse-compose identity identity = refl
inverse-compose identity rotate90 = refl
inverse-compose identity rotate180 = refl
inverse-compose identity rotate270 = refl
inverse-compose identity reflectVertical = refl
inverse-compose identity reflectDiagonal = refl
inverse-compose identity reflectHorizontal = refl
inverse-compose identity reflectAntiDiagonal = refl
inverse-compose rotate90 identity = refl
inverse-compose rotate90 rotate90 = refl
inverse-compose rotate90 rotate180 = refl
inverse-compose rotate90 rotate270 = refl
inverse-compose rotate90 reflectVertical = refl
inverse-compose rotate90 reflectDiagonal = refl
inverse-compose rotate90 reflectHorizontal = refl
inverse-compose rotate90 reflectAntiDiagonal = refl
inverse-compose rotate180 identity = refl
inverse-compose rotate180 rotate90 = refl
inverse-compose rotate180 rotate180 = refl
inverse-compose rotate180 rotate270 = refl
inverse-compose rotate180 reflectVertical = refl
inverse-compose rotate180 reflectDiagonal = refl
inverse-compose rotate180 reflectHorizontal = refl
inverse-compose rotate180 reflectAntiDiagonal = refl
inverse-compose rotate270 identity = refl
inverse-compose rotate270 rotate90 = refl
inverse-compose rotate270 rotate180 = refl
inverse-compose rotate270 rotate270 = refl
inverse-compose rotate270 reflectVertical = refl
inverse-compose rotate270 reflectDiagonal = refl
inverse-compose rotate270 reflectHorizontal = refl
inverse-compose rotate270 reflectAntiDiagonal = refl
inverse-compose reflectVertical identity = refl
inverse-compose reflectVertical rotate90 = refl
inverse-compose reflectVertical rotate180 = refl
inverse-compose reflectVertical rotate270 = refl
inverse-compose reflectVertical reflectVertical = refl
inverse-compose reflectVertical reflectDiagonal = refl
inverse-compose reflectVertical reflectHorizontal = refl
inverse-compose reflectVertical reflectAntiDiagonal = refl
inverse-compose reflectDiagonal identity = refl
inverse-compose reflectDiagonal rotate90 = refl
inverse-compose reflectDiagonal rotate180 = refl
inverse-compose reflectDiagonal rotate270 = refl
inverse-compose reflectDiagonal reflectVertical = refl
inverse-compose reflectDiagonal reflectDiagonal = refl
inverse-compose reflectDiagonal reflectHorizontal = refl
inverse-compose reflectDiagonal reflectAntiDiagonal = refl
inverse-compose reflectHorizontal identity = refl
inverse-compose reflectHorizontal rotate90 = refl
inverse-compose reflectHorizontal rotate180 = refl
inverse-compose reflectHorizontal rotate270 = refl
inverse-compose reflectHorizontal reflectVertical = refl
inverse-compose reflectHorizontal reflectDiagonal = refl
inverse-compose reflectHorizontal reflectHorizontal = refl
inverse-compose reflectHorizontal reflectAntiDiagonal = refl
inverse-compose reflectAntiDiagonal identity = refl
inverse-compose reflectAntiDiagonal rotate90 = refl
inverse-compose reflectAntiDiagonal rotate180 = refl
inverse-compose reflectAntiDiagonal rotate270 = refl
inverse-compose reflectAntiDiagonal reflectVertical = refl
inverse-compose reflectAntiDiagonal reflectDiagonal = refl
inverse-compose reflectAntiDiagonal reflectHorizontal = refl
inverse-compose reflectAntiDiagonal reflectAntiDiagonal = refl

direction : D4 → Direction → Direction
direction identity north = north
direction identity northEast = northEast
direction identity east = east
direction identity southEast = southEast
direction identity south = south
direction identity southWest = southWest
direction identity west = west
direction identity northWest = northWest
direction rotate90 north = east
direction rotate90 northEast = southEast
direction rotate90 east = south
direction rotate90 southEast = southWest
direction rotate90 south = west
direction rotate90 southWest = northWest
direction rotate90 west = north
direction rotate90 northWest = northEast
direction rotate180 north = south
direction rotate180 northEast = southWest
direction rotate180 east = west
direction rotate180 southEast = northWest
direction rotate180 south = north
direction rotate180 southWest = northEast
direction rotate180 west = east
direction rotate180 northWest = southEast
direction rotate270 north = west
direction rotate270 northEast = northWest
direction rotate270 east = north
direction rotate270 southEast = northEast
direction rotate270 south = east
direction rotate270 southWest = southEast
direction rotate270 west = south
direction rotate270 northWest = southWest
direction reflectVertical north = north
direction reflectVertical northEast = northWest
direction reflectVertical east = west
direction reflectVertical southEast = southWest
direction reflectVertical south = south
direction reflectVertical southWest = southEast
direction reflectVertical west = east
direction reflectVertical northWest = northEast
direction reflectDiagonal north = west
direction reflectDiagonal northEast = southWest
direction reflectDiagonal east = south
direction reflectDiagonal southEast = southEast
direction reflectDiagonal south = east
direction reflectDiagonal southWest = northEast
direction reflectDiagonal west = north
direction reflectDiagonal northWest = northWest
direction reflectHorizontal north = south
direction reflectHorizontal northEast = southEast
direction reflectHorizontal east = east
direction reflectHorizontal southEast = northEast
direction reflectHorizontal south = north
direction reflectHorizontal southWest = northWest
direction reflectHorizontal west = west
direction reflectHorizontal northWest = southWest
direction reflectAntiDiagonal north = east
direction reflectAntiDiagonal northEast = northEast
direction reflectAntiDiagonal east = north
direction reflectAntiDiagonal southEast = northWest
direction reflectAntiDiagonal south = west
direction reflectAntiDiagonal southWest = southWest
direction reflectAntiDiagonal west = south
direction reflectAntiDiagonal northWest = southEast

mapMaybe : ∀ {A B : Set} → (A → B) → Maybe A → Maybe B
mapMaybe f nothing = nothing
mapMaybe f (just x) = just (f x)

mirrorDelta : Delta → Delta
mirrorDelta down = up
mirrorDelta same = same
mirrorDelta up = down

axis-mirror : ∀ d i → axis (mirrorDelta d) (mirror i) ≡ mapMaybe mirror (axis d i)
axis-mirror down (V.zero) = refl
axis-mirror down (V.suc (V.zero)) = refl
axis-mirror down (V.suc (V.suc (V.zero))) = refl
axis-mirror down (V.suc (V.suc (V.suc (V.zero)))) = refl
axis-mirror down (V.suc (V.suc (V.suc (V.suc (V.zero))))) = refl
axis-mirror down (V.suc (V.suc (V.suc (V.suc (V.suc (V.zero)))))) = refl
axis-mirror same (V.zero) = refl
axis-mirror same (V.suc (V.zero)) = refl
axis-mirror same (V.suc (V.suc (V.zero))) = refl
axis-mirror same (V.suc (V.suc (V.suc (V.zero)))) = refl
axis-mirror same (V.suc (V.suc (V.suc (V.suc (V.zero))))) = refl
axis-mirror same (V.suc (V.suc (V.suc (V.suc (V.suc (V.zero)))))) = refl
axis-mirror up (V.zero) = refl
axis-mirror up (V.suc (V.zero)) = refl
axis-mirror up (V.suc (V.suc (V.zero))) = refl
axis-mirror up (V.suc (V.suc (V.suc (V.zero)))) = refl
axis-mirror up (V.suc (V.suc (V.suc (V.suc (V.zero))))) = refl
axis-mirror up (V.suc (V.suc (V.suc (V.suc (V.suc (V.zero)))))) = refl

step-equivariant : ∀ σ d q → step {size = six} (direction σ d) (coordinate σ q) ≡
  mapMaybe (coordinate σ) (step {size = six} d q)
step-equivariant identity north (r , c)
  with axis (proj₁ (deltas north)) r
... | nothing = refl
... | just r′ = refl
step-equivariant identity northEast (r , c)
  with axis (proj₁ (deltas northEast)) r | axis (proj₂ (deltas northEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant identity east (r , c)
  with axis (proj₂ (deltas east)) c
... | nothing = refl
... | just c′ = refl
step-equivariant identity southEast (r , c)
  with axis (proj₁ (deltas southEast)) r | axis (proj₂ (deltas southEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant identity south (r , c)
  with axis (proj₁ (deltas south)) r
... | nothing = refl
... | just r′ = refl
step-equivariant identity southWest (r , c)
  with axis (proj₁ (deltas southWest)) r | axis (proj₂ (deltas southWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant identity west (r , c)
  with axis (proj₂ (deltas west)) c
... | nothing = refl
... | just c′ = refl
step-equivariant identity northWest (r , c)
  with axis (proj₁ (deltas northWest)) r | axis (proj₂ (deltas northWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate90 north (r , c)
  rewrite axis-mirror (proj₁ (deltas north)) r
  with axis (proj₁ (deltas north)) r
... | nothing = refl
... | just r′ = refl
step-equivariant rotate90 northEast (r , c)
  rewrite axis-mirror (proj₁ (deltas northEast)) r
  with axis (proj₁ (deltas northEast)) r | axis (proj₂ (deltas northEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate90 east (r , c)
  with axis (proj₂ (deltas east)) c
... | nothing = refl
... | just c′ = refl
step-equivariant rotate90 southEast (r , c)
  rewrite axis-mirror (proj₁ (deltas southEast)) r
  with axis (proj₁ (deltas southEast)) r | axis (proj₂ (deltas southEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate90 south (r , c)
  rewrite axis-mirror (proj₁ (deltas south)) r
  with axis (proj₁ (deltas south)) r
... | nothing = refl
... | just r′ = refl
step-equivariant rotate90 southWest (r , c)
  rewrite axis-mirror (proj₁ (deltas southWest)) r
  with axis (proj₁ (deltas southWest)) r | axis (proj₂ (deltas southWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate90 west (r , c)
  with axis (proj₂ (deltas west)) c
... | nothing = refl
... | just c′ = refl
step-equivariant rotate90 northWest (r , c)
  rewrite axis-mirror (proj₁ (deltas northWest)) r
  with axis (proj₁ (deltas northWest)) r | axis (proj₂ (deltas northWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate180 north (r , c)
  rewrite axis-mirror (proj₁ (deltas north)) r
  with axis (proj₁ (deltas north)) r
... | nothing = refl
... | just r′ = refl
step-equivariant rotate180 northEast (r , c)
  rewrite axis-mirror (proj₁ (deltas northEast)) r | axis-mirror (proj₂ (deltas northEast)) c
  with axis (proj₁ (deltas northEast)) r | axis (proj₂ (deltas northEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate180 east (r , c)
  rewrite axis-mirror (proj₂ (deltas east)) c
  with axis (proj₂ (deltas east)) c
... | nothing = refl
... | just c′ = refl
step-equivariant rotate180 southEast (r , c)
  rewrite axis-mirror (proj₁ (deltas southEast)) r | axis-mirror (proj₂ (deltas southEast)) c
  with axis (proj₁ (deltas southEast)) r | axis (proj₂ (deltas southEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate180 south (r , c)
  rewrite axis-mirror (proj₁ (deltas south)) r
  with axis (proj₁ (deltas south)) r
... | nothing = refl
... | just r′ = refl
step-equivariant rotate180 southWest (r , c)
  rewrite axis-mirror (proj₁ (deltas southWest)) r | axis-mirror (proj₂ (deltas southWest)) c
  with axis (proj₁ (deltas southWest)) r | axis (proj₂ (deltas southWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate180 west (r , c)
  rewrite axis-mirror (proj₂ (deltas west)) c
  with axis (proj₂ (deltas west)) c
... | nothing = refl
... | just c′ = refl
step-equivariant rotate180 northWest (r , c)
  rewrite axis-mirror (proj₁ (deltas northWest)) r | axis-mirror (proj₂ (deltas northWest)) c
  with axis (proj₁ (deltas northWest)) r | axis (proj₂ (deltas northWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate270 north (r , c)
  with axis (proj₁ (deltas north)) r
... | nothing = refl
... | just r′ = refl
step-equivariant rotate270 northEast (r , c)
  rewrite axis-mirror (proj₂ (deltas northEast)) c
  with axis (proj₁ (deltas northEast)) r | axis (proj₂ (deltas northEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate270 east (r , c)
  rewrite axis-mirror (proj₂ (deltas east)) c
  with axis (proj₂ (deltas east)) c
... | nothing = refl
... | just c′ = refl
step-equivariant rotate270 southEast (r , c)
  rewrite axis-mirror (proj₂ (deltas southEast)) c
  with axis (proj₁ (deltas southEast)) r | axis (proj₂ (deltas southEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate270 south (r , c)
  with axis (proj₁ (deltas south)) r
... | nothing = refl
... | just r′ = refl
step-equivariant rotate270 southWest (r , c)
  rewrite axis-mirror (proj₂ (deltas southWest)) c
  with axis (proj₁ (deltas southWest)) r | axis (proj₂ (deltas southWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant rotate270 west (r , c)
  rewrite axis-mirror (proj₂ (deltas west)) c
  with axis (proj₂ (deltas west)) c
... | nothing = refl
... | just c′ = refl
step-equivariant rotate270 northWest (r , c)
  rewrite axis-mirror (proj₂ (deltas northWest)) c
  with axis (proj₁ (deltas northWest)) r | axis (proj₂ (deltas northWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectVertical north (r , c)
  with axis (proj₁ (deltas north)) r
... | nothing = refl
... | just r′ = refl
step-equivariant reflectVertical northEast (r , c)
  rewrite axis-mirror (proj₂ (deltas northEast)) c
  with axis (proj₁ (deltas northEast)) r | axis (proj₂ (deltas northEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectVertical east (r , c)
  rewrite axis-mirror (proj₂ (deltas east)) c
  with axis (proj₂ (deltas east)) c
... | nothing = refl
... | just c′ = refl
step-equivariant reflectVertical southEast (r , c)
  rewrite axis-mirror (proj₂ (deltas southEast)) c
  with axis (proj₁ (deltas southEast)) r | axis (proj₂ (deltas southEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectVertical south (r , c)
  with axis (proj₁ (deltas south)) r
... | nothing = refl
... | just r′ = refl
step-equivariant reflectVertical southWest (r , c)
  rewrite axis-mirror (proj₂ (deltas southWest)) c
  with axis (proj₁ (deltas southWest)) r | axis (proj₂ (deltas southWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectVertical west (r , c)
  rewrite axis-mirror (proj₂ (deltas west)) c
  with axis (proj₂ (deltas west)) c
... | nothing = refl
... | just c′ = refl
step-equivariant reflectVertical northWest (r , c)
  rewrite axis-mirror (proj₂ (deltas northWest)) c
  with axis (proj₁ (deltas northWest)) r | axis (proj₂ (deltas northWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectDiagonal north (r , c)
  with axis (proj₁ (deltas north)) r
... | nothing = refl
... | just r′ = refl
step-equivariant reflectDiagonal northEast (r , c)
  with axis (proj₁ (deltas northEast)) r | axis (proj₂ (deltas northEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectDiagonal east (r , c)
  with axis (proj₂ (deltas east)) c
... | nothing = refl
... | just c′ = refl
step-equivariant reflectDiagonal southEast (r , c)
  with axis (proj₁ (deltas southEast)) r | axis (proj₂ (deltas southEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectDiagonal south (r , c)
  with axis (proj₁ (deltas south)) r
... | nothing = refl
... | just r′ = refl
step-equivariant reflectDiagonal southWest (r , c)
  with axis (proj₁ (deltas southWest)) r | axis (proj₂ (deltas southWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectDiagonal west (r , c)
  with axis (proj₂ (deltas west)) c
... | nothing = refl
... | just c′ = refl
step-equivariant reflectDiagonal northWest (r , c)
  with axis (proj₁ (deltas northWest)) r | axis (proj₂ (deltas northWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectHorizontal north (r , c)
  rewrite axis-mirror (proj₁ (deltas north)) r
  with axis (proj₁ (deltas north)) r
... | nothing = refl
... | just r′ = refl
step-equivariant reflectHorizontal northEast (r , c)
  rewrite axis-mirror (proj₁ (deltas northEast)) r
  with axis (proj₁ (deltas northEast)) r | axis (proj₂ (deltas northEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectHorizontal east (r , c)
  with axis (proj₂ (deltas east)) c
... | nothing = refl
... | just c′ = refl
step-equivariant reflectHorizontal southEast (r , c)
  rewrite axis-mirror (proj₁ (deltas southEast)) r
  with axis (proj₁ (deltas southEast)) r | axis (proj₂ (deltas southEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectHorizontal south (r , c)
  rewrite axis-mirror (proj₁ (deltas south)) r
  with axis (proj₁ (deltas south)) r
... | nothing = refl
... | just r′ = refl
step-equivariant reflectHorizontal southWest (r , c)
  rewrite axis-mirror (proj₁ (deltas southWest)) r
  with axis (proj₁ (deltas southWest)) r | axis (proj₂ (deltas southWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectHorizontal west (r , c)
  with axis (proj₂ (deltas west)) c
... | nothing = refl
... | just c′ = refl
step-equivariant reflectHorizontal northWest (r , c)
  rewrite axis-mirror (proj₁ (deltas northWest)) r
  with axis (proj₁ (deltas northWest)) r | axis (proj₂ (deltas northWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectAntiDiagonal north (r , c)
  rewrite axis-mirror (proj₁ (deltas north)) r
  with axis (proj₁ (deltas north)) r
... | nothing = refl
... | just r′ = refl
step-equivariant reflectAntiDiagonal northEast (r , c)
  rewrite axis-mirror (proj₁ (deltas northEast)) r | axis-mirror (proj₂ (deltas northEast)) c
  with axis (proj₁ (deltas northEast)) r | axis (proj₂ (deltas northEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectAntiDiagonal east (r , c)
  rewrite axis-mirror (proj₂ (deltas east)) c
  with axis (proj₂ (deltas east)) c
... | nothing = refl
... | just c′ = refl
step-equivariant reflectAntiDiagonal southEast (r , c)
  rewrite axis-mirror (proj₁ (deltas southEast)) r | axis-mirror (proj₂ (deltas southEast)) c
  with axis (proj₁ (deltas southEast)) r | axis (proj₂ (deltas southEast)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectAntiDiagonal south (r , c)
  rewrite axis-mirror (proj₁ (deltas south)) r
  with axis (proj₁ (deltas south)) r
... | nothing = refl
... | just r′ = refl
step-equivariant reflectAntiDiagonal southWest (r , c)
  rewrite axis-mirror (proj₁ (deltas southWest)) r | axis-mirror (proj₂ (deltas southWest)) c
  with axis (proj₁ (deltas southWest)) r | axis (proj₂ (deltas southWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
step-equivariant reflectAntiDiagonal west (r , c)
  rewrite axis-mirror (proj₂ (deltas west)) c
  with axis (proj₂ (deltas west)) c
... | nothing = refl
... | just c′ = refl
step-equivariant reflectAntiDiagonal northWest (r , c)
  rewrite axis-mirror (proj₁ (deltas northWest)) r | axis-mirror (proj₂ (deltas northWest)) c
  with axis (proj₁ (deltas northWest)) r | axis (proj₂ (deltas northWest)) c
... | nothing | nothing = refl
... | nothing | just c′ = refl
... | just r′ | nothing = refl
... | just r′ | just c′ = refl
