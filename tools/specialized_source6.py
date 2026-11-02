"""AI-assisted source generator. Every geometry equation needs safe Agda checking."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate():
    source = (ROOT/'src/Othello/IncrementalIndexed6.agda').read_text()
    source = source.replace('module Othello.IncrementalIndexed6 where', 'module Othello.AgreedIndexed6 where')
    source = source.replace('using (Player)', 'using (Player; Game)')
    source = source.replace('import Othello.Incremental6 as New\n', '')
    head, body = source.split('private\n', 1)
    body = ('private\n'+body).replace('New.incrementalGame6', 'g').replace('New.agreement', 'agreement')
    source = head + 'module With (g : Game (State six)) (agreement : T.Agreement g Fast.fastGame6) where\n\n'
    source += '\n'.join('  '+line if line else '' for line in body.splitlines())+'\n'
    (ROOT/'src/Othello/AgreedIndexed6.agda').write_text(source)

    def fin(n):
        return 'F.zero' if n == 0 else '(F.suc '+fin(n-1)+')'

    def q(r,c):
        return 'q'+str(r)+str(c)

    def agda_list(items):
        return ' ∷ '.join(items+['[]'])

    rows=['('+' F.∷ '.join([f'c{r}{c}' for c in range(6)]+['F.[]'])+')' for r in range(6)]
    pattern='('+' F.∷ '.join(rows+['F.[]'])+')'
    text='''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted generated geometry, checked against the original rays.
-- This module supplies no initial-board bound.
module Othello.Specialized6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (coords; passState; nonempty)
import Othello.Rules as Rules
import Othello.Fast6 as Fast
import Othello.Finite as F
import Othello.Incremental6 as Incremental
import Othello.CellRays6 as Rays
import Game.Core as G
import Game.Transfer as T

'''
    for r in range(6):
        for c in range(6):
            name=q(r,c)
            text+=f'{name} : Coord six\n{name} = {fin(r)} , {fin(c)}\n\n'
    for r in range(6):
        for c in range(6):
            name=q(r,c)
            rays=[]
            for dr,dc in [(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)]:
                ray=[]; rr=r+dr; cc=c+dc
                while 0<=rr<6 and 0<=cc<6:
                    ray.append(f'({q(rr,cc)} , c{rr}{cc})');rr+=dr;cc+=dc
                rays.append('('+agda_list(ray)+')')
            text+=f'captures{name} : Board six → Player → List (Coord six)\n'
            text+=f'captures{name} {pattern} p = Rays.capturesRays p\n  ({agda_list(rays)})\n\n'
            text+=f'captures{name}-correct : ∀ b p → captures{name} b p ≡ Fast.allCaptures6 (state b p) {name}\n'
            text+=f'captures{name}-correct b@{pattern} p = Rays.capturesRays-correct (state b p) {name}\n\n'
    text+='''candidateCell : State six → Coord six → Cell → List (Coord six) → List (State six) → List (State six)
candidateCell s q c xs tail with sameCell c empty ∧ nonempty xs
... | false = tail
... | true = state (put {six} (Incremental.flipMany (board s) (toMove s) xs) q (playerCell (toMove s)))
  (other (toMove s)) ∷ tail

candidateCell-correct : ∀ s q xs tail →
  candidateCell s q (at {six} (board s) q) xs tail ≡ Incremental.candidate s q xs tail
candidateCell-correct s q xs tail with sameCell (at {six} (board s) q) empty ∧ nonempty xs
... | false = refl
... | true = refl

record Entry : Set where
  constructor entry
  field
    coord : Coord six
    cell : Cell
    captures : List (Coord six)

movesEntries : State six → List Entry → List (State six)
movesEntries s [] = []
movesEntries s (entry q c caps ∷ rest) = candidateCell s q c caps (movesEntries s rest)

data EntriesOK (s : State six) : List Entry → List (Coord six) → Set where
  ok-nil : EntriesOK s [] []
  ok-cons : ∀ {q c caps rest qs} → c ≡ at {six} (board s) q →
    caps ≡ Fast.allCaptures6 s q → EntriesOK s rest qs →
    EntriesOK s (entry q c caps ∷ rest) (q ∷ qs)

movesEntries-correct : ∀ s es qs → EntriesOK s es qs → movesEntries s es ≡ Incremental.moves s qs
movesEntries-correct s [] [] ok-nil = refl
movesEntries-correct s (entry q c caps ∷ rest) (.q ∷ qs) (ok-cons ce cape restOK)
  rewrite ce | cape | movesEntries-correct s rest qs restOK =
    candidateCell-correct s q (Fast.allCaptures6 s q) (Incremental.moves s qs)

entries : State six → List Entry
'''
    text+=f'entries (state b@{pattern} p) =\n  '+agda_list([f'(entry {q(r,c)} c{r}{c} (captures{q(r,c)} b p))' for r in range(6) for c in range(6)])+'\n\n'
    text+='entries-correct : ∀ s → EntriesOK s (entries s) (coords six)\n'
    proof='ok-nil'
    for r,c in reversed([(r,c) for r in range(6) for c in range(6)]):
        proof=f'ok-cons refl (captures{q(r,c)}-correct b p) ({proof})'
    text+=f'entries-correct (state b@{pattern} p) =\n  {proof}\n\n'
    text+='''moves : State six → List (State six)
moves s = movesEntries s (entries s)

moves-agree : ∀ s → moves s ≡ Fast.moves6 s (coords six)
moves-agree s = trans (movesEntries-correct s (entries s) (coords six) (entries-correct s))
  (Incremental.moves-agree s (coords six))

successors : State six → List (State six)
successors s = Fast.finish6 s (moves s) (moves (passState s))

successors-agree : ∀ s → successors s ≡ Fast.fastSuccessors s
successors-agree s rewrite moves-agree s | moves-agree (passState s) = refl

passShape : List (State six) → List (State six) → Bool
passShape [] [] = false
passShape [] (_ ∷ _) = true
passShape (_ ∷ _) opposing = false

forcedPass : State six → Bool
forcedPass s = passShape (moves s) (moves (passState s))

passShape-correct : ∀ s →
  passShape (map (Rules.applyMove s) (Rules.legalMoves s))
    (map (Rules.applyMove (passState s)) (Rules.legalMoves (passState s))) ≡ Rules.forcedPass s
passShape-correct s with Rules.legalMoves s | Rules.legalMoves (passState s)
... | [] | [] = refl
... | [] | (_ ∷ _) = refl
... | (_ ∷ _) | [] = refl
... | (_ ∷ _) | (_ ∷ _) = refl

forcedPass-agree : ∀ s → forcedPass s ≡ Rules.forcedPass s
forcedPass-agree s rewrite moves-agree s | moves-agree (passState s)
  | Fast.moves6-correct s (coords six) | Fast.moves6-correct (passState s) (coords six) = passShape-correct s

specializedGame6 : G.Game (State six)
specializedGame6 = record { turn = toMove ; next = successors ; forcedPass = forcedPass }

agreement : T.Agreement specializedGame6 Fast.fastGame6
agreement = T.agreement successors-agree (λ s → refl) forcedPass-agree
'''
    (ROOT/'src/Othello/Specialized6.agda').write_text(text)


if __name__=='__main__':
    generate()
