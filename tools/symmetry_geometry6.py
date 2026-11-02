#!/usr/bin/env python3
"""Generate finite D4 tables whose claims are checked by Agda, not trusted.

AI-assisted. This generator emits only definitions and exhaustive refl proofs.
It does not solve Othello or assert an arbitrary-board rule symmetry theorem.
"""
from pathlib import Path

NAMES = ["identity", "rotate90", "rotate180", "rotate270", "reflectVertical",
         "reflectDiagonal", "reflectHorizontal", "reflectAntiDiagonal"]


def coord(tag, r, c):
    return [(r,c), (c,5-r), (5-r,5-c), (5-c,r), (r,5-c),
            (c,r), (5-r,c), (5-c,5-r)][tag]


def symbolic(tag, r=("r",0), c=("c",0)):
    flip=lambda x:(x[0],x[1]+1)
    return [(r,c), (c,flip(r)), (flip(r),flip(c)), (flip(c),r),
            (r,flip(c)), (c,r), (flip(r),c), (flip(c),flip(r))][tag]


def rewrites(expr):
    axes=[axis for axis,n in expr if n==2]
    return (" rewrite " + " | ".join("mirror-involutive "+a for a in axes)) if axes else ""


def fin(i):
    return "V.suc (" * i + "V.zero" + ")" * i


