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

19 October 2026: safe Agda accepts the complete standard initial **6×6 raw
White-minus-Black value +4**, together with a completed legal play of the
**same optimal strategy pair ending Black16–White20**:
`Tests.CompleteUpperRows6.Result.initial6x6 : Problem2`.
Both complete `AllParts` records, `Result` and a fresh typed wrapper were
checked. The exact 4,128-module source graph has zero project postulates,
holes or proof escapes; all 23 original P1 sources and their tag are preserved.
See the [completion receipt](results/problem2-completion6-20261019.json),
[verification record](docs/verification.md) and
[private proof package](docs/private-problem2-package6.md).

The private source/evidence collection has a verified restoration of its
small evidence archive and references the existing large archives and donor
caches. It is cache-dependent; an independent standalone cold rebuild was
not performed. CPU, RAM and disk limits were preserved; at that point nothing
had been published or emailed. AI assistance is disclosed in the package documentation.

### What this public repository contains

- Agda sources for the 4×4 and 6×6 developments, the Python tooling used to
  generate and check certificates, certificate samples, and the 6×6 completion
  receipt (`results/problem2-completion6-20261019.json`).
- **Not included:** the large immutable proof archives and generated caches
  that the accepted 6×6 check depends on, so the 6×6 result cannot yet be
  rebuilt from this repository alone; internal agent handoff and planning notes
  (links to them below are marked "internal notes, not published"); and the
  ongoing 8×8 (Problem 3) work.
- Paths under `/mnt/data/...` and `/home/eapiova/...` in records and tools refer
  to the author's machines.

## Historical development notes

The dated observations below retain the proof boundaries at those earlier
times; the accepted 19 October result above is the current 6×6 status.

18 October, production: the sequential safe Agda checks for all remaining
649 UPPER / 684 LOWER groups are running within the existing 48-hour CPU
budget and unchanged resource limits. The full initial6×6 theorem remains
**unproved**. See [verification.md](docs/verification.md) and the
[live production index](results/full-row-production-current6-20261018.json).
Private package components and verification boundaries are documented in
[private-problem2-package6.md](docs/private-problem2-package6.md).

18 October, latest: safe Agda owns **50,000 UPPER / 40,000 LOWER rows** on the
fixed complete maps. Both remaining-source packages and the complete Body
layout preflight pass; **649 UPPER / 684 LOWER group proofs remain open**.
Initial6×6 +4 and the SAME optimal initial Black16–White20 pair are still
**unproved**. See [verification.md](docs/verification.md) for current receipts
and the bounded remaining-work forecast.

18 October, source preparation: all remaining UPPER certificate sources are
generated and integrity-verified; LOWER preparation is running. These sources
still need Agda checks and add no proved rows. Current cache locations and
resource receipts are in [verification.md](docs/verification.md).

18 October: Agda accepts the full **6,530,011-state UPPER** and
**6,873,047-state LOWER** tables, both prefix-resolver compatibilities and
**30,000 UPPER and 20,000 LOWER rows on their fixed maps**. Full composition and the SAME-pair bridge
are checked conditionally; 651 UPPER and 686 LOWER group proofs remain open.
The complete proof and resource gates also remain open.
Initial 6×6 +4 and the SAME initial optimal Black16–White20 pair remain
**unproved**. See [current verification status](docs/verification.md).

18 October: safe Agda checks a 1,600-row UPPER Partial and all 21 early
literal-prefix subtree checks for EACH bound. The SAME-pair initial assembly
is checked **conditionally on two fully proved global maps and their resolver
compatibilities**; those premises remain open. Initial6×6 +4 and the SAME
initial Black16–White20 optimal pair remain **unproved**. See the
[current verification status](docs/verification.md) and
[conditional assembly receipt](results/lower-prefix-inline-closure-index6-20261018.json).

18 October, consecutive row checker: safe Agda checks a **10,000-row LOWER
Partial on one encoded map**, using shared state chunks and a proved terminal
fallback. The row check takes 11.78 CPU seconds and 0.99 GiB peak RSS. Other
state rows and initial bounds remain open; this sample overlaps the older
3,000-row and 2,600-row maps, so the counts cannot be added. Initial 6×6 +4
and the SAME optimal initial Black16–White20 pair remain **unproved**. See
the [receipt index](results/consecutive-global-closure-index6-20261018.json)
and [verification status](docs/verification.md).

