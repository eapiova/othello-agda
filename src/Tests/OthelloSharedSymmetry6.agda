{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. A real rotated lower/upper certificate, with transported moves.
module Tests.OthelloSharedSymmetry6 where

open import Prelude
open import Game.Core using (white; black; Guarantees)
open import Game.Shared
open import Game.Soundness using (checkSound)
open import Othello.Board using (State; six)
open import Othello.Shared6 using (keyed6; key6)
open import Othello.SharedSymmetry6 using (lowerTransport6; upperTransport6)
open import Othello.Symmetry6 using (transformState; rotate270)
open import Othello.Statements using (lowerGoal; upperGoal)
import Othello.Fast6 as F
import Tests.Shared6 as Fixtures

lowerBank upperBank : Trie (State six)
lowerBank = build (key6 Fixtures.state12) Fixtures.state12
upperBank = build (key6 Fixtures.state10) Fixtures.state10

lowerBank-sound : AllT (Proven F.fastGame6 white (lowerGoal 4)) lowerBank
lowerBank-sound = build-all {P = Proven F.fastGame6 white (lowerGoal 4)}
  (key6 Fixtures.state12) {a = Fixtures.state12}
  (acceptShared-proven keyed6 F.fastGame6 white (lowerGoal 4)
    Fixtures.lower12 Fixtures.state12 Fixtures.lower12-accepted)

upperBank-sound : AllT (Proven F.fastGame6 black (upperGoal 4)) upperBank
upperBank-sound = build-all {P = Proven F.fastGame6 black (upperGoal 4)}
  (key6 Fixtures.state10) {a = Fixtures.state10}
  (acceptShared-proven keyed6 F.fastGame6 black (upperGoal 4)
    Fixtures.upper10 Fixtures.state10 Fixtures.upper10-accepted)

lower-rotated-accepted : checkSharedBy keyed6 lowerBank F.fastGame6 white
  (lowerGoal 4) lowerTransport6 (transformState rotate270 Fixtures.state12) (knownBy 1) ≡ true
lower-rotated-accepted = refl

upper-rotated-accepted : checkSharedBy keyed6 upperBank F.fastGame6 black
  (upperGoal 4) upperTransport6 (transformState rotate270 Fixtures.state10) (knownBy 1) ≡ true
upper-rotated-accepted = refl

lower-rotated-guaranteed : Guarantees F.fastGame6 white (lowerGoal 4)
  (transformState rotate270 Fixtures.state12)
lower-rotated-guaranteed with checkSharedBy-sound keyed6 lowerBank F.fastGame6 white
  (lowerGoal 4) lowerTransport6 lowerBank-sound
  (transformState rotate270 Fixtures.state12) (knownBy 1) lower-rotated-accepted
... | c , ok = checkSound F.fastGame6 white (lowerGoal 4)
  (transformState rotate270 Fixtures.state12) c ok

upper-rotated-guaranteed : Guarantees F.fastGame6 black (upperGoal 4)
  (transformState rotate270 Fixtures.state10)
upper-rotated-guaranteed with checkSharedBy-sound keyed6 upperBank F.fastGame6 black
  (upperGoal 4) upperTransport6 upperBank-sound
  (transformState rotate270 Fixtures.state10) (knownBy 1) upper-rotated-accepted
... | c , ok = checkSound F.fastGame6 black (upperGoal 4)
  (transformState rotate270 Fixtures.state10) c ok

invalid-tag-rejected : checkSharedBy keyed6 lowerBank F.fastGame6 white
  (lowerGoal 4) lowerTransport6 Fixtures.state12 (knownBy 8) ≡ false
invalid-tag-rejected = refl

wrong-orientation-rejected : checkSharedBy keyed6 lowerBank F.fastGame6 white
  (lowerGoal 4) lowerTransport6 (transformState rotate270 Fixtures.state12) (knownBy 0) ≡ false
wrong-orientation-rejected = refl

rotatedEntries : List (SharedEntry (State six))
rotatedEntries = sharedEntry (transformState rotate270 Fixtures.state12) (knownBy 1) ∷ []

rotatedImports : List (CheckedExport F.fastGame6 white (lowerGoal 4))
rotatedImports = checkedExport lowerBank lowerBank-sound ∷ []

rotated-shard-accepted : checkShardBy keyed6 F.fastGame6 white (lowerGoal 4)
  lowerTransport6 rotatedImports rotatedEntries ≡ true
rotated-shard-accepted = refl

rotated-shard-sound : AllT (Proven F.fastGame6 white (lowerGoal 4))
  (shardStates keyed6 rotatedEntries)
rotated-shard-sound = shardBy-sound keyed6 F.fastGame6 white (lowerGoal 4)
  lowerTransport6 rotatedImports rotatedEntries rotated-shard-accepted

rotated-missing-import-rejected : checkShardBy keyed6 F.fastGame6 white (lowerGoal 4)
  lowerTransport6 [] rotatedEntries ≡ false
rotated-missing-import-rejected = refl
