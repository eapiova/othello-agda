"""AI-assisted shared ray closure over certified cached empty coordinates."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def fin(n):
    return 'F.zero' if n == 0 else '(F.suc '+fin(n-1)+')'


def generate():
    old = (ROOT/'src/Othello/LengthRules6.agda').read_text()
    captures = dict(re.findall(r'captures(q\d\d) [^\n]+ p =\n  ([^\n]+)\n', old))
    assert len(captures) == 36
    rows = ['('+' F.∷ '.join([f'c{r}{c}' for c in range(6)]+['F.[]'])+')' for r in range(6)]
    pattern = '('+' F.∷ '.join(rows+['F.[]'])+')'
    source = '''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Ordered game refinement with certified empty-coordinate caches.
module Othello.CachedGame6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (coords; passState; nonempty)
open import Game.Core using (Game; lookup)
open import Game.Symmetry using (CertificateTransport; act)
import Game.MappedTransfer as T
import Game.DirectedIndexed as D
import Othello.EmptyCache6 as S
import Othello.Finite as F
import Othello.LengthRays6 as Lines
import Othello.LengthRules6 as Old
import Othello.LengthMoves6 as Moves
import Othello.Incremental6 as Inc
import Othello.Fast6 as Fast
import Othello.AgreedIndexed6 as A
open Old using ('''+ '; '.join(f'q{r}{c}' for r in range(6) for c in range(6))+''')

rays : State six → Coord six → List (Coord six)
'''
    source += f'rays (state {pattern} p) = λ\n  '+'\n  ; '.join(('{ ' if r == c == 0 else '')+f'({fin(r)} , {fin(c)}) → {captures[f"q{r}{c}"]}' for r in range(6) for c in range(6))+'\n  }\n\n'
    source += 'abstract\n  rays-agree : ∀ s q → rays s q ≡ Fast.allCaptures6 s q\n'
    for r in range(6):
        for c in range(6):
            source += f'  rays-agree s@(state {pattern} p) ({fin(r)} , {fin(c)}) = Old.capturesq{r}{c}-correct (board s) p\n'
    source += '''
plain : State six → List (Coord six) → (Coord six → List (Coord six)) → List (State six)
plain s [] cap = []
plain s (q ∷ qs) cap = Inc.candidate s q (cap q) (plain s qs cap)

loop : S.Cached → List (Coord six) → (Coord six → List (Coord six)) → List S.Cached
loop s [] cap = []
loop s (q ∷ qs) cap with sameCell (at {six} (board (S.raw s)) q) empty ∧ nonempty (cap q)
... | false = loop s qs cap
... | true = S.play s q (cap q) ∷ loop s qs cap

moves : S.Cached → List S.Cached
moves s = loop s (S.vacancies s) (rays (S.raw s))

private
  cong₂ : ∀ {X Y Z : Set} (f : X → Y → Z) {x x′ y y′} →
    x ≡ x′ → y ≡ y′ → f x y ≡ f x′ y′
  cong₂ f refl refl = refl

  loop-maps : ∀ s qs cap → map S.raw (loop s qs cap) ≡ plain (S.raw s) qs cap
  loop-maps s [] cap = refl
  loop-maps s (q ∷ qs) cap
    with sameCell (at {six} (board (S.raw s)) q) empty ∧ nonempty (cap q)
  ... | false = loop-maps s qs cap
  ... | true = cong₂ _∷_ (S.play-decodes s q (cap q)) (loop-maps s qs cap)

  plain-filter : ∀ s qs cap →
    plain s (S.select (λ q → sameCell (at {six} (board s) q) empty) qs) cap ≡ plain s qs cap
  plain-filter s [] cap = refl
  plain-filter s (q ∷ qs) cap with sameCell (at {six} (board s) q) empty in emptyChecked
  ... | false = plain-filter s qs cap
  ... | true with nonempty (cap q) in nonemptyChecked
  ...   | false rewrite emptyChecked | nonemptyChecked = plain-filter s qs cap
  ...   | true rewrite emptyChecked | nonemptyChecked = cong (λ tail → state
    (put {six} (Inc.flipMany (board s) (toMove s) (cap q)) q (playerCell (toMove s)))
    (other (toMove s)) ∷ tail) (plain-filter s qs cap)

  plain-rays : ∀ s qs → plain s qs (rays s) ≡ Inc.moves s qs
  plain-rays s [] = refl
  plain-rays s (q ∷ qs) rewrite rays-agree s q | plain-rays s qs = refl

abstract
  moves-maps : ∀ s → map S.raw (moves s) ≡ Old.moves (S.raw s)
  moves-maps s = trans (loop-maps s (S.vacancies s) (rays (S.raw s)))
    (trans (cong (λ qs → plain (S.raw s) qs (rays (S.raw s))) (sym (S.cache-correct s)))
      (trans (plain-filter (S.raw s) (coords six) (rays (S.raw s)))
        (trans (plain-rays (S.raw s) (coords six))
          (trans (Inc.moves-agree (S.raw s) (coords six)) (sym (Old.moves-agree (S.raw s)))))))

finish : S.Cached → List S.Cached → List S.Cached → List S.Cached
finish s [] [] = []
finish s [] (_ ∷ _) = S.pass s ∷ []
finish s (t ∷ ts) opposing = t ∷ ts

passShape : List S.Cached → List S.Cached → Bool
passShape [] [] = false
passShape [] (_ ∷ _) = true
passShape (_ ∷ _) opposing = false

successors : S.Cached → List S.Cached
successors s = finish s (moves s) (moves (S.pass s))

forcedPass : S.Cached → Bool
forcedPass s = passShape (moves s) (moves (S.pass s))

private
  finish-maps : ∀ s ss opposing → map S.raw (finish s ss opposing) ≡
    Fast.finish6 (S.raw s) (map S.raw ss) (map S.raw opposing)
  finish-maps s [] [] = refl
  finish-maps s [] (_ ∷ _) = cong (λ t → t ∷ []) (S.pass-decodes s)
  finish-maps s (_ ∷ _) opposing = refl

  passShape-maps : ∀ ss opposing → passShape ss opposing ≡
    Old.passShape (map S.raw ss) (map S.raw opposing)
  passShape-maps [] [] = refl
  passShape-maps [] (_ ∷ _) = refl
  passShape-maps (_ ∷ _) opposing = refl

abstract
  successors-maps : ∀ s → map S.raw (successors s) ≡ Old.successors (S.raw s)
  successors-maps s = trans (finish-maps s (moves s) (moves (S.pass s)))
    (cong₂ (Fast.finish6 (S.raw s)) (moves-maps s)
      (trans (moves-maps (S.pass s)) (cong Old.moves (S.pass-decodes s))))

  pass-maps : ∀ s → forcedPass s ≡ Old.forcedPass (S.raw s)
  pass-maps s = trans (passShape-maps (moves s) (moves (S.pass s)))
    (cong₂ Old.passShape (moves-maps s)
      (trans (moves-maps (S.pass s)) (cong Old.moves (S.pass-decodes s))))

game : Game S.Cached
game = record { turn = λ s → toMove (S.raw s) ; next = successors ; forcedPass = forcedPass }

refinement : T.Refinement game Old.specializedGame6 S.raw
refinement = T.refinement successors-maps (λ s → refl) pass-maps

pick : S.Cached → Coord six → Maybe S.Cached
pick s q with sameCell (at {six} (board (S.raw s)) q) empty ∧ nonempty (Moves.capturesAt (S.raw s) q)
... | false = nothing
... | true = just (S.play s q (Moves.capturesAt (S.raw s) q))

private
  pick-maps : ∀ s q → T.mapMaybe S.raw (pick s q) ≡ Moves.pick (S.raw s) q
  pick-maps s q with sameCell (at {six} (board (S.raw s)) q) empty ∧ nonempty (Moves.capturesAt (S.raw s) q)
  ... | false = refl
  ... | true = cong just (S.play-decodes s q (Moves.capturesAt (S.raw s) q))

  just-injective : ∀ {X : Set} {x y : X} → just x ≡ just y → x ≡ y
  just-injective refl = refl

  lookup-injective : ∀ xs i t → lookup (map S.raw xs) i ≡ just (S.raw t) → lookup xs i ≡ just t
  lookup-injective [] i t ()
  lookup-injective (x ∷ xs) zero t checked = cong just (S.injective x t (just-injective checked))
  lookup-injective (x ∷ xs) (suc i) t checked = lookup-injective xs i t checked

  pick-sound : ∀ s q t → pick s q ≡ just t → Σ ℕ (λ i → lookup (successors s) i ≡ just t)
  pick-sound s q t checked with Moves.pick-sound (S.raw s) q (S.raw t)
    (trans (sym (pick-maps s q)) (cong (T.mapMaybe S.raw) checked))
  ... | i , hit = i , lookup-injective (successors s) i t
    (trans (cong (λ xs → lookup xs i) (successors-maps s)) hit)

picker : D.MovePicker game (Coord six)
picker = D.movePicker pick pick-sound

module Transport (p : Player) (goal : State six → Bool)
  (laws : CertificateTransport Fast.fastGame6 p goal) where

  module Agreed = A.With Old.specializedGame6 Old.agreement
  oldLaws : CertificateTransport Old.specializedGame6 p goal
  oldLaws = Agreed.adapt p goal laws

  action : ℕ → S.Cached → S.Cached
  action tag s = S.pack (act oldLaws tag (S.raw s))

  module Adapt = T.Adapting game Old.specializedGame6 S.raw refinement
    p goal oldLaws action (λ tag s → refl)

  cachedLaws : CertificateTransport game p (λ s → goal (S.raw s))
  cachedLaws = Adapt.laws
'''
    (ROOT/'src/Othello/CachedGame6.agda').write_text(source)


if __name__ == '__main__':
    generate()
