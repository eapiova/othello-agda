# Verification ledger

## Claims

| Claim | Status | Agda evidence |
| --- | --- | --- |
| Problem 1: White wins 4×4 | Proved | `Othello.Proof4.problem1` |
| White guarantees raw difference ≥8 against every Black strategy | Proved | `Othello.Proof4.lower4` |
| Black guarantees raw difference ≤8 against every White strategy | Proved | `Othello.Proof4.upper4` |
| The two strategies realize exact score +8 | Proved | `Othello.Value.value-realized`, `value-score` applied to `value4` |
| Optimal value is unique | Proved | `Othello.Value.value-unique` |
| Generic accepted certificates construct completed plays | Proved | `Game.Soundness.checkSound` |
| Boolean scan/captures and legal-move enumeration agree with inductive brackets | Proved | `Othello.Correctness` |
| A legal placement consumes one empty square and adds one occupied square | Proved | `placement-decreases-empties`, `placement-increases-occupied` |
| Every legal successor decreases the pass-sensitive measure | Proved | `Othello.Termination.successor-decreases` |
| The successor relation is well founded | Proved | `successors-well-founded` |
| Every pair of history-dependent strategies completes a play | Proved | `all-strategies-complete` |
| Legal no-pass line ending Black 3–White 11 with two empties | Checked fixture | `Tests.PerfectLine` |
| 8×8 perft depths 0–5: 1,4,12,56,244,1396 | Checked fixture | `Tests.Perft`, `Tests.DeepPerft` |
| 4×4 perft depths 1–5: 4,12,44,128,424 | Checked fixture | `Tests.Perft`, `Tests.DeepPerft` |
| Missing/extra opponent branches, invalid choices, premature leaves, voluntary passes and wrong score bounds rejected | Checked fixtures | `Tests.Certificates` |
| Problem 2: 6×6 value +4 and optimal 16–20 terminal counts | Statement only | `Othello.Statements.Problem2` |
| Problem 3: 8×8 draw | Statement only | `Othello.Statements.Problem3` |

22 project Agda modules, all with `--safe --without-K --cubical-compatible`.
Source audit found zero project postulates, holes, termination escapes,
positivity escapes or unsafe irrelevance flags. Safe checking is the primary
evidence; text searches are an additional audit.

## Full cold checks, 5 October 2026

Both runs checked `src/Everything.agda`, including all proofs and depth-5
perft. Both exited 0, met the resource limits, and verified unchanged source.
The desktop run began with zero interfaces. The laptop run had interfaces
but explicitly ignored them. “Cold” describes Agda interface use, not OS caches.

| Machine | Agda heap cap | Wall time | Peak RSS | HTML | Record |
| --- | --- | --- | --- | --- | --- |
| eapiova-laptop, Ryzen 7 5700U | 3 GiB | 15.877 s | 0.149 GiB | No | [JSON](checks/laptop-everything.json) |
| eapiova, Ryzen 7 9800X3D | 12 GiB | 6.809 s | 0.163 GiB | Yes | [JSON](checks/desktop-everything.json) |

Flags: `--no-libraries --safe --without-K --cubical-compatible -i src
--ignore-interfaces`. The desktop also used `--html --html-dir=dist/html`.
Full commands, timestamps, cache counts and memory information are in the
records. RSS is Linux high-water resident memory; measurements include Agda
checking and, when requested, HTML generation. These are observed runs, not
an expected performance bound.

Both checks bind this exact Agda-source identity (all `.agda` and `.agda-lib`
files, names included):

`b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`

The complete source snapshot at checking time was:

`569d17c969e2ad6d81a383346cde8c9679b5a96ea6400794bbf2e2d48e1af188`

These runs occurred while the implementation was uncommitted on top of
`4f127f0bd57ce57690df2f96ff851504fac6e12d`. Their records say `dirty: true`;
this is not concealed as a tagged run. Documentation and these records were
added after checking; the Agda-source identity remains the same. A fresh
clone of the release tag is additionally checked on the desktop; that
clean-revision record and log are included in the submission archive.

## Toolchains and resources

Both binaries report Agda 2.9.0. Local build: commit b9097ba, binary SHA-256
`9ee82043d547e3c2e83bcf36ade67d3ab674347391996ca013583cf383449cba`.
Desktop binary SHA-256:
`c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`.
The latter is a Nix build with debug, optimise-heavily and cluster-counting
flags. Installed commit labels are contextual information; executable hashes
and commands identify the actual checking binaries.

The laptop has about 7 GiB RAM. The desktop has about 30 GiB RAM and around
18 GiB available at checking time. Its job ran in a user systemd scope with
`MemoryMax=16G` and `MemorySwapMax=0`. The laptop job used a 4 GiB cgroup cap,
1 GiB cgroup swap cap, a 3 GiB Agda heap cap and a 3.5 GiB RSS stop threshold.
The measurement timeout was 300 seconds. Agda jobs sharing build state were
serialized. No interfaces or dependencies were transferred to the desktop.

The core requires no stdlib. Standard-library 2.3's irrelevant recomputation
dependency passed on the desktop and failed on the laptop. The project uses
checked builtin-only finite vectors and arithmetic instead of enabling an
unsafe flag. Indexed-match warnings remain about computation under Cubical
transports; ordinary safe Agda checking succeeds. No such Cubical computation
property is asserted.

## Untrusted checks and generation

The Python suite passed all 13 tests in 1.620 seconds on the laptop. It
compares scalar and bitboard rules on 12 random complete games per size
(4,6,8), verifies both bounds, and compares every certificate-visited position.
Both independent exact searches return +8. The reference line is Black 3,
White 11, two empty squares, no passes.

The committed certificates contain 399 lower-tree nodes and 337 upper-tree
nodes, covering 451 distinct positions. The exact bitboard search cached
62,789 states. See `certificates/generation.json` for generator measurements
and `certificates/reference-results.json` for executable checks. These are
untrusted observations, not the proof. JSON certificate SHA-256:
`cc3ef3dfe89a53576c2cf49e61ff6060ca186f70eafb787b08fa7feddb18af8b`.

## Implementation changes supported by evidence

The certificate-first design fits easily on both machines, so neither a
positional hint oracle nor opening-move splitting was needed. A direct
ten-ply reflected endpoint expression in the perfect-line fixture exhausted
a 2 GiB laptop heap and timed out after 180 seconds on the desktop at
12.428 GiB RSS. The final fixture records literal intermediate boards,
checks each transition with `refl`, and connects them with an inductive legal
sequence. It avoids repeated expansion while still checking every move and
the terminal score. The final full checks above include this replacement.

The 2015 paper's 218 count refers to examined terminal positions, not all
search nodes. Scoring is raw White minus Black. Awarding terminal empties
would change the reported 3–11 line to +10; no alternate-scoring minimax
claim is made. See the references in the write-up.
