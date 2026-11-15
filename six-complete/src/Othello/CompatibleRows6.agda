{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Neutral-key interfaces keep large owner bases out of Fin APIs.
module Othello.CompatibleRows6 where

open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Game.Core using (Game; Player)
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; six)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.LazyIndexed6 as Lazy

private
  abstract
    zero-right : ∀ n → n + zero ≡ n
    zero-right zero = refl
    zero-right (suc n) = cong suc (zero-right n)

    suc-right : ∀ n m → n + suc m ≡ suc (n + m)
    suc-right zero m = refl
    suc-right (suc n) m = cong suc (suc-right n m)

    plus-comm : ∀ n m → n + m ≡ m + n
    plus-comm zero m = sym (zero-right m)
    plus-comm (suc n) m = trans (cong suc (plus-comm n m)) (sym (suc-right m n))

module Checking (g : Game (State six)) (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport g p goal) where

  module L = Lazy.Checking g p goal laws
  module V = L.Lower.V

  abstract
    linked : ∀ {n} base (demand : M.Map (State six))
      (ss oldSS : B.Vec (State six) n) (cs oldCS : B.Vec (I.IndexedCertificate ℕ) n) →
      ss ≡ oldSS → cs ≡ oldCS →
      L.Lower.checkRows (M.lookup demand) (λ i → B.finToNat i + base) ss cs ≡ true →
      (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
      Laws.Compatible demand G → Laws.Compatible (M.rows base n oldSS) G →
      Laws.Compatible (M.rows base n oldCS) C → L.A.Partial G C (M.rows base n oldSS)
    linked {n} base demand ss oldSS cs oldCS ssEqual csEqual accepted G C sameDemand sameStates sameBodies =
      L.A.rows base oldSS G C row
      where
      resolver : I.Resolver ℕ (State six)
      resolver = M.lookup demand
      embed : B.Fin n → ℕ
      embed i = B.finToNat i + base

      stateExact : (i : B.Fin n) → G (base + B.finToNat i) ≡ B.lookupVec ss i
      stateExact i = trans (Laws.rows-aligned base oldSS G sameStates i)
        (cong (λ xs → B.lookupVec xs i) (sym ssEqual))
      bodyExact : (i : B.Fin n) → C (base + B.finToNat i) ≡ B.lookupVec cs i
      bodyExact i = trans (Laws.rows-aligned base oldCS C sameBodies i)
        (cong (λ xs → B.lookupVec xs i) (sym csEqual))

      local : (i : B.Fin n) → V.TreeOK G (base + B.finToNat i)
        (B.lookupVec ss i) (B.lookupVec cs i)
      local i = subst (λ k → V.TreeOK G k (B.lookupVec ss i) (B.lookupVec cs i))
        (plus-comm (B.finToNat i) base)
        (V.lift-local {L = resolver} {G = G} sameDemand
          (V.checkLocal-sound resolver (embed i) (B.lookupVec ss i) (B.lookupVec cs i)
            (L.Lower.checkRows-row resolver embed ss cs accepted i)))

      row : (i : B.Fin n) → V.TreeOK G (base + B.finToNat i)
        (G (base + B.finToNat i)) (C (base + B.finToNat i))
      row i = subst (λ s → V.TreeOK G (base + B.finToNat i) s (C (base + B.finToNat i)))
        (sym (stateExact i))
        (subst (λ c → V.TreeOK G (base + B.finToNat i) (B.lookupVec ss i) c)
          (sym (bodyExact i)) (local i))
