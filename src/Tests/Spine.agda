{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. The joint play computes past an opaque off-path certificate.
module Tests.Spine where

open import Game.Core
open import Game.Certificate using (certificateStrategy)
open import Game.Symmetry using (Proven)
import Game.Certificate as C
open import Game.Joint
import Game.Spine as P
open import Tests.Indexed using (states)

moves : ℕ → List ℕ
moves 2 = 0 ∷ 1 ∷ []
moves 3 = 0 ∷ 1 ∷ []
moves 5 = 2 ∷ []
moves _ = []

player : ℕ → Player
player 3 = white
player _ = black

isPass : ℕ → Bool
isPass 5 = true
isPass _ = false

game : Game ℕ
game = record { turn = player ; next = moves ; forcedPass = isPass }

goal : ℕ → Bool
goal 0 = true
goal 1 = true
goal _ = false

module W = P.Paths game white goal
module B = P.Paths game black goal

abstract
  off-white : Proven game white goal 0
  off-white = C.leaf , refl

  off-black : Proven game black goal 0
  off-black = C.leaf , refl

white-at-black : W.Spine 2
white-at-black = W.split refl refl
  (W.cons (W.plug off-white) (W.cons (W.finish refl refl) W.nil))

black-at-black : B.Spine 2
black-at-black = B.pick {i = 1} refl refl refl (B.finish refl refl)

white-at-white : W.Spine 3
white-at-white = W.pick {i = 1} refl refl refl (W.finish refl refl)

black-at-white : B.Spine 3
black-at-white = B.split refl refl
  (B.cons (B.plug off-black) (B.cons (B.finish refl refl) B.nil))

white-pass : W.Spine 5
white-pass = W.forced refl refl white-at-black

black-pass : B.Spine 5
black-pass = B.forced refl refl black-at-black

black-choice-computes :
  jointCheck states game goal 2
    (certificateStrategy (W.certificate white-at-black))
    (certificateStrategy (B.certificate black-at-black)) (1 ∷ []) ≡ true
black-choice-computes = refl

white-choice-computes :
  jointCheck states game goal 3
    (certificateStrategy (W.certificate white-at-white))
    (certificateStrategy (B.certificate black-at-white)) (1 ∷ []) ≡ true
white-choice-computes = refl

pass-computes :
  jointCheck states game goal 5
    (certificateStrategy (W.certificate white-pass))
    (certificateStrategy (B.certificate black-pass)) (2 ∷ 1 ∷ []) ≡ true
pass-computes = refl

wrong-path-rejected :
  jointCheck states game goal 2
    (certificateStrategy (W.certificate white-at-black))
    (certificateStrategy (B.certificate black-at-black)) (0 ∷ []) ≡ false
wrong-path-rejected = refl

-- Both guarantees and the joint play refer to these very same certificates.
white-root : Proven game white goal 5
white-root = W.proven white-pass

black-root : Proven game black goal 5
black-root = B.proven black-pass

completed : Σ ℕ (λ t →
  CompletedPlay game white (certificateStrategy (proj₁ white-root))
    (certificateStrategy (proj₁ black-root)) 5 t × (goal t ≡ true))
completed = joint-sound states game goal 5
  (certificateStrategy (proj₁ white-root))
  (certificateStrategy (proj₁ black-root)) (2 ∷ 1 ∷ []) pass-computes
