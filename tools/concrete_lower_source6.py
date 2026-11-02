"""AI-assisted textual specialization; retain the complete safe soundness proof."""
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def generate():
    generic = (ROOT/'src/Game/EncodedResolver.agda').read_text()
    prefix = generic[:generic.index('module Checking {Key')]
    prefix = prefix.replace('module Game.EncodedResolver where', 'module Othello.ConcreteLowerChecker6 where')
    constants = '''
-- Fixed safe instance: there are no game/law/module parameters on recursion.
open import Othello.Board using (State; Coord; six)
open import Othello.Encode6 using (stateEquality6)
open import Othello.Statements using (lowerGoal)
open import Othello.DirectSymmetry6 using (lowerTransport6)
import Othello.InlineEntries6 as New
import Othello.RowPacked6 as Packed
import Othello.AgreedIndexed6 as A
import Game.NatOrder as N

Key : Set
Key = ℕ
S : Set
S = State six
Stored : Set
Stored = Packed.PackedState
Move : Set
Move = Coord six
order : I.Order Key
order = N.order
eq : StateEquality S
eq = stateEquality6
g : Game S
g = New.specializedGame6
p : Player
p = white
goal : S → Bool
goal = lowerGoal 4
module Agreed = A.With New.specializedGame6 New.agreement
laws : CertificateTransport g p goal
laws = Agreed.adapt white (lowerGoal 4) lowerTransport6
picker : MovePicker g Move
picker = New.picker
decode : Stored → S
decode = Packed.decode
matches : S → Stored → Bool
matches = Packed.matches
matches-sound : ∀ s t → matches s t ≡ true → s ≡ decode t
matches-sound = Packed.matches-sound

'''
    body = textwrap.dedent(generic[generic.index('  module Old = D.Checker'):generic.index('  mutual\n    checkLocal-sound')])
    body = body.replace('module Old = D.Checker order eq g p goal laws picker', '''import Game.EncodedResolver as General
module Generic = General.Checking order eq g p goal laws picker decode matches matches-sound
module Old = Generic.Old''')
    equivalence = '''
private
  cong₂ : ∀ {X Y Z : Set} (f : X → Y → Z) {x x′ y y′} →
    x ≡ x′ → y ≡ y′ → f x y ≡ f x′ y′
  cong₂ f refl refl = refl

abstract
  mutual
    checkLocal-agree : ∀ L owner s c → checkLocal L owner s c ≡ Generic.checkLocal L owner s c
    checkLocal-agree L owner s indexedLeaf with next g s
    ... | [] = refl
    ... | x ∷ xs = refl
    checkLocal-agree L owner s (indexedSolve fuel) = refl
    checkLocal-agree L owner s (indexedChoice i c)
      with next g s | samePlayer (turn g s) p
    ... | [] | own = refl
    ... | x ∷ xs | false = refl
    ... | x ∷ xs | true with lookup (x ∷ xs) i
    ...   | nothing = refl
    ...   | just t = checkLocal-agree L owner t c
    checkLocal-agree L owner s (indexedFork cs)
      with next g s | samePlayer (turn g s) p
    ... | [] | own = refl
    ... | x ∷ xs | true = refl
    ... | x ∷ xs | false = checkLocalForest-agree L owner (x ∷ xs) cs
    checkLocal-agree L owner s (indexedPass c) with next g s | forcedPass g s
    ... | [] | b = refl
    ... | x ∷ [] | false = refl
    ... | x ∷ y ∷ xs | b = refl
    ... | x ∷ [] | true = checkLocal-agree L owner x c
    checkLocal-agree L owner s (cite j) with I.beforeB order j owner
    ... | false = refl
    ... | true with L j
    ...   | nothing = refl
    ...   | just u = refl
    checkLocal-agree L owner s (citeBy tag j) with I.beforeB order j owner
    ... | false = refl
    ... | true with acceptedTag laws tag
    ...   | false = refl
    ...   | true with L j
    ...     | nothing = refl
    ...     | just u = refl
    checkLocal-agree L owner s (indexedPick a c)
      with samePlayer (turn g s) p | pick picker s a
    ... | false | mt = refl
    ... | true | nothing = refl
    ... | true | just t = checkLocal-agree L owner t c

    checkLocalForest-agree : ∀ L owner ss cs →
      checkLocalForest L owner ss cs ≡ Generic.checkLocalForest L owner ss cs
    checkLocalForest-agree L owner [] [] = refl
    checkLocalForest-agree L owner [] (c ∷ cs) = refl
    checkLocalForest-agree L owner (s ∷ ss) [] = refl
    checkLocalForest-agree L owner (s ∷ ss) (c ∷ cs) =
      cong₂ _∧_ (checkLocal-agree L owner s c) (checkLocalForest-agree L owner ss cs)

Compatible : Resolver → (Key → Stored) → Set
Compatible = Generic.Compatible

abstract
  tree-sound : ∀ L G owner s c → Compatible L G → checkLocal L owner s c ≡ true →
    Old.TreeOK (λ j → decode (G j)) owner s c
  tree-sound L G owner s c compatible checked =
    Generic.tree-sound L G owner s c compatible
      (trans (sym (checkLocal-agree L owner s c)) checked)
'''
    (ROOT/'src/Othello/ConcreteLowerChecker6.agda').write_text(prefix+constants+body+equivalence)
    rows = (ROOT/'src/Othello/InlineRows6.agda').read_text()
    rows_prefix = rows[:rows.index('module Checking (p')]
    rows_prefix = rows_prefix.replace('module Othello.InlineRows6 where', 'module Othello.ConcreteLowerRows6 where')
    rows_prefix += '\nimport Othello.ConcreteLowerChecker6 as Concrete\nmodule V = Concrete\n\n'
    body = textwrap.dedent(rows[rows.index('  checkRows :'):])
    (ROOT/'src/Othello/ConcreteLowerRows6.agda').write_text(rows_prefix+body)


if __name__ == '__main__':
    generate()
