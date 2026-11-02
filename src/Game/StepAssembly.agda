{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Assemble checked winning steps over one common state map.
module Game.StepAssembly where

open import Game.Core
open import Agda.Builtin.Nat using (_+_; _<_)
open import Game.Symmetry using (Proven; CertificateTransport)
open import Game.Composite using (StateEquality)
import Game.Indexed as I
import Game.DirectedIndexed as D
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatOrder as N
import Game.NatAccessibility as Access

module Assembly {S : Set} (g : Game S) (p : Player) (goal : S → Bool) where

  Step : (ℕ → S) → ℕ → Set
  Step G owner = (∀ j → N.Before j owner → Proven g p goal (G j)) →
    Proven g p goal (G owner)

  Partial : (ℕ → S) → M.Map S → Set
  Partial G table = ∀ key → M.lookup table key ≡ just (G key) → Step G key

  empty : ∀ G → Partial G M.absent
  empty G key ()

  join : ∀ {G l r} pivot → Partial G l → Partial G r → Partial G (M.branch pivot l r)
  join pivot left right key hit with key < pivot
  ... | true = left key hit
  ... | false = right key hit

  rows : ∀ {n} base (ss : B.Vec S n) G →
    (∀ i → Step G (base + B.finToNat i)) → Partial G (M.rows base n ss)
  rows {n} base ss G accepted key hit with Laws.rows-hit base n ss key hit
  ... | i , keyEquals , stateEquals = subst (Step G) (sym keyEquals) (accepted i)

  -- Absent IDs are a genuinely checked winning fallback, not omitted rows.
  complete : (table : M.Map S) (fallback : S) → Proven g p goal fallback →
    Partial (Laws.totalize table fallback) table →
    ∀ key → Step (Laws.totalize table fallback) key
  complete table fallback won partial key earlier with M.lookup table key in found
  ... | just s = subst (Proven g p goal) (cong (fromMaybe fallback) found)
      (partial key (trans found
        (cong just (sym (Laws.self-compatible table fallback key s found)))) earlier)
  ... | nothing = won

  global-proven : (G : ℕ → S) → (∀ i → Step G i) → ∀ i → Proven g p goal (G i)
  global-proven G steps i = prove i (Access.wellFounded i)
    where
    prove : ∀ j → I.Acc N.Before j → Proven g p goal (G j)
    prove j (I.acc children) = steps j (λ k earlier → prove k (children k earlier))

  -- The certificate stays local to the row proof; no global body map occurs
  -- in Step, Partial or complete. State compatibility remains an obligation.
  module Ordinary (eq : StateEquality S) (laws : CertificateTransport g p goal) where
    module Rows = I.Checker N.order eq g p goal laws
    from-row : ∀ G i {c} → Rows.TreeOK G i (G i) c → Step G i
    from-row G i checked earlier = Rows.row-sound G i earlier checked

  module Directed {Move : Set} (eq : StateEquality S)
    (laws : CertificateTransport g p goal) (picker : D.MovePicker g Move) where
    module Rows = D.Checker N.order eq g p goal laws picker
    from-row : ∀ G i {c} → Rows.TreeOK G i (G i) c → Step G i
    from-row G i checked earlier = Rows.row-sound G i earlier checked
