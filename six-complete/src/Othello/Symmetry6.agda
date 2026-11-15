{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Arbitrary-board geometry and directional rule foundations.
-- This module does not assert legal-move, successor, or certificate transport
-- for the seven nonidentity transformations.
module Othello.Symmetry6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (Direction; rayFrom; ray; scanStep; scan;
  captures; passState; dimension)
import Othello.Finite as V
open import Othello.SymmetryGeometry6 public
open import Game.Symmetry using (CertificateTransport; Proven)
open import Othello.Rules using (game)

private
  cong₂ : ∀ {A B C : Set} (f : A → B → C) {a a′ b b′} →
    a ≡ a′ → b ≡ b′ → f a b ≡ f a′ b′
  cong₂ f refl refl = refl

  vec-ext : ∀ {A : Set} {n} (xs ys : V.Vec A n) →
    (∀ i → V.lookup xs i ≡ V.lookup ys i) → xs ≡ ys
  vec-ext V.[] V.[] equal = refl
  vec-ext (x V.∷ xs) (y V.∷ ys) equal = cong₂ V._∷_
    (equal V.zero) (vec-ext xs ys (λ i → equal (V.suc i)))

board-ext : ∀ (b c : Board six) → (∀ q → at {size = six} b q ≡ at {size = six} c q) → b ≡ c
board-ext b c equal = vec-ext b c (λ r →
  vec-ext (V.lookup b r) (V.lookup c r) (λ c → equal (r , c)))

transformBoard : D4 → Board six → Board six
transformBoard σ b = V.tabulate (λ r → V.tabulate
  (λ c → at {size = six} b (coordinate (inverse σ) (r , c))))

transformState : D4 → State six → State six
transformState σ (state b p) = state (transformBoard σ b) p

at-transform : ∀ σ b q →
  at {size = six} (transformBoard σ b) q ≡ at {size = six} b (coordinate (inverse σ) q)
at-transform σ b (r , c) = trans
  (cong (λ row → V.lookup row c)
    (V.lookup-tabulate (λ r → V.tabulate
      (λ c → at {size = six} b (coordinate (inverse σ) (r , c)))) r))
  (V.lookup-tabulate (λ c → at {size = six} b (coordinate (inverse σ) (r , c))) c)

at-forward : ∀ σ b q → at {size = six} (transformBoard σ b) (coordinate σ q) ≡ at {size = six} b q
at-forward σ b q = trans (at-transform σ b (coordinate σ q))
  (cong (at {size = six} b) (coordinate-inverse σ q))

transformBoard-identity : ∀ b → transformBoard identity b ≡ b
transformBoard-identity b = board-ext (transformBoard identity b) b
  (at-transform identity b)

transformBoard-inverse : ∀ σ b → transformBoard (inverse σ) (transformBoard σ b) ≡ b
transformBoard-inverse σ b = board-ext
  (transformBoard (inverse σ) (transformBoard σ b)) b equal
  where
  equal : ∀ q → at {size = six} (transformBoard (inverse σ) (transformBoard σ b)) q ≡ at {size = six} b q
  equal q = trans (at-transform (inverse σ) (transformBoard σ b) q)
    (trans (cong (λ τ → at {size = six} (transformBoard σ b) (coordinate τ q))
                  (inverse-involutive σ)) (at-forward σ b q))

transformBoard-compose : ∀ σ τ b →
  transformBoard σ (transformBoard τ b) ≡ transformBoard (compose σ τ) b
transformBoard-compose σ τ b = board-ext
  (transformBoard σ (transformBoard τ b)) (transformBoard (compose σ τ) b) equal
  where
  equal : ∀ q → at {size = six} (transformBoard σ (transformBoard τ b)) q ≡
                at {size = six} (transformBoard (compose σ τ) b) q
  equal q = trans (at-transform σ (transformBoard τ b) q)
    (trans (at-transform τ b (coordinate (inverse σ) q))
      (trans (cong (at {size = six} b) (coordinate-compose (inverse τ) (inverse σ) q))
        (trans (cong (λ κ → at {size = six} b (coordinate κ q)) (sym (inverse-compose σ τ)))
               (sym (at-transform (compose σ τ) b q)))))

transformState-inverse : ∀ σ s → transformState (inverse σ) (transformState σ s) ≡ s
transformState-inverse σ (state b p) = cong (λ c → state c p) (transformBoard-inverse σ b)

transformState-compose : ∀ σ τ s →
  transformState σ (transformState τ s) ≡ transformState (compose σ τ) s
transformState-compose σ τ (state b p) = cong (λ c → state c p) (transformBoard-compose σ τ b)

turn-preserved : ∀ σ s → toMove (transformState σ s) ≡ toMove s
turn-preserved σ (state b p) = refl

passState-equivariant : ∀ σ s →
  transformState σ (passState {size = six} s) ≡ passState {size = six} (transformState σ s)
passState-equivariant σ (state b p) = refl

rayFrom-equivariant : ∀ n σ d q →
  rayFrom {size = six} n (direction σ d) (coordinate σ q) ≡ map (coordinate σ) (rayFrom {size = six} n d q)
rayFrom-equivariant zero σ d q = refl
rayFrom-equivariant (suc n) σ d q rewrite step-equivariant σ d q
  with Othello.Rules.step {size = six} d q
... | nothing = refl
... | just q′ = cong (λ qs → coordinate σ q′ ∷ qs) (rayFrom-equivariant n σ d q′)

ray-equivariant : ∀ σ d q →
  ray {size = six} (direction σ d) (coordinate σ q) ≡ map (coordinate σ) (ray {size = six} d q)
ray-equivariant = rayFrom-equivariant 6

private
  scanStep-equivariant : ∀ σ p q c tail →
    scanStep {size = six} p (coordinate σ q) c (mapMaybe (map (coordinate σ)) tail) ≡
    mapMaybe (map (coordinate σ)) (scanStep {size = six} p q c tail)
  scanStep-equivariant σ black q empty tail = refl
  scanStep-equivariant σ white q empty tail = refl
  scanStep-equivariant σ black q blackCell tail = refl
  scanStep-equivariant σ white q whiteCell tail = refl
  scanStep-equivariant σ black q whiteCell nothing = refl
  scanStep-equivariant σ black q whiteCell (just xs) = refl
  scanStep-equivariant σ white q blackCell nothing = refl
  scanStep-equivariant σ white q blackCell (just xs) = refl

scan-equivariant : ∀ σ b p qs →
  scan {size = six} (transformBoard σ b) p (map (coordinate σ) qs) ≡
  mapMaybe (map (coordinate σ)) (scan {size = six} b p qs)
scan-equivariant σ b p [] = refl
scan-equivariant σ b p (q ∷ qs) rewrite at-forward σ b q | scan-equivariant σ b p qs =
  scanStep-equivariant σ p q (at {size = six} b q) (scan {size = six} b p qs)

captures-equivariant : ∀ σ b p d q →
  captures {size = six} (transformBoard σ b) p (direction σ d) (coordinate σ q) ≡
  map (coordinate σ) (captures {size = six} b p d q)
captures-equivariant σ b p d q rewrite ray-equivariant σ d q with ray {size = six} d q
... | [] = refl
... | r ∷ rs rewrite at-forward σ b r with sameCell (at {size = six} b r) (playerCell (other p))
... | false = refl
... | true rewrite scan-equivariant σ b p rs with scan {size = six} b p rs
... | nothing = refl
... | just xs = refl

-- Tags are vertical reflection followed by rotations for tags four to seven. Invalid tags act as the
-- identity but are rejected by acceptedTag8; they cannot introduce a new action.
fromTag : ℕ → D4
fromTag 0 = identity
fromTag 1 = rotate90
fromTag 2 = rotate180
fromTag 3 = rotate270
fromTag 4 = reflectVertical
fromTag 5 = reflectAntiDiagonal
fromTag 6 = reflectHorizontal
fromTag 7 = reflectDiagonal
fromTag _ = identity

acceptedTag8 : ℕ → Bool
acceptedTag8 0 = true
acceptedTag8 1 = true
acceptedTag8 2 = true
acceptedTag8 3 = true
acceptedTag8 4 = true
acceptedTag8 5 = true
acceptedTag8 6 = true
acceptedTag8 7 = true
acceptedTag8 _ = false

transformTag : ℕ → State six → State six
transformTag tag = transformState (fromTag tag)

-- This constructor makes the remaining proof obligation explicit. No
-- nonidentity certificate transport instance is supplied by this module.
lawfulTransport6 : ∀ p goal →
  (∀ tag s → Proven (game six) p goal (transformTag tag s) →
             Proven (game six) p goal s) →
  CertificateTransport (game six) p goal
lawfulTransport6 p goal proof = record
  { act = transformTag ; acceptedTag = acceptedTag8 ; transport = proof }
