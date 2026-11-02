{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Layered certificates: an entry may cite any state proved by an
-- earlier entry, so repeated positions are checked once. Citations are found
-- by key in a binary trie; a found state must still pass the sound equality.
module Game.Shared where

open import Game.Core
open import Game.Certificate
open import Game.Search
import Game.Symmetry as Symmetry
open Symmetry using (CertificateTransport; act; acceptedTag; transport)
open import Game.Soundness using (checkSound)
open import Game.BooleanSearch using (forcesB; forcesB-sound)
open import Game.Composite using (StateEquality; equal; equal-sound)

------------------------------------------------------------------------
-- Binary tries. The tip case is matched first so lookups in an empty trie
-- reduce for any key.

data Trie (A : Set) : Set where
  tip : Trie A
  node : Maybe A → Trie A → Trie A → Trie A

mutual
  lookupT : ∀ {A} → List Bool → Trie A → Maybe A
  lookupT ks tip = nothing
  lookupT ks (node m l r) = lookupNode ks m l r

  lookupNode : ∀ {A} → List Bool → Maybe A → Trie A → Trie A → Maybe A
  lookupNode [] m l r = m
  lookupNode (false ∷ ks) m l r = lookupT ks l
  lookupNode (true ∷ ks) m l r = lookupT ks r

build : ∀ {A} → List Bool → A → Trie A
build [] a = node (just a) tip tip
build (false ∷ ks) a = node nothing (build ks a) tip
build (true ∷ ks) a = node nothing tip (build ks a)

mutual
  insertT : ∀ {A} → List Bool → A → Trie A → Trie A
  insertT ks a tip = build ks a
  insertT ks a (node m l r) = insertNode ks a m l r

  insertNode : ∀ {A} → List Bool → A → Maybe A → Trie A → Trie A → Trie A
  insertNode [] a m l r = node (just a) l r
  insertNode (false ∷ ks) a m l r = node m (insertT ks a l) r
  insertNode (true ∷ ks) a m l r = node m l (insertT ks a r)

AllM : ∀ {A : Set} → (A → Set) → Maybe A → Set
AllM P nothing = ⊤
AllM P (just a) = P a

AllT : ∀ {A : Set} → (A → Set) → Trie A → Set
AllT P tip = ⊤
AllT P (node m l r) = AllM P m × (AllT P l × AllT P r)

mutual
  lookup-all : ∀ {A : Set} {P : A → Set} ks (t : Trie A) {a} →
    AllT P t → lookupT ks t ≡ just a → P a
  lookup-all ks tip _ ()
  lookup-all ks (node m l r) all e = lookupNode-all ks m l r all e

  lookupNode-all : ∀ {A : Set} {P : A → Set} ks m (l r : Trie A) {a} →
    AllT P (node m l r) → lookupNode ks m l r ≡ just a → P a
  lookupNode-all [] (just x) l r (px , _) refl = px
  lookupNode-all [] nothing l r _ ()
  lookupNode-all (false ∷ ks) m l r (_ , (al , _)) e = lookup-all ks l al e
  lookupNode-all (true ∷ ks) m l r (_ , (_ , ar)) e = lookup-all ks r ar e

build-all : ∀ {A : Set} {P : A → Set} ks {a} → P a → AllT P (build ks a)
build-all [] pa = pa , (tt , tt)
build-all (false ∷ ks) pa = tt , (build-all ks pa , tt)
build-all (true ∷ ks) pa = tt , (tt , build-all ks pa)

mutual
  insert-all : ∀ {A : Set} {P : A → Set} ks {a} (t : Trie A) →
    AllT P t → P a → AllT P (insertT ks a t)
  insert-all ks tip _ pa = build-all ks pa
  insert-all ks (node m l r) all pa = insertNode-all ks m l r all pa

  insertNode-all : ∀ {A : Set} {P : A → Set} ks {a} m (l r : Trie A) →
    AllT P (node m l r) → P a → AllT P (insertNode ks a m l r)
  insertNode-all [] m l r (_ , rest) pa = pa , rest
  insertNode-all (false ∷ ks) m l r (pm , (al , ar)) pa =
    pm , (insert-all ks l al pa , ar)
  insertNode-all (true ∷ ks) m l r (pm , (al , ar)) pa =
    pm , (al , insert-all ks r ar pa)

-- Structural merge visits shared trie prefixes once. The left table wins
-- collisions; keys remain routing hints, never an equality assumption.
preferM : ∀ {A : Set} → Maybe A → Maybe A → Maybe A
preferM nothing b = b
preferM (just a) b = just a

mergeT : ∀ {A} → Trie A → Trie A → Trie A
mergeT tip b = b
mergeT a tip = a
mergeT (node m l r) (node n x y) =
  node (preferM m n) (mergeT l x) (mergeT r y)

prefer-all : ∀ {A : Set} {P : A → Set} (a b : Maybe A) →
  AllM P a → AllM P b → AllM P (preferM a b)
prefer-all nothing b pa pb = pb
prefer-all (just a) b pa pb = pa

merge-all : ∀ {A : Set} {P : A → Set} (a b : Trie A) →
  AllT P a → AllT P b → AllT P (mergeT a b)
merge-all tip b pa pb = pb
merge-all (node m l r) tip pa pb = pa
merge-all (node m l r) (node n x y) (pm , (pl , pr)) (pn , (px , py)) =
  prefer-all m n pm pn , (merge-all l x pl px , merge-all r y pr py)

------------------------------------------------------------------------
-- Certificates with citations.

data SharedCertificate : Set where
  sharedLeaf : SharedCertificate
  sharedSolve : ℕ → SharedCertificate
  sharedChoice : ℕ → SharedCertificate → SharedCertificate
  sharedFork : List SharedCertificate → SharedCertificate
  sharedPass : SharedCertificate → SharedCertificate
  known : SharedCertificate
  knownBy : ℕ → SharedCertificate

record SharedEntry (S : Set) : Set where
  constructor sharedEntry
  field
    entryState : S
    entryCertificate : SharedCertificate
open SharedEntry public

-- The key only selects where to look; soundness rests on `equal`.
record Keyed (S : Set) : Set where
  constructor keyed
  field
    key : S → List Bool
    stateEq : StateEquality S
open Keyed public

-- A proved state carries a flat certificate accepted by the original checker.
Proven : ∀ {S} → Game S → Player → (S → Bool) → S → Set
Proven = Symmetry.Proven

private
  falseElim : ∀ {A : Set} → false ≡ true → A
  falseElim ()

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

  knownResult : ∀ {S} (k : Keyed S) {g : Game S} {p goal} s u →
    Proven g p goal u → Outcome g p goal s
  knownResult k {g} {p} {goal} s u (c , ok) =
    outcome (equal (stateEq k) s u) c valid
    where
    valid : equal (stateEq k) s u ≡ true → check g p goal s c ≡ true
    valid e = subst (λ v → check g p goal v c ≡ true)
      (sym (equal-sound (stateEq k) s u e)) ok

------------------------------------------------------------------------
-- Evidence-producing evaluator, used only symbolically in soundness.

mutual
  sharedOutcome : ∀ {S} (k : Keyed S) (t : Trie S) (g : Game S) p goal →
    AllT (Proven g p goal) t → (s : S) → SharedCertificate → Outcome g p goal s
  sharedOutcome k t g p goal inv s sharedLeaf = leafResult g p goal s
  sharedOutcome k t g p goal inv s (sharedSolve fuel) = outcome
    (forcesB fuel g p goal s) (witness fuel g p goal s)
    (forcesB-sound fuel g p goal s)
  sharedOutcome k t g p goal inv s (sharedChoice i c)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = outcome false leaf (λ ())
  ... | x ∷ xs | false = outcome false leaf (λ ())
  ... | x ∷ xs | true with lookup (x ∷ xs) i in el
  ...   | nothing = outcome false leaf (λ ())
  ...   | just u = choiceResult {i = i} en eo el (sharedOutcome k t g p goal inv u c)
  sharedOutcome k t g p goal inv s (sharedFork cs)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = outcome false leaf (λ ())
  ... | x ∷ xs | true = outcome false leaf (λ ())
  ... | x ∷ xs | false = forkResult en eo (sharedForest k t g p goal inv (x ∷ xs) cs)
  sharedOutcome k t g p goal inv s (sharedPass c) with next g s in en | forcedPass g s in ep
  ... | [] | b = outcome false leaf (λ ())
  ... | x ∷ [] | false = outcome false leaf (λ ())
  ... | x ∷ y ∷ xs | b = outcome false leaf (λ ())
  ... | x ∷ [] | true = passResult en ep (sharedOutcome k t g p goal inv x c)
  sharedOutcome k t g p goal inv s known with lookupT (key k s) t in el
  ... | nothing = outcome false leaf (λ ())
  ... | just u = knownResult k s u (lookup-all (key k s) t inv el)

  sharedOutcome k t g p goal inv s (knownBy tag) = outcome false leaf (λ ())

  sharedForest : ∀ {S} (k : Keyed S) (t : Trie S) (g : Game S) p goal →
    AllT (Proven g p goal) t → (ss : List S) → List SharedCertificate →
    ForestOutcome g p goal ss
  sharedForest k t g p goal inv [] [] = forestOutcome true [] (λ e → refl)
  sharedForest k t g p goal inv [] (c ∷ cs) = forestOutcome false [] (λ ())
  sharedForest k t g p goal inv (s ∷ ss) [] = forestOutcome false [] (λ ())
  sharedForest k t g p goal inv (s ∷ ss) (c ∷ cs)
    with sharedOutcome k t g p goal inv s c
  ... | r with succeeds r in er
  ...   | false = forestOutcome false [] (λ ())
  ...   | true = prepend (sharedForest k t g p goal inv ss cs)
    where
    prepend : ForestOutcome g p goal ss → ForestOutcome g p goal (s ∷ ss)
    prepend rs = forestOutcome (ForestOutcome.allSucceed rs)
      (evidence r ∷ ForestOutcome.evidences rs) valid
      where
      valid : ForestOutcome.allSucceed rs ≡ true →
        checkForest g p goal (s ∷ ss) (evidence r ∷ ForestOutcome.evidences rs) ≡ true
      valid e rewrite evidenceOK r er = ForestOutcome.evidencesOK rs e

------------------------------------------------------------------------
-- Boolean checker: this is what the kernel evaluates.

mutual
  checkShared : ∀ {S} → Keyed S → Trie S → Game S → Player → (S → Bool) →
    S → SharedCertificate → Bool
  checkShared k t g p goal s sharedLeaf with next g s
  ... | [] = goal s
  ... | x ∷ xs = false
  checkShared k t g p goal s (sharedSolve fuel) = forcesB fuel g p goal s
  checkShared k t g p goal s (sharedChoice i c)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | false = false
  ... | x ∷ xs | true with lookup (x ∷ xs) i
  ...   | nothing = false
  ...   | just u = checkShared k t g p goal u c
  checkShared k t g p goal s (sharedFork cs)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | true = false
  ... | x ∷ xs | false = checkSharedForest k t g p goal (x ∷ xs) cs
  checkShared k t g p goal s (sharedPass c) with next g s | forcedPass g s
  ... | [] | b = false
  ... | x ∷ [] | false = false
  ... | x ∷ y ∷ xs | b = false
  ... | x ∷ [] | true = checkShared k t g p goal x c
  checkShared k t g p goal s known with lookupT (key k s) t
  ... | nothing = false
  ... | just u = equal (stateEq k) s u

  checkShared k t g p goal s (knownBy tag) = false

  checkSharedForest : ∀ {S} → Keyed S → Trie S → Game S → Player →
    (S → Bool) → List S → List SharedCertificate → Bool
  checkSharedForest k t g p goal [] [] = true
  checkSharedForest k t g p goal [] (c ∷ cs) = false
  checkSharedForest k t g p goal (s ∷ ss) [] = false
  checkSharedForest k t g p goal (s ∷ ss) (c ∷ cs) =
    checkShared k t g p goal s c ∧ checkSharedForest k t g p goal ss cs

mutual
  checkShared-eq : ∀ {S} (k : Keyed S) t (g : Game S) p goal inv s c →
    checkShared k t g p goal s c ≡ succeeds (sharedOutcome k t g p goal inv s c)
  checkShared-eq k t g p goal inv s sharedLeaf with next g s in en
  ... | [] = refl
  ... | x ∷ xs = refl
  checkShared-eq k t g p goal inv s (sharedSolve fuel) = refl
  checkShared-eq k t g p goal inv s (sharedChoice i c)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = refl
  ... | x ∷ xs | false = refl
  ... | x ∷ xs | true with lookup (x ∷ xs) i in el
  ...   | nothing = refl
  ...   | just u = checkShared-eq k t g p goal inv u c
  checkShared-eq k t g p goal inv s (sharedFork cs)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = refl
  ... | x ∷ xs | true = refl
  ... | x ∷ xs | false = checkSharedForest-eq k t g p goal inv (x ∷ xs) cs
  checkShared-eq k t g p goal inv s (sharedPass c)
    with next g s in en | forcedPass g s in ep
  ... | [] | b = refl
  ... | x ∷ [] | false = refl
  ... | x ∷ y ∷ xs | b = refl
  ... | x ∷ [] | true = checkShared-eq k t g p goal inv x c
  checkShared-eq k t g p goal inv s known with lookupT (key k s) t in el
  ... | nothing = refl
  ... | just u = refl

  checkShared-eq k t g p goal inv s (knownBy tag) = refl

  checkSharedForest-eq : ∀ {S} (k : Keyed S) t (g : Game S) p goal inv ss cs →
    checkSharedForest k t g p goal ss cs ≡
    ForestOutcome.allSucceed (sharedForest k t g p goal inv ss cs)
  checkSharedForest-eq k t g p goal inv [] [] = refl
  checkSharedForest-eq k t g p goal inv [] (c ∷ cs) = refl
  checkSharedForest-eq k t g p goal inv (s ∷ ss) [] = refl
  checkSharedForest-eq k t g p goal inv (s ∷ ss) (c ∷ cs)
    rewrite checkShared-eq k t g p goal inv s c
    with sharedOutcome k t g p goal inv s c
  ... | r with succeeds r in er
  ...   | false = refl
  ...   | true = checkSharedForest-eq k t g p goal inv ss cs

checkShared-sound : ∀ {S} (k : Keyed S) t (g : Game S) p goal →
  AllT (Proven g p goal) t → ∀ s c → checkShared k t g p goal s c ≡ true →
  Proven g p goal s
checkShared-sound k t g p goal inv s c e =
  evidence r , evidenceOK r (trans (sym (checkShared-eq k t g p goal inv s c)) e)
  where
  r = sharedOutcome k t g p goal inv s c

------------------------------------------------------------------------
-- Layers. Entries are checked in order; each accepted state becomes citable
-- by every later entry. The final trie is returned so the root lookup shares
-- the same reduction.

layers : ∀ {S} → Keyed S → Game S → Player → (S → Bool) →
  Trie S → List (SharedEntry S) → Maybe (Trie S)
layers k g p goal t [] = just t
layers k g p goal t (sharedEntry s c ∷ es) with checkShared k t g p goal s c
... | false = nothing
... | true = layers k g p goal (insertT (key k s) s t) es

knownIn : ∀ {S} → Keyed S → Trie S → S → Bool
knownIn k t s with lookupT (key k s) t
... | nothing = false
... | just u = equal (stateEq k) s u

acceptShared : ∀ {S} → Keyed S → Game S → Player → (S → Bool) →
  List (SharedEntry S) → S → Bool
acceptShared k g p goal es s with layers k g p goal tip es
... | nothing = false
... | just t = knownIn k t s

layers-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal t es {t′} →
  AllT (Proven g p goal) t → layers k g p goal t es ≡ just t′ →
  AllT (Proven g p goal) t′
layers-sound k g p goal t [] inv refl = inv
layers-sound k g p goal t (sharedEntry s c ∷ es) inv e
  with checkShared k t g p goal s c in ec
... | false = nothingElim e
  where
  nothingElim : ∀ {A B : Set} {x : B} → nothing ≡ just x → A
  nothingElim ()
... | true = layers-sound k g p goal (insertT (key k s) s t) es
  (insert-all (key k s) t inv (checkShared-sound k t g p goal inv s c ec)) e

knownIn-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal t s →
  AllT (Proven g p goal) t → knownIn k t s ≡ true → Proven g p goal s
knownIn-sound k g p goal t s inv e with lookupT (key k s) t in el
... | nothing = falseElim e
... | just u with lookup-all (key k s) t inv el
...   | c , ok = c , subst (λ v → check g p goal v c ≡ true)
  (sym (equal-sound (stateEq k) s u e)) ok

acceptShared-proven : ∀ {S} (k : Keyed S) (g : Game S) p goal es s →
  acceptShared k g p goal es s ≡ true → Proven g p goal s
acceptShared-proven k g p goal es s e with layers k g p goal tip es in el
... | nothing = falseElim e
... | just t = knownIn-sound k g p goal t s (layers-sound k g p goal tip es tt el) e

acceptShared-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal es s →
  acceptShared k g p goal es s ≡ true → Guarantees g p goal s
acceptShared-sound k g p goal es s e with acceptShared-proven k g p goal es s e
... | c , ok = checkSound g p goal s c ok

------------------------------------------------------------------------
-- Symmetry-aware checker. A caller supplies actual certificate transport laws;
-- neither geometric permutations nor successor-list order are assumed here.
-- The older checker deliberately rejects knownBy, even for identity tags.

mutual
  sharedOutcomeBy : ∀ {S} (k : Keyed S) (t : Trie S) (g : Game S) p goal (laws : CertificateTransport g p goal) →
    AllT (Proven g p goal) t → (s : S) → SharedCertificate → Outcome g p goal s
  sharedOutcomeBy k t g p goal laws inv s sharedLeaf = leafResult g p goal s
  sharedOutcomeBy k t g p goal laws inv s (sharedSolve fuel) = outcome
    (forcesB fuel g p goal s) (witness fuel g p goal s)
    (forcesB-sound fuel g p goal s)
  sharedOutcomeBy k t g p goal laws inv s (sharedChoice i c)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = outcome false leaf (λ ())
  ... | x ∷ xs | false = outcome false leaf (λ ())
  ... | x ∷ xs | true with lookup (x ∷ xs) i in el
  ...   | nothing = outcome false leaf (λ ())
  ...   | just u = choiceResult {i = i} en eo el (sharedOutcomeBy k t g p goal laws inv u c)
  sharedOutcomeBy k t g p goal laws inv s (sharedFork cs)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = outcome false leaf (λ ())
  ... | x ∷ xs | true = outcome false leaf (λ ())
  ... | x ∷ xs | false = forkResult en eo (sharedForestBy k t g p goal laws inv (x ∷ xs) cs)
  sharedOutcomeBy k t g p goal laws inv s (sharedPass c) with next g s in en | forcedPass g s in ep
  ... | [] | b = outcome false leaf (λ ())
  ... | x ∷ [] | false = outcome false leaf (λ ())
  ... | x ∷ y ∷ xs | b = outcome false leaf (λ ())
  ... | x ∷ [] | true = passResult en ep (sharedOutcomeBy k t g p goal laws inv x c)
  sharedOutcomeBy k t g p goal laws inv s known with lookupT (key k s) t in el
  ... | nothing = outcome false leaf (λ ())
  ... | just u = knownResult k s u (lookup-all (key k s) t inv el)

  sharedOutcomeBy k t g p goal laws inv s (knownBy tag)
    with acceptedTag laws tag
  ... | false = outcome false leaf (λ ())
  ... | true with lookupT (key k (act laws tag s)) t in el
  ...   | nothing = outcome false leaf (λ ())
  ...   | just u with equal (stateEq k) (act laws tag s) u in eq
  ...     | false = outcome false leaf (λ ())
  ...     | true = outcome true (proj₁ proof) (λ _ → proj₂ proof)
    where
    earlier : Proven g p goal (act laws tag s)
    earlier = subst (Proven g p goal)
      (sym (equal-sound (stateEq k) (act laws tag s) u eq))
      (lookup-all (key k (act laws tag s)) t inv el)
    proof : Proven g p goal s
    proof = transport laws tag s earlier

  sharedForestBy : ∀ {S} (k : Keyed S) (t : Trie S) (g : Game S) p goal (laws : CertificateTransport g p goal) →
    AllT (Proven g p goal) t → (ss : List S) → List SharedCertificate →
    ForestOutcome g p goal ss
  sharedForestBy k t g p goal laws inv [] [] = forestOutcome true [] (λ e → refl)
  sharedForestBy k t g p goal laws inv [] (c ∷ cs) = forestOutcome false [] (λ ())
  sharedForestBy k t g p goal laws inv (s ∷ ss) [] = forestOutcome false [] (λ ())
  sharedForestBy k t g p goal laws inv (s ∷ ss) (c ∷ cs)
    with sharedOutcomeBy k t g p goal laws inv s c
  ... | r with succeeds r in er
  ...   | false = forestOutcome false [] (λ ())
  ...   | true = prepend (sharedForestBy k t g p goal laws inv ss cs)
    where
    prepend : ForestOutcome g p goal ss → ForestOutcome g p goal (s ∷ ss)
    prepend rs = forestOutcome (ForestOutcome.allSucceed rs)
      (evidence r ∷ ForestOutcome.evidences rs) valid
      where
      valid : ForestOutcome.allSucceed rs ≡ true →
        checkForest g p goal (s ∷ ss) (evidence r ∷ ForestOutcome.evidences rs) ≡ true
      valid e rewrite evidenceOK r er = ForestOutcome.evidencesOK rs e

------------------------------------------------------------------------
-- Boolean checker: this is what the kernel evaluates.

mutual
  checkSharedBy : ∀ {S} → Keyed S → Trie S → (g : Game S) → (p : Player) → (goal : S → Bool) →
    CertificateTransport g p goal →
    S → SharedCertificate → Bool
  checkSharedBy k t g p goal laws s sharedLeaf with next g s
  ... | [] = goal s
  ... | x ∷ xs = false
  checkSharedBy k t g p goal laws s (sharedSolve fuel) = forcesB fuel g p goal s
  checkSharedBy k t g p goal laws s (sharedChoice i c)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | false = false
  ... | x ∷ xs | true with lookup (x ∷ xs) i
  ...   | nothing = false
  ...   | just u = checkSharedBy k t g p goal laws u c
  checkSharedBy k t g p goal laws s (sharedFork cs)
    with next g s | samePlayer (turn g s) p
  ... | [] | own = false
  ... | x ∷ xs | true = false
  ... | x ∷ xs | false = checkSharedForestBy k t g p goal laws (x ∷ xs) cs
  checkSharedBy k t g p goal laws s (sharedPass c) with next g s | forcedPass g s
  ... | [] | b = false
  ... | x ∷ [] | false = false
  ... | x ∷ y ∷ xs | b = false
  ... | x ∷ [] | true = checkSharedBy k t g p goal laws x c
  checkSharedBy k t g p goal laws s known with lookupT (key k s) t
  ... | nothing = false
  ... | just u = equal (stateEq k) s u

  checkSharedBy k t g p goal laws s (knownBy tag) with acceptedTag laws tag
  ... | false = false
  ... | true with lookupT (key k (act laws tag s)) t
  ...   | nothing = false
  ...   | just u = equal (stateEq k) (act laws tag s) u

  checkSharedForestBy : ∀ {S} → Keyed S → Trie S → (g : Game S) → (p : Player) →
    (goal : S → Bool) → CertificateTransport g p goal → List S → List SharedCertificate → Bool
  checkSharedForestBy k t g p goal laws [] [] = true
  checkSharedForestBy k t g p goal laws [] (c ∷ cs) = false
  checkSharedForestBy k t g p goal laws (s ∷ ss) [] = false
  checkSharedForestBy k t g p goal laws (s ∷ ss) (c ∷ cs) =
    checkSharedBy k t g p goal laws s c ∧ checkSharedForestBy k t g p goal laws ss cs

mutual
  checkSharedBy-eq : ∀ {S} (k : Keyed S) t (g : Game S) p goal (laws : CertificateTransport g p goal) inv s c →
    checkSharedBy k t g p goal laws s c ≡ succeeds (sharedOutcomeBy k t g p goal laws inv s c)
  checkSharedBy-eq k t g p goal laws inv s sharedLeaf with next g s in en
  ... | [] = refl
  ... | x ∷ xs = refl
  checkSharedBy-eq k t g p goal laws inv s (sharedSolve fuel) = refl
  checkSharedBy-eq k t g p goal laws inv s (sharedChoice i c)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = refl
  ... | x ∷ xs | false = refl
  ... | x ∷ xs | true with lookup (x ∷ xs) i in el
  ...   | nothing = refl
  ...   | just u = checkSharedBy-eq k t g p goal laws inv u c
  checkSharedBy-eq k t g p goal laws inv s (sharedFork cs)
    with next g s in en | samePlayer (turn g s) p in eo
  ... | [] | own = refl
  ... | x ∷ xs | true = refl
  ... | x ∷ xs | false = checkSharedForestBy-eq k t g p goal laws inv (x ∷ xs) cs
  checkSharedBy-eq k t g p goal laws inv s (sharedPass c)
    with next g s in en | forcedPass g s in ep
  ... | [] | b = refl
  ... | x ∷ [] | false = refl
  ... | x ∷ y ∷ xs | b = refl
  ... | x ∷ [] | true = checkSharedBy-eq k t g p goal laws inv x c
  checkSharedBy-eq k t g p goal laws inv s known with lookupT (key k s) t in el
  ... | nothing = refl
  ... | just u = refl

  checkSharedBy-eq k t g p goal laws inv s (knownBy tag) with acceptedTag laws tag
  ... | false = refl
  ... | true with lookupT (key k (act laws tag s)) t in el
  ...   | nothing = refl
  ...   | just u with equal (stateEq k) (act laws tag s) u in eq
  ...     | false = refl
  ...     | true = refl

  checkSharedForestBy-eq : ∀ {S} (k : Keyed S) t (g : Game S) p goal (laws : CertificateTransport g p goal) inv ss cs →
    checkSharedForestBy k t g p goal laws ss cs ≡
    ForestOutcome.allSucceed (sharedForestBy k t g p goal laws inv ss cs)
  checkSharedForestBy-eq k t g p goal laws inv [] [] = refl
  checkSharedForestBy-eq k t g p goal laws inv [] (c ∷ cs) = refl
  checkSharedForestBy-eq k t g p goal laws inv (s ∷ ss) [] = refl
  checkSharedForestBy-eq k t g p goal laws inv (s ∷ ss) (c ∷ cs)
    rewrite checkSharedBy-eq k t g p goal laws inv s c
    with sharedOutcomeBy k t g p goal laws inv s c
  ... | r with succeeds r in er
  ...   | false = refl
  ...   | true = checkSharedForestBy-eq k t g p goal laws inv ss cs

checkSharedBy-sound : ∀ {S} (k : Keyed S) t (g : Game S) p goal (laws : CertificateTransport g p goal) →
  AllT (Proven g p goal) t → ∀ s c → checkSharedBy k t g p goal laws s c ≡ true →
  Proven g p goal s
checkSharedBy-sound k t g p goal laws inv s c e =
  evidence r , evidenceOK r (trans (sym (checkSharedBy-eq k t g p goal laws inv s c)) e)
  where
  r = sharedOutcomeBy k t g p goal laws inv s c

------------------------------------------------------------------------
-- Layers. Entries are checked in order; each accepted state becomes citable
-- by every later entry. The final trie is returned so the root lookup shares
-- the same reduction.

layersBy : ∀ {S} → Keyed S → (g : Game S) → (p : Player) → (goal : S → Bool) →
  CertificateTransport g p goal →
  Trie S → List (SharedEntry S) → Maybe (Trie S)
layersBy k g p goal laws t [] = just t
layersBy k g p goal laws t (sharedEntry s c ∷ es) with checkSharedBy k t g p goal laws s c
... | false = nothing
... | true = layersBy k g p goal laws (insertT (key k s) s t) es

acceptSharedBy : ∀ {S} → Keyed S → (g : Game S) → (p : Player) → (goal : S → Bool) →
  CertificateTransport g p goal →
  List (SharedEntry S) → S → Bool
acceptSharedBy k g p goal laws es s with layersBy k g p goal laws tip es
... | nothing = false
... | just t = knownIn k t s

layersBy-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal (laws : CertificateTransport g p goal) t es {t′} →
  AllT (Proven g p goal) t → layersBy k g p goal laws t es ≡ just t′ →
  AllT (Proven g p goal) t′
layersBy-sound k g p goal laws t [] inv refl = inv
layersBy-sound k g p goal laws t (sharedEntry s c ∷ es) inv e
  with checkSharedBy k t g p goal laws s c in ec
... | false = nothingElim e
  where
  nothingElim : ∀ {A B : Set} {x : B} → nothing ≡ just x → A
  nothingElim ()
... | true = layersBy-sound k g p goal laws (insertT (key k s) s t) es
  (insert-all (key k s) t inv (checkSharedBy-sound k t g p goal laws inv s c ec)) e

acceptSharedBy-proven : ∀ {S} (k : Keyed S) (g : Game S) p goal (laws : CertificateTransport g p goal) es s →
  acceptSharedBy k g p goal laws es s ≡ true → Proven g p goal s
acceptSharedBy-proven k g p goal laws es s e with layersBy k g p goal laws tip es in el
... | nothing = falseElim e
... | just t = knownIn-sound k g p goal t s (layersBy-sound k g p goal laws tip es tt el) e

acceptSharedBy-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal (laws : CertificateTransport g p goal) es s →
  acceptSharedBy k g p goal laws es s ≡ true → Guarantees g p goal s
acceptSharedBy-sound k g p goal laws es s e with acceptSharedBy-proven k g p goal laws es s e
... | c , ok = checkSound g p goal s c ok

------------------------------------------------------------------------
-- Checked shards. An export contains only this shard's local states, not its
-- ancestors. Its state trie is transparent; clients may put exportSound in
-- an abstract block so importing a shard never unfolds its certificate proof.

record CheckedExport {S : Set} (g : Game S) (p : Player) (goal : S → Bool) : Set where
  constructor checkedExport
  field
    exportStates : Trie S
    exportSound : AllT (Proven g p goal) exportStates
open CheckedExport public

-- Keep only the cited keys of an accepted export. Missing keys stay missing;
-- selection cannot add a claim or bypass the citation's full state equality.
selectT : ∀ {A : Set} → List (List Bool) → Trie A → Trie A
selectT [] t = tip
selectT (ks ∷ keys) t with lookupT ks t
... | nothing = selectT keys t
... | just a = insertT ks a (selectT keys t)

selectT-sound : ∀ {A : Set} {P : A → Set} keys (t : Trie A) →
  AllT P t → AllT P (selectT keys t)
selectT-sound [] t inv = tt
selectT-sound (ks ∷ keys) t inv with lookupT ks t in found
... | nothing = selectT-sound keys t inv
... | just a = insert-all ks (selectT keys t) (selectT-sound keys t inv)
  (lookup-all ks t inv found)

selectExport : ∀ {S} {g : Game S} {p goal} → List (List Bool) →
  CheckedExport g p goal → CheckedExport g p goal
selectExport keys e = checkedExport (selectT keys (exportStates e))
  (selectT-sound keys (exportStates e) (exportSound e))

importStates : ∀ {S} {g : Game S} {p goal} → List (CheckedExport g p goal) → Trie S
importStates [] = tip
importStates (e ∷ es) = mergeT (exportStates e) (importStates es)

importStates-sound : ∀ {S} {g : Game S} {p goal}
  (es : List (CheckedExport g p goal)) → AllT (Proven g p goal) (importStates es)
importStates-sound [] = tt
importStates-sound (e ∷ es) =
  merge-all (exportStates e) (importStates es) (exportSound e) (importStates-sound es)

-- Computing the export needs no imported table or certificate reduction.
-- First entries win duplicate keys, matching the merge convention above.
shardStates : ∀ {S} → Keyed S → List (SharedEntry S) → Trie S
shardStates k [] = tip
shardStates k (sharedEntry s c ∷ es) = insertT (key k s) s (shardStates k es)

checkShard : ∀ {S} → Keyed S → (g : Game S) → (p : Player) → (goal : S → Bool) →
  List (CheckedExport g p goal) → List (SharedEntry S) → Bool
checkShard k g p goal imports es with layers k g p goal (importStates imports) es
... | nothing = false
... | just t = true

-- Although shardStates is built separately, its entries are proved against
-- exactly the imported states and the accepted earlier local entries.
layers-local-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal t es {t′} →
  AllT (Proven g p goal) t → layers k g p goal t es ≡ just t′ →
  AllT (Proven g p goal) (shardStates k es)
layers-local-sound k g p goal t [] inv e = tt
layers-local-sound k g p goal t (sharedEntry s c ∷ es) inv e
  with checkShared k t g p goal s c in ec
... | false = impossible e
  where
  impossible : ∀ {A B : Set} {x : B} → nothing ≡ just x → A
  impossible ()
... | true = insert-all (key k s) (shardStates k es)
  (layers-local-sound k g p goal (insertT (key k s) s t) es
    (insert-all (key k s) t inv proved) e) proved
  where
  proved = checkShared-sound k t g p goal inv s c ec

shard-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal imports es →
  checkShard k g p goal imports es ≡ true →
  AllT (Proven g p goal) (shardStates k es)
shard-sound k g p goal imports es e
  with layers k g p goal (importStates imports) es in el
... | nothing = falseElim e
... | just t = layers-local-sound k g p goal (importStates imports) es
  (importStates-sound imports) el

-- This wrapper requires the requested state to be locally exported, so an
-- empty shard cannot present an ancestor's state as its own result.
acceptShard : ∀ {S} → Keyed S → (g : Game S) → (p : Player) → (goal : S → Bool) →
  List (CheckedExport g p goal) → List (SharedEntry S) → S → Bool
acceptShard k g p goal imports es s =
  checkShard k g p goal imports es ∧ knownIn k (shardStates k es) s

acceptShard-proven : ∀ {S} (k : Keyed S) (g : Game S) p goal imports es s →
  acceptShard k g p goal imports es s ≡ true → Proven g p goal s
acceptShard-proven k g p goal imports es s e =
  knownIn-sound k g p goal (shardStates k es) s
    (shard-sound k g p goal imports es
      (andLeft (checkShard k g p goal imports es) (knownIn k (shardStates k es) s) e))
    (andRight (checkShard k g p goal imports es) (knownIn k (shardStates k es) s) e)

acceptShard-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal imports es s →
  acceptShard k g p goal imports es s ≡ true → Guarantees g p goal s
acceptShard-sound k g p goal imports es s e
  with acceptShard-proven k g p goal imports es s e
... | c , ok = checkSound g p goal s c ok

-- The same shard boundary supports tagged citations. Imported proofs are
-- transported by the supplied laws; local exports keep their actual states.
checkShardBy : ∀ {S} → Keyed S → (g : Game S) → (p : Player) → (goal : S → Bool) →
  CertificateTransport g p goal → List (CheckedExport g p goal) → List (SharedEntry S) → Bool
checkShardBy k g p goal laws imports es with layersBy k g p goal laws (importStates imports) es
... | nothing = false
... | just t = true

layersBy-local-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal
  (laws : CertificateTransport g p goal) t es {t′} →
  AllT (Proven g p goal) t → layersBy k g p goal laws t es ≡ just t′ →
  AllT (Proven g p goal) (shardStates k es)
layersBy-local-sound k g p goal laws t [] inv e = tt
layersBy-local-sound k g p goal laws t (sharedEntry s c ∷ es) inv e
  with checkSharedBy k t g p goal laws s c in ec
... | false = impossible e
  where
  impossible : ∀ {A B : Set} {x : B} → nothing ≡ just x → A
  impossible ()
... | true = insert-all (key k s) (shardStates k es)
  (layersBy-local-sound k g p goal laws (insertT (key k s) s t) es
    (insert-all (key k s) t inv proved) e) proved
  where
  proved = checkSharedBy-sound k t g p goal laws inv s c ec

shardBy-sound : ∀ {S} (k : Keyed S) (g : Game S) p goal
  (laws : CertificateTransport g p goal) imports es →
  checkShardBy k g p goal laws imports es ≡ true →
  AllT (Proven g p goal) (shardStates k es)
shardBy-sound k g p goal laws imports es e
  with layersBy k g p goal laws (importStates imports) es in el
... | nothing = falseElim e
... | just t = layersBy-local-sound k g p goal laws (importStates imports) es
  (importStates-sound imports) el
