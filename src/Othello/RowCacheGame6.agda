{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Ordered move refinement with cached codes and retained cells.
module Othello.RowCacheGame6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (nonempty)
open import Game.Core using (Game; lookup)
open import Game.Symmetry using (CertificateTransport; act)
import Game.MappedTransfer as T
import Game.DirectedIndexed as D
import Othello.RowCacheState6 as S
import Othello.LengthRules6 as Old
import Othello.LengthMoves6 as Moves
import Othello.InlineEntries6 as Inline
import Othello.Fast6 as Fast
import Othello.AgreedIndexed6 as A

private
  cong₂ : ∀ {X Y Z : Set} (f : X → Y → Z) {x x′ y y′} →
    x ≡ x′ → y ≡ y′ → f x y ≡ f x′ y′
  cong₂ f refl refl = refl

movesEntries : S.CachedState → List Old.Entry → List S.CachedState
movesEntries s [] = []
movesEntries s (Old.entry q c caps ∷ es) with sameCell c empty ∧ nonempty caps
... | false = movesEntries s es
... | true = S.play s q caps ∷ movesEntries s es

moves : S.CachedState → List S.CachedState
moves s = movesEntries s (Inline.entries (S.decode s))

private
  entries-maps : ∀ s es → map S.decode (movesEntries s es) ≡ Old.movesEntries (S.decode s) es
  entries-maps s [] = refl
  entries-maps s (Old.entry q c caps ∷ es) with sameCell c empty ∧ nonempty caps
  ... | false = entries-maps s es
  ... | true = cong₂ _∷_ (S.play-decodes s q caps) (entries-maps s es)

abstract
  moves-maps : ∀ s → map S.decode (moves s) ≡ Old.moves (S.decode s)
  moves-maps s = trans (entries-maps s (Inline.entries (S.decode s))) (Inline.moves-agree (S.decode s))

finish : S.CachedState → List S.CachedState → List S.CachedState → List S.CachedState
finish s [] [] = []
finish s [] (_ ∷ _) = S.pass s ∷ []
finish s (t ∷ ts) opposing = t ∷ ts

passShape : List S.CachedState → List S.CachedState → Bool
passShape [] [] = false
passShape [] (_ ∷ _) = true
passShape (_ ∷ _) opposing = false

successors : S.CachedState → List S.CachedState
successors s = finish s (moves s) (moves (S.pass s))

forcedPass : S.CachedState → Bool
forcedPass s = passShape (moves s) (moves (S.pass s))

private
  finish-maps : ∀ s ss opposing → map S.decode (finish s ss opposing) ≡
    Fast.finish6 (S.decode s) (map S.decode ss) (map S.decode opposing)
  finish-maps s [] [] = refl
  finish-maps s [] (_ ∷ _) = cong (λ t → t ∷ []) (S.pass-decodes s)
  finish-maps s (_ ∷ _) opposing = refl

  passShape-maps : ∀ ss opposing → passShape ss opposing ≡
    Old.passShape (map S.decode ss) (map S.decode opposing)
  passShape-maps [] [] = refl
  passShape-maps [] (_ ∷ _) = refl
  passShape-maps (_ ∷ _) opposing = refl

abstract
  successors-maps : ∀ s → map S.decode (successors s) ≡ Old.successors (S.decode s)
  successors-maps s = trans (finish-maps s (moves s) (moves (S.pass s)))
    (cong₂ (Fast.finish6 (S.decode s)) (moves-maps s)
      (trans (moves-maps (S.pass s)) (cong Old.moves (S.pass-decodes s))))

  pass-maps : ∀ s → forcedPass s ≡ Old.forcedPass (S.decode s)
  pass-maps s = trans (passShape-maps (moves s) (moves (S.pass s)))
    (cong₂ Old.passShape (moves-maps s)
      (trans (moves-maps (S.pass s)) (cong Old.moves (S.pass-decodes s))))

game : Game S.CachedState
game = record { turn = λ s → toMove (S.decode s) ; next = successors ; forcedPass = forcedPass }

refinement : T.Refinement game Old.specializedGame6 S.decode
refinement = T.refinement successors-maps (λ s → refl) pass-maps

pick : S.CachedState → Coord six → Maybe S.CachedState
pick s q with sameCell (at {six} (board (S.decode s)) q) empty ∧ nonempty (Moves.capturesAt (S.decode s) q)
... | false = nothing
... | true = just (S.play s q (Moves.capturesAt (S.decode s) q))

private
  pick-maps : ∀ s q → T.mapMaybe S.decode (pick s q) ≡ Moves.pick (S.decode s) q
  pick-maps s q with sameCell (at {six} (board (S.decode s)) q) empty ∧ nonempty (Moves.capturesAt (S.decode s) q)
  ... | false = refl
  ... | true = cong just (S.play-decodes s q (Moves.capturesAt (S.decode s) q))

  just-injective : ∀ {X : Set} {x y : X} → just x ≡ just y → x ≡ y
  just-injective refl = refl

  lookup-injective : ∀ xs i t → lookup (map S.decode xs) i ≡ just (S.decode t) → lookup xs i ≡ just t
  lookup-injective [] i t ()
  lookup-injective (x ∷ xs) zero t checked = cong just (S.injective x t (just-injective checked))
  lookup-injective (x ∷ xs) (suc i) t checked = lookup-injective xs i t checked

  pick-sound : ∀ s q t → pick s q ≡ just t → Σ ℕ (λ i → lookup (successors s) i ≡ just t)
  pick-sound s q t checked with Moves.pick-sound (S.decode s) q (S.decode t)
    (trans (sym (pick-maps s q)) (cong (T.mapMaybe S.decode) checked))
  ... | i , hit = i , lookup-injective (successors s) i t
    (trans (cong (λ xs → lookup xs i) (successors-maps s)) hit)

picker : D.MovePicker game (Coord six)
picker = D.movePicker pick pick-sound

module Transport (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Agreed = A.With Old.specializedGame6 Old.agreement
  oldLaws : CertificateTransport Old.specializedGame6 p goal
  oldLaws = Agreed.adapt p goal laws

  action : ℕ → S.CachedState → S.CachedState
  action tag s = S.pack (act oldLaws tag (S.decode s))

  module Adapt = T.Adapting game Old.specializedGame6 S.decode refinement
    p goal oldLaws action (λ tag s → S.decode-pack (act oldLaws tag (S.decode s)))

  cachedLaws : CertificateTransport game p (λ s → goal (S.decode s))
  cachedLaws = Adapt.laws
