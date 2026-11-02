{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Symbolic partial coverage composes independently checked rows.
module Othello.NatAssembly6 where

open import Prelude
open import Agda.Builtin.Nat using (_+_; _<_)
open import Agda.Builtin.String using (String)
open import Game.Core using (Game; Player; next)
open import Game.Symmetry using (CertificateTransport)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.NatIndexed6 as D
open import Othello.Board using (State; six)

module Assembly (g : Game (State six)) (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport g p goal) where

  module Lower = D.Checking g p goal laws

  Partial : (ℕ → State six) → (ℕ → I.IndexedCertificate ℕ) → M.Map (State six) → Set
  Partial G C map = ∀ key → M.lookup map key ≡ just (G key) →
    Lower.V.TreeOK G key (G key) (C key)

  empty : ∀ G C → Partial G C M.absent
  empty G C key ()

  rows : ∀ {n} base (ss : B.Vec (State six) n) G C →
    (∀ i → Lower.V.TreeOK G (base + B.finToNat i)
      (G (base + B.finToNat i)) (C (base + B.finToNat i))) →
    Partial G C (M.rows base n ss)
  rows {n} base ss G C accepted key hit with Laws.rows-hit base n ss key hit
  ... | i , keyEquals , stateEquals =
    subst (λ k → Lower.V.TreeOK G k (G k) (C k)) (sym keyEquals) (accepted i)

  join : ∀ {G C l r} pivot → Partial G C l → Partial G C r →
    Partial G C (M.branch pivot l r)
  join pivot left right key hit with key < pivot
  ... | true = left key hit
  ... | false = right key hit

  -- The finite checker is unchanged. Map routes justify exact state/body
  -- ownership; sparse compatibility justifies every citation separately.
  linkedRows : ∀ {n} base L stateText bodyText →
    Lower.checkPart {n} L (λ i → base + B.finToNat i) stateText bodyText ≡ true →
    (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Lower.V.Compatible L G →
    (statesMap : M.Map (State six)) →
    (bodiesMap : M.Map (I.IndexedCertificate ℕ)) →
    Laws.Route statesMap base n (D.states n stateText) →
    Laws.Route bodiesMap base n (D.bodies n bodyText) →
    Laws.Compatible statesMap G → Laws.Compatible bodiesMap C →
    Partial G C (M.rows base n (D.states n stateText))
  linkedRows {n} base L stateText bodyText accepted G C compatible
    statesMap bodiesMap stateRoute bodyRoute sameStates sameBodies =
    rows base (D.states n stateText) G C
      (Lower.linkPart L (λ i → base + B.finToNat i) stateText bodyText accepted
        G C compatible (Laws.route-aligned G stateRoute sameStates)
        (Laws.route-aligned C bodyRoute sameBodies))

  linkedAligned : ∀ {n} base (demand : M.Map (State six)) stateText bodyText →
    Lower.checkPart {n} (M.lookup demand) (λ i → base + B.finToNat i) stateText bodyText ≡ true →
    (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned demand G →
    Laws.Aligned (M.rows base n (D.states n stateText)) G →
    Laws.Aligned (M.rows base n (D.bodies n bodyText)) C →
    Partial G C (M.rows base n (D.states n stateText))
  linkedAligned {n} base demand stateText bodyText accepted G C compatible sameState sameBody =
    rows base (D.states n stateText) G C
      (Lower.linkPart (M.lookup demand) (λ i → base + B.finToNat i) stateText bodyText accepted
        G C (Laws.aligned-compatible {map = demand} {G = G} compatible) sameState sameBody)

  -- Missing IDs denote a checked terminal fallback, never an omitted lemma.
  -- Equal domains prohibit a body without its corresponding state.
  complete : (statesMap : M.Map (State six)) →
    (bodiesMap : M.Map (I.IndexedCertificate ℕ)) →
    Laws.Together statesMap bodiesMap → (fallback : State six) →
    next g fallback ≡ [] → goal fallback ≡ true →
    Partial (Laws.totalize statesMap fallback)
      (Laws.totalize bodiesMap I.indexedLeaf) statesMap →
    ∀ key → Lower.V.TreeOK (Laws.totalize statesMap fallback) key
      (Laws.totalize statesMap fallback key) (Laws.totalize bodiesMap I.indexedLeaf key)
  complete statesMap bodiesMap paired fallback terminal won partial key
    with M.lookup statesMap key in es | M.lookup bodiesMap key in ec
  ... | just s | body =
    subst (λ c → Lower.V.TreeOK G key s c) (cong (fromMaybe I.indexedLeaf) ec)
      (subst (λ t → Lower.V.TreeOK G key t (C key)) (cong (fromMaybe fallback) es)
        (partial key (trans es
          (cong just (sym (Laws.self-compatible statesMap fallback key s es))))))
    where
    G = Laws.totalize statesMap fallback
    C = Laws.totalize bodiesMap I.indexedLeaf
  ... | nothing | nothing = Lower.V.ok-leaf terminal won
  ... | nothing | just c = contradiction
    (trans (sym (cong Laws.isJust es))
      (trans (Laws.same-domain paired key) (cong Laws.isJust ec)))
    where
    contradiction : ∀ {A : Set} → false ≡ true → A
    contradiction ()
