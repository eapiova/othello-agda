{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Tests.Search6 where

open import Game.Core
open import Game.Certificate
open import Game.Search
open import Game.Composite
open import Agda.Builtin.Nat using (_==_)
import Othello.Board as OB
import Othello.Rules as OR
open import Othello.Finite using (tabulate)

-- A finite toy graph tests every search/checker branch without a large search.
Toy : Set
Toy = ℕ × Player

toyNext : Toy → List Toy
toyNext (2 , p) = (1 , white) ∷ (0 , white) ∷ []
toyNext (3 , p) = (0 , white) ∷ (0 , black) ∷ []
toyNext (4 , p) = (0 , black) ∷ []
toyNext (5 , p) = (0 , black) ∷ []
toyNext _ = []

toyPass : Toy → Bool
toyPass (4 , p) = true
toyPass _ = false

toyGoal : Toy → Bool
toyGoal (0 , p) = true
toyGoal _ = false

toyGame : Game Toy
toyGame = record { turn = proj₂ ; next = toyNext ; forcedPass = toyPass }

private
  leftTrue : ∀ a b → a ∧ b ≡ true → a ≡ true
  leftTrue true b e = refl
  leftTrue false b ()

  rightTrue : ∀ a b → a ∧ b ≡ true → b ≡ true
  rightTrue true b e = e
  rightTrue false b ()

  natSound : ∀ n m → (n == m) ≡ true → n ≡ m
  natSound zero zero e = refl
  natSound zero (suc m) ()
  natSound (suc n) zero ()
  natSound (suc n) (suc m) e = cong suc (natSound n m e)

  playerSound : ∀ p q → samePlayer p q ≡ true → p ≡ q
  playerSound black black e = refl
  playerSound black white ()
  playerSound white black ()
  playerSound white white e = refl

  toyEqual : Toy → Toy → Bool
  toyEqual (n , p) (m , q) = (n == m) ∧ samePlayer p q

  toyEqualSound : ∀ s t → toyEqual s t ≡ true → s ≡ t
  toyEqualSound (n , p) (m , q) e
    with natSound n m (leftTrue (n == m) (samePlayer p q) e)
       | playerSound p q (rightTrue (n == m) (samePlayer p q) e)
  ... | refl | refl = refl

toyEquality : StateEquality Toy
toyEquality = stateEquality toyEqual toyEqualSound

zero-fuel-terminal-rejected : forces 0 toyGame black toyGoal (0 , white) ≡ false
zero-fuel-terminal-rejected = refl

positive-terminal-accepted : forces 1 toyGame black toyGoal (0 , white) ≡ true
positive-terminal-accepted = refl

wrong-terminal-goal-rejected : forces 1 toyGame black toyGoal (1 , white) ≡ false
wrong-terminal-goal-rejected = refl

exhausted-child-rejected : forces 1 toyGame black toyGoal (2 , black) ≡ false
exhausted-child-rejected = refl

own-choice-accepted : forces 2 toyGame black toyGoal (2 , black) ≡ true
own-choice-accepted = refl

own-witness-selects-second : witness 2 toyGame black toyGoal (2 , black) ≡ choice 1 leaf
own-witness-selects-second = refl

opponent-replies-accepted : forces 2 toyGame black toyGoal (3 , white) ≡ true
opponent-replies-accepted = refl

opponent-witness-covers-both : witness 2 toyGame black toyGoal (3 , white) ≡ fork (leaf ∷ leaf ∷ [])
opponent-witness-covers-both = refl

opponent-bad-reply-rejected : forces 2 toyGame black toyGoal (2 , white) ≡ false
opponent-bad-reply-rejected = refl

compulsory-pass-accepted : forces 2 toyGame black toyGoal (4 , white) ≡ true
compulsory-pass-accepted = refl

compulsory-pass-emitted : witness 2 toyGame black toyGoal (4 , white) ≡ pass leaf
compulsory-pass-emitted = refl

pass-consumes-fuel : forces 1 toyGame black toyGoal (4 , white) ≡ false
pass-consumes-fuel = refl

search-check-proof : check toyGame black toyGoal (2 , black)
  (witness 2 toyGame black toyGoal (2 , black)) ≡ true
search-check-proof = forces-sound 2 toyGame black toyGoal (2 , black) own-choice-accepted

toyShards : Shards Toy
toyShards = (entry (0 , white) localLeaf ∷ []) ∷
            (entry (0 , black) (solve 1) ∷ []) ∷ []

items-accepted : itemsOK toyGame black toyGoal toyShards ≡ true
items-accepted = refl

choice-composition-accepted : checkComposite toyEquality toyShards toyGame black toyGoal
  (2 , black) (choose 1 (lemma 0 0)) ≡ true
choice-composition-accepted = refl

cross-shard-fork-accepted : checkComposite toyEquality toyShards toyGame black toyGoal
  (3 , white) (replies (lemma 0 0 ∷ lemma 1 0 ∷ [])) ≡ true
cross-shard-fork-accepted = refl

pass-composition-accepted : checkComposite toyEquality toyShards toyGame black toyGoal
  (4 , white) (passing (lemma 1 0)) ≡ true
pass-composition-accepted = refl

composed-guarantee : Guarantees toyGame black toyGoal (3 , white)
composed-guarantee = compositionSound toyEquality toyShards toyGame black toyGoal
  (3 , white) (replies (lemma 0 0 ∷ lemma 1 0 ∷ [])) items-accepted cross-shard-fork-accepted

closed-local-search-accepted : checkLocal toyGame black toyGoal (2 , black) (solve 2) ≡ true
closed-local-search-accepted = refl

closed-local-fork-accepted : checkLocal toyGame black toyGoal (3 , white)
  (localFork (localLeaf ∷ solve 1 ∷ [])) ≡ true
closed-local-fork-accepted = refl

closed-local-pass-accepted : checkLocal toyGame black toyGoal (4 , white) (localPass (solve 1)) ≡ true
closed-local-pass-accepted = refl

exhausted-entry-rejected : itemsOK toyGame black toyGoal
  ((entry (0 , white) (solve 0) ∷ []) ∷ []) ≡ false
exhausted-entry-rejected = refl

missing-local-reply-rejected : checkLocal toyGame black toyGoal (3 , white)
  (localFork (localLeaf ∷ [])) ≡ false
missing-local-reply-rejected = refl

missing-skeleton-reply-rejected : checkComposite toyEquality toyShards toyGame black toyGoal
  (3 , white) (replies (lemma 0 0 ∷ [])) ≡ false
missing-skeleton-reply-rejected = refl

bad-state-rejected : checkComposite toyEquality toyShards toyGame black toyGoal
  (1 , white) (lemma 0 0) ≡ false
bad-state-rejected = refl

bad-turn-reference-rejected : checkComposite toyEquality toyShards toyGame black toyGoal
  (0 , black) (lemma 0 0) ≡ false
bad-turn-reference-rejected = refl

bad-shard-rejected : checkComposite toyEquality toyShards toyGame black toyGoal
  (0 , white) (lemma 2 0) ≡ false
bad-shard-rejected = refl

bad-local-index-rejected : checkComposite toyEquality toyShards toyGame black toyGoal
  (0 , white) (lemma 0 1) ≡ false
bad-local-index-rejected = refl

wrong-turn-choice-rejected : checkLocal toyGame black toyGoal (2 , white)
  (localChoice 1 localLeaf) ≡ false
wrong-turn-choice-rejected = refl

out-of-range-choice-rejected : checkLocal toyGame black toyGoal (2 , black)
  (localChoice 2 localLeaf) ≡ false
out-of-range-choice-rejected = refl

voluntary-local-pass-rejected : checkLocal toyGame black toyGoal (5 , white)
  (localPass localLeaf) ≡ false
voluntary-local-pass-rejected = refl

voluntary-skeleton-pass-rejected : checkComposite toyEquality toyShards toyGame black toyGoal
  (5 , white) (passing (lemma 1 0)) ≡ false
voluntary-skeleton-pass-rejected = refl

-- Two tiny native 6×6 fixtures exercise the actual rule implementation. No
-- opening search is attempted: fuel one only examines the initial frontier.
terminalSix : OB.State OB.six
terminalSix = OB.state (tabulate (λ r → tabulate (λ c → OB.whiteCell))) white

native-six-terminal-accepted : forces 1 (OR.game OB.six) white (λ s → true) terminalSix ≡ true
native-six-terminal-accepted = refl

native-six-terminal-witness : witness 1 (OR.game OB.six) white (λ s → true) terminalSix ≡ leaf
native-six-terminal-witness = refl

native-six-initial-exhausted : forces 1 (OR.game OB.six) black (λ s → true) (OB.initial OB.six) ≡ false
native-six-initial-exhausted = refl

native-six-voluntary-pass-rejected : checkLocal (OR.game OB.six) black (λ s → true)
  (OB.initial OB.six) (localPass localLeaf) ≡ false
native-six-voluntary-pass-rejected = refl
