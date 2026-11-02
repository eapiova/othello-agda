"""AI-assisted fixed-width certificate data parser; inputs remain untrusted."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def generate():
    old=(ROOT/'src/Othello/DirectedCompact6.agda').read_text()
    head=old[:old.index('private\n  rankNat')].replace('Othello.DirectedCompact6','Othello.UnicodeCompact6')
    head+='''private
  readCode : ℕ → List Char → Maybe (ℕ × List Char)
  readCode bound [] = nothing
  readCode bound (c ∷ cs) with primCharToNat c < 256
  ... | true = nothing
  ... | false with (primCharToNat c - 256) ≤ᵇ bound
  ...   | false = nothing
  ...   | true = just ((primCharToNat c - 256) , cs)

  readWord : ℕ → List Char → Maybe (ℕ × List Char)
  readWord bound [] = nothing
  readWord bound (c ∷ cs) with primCharToNat c < 16384
  ... | true = nothing
  ... | false with (primCharToNat c - 16384) < bound
  ...   | false = nothing
  ...   | true = just ((primCharToNat c - 16384) , cs)

  readKey : List Char → Maybe (ℕ × List Char)
  readKey cs with readWord 19532 cs
  ... | nothing = nothing
  ... | just (hi , tail) with readWord 1024 tail
  ...   | nothing = nothing
  ...   | just (lo , rest) with (1024 * hi + lo) < 20000000
  ...     | false = nothing
  ...     | true = just ((1024 * hi + lo) , rest)

  length : ∀ {A : Set} → List A → ℕ
  length [] = zero
  length (_ ∷ xs) = suc (length xs)

'''
    head+=old[old.index('coordinate :'):old.index('\nprivate\n  classify')]
    head+='''
private
  classify : Char → ℕ
  classify c with primCharToNat c < 65
  ... | true = 8
  ... | false = primCharToNat c - 65

'''
    tail=old[old.index('mutual\n'):]
    tail=tail.replace('idTail 0 false cs','readKey cs').replace('idTail 0 false tail','readKey tail')
    tail=tail.replace('numberTail 0 false cs','readCode 128 cs')
    (ROOT/'src/Othello/UnicodeCompact6.agda').write_text(head+tail)


if __name__=='__main__':generate()
