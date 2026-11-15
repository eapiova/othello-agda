{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Faster Boolean evaluation yields the original row judgment.
module Othello.IncrementalIndexed6 where

open import Prelude
open import Agda.Builtin.String using (String)
open import Agda.Builtin.Nat using (_+_)
open import Game.Core using (Player)
open import Game.Symmetry using (Proven; CertificateTransport; act; acceptedTag; transport)
open import Othello.Board using (State; six)
open import Othello.Encode6 using (stateEquality6)
import Game.Balanced as B
import Game.Indexed as I
import Game.IndexedTransfer as IT
import Game.NatOrder as N
import Game.Transfer as T
import Othello.Fast6 as Fast
import Othello.Incremental6 as New
import Othello.NatIndexed6 as D
import Othello.LazyIndexed6 as Lazy
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.CompatibleRows6 as Compatible

private
  abstract
    to-old : ∀ p goal s → Proven New.incrementalGame6 p goal s → Proven Fast.fastGame6 p goal s
    to-old p goal s (c , checked) = c ,
      trans (sym (T.check-cong New.incrementalGame6 Fast.fastGame6 New.agreement p goal s c)) checked

    to-new : ∀ p goal s → Proven Fast.fastGame6 p goal s → Proven New.incrementalGame6 p goal s
    to-new p goal s (c , checked) = c ,
      trans (T.check-cong New.incrementalGame6 Fast.fastGame6 New.agreement p goal s c) checked

    transport-new : ∀ p goal (laws : CertificateTransport Fast.fastGame6 p goal) tag s →
      Proven New.incrementalGame6 p goal (act laws tag s) → Proven New.incrementalGame6 p goal s
    transport-new p goal laws tag s proof =
      to-new p goal s (transport laws tag s (to-old p goal (act laws tag s) proof))

adapt : ∀ p goal → CertificateTransport Fast.fastGame6 p goal →
  CertificateTransport New.incrementalGame6 p goal
adapt p goal laws = record
  { act = act laws
  ; acceptedTag = acceptedTag laws
  ; transport = transport-new p goal laws
  }

module Checking (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Old = Lazy.Checking Fast.fastGame6 p goal laws
  module Optimized = Lazy.Checking New.incrementalGame6 p goal (adapt p goal laws)
  module Compare = IT.Comparing N.order stateEquality6 New.incrementalGame6 Fast.fastGame6 p goal
    (adapt p goal laws) laws New.agreement (λ tag s → refl) (λ tag → refl)
  module Link = Compatible.Checking Fast.fastGame6 p goal laws

  abstract
    rows-agree : ∀ {n} L embed (ss : B.Vec (State six) n) cs →
      Optimized.Lower.checkRows L embed ss cs ≡ Old.Lower.checkRows L embed ss cs
    rows-agree L embed B.nil B.nil = refl
    rows-agree L embed (B.cons s ss) (B.cons c cs)
      rewrite Compare.local-agrees L (embed B.fzero) s c |
        rows-agree L (λ i → embed (B.fsuc i)) ss cs = refl

    part-agrees : ∀ {n} L (embed : B.Fin n → ℕ) (stateText bodyText : String) →
      Optimized.checkPart L embed stateText bodyText ≡ Old.checkPart L embed stateText bodyText
    part-agrees {n} L embed stateText bodyText with D.decodeBodies n bodyText
    ... | nothing = refl
    ... | just cs = cong (λ b → Lazy.validStates n stateText ∧ b)
      (rows-agree L embed (Lazy.states n stateText) cs)

    accepted-old : ∀ {n} L (embed : B.Fin n → ℕ) stateText bodyText →
      Optimized.checkPart L embed stateText bodyText ≡ true →
      Old.checkPart L embed stateText bodyText ≡ true
    accepted-old L embed stateText bodyText checked =
      trans (sym (part-agrees L embed stateText bodyText)) checked

    linkedRows : ∀ {n} base (demand : M.Map (State six))
      (ss oldSS : B.Vec (State six) n) (cs oldCS : B.Vec (I.IndexedCertificate ℕ) n) →
      ss ≡ oldSS → cs ≡ oldCS →
      Optimized.Lower.checkRows (M.lookup demand) (λ i → B.finToNat i + base) ss cs ≡ true →
      (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
      Laws.Compatible demand G → Laws.Compatible (M.rows base n oldSS) G →
      Laws.Compatible (M.rows base n oldCS) C → Old.A.Partial G C (M.rows base n oldSS)
    linkedRows {n} base demand ss oldSS cs oldCS ssEqual csEqual checked =
      Link.linked {n = n} base demand ss oldSS cs oldCS ssEqual csEqual
        (trans (sym (rows-agree (M.lookup demand) (λ i → B.finToNat i + base) ss cs)) checked)