def generate():
    out = ['''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Exhaustive finite tables; each equation is kernel checked.
module Othello.SymmetryGeometry6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (Direction; north; northEast; east; southEast;
  south; southWest; west; northWest; step; Delta; down; same; up; deltas; axis)
import Othello.Finite as V

data D4 : Set where
  identity rotate90 rotate180 rotate270 reflectVertical reflectDiagonal
    reflectHorizontal reflectAntiDiagonal : D4

mirror : V.Fin 6 → V.Fin 6
''']
    out += [f'mirror ({fin(i)}) = {fin(5-i)}\n' for i in range(6)]
    out += ['''
mirror-involutive : ∀ i → mirror (mirror i) ≡ i
''']
    out += [f'mirror-involutive ({fin(i)}) = refl\n' for i in range(6)]
    out += ['''
coordinate : D4 → Coord six → Coord six
coordinate identity (r , c) = r , c
coordinate rotate90 (r , c) = c , mirror r
coordinate rotate180 (r , c) = mirror r , mirror c
coordinate rotate270 (r , c) = mirror c , r
coordinate reflectVertical (r , c) = r , mirror c
coordinate reflectDiagonal (r , c) = c , r
coordinate reflectHorizontal (r , c) = mirror r , c
coordinate reflectAntiDiagonal (r , c) = mirror c , mirror r

inverse : D4 → D4
inverse identity = identity
inverse rotate90 = rotate270
inverse rotate180 = rotate180
inverse rotate270 = rotate90
inverse reflectVertical = reflectVertical
inverse reflectDiagonal = reflectDiagonal
inverse reflectHorizontal = reflectHorizontal
inverse reflectAntiDiagonal = reflectAntiDiagonal

inverse-involutive : ∀ σ → inverse (inverse σ) ≡ σ
''']
    out += [f'inverse-involutive {n} = refl\n' for n in NAMES]
    out += ['''
coordinate-inverse : ∀ σ q → coordinate (inverse σ) (coordinate σ q) ≡ q
''']
    for a,n in enumerate(NAMES):
        inv=[0,3,2,1,4,5,6,7][a]
        out.append(f'coordinate-inverse {n} (r , c){rewrites(symbolic(inv,*symbolic(a)))} = refl\n')
    out += ['''
coordinate-inverse-right : ∀ σ q → coordinate σ (coordinate (inverse σ) q) ≡ q
coordinate-inverse-right σ q = trans
  (sym (cong (λ τ → coordinate τ (coordinate (inverse σ) q)) (inverse-involutive σ)))
  (coordinate-inverse (inverse σ) q)

compose : D4 → D4 → D4
''']
    table={}
    for a in range(8):
        for b in range(8):
            target=next(k for k in range(8) if all(coord(a,*coord(b,r,c))==coord(k,r,c) for r in range(6) for c in range(6)))
            table[a,b]=target
            out.append(f'compose {NAMES[a]} {NAMES[b]} = {NAMES[target]}\n')
    out += ['''
coordinate-compose : ∀ σ τ q →
  coordinate σ (coordinate τ q) ≡ coordinate (compose σ τ) q
''']
    for ai,a in enumerate(NAMES):
        for bi,b in enumerate(NAMES):
            out.append(f'coordinate-compose {a} {b} (r , c){rewrites(symbolic(ai,*symbolic(bi)))} = refl\n')
    out += ['''
inverse-compose : ∀ σ τ → inverse (compose σ τ) ≡ compose (inverse τ) (inverse σ)
''']
    for a in NAMES:
        for b in NAMES:
            out.append(f'inverse-compose {a} {b} = refl\n')
    dirs=['north','northEast','east','southEast','south','southWest','west','northWest']
    deltas=[(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)]
    out += ['\ndirection : D4 → Direction → Direction\n']
    for a in range(8):
        rr,cc=coord(a,2,2)
        for d,(dr,dc) in enumerate(deltas):
            r,c=coord(a,2+dr,2+dc)
            td=deltas.index((r-rr,c-cc))
            out.append(f'direction {NAMES[a]} {dirs[d]} = {dirs[td]}\n')
    out += ['''
mapMaybe : ∀ {A B : Set} → (A → B) → Maybe A → Maybe B
mapMaybe f nothing = nothing
mapMaybe f (just x) = just (f x)

mirrorDelta : Delta → Delta
mirrorDelta down = up
mirrorDelta same = same
mirrorDelta up = down

axis-mirror : ∀ d i → axis (mirrorDelta d) (mirror i) ≡ mapMaybe mirror (axis d i)
''']
    for d in ['down','same','up']:
        for i in range(6):
            out.append(f'axis-mirror {d} ({fin(i)}) = refl\n')
    out += ['''
step-equivariant : ∀ σ d q → step {size = six} (direction σ d) (coordinate σ q) ≡
  mapMaybe (coordinate σ) (step {size = six} d q)
''']
    for ai,a in enumerate(NAMES):
        for di,d in enumerate(dirs):
            dr,dc=deltas[di]
            mirrored={axis for axis,n in symbolic(ai) if n==1}
            rewrite=[]
            if 'r' in mirrored and dr != 0:
                rewrite.append(f'axis-mirror (proj₁ (deltas {d})) r')
            if 'c' in mirrored and dc != 0:
                rewrite.append(f'axis-mirror (proj₂ (deltas {d})) c')
            out.append(f'step-equivariant {a} {d} (r , c)\n')
            if rewrite:
                out.append('  rewrite '+' | '.join(rewrite)+'\n')
            if dr == 0:
                out.append(f'  with axis (proj₂ (deltas {d})) c\n')
                out.append('... | nothing = refl\n')
                out.append('... | just c′ = refl\n')
            elif dc == 0:
                out.append(f'  with axis (proj₁ (deltas {d})) r\n')
                out.append('... | nothing = refl\n')
                out.append('... | just r′ = refl\n')
            else:
                out.append(f'  with axis (proj₁ (deltas {d})) r | axis (proj₂ (deltas {d})) c\n')
                out.append('... | nothing | nothing = refl\n')
                out.append('... | nothing | just c′ = refl\n')
                out.append('... | just r′ | nothing = refl\n')
                out.append('... | just r′ | just c′ = refl\n')
    return ''.join(out)


if __name__ == '__main__':
    path = Path(__file__).resolve().parents[1] / 'src/Othello/SymmetryGeometry6.agda'
    path.write_text(generate())
