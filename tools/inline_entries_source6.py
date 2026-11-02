"""AI-assisted deforestation of repeated board destructuring in move entries."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def generate():
    old=(ROOT/'src/Othello/LengthRules6.agda').read_text()
    captures=dict(re.findall(r'captures(q\d\d) [^\n]+ p =\n  ([^\n]+)\n',old))
    assert len(captures)==36
    row_patterns=['('+' F.∷ '.join([f'c{r}{c}' for c in range(6)]+['F.[]'])+')' for r in range(6)]
    pattern='('+' F.∷ '.join(row_patterns+['F.[]'])+')'
    source='''{-# OPTIONS --safe --without-K --cubical-compatible #-}
-- AI-assisted. Inline ray expressions into the already destructured entries.
module Othello.InlineEntries6 where

open import Prelude
open import Othello.Board
open import Othello.Rules using (coords; passState)
open import Game.Core using (lookup)
import Game.Core as G
import Game.Transfer as T
import Game.DirectedIndexed as D
import Othello.Finite as F
import Othello.LengthRays6 as Lines
import Othello.LengthRules6 as Old
import Othello.LengthMoves6 as Moves
import Othello.Fast6 as Fast
open Old using ('''+ '; '.join(f'q{r}{c}' for r in range(6) for c in range(6))+''')

entries : State six → List Old.Entry
'''
    source+=f'entries (state {pattern} p) =\n  '+' ∷ '.join([f'(Old.entry q{r}{c} c{r}{c} ({captures[f"q{r}{c}"]}))' for r in range(6) for c in range(6)]+['[]'])+'\n\n'
    source+='''abstract
  entries-agree : ∀ s → entries s ≡ Old.entries s
'''
    source+=f'  entries-agree (state {pattern} p) = refl\n\n'
    source+='''moves : State six → List (State six)
moves s = Old.movesEntries s (entries s)

abstract
  moves-agree : ∀ s → moves s ≡ Old.moves s
  moves-agree s = cong (Old.movesEntries s) (entries-agree s)

successors : State six → List (State six)
successors s = Fast.finish6 s (moves s) (moves (passState s))

forcedPass : State six → Bool
forcedPass s = Old.passShape (moves s) (moves (passState s))

abstract
  successors-agree : ∀ s → successors s ≡ Old.successors s
  successors-agree s rewrite moves-agree s | moves-agree (passState s) = refl

  pass-agree : ∀ s → forcedPass s ≡ Old.forcedPass s
  pass-agree s rewrite moves-agree s | moves-agree (passState s) = refl

specializedGame6 : G.Game (State six)
specializedGame6 = record { turn = toMove ; next = successors ; forcedPass = forcedPass }

agreement : T.Agreement specializedGame6 Fast.fastGame6
agreement = T.agreement (λ s → trans (successors-agree s) (Old.successors-agree s))
  (λ s → refl) (λ s → trans (pass-agree s) (Old.forcedPass-agree s))

private
  pick-sound : ∀ s q t → Moves.pick s q ≡ just t →
    Σ ℕ (λ i → lookup (successors s) i ≡ just t)
  pick-sound s q t checked with Moves.pick-sound s q t checked
  ... | i , hit = i , trans (cong (λ ss → lookup ss i) (successors-agree s)) hit

picker : D.MovePicker specializedGame6 (Coord six)
picker = D.movePicker Moves.pick pick-sound
'''
    (ROOT/'src/Othello/InlineEntries6.agda').write_text(source)
    rows=(ROOT/'src/Othello/LengthRows6.agda').read_text().replace('Othello.LengthRows6','Othello.InlineRows6').replace('import Othello.LengthRules6 as New','import Othello.InlineEntries6 as New').replace('Moves.picker Packed.decode','New.picker Packed.decode')
    (ROOT/'src/Othello/InlineRows6.agda').write_text(rows)


if __name__=='__main__':generate()
