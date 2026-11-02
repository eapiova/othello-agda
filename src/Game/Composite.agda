{-# OPTIONS --safe --without-K --cubical-compatible #-}
module Game.Composite where

open import Game.Core
open import Game.Certificate
open import Game.Soundness using (checkSound)
open import Game.Search
open import Game.BooleanSearch using (forcesB; forcesB-sound)

-- Entries are closed: there is deliberately no reference constructor here.
data LocalCertificate : Set where
  localLeaf : LocalCertificate
  solve : ℕ → LocalCertificate
  localChoice : ℕ → LocalCertificate → LocalCertificate
  localFork : List LocalCertificate → LocalCertificate
  localPass : LocalCertificate → LocalCertificate

record Entry (S : Set) : Set where
  constructor entry
  field
    state : S
    localCertificate : LocalCertificate
open Entry public

Shards : Set → Set
Shards S = List (List (Entry S))

record StateEquality (S : Set) : Set where
  constructor stateEquality
  field
    equal : S → S → Bool
    equal-sound : ∀ s t → equal s t ≡ true → s ≡ t
open StateEquality public

-- Only the outer skeleton can mention independently checked table entries.
data Skeleton : Set where
  local : LocalCertificate → Skeleton
  lemma : ℕ → ℕ → Skeleton
  choose : ℕ → Skeleton → Skeleton
  replies : List Skeleton → Skeleton
  passing : Skeleton → Skeleton

private
  falseElim : ∀ {A : Set} → false ≡ true → A
  falseElim ()

  nothingElim : ∀ {A B : Set} {x : B} → nothing ≡ just x → A
  nothingElim ()

  andLeft : ∀ a b → a ∧ b ≡ true → a ≡ true
  andLeft true b e = refl
  andLeft false b ()

  andRight : ∀ a b → a ∧ b ≡ true → b ≡ true
  andRight true b e = e
  andRight false b ()

  leafResult : ∀ {S} (g : Game S) p goal s → Outcome g p goal s
  leafResult g p goal s with next g s in en
  ... | [] = outcome (goal s) leaf valid
    where
    valid : goal s ≡ true → check g p goal s leaf ≡ true
    valid e rewrite en = e
  ... | x ∷ xs = outcome false leaf (λ ())

  choiceResult : ∀ {S} {g : Game S} {p goal s x xs t i} →
    next g s ≡ x ∷ xs → samePlayer (turn g s) p ≡ true →
    lookup (x ∷ xs) i ≡ just t → Outcome g p goal t → Outcome g p goal s
  choiceResult {g = g} {p} {goal} {s} {i = i} en eo el r =
    outcome (succeeds r) (choice i (evidence r)) valid
    where
    valid : succeeds r ≡ true → check g p goal s (choice i (evidence r)) ≡ true
    valid e rewrite en | eo | el = evidenceOK r e

  passResult : ∀ {S} {g : Game S} {p goal s x} →
    next g s ≡ x ∷ [] → forcedPass g s ≡ true →
    Outcome g p goal x → Outcome g p goal s
  passResult {g = g} {p} {goal} {s} en ep r =
    outcome (succeeds r) (pass (evidence r)) valid
    where
    valid : succeeds r ≡ true → check g p goal s (pass (evidence r)) ≡ true
    valid e rewrite en | ep = evidenceOK r e

  forkResult : ∀ {S} {g : Game S} {p goal s x xs} →
    next g s ≡ x ∷ xs → samePlayer (turn g s) p ≡ false →
    ForestOutcome g p goal (x ∷ xs) → Outcome g p goal s
  forkResult {g = g} {p} {goal} {s} en eo r =
    outcome (ForestOutcome.allSucceed r) (fork (ForestOutcome.evidences r)) valid
    where
    valid : ForestOutcome.allSucceed r ≡ true →
      check g p goal s (fork (ForestOutcome.evidences r)) ≡ true
    valid e rewrite en | eo = ForestOutcome.evidencesOK r e

mutual
  localOutcome : ∀ {S} (g : Game S) (p : Player) (goal : S → Bool)
    (s : S) → LocalCertificate → Outcome g p goal s
  localOutcome g p goal s localLeaf = leafResult g p goal s
  localOutcome g p goal s (solve fuel) = outcome
    (forcesB fuel g p goal s) (witness fuel g p goal s)
    (forcesB-sound fuel g p goal s)
  localOutcome g p goal s (localChoice i c)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = outcome false leaf (λ ())
  ... | x ∷ xs | false = outcome false leaf (λ ())
  ... | x ∷ xs | true with lookup (x ∷ xs) i in el
  ...   | nothing = outcome false leaf (λ ())
  ...   | just t = choiceResult {i = i} en eo el (localOutcome g p goal t c)
  localOutcome g p goal s (localFork cs)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = outcome false leaf (λ ())
  ... | x ∷ xs | true = outcome false leaf (λ ())
  ... | x ∷ xs | false = forkResult en eo (localForest g p goal (x ∷ xs) cs)
  localOutcome g p goal s (localPass c) with next g s in en | forcedPass g s in ep
  ... | [] | b = outcome false leaf (λ ())
  ... | x ∷ [] | false = outcome false leaf (λ ())
  ... | x ∷ y ∷ xs | b = outcome false leaf (λ ())
  ... | x ∷ [] | true = passResult en ep (localOutcome g p goal x c)

  localForest : ∀ {S} (g : Game S) (p : Player) (goal : S → Bool)
    (ss : List S) → List LocalCertificate → ForestOutcome g p goal ss
  localForest g p goal [] [] = forestOutcome true [] (λ e → refl)
  localForest g p goal [] (c ∷ cs) = forestOutcome false [] (λ ())
  localForest g p goal (s ∷ ss) [] = forestOutcome false [] (λ ())
  localForest g p goal (s ∷ ss) (c ∷ cs) with localOutcome g p goal s c
  ... | r with succeeds r in er
  ...   | false = forestOutcome false [] (λ ())
  ...   | true = prepend (localForest g p goal ss cs)
    where
    prepend : ForestOutcome g p goal ss → ForestOutcome g p goal (s ∷ ss)
    prepend rs = forestOutcome (ForestOutcome.allSucceed rs)
      (evidence r ∷ ForestOutcome.evidences rs) valid
      where
      valid : ForestOutcome.allSucceed rs ≡ true →
        checkForest g p goal (s ∷ ss) (evidence r ∷ ForestOutcome.evidences rs) ≡ true
      valid e rewrite evidenceOK r er = ForestOutcome.evidencesOK rs e

-- Acceptance carries only Booleans. Evidence and its proof are constructed
-- separately when soundness is used, rather than retained during reduction.
mutual
  checkLocal : ∀ {S} → Game S → Player → (S → Bool) → S → LocalCertificate → Bool
  checkLocal g p goal s localLeaf with next g s
  ... | [] = goal s
  ... | x ∷ xs = false
  checkLocal g p goal s (solve fuel) = forcesB fuel g p goal s
  checkLocal g p goal s (localChoice i c)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | false = false
  ... | x ∷ xs | true with lookup (x ∷ xs) i
  ...   | nothing = false
  ...   | just t = checkLocal g p goal t c
  checkLocal g p goal s (localFork cs)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | true = false
  ... | x ∷ xs | false = checkLocalForest g p goal (x ∷ xs) cs
  checkLocal g p goal s (localPass c) with next g s | forcedPass g s
  ... | [] | b = false
  ... | x ∷ [] | false = false
  ... | x ∷ y ∷ xs | b = false
  ... | x ∷ [] | true = checkLocal g p goal x c

  checkLocalForest : ∀ {S} → Game S → Player → (S → Bool) →
    List S → List LocalCertificate → Bool
  checkLocalForest g p goal [] [] = true
  checkLocalForest g p goal [] (c ∷ cs) = false
  checkLocalForest g p goal (s ∷ ss) [] = false
  checkLocalForest g p goal (s ∷ ss) (c ∷ cs) =
    checkLocal g p goal s c ∧ checkLocalForest g p goal ss cs

mutual
  checkLocal-eq : ∀ {S} (g : Game S) p goal s c →
    checkLocal g p goal s c ≡ succeeds (localOutcome g p goal s c)
  checkLocal-eq g p goal s localLeaf with next g s in en
  ... | [] = refl
  ... | x ∷ xs = refl
  checkLocal-eq g p goal s (solve fuel) = refl
  checkLocal-eq g p goal s (localChoice i c)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = refl
  ... | x ∷ xs | false = refl
  ... | x ∷ xs | true with lookup (x ∷ xs) i in el
  ...   | nothing = refl
  ...   | just t = checkLocal-eq g p goal t c
  checkLocal-eq g p goal s (localFork cs)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = refl
  ... | x ∷ xs | true = refl
  ... | x ∷ xs | false = checkLocalForest-eq g p goal (x ∷ xs) cs
  checkLocal-eq g p goal s (localPass c)
    with next g s in en | forcedPass g s in ep
  ... | [] | b = refl
  ... | x ∷ [] | false = refl
  ... | x ∷ y ∷ xs | b = refl
  ... | x ∷ [] | true = checkLocal-eq g p goal x c

  checkLocalForest-eq : ∀ {S} (g : Game S) p goal ss cs →
    checkLocalForest g p goal ss cs ≡
    ForestOutcome.allSucceed (localForest g p goal ss cs)
  checkLocalForest-eq g p goal [] [] = refl
  checkLocalForest-eq g p goal [] (c ∷ cs) = refl
  checkLocalForest-eq g p goal (s ∷ ss) [] = refl
  checkLocalForest-eq g p goal (s ∷ ss) (c ∷ cs)
    rewrite checkLocal-eq g p goal s c with localOutcome g p goal s c
  ... | r with succeeds r in er
  ...   | false = refl
  ...   | true = checkLocalForest-eq g p goal ss cs

flattenLocal : ∀ {S} → Game S → Player → (S → Bool) → S → LocalCertificate → Certificate
flattenLocal g p goal s c = evidence (localOutcome g p goal s c)

local-sound : ∀ {S} (g : Game S) p goal s c → checkLocal g p goal s c ≡ true →
  check g p goal s (flattenLocal g p goal s c) ≡ true
local-sound g p goal s c e = evidenceOK (localOutcome g p goal s c)
  (trans (sym (checkLocal-eq g p goal s c)) e)

entryAt : ∀ {S} → Shards S → ℕ → ℕ → Maybe (Entry S)
entryAt tables shard index with lookup tables shard
... | nothing = nothing
... | just entries = lookup entries index

allOK : ∀ {A : Set} → (A → Bool) → List A → Bool
allOK test [] = true
allOK test (x ∷ xs) = test x ∧ allOK test xs

entryOK : ∀ {S} → Game S → Player → (S → Bool) → Entry S → Bool
entryOK g p goal e = checkLocal g p goal (state e) (localCertificate e)

shardOK : ∀ {S} → Game S → Player → (S → Bool) → List (Entry S) → Bool
shardOK g p goal = allOK (entryOK g p goal)

itemsOK : ∀ {S} → Game S → Player → (S → Bool) → Shards S → Bool
itemsOK g p goal = allOK (shardOK g p goal)

allOK-++ : ∀ {A : Set} (test : A → Bool) xs ys →
  allOK test xs ≡ true → allOK test ys ≡ true → allOK test (xs ++ ys) ≡ true
allOK-++ test [] ys ex ey = ey
allOK-++ test (x ∷ xs) ys ex ey
  rewrite andLeft (test x) (allOK test xs) ex =
    allOK-++ test xs ys (andRight (test x) (allOK test xs) ex) ey

itemsOK-++ : ∀ {S} (g : Game S) p goal left right →
  itemsOK g p goal left ≡ true → itemsOK g p goal right ≡ true →
  itemsOK g p goal (left ++ right) ≡ true
itemsOK-++ g p goal left right = allOK-++ (shardOK g p goal) left right

itemsOK-cons : ∀ {S} (g : Game S) p goal entries tables →
  shardOK g p goal entries ≡ true → itemsOK g p goal tables ≡ true →
  itemsOK g p goal (entries ∷ tables) ≡ true
itemsOK-cons g p goal entries tables es et rewrite es = et

private
  allOK-lookup : ∀ {A : Set} (test : A → Bool) (xs : List A) i x →
    allOK test xs ≡ true → lookup xs i ≡ just x → test x ≡ true
  allOK-lookup test [] i x ok ()
  allOK-lookup test (y ∷ ys) zero x ok el =
    subst (λ z → test z ≡ true) (cong (fromMaybe y) el)
      (andLeft (test y) (allOK test ys) ok)
  allOK-lookup test (y ∷ ys) (suc i) x ok el =
    allOK-lookup test ys i x (andRight (test y) (allOK test ys) ok) el

itemsOK-sound : ∀ {S} (g : Game S) p goal tables shard index e →
  itemsOK g p goal tables ≡ true → entryAt tables shard index ≡ just e →
  checkLocal g p goal (state e) (localCertificate e) ≡ true
itemsOK-sound g p goal tables shard index e ok el with lookup tables shard in es
... | nothing = nothingElim el
... | just entries = allOK-lookup (entryOK g p goal) entries index e
  (allOK-lookup (allOK (entryOK g p goal)) tables shard entries ok es) el

mutual
  checkComposite : ∀ {S} → StateEquality S → Shards S → Game S → Player →
    (S → Bool) → S → Skeleton → Bool
  checkComposite eq tables g p goal s (local c) = checkLocal g p goal s c
  checkComposite eq tables g p goal s (lemma shard index) with entryAt tables shard index
  ... | nothing = false
  ... | just e = equal eq s (state e)
  checkComposite eq tables g p goal s (choose i c)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | false = false
  ... | x ∷ xs | true with lookup (x ∷ xs) i
  ...   | nothing = false
  ...   | just t = checkComposite eq tables g p goal t c
  checkComposite eq tables g p goal s (replies cs)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | true = false
  ... | x ∷ xs | false = checkCompositeForest eq tables g p goal (x ∷ xs) cs
  checkComposite eq tables g p goal s (passing c) with next g s | forcedPass g s
  ... | [] | b = false
  ... | x ∷ [] | false = false
  ... | x ∷ y ∷ xs | b = false
  ... | x ∷ [] | true = checkComposite eq tables g p goal x c

  checkCompositeForest : ∀ {S} → StateEquality S → Shards S → Game S → Player →
    (S → Bool) → List S → List Skeleton → Bool
  checkCompositeForest eq tables g p goal [] [] = true
  checkCompositeForest eq tables g p goal [] (c ∷ cs) = false
  checkCompositeForest eq tables g p goal (s ∷ ss) [] = false
  checkCompositeForest eq tables g p goal (s ∷ ss) (c ∷ cs) =
    checkComposite eq tables g p goal s c ∧ checkCompositeForest eq tables g p goal ss cs

-- This expansion is only a symbolic proof target. Checking a skeleton uses
-- booleans above and never constructs its expanded certificate tree.
mutual
  flatten : ∀ {S} → Shards S → Game S → Player → (S → Bool) → S → Skeleton → Certificate
  flatten tables g p goal s (local c) = flattenLocal g p goal s c
  flatten tables g p goal s (lemma shard index) with entryAt tables shard index
  ... | nothing = leaf
  ... | just e = flattenLocal g p goal (state e) (localCertificate e)
  flatten tables g p goal s (choose i c) with lookup (next g s) i
  ... | nothing = leaf
  ... | just t = choice i (flatten tables g p goal t c)
  flatten tables g p goal s (replies cs) = fork (flattenForest tables g p goal (next g s) cs)
  flatten tables g p goal s (passing c) with next g s
  ... | [] = leaf
  ... | x ∷ xs = pass (flatten tables g p goal x c)

  flattenForest : ∀ {S} → Shards S → Game S → Player → (S → Bool) →
    List S → List Skeleton → List Certificate
  flattenForest tables g p goal [] cs = []
  flattenForest tables g p goal (s ∷ ss) [] = []
  flattenForest tables g p goal (s ∷ ss) (c ∷ cs) =
    flatten tables g p goal s c ∷ flattenForest tables g p goal ss cs

mutual
  flatten-sound : ∀ {S} (eq : StateEquality S) tables (g : Game S) p goal s c →
    itemsOK g p goal tables ≡ true → checkComposite eq tables g p goal s c ≡ true →
    check g p goal s (flatten tables g p goal s c) ≡ true
  flatten-sound eq tables g p goal s (local c) ok ec = local-sound g p goal s c ec
  flatten-sound eq tables g p goal s (lemma shard index) ok ec
    with entryAt tables shard index in el
  ... | nothing = falseElim ec
  ... | just e = subst (λ t → check g p goal t
                    (flattenLocal g p goal (state e) (localCertificate e)) ≡ true)
    (sym (equal-sound eq s (state e) ec))
    (local-sound g p goal (state e) (localCertificate e)
      (itemsOK-sound g p goal tables shard index e ok el))
  flatten-sound eq tables g p goal s (choose i c) ok ec
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = falseElim ec
  ... | x ∷ xs | false = falseElim ec
  ... | x ∷ xs | true with lookup (x ∷ xs) i in el
  ...   | nothing = falseElim ec
  ...   | just t rewrite en | eo | el = flatten-sound eq tables g p goal t c ok ec
  flatten-sound eq tables g p goal s (replies cs) ok ec
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = falseElim ec
  ... | x ∷ xs | true = falseElim ec
  ... | x ∷ xs | false = flattenForest-sound eq tables g p goal (x ∷ xs) cs ok ec
  flatten-sound eq tables g p goal s (passing c) ok ec
    with next g s in en | forcedPass g s in ep
  ... | [] | b = falseElim ec
  ... | x ∷ [] | false = falseElim ec
  ... | x ∷ y ∷ xs | b = falseElim ec
  ... | x ∷ [] | true rewrite en | ep = flatten-sound eq tables g p goal x c ok ec

  flattenForest-sound : ∀ {S} (eq : StateEquality S) tables (g : Game S) p goal ss cs →
    itemsOK g p goal tables ≡ true → checkCompositeForest eq tables g p goal ss cs ≡ true →
    checkForest g p goal ss (flattenForest tables g p goal ss cs) ≡ true
  flattenForest-sound eq tables g p goal [] [] ok ec = refl
  flattenForest-sound eq tables g p goal [] (c ∷ cs) ok ()
  flattenForest-sound eq tables g p goal (s ∷ ss) [] ok ()
  flattenForest-sound eq tables g p goal (s ∷ ss) (c ∷ cs) ok ec
    rewrite flatten-sound eq tables g p goal s c ok
      (andLeft (checkComposite eq tables g p goal s c)
               (checkCompositeForest eq tables g p goal ss cs) ec) =
      flattenForest-sound eq tables g p goal ss cs ok
        (andRight (checkComposite eq tables g p goal s c)
                  (checkCompositeForest eq tables g p goal ss cs) ec)

compositionSound : ∀ {S} (eq : StateEquality S) tables (g : Game S) p goal s c →
  itemsOK g p goal tables ≡ true → checkComposite eq tables g p goal s c ≡ true →
  Guarantees g p goal s
compositionSound eq tables g p goal s c ok ec =
  checkSound g p goal s (flatten tables g p goal s c)
    (flatten-sound eq tables g p goal s c ok ec)
