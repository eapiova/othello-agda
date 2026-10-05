#set page(paper: "a4", margin: 22mm)
#set text(size: 10.5pt)
#set par(justify: true)
#set heading(numbering: "1.")
#set page(footer: context [#h(1fr)#counter(page).display()])

#align(center)[
  #text(size: 18pt, weight: "bold")[Certified strategies for 4×4 Othello in Agda]
  #v(4mm)
  TPP-mark 2026, Problem 1 · eapiova · October 2026
]

= Result and statement

The submission proves that White wins standard 4×4 Othello. It proves the
stronger result that the raw terminal disc difference, White minus Black,
has optimal value +8. A White strategy guarantees a difference of at least
8 against every Black strategy; a Black strategy guarantees a difference
of at most 8 against every White strategy. The Agda inhabitants are
`Othello.Proof4.problem1` and `Othello.Proof4.value4`.

Strategies receive the full chronological history and the current board.
A strategy returns a natural successor index. An out-of-range recommendation
selects the first legal successor, so every function denotes a legal strategy
at a nonterminal position. Every legal strategy is expressible by choosing its
actual successor index. A guarantee supplies a forcing strategy and, for each
opposing strategy, a completed play with a terminal board satisfying the goal.
Consequently the theorem contains an existence claim, rather than an implication
that could hold because no completed play exists.

`Othello.Value.value-realized` pairs the two forcing strategies and constructs
a completed play whose White count equals its Black count plus 8.
`value-score` relates this equality to the signed integer score. Play
determinism also yields `value-unique`: two alleged values for the same
initial game must coincide.

Problem 2 and Problem 3 are stated only. The 6×6 statement retains both value
+4 and an optimal-strategy outcome with Black 16 and White 20; a difference of
4 alone would lose the separate disc counts. The 8×8 statement has value 0.
No inhabitants of those types are asserted.

= Rules and score

Boards are nested finite vectors of cells, indexed by a size with dimensions
4, 6 or 8. Coordinates consist of two bounded finite indices. The initial
center is W B / B W, and Black moves first. A placement requires an empty
square and at least one adjacent opponent disc followed along a straight
ray by a friendly disc. The implementation examines all eight directions,
with bounds checked separately on each coordinate, and flips all captured
discs using the original board.

Successors enumerate legal placements in row-major order. If the mover has
no placement but the opponent does, there is exactly one successor: a pass
with an unchanged board and the opposite mover. If neither can place, the
successor list is empty. Terminal positions may contain empty squares.

Score is White discs minus Black discs; empty squares are not awarded.
The independent perfect-play fixture is Black 3–White 11 with two empty
squares and no passes. This agrees with Takeshita and Ikeda's reported line.
Awarding those empty squares to White changes that particular line's score
to +10, without establishing the minimax value of that other convention.

#pagebreak()
= Certificates and proof boundary

An exact Python bitboard search produces two finite strategy trees. A second,
scalar board implementation independently checks the value, legal moves,
terminal line and certificates. Search and generation are untrusted:
neither a Python answer nor native execution of a checker establishes the
submitted theorem.

The certificate language has four constructors. A leaf requires genuine
terminality and the requested score bound. A choice supplies one legal
successor index at the forcing player's turn. An opponent fork must have
exactly one child for every successor, in order. A pass requires a forced
pass and a singleton successor list. Certificates contain no board states
or trusted terminal scores. The Agda checker recomputes the game successors
and disc counts itself.

`Game.Soundness.checkSound` proves generically that acceptance implies a
constructive guarantee. Its recursion follows the finite certificate,
including every opponent branch. Arbitrary opposing recommendations are
resolved to an actual legal successor. The resulting play records the
normalized index in the history used for later decisions. Certificate
acceptance therefore establishes termination along each forcing strategy
without assuming global game termination.

The concrete certificates have 399 nodes for White's lower bound and
337 nodes for Black's upper bound. Their union visits 451 distinct positions
whose successors were compared independently in Python. This count describes
these trees, not the entire game graph. The exact search cached 62,789 states.
The two concrete acceptance equalities in `Othello.Proof4` are proved by
`refl`, invoking Agda's evaluator. No postulate or external solver theorem is
introduced. The safe checked soundness theorem then produces the strategies.

= Faithfulness and termination

