{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Small checked fixtures isolate shard import and citation order.
module Tests.SharedImports6 where

open import Game.Core
open import Game.Composite using (stateEquality)
open import Game.Shared

private
  natEq : ℕ → ℕ → Bool
  natEq zero zero = true
  natEq zero (suc y) = false
  natEq (suc x) zero = false
  natEq (suc x) (suc y) = natEq x y

  natEq-sound : ∀ x y → natEq x y ≡ true → x ≡ y
  natEq-sound zero zero e = refl
  natEq-sound zero (suc y) ()
  natEq-sound (suc x) zero ()
  natEq-sound (suc x) (suc y) e = cong suc (natEq-sound x y e)

  natKey : ℕ → List Bool
  natKey zero = []
  natKey (suc n) = true ∷ natKey n

  fixtureKey : Keyed ℕ
  fixtureKey = keyed natKey (stateEquality natEq natEq-sound)

  successors : ℕ → List ℕ
  successors zero = []
  successors 1 = 0 ∷ []
  successors 2 = 1 ∷ []
  successors 3 = 0 ∷ 2 ∷ []
  successors (suc (suc (suc (suc n)))) = 3 ∷ []

  owner : ℕ → Player
  owner 3 = black
  owner _ = white

  fixtureGame : Game ℕ
  fixtureGame = record { turn = owner ; next = successors ; forcedPass = λ _ → false }

  goal : ℕ → Bool
  goal zero = true
  goal (suc n) = false

entries0 entries1 entries2 entries3 : List (SharedEntry ℕ)
entries0 = sharedEntry 0 sharedLeaf ∷ []
entries1 = sharedEntry 1 (sharedChoice 0 known) ∷ []
entries2 = sharedEntry 2 (sharedChoice 0 known) ∷ []
entries3 = sharedEntry 3 (sharedFork (known ∷ known ∷ [])) ∷ []

states0 states1 states2 states3 : Trie ℕ
states0 = shardStates fixtureKey entries0
states1 = shardStates fixtureKey entries1
states2 = shardStates fixtureKey entries2
states3 = shardStates fixtureKey entries3

-- The export state remains reducible even when its soundness is abstract.
abstract
  sound0 : AllT (Proven fixtureGame white goal) states0
  sound0 = shard-sound fixtureKey fixtureGame white goal [] entries0 refl

export0 : CheckedExport fixtureGame white goal
export0 = checkedExport states0 sound0

abstract
  sound1 : AllT (Proven fixtureGame white goal) states1
  sound1 = shard-sound fixtureKey fixtureGame white goal (export0 ∷ []) entries1 refl

export1 : CheckedExport fixtureGame white goal
export1 = checkedExport states1 sound1

abstract
  sound2 : AllT (Proven fixtureGame white goal) states2
  sound2 = shard-sound fixtureKey fixtureGame white goal (export1 ∷ []) entries2 refl

export2 : CheckedExport fixtureGame white goal
export2 = checkedExport states2 sound2

selectedImports : List (CheckedExport fixtureGame white goal)
selectedImports = export0 ∷ export2 ∷ []

chained-multiple-imports-accepted :
  acceptShard fixtureKey fixtureGame white goal selectedImports entries3 3 ≡ true
chained-multiple-imports-accepted = refl

chained-multiple-imports-guaranteed : Guarantees fixtureGame white goal 3
chained-multiple-imports-guaranteed =
  acceptShard-sound fixtureKey fixtureGame white goal selectedImports entries3 3
    chained-multiple-imports-accepted

local-export-excludes-ancestors : lookupT (natKey 0) (exportStates export2) ≡ nothing
local-export-excludes-ancestors = refl

missing-selected-import-rejected :
  checkShard fixtureKey fixtureGame white goal (export2 ∷ []) entries3 ≡ false
missing-selected-import-rejected = refl

transitive-state-not-implicitly-imported :
  checkShard fixtureKey fixtureGame white goal (export2 ∷ []) entries1 ≡ false
transitive-state-not-implicitly-imported = refl

empty-shard-cannot-export-imported-root :
  acceptShard fixtureKey fixtureGame white goal (export0 ∷ []) [] 0 ≡ false
empty-shard-cannot-export-imported-root = refl

earlier-local-state-accepted :
  checkShard fixtureKey fixtureGame white goal (export0 ∷ []) (entries1 ++ entries2) ≡ true
earlier-local-state-accepted = refl

future-local-state-rejected :
  checkShard fixtureKey fixtureGame white goal (export0 ∷ []) (entries2 ++ entries1) ≡ false
future-local-state-rejected = refl

self-citation-rejected :
  checkShard fixtureKey fixtureGame white goal [] (sharedEntry 0 known ∷ []) ≡ false
self-citation-rejected = refl

-- A deliberately colliding key cannot substitute a different imported state.
private
  collisionKey : Keyed ℕ
  collisionKey = keyed (λ _ → []) (stateEquality natEq natEq-sound)

wrong-imported-state-rejected :
  checkShared collisionKey (exportStates export0) fixtureGame white goal 1 known ≡ false
wrong-imported-state-rejected = refl

merge-left-collision-wins :
  lookupT [] (mergeT (build [] 0) (build [] 1)) ≡ just 0
merge-left-collision-wins = refl

selectedKeysImport : CheckedExport fixtureGame white goal
selectedKeysImport = selectExport (natKey 0 ∷ natKey 99 ∷ []) export0

selected-key-still-accepted : checkShard fixtureKey fixtureGame white goal
  (selectedKeysImport ∷ []) entries1 ≡ true
selected-key-still-accepted = refl

missing-selected-key-not-created : lookupT (natKey 99)
  (exportStates selectedKeysImport) ≡ nothing
missing-selected-key-not-created = refl

omitted-key-not-created : checkShard fixtureKey fixtureGame white goal
  (selectExport [] export0 ∷ []) entries1 ≡ false
omitted-key-not-created = refl