18 October, packed row assembly: safe Agda checks a **3,000-row LOWER Partial
over one encoded state map**, with exact row ownership and citation-map
compatibility proved. The 3,385 referenced keys outside these owned rows
still need proofs. This sample map and the earlier 2,600-row map overlap;
their coverage figures cannot be added. The closed row assembly passes in
10.60 CPU seconds and 0.94 GiB peak RSS. Initial 6×6 +4 and the SAME initial
optimal Black16–White20 pair remain **unproved**. See the
[checked receipt index](results/packed-common-rows-closure-index6-20261018.json)
and [verification status](docs/verification.md).

18 October, literal strategy suffix: safe Agda checks both +4 guarantees
at the 13 literal states `p21`–`p33` and assembles one pair following that
suffix to Black16–White20. The checked
[initial bridge](src/Othello/SpliceSuffix21.agda) still requires both guarantees
at all 21 earlier states `p0`–`p20`; the initial value and Problem2 remain
**unproved**. See [the checked receipt index](results/splice-suffix21-closure-index6-20261018.json).
The earlier common state/body-map theorem retains its 2,600 lower rows. The user-approved CPU
redistribution is applied; total CPU remains 48 hours and resource safeguards
are unchanged. See [current verification status](docs/verification.md).

18 October, canonical desktop continuation: safe Agda checks **1,600 new lower
rows** and composes them with the accepted 1,000-row baseline into a genuine
**2,600-row Partial theorem over one common state and certificate map**.
All 23 tagged P1 sources and the original checkpoint are preserved. The initial
6x6 +4 theorem and the SAME optimal Black16-White20 pair remain unproved.
Necessary formalization and tests are authorized within the existing limits,
without per-test confirmation. See the current desktop handoff (internal notes, not published)
and [verification ledger](docs/verification.md).

18 October, multi-part update: safe Agda accepts all four direct-import parts
(800 repeated row assertions) and their semantic composition with the prior
200-row part. The resulting **1,000-row Partial theorem uses a common state and
certificate map**. The bounded desktop job uses362.54 CPU seconds,327.32 wall
seconds and5.56GiB peak RSS. Held-out row/bridge CPU prediction errors are1.65%
and1.06%; the whole-workflow production gates remain open. All23 P1 sources and
zero postulates are preserved. The initial6x6 +4 theorem and the SAME optimal
initial16-20 pair remain unproved. See the
current handoff (internal notes, not published).

18 October: safe Agda accepts the variant with directly shared state data for
Part34176: all 200 repeated row checks and their 17-module full-map bridge pass.
The complete bounded job uses 82.12 CPU seconds, 74.66 wall seconds and 4.05 GiB
peak RAM. All four accepted donors, all 23 P1 sources and zero postulates are
preserved. This checks partial coverage; the initial 6×6 +4 theorem and the
same optimal initial 16-20 pair remain unproved. The single-test disk exception
is consumed and production remains unauthorized. See the
current handoff (internal notes, not published).

17 October: safe Agda accepts all eight new lower parts (1,600 new local
row facts). Heldout row CPU prediction error is1.13%; the bounded desktop pilot
uses118.58 CPU seconds and1.20GiB peak RAM. Donors, all23 P1 sources and zero
postulates are preserved. Initial6x6 +4 and its SAME optimal16-20 pair remain
unproved; no production is authorized. See the current handoff (internal notes, not published).

13 October: both lower and upper sample assemblies pass with direct applications,
reusing all 32 accepted row proofs. Peak linkage-check RAM is 0.91 / 1.12 GiB;
Root interfaces are under 50 KB. Private imports give no further benefit.
Complete initial coverage, full-size assembly memory and artifact storage are
still unvalidated; production remains NO-GO. The initial +4 theorem and its
optimal 16–20 strategy pair are not yet proved. See the
current assessment and handoff (internal notes, not published).

12 October continuation: the largest initial-layout parts pass all twelve
safe 50-row checks (600 rows, peak checker RSS 1.07 GiB). Closed global lower
sample alignment passes at 4 and 8 parts; the 16-part monolithic form exhausts
its desktop heap. Splitting lets all sixteen lower sample parts assemble with global
lookup alignment checked (peak RSS 2.10 GiB). Eight checker workers measure
6.53 effective slots. All upper sample alignments now pass as well (peak checker
RSS 2.73 GiB; complete CPU forecast error 1.37%). The initial theorem, optimal initial pair and production gates
remain open. P1 and zero postulates are preserved. See the
current handoff (internal notes, not published).

