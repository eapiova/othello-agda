{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Coverage must reject missing values, collisions and omitted
-- branches even when the target trie uses a different routing shape.
module Tests.SharedExport6 where

open import Game.Core hiding (terminal)
open import Game.Certificate using (leaf)
open import Game.Composite using (stateEquality)
open import Game.Shared
open import Game.SharedExport

private
  boolEq : Bool → Bool → Bool
  boolEq false false = true
  boolEq true true = true
  boolEq _ _ = false

  boolEq-sound : ∀ x y → boolEq x y ≡ true → x ≡ y
  boolEq-sound false false e = refl
  boolEq-sound false true ()
  boolEq-sound true false ()
  boolEq-sound true true e = refl

  collisionKey : Keyed Bool
  collisionKey = keyed (λ _ → []) (stateEquality boolEq boolEq-sound)

  terminal : Game Bool
  terminal = record { turn = λ _ → white ; next = λ _ → [] ; forcedPass = λ _ → false }

  goal : Bool → Bool
  goal s = s

  source : Trie Bool
  source = build [] true

  source-sound : AllT (Proven terminal white goal) source
  source-sound = build-all {A = Bool} {P = Proven terminal white goal}
    [] {a = true} (leaf , refl)

  literal : Trie Bool
  literal = node nothing (build [] true) (build [] true)

literal-coverage-accepted : covered collisionKey source literal ≡ true
literal-coverage-accepted = refl

literal-export-proved : AllT (Proven terminal white goal) literal
literal-export-proved =
  covered-sound collisionKey terminal white goal source literal
    source-sound literal-coverage-accepted

colliding-wrong-state-rejected :
  covered collisionKey source (build [] false) ≡ false
colliding-wrong-state-rejected = refl

missing-state-rejected : covered collisionKey tip (build [] true) ≡ false
missing-state-rejected = refl

bad-right-branch-rejected :
  covered collisionKey source (node (just true) (build [] true) (build [] false)) ≡ false
bad-right-branch-rejected = refl

empty-export-has-no-root : knownIn collisionKey tip true ≡ false
empty-export-has-no-root = refl

empty-export-coverage-accepted : covered collisionKey source tip ≡ true
empty-export-coverage-accepted = refl
