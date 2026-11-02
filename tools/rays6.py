#!/usr/bin/env python3
"""Generate the literal 6×6 ray table and exhaustive definitional proof."""
from pathlib import Path
D = [('north',-1,0),('northEast',-1,1),('east',0,1),('southEast',1,1),('south',1,0),('southWest',1,-1),('west',0,-1),('northWest',-1,-1)]
def f(n):
    return 'F.zero' if n == 0 else '(F.suc ' + f(n-1) + ')'
def q(r,c): return '(' + f(r) + ' , ' + f(c) + ')'
lines=['{-# OPTIONS --safe --without-K --cubical-compatible #-}', 'module Othello.Rays6 where', '', 'open import Prelude', 'open import Othello.Rules using (Direction; north; northEast; east; southEast; south; southWest; west; northWest; Coord; six; ray)', 'import Othello.Finite as F', '', '-- Generated literal coordinates; each proof clause checks the original geometry.', 'ray6 : Direction → Coord six → List (Coord six)']
for d,dr,dc in D:
 for r in range(6):
  for c in range(6):
   rr,cc=r+dr,c+dc; xs=[]
   while 0<=rr<6 and 0<=cc<6:
    xs.append(q(rr,cc)); rr+=dr; cc+=dc
   lines.append('ray6 '+d+' '+q(r,c)+' = '+' ∷ '.join(xs+['[]']))
lines += ['', 'ray6-correct : (d : Direction) (q : Coord six) → ray6 d q ≡ ray {six} d q']
for d,_,_ in D:
 for r in range(6):
  for c in range(6): lines.append('ray6-correct '+d+' '+q(r,c)+' = refl')
Path('src/Othello/Rays6.agda').write_text('\n'.join(lines)+'\n')