12 October: **all 32 initial-layout sample parts are Agda-checked**, including
both fixed holdout batches. CPU errors against the unchanged prospective row
forecast are 1.8% lower and 0.4% upper. Both conditional 4/8/16-part assembly
pilots pass while reusing accepted parts. Global alignment, worst-case parts,
full initial assembly and production gates remain open. The initial +4 theorem,
SAME optimal initial 16–20 pair and private package remain unfinished. P1 and
zero postulates are preserved. See the current handoff (internal notes, not published).

10 October: **all 267 parts, all 31 assembly nodes and the final root of the
numeric lower descendant are Agda-checked**. The desktop run is terminal,
accepted and collected, with assembly peak RAM 2.04 GiB. It proves an original-
rule lower +4 guarantee from a 14-disc position. P1 is preserved, with zero
postulates. Initial 6×6 +4, the initial optimal 16–20 pair, production gates
and submission packaging remain unfinished. The uniform-lazy generator has
five passing metered tests; a new lower/upper assembly pilot is next. Older
dated observations below are historical. See the
current handoff (internal notes, not published).

9 October, after the collected lazy repair: **243 numeric descendant parts
are accepted**. `nat-descendant-final-20261009` is terminal and collected,
with Part0–241 preserved and Part242 stopped by heap exhaustion. The accepted,
collected `nat-lazy-repair242-20261009` checks 145 real state-vector equalities
and restores Part242's original conditional export: 18.412866 CPU seconds,
0.783798 GiB RSS. Earlier proof sources, interfaces and input data are unchanged.
The original fixed-suffix forecast remains incomplete/inconclusive; its failed
held-out Part242 cannot be replaced by lazy timings or omitted after observation.
The detached lazy continuation is active on the desktop, preserving the 243-part
prefix and checking the remaining parts, hierarchy and Root. Initial +4, the
SAME optimal initial 16–20 pair, root
feasibility, production GO and private packaging remain incomplete. The allowance
is 48 CPU-hours. See the current handoff (internal notes, not published).
The detailed dated observations below retain their historical scope.

9 October: the persistent goal covers the initial 6×6 theorem, optimal 16–20
strategy pair and private submission packaging. Those requirements remain
unproved. The fixed pilot now has **twenty of twenty** sampled original-rule
lower +4 guarantees and all 100 sampled upper bounds checked safely. All 451
holdout phases pass; measured CPU is 2.78% above the forecast recorded before
checking. Part/binding RSS maxima are 0.85 / 2.55 GiB, within the unchanged caps.
Earlier accepted proofs, failed attempts, zero postulates and tagged P1 remain
preserved.

The earlier per-frontier representation has no production GO: its nominal token
component projects 1,729 desktop hours and its compact certificate data 76.6 GiB,
exceeding the approved 168-hour / 10-GiB gates before additional workflow costs.
After the user authorized more compute, the ledger allowance became 48 CPU-hours.
The compact, symmetry-normalized native censuses now complete both initial
bounds: 67,468,478 distinct lower positions and 66,936,456 upper positions.
Their expanded trees contain 713,527,417 and 207,779,198 occurrences respectively.
Each took about ten minutes on the desktop at about 5 GiB RSS. These are exact
native counts, not Agda acceptances. New bounded shared-certificate pilots pass
both prospectively fixed heldout timing checks. The streaming exporter also
pins the chosen 16–20 line: Agda accepts both +4 bounds at its 16-disc, 18-disc
and 20-disc positions. The 16-disc checks use 259.52 nested CPU seconds with
a largest part of 1.303 GiB. An independently tested exporter bounds long
inline bodies. The resumed 14-disc lower pilot now accepts all 267 parts and
their original-rule root assembly, reusing its first 168 accepted parts.
Duplicate frozen source allocation and lossless archival of retired native
dumps recover room without changing proofs.

The full line-pinned layout measurements also complete: 34,366 lower and
34,932 upper parts, with about 478 MiB of combined compact data. Their proof
imports form almost complete prefix closures. The earlier measured cost model
projects about 17,504 CPU-hours before final assembly, so this dependency design
has no production GO. This is a statistical forecast, not an Agda result or a
proof that every representation is infeasible.