`Othello.Correctness` gives an inductive description of a bracket, separately
from Boolean scanning, and proves scan and capture soundness and completeness.
It proves that Boolean legality corresponds to an empty square with a bracket,
and that legal-move enumeration is complete. General counting proofs establish
that each legal placement consumes exactly one empty square and increases
occupied squares by exactly one, while flips preserve both quantities.

The termination development uses a natural measure consisting of twice
the empty-square count plus a bit for having no current placement. A placement
decreases the empty count. A forced pass leaves the count unchanged and turns
an immobile mover into a mobile mover, dropping the bit. Thus every legal
successor decreases the measure. Accessibility supplies completed plays for
arbitrary pairs of strategies independently of the certificate theorem.

Agda fixtures exercise corners, edges, multiple capture directions, illegal
placements, compulsory passes, terminal empties, mirrored starts and the
3–11 line. Perft counts pass as a ply and assigns zero paths to a terminal
position at positive depth. The 8×8 initial counts through depth 5 are
4, 12, 56, 244 and 1396, agreeing with OEIS A124004.

#pagebreak()
= Reproduction and evidence

The project is self-contained on `Agda.Builtin.*`, a small prelude, and
checked finite-vector and arithmetic modules. Every project Agda module
uses `--safe --without-K --cubical-compatible`. There are no project
postulates, unsolved holes, termination escapes or positivity escapes.
The core uses ordinary Agda equality; it does not assert Cubical computation
under transports. Agda reports indexed-match compatibility warnings about
that additional computation behavior.

Two available Agda binaries both identify themselves as version 2.9.0 but
differ in build and behavior. A standard-library 2.3 irrelevant-field module
was accepted by the desktop binary and rejected by the laptop binary.
The builtin-only foundation avoids this dependency and enables both machines
to check the same source without registered libraries. Verification records
include the binary hashes, not just the version string.

Run the Python checks with
`python3 -m unittest discover -s tools -p 'test_*.py' -v`.
Run the complete Agda development with
`agda --no-libraries --safe --without-K --cubical-compatible -i src src/Everything.agda`.
The scripts in `scripts/` add heap limits and serialized measurements.
For fresh checking, `tools/measure.py` supports `--cold`, which passes
`--ignore-interfaces`, and `--html` for highlighted source.

The source laptop is a Ryzen 7 5700U with about 7 GiB RAM. The desktop,
accessed over the user's Tailscale SSH connection, has a Ryzen 7 9800X3D and
about 30 GiB RAM. Desktop checks run in an isolated source snapshot with a
16 GiB systemd memory limit and no cgroup swap, with a separate Agda heap
limit. Build interfaces are not transferred. The scripts record command,
source hashes, machine, toolchain, cache state, exit code, wall time and peak
RSS. The checked source must remain unchanged throughout a measured run.

The verification ledger and packaged machine-readable records contain the
actual measurements. Cold checking of all 22 project modules, including
depth-5 perft, took 6.81 seconds with 0.163 GiB peak RSS on the desktop,
including HTML generation. The laptop took 15.88 seconds with 0.149 GiB
peak RSS. These describe those source snapshots and binaries.
The release includes tagged source, certificate data, this write-up,
highlighted source, checking logs and a submission manifest. Problems 2 and
3 remain explicitly marked statement only.

= AI assistance

The project used Codex and a user-supplied Claude plan. Codex assisted with
implementation, proof terms, tests, documentation and untrusted certificates.
Observed session metadata identified the continuing coordinator as GPT-6.1 Sol
with xhigh effort; the implementation workers were explicitly started as
GPT-6.1 Sol with high effort. Earlier unobserved coordinator identities are
not inferred. The full disclosure is in `docs/ai-use.md`. Correctness rests
on safe Agda checking and the stated rule model. The submission email has
not been sent.

= References

#link("https://auto-res.github.io/tpp2026/en/tpp2026mark/")[TPP-mark 2026 challenge.]
Problems and submission requirements, deadline 15 November 2026.

#link("https://miyazaki-u.repo.nii.ac.jp/record/4739/files/engineering44_221-227.pdf")[
Takeshita and Ikeda (2015), pp. 224–225.]
The reported 3–11 line and 218 examined terminal positions; the latter is
not a count of all nodes or of this submission's certificates.

#link("https://oeis.org/A124004")[OEIS A124004.]
Initial 8×8 Othello game-tree counts.
