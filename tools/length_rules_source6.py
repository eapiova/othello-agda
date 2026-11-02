"""AI-assisted fixed-ray capture counts; every equation needs safe checking."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def generate():
    old=(ROOT/'src/Othello/Specialized6.agda').read_text()
    head=old.split('capturesq00 :',1)[0]
    head=head.replace('module Othello.Specialized6 where','module Othello.LengthRules6 where')
    head+='''import Othello.Specialized6 as Old
import Othello.LengthRays6 as Lines

private
  append-cong : ∀ {A : Set} {xs ys zs ws : List A} →
    xs ≡ ys → zs ≡ ws → xs ++ zs ≡ ys ++ ws
  append-cong refl refl = refl

'''
    rows=['('+' F.∷ '.join([f'c{r}{c}' for c in range(6)]+['F.[]'])+')' for r in range(6)]
    pattern='('+' F.∷ '.join(rows+['F.[]'])+')'
    def listing(xs):return ' ∷ '.join([*xs,'[]'])
    for r in range(6):
        for c in range(6):
            name=f'q{r}{c}';expressions=[];proofs=[]
            for dr,dc in [(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)]:
                qs=[];cs=[];rr=r+dr;cc=c+dc
                while 0<=rr<6 and 0<=cc<6:
                    qs.append(f'q{rr}{cc}');cs.append(f'c{rr}{cc}');rr+=dr;cc+=dc
                n=len(qs)
                count=' '.join([f'Lines.count{n}','p',*cs])
                expressions.append(f'(Lines.prefix ({count}) ({listing(qs)}))')
                proofs.append('('+' '.join([f'Lines.correct{n}','p',*qs,*cs])+')')
            expression=' ++ '.join([*expressions,'[]'])
            proof='refl'
            for item in reversed(proofs):proof=f'append-cong {item} ({proof})'
            head+=f'captures{name} : Board six → Player → List (Coord six)\n'
            head+=f'captures{name} {pattern} p =\n  {expression}\n\n'
            head+=f'captures{name}-correct : ∀ b p → captures{name} b p ≡ Fast.allCaptures6 (state b p) {name}\n'
            head+=f'captures{name}-correct b@{pattern} p = trans\n  ({proof})\n  (Old.captures{name}-correct b p)\n\n'
    head+=old[old.index('candidateCell :'):]
    (ROOT/'src/Othello/LengthRules6.agda').write_text(head)
    moves=(ROOT/'src/Othello/DirectMoves6.agda').read_text().replace('Othello.DirectMoves6','Othello.LengthMoves6').replace('import Othello.Specialized6 as New','import Othello.LengthRules6 as New')
    (ROOT/'src/Othello/LengthMoves6.agda').write_text(moves)
    rows=(ROOT/'src/Othello/RowPackedIndexed6.agda').read_text().replace('Othello.RowPackedIndexed6','Othello.LengthRows6').replace('import Othello.Specialized6 as New','import Othello.LengthRules6 as New').replace('import Othello.DirectMoves6 as Moves','import Othello.LengthMoves6 as Moves')
    (ROOT/'src/Othello/LengthRows6.agda').write_text(rows)


if __name__=='__main__':generate()
