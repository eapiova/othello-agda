# othello-agda

Safe Agda formalization of standard 4×4 Othello for
[TPP-mark 2026](https://auto-res.github.io/tpp2026/en/tpp2026mark/).

The proved result is the exact **raw disc difference +8 for White**: White has a
strategy guaranteeing at least +8 against every Black strategy, and Black has
a strategy holding the result to at most +8 against every White strategy.
Strategies may depend on the full move history and current position.
Every guarantee includes an actual completed legal play; termination is not
assumed by a vacuous implication about possible outcomes.

## Current status

`Othello.Proof4.problem1` proves that White wins; `value4` proves the exact
value +8 with constructive strategies. Both concrete certificate checks use
`refl`. `Othello.Value.value-realized` constructs a completed play of the two
strategies with that exact score, and `value-unique` proves uniqueness.

The untrusted Python solvers independently return +8. Both generated strategy
certificates pass an independent scalar checker, and the bitboard and scalar
rules agree on all 451 positions visited by the certificates. The lower and
upper trees have 399 and 337 nodes. The final machine checks and proof scope
are recorded in [the verification ledger](docs/verification.md).

## Check and reproduce

Install Agda 2.9.0 and put `agda` on `PATH`. The core is self-contained on
`Agda.Builtin.*` and a small checked prelude; no globally registered libraries
or network access are needed to check its source.

```sh
python3 -m unittest discover -s tools -p 'test_*.py' -v
python3 tools/ref.py
python3 tools/generate.py
scripts/check.sh src/Everything.agda
scripts/measure-agda-rss.sh cold src/Everything.agda results 3G --cold
mkdir -p dist
typst compile docs/writeup.typ dist/writeup.pdf
```

Every core module uses `--safe --without-K --cubical-compatible`. No project
postulates, unsolved holes, termination escapes, or foreign solver assumptions
are permitted. The development uses ordinary Agda equality. Indexed-match
warnings describe limits on computation under Cubical transports; that
additional behavior is not part of the theorem.

Two installed binaries both report 2.9.0 but differ in build and behavior:
standard-library 2.3's irrelevant-field recomputation module failed on the
laptop and passed on the desktop. We therefore use the builtin-only foundation
and record binary hashes rather than treating version strings as sufficient
toolchain identities. No unsafe irrelevance flag is enabled.

## Rules and scoring

The center begins W B / B W, Black moves first, and a placement must bracket
one or more opponent discs in at least one of eight directions. All bracketed
directions flip using the original board. Passing is compulsory when only the
opponent has a legal placement. The game ends when neither player can place,
including endings with unoccupied squares.

Score means **White discs minus Black discs**. Unoccupied squares are not
awarded to either player. A reported perfect-play line ends Black 3–White 11
with two empty squares, giving +8. Awarding those empties to White would make
that particular line score +10; it does not establish a minimax value under
that different scoring convention. See
[Takeshita and Ikeda (2015), pp. 224–225](https://miyazaki-u.repo.nii.ac.jp/record/4739/files/engineering44_221-227.pdf).

Problem 2 retains both the +4 value and the separate 20–16 outcome under an
optimal strategy pair. Problems 2 and 3 are **statement only**, with no
inhabitants asserted.

## Trust boundary

The Python bitboard solver, separate scalar oracle, certificate generator,
JSON, and generated certificate data are untrusted. The Agda checker derives
each successor board from its own rules, covers every legal opponent response,
and validates forcing choices, passes, terminality, and terminal scores.
Its generic soundness theorem converts accepted certificates into constructive
strategies and completed plays. Acceptance of the concrete certificates must
be established inside Agda; native execution alone is insufficient.

`Othello.Correctness` proves scan/capture correctness against inductive
brackets, legality and enumeration completeness, and placement count changes.
The separate termination proof uses twice the empty-square count plus an
immobility bit, so legal placements and compulsory passes both decrease it.
The rule fixtures, legal 3–11 sequence and malformed-certificate tests are
checked in Agda. The Python suite additionally compares independently written
rule implementations on random games and every certificate position.

## Desktop checks

The compute desktop is reached through the configured Tailscale alias
`ssh desktop`. Source is authoritative on the laptop. Freeze a source snapshot,
transfer it, and run a single heavy check in `tmux` under a user systemd scope:

```sh
python3 tools/snapshot.py dist/source.tar.gz
# Transfer and unpack into a dedicated desktop run directory.
systemd-run --user --scope --quiet \
  --property=MemoryMax=16G --property=MemorySwapMax=0 \
  scripts/measure-agda-rss.sh desktop src/Everything.agda results 12G --cold
```

The systemd limit controls the whole scope; `-M` separately limits the Haskell
heap. The measurement tool serializes project checks, monitors RSS and timeout,
cleans up interrupted jobs, and records source identities, binary identity,
flags, cache mode, exit status, runtime, and memory. A changed source snapshot
or failed check cannot be marked accepted.

## Submission

Provide a tagged source archive, certificate data, highlighted source HTML,
the verification ledger and machine-readable checking results, and a short
write-up. Submit by November 15, 2026 to the addresses listed on the challenge
page. Sending the email is a separate action.

With the release tag on a clean checkout and matching cold checks from both
machines in `results/`, run `python3 tools/package.py`. The package includes
the three-page write-up, verification records and logs, and HTML. The
packager refuses unmatched checks, an untagged commit or missing artifacts.

[AI assistance is disclosed here](docs/ai-use.md). Commit messages are plain.
The project is MIT licensed.
