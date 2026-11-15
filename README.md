# othello-agda

Safe Agda results for standard Othello, submitted to
[TPP-mark 2026](https://auto-res.github.io/tpp2026/en/tpp2026mark/).

Riccardo Borsetto · 15 November 2026

- **Problem 1 (4×4): proved.** White wins; stronger exact raw White-minus-Black value **+8**
  (`Othello.Proof4.problem1`, `Othello.Proof4.value4`).
- **Problem 2 (6×6): proved.** Raw value **+4** and a completed legal play of the **same
  optimal forcing-strategy pair**, ending Black 16 / White 20
  (`Tests.CompleteUpperRows6.Result.initial6x6 : Problem2`). Final safe Agda acceptance:
  19 October 2026.
- **Problem 3 (8×8): not proved.** Only conditional partial work exists; no closed
  inhabitant of `Problem3 = HasValue eight 0` is claimed.

Start with the [report](docs/tpp2026/writeup.pdf) (LaTeX source alongside) and its
[formal-source companion](docs/tpp2026/formal-source.html). AI assistance is disclosed
in the report.

## Layout

| Path | Contents |
|---|---|
| `src/` | Rules, generic certificate soundness, the 4×4 proof, statements and the 6×6 development modules |
| `six-complete/` | All 4,128 selected non-builtin modules of the accepted 6×6 proof, plus the typed final wrapper, with source inventory, dependency graph and acceptance records |
| `certificates/` | Untrusted generated certificate data |
| `docs/verification.md`, `docs/checks/` | 4×4 checking records |
| `docs/tpp2026/` | Submission report and formal-source companion |
| `tools/` | Untrusted reference solver, certificate generator and tests |

## Checking

Install Agda 2.9.0. Every core module uses `--safe --without-K --cubical-compatible`;
no project postulates, holes or termination escapes are permitted, and no external
library is required.

4×4 (seconds):

```sh
scripts/check.sh src/Everything.agda
```

6×6 source identities and exact dependency closure (no prover is run):

```sh
cd six-complete && python3 -I -B verify-sources.py
```

A fresh 6×6 check of the flattened layout, **not cold-rebuild tested or resource-validated**:

```sh
cd six-complete
agda --no-libraries --safe --without-K --cubical-compatible -i src src/Tests/FinalProblem2Check6.agda
```

A cold run recomputes large Boolean row proofs; use a disposable checkout and a fresh cache.

## Trust boundary

Native search, Python tools, generated certificates and maps, and AI output are
untrusted. The accepted results rest on safe Agda checking against the rule model in
`src/Othello/Rules.agda` and the statements in `src/Othello/Statements.agda`.
Unoccupied squares are not awarded to either player.

Archives, retained row interfaces and checking evidence are in the
[submission Release](https://github.com/eapiova/othello-agda/releases/tag/tpp2026-submission-20261115).
Retained interfaces are evidence, not a portable cache.

## License

MIT; see [LICENSE](LICENSE).
