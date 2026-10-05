# othello-agda

Safe Agda formalization of standard 4×4 Othello for
[TPP-mark 2026](https://auto-res.github.io/tpp2026/en/tpp2026mark/).

The proved result is the exact **raw disc difference +8 for White**: White has a
strategy guaranteeing at least +8 against every Black strategy, and Black has
a strategy holding the result to at most +8 against every White strategy.
Strategies may depend on the full move history and current position.
Every guarantee includes an actual completed legal play; termination is not
assumed by a vacuous implication about possible outcomes.

## Status

`Othello.Proof4.problem1` proves that White wins; `value4` proves the exact
value +8 with constructive strategies. Both concrete certificate checks use
`refl`. `Othello.Value.value-realized` constructs a completed play of the two
strategies with that exact score, and `value-unique` proves uniqueness.

The untrusted Python solvers independently return +8. Both generated strategy
certificates pass an independent scalar checker, and the bitboard and scalar
rules agree on all 451 positions visited by the certificates. The lower and
upper trees have 399 and 337 nodes. Machine checks are recorded in
[the verification ledger](docs/verification.md).

Problems 2 and 3 are **statement only** in this release, with no inhabitants
asserted.

## Check

Install Agda 2.9.0 and put `agda` on `PATH`. The core is self-contained on
`Agda.Builtin.*` and a small checked prelude; no globally registered libraries
or network access are needed.

```sh
python3 -m unittest discover -s tools -p 'test_*.py' -v
python3 tools/ref.py
python3 tools/generate.py
scripts/check.sh src/Everything.agda
```

Every core module uses `--safe --without-K --cubical-compatible`. No project
postulates, unsolved holes, termination escapes, or foreign solver assumptions
are permitted.

## Rules and scoring

The center begins W B / B W, Black moves first, and a placement must bracket
one or more opponent discs in at least one of eight directions. All bracketed
directions flip using the original board. Passing is compulsory when only the
opponent has a legal placement. The game ends when neither player can place,
including endings with unoccupied squares.

Score means **White discs minus Black discs**. Unoccupied squares are not
awarded to either player. A reported perfect-play line ends Black 3–White 11
with two empty squares, giving +8. See
[Takeshita and Ikeda (2015), pp. 224–225](https://miyazaki-u.repo.nii.ac.jp/record/4739/files/engineering44_221-227.pdf).

## Trust boundary

The Python bitboard solver, separate scalar oracle, certificate generator,
JSON, and generated certificate data are untrusted. The Agda checker derives
each successor board from its own rules, covers every legal opponent response,
and validates forcing choices, passes, terminality, and terminal scores.
Its generic soundness theorem converts accepted certificates into constructive
strategies and completed plays.

`Othello.Correctness` proves scan/capture correctness against inductive
brackets, legality and enumeration completeness, and placement count changes.
The separate termination proof uses twice the empty-square count plus an
immobility bit, so legal placements and compulsory passes both decrease it.

## License

MIT; see [LICENSE](LICENSE).