`Game.Indexed` links independently checked rows using a well-founded order
and local/global resolver compatibility. Balanced IDs, exact compact decoding,
sparse state views and explicit strategy spines are implemented. All 267 parts
of the data-only import experiment accept. A real three-shard desktop pilot
also accepts independent proofs, original-rule assembly and an actual 16–20
completed strategy pair **from a late position**; the extended `Everything6`
passes in that run. A new hierarchical assembly pilot also checks both bounds
and the actual late-position 16–20 play; its extended `Everything6` accepts.
The complete 53,217-row indexed descendant now has **all 267 parts and 30
hierarchy nodes accepted**, with earlier proofs reused unchanged. The final
hierarchy node exhausts its 2,600-MiB heap during import loading, before its
proof declaration; the final root is therefore unchecked. The separate legacy
descendant proof remains accepted. Updated safe `Everything6` also passes.
Numeric references now avoid embedding the whole shard layout in certificate
types. Three real-part comparisons show about 5–6% less CPU and 34–41% smaller
own interfaces. Their memory improvement varies; the largest optimized sample
still uses about 1.40 GiB. Safe numeric map, ordering and assembly proofs pass,
including a generated three-shard hierarchy for both original-rule descendant
bounds. Updated `Everything6` passes on the desktop; the assembly fixture also
passes on the laptop. These are measured small pilots, not a production GO.
At the earlier launch, the bounded detached **`nat-descendant-20261009`** checks the full
53,217-row lower descendant with the numeric format, then its hierarchy and
root. It checkpoints every accepted part. A second detached service,
`nat-descendant-finish-20261009`, waits and resumes the exact accepted prefix
if the first service stops for CPU. The finite desktop queue survives
laptop shutdown; see the handoff for authoritative service state.

Initial +4, the initial optimal pair, full production gates and submission
packaging remain unfinished. See the current handoff (internal notes, not published).

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

The `six` branch adds a zero-postulate 6×6 feasibility study. Its safe search,
frontier composition, faster equivalent rules and late-game pilot are checked;
the initial 6×6 result remains unproved. See remote jobs and Android access (internal notes, not published)
for detached desktop computation and phone pairing, and the
feasibility study (internal notes, not published) for measured progress and outstanding gates.
The study now includes checked shard imports and all eight board symmetries,
with certificate transport that remaps legal choices and opponent replies.
The current per-leaf design fails the production timing and artifact gates;
the one-week production run has not started.
The subsequent 100-position global-sharing pilot adds a checked compact
decoder. Its payload is about 1.85× smaller, but sharing removes only 0.4% of
tokens in this sample. Memory diagnosis repairs root assembly; checked literal
import tables let Part77 and its dependent Part78 pass within unchanged caps.
The pilot now has checked upper +4 guarantees from **all 100 sampled positions**.
The original layout reaches 84 of 125 accepted parts; separate citation closures
check the remaining 34 root bounds with at most 1.14 GiB RSS per part.
The 7 October module-local warning filter preserves those certificates and
ordinary equality goals, checks all 263 parts and ten groups, and **accepts one
combined theorem for the 100 sampled bounds**. The collector uses 2.74 CPU
seconds / 2.42 GiB RSS within its unchanged limits; parts peak at 1.21 GiB.
The full interface pool has 75% fewer serialized nodes than the packed baseline.
A prospective upper timing holdout differs by 2.85%. The initial result remains
unproved; lower-side and complete-workflow feasibility still need validation
before production. The matched twenty-root lower pilot accepts 122 parts before
exhausting its fixed heap cap. Its verified prefix supplies two original-rule
lower +4 guarantees without repeating certificate checks; the full sample and
timing holdout remain incomplete. A later stress test isolates the largest
unproved training root. Its original layout still exhausts the heap, but four
independent conditional certificate checks pass at 0.49–0.81 GiB RSS. Supplying
their citation proofs through the original merged tables hits the CPU limits.
A new owner-directed collector discharges all 12,248 citations and proves that
root's original-rule White lower +4 guarantee in 66.62 CPU seconds at 2.55 GiB
RSS, within the unchanged assembly caps. This brings the fixed lower sample to
three of twenty standalone bounds; its timing holdout and the initial-board
theorem remain incomplete. All jobs are collected. See the
current handoff (internal notes, not published) for the preserved state and next
engineering questions.

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
