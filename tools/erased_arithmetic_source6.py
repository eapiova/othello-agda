"""AI-assisted proof-field erasure; no unsafe irrelevance options are used."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def generate():
    source=(ROOT/'src/Othello/ArithmeticState6.agda').read_text()
    source=source.replace('Othello.ArithmeticState6','Othello.ErasedArithmeticState6')
    source=source.replace('import Game.BooleanUIP as UIP','import Game.BooleanRecompute as Recover')
    source=source.replace('    canonical : P.encode (P.decode raw) ≡ raw','    .storedCanonical : P.encode (P.decode raw) ≡ raw')
    source=source.replace('  module Paths = UIP.Checking P.equal P.equal-sound equal-refl','''  module Recovery = Recover.Checking P.equal P.equal-sound equal-refl

canonical : ∀ s → P.encode (P.decode (raw s)) ≡ raw s
canonical (coded r witness) = Recovery.recompute witness

private''')
    source=source.replace('coded-ext (coded r a) (coded .r b) refl = cong (coded r) (Paths.unique a b)','coded-ext (coded r a) (coded .r b) refl = refl')
    (ROOT/'src/Othello/ErasedArithmeticState6.agda').write_text(source)
    source=(ROOT/'src/Othello/ArithmeticGame6.agda').read_text().replace('Othello.ArithmeticGame6','Othello.ErasedArithmeticGame6').replace('Othello.ArithmeticState6','Othello.ErasedArithmeticState6')
    (ROOT/'src/Othello/ErasedArithmeticGame6.agda').write_text(source)
    source=(ROOT/'src/Othello/ArithmeticRows6.agda').read_text().replace('Othello.ArithmeticRows6','Othello.ErasedArithmeticRows6').replace('Othello.ArithmeticGame6','Othello.ErasedArithmeticGame6').replace('Othello.ArithmeticState6','Othello.ErasedArithmeticState6')
    (ROOT/'src/Othello/ErasedArithmeticRows6.agda').write_text(source)


if __name__=='__main__':generate()
