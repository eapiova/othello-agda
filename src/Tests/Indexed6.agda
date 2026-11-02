{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Real 6×6 terminal rows exercise independent decoding/linking.
-- This fixture does not establish the initial 6×6 game value.
module Tests.Indexed6 where

open import Prelude
open import Agda.Builtin.String using (String; primStringToList)
open import Game.Core using (white; Guarantees)
open import Game.Symmetry using (CertificateTransport; identityTransport; Proven)
import Game.Indexed as I
import Game.Balanced as B
import Game.BalancedView as View
import Othello.Indexed6 as D
open import Othello.Board using (State; six; initial)
open import Othello.CompactShared6 using (decodeCompactState)
open import Othello.Statements using (lowerGoal)
import Othello.Rules as R

shape : B.Shape
shape = B.branch (B.leaf 1) (B.leaf 2)

first second third : B.Id shape
first = B.left (B.row B.fzero)
second = B.right (B.row B.fzero)
third = B.right (B.row (B.fsuc B.fzero))

position : State six
position = fromMaybe (initial six) (decodeCompactState "wQPPNEHDQPHDE")

leftStates rightStates : String
leftStates = "wQPPNEHDQPHDE"
rightStates = "wQPPNEHDQPHDEwQPPNEHDQPHDE"

leftBodies rightBodies : String
leftBodies = "L"
rightBodies = "Ka00R0b00"

stateTree : B.Tree (State six) shape
stateTree = B.join (B.rows (D.states 1 leftStates)) (B.rows (D.states 2 rightStates))

bodyTree : B.Tree (I.IndexedCertificate (B.Id shape)) shape
bodyTree = B.join (B.rows (D.bodies shape 1 leftBodies))
  (B.rows (D.bodies shape 2 rightBodies))

G : B.Id shape → State six
G = B.lookup stateTree

C : B.Id shape → I.IndexedCertificate (B.Id shape)
C = B.lookup bodyTree

emptyView : View.View (State six) shape
emptyView = View.absent

localView : View.View (State six) shape
localView = View.branches (View.present (B.cons (just position) B.nil))
  (View.present (B.cons (just position) (B.cons (just position) B.nil)))

compatible : View.Compatible localView G
compatible = left-compatible , right-compatible
  where
  left-compatible : ∀ i u →
    B.lookupVec (B.cons (just position) B.nil) i ≡ just u → G (B.left (B.row i)) ≡ u
  left-compatible B.fzero u refl = refl
  right-compatible : ∀ i u →
    B.lookupVec (B.cons (just position) (B.cons (just position) B.nil)) i ≡ just u →
    G (B.right (B.row i)) ≡ u
  right-compatible B.fzero u refl = refl
  right-compatible (B.fsuc B.fzero) u refl = refl

laws : CertificateTransport (R.game six) white (lowerGoal 4)
laws = identityTransport (R.game six) white (lowerGoal 4)
module Check = D.Checking shape (R.game six) white (lowerGoal 4) laws
module V = Check.V

firstAccepted : Check.checkPart (View.resolve emptyView)
  (λ i → B.left (B.row i)) leftStates leftBodies ≡ true
firstAccepted = refl

laterAccepted : Check.checkPart (View.resolve localView)
  (λ i → B.right (B.row i)) rightStates rightBodies ≡ true
laterAccepted = refl

localRows : ∀ i → V.LocalOK (View.resolve localView) i (G i) (C i)
localRows (B.left (B.row B.fzero)) =
  V.checkLocal-sound (View.resolve localView) first position I.indexedLeaf refl
localRows (B.right (B.row i)) =
  V.checkLocal-sound (View.resolve localView) (B.right (B.row i))
    (G (B.right (B.row i))) (C (B.right (B.row i)))
    (Check.checkPart-row (View.resolve localView) (λ j → B.right (B.row j))
      rightStates rightBodies laterAccepted i)

rows : ∀ i → V.TreeOK G i (G i) (C i)
rows i = V.lift-local (View.compatible compatible) (localRows i)

terminal-proven : Proven (R.game six) white (lowerGoal 4) position
terminal-proven = V.global-proven G C rows third

terminal-guarantee : Guarantees (R.game six) white (lowerGoal 4) position
terminal-guarantee = V.global-sound G C rows third

path-id-accepted : D.readId shape (primStringToList "b01") ≡ just (third , [])
path-id-accepted = refl

path-id-out-of-range : D.readId shape (primStringToList "b02") ≡ nothing
path-id-out-of-range = refl

bad-path-rejected : D.readId shape (primStringToList "c00") ≡ nothing
bad-path-rejected = refl

truncated-path-rejected : D.readId shape (primStringToList "b0") ≡ nothing
truncated-path-rejected = refl

truncated-state-rejected : Check.checkPart (View.resolve localView)
  (λ i → B.right (B.row i)) leftStates rightBodies ≡ false
truncated-state-rejected = refl

missing-body-rejected : Check.checkPart (View.resolve localView)
  (λ i → B.right (B.row i)) rightStates "Ka00" ≡ false
missing-body-rejected = refl

extra-body-rejected : Check.checkPart (View.resolve localView)
  (λ i → B.right (B.row i)) rightStates "Ka00R0b00L" ≡ false
extra-body-rejected = refl

extra-state-rejected : Check.checkPart (View.resolve localView)
  (λ i → B.left (B.row i)) rightStates leftBodies ≡ false
extra-state-rejected = refl

malformed-body-rejected : Check.checkPart (View.resolve localView)
  (λ i → B.left (B.row i)) leftStates "?" ≡ false
malformed-body-rejected = refl

invalid-tag-rejected : Check.checkPart (View.resolve localView)
  (λ i → B.right (B.row i)) rightStates "Ka00R8b00" ≡ false
invalid-tag-rejected = refl

forward-reference-rejected : Check.checkPart (View.resolve localView)
  (λ i → B.left (B.row i)) leftStates "Kb00" ≡ false
forward-reference-rejected = refl

self-reference-rejected : Check.checkPart (View.resolve localView)
  (λ i → B.left (B.row i)) leftStates "Ka00" ≡ false
self-reference-rejected = refl

missing-import-rejected : Check.checkPart (View.resolve emptyView)
  (λ i → B.right (B.row i)) rightStates rightBodies ≡ false
missing-import-rejected = refl

wrong-state : I.Resolver (B.Id shape) (State six)
wrong-state i = just (initial six)

wrong-state-rejected : Check.checkPart wrong-state
  (λ i → B.right (B.row i)) rightStates rightBodies ≡ false
wrong-state-rejected = refl

-- A malformed payload still has two total fallback rows, but cannot be used
-- as accepted evidence for them.
default-does-not-accept : Check.checkPart (View.resolve localView)
  (λ i → B.right (B.row i)) "?" "?" ≡ false
default-does-not-accept = refl
