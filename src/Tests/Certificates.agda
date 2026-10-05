{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.Certificates where

open import Prelude
open import Game.Core
open import Game.Certificate
open import Othello.Board
open import Othello.Rules using (game)
open import Othello.Statements
open import Othello.Generated4

-- These exercise the Agda checker, independently of the Python input checks.
premature-leaf-rejected :
  check (game four) white (lowerGoal 8) (initial four) leaf ≡ false
premature-leaf-rejected = refl

voluntary-pass-rejected :
  check (game four) white (lowerGoal 8) (initial four) (pass leaf) ≡ false
voluntary-pass-rejected = refl

illegal-choice-rejected :
  check (game four) black (upperGoal 8) (initial four) (choice 63 leaf) ≡ false
illegal-choice-rejected = refl

missing-replies-rejected :
  check (game four) white (lowerGoal 8) (initial four) (fork []) ≡ false
missing-replies-rejected = refl

removeLast : ∀ {A : Set} → List A → List A
removeLast [] = []
removeLast (x ∷ []) = []
removeLast (x ∷ y ∷ xs) = x ∷ removeLast (y ∷ xs)

missingReply : Certificate → Certificate
missingReply (fork cs) = fork (removeLast cs)
missingReply c = c

extraReply : Certificate → Certificate
extraReply (fork cs) = fork (cs ++ (leaf ∷ []))
extraReply c = c

valid-prefix-with-missing-reply-rejected :
  check (game four) white (lowerGoal 8) (initial four)
    (missingReply lowerCertificate) ≡ false
valid-prefix-with-missing-reply-rejected = refl

extra-reply-rejected :
  check (game four) white (lowerGoal 8) (initial four)
    (extraReply lowerCertificate) ≡ false
extra-reply-rejected = refl

overstated-lower-bound-rejected :
  check (game four) white (lowerGoal 9) (initial four) lowerCertificate ≡ false
overstated-lower-bound-rejected = refl

understated-upper-bound-rejected :
  check (game four) black (upperGoal 7) (initial four) upperCertificate ≡ false
understated-upper-bound-rejected = refl
