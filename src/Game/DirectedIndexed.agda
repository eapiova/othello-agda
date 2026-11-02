{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Directed moves are checked without enumerating successors;
-- soundness reconstructs an ordinary indexed choice from pick-sound.
module Game.DirectedIndexed where

open import Game.Core
open import Game.Certificate using (Certificate; leaf; choice; fork; pass; check; checkForest)
open import Game.Composite using (StateEquality; equal; equal-sound)
open import Game.BooleanSearch using (forcesB; forcesB-sound)
import Game.Search as Search
open import Game.Symmetry using (Proven; CertificateTransport; act; acceptedTag; transport)
open import Game.Soundness using (checkSound)
import Game.Indexed as I

record MovePicker {S : Set} (g : Game S) (Move : Set) : Set where
  constructor movePicker
  field
    pick : S → Move → Maybe S
    pick-sound : ∀ s a t → pick s a ≡ just t →
      Σ ℕ (λ i → lookup (next g s) i ≡ just t)
open MovePicker public

data DirectedCertificate (Key Move : Set) : Set where
  indexedLeaf : DirectedCertificate Key Move
  indexedSolve : ℕ → DirectedCertificate Key Move
  indexedChoice : ℕ → DirectedCertificate Key Move → DirectedCertificate Key Move
  indexedFork : List (DirectedCertificate Key Move) → DirectedCertificate Key Move
  indexedPass : DirectedCertificate Key Move → DirectedCertificate Key Move
  cite : Key → DirectedCertificate Key Move
  citeBy : ℕ → Key → DirectedCertificate Key Move
  indexedPick : Move → DirectedCertificate Key Move → DirectedCertificate Key Move

Resolver : Set → Set → Set
Resolver Key S = Key → Maybe S

globalResolver : ∀ {Key S : Set} → (Key → S) → Resolver Key S
globalResolver G j = just (G j)

private
  false-elim : ∀ {A : Set} → false ≡ true → A
  false-elim ()

  and-left : ∀ a b → a ∧ b ≡ true → a ≡ true
  and-left true b e = refl
  and-left false b ()

  and-right : ∀ a b → a ∧ b ≡ true → b ≡ true
  and-right true b e = e
  and-right false b ()

  just-injective : ∀ {A : Set} {x y : A} → just x ≡ just y → x ≡ y
  just-injective refl = refl

  nothing-elim : ∀ {A B : Set} {x : A} → nothing ≡ just x → B
  nothing-elim ()

module Checker {Key S Move : Set} (order : I.Order Key) (eq : StateEquality S)
  (g : Game S) (p : Player) (goal : S → Bool)
  (laws : CertificateTransport g p goal) (picker : MovePicker g Move) where

  mutual
    checkLocal : Resolver Key S → Key → S → DirectedCertificate Key Move → Bool
    checkLocal L owner s indexedLeaf with next g s
    ... | [] = goal s
    ... | x ∷ xs = false
    checkLocal L owner s (indexedSolve fuel) = forcesB fuel g p goal s
    checkLocal L owner s (indexedChoice i c)
      with next g s | samePlayer (turn g s) p
    ... | [] | own = false
    ... | x ∷ xs | false = false
    ... | x ∷ xs | true with lookup (x ∷ xs) i
    ...   | nothing = false
    ...   | just t = checkLocal L owner t c
    checkLocal L owner s (indexedFork cs)
      with next g s | samePlayer (turn g s) p
    ... | [] | own = false
    ... | x ∷ xs | true = false
    ... | x ∷ xs | false = checkLocalForest L owner (x ∷ xs) cs
    checkLocal L owner s (indexedPass c) with next g s | forcedPass g s
    ... | [] | b = false
    ... | x ∷ [] | false = false
    ... | x ∷ y ∷ xs | b = false
    ... | x ∷ [] | true = checkLocal L owner x c
    checkLocal L owner s (cite j) with I.beforeB order j owner
    ... | false = false
    ... | true with L j
    ...   | nothing = false
    ...   | just u = equal eq s u
    checkLocal L owner s (citeBy tag j) with I.beforeB order j owner
    ... | false = false
    ... | true with acceptedTag laws tag
    ...   | false = false
    ...   | true with L j
    ...     | nothing = false
    ...     | just u = equal eq (act laws tag s) u
    checkLocal L owner s (indexedPick a c)
      with samePlayer (turn g s) p | pick picker s a
    ... | false | mt = false
    ... | true | nothing = false
    ... | true | just t = checkLocal L owner t c

    checkLocalForest : Resolver Key S → Key → List S →
      List (DirectedCertificate Key Move) → Bool
    checkLocalForest L owner [] [] = true
    checkLocalForest L owner [] (c ∷ cs) = false
    checkLocalForest L owner (s ∷ ss) [] = false
    checkLocalForest L owner (s ∷ ss) (c ∷ cs) =
      checkLocal L owner s c ∧ checkLocalForest L owner ss cs

  mutual
    data LocalOK (L : Resolver Key S) (owner : Key) (s : S) :
      DirectedCertificate Key Move → Set where
      ok-leaf : next g s ≡ [] → goal s ≡ true → LocalOK L owner s indexedLeaf
      ok-solve : ∀ {fuel} → forcesB fuel g p goal s ≡ true →
        LocalOK L owner s (indexedSolve fuel)
      ok-choice : ∀ {x xs t i c} → samePlayer (turn g s) p ≡ true →
        next g s ≡ x ∷ xs → lookup (x ∷ xs) i ≡ just t →
        LocalOK L owner t c → LocalOK L owner s (indexedChoice i c)
      ok-fork : ∀ {x xs cs} → samePlayer (turn g s) p ≡ false →
        next g s ≡ x ∷ xs → ForestOK L owner (x ∷ xs) cs →
        LocalOK L owner s (indexedFork cs)
      ok-pass : ∀ {x c} → forcedPass g s ≡ true → next g s ≡ x ∷ [] →
        LocalOK L owner x c → LocalOK L owner s (indexedPass c)
      ok-cite : ∀ {j u} → I.Order._<_ order j owner → L j ≡ just u →
        s ≡ u → LocalOK L owner s (cite j)
      ok-citeBy : ∀ {tag j u} → I.Order._<_ order j owner →
        acceptedTag laws tag ≡ true → L j ≡ just u → act laws tag s ≡ u →
        LocalOK L owner s (citeBy tag j)
      ok-pick : ∀ {a t c} → samePlayer (turn g s) p ≡ true →
        pick picker s a ≡ just t → LocalOK L owner t c →
        LocalOK L owner s (indexedPick a c)

    data ForestOK (L : Resolver Key S) (owner : Key) :
      List S → List (DirectedCertificate Key Move) → Set where
      ok-nil : ForestOK L owner [] []
      ok-cons : ∀ {s ss c cs} → LocalOK L owner s c → ForestOK L owner ss cs →
        ForestOK L owner (s ∷ ss) (c ∷ cs)

  mutual
    checkLocal-sound : ∀ L owner s c → checkLocal L owner s c ≡ true →
      LocalOK L owner s c
    checkLocal-sound L owner s indexedLeaf e with next g s in en
    ... | [] = ok-leaf en e
    ... | x ∷ xs = false-elim e
    checkLocal-sound L owner s (indexedSolve fuel) e = ok-solve e
    checkLocal-sound L owner s (indexedChoice i c) e
      with next g s in en | samePlayer (turn g s) p in eo
    ... | [] | own = false-elim e
    ... | x ∷ xs | false = false-elim e
    ... | x ∷ xs | true with lookup (x ∷ xs) i in el
    ...   | nothing = false-elim e
    ...   | just t = ok-choice eo en el (checkLocal-sound L owner t c e)
    checkLocal-sound L owner s (indexedFork cs) e
      with next g s in en | samePlayer (turn g s) p in eo
    ... | [] | own = false-elim e
    ... | x ∷ xs | true = false-elim e
    ... | x ∷ xs | false = ok-fork eo en
      (checkLocalForest-sound L owner (x ∷ xs) cs e)
    checkLocal-sound L owner s (indexedPass c) e
      with next g s in en | forcedPass g s in ep
    ... | [] | b = false-elim e
    ... | x ∷ [] | false = false-elim e
    ... | x ∷ y ∷ xs | b = false-elim e
    ... | x ∷ [] | true = ok-pass ep en (checkLocal-sound L owner x c e)
    checkLocal-sound L owner s (cite j) e with I.beforeB order j owner in eb
    ... | false = false-elim e
    ... | true with L j in el
    ...   | nothing = false-elim e
    ...   | just u = ok-cite (I.before-sound order j owner eb) el
      (equal-sound eq s u e)
    checkLocal-sound L owner s (citeBy tag j) e with I.beforeB order j owner in eb
    ... | false = false-elim e
    ... | true with acceptedTag laws tag in et
    ...   | false = false-elim e
    ...   | true with L j in el
    ...     | nothing = false-elim e
    ...     | just u = ok-citeBy (I.before-sound order j owner eb) et el
      (equal-sound eq (act laws tag s) u e)
    checkLocal-sound L owner s (indexedPick a c) e
      with samePlayer (turn g s) p in eo | pick picker s a in ep
    ... | false | mt = false-elim e
    ... | true | nothing = false-elim e
    ... | true | just t = ok-pick eo ep (checkLocal-sound L owner t c e)

    checkLocalForest-sound : ∀ L owner ss cs →
      checkLocalForest L owner ss cs ≡ true → ForestOK L owner ss cs
    checkLocalForest-sound L owner [] [] e = ok-nil
    checkLocalForest-sound L owner [] (c ∷ cs) ()
    checkLocalForest-sound L owner (s ∷ ss) [] ()
    checkLocalForest-sound L owner (s ∷ ss) (c ∷ cs) e =
      ok-cons (checkLocal-sound L owner s c
        (and-left (checkLocal L owner s c) (checkLocalForest L owner ss cs) e))
        (checkLocalForest-sound L owner ss cs
          (and-right (checkLocal L owner s c) (checkLocalForest L owner ss cs) e))

  Compatible : Resolver Key S → (Key → S) → Set
  Compatible L G = ∀ j u → L j ≡ just u → G j ≡ u

  TreeOK : (Key → S) → Key → S → DirectedCertificate Key Move → Set
  TreeOK G = LocalOK (globalResolver G)

  TreeForestOK : (Key → S) → Key → List S →
    List (DirectedCertificate Key Move) → Set
  TreeForestOK G = ForestOK (globalResolver G)

  mutual
    lift-local : ∀ {L G owner s c} → Compatible L G → LocalOK L owner s c →
      TreeOK G owner s c
    lift-local compatible (ok-leaf en eg) = ok-leaf en eg
    lift-local compatible (ok-solve ef) = ok-solve ef
    lift-local compatible (ok-choice eo en el a) =
      ok-choice eo en el (lift-local compatible a)
    lift-local compatible (ok-fork eo en as) =
      ok-fork eo en (lift-forest compatible as)
    lift-local compatible (ok-pass ep en a) = ok-pass ep en (lift-local compatible a)
    lift-local compatible (ok-cite {j} {u} ej el es) =
      ok-cite ej (cong just (compatible j u el)) es
    lift-local compatible (ok-citeBy {tag} {j} {u} ej et el es) =
      ok-citeBy ej et (cong just (compatible j u el)) es
    lift-local compatible (ok-pick eo ep a) =
      ok-pick eo ep (lift-local compatible a)

    lift-forest : ∀ {L G owner ss cs} → Compatible L G → ForestOK L owner ss cs →
      TreeForestOK G owner ss cs
    lift-forest compatible ok-nil = ok-nil
    lift-forest compatible (ok-cons a as) =
      ok-cons (lift-local compatible a) (lift-forest compatible as)

  choice-valid : ∀ {s t i c} → samePlayer (turn g s) p ≡ true →
    lookup (next g s) i ≡ just t → check g p goal t c ≡ true →
    check g p goal s (choice i c) ≡ true
  choice-valid {s} {i = i} eo el ec with next g s
  ... | [] = nothing-elim el
  ... | x ∷ xs rewrite eo | el = ec

  mutual
    row-sound : ∀ G owner {s c} →
      (∀ j → I.Order._<_ order j owner → Proven g p goal (G j)) →
      TreeOK G owner s c → Proven g p goal s
    row-sound G owner {s = s} earlier (ok-leaf en eg) = leaf , valid
      where
      valid : check g p goal s leaf ≡ true
      valid rewrite en = eg
    row-sound G owner {s = s} earlier (ok-solve {fuel} ef) =
      Search.witness fuel g p goal s , forcesB-sound fuel g p goal s ef
    row-sound G owner {s = s} earlier (ok-choice {i = i} eo en el a)
      with row-sound G owner earlier a
    ... | c , ec = choice i c , valid
      where
      valid : check g p goal s (choice i c) ≡ true
      valid rewrite en | eo | el = ec
    row-sound G owner {s = s} earlier (ok-fork eo en as)
      with forest-sound G owner earlier as
    ... | cs , ecs = fork cs , valid
      where
      valid : check g p goal s (fork cs) ≡ true
      valid rewrite en | eo = ecs
    row-sound G owner {s = s} earlier (ok-pass ep en a)
      with row-sound G owner earlier a
    ... | c , ec = pass c , valid
      where
      valid : check g p goal s (pass c) ≡ true
      valid rewrite en | ep = ec
    row-sound G owner {s = s} earlier (ok-cite {j} {u} ej el es) =
      subst (Proven g p goal) (sym es)
        (subst (Proven g p goal) (just-injective el) (earlier j ej))
    row-sound G owner {s = s} earlier (ok-citeBy {tag} {j} {u} ej et el es) =
      transport laws tag s
        (subst (Proven g p goal) (sym es)
          (subst (Proven g p goal) (just-injective el) (earlier j ej)))
    row-sound G owner {s = s} earlier (ok-pick {a} {t} epick el a-ok)
      with pick-sound picker s a t el | row-sound G owner earlier a-ok
    ... | i , ei | c , ec = choice i c , choice-valid epick ei ec

    forest-sound : ∀ G owner {ss cs} →
      (∀ j → I.Order._<_ order j owner → Proven g p goal (G j)) →
      TreeForestOK G owner ss cs →
      Σ (List Certificate) (λ ds → checkForest g p goal ss ds ≡ true)
    forest-sound G owner earlier ok-nil = [] , refl
    forest-sound G owner earlier (ok-cons {s} {ss} a as)
      with row-sound G owner earlier a | forest-sound G owner earlier as
    ... | c , ec | cs , ecs = c ∷ cs , valid
      where
      valid : checkForest g p goal (s ∷ ss) (c ∷ cs) ≡ true
      valid rewrite ec = ecs

  global-proven : (G : Key → S) (C : Key → DirectedCertificate Key Move) →
    (∀ i → TreeOK G i (G i) (C i)) →
    ∀ i → Proven g p goal (G i)
  global-proven G C rows i = prove i (I.wellFounded order i)
    where
    prove : ∀ j → I.Acc (I.Order._<_ order) j → Proven g p goal (G j)
    prove j (I.acc children) = row-sound G j
      (λ k ek → prove k (children k ek)) (rows j)

  localRows-proven : (G : Key → S) (C : Key → DirectedCertificate Key Move)
    (L : Key → Resolver Key S) →
    (∀ i → Compatible (L i) G) →
    (∀ i → checkLocal (L i) i (G i) (C i) ≡ true) →
    ∀ i → Proven g p goal (G i)
  localRows-proven G C L compatible accepted = global-proven G C
    (λ i → lift-local (compatible i)
      (checkLocal-sound (L i) i (G i) (C i) (accepted i)))

  global-sound : (G : Key → S) (C : Key → DirectedCertificate Key Move) →
    (∀ i → TreeOK G i (G i) (C i)) →
    ∀ i → Guarantees g p goal (G i)
  global-sound G C rows i with global-proven G C rows i
  ... | c , ec = checkSound g p goal (G i) c ec

open Checker public
