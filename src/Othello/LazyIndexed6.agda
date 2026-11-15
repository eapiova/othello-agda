{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Imported state vectors decode only the requested row. Own
-- rows retain a complete syntax check; all game and citation checks are reused.
module Othello.LazyIndexed6 where

open import Prelude
open import Agda.Builtin.Char using (Char)
open import Agda.Builtin.String using (String; primStringToList)
open import Agda.Builtin.Nat using (_+_)
open import Game.Core using (Game; Player)
open import Game.Symmetry using (CertificateTransport)
open import Othello.Board using (State; six; initial)
open import Othello.CompactShared6 using (readCompactState)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.NatIndexed6 as D
import Othello.NatAssembly6 as Old

private
  take : ∀ {A : Set} → ℕ → List A → List A
  take zero xs = []
  take (suc n) [] = []
  take (suc n) (x ∷ xs) = x ∷ take n xs

  drop : ∀ {A : Set} → ℕ → List A → List A
  drop zero xs = xs
  drop (suc n) [] = []
  drop (suc n) (x ∷ xs) = drop n xs

  readOne : List Char → Maybe (State six)
  readOne chars with readCompactState (take 13 chars)
  ... | just (s , []) = just s
  ... | _ = nothing

  validChars : ℕ → List Char → Bool
  validChars zero [] = true
  validChars zero (_ ∷ _) = false
  validChars (suc n) chars with readOne chars
  ... | nothing = false
  ... | just s = validChars n (drop 13 chars)

  statesChars : (n : ℕ) → List Char → B.Vec (State six) n
  statesChars zero chars = B.nil
  statesChars (suc n) chars = B.cons
    (fromMaybe (initial six) (readOne chars)) (statesChars n (drop 13 chars))

-- Each encoded state has one player and twelve ternary-triplet characters.
-- These total data definitions are not proof assumptions. checkPart validates
-- every own row, and the unchanged sound checker validates every cited state.
states : (n : ℕ) → String → B.Vec (State six) n
states n text = statesChars n (primStringToList text)

validStates : ℕ → String → Bool
validStates n text = validChars n (primStringToList text)

module Checking (g : Game (State six)) (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport g p goal) where

  module Lower = D.Checking g p goal laws
  module A = Old.Assembly g p goal laws

  checkPart : ∀ {n} → I.Resolver ℕ (State six) →
    (B.Fin n → ℕ) → String → String → Bool
  checkPart {n} L embed stateText bodyText with D.decodeBodies n bodyText
  ... | nothing = false
  ... | just cs = validStates n stateText ∧
    Lower.checkRows L embed (states n stateText) cs

  private
    and-right : ∀ a b → a ∧ b ≡ true → b ≡ true
    and-right true b e = e
    and-right false b ()

    false-elim : ∀ {A : Set} → false ≡ true → A
    false-elim ()

  checkPart-row : ∀ {n} L embed stateText bodyText →
    checkPart {n} L embed stateText bodyText ≡ true → ∀ i →
    Lower.V.checkLocal L (embed i) (B.lookupVec (states n stateText) i)
      (B.lookupVec (D.bodies n bodyText) i) ≡ true
  checkPart-row {n} L embed stateText bodyText e with D.decodeBodies n bodyText in ec
  ... | nothing = false-elim e
  ... | just cs rewrite ec = Lower.checkRows-row L embed (states n stateText) cs
    (and-right (validStates n stateText) (Lower.checkRows L embed (states n stateText) cs) e)

  linkPart : ∀ {n} L embed stateText bodyText →
    checkPart {n} L embed stateText bodyText ≡ true →
    (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Lower.V.Compatible L G →
    (∀ i → G (embed i) ≡ B.lookupVec (states n stateText) i) →
    (∀ i → C (embed i) ≡ B.lookupVec (D.bodies n bodyText) i) →
    ∀ i → Lower.V.TreeOK G (embed i) (G (embed i)) (C (embed i))
  linkPart {n} L embed stateText bodyText accepted G C compatible sameState sameBody i =
    subst (λ s → Lower.V.TreeOK G (embed i) s (C (embed i))) (sym (sameState i))
      (subst (λ c → Lower.V.TreeOK G (embed i) (B.lookupVec (states n stateText) i) c)
        (sym (sameBody i)) (Lower.V.lift-local compatible
          (Lower.V.checkLocal-sound L (embed i) (B.lookupVec (states n stateText) i)
            (B.lookupVec (D.bodies n bodyText) i)
            (checkPart-row L embed stateText bodyText accepted i))))

  linkedAligned : ∀ {n} base (demand : M.Map (State six)) stateText bodyText →
    checkPart {n} (M.lookup demand) (λ i → base + B.finToNat i) stateText bodyText ≡ true →
    (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned demand G → Laws.Aligned (M.rows base n (states n stateText)) G →
    Laws.Aligned (M.rows base n (D.bodies n bodyText)) C →
    A.Partial G C (M.rows base n (states n stateText))
  linkedAligned {n} base demand stateText bodyText accepted G C compatible sameState sameBody =
    A.rows base (states n stateText) G C
      (linkPart (M.lookup demand) (λ i → base + B.finToNat i) stateText bodyText accepted
        G C (Laws.aligned-compatible {map = demand} {G = G} compatible) sameState sameBody)
