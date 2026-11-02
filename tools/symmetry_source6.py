"""AI-assisted direct D4 permutations; Agda checks each against the old action."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def generate():
    def board(f):
        rows=['('+' F.∷ '.join([f(r,c) for c in range(6)]+['F.[]'])+')' for r in range(6)]
        return '('+' F.∷ '.join(rows+['F.[]'])+')'
    pattern=board(lambda r,c:f'c{r}{c}')
    # For output coordinate q, read the input at inverse(sigma)(q).
    permutations=[('identity',lambda r,c:(r,c)),('rotate90',lambda r,c:(5-c,r)),
      ('rotate180',lambda r,c:(5-r,5-c)),('rotate270',lambda r,c:(c,5-r)),
      ('reflectVertical',lambda r,c:(r,5-c)),('reflectDiagonal',lambda r,c:(c,r)),
      ('reflectHorizontal',lambda r,c:(5-r,c)),('reflectAntiDiagonal',lambda r,c:(5-c,5-r))]
    source='''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted generated permutations; each equality checks the old D4 action.
module Othello.DirectSymmetry6 where

open import Prelude
open import Othello.Board
open import Game.Symmetry using (CertificateTransport; Proven)
open import Othello.Statements using (lowerGoal; upperGoal)
import Othello.Finite as F
import Othello.Symmetry6 as S
import Othello.SharedSymmetry6 as Old
import Othello.Fast6 as Fast

transformBoard : S.D4 → Board six → Board six
'''
    for name,f in permutations:
        source+=f'transformBoard S.{name} {pattern} =\n  '+board(lambda r,c:'c'+''.join(str(k) for k in f(r,c)))+'\n'
    source+='\ntransformBoard-correct : ∀ sigma b → transformBoard sigma b ≡ S.transformBoard sigma b\n'
    for name,_ in permutations:source+=f'transformBoard-correct S.{name} {pattern} = refl\n'
    source+='''
transformState : S.D4 → State six → State six
transformState sigma (state b p) = state (transformBoard sigma b) p

transformState-correct : ∀ sigma s → transformState sigma s ≡ S.transformState sigma s
transformState-correct sigma (state b p) = cong (λ c → state c p) (transformBoard-correct sigma b)

transformTag : ℕ → State six → State six
transformTag tag = transformState (S.fromTag tag)

transformTag-correct : ∀ tag s → transformTag tag s ≡ S.transformTag tag s
transformTag-correct tag s = transformState-correct (S.fromTag tag) s

abstract
  transport-lower : ∀ tag s → Proven Fast.fastGame6 white (lowerGoal 4) (transformTag tag s) →
    Proven Fast.fastGame6 white (lowerGoal 4) s
  transport-lower tag s proof = Old.transport-lower6 tag s
    (subst (Proven Fast.fastGame6 white (lowerGoal 4)) (transformTag-correct tag s) proof)

  transport-upper : ∀ tag s → Proven Fast.fastGame6 black (upperGoal 4) (transformTag tag s) →
    Proven Fast.fastGame6 black (upperGoal 4) s
  transport-upper tag s proof = Old.transport-upper6 tag s
    (subst (Proven Fast.fastGame6 black (upperGoal 4)) (transformTag-correct tag s) proof)

lowerTransport6 : CertificateTransport Fast.fastGame6 white (lowerGoal 4)
lowerTransport6 = record { act = transformTag ; acceptedTag = S.acceptedTag8 ; transport = transport-lower }

upperTransport6 : CertificateTransport Fast.fastGame6 black (upperGoal 4)
upperTransport6 = record { act = transformTag ; acceptedTag = S.acceptedTag8 ; transport = transport-upper }
'''
    (ROOT/'src/Othello/DirectSymmetry6.agda').write_text(source)


if __name__=='__main__':
    generate()
