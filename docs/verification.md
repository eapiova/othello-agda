## 2026-10-19 — Complete initial6×6 Problem2 accepted

Safe Agda accepted `Tests.CompleteUpperRows6.Result.initial6x6 : Problem2`
at12:36UTC, with both actual complete `AllParts` records, `Result` and a fresh
typed wrapper. This proves standard initial6×6 raw White-minus-Black+4 against
all opposing strategies and a completed legal play of the SAME optimal pair
ending Black16/White20. The selected `Statements`, `Board`, `Rules` and
`Game.Core` definitions were reviewed explicitly; Black moves first and no
empty-square bonus is used.

Authoritative records are
`results/final-problem2-ephemeral-reconciliation6-20261019.json` and
`results/problem2-completion6-20261019.json`. The accepted service consumed
265.381154 whole-service CPU seconds and peaked at7.839565GiB, with zero swap.
The outer wait4 record was charged once and its positive systemd residual
accounted separately; the nested checker receipt was not charged again.

All667 production batches cover6,530,011 UPPER and6,873,047 LOWER row facts.
The final check reused1337 accepted Rows interfaces read-only, rebuilt1337
data-only Body interfaces exactly once, and checked the two AllParts records,
Result and wrapper. New interfaces existed only in512MiB/16MiB private tmpfs
mounts, inside the unchanged12GiB total RAM cap. All six archive views closed;
borrowed source/cache pools, accepted Rows and persistent build roots stayed
unchanged. The complete Agda output is retained losslessly compressed.

The exact4128 non-builtin source modules pass the safe/without-K/cubical-compatible
audit: zero postulates, explicit holes or proof escapes. Builtins are explicitly
from the pinned Agda2.9.0 compiler. All23 P1 files match both canonical pins
and tag `tpp-mark-2026-problem1` (`e734d4c3e8a783a5033f7510739d680943a26015`).
The original4×4 proof remains preserved.

The private package verified all667 row-check receipts in334 closed cohorts
and restored66 small source/evidence files with exact bytes, modes and ns
timestamps. See [private-problem2-package6.md](private-problem2-package6.md).
Large archives and donor caches remain references; this is a local collection,
not an independently cold-rebuilt standalone distribution. AI assistance is
disclosed. No publication, upload, email, commit or push was performed.

Earlier dated entries below are historical observations, including failures
and earlier conditional or partial results. Their receipts remain preserved.

## 2026-10-18 19:53 UTC — Production continues; final checker prepared

Twelve accepted production batches bring fixed-map coverage to **280,011
UPPER / 40,000 LOWER rows**. There are 625 UPPER and 684 LOWER group fields
still open. The exact current service handle and counters remain in
`results/full-row-production-current6-20261018.json`; the pinned production
inputs have not changed. The full initial6x6 theorem remains **unproved**.

`tools/final_problem2_check6.py` and `tools/problem2_source_audit6.py` are
prepared and parse successfully. No final Agda check or complete source audit
has run. The final controller requires complete row coverage and reconciled
outer reservations before a finite final-stage authorization and launch. It
will permit reconstruction of omitted data-only Body modules while rejecting
repeated Boolean Rows checks, and check both AllParts, Result and the exact
Problem2 wrapper. The full completion requirements are recorded in
`results/problem2-completion-requirements6-20261018.json`.

An independent bounded meter records whole-service cgroup CPU, including the
supervisor CPU excluded from wait4 child rusage. Reconciliation must retain
the exact wait4 receipt and conservatively account the positive cgroup-minus-
wait4 residual within the same reserved kernel envelope. The meter uses the
existing parent controller allowance. Its 64MiB hard RAM envelope is deducted
from the primary service envelope, keeping aggregate Othello RAM at12GiB;
all original CPU, swap, disk and preservation limits remain in force.

The private package's current collection and restoration boundaries are in
[private-problem2-package6.md](private-problem2-package6.md). It is a local
manifest and archive collection with exact source provenance; independent
standalone-package rebuilding and final package closure remain pending.
AI assistance covered the prepared controllers, source audit, meter and docs.

## 2026-10-18 19:29 UTC — Full remaining-row checks started

The reviewed single-checker controller is running the frozen **649 UPPER /
684 LOWER groups** (325 + 342 batches). At launch, safe coverage remains
50,000 UPPER / 40,000 LOWER rows; **the complete initial6x6 theorem and the
SAME optimal initial Black16–White20 pair remain unproved**. Read
`results/full-row-production-current6-20261018.json` for live progress,
service/reservation handles and terminal-record reconciliation instructions.
The continuation and forecast JSON files are pinned inputs and must stay
unchanged during this production run. Do not dispatch a duplicate service.

An additional 8,000 unused compiled and 5,000 unused native CPU seconds were
transferred to kernel, preserving the **172,800-second total** and all prior
charges. Production reserves 50,000 kernel seconds, with a 49,500-second outer
cap, sequential 160-CPU/400-wall-second child caps and an 18-hour service wall
cap. RAM stays 12 GiB, swap/core zero, root free floor 80 GiB, retained study
cap 12 GiB. The physical forecast is tight and includes explicit stop buffers;
resource exhaustion must retain accepted progress and every failure receipt.

The private selected-source dependency package is integrity-verified: 4,128
selected modules, with 92 core files in a 382,209-byte archive; large source
archives are reused. This is source integrity evidence, not a package build
or a full theorem check. See `results/private-core-package-index6-20261018.json`.

The synthetic archive validation passes five cases: interrupted append to new
and existing ZIPs, rollback of an uncommitted closed append, preservation of a
committed append, and lossless receipt cohorts with actual filesystem metadata.
The first fixture incorrectly assumed POSIX chmod0640 on the mounted artifact
filesystem; that failed receipt and its 0.174810 CPU-second charge are retained.
The corrected run uses observed file modes/timestamps and passes in 0.162045
CPU seconds. See `results/full-row-storage-validation-index6-20261018.json`.
Durable central-directory journals protect earlier proof and receipt members.
Only validated data-only Body interfaces may be evicted; mathematical Rows
payloads remain archived with exact header/payload lineage. AI assistance
covered the controller, review, packaging, tests and documentation.

## 2026-10-18 19:05 UTC — 50,000 UPPER / 40,000 LOWER rows; complete-source preflight passes

Safe Agda accepts fresh groups **100 and 300 on each fixed full map**. UPPER
now owns groups 6, 100, 300, 500, 652 (50,000 rows); LOWER owns 6, 100, 300,
686 (40,000 rows). **649 UPPER and 684 LOWER group fields still need proofs.
Initial6x6 +4 and the SAME optimal initial Black16–White20 pair remain open.**
New receipts: `results/complete-row-preflight-index6-20261018.json` and
`results/complete-lower-batch-index6-20261018.json`.

The frozen two-group predictions pass the unchanged 30% component gate:
UPPER 52.472341 predicted versus 53.621652 measured CPU seconds (2.143371%
error), LOWER 50.070906 versus 51.015548 (1.851675%). Both bounds also pass
cached proof replay after deleting only generated Body data interfaces, and
again after recompressing the row interface frames with identical 24-byte
headers and decoded payloads. Pilot original frames remain archived; no
Boolean row checks are repeated by those replays. The source bytes are exact.

Both remaining-source packages are complete and integrity-verified: UPPER
104,119,064 bytes / 80,262,245 tokens, LOWER 111,009,620 bytes / 88,263,404
tokens. LOWER preparation was interrupted before its original internal output
envelope would overflow, and recovered by appending only missing groups to
the closed ZIP. All 642 reused source groups, their bytes/modes/timestamps,
the failed receipt and its 766.814607 CPU-second charge are retained. The
recovery charges 123.344896 CPU seconds. Current source indices are
`results/complete-{upper,lower}-row-sources-index6-20261018.json`.

Loading **all remaining Body modules with both full state tables** succeeds
with `--no-write-interfaces`: 112.171397 CPU seconds, 4.914501 GiB peak RSS.
This is a complete-source layout measurement, not a check of the remaining
game rows or of the final theorem. The complete row records remain unsupplied.

Lossless archives retain 7,082 closed controller/log/receipt/inactive-source
files. Another 124 inactive cache copies were removed only after an exact
byte-hash restore map proved their contents remain in unchanged checkpoint
archives; active donors and all mathematical proof bytes are preserved.
Twenty-three newer closed logs are also archived byte for byte. See the
`closed-text-archive`, `archived-cache-duplicates` and `completion-log-archive`
receipt indices dated 20261018. Historical plaintext paths now resolve through
their archive manifests. P1, original desktop runs and NAMOR are unchanged.

The calibration/preparation scope is 4263.508022/6000 CPU seconds, including
every earlier failure and allowance. All current jobs are closed and all
views unmounted. The remaining-row forecast is frozen in
`results/complete-remaining-row-forecast6-20261018.json`: 44,504.606065 checker
CPU seconds for 667 batches. It proposes a 50,000-second production reservation
and an unused-category transfer of 8,000 compiled + 5,000 native seconds;
neither transfer nor production reservation is applied yet. The 172,800-second
total is unchanged. Its storage estimate fits narrowly and requires grouped
record archiving, compact retained proof frames and physical guards; a bounded
resumable production harness still must implement these controls before GO.
AI assistance covered these sources, proofs, measurements and resource plans.

## 2026-10-18 18:25 UTC — Complete UPPER certificate sources prepared; LOWER preparation running

The authenticated UPPER wire has produced sources for all **651 remaining
groups / 6,500,011 owners**, including the final 11-row group. The archive
contains 1,304 modules, 80,262,245 certificate tokens and 104,119,064 compressed
bytes. Every source entry, mode and nanosecond timestamp was verified through
the read-only archive view. Preparation charged 809.293547 CPU seconds, plus
the recorded 10-second controller allowance; all 23 P1 files are unchanged.
Receipt: `results/complete-upper-row-sources-index6-20261018.json`.

**These new row sources have not been checked by Agda.** The generated
`Result.initial6x6 : Problem2` is also unchecked source. Mathematical coverage
remains 30,000 UPPER and 20,000 LOWER rows, with 651/686 group fields open.
LOWER source preparation is running under its existing assembly reservation;
the next preflight will check two new UPPER groups and measure loading all
Body modules without claiming any additional row proofs from that load.

Both full table caches now use payload-preserving recompression: current
archives are 91,931,780 UPPER bytes and 97,645,857 LOWER bytes. All source and
mathematical proof interface bytes are unchanged; each recompressed data-only
interface retains its 24-byte header and exactly the same decoded payload.
Dual-cache Agda replay succeeds without repeating Boolean row checks. The
original compressed data frames differ intentionally; their lineage is
recorded. Use the current cache references, not historical container paths.
See `results/packed-{upper,lower}-cache-index6-20261018.json`.

Unused vector-table data interfaces were retired while preserving all source
and non-table proof interfaces in a verified archive. Seven closed sample
JSON inputs were archived losslessly. Receipts and historical paths remain
preserved; original desktop runs and NAMOR were untouched. See
`results/retired-data-release-index6-20261018.json` and
`results/sample-input-archive-index6-20261018.json`.

The recorded calibration/preparation scope is now capped at 6,000 cumulative
CPU seconds; 2,953.250235 are consumed before the live LOWER job. This changes
no total grant: 172,800 CPU seconds, 12 GiB RAM, no swap/core dumps, the 80 GiB
root floor and 12 GiB retained-artifact cap still apply. AI assistance covered
source generation, cache/storage work, provenance and bounded test harnesses.
**Initial6x6 +4 and the SAME optimal Black16–White20 pair remain unproved.**

## 2026-10-18 17:19 UTC — Cached row proofs survive omission of data-only interfaces

An isolated copy retains the exact accepted `Rows500.agdai` proof while
omitting `Body500.agdai`. With `--no-write-interfaces`, Agda rebuilds only the
String data and reuses the unchanged row proof: exit 0, 9.291834 CPU seconds,
0.914860 GiB RSS, no Boolean game-row rerun and no new data interface written.

A second read-only view also omits all **654 UPPER Group data interfaces**.
Every source byte remains identical to the accepted full-map source. Agda
again reuses the unchanged proof: exit 0, 25.085343 CPU seconds, 2.968811 GiB
RSS. The data-only cache policy is therefore usable in this tested case;
complete-layout storage and whole-proof memory are still unvalidated. Both
original archives remain untouched. These replays add zero game rows.

Indices: `results/data-cache-eviction-index6-20261018.json` and
`results/table-cache-eviction-index6-20261018.json`. Current complete audit and
continuation details are in `results/full-text-maps-current-audit6-20261018.json`
and `results/full-text-maps-continuation6-20261018.json`. All jobs are closed;
all archive views are unmounted; the ledger has no outstanding reservation.
The cumulative calibration scope is 1916.086973/2000 CPU seconds; the unchanged
172800-second total grant has 63178.111559 seconds available. All 23 P1 files
still match. **The full initial6x6 theorem remains open:** 30,000 UPPER and
20,000 LOWER rows are owned, with 651 UPPER and 686 LOWER group fields pending.
AI assistance covered these bounded cache/storage experiments and their
receipts; no source or proof payload is changed by either replay.

## 2026-10-18 16:56 UTC — 30,000 UPPER and 20,000 LOWER rows on the full fixed maps

A fresh UPPER group 500 (owners 5000000..5009999) is accepted and certified on
the SAME 6,530,011-state `Tests.TextUpperPacked6.Root.G` as groups 6 and 652.
The fixed UPPER map now has 30,000 owned rows; LOWER has 20,000 on its own
6,873,047-state map. **651 UPPER and 686 LOWER certified group fields remain
open. Initial 6x6 +4 and the SAME optimal initial Black16–White20 pair remain
unproved.** Both exact prefix compatibilities and the conditional full-map /
SAME-pair composition are already checked; the complete records are unsupplied.

The revised two-point UPPER forecast is frozen before checking the fresh group:
42.787521 CPU seconds predicted, 43.913555 measured, **2.564205% error**.
Together with the independent LOWER heldout's 2.736527% error, the new row-cost
component gates pass. The older failed forecast is preserved. Full certificate
generation, retained storage and whole-proof memory still need validation;
production GO remains false.

A complete authenticated 6,530,011-state Python index is built successfully:
11.456895 CPU seconds for indexing, 10.113453 for the second scan, 1.423607
for transforming the selected 154,240-token group. The enclosing preparation
uses 0.923378 GiB peak RSS. The new safe Agda row check uses 2.345745 GiB RSS
and produces two accepted interfaces, including `Rows500.certified`.
Index: `results/text-upper-holdout-index6-20261018.json`.

The complete UPPER/LOWER caches are mounted from the immutable archives in
`results/text-{upper,lower}-cache-current6-20261018.json`; their old plaintext
paths are historical. The accepted fresh group is at
`/mnt/data/othello-agda-desktop-artifacts-20261018/text-upper-holdout6-20261018/check`.
AI assistance covered preparation, proof assembly, cost modelling and resource
controls. Original desktop runs, NAMOR, P1 and the total CPU grant are preserved.

## 2026-10-18 — Both full state maps and exact prefix compatibilities checked; initial theorem open

Agda accepts the fixed direct-text LOWER table containing all **6,873,047
states**, the exact **558-entry** LOWER prefix compatibility, a symbolic
**688-field** certified composition, and the conditional application to
`Problem2` with the actual UPPER map and its already checked compatibility.
The latter uses the existing SAME-pair splice to Black16–White20. It still
requires both complete records of certified group proofs; neither is supplied.

On this new fixed LOWER map, groups 6 and 686 provide **20,000 accepted rows**
(indices 60000..69999 and 6860000..6869999). The training check takes
24.232649 CPU seconds and 1.571480 GiB RSS; the dense heldout takes
86.853720 CPU seconds and 3.137917 GiB RSS. These are conditional row proofs,
not initial guarantees, and are separate from earlier sampled maps. There are
686 LOWER and 652 UPPER group fields still open. **Initial6x6 +4 and the SAME
optimal initial 16–20 pair remain unproved.**

A revised cost model uses both old UPPER cases for its token slope and only
LOWER training for its offset. Its prediction is frozen before the untouched
LOWER heldout check: 84.476945 CPU seconds predicted versus 86.853720 measured,
**2.736527% error**, passing this new 30% component gate. The earlier failed
UPPER forecast remains failed. Full certificate generation, retained storage
and whole-proof feasibility still require validation; production GO is false.

Index: `results/text-lower-closure-index6-20261018.json`. The nine accepted
phases produce 698 interfaces; the enclosing job charges 253.203755 CPU seconds
plus the recorded 20-second controller allowance. Safe flags, zero postulates,
P1 and existing donor hashes are preserved. No native solver is run: two
complete authenticated scans read the protected existing LOWER wire unchanged.
AI assistance covered the generator, conditional composition and test harness.

The LOWER source/cache is now sealed; its current location and replay status
are in `results/text-lower-cache-current6-20261018.json`. Historical paths in
older entries below remain provenance, not instructions to recreate them.

The complete LOWER cache now contains 1,407 verified entries and 698 accepted
interfaces in the 118,617,551-byte archive referenced by that current-location
file. A joint replay through BOTH full archive views succeeds at the original
4,500 MiB heap setting: exit 0, 18.243222 CPU seconds, 2.083710 GiB RSS.
The earlier 2,800 MiB replay exhausts its heap and is retained and charged;
it does not invalidate the unchanged accepted interfaces. See
`results/lower-cache-archive-index6-20261018.json` and the accepted recovery
`results/lower-cache-replay-index6-20261018.json`.

Storage experiments leave all original archives unchanged. Six sampled decoded
interface payloads compress well, but neither default Zstandard levels with
the pinned Agda library nor a reversible frame-delta codec saves original
interface bytes: default reencoding differs, and payload-plus-delta is larger
in every sampled case. These routes are not deployed. See the three
`results/interface-codec-{probe,parameters,delta}-index6-20261018.json` indices.
The full storage/generation feasibility gate remains open.

## 2026-10-18 — Full UPPER cache sealed and replayed; physical headroom recovered

The complete live text UPPER cache is now in the 112,289,378-byte archive
`/mnt/data/othello-agda-desktop-artifacts-20261018/sealed-text-cache6-20261018/text-cache.zip`.
All 1,342 entries preserve their bytes, modes and nanosecond modification times.
The exact source identity and 664-interface pool were verified through the
read-only archive view before and after Agda replayed the accepted dense
10,000-row interface (exit 0, 9.138584 CPU seconds, 0.898422 GiB RSS). Only after
that successful replay and an independent archive hash check was the plaintext
`text-upper-probe6-20261018-fixed/check` removed. Future imports must mount the
archive and remap that historical donor path; use
`results/text-upper-cache-current6-20261018.json` and
`results/sealed-text-cache-closure-index6-20261018.json`.

The retired, unused full vector cache is separately preserved in a verified
116,011,771-byte ZIP (1,331 entries); see
`results/retired-vector-archive-index6-20261018.json`. 194 completed generated
logs are preserved byte for byte, with original metadata, in a 2,146,313-byte ZIP;
see `results/study-log-archive-index6-20261018.json`. Their former paths are
historical references, recoverable from the manifest. Original desktop runs,
NAMOR and P1 are unchanged. Physical archives count within the same 12 GiB cap;
virtual read-only views do not consume a second physical copy.

AI assistance covered the archive/replay harness and data-preserving cleanup.
These storage checks add zero game rows and do not complete the initial 6x6
mathematical objective. The earlier failed 30% forecast gate remains failed.

## 2026-10-18 — Complete UPPER state table; 20,000 rows and conditional full composition checked

Agda accepts a fixed text-backed table containing all 6,530,011 UPPER states,
32,651 lookup chunks and 654 groups. The original vector-backed data table
also checks, but the dense 10,000-row group exhausts its 4,500 MiB heap.
`DirectPackedText6`, `TextStateMap6` and `TextStateAssembly6` avoid constructing
all preceding packed states when a row is looked up. They reuse exactly the
same state-string literals and directed certificate bodies. The dense group
then passes: 67.110880 CPU seconds, 2.843330 GiB peak RSS. The ordinary early
group passes in 24.195657 CPU / 1.602947 GiB. Both use the SAME fixed full G:
groups 6 and 652, owners 60000..69999 and 6520000..6529999. Their 20,000 rows
can be combined on this map. Older sample maps and the vector-backed map are
separate; do not add their coverage to this map.

The exact 513-entry UPPER prefix resolver compatibility is CLOSED against
this full text-backed G (`Tests.TextUpperPacked6.Compatible.compatible`).
`TextCertifiedAssembly6` requires an actual Partial in the sole constructor
of Certified; ProvenMap likewise requires the full pointwise Proven function.
`Tests.ParametricFullUpper6.Assembly` keeps G symbolic while checking the
654-field composition and then instantiates the ACTUAL full text map.
Its conditional composition passes in 16.111608 CPU / 2.450172 GiB RSS;
the two already accepted groups are reused through Certified in 9.197493 CPU.
The earlier direct/concrete compositions remain failed/censored evidence;
no memory or disk limit was raised for these recoveries.

The remaining 652 UPPER certified fields are NOT supplied. LOWER still needs
its full map/row proofs and exact sparse-prefix resolver compatibility. The
conditional SAME-pair bridge from both complete maps remains available, but
no initial +4 guarantee or completed initial Problem2 inhabitant is claimed.
All 21 early literal prefix pairs remain conditional on the full-map proofs;
the 13 literal suffix pairs are unconditionally checked. INITIAL 6x6 +4 AND
THE SAME INITIAL OPTIMAL BLACK16–WHITE20 PAIR REMAIN UNPROVED.

The frozen 10,000-row CPU prediction was 87.371512 seconds versus measured
67.110880: error 30.189787%, ABOVE the strict 30% component gate. This gate
has NOT passed. Do not relax it retroactively. Calibrate with the measured
row mixes and test a NEW untouched case; archive/storage and LOWER full-map
costs also need validation before production GO. All raw/native data remain
untrusted; the kernel checks are the proof evidence.

Current full data and two game-row proofs:
`/mnt/data/othello-agda-desktop-artifacts-20261018/text-upper-probe6-20261018-fixed/check`.
Checked full conditional composition:
`/mnt/data/othello-agda-desktop-artifacts-20261018/text-parametric-assembly6-20261018/check`.
The latter has an accepted private checkpoint and source/interface hashes.
Receipt indices: `results/text-upper-closure-index6-20261018.json`,
`results/text-parametric-closure-index6-20261018.json`; final inventory is
`results/full-text-upper-final-audit6-20261018.json`. Current UPPER ZIP input
is `results/upper-wire-current6-20261018.json`; `packed_wire6.records` validates
the sealed container and every raw row/byte/hash while streaming it.

The single ledger preserves every failure, actual and controller allowance.
Original inline scope is now explicitly 1500 CPU seconds; cumulative usage
is 1300.850102. Total allocation remains 172800 CPU seconds, with no new total
grant. All core sources use `--safe --without-K --cubical-compatible`; zero
postulates and 23 tagged P1 hashes are preserved. Swap/core 0, aggregate RAM
12 GiB, retained physical study 12 GiB and ordinary root floor 80 GiB remain.
All external physical artifacts count, including both full-data layouts and
failed attempts. Original desktop runs and NAMOR remain untouched. No email
or publication. Codex assisted with source, formal proofs, extraction,
resource harnesses and documentation.

Next: free physical artifact headroom by verified archiving of the retired
vector dataset, which is already omitted from the current accepted donor set;
seal/validate a read-only view of the live text data cache before removing any
live plaintext. Preserve all metadata and receipts. Then validate independent
cost/storage cases, construct the full LOWER table/compatibility/closure,
and finish EVERY row group on both sides before applying the initial bridge.
Use bounded batches/imports to amortize the measured 8.5838 CPU full-map load.
Do not repeat the failed concrete-G654-field elaboration; use the accepted
parametric composition and opaque proof objects. Goal remains active.

## 2026-10-18 — UPPER sample and literal-prefix assembly checked; full maps OPEN

Safe Agda accepts 1,600 actual UPPER rows on ONE shared packed map, representing
333,011 states in 1,666 chunks. Training and heldout parts were frozen before
checking; the heldout aggregate CPU forecast error is 1.7593%. This validates
that sampled component, not the full workflow or production resource forecast.
The same earlier 10,000 LOWER rows are now retargeted to their 50 actual source
chunks; these are reused rows, not additional coverage.

`Othello.InlinePrefix6` reconstructs a literal-prefix guarantee from a checked
inline subtree, a compatible resolver and proofs of every cited global state.
Agda checks 21 such LOWER and 21 UPPER conditional guarantees for `p0`..`p20`.
The subtrees are extracted from EXISTING native wire bodies: no new search is
used for the prefixes. They contain 545 LOWER / 534 UPPER tokens, with 558 / 513
states in the respective sparse citation resolvers. Agda also accepts
`Tests.InlineLowerPrefixes6.Joint.problem2-from-complete-maps`, which combines
these conditional guarantees with the already checked literal suffix `p21`..`p33`
to construct the SAME initial optimal pair completing Black16–White20.

The Joint theorem STILL TAKES two fully proved global maps and two exact
resolver-compatibility proofs as arguments. Those arguments are NOT supplied.
The 21 early literal guarantee pairs remain unclosed; the unconditional suffix
still has 13 pairs. Initial6x6 +4 and Problem2 remain UNPROVED. The 1,600 UPPER,
10,000 LOWER, older 3,000 and 2,600 samples are different partial maps; DO NOT add
their coverage figures or treat conditional prefix functions as closed bounds.

The UPPER native wire was retained using the exact previously accepted native
binary and policy, with no new compilation. It has 6,530,011 rows / 470,365,910 bytes,
SHA256 `9ce6e5da5ae323b2b4d40b5096df960c8153fe548566e6cc466232824f5593bb`.
It remains untrusted data; native success supplies no Agda premise. The protected
existing LOWER wire has 6,873,047 rows / 88,689,949 tokens and can supply the LOWER
formalization without rerunning its native solver. Original desktop runs and
NAMOR are unchanged.

Receipt indices: `results/range-upper-closure-index6-20261018.json`,
`results/upper-kernel-closure-index6-20261018.json`,
`results/prefix-inline-closure-index6-20261018.json`,
`results/lower-prefix-inline-closure-index6-20261018.json`, and
`results/upper-wire-export-closure-index6-20261018.json`.
All checks preserve `--safe --without-K --cubical-compatible`, zero postulates
and 23 tagged P1 files. CPU charges and controller allowances are preserved in
the single desktop ledger; the inline cumulative cap is explicitly 900 CPU
seconds (used 664.214418), total allocation remains 172800. Root 80 GiB, physical
retained study 12 GiB (INCLUDING every external output), RAM 12 GiB, swap/core 0
remain in force. Codex assisted with the source, proofs, extraction, harnesses,
archive handling and documentation. No publication or email was sent.

The fresh UPPER wire is now stored losslessly in a ZIP/Zstandard93 container:
`/mnt/data/othello-agda-desktop-artifacts-20261018/upper-wire-staged6-20261018/initial-upper.wire.zip`,
entry `initial-upper.wire`, 139962081 bytes, container SHA256
`9fd4d48f9dd348c668fd6b5f43451032b0d17a21cfe8748b05c1c92484bbd730`.
Independent decompression verifies all 470365910 original bytes, 6530011 rows
and the original raw SHA256. The fresh materialized raw path is intentionally
removed; the current input reference is `results/upper-wire-current6-20261018.json`.
Use a streaming ZIP reader for further extraction; do not assume the old raw
path still exists. Protected historical LOWER wire and all original runs remain
untouched. The first whole-copy attempt hit its 80 MiB own-output guard
(27.085180 CPU); its partial prefix was verified as an exact duplicate of the
retained raw input before removal. All failure receipts remain. A journalled
32MiB-tail conversion then passes in 99.354321 charged CPU. Each tail copy and
its recovery journal were durable before truncation; the final consolidated
archive was verified before duplicate parts and the empty raw prefix were
removed. The original global-native 5650 cumulative family now includes
2909.346690 CPU seconds, including ALL old actuals and controller allowances.

Next: add bounded streaming ZIP input; validate compact full-map
storage/import and 10,000-row UPPER grouping with a heldout full-workflow forecast;
then close both full maps, exact sparse resolver compatibility, apply Joint,
and retain the final private package. Full production GO is still FALSE.

## 2026-10-18T13:53:35.494366+00:00 —10000 consecutive LOWER rows checked; shared state chunks and read-only archive view accepted

Safe Agda checks `Tests.ConsecutiveGlobalBatch6.Closed.partial`:10000 real,
consecutive LOWER rows (old wire parts342..391, numeric owners68400..78399)
over ONE common encoded state map. Ownership and citation lookup use G
directly. This is a Partial theorem: earlier-row winning witnesses remain
inputs to each Step. The data map contains62800 states in314 lookup vectors
of200, grouped50 vectors per source module (7 modules). Its52800 other data
rows have no complete checked row coverage here. Absent keys denote an
all-white terminal packed state, whose LOWER `Proven` leaf witness is checked
in the accepted Root interface. That terminal fallback is an endgame anchor;
no initial-state guarantee follows without full row coverage and root ownership.
The new sample map, the earlier3000-row packed map and the2600-row state/body
map remain distinct with overlapping samples. DO NOT add their row counts.

`Othello.GlobalPackedRows6` first removes local state/resolver payload from
parts, reconstructing each row directly from G. Its generic theorem and the
same1000-row instance check (4.272800 CPU,0.735065 GiB RSS). The larger10000-row
Fin-tabulated instance is CPU-censored at95.078521 seconds and has NO Closed
interface (outer122.771041). All10 completed decoder/data/Body/Root interfaces
are preserved; the terminal fallback proof is included in Root. The new
`Othello.ConsecutivePackedRows6` advances owners directly by `suc`, with a
safe symbolic proof connecting this checker to Step/Partial. Using the EXACT
same state and certificate sources, its10000-row instance passes in11.779759
nested CPU /14.340577 wall seconds,0.988476 GiB peak RSS. The profile attributes
10.514 seconds to Closed. Generic checker CPU1.291005; complete outer CPU
18.136957. No extra native solver or wire scan runs in this recovery. The two
runs have different cache states; no matched speedup factor is claimed.

The original preparation authenticates the entire existing498606513-byte LOWER
wire in both streaming passes, preserving its SHA256 and row count. It uses
12.812167 CPU seconds, produces53074 certificate tokens and a1329257-byte
sample. The extractor retains its ordinary16-part default and now accepts an
EXPLICIT max-selected-parts argument bounded by64; this test freezes50 parts,
8MiB sample,160000 tokens/references and at most392 state chunks before use.
No native count/export is relabeled as a proof. This old LOWER extraction epoch
is not the new native-policy or UPPER validation. Full-workflow forecasts,
production gates and complete initial bounds remain OPEN.

Closure index: `results/consecutive-global-closure-index6-20261018.json`.
The accepted checkpoint includes12 interfaces: two new row/checker interfaces
and10 exact accepted donor interfaces. Its accepted-data source collection
OMITS the unaccepted Fin-tabulation Closed source. Source, interface, binary,
flag, cache, CPU/memory and helper provenance are preserved. Package bytes
2419350, SHA256
`c74c9b3ea51cc25be112e39b966eb1dc6ac0084a4367fe39e7253c0edf26e334`.
`measured-footprint.json` separates the single decoder/checker interfaces,
shared state groups, Body and Closed; these measurements alone are not a
validated complete-layout prediction. The finished project private package
remains OPEN.

A separate read-only ZIP-view pilot also passes. It compiles the local
`study_archive_fs6.c` against the installed libzip/FUSE libraries, archives an
accepted check tree, then verifies all39 entries /692406 bytes, exact source
and interface hashes, modes and nanosecond timestamps before and after Agda.
Writes are denied. Agda loads its existing Holdout interface from the view
successfully (1.155230 CPU). The view is unmounted, its process exits0 and
original sources/interfaces are retained. ZIP bytes503578; outer11.343776.
Index: `results/global-archive-closure-index6-20261018.json`. This provides a
verified data-preserving read-only archive mechanism; complete-layout storage
and final import memory still require measured validation. Physical archives,
originals and every other external output count inside the SAME12GiB cap.

The ORIGINAL inline calibration family totals524.202111/600
CPU seconds, with all earlier failures, controls and the200→600 explicit cap
extension preserved. No reset or total CPU grant increase was made. Receipts:
`results/global-archive-admission6-20261018.json`,
`results/compact-global-admission6-20261018.json` and
`results/consecutive-global-admission6-20261018.json`.
Every23 P1 source and accepted donor cache is unchanged. RAM12GiB total,
swap/core0, root free floor80GiB, study artifacts12GiB, protected old desktop
runs and NAMOR remain intact. No Othello service, archive mount or CPU
reservation remains live. Total charged104458.261341,
withheld2713.956401, available65627.782258;
kernel available41287.004046.
Global allocation is still172800 CPU seconds (48h).

The13 literal guarantee pairs p21..p33 and their SAME-pair suffix ending
Black16–White20 remain checked. The21 earlier literal pairs p0..p20, the
initial standard6x6 +4 theorem and the SAME initial optimal pair remain OPEN.
Next production-relevant obligations include UPPER/new-policy row validation,
complete compact data/import/storage scaling, and assembling row ranges on the
actual global state table before the initial root and prefix transport proofs.
Native goal ACTIVE. AI assistance is disclosed; no publication or email.

## 2026-10-18T13:17:28.735003+00:00 —3000 sampled LOWER Steps assembled on one encoded map; initial theorem OPEN

Safe Agda now checks `Tests.PackedCommonRows6.Closed.partial`:3000 sampled
LOWER rows on ONE common packed-state map. Exact ownership of each of the
three1000-row vectors and compatibility of all local citation lookups with
this map are discharged. The common map also stores3385 distinct referenced
keys outside these owned vectors; their row proofs remain OPEN. This is a
Partial theorem, with earlier-row winning guarantees still required by each
Step. No `complete` or `global-proven` call is made. The fallback in this
sample is the initial packed state and has NO proved winning guarantee here;
full completion requires a checked terminal fallback or its explicit proof.
The old2600-row common state/body-map Partial is preserved. These are different
maps, with overlapping samples: DO NOT add the two coverage figures.

`Othello.PackedVectors6` proves exact packing/decoding and symbolic ownership.
`Othello.PackedRowPartial6` keeps base/Fin arithmetic symbolic inside a generic
row-to-Partial boundary. Its instantiated3000-row check passes in10.602540
nested CPU seconds and0.931446 GiB peak RSS. Complete outer CPU is17.247309.
Five interfaces, exact source/helper/donor hashes, checker binary/flags,
cache state and all phase receipts are preserved. All23 P1 files and accepted
donor caches are unchanged. Closure index:
`results/packed-common-rows-closure-index6-20261018.json`.
Accepted conditional checkpoint bytes1376255, SHA256
`d697927e252b7b353d6889f8918882f6d2a3d866200ea5d6a2960b2f775c59c1`. This package depends on pinned accepted donor
packages; the finished whole-project private submission package is still OPEN.

Failures are retained and charged: missing `Game.NatMapCheck` in the isolated
source path (4.300193 outer CPU; generic vector lemma accepted), then1400MiB
heap exhaustion (11.185384) and2800MiB heap exhaustion (19.585977). In both heap
failures the common Data interface is emitted, but Closed is NOT accepted.
After those two censored explicit-ownership attempts, the symbolic Partial
boundary succeeds under a4GiB hard/no-swap/core0 cgroup, using less than1GiB
checker RSS. This supports the large-base/unknown-Fin diagnosis; it is not a
controlled proof that arithmetic was the sole source of all allocation.
No further heap-only retry or old retired wrapper/search retry is selected.

The preceding1000-row grouping calibration also passes all three samples:
2000 training rows and1000 heldout rows, from the old accepted LOWER wire.
The forecast is frozen before holdout; relative CPU error21.253486% passes
the predeclared30% component gate. Across3000 rows, the data/body/checker
interfaces total333600 bytes, and corresponding sources343470 bytes.
These samples have different certificate mixes from the earlier200-row pilot;
no matched whole-workflow footprint or speedup is inferred. The LOWER-only
source/interface scenarios still exceed current artifact headroom; UPPER,
new native extraction policy, full imports/assembly and complete storage
remain unvalidated. Production GO is FALSE. Index:
`results/big-rows-closure-index6-20261018.json`.
The first preparation attempt failed at integer/string state-key normalization
before Agda (17.151103 CPU); one fresh recovery reuses the SHA-verified sampled
JSON without rescanning the wire (13.426676 CPU). Both are preserved.

Before these tests the ORIGINAL inline calibration cap was explicitly extended
200→600 under the user's recorded compute authorization; no past consumption
was reset and no global CPU grant was added. Its current cumulative total is
331.950337/600 CPU seconds, including every failed
attempt and controller allowance. Receipts:
`results/inline-calibration-cap-extension6-20261018.json` and the packed-common
admission/recovery/memory/symbolic admission records. Every physical output,
including failed runs on `/mnt/data` and relocated archives, is included in
the SAME12GiB retained-study cap via
`results/study6-external-artifacts-20261018.json`. Root floor80GiB, total
study RAM12GiB, swap/core0 and protected old desktop runs/NAMOR remain intact.

The13 literal guarantee pairs p21..p33 and the checked SAME-pair suffix to
Black16–White20 are preserved. The conditional initial bridge still needs
both guarantees at p0..p20. Initial standard6x6 +4, the SAME initial optimal
Black16–White20 pair and the finished private package remain OPEN.
No Othello service or CPU reservation remains live. Total charged
104306.009567, withheld2673.956401, available
65820.034032; kernel available
41439.255820 CPU seconds.
Total allocation remains172800 CPU seconds (48h). Native goal stays ACTIVE.
AI assistance is disclosed. No publication or email.

## 2026-10-18T12:50:22.940466+00:00 — Budget redistribution applied;13 literal prefix-state pairs and conditional initial bridge checked

The user's explicit approval (reply12:32:55UTC: "sisi puoi anche alzare i limit
senza problemi") was forwarded into this canonical thread. Exactly32000
unused native CPU seconds were transferred to Agda kernel. Effective category
allocations are native44602, kernel96800, compiled9798, assembly21600, still
172800 total CPU seconds (48 hours). NO total increase is applied yet. Necessary
future compute increases are authorized only with finite, proportionate caps
recorded before use, preserving every past consumption/withholding and all
RAM/disk/stability limits. No purchases or paid services are authorized.
Receipt: `results/completion6-budget-authorization-20261018.json`.
`AGENTS.md` and the original reallocation proposal now reflect application.

Safe Agda checks both exact+4 Guarantees for literal states21..33 (13 of the
34 trace states). `Othello.SpliceSuffix21` assembles ONE pair from p21 along
the exact suffix to p33. The checked p33 disc counts are Black16–White20.
The checked `problem2-from-first21` returns the full initial Problem2 ONLY
when supplied both required guarantees at every literal state p0..p20. Those
21 pairs remain OPEN. This is not an initial value theorem. Canonical-map
ownership/transport for the remaining initial-prefix states still needs proof.
Distinct common-map Partial coverage stays2600 LOWER rows.

Receipts: `results/splice-suffix21-closure-index6-20261018.json` points to the
physical closure on `/mnt/data`. The conditional package includes15 accepted
interfaces and their exact sources (all13 state modules plus two suffix
assemblies), omitting the unchecked State20/State20Boolean sources from the
accepted source collection. Package bytes2401299, SHA256
`9462d13fd965f9a1e893ca2e2aa7228c970e60a579034fb122b6779eabdc4002`. Original path-splice170 scope totals166.409820
including all controls/failures. State20's certificate-carrying Search hits
15CPU (outer30.566406 for the multi-state attempt, five earlier state pairs
accepted). The ONE Boolean recovery hits20CPU and produces no interface
(outer24.891451); post-terminal donor/P1 audit passes. Final suffix21 bridge
passes in0.563050 module CPU /3.920035 outer CPU. No further same State20
search retry is selected, and this path-splice170 scope is retired.

All23 tagged P1 sources and all accepted donor caches remain unchanged.
The inline200 comparison scope is also retired at199.053695. Its private-
imports variant increased interface bytes3.322010% and is rejected. Earlier
text-map gains remain accepted, but do not prove complete workflow/storage
feasibility. The next production-relevant representation question is whether
larger row batches can fit full source/interfaces within the unchanged study
artifact cap; no full-production GO has been inferred from component models.

To preserve root free-space headroom, six current canonical probe archives
were copied byte-identically to the data filesystem, hash-verified, and their
original paths replaced atomically by symlinks. No source, interface, receipt,
old desktop run or NAMOR file was modified. Root released14508032 bytes.
The physical archive directory is explicitly included in the SAME12GiB study
cap via `results/study6-external-artifacts-20261018.json`; future storage
inventories MUST include every registry root, not old glob-only helpers.
Receipt: `results/current-probe-archive-relocation6-20261018.json`.

No Othello job or CPU reservation remains live. Total charged
104223.112925, withheld2623.956401, available
65952.930674; kernel available
41522.152462 CPU seconds. RAM12GiB,
swap/core0, root floor80GiB and retained-study cap12GiB remain unchanged.
The complete initial6x6+4 theorem, SAME initial optimal Black16–White20 pair
and completed private submission package remain OPEN. Native goal ACTIVE.
AI assistance is disclosed; no publication or email.

## 2026-10-18T12:34:01.882087+00:00 — Private imports checked and rejected; original inline200 scope retired

Safe Agda accepts the exact same200-row Step theorem with private imports.
The interface grows22667→23420 bytes (+3.322010%); no size improvement or
production benefit is claimed. No semantic checker or state data changes.
Receipt `/mnt/data/othello-agda-desktop-artifacts-20261018/private-inline-probe6-20261018/closure.json`
records4.922759 outer CPU, one interface and zero new distinct rows. The
ORIGINAL inline200 family totals199.053695 with all prior actuals/allowances.
This calibration family is now retired, with no cap reset or further retry.
All accepted donors and23 P1 files are unchanged; external physical bytes
remain included in the12GiB study cap. A source-only Luna/high leaf wrote
this variant; parent checking and reconciliation are recorded separately.

A separate continuation of the ORIGINAL path-splice170 scope is checking
closed lower/upper Guarantees at the exact literal states26..33, using the
existing safe Game.Search and Soundness implementation. The planned suffix
pair covers only that literal endgame, not initial6x6. Its source is pending
Agda acceptance; no closed bound is inferred from generated source alone.
The reserve is70 kernel seconds, outer45, phase12, hard RAM2GiB/heap1400MiB,
swap/core0, with10 assembly control allowance; original scope envelope is
159.788702/170. A source-only Sol/medium leaf wrote the nine suffix files.
Initial +4, SAME initial optimal Black16–White20 pair, common-map completion
and the completed private package remain OPEN. Distinct common-map Partial
stays2600 LOWER rows. Category allocations are unchanged; reallocation
approval remains pending. AI assistance is disclosed; no publication/email.

## 2026-10-18T12:26:35.495664+00:00 — Text-map interfaces checked; CPU proposal pending; initial theorem OPEN

The compact local-map representation now passes the SAME800 training and600
held-out LOWER rows through the unchanged sound `SharedInlineSteps6` checker.
The total data decoder `PackedMapText6` asserts no global compatibility;
compatibility and ownership remain explicit hypotheses of these Step exports.
No new distinct common-map rows are added. Across the seven parts, state
interfaces shrink1655357→242862 bytes; Checked interfaces289264→135197.
Combined reduction versus the preceding shared-instance route is80.558731%.
Training data/body/row cost is1.558 module CPU seconds, including four explicit
1ms allowances for omitted tiny State modules. Held-out relative error is
2.334721%, passing the predeclared30% component gate. Its analogous three
omitted State-module allowances are explicit too. This model covers local
map source and row computation only. Global map/import/assembly/storage costs
are excluded; UPPER and the new extraction-policy epoch remain unvalidated.
The combined count scenario is27894.907573 CPU seconds; production GO is false.

All preparation/checking failures are preserved: the character marker65 pattern
was rejected before any interface (3.711723 outer CPU); subtracting65 yields
small patterns0,1,17. The repaired generic module and800-row Training pass,
but the profile collector wrongly expected sub-millisecond State modules to
be printed (5.385238 outer CPU); Holdout had not started. Its first isolated
launch then failed in preexec because inner12-CPU exceeded inherited outer10
hard CPU limit (1.690190 outer, NO Agda process). One fresh heldout launch
uses7 phase/9 outer limits and succeeds (6.257279 outer). The correct uniquely
named heldout log is used by the frozen closure builder. No semantic checker
failure is silently converted to acceptance. The ORIGINAL inline200 family
now totals193.130936, including all earlier failures and controller allowances;
no reset or additional retry of these variants is selected.

The ordinary root80GiB floor prevented a conservative12MiB output reservation.
No floor exception was taken. Fresh heldout artifacts are on `/mnt/data` at
`/mnt/data/othello-agda-desktop-artifacts-20261018/text-map-holdout6-20261018-fixed`.
The external output and its failed predecessor are explicitly counted by
physical allocated bytes in the SAME12GiB retained-study cap, alongside all
prior study data. Root metadata retains a1MiB reserve above80GiB. Future
storage checks must include EVERY root listed in
`results/study6-external-artifacts-20261018.json`, even though those paths are
outside the repository; do not rely on old glob-only storage helpers alone.
No source/cache is taken from laptop, no old desktop run or NAMOR is changed.
Closure index: `results/text-map-holdout6-20261018-closure-index.json`.
Accepted conditional package1504444 bytes, SHA256 `025796ecbce2588523fb547e69ee68b1fdc19cfaf109574627712cfdfa88fe40`.
It includes the exact accepted generic/800-row training sources/interfaces,
new600-row heldout sources/interfaces, helper snapshots and provenance.

There are no live Othello jobs or reservations at closure. Ledger total172800,
charged104151.569048, withheld2601.956401,
available66046.474551; kernel available
9593.696339 seconds. Allocations
are UNCHANGED. User response to the32000 native→kernel reallocation proposal
is still pending; elapsed time is not approval. The proposal does not increase
total CPU or override RAM/swap/disk/artifact/prior-stage limits, and does not
itself establish production feasibility. No automatic production is selected.

Distinct common-map coverage remains2600 LOWER rows. Initial +4, SAME optimal
pair Black16–White20, all34 line ownership cuts/alignment and a completed
private package remain OPEN. All23 tagged P1 files remain unchanged. The
native goal stays ACTIVE. AI assistance is disclosed. No publication/email.

## 2026-10-18T12:12:39.404359+00:00 — Complete native UPPER counts; shared checker accepted; mathematical objective OPEN

Safe Agda accepts `Othello.SharedInlineSteps6` and all seven old-row parts:
1400 repeated LOWER rows,10 new interfaces, zero new distinct rows.
The fixed checker is shared once; each part exports its Step result without
instantiating checker/assembly modules. The exact comparable part interfaces
shrink1388334→289264 bytes (79.164668%); shared interface891722 bytes.
Training9055 tokens costs1.505 module CPU seconds including donor body cost,
versus1.862 before (19.172932% reduction). Held-out7155 tokens cost1.205,
with1.310571% prospective error, passing the30% component gate. This is
LOWER old-epoch component evidence, not a validated UPPER or whole-workflow
forecast. State/resolver data, imports, assembly and retained-artifact costs
remain outside that row model. The current combined count scenario is
26945.979395 CPU seconds for this component only; production GO remains false.
Receipt: `results/shared-inline-scaling6-20261018/closure.json`.
Outer CPU10.976315; ORIGINAL inline200 family166.086506 including all earlier
failures and control allowances. A Python pragma-format preparation error
occurred before any reservation/checker; its sources/receipt are preserved
and its control cost is covered by the same new10 assembly allowance.
A source-only Sol/medium leaf wrote the shared module/emitter; the parent
owned checking, acceptance and accounting. No Boolean semantics were replaced.

The contiguous numeric-owner recovery succeeds only after its explicit type
uses the SAME numeric owner expression, avoiding alias conversion. Its200
rows are old rows; matched module CPU0.851 versus0.875 shows no material gain.
Both heap failures and the duplicate-module preparation failure are retained.
That original inline scope was145.110191 before the shared-instance check.
Receipt: `results/contiguous-explicit-rows-probe6-20261018-fixed/closure.json`.

The generic `StepFromNatAssembly6` bridge checks, but BOTH closed2600-row
Partial-to-Step wrappers are CPU-censored with no interface. Original Step100
scope is92.946357, including retry26.104812; no further same-wrapper retry.
The previous2600-row common-map LOWER Partial remains valid. The concrete
Step export is not accepted. Receipt:
`results/step-existing-partial6-20261018-fixed/closure.json`.

Native UPPER counting completes:61356859 selected DAG states,6530011 wire
records,80755243 tokens and32651 planned200-row parts. Together with LOWER:
162123484 tokens and64685 parts. This is untrusted extraction guidance only;
no wire/source is exported or retained and no proof row follows. Native UPPER
outer CPU726.486829; original global-reuse5650 scope1866.560854 including
new300 controller allowance. Exact accepted binary/warm TT and P1 are unchanged.
The native `line_maintained:false` field is a hardcoded legacy output, not a
trace audit; source move pins remain active, while all34 canonical ownership
cuts/alignment and their Agda guarantees remain OPEN. Receipt:
`results/global-upper-layout6-20261018/closure.json`.

At this closure no Othello job/reservation is active. Ledger: total172800,
charged104134.524618, withheld2591.956401,
available66073.518981; kernel available
9610.740769 CPU seconds. Category
allocations are UNCHANGED. Proposal
`results/budget-reallocation-proposal6-20261018.json` requests user approval
for32000 unused native seconds→kernel, without increasing total172800 or any
other limit; it is NOT APPLIED. No response is inferred from elapsed time.
RAM12GiB, swap/core0, root free floor80GiB and retained-study cap12GiB remain.
Protected old desktop runs and NAMOR are untouched. The migration hold has
already been revoked; no laptop coordinator is restarted.

Distinct common-map Partial remains2600 LOWER rows. Initial standard6x6 +4,
SAME optimal pair Black16–White20, all initial proven bounds and completed
private package remain OPEN. Tagged23 P1 files are unchanged. The native goal
remains ACTIVE. AI assistance is disclosed; no publication or email.

## 2026-10-18T11:15:32.877363+00:00 — Arithmetic Boolean comparison rejects that route; contiguous owners in recovery

The isolated primitive-arithmetic Boolean checker and both matched200-row
assertions complete safely. Baseline module CPU is0.852 seconds; the arithmetic
working-state variant is2.817, approximately3.306338 times baseline. Thus the
variant is rejected for performance, and no further game-refinement proof
work is selected from this screen. It supplies Boolean facts only: semantic
soundness, TreeOK exports and new common-map coverage are explicitly zero.
The same states, directed bodies and resolver codes are used on both sides.

The first launch changed CLI warning options, causing a preserved Prelude
interface to need reconstruction. The read-only donor guard rejected that
write. Its3.468327 CPU receipt is retained; donor pools remain unchanged.
One fresh launch restores the prior CLI options and passes all three phases.
Receipt `results/primitive-arithmetic-boolean-probe6-20261018-fixed/closure.json`
records22.980949 outer CPU seconds; the entire ORIGINAL arithmetic200 scope
now totals152.276371 including all earlier actuals and20+10 control allowances.
The923557-byte Boolean checkpoint has SHA256
`c528785c145a9d193f84c6e5e33b826c61c7c5a8d4fabd31fc8db10f336cbad9`. A source-only Sol/medium leaf wrote the
Boolean evaluator/emitter; dispatch, acceptance and reconciliation are owned
by the coordinator. No native solver executes.

A separate continuation of the original INLINE calibration200 scope tests
contiguous numeric row owners, retaining the same generic local checker.
The first generic soundness module and baseline pass, but its concrete
variant exhausts2GiB heap (exit251) with no interface. The failed outer
25.955199 CPU seconds and all source/interface evidence remain preserved.
One correction replaces successive `suc` constructors by built-in numeric
addition and adjusts the proved index shift. This is a hypothesis about
representation cost, not a measured gain. The corrected generic/200-row
checks are in progress under unchanged3GiB hard RAM,2GiB heap,15-CPU phase
caps,40 outer cap and55 reservation. Its predeclared combined envelope is
158.912943/200, preserving67.957744 prior inline calibration consumption
and the new10 control allowance. No source cache or old run is overwritten.

The full6x6 value, SAME optimal Black16–White20 pair and completed package
remain OPEN. Distinct common-map Partial stays2600 LOWER rows. All23 P1
files are unchanged in the completed screen; AI assistance is disclosed.
No publication or email occurs.

## 2026-10-18T11:01:22.274570+00:00 — Arithmetic recovery censored; all jobs reconciled, objective OPEN

Safe Agda checks the new `PrimitiveArithmeticState6` module, including
arithmetic unpack-encode and numeric-pick decoding proofs, in0.789292 CPU
seconds. The next `PrimitiveArithmeticGame6` phase hits its20-CPU guard:
20.031467 measured CPU seconds, exit137, no interface. The row-checker and
matched200-row performance phases are never reached. This supplies neither
a measured speedup nor new TreeOK/common-map coverage. The failed game
source remains experimental and is excluded from completed proof claims.
There is no further retry of this same game check selected.

Receipt `results/primitive-arithmetic-probe6-20261018-fixed/closure.json`
records the recovery's32.494615 outer CPU seconds and original combined
115.827095/200 scope, including58.034395 prior arithmetic actuals, the5.298085
failed source preparation and the single20 allowance. Exact failed sources,
helpers, phase receipts and the one partial interface remain preserved.
All donor pools, checked source hashes and23 tagged P1 files are unchanged.

No Othello job or CPU reservation remains active at this closure. Total CPU
charged is103257.860313, withheld2251.956401, available
67290.183286 within the unchanged172800 total. Category allocations are
unchanged; kernel availability is9760.918245 seconds. The accepted
InlineSteps old-row LOWER component scenario remains16731.934262 seconds,
not a complete workflow or an impossibility theorem. A new proof-production
run is therefore not selected on this evidence. The native degree-weighted
fixture also failed its predeclared improvement gate; no initial run follows.

Common-map Partial coverage remains2600 distinct LOWER rows. Initial +4,
SAME optimal Black16–White20 pair and completed private package remain OPEN.
The native goal remains active; this closure is not mathematical completion.
AI assistance is disclosed, with no publication or email.

## 2026-10-18T10:59:47.568725+00:00 — Sharing-weighted fixture closed; arithmetic decoder recovery in progress

The static candidate-indegree policy completes its two native fixtures.
LOWER changes3698→3680 retained DAG nodes and3929→3916 wire tokens, a0.330873%
token reduction. UPPER remains28 nodes/29tokens. Actual unweighted forcing
trees are recomputed after the heuristic pass. The predeclared20% fixture
gate fails, so neither initial-board direction is dispatched. This is
untrusted extraction guidance only. Receipt
`results/degree-reuse-layout6-20261018/closure.json` records the unchanged
original5650 family cap and840.074025 combined CPU seconds, including
all earlier global-reuse actuals/control allowances and the new15 allowance.
No graph/wire/source export or new proof row is claimed.

A bounded continuation of the original erased-arithmetic200-CPU scope now
compares primitive arithmetic cell reads with the large row-code pattern
table on the SAME200 existing selection rows. It copies the entire safe
state/game/checker proofs; numerical capture updates retain their checked
canonical witness. The first source check failed because the true branch
needed the new unpack-encode rewrite after its with abstraction. Its5.298085
outer CPU seconds and exact failed source/helper receipts are preserved.
One fresh recovery has55 kernel reservation/35 outer CPU cap,3GiB hard RAM,
swap/core0, within58.034395 prior actual+failure+one20 allowance+55≤200.
The repaired primitive state proof passes; game/row equivalence and matched
performance remain PENDING. No speedup, new row coverage or initial theorem
is inferred before those receipts. No unsafe irrelevance flags are enabled.

Initial +4, SAME optimal Black16–White20 pair and completed private package
remain OPEN; common-map Partial stays2600 distinct LOWER rows. AI assistance
is disclosed, and no publication or email occurs.

## 2026-10-18T10:51:56.243812+00:00 — Historical-query initial LOWER censored; objective OPEN

The historical-cost memo recovery reaches its native1450 CPU limit with an
incomplete initial LOWER graph. Its prefix contains3,573,142 visited states;
this is explicitly NOT the complete graph, wire or layout. The native report
marks `complete=false`, `oracle_aborted=true`, `layout_censored=true` and
`layout_stop_reason=incomplete-native-graph`. Wire/layout counts are zero.
The native warm TT and guarded provenance files remain unchanged. Root solver
validation is untrusted instrumentation and supplies no Agda theorem.

Terminal outer receipt is1452.728396 CPU seconds, exit1, accepted=false.
The assertion failure records the native censoring; it is not a checker pass.
Build/fixture/lower actuals total1454.620119. Including1427.460859 prior
query-family actuals and the existing20+114+400 control allowances, the
family closes at3416.080978/5650. Systemd reports1593.376601 CPU seconds for
the lower group,140.648205 above its wait4 receipt; this difference is covered
by the already withheld400 allowance, without a second charge. No UPPER,
restart, wire export or proof production is selected for this method.
Receipt: `results/historical-query-layout6-20261018/closure.json`.

A source-only sharing-weighted continuation of the earlier global-reuse
family is compiled for its small fixtures. It weights a candidate subtree
by static candidate indegree, preserves existing line pins, makes no new
solver queries during postprocessing, and recomputes actual unweighted tree
counts afterward. It reuses existing graph arrays. The original5650 family
cap and824.098 prior combined consumption remain fixed. Only compiled18,
fixture100 and control15 are allocated; initial-board dispatch is disabled
pending the predeclared20% fixture LOWER token-reduction gate. This source
is untrusted instrumentation and is not accepted performance/proof evidence.

All proof obligations remain as previously recorded:2600 distinct common-map
LOWER rows, initial LOWER/UPPER and SAME optimal16–20 pair OPEN. No publication
or email; AI assistance is disclosed.

## 2026-10-18T10:47:59.760273+00:00 — Generic row-to-step boundary accepted; objective OPEN

Safe Agda accepts `Othello.InlineSteps6`, moving the certificate-indexed
TreeOK intermediate into one generic theorem over arbitrary row data. Concrete
row modules now export encoded winning steps directly. Training uses the same
800 accepted rows, then freezes its forecast before the same600 held-out rows.
The10 new interfaces repeat existing facts: no new distinct common-map rows.
All donor source/interface pools and23 P1 files remain unchanged.

Training body-source-plus-row CPU is1.862 for9055 tokens, including the
previously measured donor TextBodies source allowance. The component slope is
0.000205632247377 CPU seconds/token; held-out cost is1.496,
predicted1.471298730, relative error1.651154%, within30%. The generic theorem
checks in0.146 module CPU seconds (1.084507 full phase). State/resolver source
costs remain separate. This modest observed change supplies no whole-workflow
forecast or production gate. Applied as an OLD-ROW planning scenario to the
new global-reuse81,368,241 tokens, LOWER alone is16731.934262 CPU seconds,
above the remaining9798.710946 kernel seconds before assembly/UPPER.

Receipt `results/inline-boundary-scaling6-20261018/closure.json`: outer
15.794304 CPU seconds, three-calibration combined scope67.957744/200 including
one20 assembly allowance. Archive is3883864 bytes, SHA256
`055bedd9e466723b08b1077fdcef9a7c0edfed1c55a859e23732462a344795ab`. The historical-query initial LOWER is still
in progress at its predeclared caps. Initial +4, SAME optimal Black16–White20
pair and completed private package remain OPEN; Partial coverage stays2600
distinct LOWER rows. AI assistance is disclosed; no publication or email.

## 2026-10-18T10:44:45.216934+00:00 — Colour/bound reuse scout closed; objective OPEN

A read-only Astra assessment identified colour-and-turn transport with actual
proved score envelopes as a possible mixed-bound reuse rule. It remains
unformalized. A bounded native scout compares complete selected-policy graphs
on four suffixes of the prescribed16–20 trace, preserving every suffix root.
At plies20/18/16/14 the combined graphs contain718/3466/7401/49038 nodes.
The largest case matches129 colour pairs and retains101 cross citations, but
removes only26 nodes (0.0530201%). No initial-board, token or Agda-cost forecast
follows. This does not justify large new colour-transport formalization.

Receipt `results/cross-bound-pinned-screen6-20261018-fixed/closure.json`
accepts the SCREEN ONLY, not a proof: build0.783284 CPU seconds, native7.788965,
combined24.316393/100 including the original scout, both failed preparations/
collections and the shared15 assembly allowance. The first deeper collection
failed because frontier mode disabled existing line pins. The correction
changes only that guard; its first preparation assertion then failed on a
non-unique replacement substring, and a mistakenly dispatched build failed
its precondition. All failures remain preserved, charged and excluded from
accepted evidence. The anchored correction completes all four cases; all
required suffix roots and cycle checks pass. These are untrusted native data.

The historical-query initial LOWER remains in progress under its previously
recorded1450 native/1550 outer CPU caps and original5650 family scope.
Kernel availability is9814.505250 seconds; no category
reassignment or budget grant occurs. Distinct common-map Partial coverage
remains2600 LOWER rows. Initial +4, SAME optimal Black16–White20 pair and
completed private package remain OPEN. AI assistance is disclosed; no email
or publication.

## 18 October 2026, 10:25 UTC — Full LOWER counts and fresh component models; objective OPEN

The untrusted global-reuse initial LOWER census completes in754.207246 outer
CPU seconds. It selects61,791,767 of67,468,513 original graph states and emits
COUNTS ONLY:6,406,773 records,81,368,241 tokens,32,034 parts, maximum1476 imported
citations per part. Original and postprocessed counts are distinct; every
postprocessed node/edge/tree-count invariant passes. This is about8.3% fewer
tokens than the old88,689,949-token wire. No new wire or Agda source is retained.
`results/global-reuse-layout6-20261018/closure.json` records the completed LOWER
and deferred UPPER. Its combined scope, including corrected control allowance,
is824.098/5650 CPU seconds. All34 trace-state ownership cuts remain OPEN.

Fresh literal and compact component calibrations use800 training rows and600
held-out rows, excluding optimization-selection part33154. Training forecasts
are frozen before checking the holdout. Safe Agda also checks conditional
encoded Step exports. Literal source-body plus row cost is0.000378575373 CPU
seconds/token (held-out error4.589405%); Unicode compact is0.000219657648
(error1.587322%). Both pass the30% COMPONENT tolerance. Literal-body source
checking is included in the former, avoiding the misleading comparison with
row-module timing alone. State/resolver source costs are reported separately;
complete map compatibility, imports/assembly and retained artifacts are not
validated by these component models.

The compact LOWER scenario for the new global-reuse counts is17,873.156416 CPU
seconds, exceeding the remaining9814.505250 kernel seconds before UPPER or
assembly. This is a planning scenario using the old-row model on a new policy,
not a fresh-epoch validation or impossibility result. Full proof production is
not selected. Distinct common-map coverage stays2600 LOWER rows.

Calibrations share their original200-CPU scope and one20 allowance: combined
52.163440/200 seconds. Literal archive is5126792 bytes,
SHA256 `3964a44c888ddd1cf86b8b85d6e9b84affbb9048bc9849f351eaa78bda2b4a35`; compact continuation archive
is1579570 bytes, SHA256 `b63de2a7e5e75f1c7dd4173f5f928a161df8df6843d82acf5f877b99d1876ab6`.
Receipts: `results/inline-scaling6-20261018/closure.json` and
`results/inline-compact-scaling6-20261018/closure.json`. All donor pools and23
P1 files are unchanged. Repeated conditional row facts supply no new coverage.

The exact-epoch reuse-query attempt was intentionally stopped, retaining its
1423.784152-CPU failed receipt and supervisor reconciliation. No complete count
or forecast is inferred. One historical-cost recovery keeps persistent256MiB
memo guidance, a100000-step query cap and unchanged native bound/leaf checks.
Its costs are explicitly historical estimates, not current exact minima.
Small LOWER/UPPER fixtures complete at2525nodes/108records/2750tokens and
26nodes/2records/27tokens. Initial LOWER is LIVE at
`results/historical-query-layout6-20261018`,1450 native/1550 outer CPU caps,
1700 reservation,6GiB hard RAM, swap/core0. The original5650-CPU FAMILY includes
all predecessor charges, prior control corrections and400 reserved assembly
allowance for future supervision; its predeclared envelope is5589.460859.
UPPER remains undispatched, capped at1550 native/1650 outer with1800 reservation.

Final systemd CPU records exposed controller CPU outside the wait4 receipt.
Only the uncovered DIFFERENCES are conservatively withheld in assembly:
206 seconds for bounded-layout,114 for stopped reuse-query,49 for global-reuse,
after their existing20 allowances and with5 seconds preparation margin. Native
receipts are not charged again, allocations and172800 total remain unchanged,
and every5650 scope still holds. Exact journal evidence and allowances are in
each `control-accounting.json`; old receipts/closures remain preserved.

A bounded Astra/medium read-only assessment is examining cross-bound lemma
reuse and score/colour transport. It may suggest a discriminating experiment;
it supplies no accepted theorem or speedup. Initial +4, the SAME optimal16–20
pair and the completed private package remain OPEN. No publication or email.

## 18 October 2026, 10:03 UTC — Encoded Step accepted; two bounded native comparisons

`Game.EncodedStepAssembly` retains encoded values in the state map and decodes
only at the logical winning-step boundary. Safe Agda accepts `empty`, `join`,
`rows`, checked missing-key completion and accessibility recursion, together
with an encoded toy root and fallback. Four interfaces pass, including two
repeated dependencies. Receipt:
`results/encoded-step-assembly-probe6-20261018/closure.json`; outer8.310154 CPU,
one20 allowance,28.310154/100 combined. Its354137-byte archive has SHA256
`043d7efdfa78b3887521fee31af446a73db67e5e540c8893ac852abdfa04b009`.
This is a generic conditional architecture, not a full6x6 map, new row coverage
or a measured performance improvement. P1 and all donor pools are unchanged.

A source-only Sol/medium leaf supplied `global_reuse_layout6.py`. Before
building, the coordinator replaced repeated per-disc graph scans with bounded
memoized DFS and a fresh reachable child-before-parent order, using only the
already allocated graph arrays. The original pinned min-replies graph must
first complete. Own choices may then use any exact-key child already in that
same-goal graph; pinned choices remain fixed. Original and postprocessed graph
statistics are reported separately. This minimizes forcing-tree cost within
the existing state set; it does not claim a minimum DAG.

Both small fixtures complete: LOWER3805→3698 DAG nodes,5534→5503 tree nodes,
109records/3929tokens; UPPER28→28 DAG nodes,2records/29tokens. Node, edge and
tree counts are checked not to exceed the original counts. These are untrusted
extraction counts only. Explicit ownership cuts for all34 line states remain
OPEN. No wire or source is exported.

`results/global-reuse-layout6-20261018` now runs its initial LOWER comparison
under a fresh predeclared5650-CPU two-sided scope (compiled20, fixture110,
LOWER2750, UPPER2750, assembly20); previous method caps are not reset. To permit
the two native comparisons concurrently, the running reuse-query group's hard
memory cap was lowered from9GiB to6GiB, and global-reuse receives6GiB. Their
combined hard cap is12GiB, swap/core0; no additional Othello job overlaps.
Runtime limits and exact before/after memory properties are preserved in
`results/reuse-query-layout6-20261018/runtime-memory-allocation.json`.
CPU caps, category allocations and the80GiB disk floor are unchanged.

A new inline checker calibration is SOURCE-ONLY pending, using training
parts342/10441/17236/26707 and held-out4913/15761/23417. Selection case33154 is
excluded. It will check repeated rows and conditional encoded Step exports,
freeze its row-component prediction before the holdout, and report state/
resolver costs separately. No calibration job is dispatched while both6GiB
native groups are active. It supplies no forecast or acceptance yet.

Initial LOWER/UPPER roots, SAME optimal16–20 pair and completed private package
remain OPEN; distinct common-map Partial remains2600 LOWER rows.

## 18 October 2026, 09:50 UTC — Step assembly checked; initial census still OPEN

Safe Agda accepts `Game.StepAssembly` and its closed toy example. The
`Step`/`Partial` contract keeps one common state map and local checked row
proofs, with a checked winning fallback for absent keys and well-founded
recursion over earlier keys. Its final assembly contract needs no global
certificate-body map. Ordinary and directed row bridges are checked; the
existing2600-row common Partial has not yet been instantiated into this new
contract. This supplies no initial6x6 bound or measured workflow speedup.

Receipt `results/step-assembly-probe6-20261018-fixed2/closure.json` accepts
three interfaces. Both earlier failed receipts remain preserved. Total scope
is37.346919/100 CPU seconds including one20-second allowance. Archive
`results/step-assembly-probe6-20261018-fixed2/accepted-conditional-checkpoint.tar.gz`
is253911 bytes, SHA256
`75a0ca2b18fd6af105fba1298ddae671a5e5246f29abbac436f8cfbff878a400`.
All taggedP1 files and donor pools are unchanged.

The earlier `bounded-layout6-20261018` initial LOWER census is CLOSED FAILED:
the outer2600-CPU guard stops it with2632.827210 measured CPU seconds, before
any final `lower.json` or complete count. Combined build/fixture/LOWER charges
plus20 assembly are2655.099887/5650. UPPER was never dispatched. No prefix
count is presented as a complete graph or forecast.

A separate per-query-capped family first completes small LOWER/UPPER fixtures
at2845nodes/88records/3034tokens and26nodes/2records/27tokens. Its source-only
Sol/medium continuation adds exact-key completed-subgraph preference and
invalidates cost estimates whenever the completed set changes. The coordinator
reviews, builds and checks it: LOWER2436nodes/122records/2691tokens; UPPER
26nodes/2records/27tokens. These remain untrusted native counts. A guard
preflight exposed a32MiB aggregate allowance being passed to a16MiB per-probe
cap; this was repaired before any new native phase, with provenance retained.

The reuse-query INITIAL LOWER census is LIVE at
`results/reuse-query-layout6-20261018`, with2500 native/2600 outer CPU caps,
2750 reservation,9GiB hard RAM, swap/core0, counts only and ordinary disk
limits. Both variants share their original5650-CPU family cap and single
20-second allowance; the predecessor's1.763920 actual CPU seconds are included.
No graph, wire or Agda source is exported. No production gain or complete
initial count is claimed. Kernel availability before this census is
9854.978845 CPU seconds; category allocations remain unchanged.

The initial +4 bounds, SAME optimal Black16–White20 pair and private completed
package remain OPEN. Common-map Partial remains2600 distinct LOWER rows.

## 18 October 2026, 09:11 UTC — SAME-pair path assembly checked, bounds OPEN

Safe Agda accepts all four modules in the one splice recovery:
`Game.StrategySplice`, `Game.PathSplice`, `Othello.PathSplice6`, and
`Othello.SpliceLine6`. `patch` follows a winning continuation on the chosen
history prefix and keeps an existing winning strategy after divergence.
`Along.assemble` proves that the resulting white and black guarantees admit
one completed play along the same prescribed legal trace. Fast-game agreement
transfers those exact strategies and that play to the original rules.

`SpliceLine6` checks the actual33-ply standard initial6x6 trace, including its
forced pass, terminality and Black16/White20 counts. Its public theorem
`problem2-from-prefix-bounds : Along.Bounds line → Problem2` is CONDITIONAL:
all winning guarantees on the line are still inputs. No initial bound, global
coverage or full Problem2 theorem has been supplied. This route can use opaque
checked off-line guarantees without normalizing their certificate strategies;
the common on-line strategy choices are constructed explicitly.

The initial concrete original-rule wrapper hit35CPU with no interface; its
failed receipt remains unchanged. Separating generic finishing from the literal
trace and using the already checked fast-game agreement accepts the recovery
in8.265434 outer CPU seconds. Combined scope, including
the prior failure and the one20-second allowance, is
79.788702/170 CPU seconds. Recovery phase CPU is
0.191040/0.169702/0.260992/0.529588 seconds; peak0.132874GiB.
Archive `results/path-splice-probe6-20261018-fixed/accepted-conditional-checkpoint.tar.gz` is545982 bytes,
SHA256 `e2fb1cd49ada5f8f4b600c65ca8fd2a8be5ae897cf117ee00c013bcf14fc1804`. P1 and all donor pools are unchanged.

For eventual complete maps, expose the canonical versions of all34 trace
states as owned records (adding cuts where they would otherwise be inlined),
prove their exact map lookup alignment and transport both bound guarantees
back to the literal states. Then instantiate `Along.Bounds line`. Existing
fail-closed line pins keep these states in the selected native graph, but the
current counts-only cut policy does not yet force all of them to be exported.
This export/lookup obligation remains OPEN; do not infer it from native pins.
The earlier SharedProof6 certificate/jointCheck route remains available.
Common-map Partial remains2600 distinct LOWER rows. The earlier initial native LOWER layout census later failed at its CPU cap;
see the newer closure above. No wire/source export or proof production began.

## 18 October 2026, 09:06 UTC — bounded cost search and initial layout

The uncapped exact-cost16 sample is censored at40 native CPU seconds on its
first graph:1134 visited nodes are only a prefix. Its earlier helper-identity
failure and the exact-binary recovery remain failed receipts. Their combined
scope costs57.273078/187 CPU seconds including the one15-second allowance;
no incomplete count is used as a complete graph.

A new bounded search distinguishes exact costs from lower bounds, prunes at
cost4096 and falls back to the original validated native choice when a cost
is unknown. Its three complete sample graphs are1684/194/220 nodes, versus
cost12's2914/200/220. The capped screen closure costs
19.175981/187 CPU seconds including15 assembly;
all counts remain untrusted extraction guidance.

`results/bounded-layout6-20261018` uses this policy with the existing fail-closed
16–20 line pins and the established counts-only layout instrumentation. Its
LOWER fixture accepts1684nodes/83records/1861tokens; the UPPER near-terminal
fixture accepts26nodes/2records/27tokens. The INITIAL LOWER counts phase is
LIVE with native2500/outer2600 CPU caps,2750 native reservation,9GiB hard RAM,
no swap/core and the ordinary80GiB floor. No wire, graph or Agda source is
exported. The predeclared two-sided scope cap is5650 CPU seconds including
compiled20, fixtures110, two2750 native reservations and20 assembly. This is
not proof production or an initial-value result.

An Astra/medium leaf inspected existing assembly and interface costs in read-only
mode, without tests, solver execution, writes or delegation. It found no
new measured factor-two workflow gain. A contract without a global body map
could simplify final assembly, but savings remain unmeasured. The coordinator
has separately prepared a generic strategy-splice theorem and a conditional
SAME-pair line assembly; checking is in progress. Required prefix bounds remain
open. Distinct common-map coverage remains2600 LOWER rows; the full objective
is incomplete. The main model has not changed.

## 18 October 2026, 08:44 UTC — row cache checked, not selected

The one recovery of the row-cache probe accepts all seven interfaces: cached
row arithmetic, state representation, ordered game refinement, resolver and
three same200-row conditional TreeOK variants. Module CPU is0.842 seconds for
InlineRows6,1.004 for cached codes with literal bodies and1.249 with Unicode
bodies. This hybrid is slower and is not selected. The accepted archive is
`results/row-cache-probe6-20261018-fixed/accepted-conditional-checkpoint.tar.gz`
(3046064 bytes, SHA256 `41380c86b75384931a16f5e6751186f71730298391e305f087f670028ced7721`). Combined outer
CPU including the failed attempt and shared20-second allowance is
76.462929/200 seconds.
All donors and23 taggedP1 sources are unchanged; distinct common-map coverage
remains2600 LOWER rows. Initial lower/upper Proven roots and the SAME-pair
jointCheck remain open. Kernel availability at this closure is
9932.114466 CPU seconds; allocations
are unchanged. A source-only Sol/medium leaf supplied CachedRow6; the
coordinator integrated the modules, checked and reconciled both attempts.

## 18 October 2026, 08:42 UTC — cost12 screen and row cache

The bounded cost12 native screen is closed at
`results/endgame12-screen6-20261018/closure.json`: 0.975255 compiled CPU
seconds, 1.641371 native CPU seconds, and the predeclared 15-second assembly
allowance. Exact-cost12 versus cost8 changes the three 16-empty sample graphs
from 3416/304/291 to 2914/200/220 nodes. This is untrusted extraction guidance;
no initial-board forecast or Agda premise follows. The initial +4 bound and
SAME optimal Black16–White20 pair remain open.

`CachedRow6` was produced with a source-only Sol/medium leaf; integration and
all checks remain coordinator-owned. Its finite arithmetic update proof is
accepted in the first row-cache probe (0.459167 CPU seconds). That attempt
fails next on a missing local binary congruence lemma in RowCacheState6 and is
closed without row coverage. One fresh recovery uses the same 200 existing
rows, the same citations and a combined 200 CPU-second cap including the
shared 20-second allowance. The original failure and donor pools are retained.
The recovery is pending; the best previously accepted generic checker remains
InlineEntries6/InlineRows6. No distinct new common-map rows have been added.

# Verification ledger

18 October 08:29 UTC, closed-instance specialization is not selected.
Two semantic versions reach their35/15 CPU hard caps with no interface.
Their failed reports and helper snapshots remain unchanged. A final Boolean-only
aggregate imports both200-row assertions in one cold process:0.852 generic /
0.831 specialized module CPU seconds; Boolean core0.042. Four interfaces pass,
but generic semantic soundness for that closed implementation is unaccepted,
so its conditional TreeOK row count is explicitly zero. The entire scope,
including both failed attempts and the shared20 allowance, costs111.324755 of
140 CPU seconds. Receipt:
`results/concrete-lower-probe6-20261018-boolean/closure.json`.
The certified generic inline checker remains the preferred implementation.
Global available at that closure74,869.607464 CPU seconds, kernel9,988.577395,
no reservations and unchanged allocations. Unchecked ConcreteLowerChecker6/
ConcreteLowerRows6 sources are experimental; do not cite them as checked.

The native oracle-TT alignment screen also closes: exact-cost8 baseline graphs
3416/304/291 become6631/418/318, so oracle alignment is rejected. It adds no
kernel evidence. Record: `results/tt-policy-screen6-20261018/closure.json`.
Initial +4, full lower/upper roots, SAME16-20 pair and packaging remain open;
common-map Partial remains2,600 lower rows, no new row coverage.


18 October 08:20 UTC, native policy screens are complete and reconciled.
Three cold known lower fixtures compare minimum replies with completed-memo
preference (states3805/3690,361/361,316/316), larger fail-soft margin
(3805/4773,361/952,316/372), and exact forcing-tree minimization below eight
empties (3805/3416,361/304,316/291). The margin policy is worse; the other
reductions are modest and validate no initial-game forecast. All census counts
remain untrusted, with no new Agda premise, distinct row or proof coverage.
The exact-cost memo is64MiB, reset for each frontier run, included in the native
allocation guard, and uses complete canonical keys. Every policy delta restores
byte-for-byte to the original census; solver/rules/TT code is unchanged.
Closure receipts: `memo-reuse-screen6-20261018`, `margin-policy-screen6-20261018`
and `endgame-cost-screen6-20261018` under results. Each respects its137CPU cap;
actual build/native charges and conservative assembly allowances are separate.

A140CPU bounded Agda probe now compares the generic inline verifier with a
textual closed LOWER instance. It retains the complete local/forest soundness
and semantic TreeOK bridge, fixing game, order, picker, transport and score
instead of carrying module parameters on recursion. Source preparation alone
is not accepted evidence. Record: `results/concrete-lower-probe6-20261018/plan.json`.
Common-map Partial remains2,600 lower rows; initial lower/upper roots, the SAME
optimal Black16-White20 pair and final package remain open.


18 October 08:04 UTC, certified empty-coordinate game accepted, no speedup.
`EmptyCache6` proves ordered vacancies unchanged by arbitrary capture lists,
removal after a placement, cache injectivity and safe equality recovery.
`CachedGame6` proves exact arbitrary-board ordered successors/pass refinement
and directed picker soundness. `CachedRows6` plus all three conditional200-row
instances pass (six interfaces). Matched module CPU: inline0.870, cached0.931,
cached Unicode1.155 seconds. This variant is not selected for performance.
Five failed integration attempts remain failed, with exact helper snapshots;
all outer charges plus the one20-second allowance total110.752740 CPU seconds
within the original200-second scope. Receipt:
`results/cached-game-probe6-20261018-fixed5/closure.json`.
Global availability after this closure is75,040.173470 CPU seconds,
kernel10,079.902151, zero reservations, unchanged category allocations.
Common-map Partial stays2,600 lower rows; full initial roots/SAME pair are open.

A separate untrusted stable-disc screen over eight existing parts (1,600 rows)
finds2,354 removable explicit descendants among22,397 nodes, with1,813 possible
cut points. References conceal external subtrees; this is neither a forecast
nor a soundness proof for stability. It costs1.259106 assembly CPU seconds plus
10 conservative allowance, reconciled once by study6. Receipt:
`results/stable-bound-screen6-20261018/screen.json`. No Agda premise or new row.
A new source-only native census policy prefers a child already present in the
completed exact-key same-run memo, then minimum replies. A bounded cold build/
three-fixture screen is underway; no reduction or complete initial game is
claimed before terminal results. Solver/rule/TT source is unchanged by a
reversible census-only delta. Scope137 CPU seconds (compiled12, native110,
assembly15), with1GiB hard memory/no swap/core0 and ordinary storage limits.


18 October 07:49 UTC, erased arithmetic comparison closed successfully.
Seven safe interfaces pass, including constructive irrelevant-witness equality
recovery, ordered game/pass refinement and both existing200-row instances.
Matched relevant/irrelevant module CPU is 2.417 / 2.406 seconds: no material
improvement. Receipt: `results/erased-arithmetic-probe6-20261018/closure.json`.
Sole outer charge58.034395 plus20 allowance, within200. Global available
75,150.926211 CPU seconds, kernel10,170.654892, zero reservations. No new rows,
initial theorem or SAME pair. The live notices below are historical.
Source-only work now prepares certified empty-coordinate caches; no acceptance
or speedup is claimed before the next bounded check.


18 October 07:47 UTC, latest status (earlier live notices below are historical).
All probes through `inline-entries-probe6-20261018` are terminal and reconciled.
Strict packed fields and strict ordinary boards pass all identity/refinement
proofs but are slower: module CPU 1.180 hybrid, 1.709 packed lazy, 1.732 packed
strict, 1.455 ordinary strict. Receipt: `results/strict-state-probe6-20261018/closure.json`.

`LengthRays6` checks all 728 player/cell prefix cases, then arbitrary-board
capture, ordered moves and pass agreement. Two existing conditional 200-row
instances pass: module CPU 1.180 baseline / 1.055 length rays. This local
10.6 percent reduction has no full-workflow forecast. Receipt:
`results/length-rays-probe6-20261018/closure.json`.

The Unicode codec consumes complete fixed-width bodies and checks exact
decoding of the existing 200 certificates: 1.350 ASCII / 1.268 Unicode module
CPU seconds. Receipt: `results/unicode-codec-probe6-20261018/closure.json`.
Inlining each ray expression into one shared board destructuring proves exact
entries equality and passes ordered successor/pass and picker linkage. Its
matched modules use 1.027 length baseline / 0.859 inline literal / 1.098 inline
Unicode CPU seconds. Receipt: `results/inline-entries-probe6-20261018/closure.json`.
These are repeated rows, not additional common-map coverage.

After those closures the ledger has 75,228.960606 CPU seconds available,
including 10,228.689287 kernel, zero reservations and unchanged allocations.
The common-map Partial still owns 2,600 lower rows. Whole initial lower/upper
roots, SAME optimal Black16-White20 pair and final package remain open.
A separate bounded erased-canonical-witness arithmetic comparison is live:
`results/erased-arithmetic-probe6-20261018/plan.json`, 180 kernel reserved plus
20 assembly allowance, 4GiB/no swap/core zero. Its first two core phases pass;
no whole-probe acceptance or timing claim follows yet.


18 October 07:16 UTC, arithmetic game and instance accepted, slower.
The finite arithmetic-state proof passes with four core interfaces; all
column-stage attempts, including both rewriting corrections, use 162.661709
CPU seconds of the 200-second cap including their shared allowance. Its
checkpoint is `results/arithmetic-columns-probe6-20261018-state/closure.json`.

A separate cold evaluation safely checks the exact ordered successor/pass
refinement of `ArithmeticGame6`, arithmetic row soundness and all 1,095
canonical-code witnesses. Both existing conditional 200-row TreeOK variants
pass, with nine interfaces. The stored-code/ordinary-working-board baseline
uses 1.170 module CPU seconds; arithmetic working codes use 2.421, so arithmetic
updates are not selected as an optimization. Complete phases use 6.866039 /
8.196737 CPU seconds. Core game checking uses 19.057740 seconds at 2.050323GiB
peak RSS. The sole enclosing receipt charges 58.155632 seconds plus 20
conservative allowance, within 200. Record:
`results/arithmetic-evaluation-probe6-20261018/closure.json`.
Global availability after reconciliation: 75,545.841984 CPU seconds, kernel
10,465.570665, no reservations and unchanged category allocations. These
checks add no distinct rows, common-map Partial join, initial roots or SAME
optimal pair theorem. Whole-workflow forecast remains unvalidated.

A bounded strict-evaluation comparison is live at 07:17 UTC. It uses Agda's
safe `Agda.Builtin.Strict` primitive and must prove the forced value equals
the original value for every board/code. Both packed codes and ordinary Cell
boards are compared against matched baselines on the same 200 rows. No
speedup or acceptance is claimed before the terminal report.

18 October 07:10 UTC, finite arithmetic reflection accepted.
The 24-function column layout still reaches its 90-second process cap, with
no row-arithmetic interface; its sole outer receipt charges 122.506547 CPU
seconds and the raw report remains false. Hardened limits produce no core.
The bounded recovery changes proof layout to constructive finite Boolean
quantifiers: `Othello.FiniteCheck6` proves exhaustive Cell/Fin/row coverage,
and one closed Boolean assertion checks all 4,374 reads and 13,122 replacements.
`Othello.RowArithmetic6` passes in 0.181 module CPU seconds. There is no native
solver premise. All three interfaces (BooleanUIP, FiniteCheck6, RowArithmetic6)
are accepted despite the subsequent ArithmeticState integration failure;
the raw whole-run report remains false. That outer receipt charges 6.646842
CPU seconds. The failed integration needs the decoder roundtrip rewrite in
the subsequently unfolded successful-move branch; a source-only correction
is under bounded check. No arithmetic game or 200-row claim follows yet.
The final recovery reserves 40 seconds and checks only core/ref-data targets,
sharing the original 20-second allowance. All attempts remain inside the
original separate 200-second column-stage cap. Records:
`results/arithmetic-columns-probe6-20261018-finite/closure.json` and
`results/arithmetic-columns-probe6-20261018-finite-fixed/plan.json`.

18 October 07:05 UTC, arithmetic integration remains unchecked.
The constructive `Game.BooleanUIP` proof passes after an explicit endpoint
annotation; no K axiom or postulate is used. The monolithic 4,374-read plus
13,122-replacement row proof reaches its 180-second per-process CPU limit
without producing a row interface. SIGXCPU writes a systemd core dump; its
temporary write breaches the ordinary disk floor and the storage guard
interrupts the worker. The report is absent, not accepted. Only the single
BooleanUIP interface is accepted; all arithmetic-state/game/row/instance
claims remain open. The outer receipt charges 238.098217 CPU seconds,
plus the prior 5.129171-second inference failure. One shared 20-second
allowance and an extra conservative five seconds for core handling keep
this failed scope at 268.227388 of 320 seconds; its unused amount is not
reset or transferred. Accepted donors and P1 are re-audited unchanged.
Record: `results/arithmetic-game-probe6-20261018-fixed/closure.json`.

Only the exact new core file for PID588148 from this Othello service is
removed, preserving its metadata and hash; all other core files are untouched.
The 80 GiB floor is restored. `run_job.py` now sets RLIMIT_CORE to zero and
uses identical soft/hard CPU limits; systemd probe units also set LimitCORE=0.
A one-second CPU-limit smoke test records child limits [0,0] core/[1,1] CPU,
SIGKILL exit -9 and no new coredump entry. It is covered by the five-second
handling allowance. Receipts: `own-coredump-cleanup.json` and
`runtime-core-hardening.json` in that same failed result directory.

A separate 200-second bounded column-layout comparison starts at 07:05 UTC,
with 180 kernel seconds reserved plus 20 assembly seconds. It keeps the same
4,374/13,122 finite obligations but divides them among 24 smaller functions;
it changes no arithmetic operation or theorem statement. No acceptance or
speedup is claimed before its terminal report. Record:
`results/arithmetic-columns-probe6-20261018/plan.json`.

18 October 06:50 UTC, complete transition repacking is accepted but slower.
`Othello.PackedGame6` safely refines to the original specialized ordered game
for every stored state, and its directed picker is sound. `PackedRows6` and
both existing 200-row conditional instances pass (four interfaces). The
six-Nat stored-resolver baseline uses 1.193 module CPU seconds; repacking via
ordinary boards after every transition uses 1.696. It is not selected.
The sole outer receipt charges 33.631376 CPU seconds, plus a 20-second
conservative allowance, within 320. Reconciled availability: 76,054.886714
global, 10,909.615395 kernel, zero reservations and unchanged allocations.
Record: `results/packed-game-probe6-20261018/closure.json`. No new distinct
rows, common-map Partial join, initial value or same-pair result.

18 October 06:46 UTC, six-Nat stored-resolver probe accepted.
Safe Agda checks `Game.MappedTransfer`, all 729 row roundtrip equations in
`Othello.RowPacked6`, arbitrary-board matching soundness, the generic
`Game.EncodedResolver` and its six-board row integration. All 1,095 supplied
citation codes match the exact prior accepted same-key inputs. Matched
conditional 200-row modules use 1.585 CPU seconds for ordinary stored boards
and 1.171 for six-Nat stored values, while working boards remain ordinary.
Complete phases cost 7.054688 / 6.698694 seconds. Seven interfaces pass.
The original parser failure is retained and charged; combined outer receipts
plus one shared assembly allowance use 61.595114 CPU seconds within 320.
Record: `results/row-packed-probe6-20261018-fixed/closure.json`.
Reconciled global availability is 76,108.518090 seconds, kernel 10,943.246771,
with no reservations at this checkpoint and unchanged category allocations.
No new distinct rows, common-map Partial join, initial value or SAME-pair
closure is supplied. The sample saving does not validate a new full forecast.

18 October 06:33 UTC, prospective directed-body comparison accepted.
`Othello.DirectedCompact6` safely decodes the new directed syntax; Agda
checks exact equality with the accepted 200-row body vector and both
conditional variants. The initial rejected large literal pattern and bounded
correction remain separate receipts. An internal profile of the prior
200-row checker reports 5.176 seconds deserialization and 1.514 seconds
Typing.CheckRHS; the 6.986-second total is not a row-only measurement.
Records: `results/checker-profile6-20261018-fixed/` and
`results/directed-codec-probe6-20261018-fixed/`.

A new cold-source experiment checks 800 existing training rows and 800
held-out existing rows in both literal and compact directed formats. Source
body cost plus row-module checking is measured separately from state/resolver
source and imports. The forecast is frozen before ANY held-out source check.
Held-out aggregate relative error is 8.894669% literal and 12.749013% compact;
both sampled 30% component gates pass. The compact component predicts
32,400.480540254 CPU seconds for the full LOWER wire's 88,689,949 tokens,
exceeding the 10,984.841885 kernel seconds available after reconciliation.
This rejects production with this measured workflow within the current
category balance; it is not a lower bound on all possible proof methods.
Whole-workflow CPU, memory, storage, upper coverage and SAME-pair gates remain
unvalidated. Zero new distinct rows and zero new common-map Partial joins.
Records: `results/directed-scaling6-20261018-final/forecast-freeze.json`,
`holdout-comparison.json`, and `closure.json`. The original statistics
KeyError after 22 accepted training interfaces and the subsequent zero-interface
module-name ambiguity are retained as failed receipts. The final recovery
uses fresh module names and 21 new interfaces. All three outer receipts plus
one shared assembly allowance use 62.422610 CPU seconds of the 320-second
scope. Reconciled global availability is 76,170.113204 seconds, with unchanged
category allocations and no reservations at that checkpoint.

18 October 06:09 UTC, specialization and directed-choice soundness pass.
Safe Agda checks `Othello.CellRays6`, `Othello.Specialized6` and the generic
`Othello.AgreedIndexed6`. The first rejected implicit-size application remains
recorded; its correction is checked. The specialized evaluator agrees with
the original ordered game on EVERY six-board state, including forced pass.
Two original conditional 200-row Partial instances pass; their matched module
profiles are 3.513 seconds incremental / 2.309 seconds specialized. This adds
zero distinct rows. Record:
`results/specialized-rule-probe6-20261018-fixed/closure.json`.

The new `Game.DirectedIndexed` checker accepts a coordinate choice directly,
and its generic soundness reconstructs an ordinary legal choice using a
proved successor-index witness. `Othello.DirectMoves6` supplies that witness
for every successful six-board pick. `Othello.DirectedRows6` supplies fused
row soundness. Safe Agda checks the original body-vector equality and two
matched 200-row conditional TreeOK instances: ordinary literal choices use
2.131 module CPU seconds; 2,663 directed choices use 1.885. The first generic
with-scope error remains rejected, with the correction checked in the recovery.
This changes certificate syntax; it is NOT an additional common-map Partial
join. Record: `results/directed-move-probe6-20261018-fixed/closure.json`.

Finally `Othello.DirectSymmetry6` checks direct permutations against all eight
original D4 board actions and checks both lower/upper certificate transports.
Matched directed 200-row TreeOK instances use 1.878 module CPU seconds with
the original actions and 1.628 with direct actions. Complete phases cost
7.238631 / 6.986057 seconds; the import cost remains visible. All three
interfaces pass. Record: `results/direct-symmetry-probe6-20261018/closure.json`.

All enclosing receipts, failures and recoveries are charged once. At this
checkpoint 76,330.659958 CPU seconds remain globally, with 11,085.388639 in
the kernel category and no reservations. Every category allocation is
unchanged. Accepted donor pools and all 23 P1 files are unchanged. These
small conditional observations do not validate whole-map throughput, storage,
initial lower/upper coverage or the SAME optimal initial Black16-White20 pair.
The common-map milestone remains 2,600 distinct lower rows.

18 October 05:40 UTC, fused row soundness passes. The observations below
about blocked host memory and untested packed data are historical snapshots:
the disjoint NAMOR process ended, and the subsequent probes passed without
altering NAMOR. Safe Agda checks `Othello.PackedNat6`, its exact equality to
the existing 200-state vector and initial board, and the original conditional
Partial judgment. Integer encoding alone gives no measured row advantage.
Separating acceptance and linkage also gives no improvement: the old Aligned
link costs 16.876132 CPU seconds, the generic Compatible link 16.921480.
Records: `results/packed-nat-probe6-20261018/closure.json` and
`results/packed-nat-probe6-20261018-split/closure.json`.

Fusing the closed Boolean `refl` with generic soundness avoids that separate
linkage cost. Four conditional instances over the SAME existing 200 rows pass
with five new interfaces and two precisely pinned reused core interfaces.
The import-only root does not join distinct rows. Module CPU profiles are
6.180 seconds for compact original rules, 6.102 for packed original rules,
3.490 for compact incremental rules and 3.470 for packed incremental rules.
The compact incremental form is the selected candidate; no whole-game forecast
is validated. A first missing generated import remains rejected, with both
attempts charged once: 50.257585 measured outer CPU seconds plus one shared
20-second conservative allowance, within the 220-second scope. Record:
`results/fused-row-probe6-20261018-fixed/closure.json`.

After this reconciliation the unchanged 172,800-second ledger has
76,560.031868 CPU seconds available, including 11,254.760549 kernel seconds,
and no reservations. Subsequent live balances and bounded jobs are recorded
in the single ledger. Common-map coverage remains 2,600 lower rows; complete
initial lower/upper roots and the SAME optimal initial pair remain open.

18 October, indexed agreement passes; performance diagnosis remains pending.
Safe Agda accepts `Game.IndexedTransfer` and the first version of
`Othello.IncrementalIndexed6`: pointwise game/action agreement transports the
Boolean indexed checker, including solve, pass and symmetry-citation cases.
The existing 200-row instance also accepts the original Boolean judgment and
conditional Partial linkage. Its combined variant uses 40.553380 CPU seconds,
versus 11.018517 for the compact baseline, so it is not adopted as a speedup.
The first rejected symmetry-case proof and the accepted correction are both
preserved. Together they charge 83.469910 CPU seconds plus one shared
20-second allowance, within their 220-second scope. Record:
`results/incremental-indexed-probe6-20261018-fixed/closure.json`.

The workspace now has an untested opacity-only change to that new integration
module, and an untested `Othello.PackedNat6` decoder to ordinary six-board
states. Prepared probes separate Boolean work from proof transport and check
integer-state equality against the accepted 200-row vector and initial board.
Neither pending probe has launched or reserved CPU: actual host memory
pressure from the separate NAMOR checkout fails the launch headroom guard.
NAMOR is untouched. The Othello job guard permits disjoint NAMOR checks only
with separate sources/caches, sufficient host headroom and unchanged own
hard RAM/no-swap bounds; it retains a live 2 GiB host-memory floor.

Offline preparation and small diagnostics conservatively exclude another
5 assembly CPU seconds. Latest reconciled ledger has 76,807.611067 CPU seconds
available, including 11,442.339748 kernel seconds, with zero reservations.
See `results/completion6-offline-preparation-20261018.json`. Initial +4, the
SAME optimal initial Black16-White20 pair and whole-workflow resource gates
remain open; the common-map certificate coverage is still 2,600 rows.

18 October, full-resolver representation and incremental rule agreement pass.
The full-resolver probe checks exactly nine cold modules and a shared-map
400-row Partial for two existing parts. Every citation is checked directly
against the accepted full state map; only each owned chunk needs a route.
Agda uses 206.542657 CPU seconds; the sole enclosing receipt charges
274.152180. Systemd records 296.317863 CPU seconds, 6,597,238,784 bytes peak
memory and zero swap. The 22.165683-second service difference is covered by
the separate 50-second conservative allowance. Part33154's interface falls
from 341,682 to 39,870 bytes; its row-profile CPU remains similar (22.506 versus
22.210 seconds). Neither the byte ratio nor this two-part run validates a
whole-game forecast. Record: `results/full-resolver-probe6-20261018/closure.json`.

Safe Agda also checks the new `src/Othello/Incremental6.agda`, byte-identical
to the isolated checked copy. It proves agreement with the old ordered rules
for every 6x6 board, including repeated capture coordinates and empty cells.
It introduces no postulates or rule premises. On the same 200 existing
positions, both implementations match all 522 expected ordered successors.
The module profiler reports 624 ms old / 385 ms incremental for this move-list
comparison; complete phase CPU is 1.014875 / 0.824760 seconds. Indexed row and
whole-game benefits are unmeasured. All four phases pass; the enclosing receipt
charges 28.285951 CPU seconds, systemd 30.605212, with a separate conservative
20-second allowance. Record and source hash:
`results/incremental-rule-probe6-20261018/closure.json`.

These tests add no distinct certificate rows. The accepted 2,600-row common-map
coverage, all 23 P1 files, all 101 original formal modules and the original
checkpoint are preserved. One new standalone formal module is now checked.
Latest ledger: 95,155.962622 CPU seconds charged, 727.956401 withheld, zero
reserved, 76,916.080977 available. Initial +4, complete lower/upper coverage,
the SAME optimal initial Black16-White20 pair and final packaging remain open.

18 October, bounded representation diagnostics completed. These experiments
add zero distinct rows beyond the 2,600-row common-map result below.

The first singleton-citation attempt is interrupted early and remains rejected
(checker exit -15, outer exit 1). A one-citation diagnostic then rejects its
implicit resolver parameter with unsolved metas (exit 42); explicit `{G = G}`
passes. The corrected two-part checker exits 0 and accepts the shared-map
400-row Partial. Its harness exits 1 because the generator declared 51 modules
but the theorem needs only 50: the unused second Family alias is not imported.
`semantic-scope-audit.json` records the accepted theorem and that precise unused
source; the failed harness report is preserved. No missing proof is assumed.
Row profile cost falls from 24.792 to 21.526 CPU seconds, while the new
correspondence proofs cost another 6.745 seconds. This is not a validated
whole-workflow speedup. Records: `results/sparse-citation-pilot6-20261018/`,
`results/citation-diagnostic6-20261018/`, and
`results/sparse-citation-pilot6-20261018-fixed/`.

A constructor-data experiment checks exact equality with the accepted compact
state/body vectors, then rechecks the same 200 rows with symbolic Partial
linkage. After one cheap generic-type failure, all five recovery phases pass.
The compact baseline uses 10.614856 CPU seconds; constructor rows and linkage
use 21.844956, plus 2.829329 for the state/body equalities. The constructor
variant is not adopted. Both attempts together charge 51.890467 CPU seconds
plus one shared conservative 20-second allowance, within the original 220-second
scope. Their peak service memory is 737,828,864 bytes, with zero swap.
Exact receipts and the conditional checkpoint are under
`results/direct-rows-probe6-20261018-fixed/`; the failed first receipt remains
under `results/direct-rows-probe6-20261018/`.

All enclosing receipts, including failures, are charged once. After these
diagnostics the unchanged 172,800-second ledger has 94,853.524491 charged,
657.956401 withheld, zero reserved and 77,288.519108 available; kernel balance
is 11,828.247789 seconds. These balances do not validate a full-game forecast.
No initial lower/upper root or SAME optimal initial pair is claimed.

18 October, continued desktop formalization: 1,600 new lower wire-epoch rows
and their shared-map join pass safe Agda. The user has authorized necessary
formalization and tests within the existing budgets, without per-test consent;
the authority record is `results/completion6-continuation-authorization-20261018.json`.
The historical state-map pilot is closed with its unused 160.510047 CPU seconds
preserved; no allocation, grant, charge or stage counter is reset.

Eight disjoint new parts add 1,600 checked rows to the accepted 1,000-row
baseline. All 95 declared modules are checked from cold owned caches. The
result is a genuine `Partial` theorem for 2,600 rows under one common state
map and one common certificate-body map. All 13 borrowed source/interface
pools and all 23 tagged P1 files remain unchanged. Unowned citations remain
obligations; complete initial lower/upper coverage and the SAME optimal
Black16-White20 initial pair are still unproved.

The Agda invocation exits 0 at 275.778672 CPU / 392.676160 wall seconds.
Its millisecond-rounded module profile assigns 76.750 seconds to the eight
row modules and 187.349 seconds to undiagnosed Miscellaneous work; no current
whole-workflow forecast or production gate is validated. The sole enclosing
receipt charges 381.419344 CPU seconds once. Systemd records 414.154418 CPU
seconds, 8,466,571,264 bytes peak memory and zero swap. The 32.735074-second
service difference is covered by the separate conservative 50-second
preparation/supervision allowance. Nested CPU is not charged again.

Final checkpoint storage is 11,890,331,648 allocated study bytes with
86,906,421,248 free bytes, respecting the 12 GiB artifact cap and ordinary
80 GiB floor. Receipts, exact flags, binary/source/cache hashes and the
accepted private checkpoint are in `results/completion-batch-lower-a6-20261018/`.
The ledger has no outstanding reservations and 78,080.333895 CPU seconds
available across its unchanged categories. This partial result does not
complete the initial 6x6 objective.

18 October, desktop grouped-bridge measurement accepted after distinct consent.
The migration hold was explicitly revoked and the authorized cache cleanup
restored the ordinary80GiB free-space floor. The new single-job approval is
`results/grouped-bridge6-20261018-authorization.json`; it grants240CPU seconds
within the existing budget,12GiB hard memory with zero swap and64MiB new
artifacts, with no automatic retry, native search or production.

One safe Agda invocation checks exact copies of the seven accepted bridge
modules for parts380 and17924 plus one import-only target. All eight owned
targets start cold; accepted row facts and the five accepted dependency pools
remain read-only. Exact source/interface hashes and all23 P1 sources are
unchanged before and after. The Agda receipt exits0 at54.487123CPU seconds,
83.102665wall seconds and3.937756GiB peak RSS. Historical separate bridge
receipts total87.997720CPU seconds: this grouping observation uses33.510597
fewer CPU seconds, but is not a controlled speedup measurement or a full-game
forecast. No new distinct game rows or combined semantic theorem are added.

The sole enclosing receipt exits0 at80.607683CPU seconds and3.986530GiB peak
RSS. The final service journal records87.828717CPU seconds,4,275,781,632bytes
memory peak and zero swap. A conservative20CPU preparation/supervision
allowance covers the7.221034-second service difference without charging it
again. The ledger charges80.607684CPU seconds once, retains the20-second
allowance and has no outstanding reservations. The approved scope consumes
or excludes100.607684CPU seconds, leaving160.510047CPU seconds in the existing
full-map stage; the global allocation remains172,800CPU seconds.

Records, hashes, exact flags, source copies and receipts are retained under
`results/grouped-bridge6-20261018/`. New artifacts allocate1,581,056bytes at
the final worker audit; the ordinary80GiB floor and12GiB study-artifact cap
both pass. The original accepted checkpoint remains unchanged. Initial lower
and upper coverage and the SAME optimal initial Black16-White20 pair remain
unproved. This approval covers only the completed grouping measurement.

18 October, multi-part canonical checks and semantic Partial join accepted.
Safe Agda checks all four selected parts380,17924,21836,29329 under direct
canonical state imports: 800 repeated Boolean row assertions and zero new
distinct game rows. It also accepts their full-map bridges and a genuine
semantic join with the prior accepted200-row Part34176. The resulting Partial
theorem uses ONE common state lookup and ONE common certificate-body lookup
for1,000 owned rows. It is not merely an import aggregation. No Boolean check
of the prior Part34176 is repeated. Every owned target starts cold; only the
expected12 row,29 bridge and1 semantic-joint modules are checked (42 new
interfaces). All five borrowed donors and all new row/bridge caches remain
unchanged after assembly.

The row phases use39.077814 CPU seconds in total, with maximum1.031830GiB RSS;
the four bridges use179.219765 CPU seconds, maximum3.812351GiB. The semantic
joint uses98.689212 CPU seconds at5.465900GiB. The sole enclosing child receipt
is362.535081 CPU seconds,327.322367 wall seconds and5.559666GiB peak RSS.
Systemd records386.635811 CPU seconds and zero swap. Its24.100730-second
supervisor difference is excluded separately; nested phase CPU is not charged
again. The complete authorized test stays within600CPU seconds,12GiB hard RAM,
12GiB total study artifacts and its temporary60GiB free-space floor.

Row and bridge forecasts were frozen before the first held-out part. For the
two held-out cases, row prediction24.899175 CPU seconds versus25.311002 actual
has1.653979% relative error; bridge prediction90.265734 versus91.222045 actual
has1.059440% error. Both sampled30% gates pass. These observations validate only
the sampled row/bridge components: the joint has one measured case, and no
whole-initial-game CPU, memory, artifact or production GO follows. Near-constant
43.7-46.3-second per-part bridge times suggest investigating grouped bridge
checks to amortize imports; this remains an unmeasured engineering hypothesis.

Final in-run storage is11,843,805,184 allocated study bytes and74,697,388,032
free bytes. All23 P1 sources retain identity
b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f;
all101 formal source modules are unchanged and have safe options, with zero
source postulates. Exact authorization, plan,42 source/cache identities,
forecast and actual receipts are under `results/canonical-multi6-20261018/`;
see `summary.json` and `collected/results/canonical-multi-pilot6/report.json`.
The test's disk exception and single-job consent are consumed. Ordinary80GiB
storage policy and production gates remain unchanged. Complete initial lower
and upper coverage, the same optimal initial16-20 pair and final packaging
remain unproved/unfinished. No native search or production was launched.

18 October, canonical-state row and full-map linkage pilot accepted.
The explicitly approved single test uses the temporary 60 GiB free-space floor,
while preserving the 12 GiB artifact cap and hard no-swap RAM limit. Safe Agda
checks exactly three new row modules and seventeen bridge modules from cold own
caches, reusing the accepted dependencies read-only. Part34176 repeats its same
200 Boolean row assertions under direct imports of the canonical state data;
it adds zero distinct game rows. All four accepted donors and the new row cache
remain unchanged after linkage.

The row phase takes 22.877007 CPU seconds at 1.256264 GiB peak RSS. The bridge
phase takes 46.120688 CPU seconds at 3.939846 GiB. Including the controller,
source/cache audits and nested supervisors, the sole outer child receipt is
82.115055 CPU seconds, 74.656333 wall seconds and 4.049210 GiB peak RSS. Systemd
records 87.692116 CPU seconds and zero swap; its 5.577061-second supervisor
difference is excluded separately in the ledger. Nested phase receipts are
not charged a second time. The 503 existing state modules are shared directly;
new row sources shrink from 506 modules / 1,545,841 bytes to three modules /
81,604 bytes. This measured run completes without the previous stop/resume
cycle. A controlled speedup ratio is not claimed: the old cumulative run paid
an extra import cost on restart.

Final measured storage is 11,805,831,168 allocated study bytes and
74,737,639,424 free bytes, within this test's 12/60 GiB limits. All 23 P1 source
files retain identity b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f;
the formal source identity is unchanged and all 101 source Agda modules retain
safe options, with zero source postulates. Evidence, exact authorization,
source identities, cold-cache receipts and interface hashes are under
`results/canonical-state-floor60-20261018/`, especially `summary.json` and
`collected/results/canonical-state-pilot6/report.json`.

This is a 200-row partial-coverage result. Complete initial lower/upper
coverage, full assembly and the same optimal initial 16-20 strategy pair are
still required. A single case does not validate the production forecast or
memory/artifact gates. The next experiment should use multiple retained lower
parts with direct canonical imports and measure linkage/combined assembly,
without native search. This single-test authorization is consumed; it grants
no production or further desktop run. The ordinary 80 GiB floor is unchanged.

17 October, canonical-state experiment implementation prepared locally.
`tools/canonical_state_pilot6.py` now implements the proposed two-phase test:
a fresh 200-row Part34176 check with direct canonical imports, followed by
its 17-module full-map bridge. The first phase is limited to 1.5 GiB RSS and
the second to 11.5 GiB RSS under a 12 GiB hard no-swap cgroup. Each phase has
a 240-second child CPU cap, enclosed by a 540-second cap within the proposed
600-second total allowance. Only the reviewed 3+17 new modules may be checked;
all four accepted donors and the new row proof are protected and rehashed.
Any failed phase stops the experiment. It performs no native search and does
not establish the initial-board theorem or authorize production.

Ten local Python tests pass, including refusal to reuse the previous
Batch15/Root-only consent for the 200 repeated Boolean row checks. The worker
and all canonical prototypes remain unexecuted in Agda. No new desktop test
has started: the free-space floor is still not met and this new scope has no
human approval. The concrete plan is under
`results/canonical-state-sharing6-20261017/pilot-plan.json`.

17 October 13:57 UTC, resource stop after the successful bridge.
The desktop's free space has fallen to 76,566,704,128 bytes (about 71.31 GiB),
below the separately approved 80 GiB floor. Study artifacts remain below their
12 GiB cap (11,793,784,832 allocated bytes). No proof job is running or queued,
and no new computation is launched after observing the breach. No originals
are removed and neither the disk floor nor a CPU allocation is changed.

The accepted Part34176 bridge remains valid. Its final 2,671,814-byte checkpoint
is present on both machines with identical SHA256
7feeb505e357012401b4fe2b967ac6d8d6a74140047bdc79196e574ce16cfdcd.
Every archive entry was verified locally. The desktop metadata verifier passed
its archive/P1/cache assertions, then failed its final storage-admission guard;
its failed receipt is retained and charged. Therefore the backup metadata job
is not labelled accepted. A later read-only byte comparison confirms the
copied archive is identical. The canonical direct-import variant remains
prepared only; no additional Agda check or production is authorized here.
The persistent goal remains active and incomplete. Restore the agreed disk
margin before another desktop test, then review the next bounded pilot scope.

17 October, Part34176 full-map linkage is now accepted.
The separately authorized continuation checks exactly Batch15 and Root, reusing
the 15 interfaces preserved by the earlier capped run. Safe Agda accepts the
complete 17-module bridge: 52.027149 kernel CPU seconds, 62.047792 outer child
CPU seconds, 56.466502 outer wall seconds and 5.137329 GiB outer peak RSS.
Systemd records 66.306341 CPU seconds for the whole service. Its 4.258549-second
supervisor difference is excluded separately from the budget. The initial
capped attempt remains charged (270.692577 seconds), giving 332.740369 child
CPU seconds across both attempts; neither receipt is discarded.

Only the two missing modules appear as new Checking lines. All 15 prior own
interface hashes and all four donor source/cache pools are unchanged. There
are now 17 own interfaces with pool hash e244fa68ad430a8041847d1535a048c81640f5c544691c1c682d4f038a21a9c3.
The bridge specializes the already accepted 200-row fact to the complete lower
state lookup. It checks zero new Boolean rows and runs no native solver.
It proves partial coverage, with the terminal fallback data retained; it does
not prove the initial +4 value or the SAME optimal initial 16-20 strategy pair.
All original Agda sources and the 23 tagged P1 files are unchanged, with zero
postulates. No production is authorized. Receipts and audit:
`results/new-row-bridge6-20261017/resume-summary.json`.

A new untrusted source generator prepares direct canonical state imports for
future fresh row checks. In the same 200-row/503-demand fixture, source output
falls from 1,545,841 bytes and 506 modules to 81,604 bytes and 3 modules. Row
assertions and certificate bodies compare exactly after renaming state imports.
No StateData literals or re-export modules are copied into the new part.
Eight Python tests pass, including malformed metadata and preservation guards.
One earlier test-only fixture path failure is retained and charged. The new
3-module row prototype and 17-module bridge prototype have NOT been checked
by Agda. No speedup or production forecast is claimed. A future check would
repeat the 200 existing row certificates in the new representation and would
require scope beyond the completed two-module-only consent.
Prepared sources: `results/canonical-state-sharing6-20261017/direct-preparation.json`.

17 October, Part34176 full-map bridge stopped at its approved CPU cap.
The separate human consent authorized the exact17-module bridge, at most300
CPU seconds with12GiB hard RAM,12GiB study artifacts,80GiB free disk and one
heavy job. The detached desktop run used the frozen source a43b8e20 and the
same pinned safe Agda binary as its four read-only dependencies. It stopped
with cpu-limit (exit-9):270.692577 measured child-tree CPU seconds,
244.718681 wall seconds and6.561646GiB peak RSS. Systemd records
288.712637 CPU seconds for the whole service, including its supervisor, within
the300-second consent. The18.020060-second difference is excluded separately
from the remaining assembly budget without duplicating the child rusage charge.
There is no successful bridge
receipt and no new initial-board theorem. The original worker report remains
in its interrupted checking state; the final outer receipt and closure audit
are authoritative about termination.

Batch0 through Batch14 produced15 interfaces (2,607,817 bytes). Batch15 began
but has no completed interface, and Root has no interface. These are partial
artifacts from a stopped run, not a completed17-module acceptance. The run
created no new Boolean row acceptance equation and did not recheck the old
row certificates. All four donor source/interface pools match their pinned
pre-run hashes after termination. All17 generated source hashes match the
approved plan. The desktop has87.30GiB free and the study uses10.98GiB;
originals and the stopped cache remain preserved. All23 P1 sources and all
existing formal sources remain unchanged, with zero postulates.

The failed run is charged once, using the outer rusage receipt. No automatic
retry or production is launched. A concrete unlaunched continuation driver
requires a new600-CPU-second scope and the same12/12/80GiB limits. It pins the
exact15 preserved interfaces and unchanged17-module source, admits only the
two missing Checking modules, and rejects any altered donor or prior cache.
The existing source and global CPU allocations are unchanged. This next scope
fits within the remaining map-stage hour; its cost is unvalidated.
Receipts, closure audit, prepared continuation and plan are under
`results/new-row-bridge6-20261017/`. The full +4 theorem, the SAME optimal
initial16-20 pair and the whole-workflow production gates remain unfinished.

16 October, NEW lower-row pilot prepared, not launched. The untrusted
`wire_part_samples6.py` scans the already retained full native wire twice,
authenticates its complete SHA256 and file identity on each pass, and indexes
only reference states needed by selected parts. It preserves global numeric
row IDs and emits the existing conditional safe checker input. It retains no
full graph dictionary and invokes neither a solver nor Agda.

The sample is frozen before viewing new row contents or timings: parts 380,
4654, 12541, 15478, 17924, 21836, 29329 and 34176. They are distinct from all
16 previously accepted lower parts and contain 1,600 previously unchecked rows.
Four training parts precede four held-out parts. The bounded desktop worker
requires a separate human approval pinned to the exact plan. It enforces
independent cold own caches, readonly accepted generic dependencies, a
1.5-GiB RSS limit per part, and a timing prediction frozen before held-out
checks. Its proposed total is at most 900 CPU seconds from the remaining
map-stage hour, with a 3-GiB hard memory cgroup, 12-GiB study artifact cap and
80-GiB free-space floor. No full production permission follows from this pilot.

Sixteen light Python tests pass (0.427544 CPU seconds). They cover conversion,
whole-file pins, missing/forward/ambiguous citations, changed/truncated input,
output/index bounds, deterministic disjoint selection, compatibility with the
existing source generator, and refusal of the old linkage-only approval.
These tests are not Agda acceptance of the new rows. All original formal
sources, including P1, keep their previous identities. Sources, the exact
plan and receipts are under `results/wire-new-lower6-20261016/`. The new desktop
row checks remain pending scope approval; no new heavy job is launched here.

16 October, complete lower map alignment and accepted-row linkage completed.
A new safe `Game.NatMapRoute` certificate stores builtin Boolean interval guards.
Its structural soundness proof converts these guards to the existing
`Game.NatMapLaws.Route`; no checker or original rule proof is changed. Large
row-index equalities stay symbolic while closing the usable interface at map
compatibility. `Tests.NatMapRoute` includes a 6,873,000 offset and an impossible
hidden-row route. Both modules are imported by `Everything6`.

Safe desktop Agda accepts all 2,702 needed chunk routes against the complete
6,873,047-position lower map, proving lookup agreement for their 540,247 encoded
rows. The new 87-interface alignment check takes 65.869782 CPU seconds and
6.614372 GiB RSS (outer job: 78.616208 CPU / 6.746269 GiB). Its closed result is
compatibility of the ORIGINAL sparse demand map with the concrete full-map
lookup. Exact locally regenerated sources match every accepted source digest.

The human separately authorizes an at-most-300-CPU-second test of existing
row-fact linkage. Safe Agda accepts all 18 new modules, reusing the original
16 parts' 3,047 lower `TreeOK` facts with the concrete full-map lookup. Checker
cost is 46.895812 CPU seconds and 4.362675 GiB RSS; the outer job costs
56.867723 CPU seconds and peaks at 4.469498 GiB. Its log contains exactly the
18 NEW Checking lines. There is no new Boolean row acceptance equation and no
native solver invocation. All three borrowed source/cache pools remain exact.
This proves partial local-rule coverage on the full state model, not a closed
winning strategy or the initial +4 bound.

The laptop checks the two new route modules and then accepts the extended
`Everything6` incrementally in 37.792676 CPU seconds / 0.315128 GiB RSS. A prior
aggregate run reaches its 60-second CPU cap (60.223535 CPU seconds); its checked
interfaces are retained for resumption. An interrupted earlier launch has no
receipt or surviving process/cache-lock holder: its complete 62-second allowance
is conservatively withheld, not reported as measured CPU or proof acceptance.
The small earlier source errors and every failed run are retained and charged.

All 23 tagged P1 files keep identity b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f.
The only modified pre-existing formal file is `Everything6.agda`, which adds
imports of the two new safe modules. There are zero postulates or escapes.
Storage after linkage is 10.9311 GiB for study runs, with 92.7914 GiB free,
within the explicitly approved 12-GiB / 80-GiB test exception. The measured
map-stage work plus the withheld allowance stays below its one CPU hour; the
new linkage stays below its separately authorized five minutes.

The initial value, the SAME optimal initial 16-20 pair, full Boolean coverage,
and production timing/resource gates remain unproved or unvalidated. The next
required experiment is cold checking of genuinely new representative rows from
the already exported full lower wire, with selective reference indexing and
local map imports. Repeating only already accepted samples cannot establish
that production cost. That experiment is outside the present linkage-only
scope and no production is launched. No commit, push, tag or email is made.

Evidence, scope approvals, source agreement and checkpoint:
`results/full-map-alignment6-20261016/`; exact measured jobs:
`results/remote6/full-map-lower-{alignment,row-link}-20261016/`.


16 October, full LOWER data-map test completed successfully. Safe Agda accepts
`Tests.FullInitialLower6.Root`, covering 6,873,047 encoded positions in 34,366
200-row parts (the last has 47 rows). All 35,760 new data/map interfaces are
written; 2,702 accepted same-machine state literals are reused only after exact
whole-literal digest agreement with the new native wire. The 498,606,513-byte
wire is complete and pinned by SHA256. Native output remains untrusted data.

The cold own-module Agda check takes 1,005.706864 CPU / 1,008.344620 wall seconds
and peaks at 6.220589 GiB RSS. Generic dependencies and the 2,702 reused literals
are already cached; this is not an OS-cold whole-project check. All flags are
`--no-libraries --safe --without-K --cubical-compatible --save-metas`, with a
10-GiB compacting heap. The approved cgroup bound is below 12 GiB. Its complete
outer phase costs 1,216.852812 CPU seconds / 6.280083 GiB RSS. Native export and
source-generation outer costs are 829.005080 and 9.590815 CPU seconds. Each outer
receipt includes its children and is charged once; nested timings are not charged
again. The measured stage remains below its 3,600-CPU-second ceiling.

A separate capped read-only audit pins every new interface and verifies exact
35760/35760 source-to-interface coverage, unchanged map sources and the unchanged
accepted donor source/interface pool. New interfaces total 219,200,860 bytes.
At this audit all study directories allocate 11,700,256,768 bytes (10.897 GiB),
and free disk is 99,679,199,232 bytes (92.834 GiB), satisfying the approved
12-GiB artifact cap and 80-GiB floor. Originals, P1 and previous checkpoints are
retained. All core Agda sources remain unchanged; no postulates are introduced.

This establishes feasibility of importing the complete lower state map under
the pilot's 12-GiB limit. It checks ZERO game-certificate rows and proves neither
the initial +4 bound nor the SAME optimal initial 16-20 pair. The 1.5-GiB
production-part gate and previous failed timing prediction are not superseded
by this result; no production GO follows. The next bounded engineering step is
to align local accepted row facts with the full map while keeping per-part
imports local, before measuring certificate linkage. Complete certificate
production is outside this authorization.

Receipts and generated-source/cache manifests are retained under the three
`results/remote6/full-map-lower-{native,generate,check}-20261016/` directories.
The normalized report and durable checkpoint are under
`results/full-map-approved6-20261016/`. No commit, push, tag, publication or
submission email is performed.


16 October, approved full lower map pilot (historical launch record): the human explicitly approves
one new native lower export and an Agda check of data maps only, within 3,600 CPU
seconds from the existing 48-hour study budget, 12 GiB hard memory, 12 GiB total
study artifacts, and at least 80 GiB free disk. These dated limits supersede the
pending proposal below for this experiment only. The controller keeps the normal
limits for unrelated jobs, checks the cumulative stage CPU before each launch,
and monitors allocated storage while running. The native export is detached on
the desktop under `othello6-full-map-lower-native-20261016.service`. Subsequent
source generation and the cold map check have separate capped reservations.
No complete game-row verification or production is authorized. The original
proposal and predecessor checkpoints remain immutable. Approval and receipts are
under `results/full-state-map6-20261016/` and the corresponding `results/remote6/`
phase directories. No initial value or optimal-pair theorem follows from this test.


16 October, full state-map preparation: the pinned full initial-layout runs
were counts-only and did not request a complete wire export. The reviewed lower
report counts 6,873,047 rows / 34,366 parts and predicts its exact wire length
as 498,606,513 bytes. Its previous native census costs 688.801684 CPU seconds;
materialization adds unmeasured I/O. No new native search or export runs here.
The original native executable, C source, immutable TT and protected sidecars
are rehashed successfully. No claim is made about every unreviewed archive.

`tools/full_state_map6.py` is a streaming, untrusted source emitter for the
measured contiguous 200-row partition. It pins the whole wire digest and row
count, bounds records/output, rejects malformed/truncated input, and exposes no
complete Root after a failed conversion. It emits text-only state modules and
bounded balanced map groups. Existing state chunks can be imported only when
their literal digest matches exactly. It copies no proof interface. Four final
Python tests pass. Safe Agda accepts a data-map smoke check from an existing
12-row real native fixture in 0.181304 CPU seconds / 0.123920 GiB RSS. That
fixture is regrouped for data typing only: no certificate-ID correspondence,
game-row acceptance, full-scale performance or initial bound is claimed.

The complete lower export needs 475.51 MiB before source/cache generation;
preflight finds only 45.01 MiB below the current 10-GiB study artifact ceiling.
The desktop has 93.78 GiB free, below the normal 100-GiB floor. The current
short-comparison resource exception also cannot cover its prior 11.5-minute
native cost. A concrete resource proposal is recorded, not launched: at most
one CPU hour from the existing budget, 12 GiB hard memory / total study artifacts,
80 GiB free disk, one heavy job at a time, only lower data export and map imports.
The human is asked to approve this expansion. Until an answer, current caps
stay unchanged and no full export, full-map check or production is authorized.

All core Agda and 23 tagged P1 files remain unchanged; postulates stay zero.
The initial +4 theorem and SAME optimal initial 16-20 pair remain unfinished.
Records and proposal: `results/full-state-map6-20261016/`.


16 October, combined two-sided sample assembly: safe Agda accepts a cold
collector of both existing partial roots. It loads 6,961 distinct dependency
interfaces spanning 6,061 demanded state chunks (1,211,972 encoded state rows),
with 6,172 owned checked rows
(3,047 lower and 3,125 upper). These rows were already accepted; this checks
their joint assembly and adds no initial-board coverage. Checker cost is
9.981656 CPU / 10.024219 wall seconds and 1.692024 GiB peak RSS. The new interface
is 200,108 bytes; no dependency interface is copied or altered. The checker log
contains only the new collector's Checking line, confirming cached dependencies.

A plain sum of the two old separate-root costs predicts 7.405426 seconds. The
joint result is 34.7884% higher, outside a +/-30% band. This simple
predictor is not validated; no whole-workflow forecast or production gate is
claimed. Full-size import memory, all initial rows and the SAME optimal initial
16-20 pair remain unverified. The 10 GiB artifact and resumed 300-second comparison
caps stay in force; the authoritative study ledger remains 48 CPU hours.

Directly including two complete source roots first fails on ambiguous Prelude.
A first mount-view candidate hides the upper-specific directories too and fails
with FileNotFound. Both failures and their actual CPU are retained. The corrected
view opens original directories before masking the duplicate upper source tree,
then mounts them read-only through directory file descriptors. A canary verifies
visible upper namespaces, hidden duplicate Prelude and EROFS on writes. Duplicate
source/interface bytes are checked identical, all donor build locks are held,
and donor source/cache hashes remain unchanged. `namespace_view` in
`tools/readonly_dependencies6.py` exposes this exact checked launcher; three
contract tests pass. All core Agda and 23 tagged P1 files remain unchanged;
postulates stay zero. Records: `results/joint-sample-assembly-fd6-20261016/`.
No production, publication or email.


12 October, global alignment and extrema continuation: safe Agda accepts
CLOSED lower sample coverage for the 4-part and 8-part global lookup models
(1.513968 and 17.354923 nested CPU seconds; 0.303246 and 1.794640 GiB RSS).
The 16-part monolithic model exhausts its 2700-MiB heap on the desktop;
the accepted earlier stages, all 32 sampled part proofs and every failed
attempt are preserved. Explicit route-alignment arguments fix the earlier
inference timeouts. The module-splitting pilot accepts all103 targets and CLOSED partial
coverage of all16 lower sample parts (3,047 owned rows and 2,702 demanded chunks):
477.787169 nested CPU seconds, 2.104958 GiB maximum checker RSS, with no sampled
part rechecked. Its terminal outer receipt records 594.638526 CPU seconds.
Both lookup-compatibility premises are discharged. The initial root and complete
coverage of imported unowned states remain unproved.

The controlled 1/4/8-worker real-slice throughput test accepts all13 checks.
Measured effective slots are 1.00/3.85/6.53; the eight-worker peak is 7.143257 GiB
inside the 15-GiB slice. Each worker starts with private sources/cache copies
and a cold own target. Only closed batch inputs are subsequently shared, with
source, interface and receipt bytes preserved. A quadratic post-check cache
hash loop is corrected for future runs; it does not change recorded check timings.
The upper global alignment prediction is frozen before launch at
`results/initial-upper-alignment-forecast6-20261012/report.json`: 720.843446 nested
CPU seconds. `initial-upper-global-shards-20261012` accepts its first84
alignment targets (505.440108 nested CPU seconds), then stops at the artifact
guard during a temporary maintenance-journal allocation. Its terminal receipt
records 614.321743 outer CPU seconds; there is no failed Agda target in that
prefix. Exact closed-cache sharing reclaims 84,803,584 bytes, then 54,157,312 bytes
from the closed upper clone. Detached `initial-upper-shards-resume-20261012`
preserves its84-target prefix and accepts another36 before the storage guard.
The final private-copy preparation also reaches the guard before any Agda check.
Chained source-root guards preserve all120 accepted targets. Verified lossless
archival reduces 65,266,879 journal bytes to 8,569,622 bytes; primary checking
receipts, sources and proof interfaces remain intact.

`initial-upper-shards-finish-fixed-20261012` accepts the final3 targets and CLOSED
upper partial Root. All123 upper alignment targets are now accepted, covering
3,125 owned rows and 3,359 demanded chunks, with none rechecked. Complete nested
CPU is 710.970664 seconds against the unchanged 720.843446 prediction: 1.3696%
below, passing the prospective ±30% criterion. Maximum checker RSS is 2.731224
GiB; the final Root uses 14.039065 CPU seconds. Both lower/upper sample global
alignments are checked; neither establishes complete initial-board coverage.
All jobs in this completed alignment batch are terminal and collected. The
full-workflow/artifact and initial-root production gates remain pending.

Both native extrema passes are complete and collected (2,724.392805 CPU seconds).
They identify lower parts 32942/34263 and upper part 34183. All twelve original-
rank 50-row slices of those parts accept in safe Agda: 600 owned rows,
140.737918 nested kernel CPU seconds and 1.069580 GiB maximum checker RSS.
The native data supplies no proof premise. Closed exact source/interface
sharing reclaims 183,271,424 bytes for this continuation, preserving all
bytes, modes, timestamps and receipts; future writable caches use private
copies. Four module-splitting generator guards and five slicing guards pass.

The initial +4 theorem, SAME optimal initial 16–20 pair, complete production
gates and private package remain unfinished. This is progress under the
48-CPU-hour ledger; P1's 23 tagged sources and the safe mathematical core
remain unchanged, with zero postulates. The frozen row-only forecast and
its complete holdout result are unchanged. The observations below are dated
history; no publication, commit, push, tag or email occurs.

12 October, checked initial samples: **all 32 sampled parts are Agda-checked**
(16 per bound, 6,172 owned rows). The prospectively reserved eight holdout parts
per bound all accept. Lower holdout CPU is 78.922295 seconds against the frozen
80.373636 prediction (1.8057% below); upper is 98.246057 against 98.612734
(0.3718% below). Both complete per-side row-cost checks meet the fixed ±30%
criterion. Holdout maximum part RSS is 1.026546/1.397984 GiB. No accepted
training part is rechecked. The independent same-desktop audit verifies
source, compiler, flags, closed donor interfaces and both complete residuals
in `results/initial-lazy-offline6/validation.json`.

The conditional 4/8/16-part assembly pilot accepts on both sides, reusing all
sampled part proofs. The lower three stages total 2.908564 nested CPU seconds;
upper total 3.425929 nested CPU seconds. Assembly leaves per-part demand,
combined state and combined body alignment as explicit premises. This measures
real import/proof linkage; global self-alignment and the initial root remain
unmeasured. Largest sample assembly is below 0.5 GiB RSS. Five generator guards
pass. Full native layouts also contain unseen parts with up to 1,263 lower /
1,495 upper direct dependencies, beyond the sampled range: targeted worst-case
checks or smaller proof slices are still needed before production.

The frozen row forecast remains unchanged at
`results/initial-lazy-forecast6-20261012/report.json` (SHA256
`49de1a46cb3d0d7f31f0ab5d910465de38a21edbef2335ec7984746fe127acf3`).
It validates row costs only; measured throughput, complete global assembly,
full artifact volume and the initial optimal pair remain outstanding. The
original 9 October forecast remains inconclusive. P1's 23 tagged source files
and the safe mathematical core remain unchanged, with zero postulates.
The initial +4 theorem, SAME initial optimal 16–20 pair and private submission
package remain incomplete; there is no production GO, publication or email.
All jobs in this dated batch are terminal and collected. Source remains
laptop-authoritative; no AI coding session was migrated. Earlier notes below
retain their historical scope.

12 October, after initial-layout training: both native extractions are terminal,
accepted and collected. Their complete line-pinned layouts contain 34,366 lower
parts and 34,932 upper parts. The 16 samples per side were selected before
extraction: eight training and eight held out. Native counts remain untrusted.

All eight **lower training parts and all eight upper training parts are accepted
by safe Agda**, covering 3,200 owned rows and their conditional linking exports.
The first two lower parts are reused with their original source/compiler/cache
receipts. Maximum part RSS is 1.397385 GiB lower and 1.416576 GiB upper.
These isolated checker facts do not establish the initial-board guarantees.

The prospective row forecast is frozen at
`results/initial-lazy-forecast6-20261012/report.json` (SHA256
`49de1a46cb3d0d7f31f0ab5d910465de38a21edbef2335ec7984746fe127acf3`).
It predicts 80.373636 lower and 98.612734 upper holdout CPU seconds. Five
forecast guards and five holdout-runner guards pass in metered runs. The first
holdout test assertion mismatch and a launch before the forecast transfer
completed are retained; no Agda holdout ran in that failed launch. The transferred
forecast now verifies on the desktop, and detached
`initial-lower-holdout-fixed-20261012` / `initial-upper-holdout-20261012`
check only the eight reserved parts per side in private copies of the accepted
training caches. Acceptance and the fixed per-side ±30% CPU criterion remain
pending until their terminal receipts and reports are collected.

Nine lower continuation tests pass. Lossless closed native archival recovers
514,965,504 allocated bytes without altering accepted proof sources, interfaces,
receipts or the transposition table. The 48-CPU-hour ledger remains authoritative;
part/diagnostic assembly/slice limits remain 1.5/3/15 GiB, study artifacts 10 GiB,
and launch free disk 100 GiB. The complete production gates additionally require
measured throughput, assembly scaling, ≤168 predicted wall-hours and ≤12 GiB
final assembly RSS. The row forecast supplies no production GO.

P1's 23 tagged files and the safe mathematical source identity remain preserved,
with zero postulates. Initial 6×6 +4, the SAME optimal initial 16–20 pair and
private submission packaging remain unfinished. Detached finite checker jobs
survive laptop shutdown; the coordinator does not migrate to the desktop.
No commit, push, tag, publication or email occurs. Earlier dated observations
below retain their historical scope; query status for current service state.

12 October continuation: the **uniform-lazy lower/upper real-game assembly
pilot accepts all 16 targets**, including both original-rule Roots: 5.087585
nested kernel CPU seconds and 0.218502 GiB maximum target RSS (14.464276 outer
CPU seconds). The independent high-ID part fixture also accepts all eight
targets at IDs around 6.87 million: 2.528719 nested CPU seconds and 0.205620
GiB target RSS. That second fixture proves conditional links, not an initial
bound. Three sample-emitter tests and five sampler codec/guard tests pass.

The native sampler matches the complete small exporter, exact partition counts,
numeric bodies and demanded state chunks, with 153 rows replayed against the
scalar game rules. Its 30 cases include one rejected invalid +37 threshold;
four native resource/error fixtures reject incomplete output and protect an
existing artifact. The earlier validation-driver failure is retained and
charged; the native compiler itself succeeded. The accepted fixed validation
report SHA256 is `a1071a4ac2a65076daeee3f838903b2475e881ebf115062179f4994cd00e2209`.

Detached `initial-lazy-samples-20261012` now extracts 16 prospectively fixed
part samples from each complete line-pinned initial bound. Eight per side are
training cases and eight are reserved for later kernel holdout checks; no cost
forecast is frozen yet. It stores selected rows and demanded state chunks,
not the full native graph. Caps: 4,300 total CPU seconds, 2,100 per native
bound, 8.5 GiB supervisor RSS, 16 MiB output per bound. The same 10-GiB artifact
and 100-GiB free-space guards remain. The finite service survives laptop loss;
source editing remains with the coordinator. Initial Agda +4, the SAME optimal
initial 16–20 pair, production GO and submission packaging remain incomplete.
See `results/remote6/initial-lazy-samples-20261012/job.json` for the exact frozen
source, command and reservation; current service state comes from status, not
this dated note. P1 and the safe mathematical core remain unchanged.

10 October, completed desktop check: **all 267 parts, all 31 hierarchy
nodes and Root of the 53,217-row numeric lower descendant are Agda-checked**.
`nat-lazy-finish-20261010` is terminal, accepted and collected. It preserves the
261-part prefix and checks the final six parts and complete assembly. Outer
CPU is 289.285175 seconds, wall 271.050905 seconds and supervisor peak RSS
2.098064 GiB; nested kernel CPU is 232.032310 seconds. Assembly peak is
2.035168 GiB, below the 3-GiB diagnostic cap. The root exports an original-rule
White lower +4 guarantee **from the 14-disc descendant**. It does not establish
the standard initial-board theorem or the initial optimal 16–20 pair.

The final audit authenticates the terminal receipt, all accepted phase
sources/flags/compiler/interfaces and the original-rule root statement, and
scans all generated safe source for postulates and escape pragmas. Report
SHA256: `02789615690a064bc952fa1a6ba2e5976d3655fc01224905b746d89855c0f57f`;
checked source: `ff9fcfde3245b1356f86abac6a0d535fde72265c922253c3d897b710b30e4e1d`.
The audit record is `results/remote6/nat-lazy-root-audit-20261010/`.
Identical closed-run source/interface sharing recovers 68,853,760 bytes without
changing proof bytes, timestamps or receipts. Future writable roots use private
copies. The simpler uniform-lazy generator has five metered passing tests;
its next validation is a real lower/upper original-rule assembly pilot.

The ledger allowance remains 48 CPU-hours. P1's 23 tagged source files and the
95-file safe core identity are preserved. Zero postulates remain. Initial +4,
the SAME initial optimal 16–20 pair, complete production gates and private
submission packaging remain unfinished. Older observations below are dated
history; their active-job labels do not describe the current service state.

At 2026-10-09T15:23:01.846447+00:00, detached `nat-lazy-descendant-20261009` is active on the
desktop, reusing all 243 accepted parts and generating only the next unchecked
parts with the safe lazy decoder. 243 parts are observed accepted. The job
then checks the unchanged 31-node hierarchy and Root; those acceptances remain
pending. Outer/nested CPU caps are 1,800/1,600 seconds; part RSS is 1.5 GiB,
diagnostic hierarchy RSS 3 GiB, and the slice is 15 GiB with swap disabled.
Sleep targets are masked and user linger is enabled. The queue survives laptop
shutdown; coding still runs through the coordinator. See
`results/nat-lazy-offline6/live-observation.json` for this dated observation.

The continuation passed nine provenance/cache-isolation tests and an actual
desktop preflight. Additional closed-run duplicate sharing recovers 56,942,592
bytes of source/interfaces and 24,846,336 bytes of frozen sources; identities,
timestamps, modes and receipts are preserved. New writable roots use private
copies. The initial theorem, initial optimal pair and production gates remain
unproved.


Current records, 9 October, after the collected Part242 repair: **243 numeric
parts are accepted; hierarchy and Root remain unchecked**. Both services below
are terminal and collected. The final service's report retains its last
`checking-remaining-parts` checkpoint label; the terminal outer receipt and
failed child record establish its memory stop, not a running proof job.

| Run | Accepted scope / stop | Outer CPU seconds | Report SHA256 |
| --- | --- | ---: | --- |
| `nat-descendant-final-20261009` | Part0–241 accepted; Part242 heap exhausted, exit 251 | 797.022737 | `dfc56661c913c390198291b1eec111f9fcfa4dc0b3e4ae6d7c675223a7497e53` |
| `nat-lazy-repair242-20261009` | 149 repair targets accepted; original conditional Part242 export checked; 243 total parts | 180.749937 | `38265722a01b7ce31cb18553501084ad9de2c7703e7119cb9a7e92c990081547` |

Collected reports are in
`results/remote6/nat-descendant-final-20261009/artifacts/results/nat-final6/report.json`
and
`results/remote6/nat-lazy-repair242-20261009/artifacts/results/nat-lazy-repair6/report.json`.
Final interface map SHA256:
`2ca675ed5c34ed475c52e64b14f9c7bde0a4d48cb6e8dfd45b673d81267de854`;
terminal actual receipt SHA256:
`eb778045ddb811792a55181588bceda955f5b0ed0b97a76eba239c4562e130a2`.
The failed Part242 consumes 61.640891 CPU seconds, 61.748894 wall seconds and
1.444786 GiB recorded peak RSS; its heap exhausts at 1,415,577,600 bytes
(1,350 MiB). The failure and its logs remain preserved and charged.

The repair checks the lazy checker, shared lazy family, generic `RepairBridge`
first, then 145 actual `StateEq` vector equalities and the original conditional
Part242 export after its lazy Boolean check. Accepted Part242 consumes
18.412866 CPU seconds, 18.449438 wall seconds and 0.783798 GiB RSS, exit 0.
Nested CPU is 78.732017 seconds, included in the outer 180.749937-second charge;
outer wall is 169.065052 seconds and RSS 0.822170258 GiB. Repair map SHA256:
`c6c0314053b003f3c6aea004dfd972988dcec75ef7b18c7e734d07441fac3982`.
Frozen outer source SHA256:
`b38aabca931362901c5929d0a4f6a2de6559caae86381a1b2e2a3dfa43c2d2d4`.
The inherited 1,225-file checked-source epoch remains
`86ffedf14980a40ea464fa6110db9d37130015d166ff31c39a361b5aed126233`;
the new 1,373-file repair epoch is
`42d11b401de02a2a883e594b30bf3b76b1a7f02f0d2137a6a4eadc1c47a849eb`.
Only previously unchecked Part242 changes, with new helpers added. Original
state/body data and earlier accepted sources/interfaces are unchanged; inherited
checks are not attributed to the new whole-source hash. Completed repair child
logs are gzip round-trip archived with hashes; interfaces/data/source persist.

The original prospective 66-target suffix forecast is **incomplete/inconclusive**
because held-out Part242 fails memory. Lazy timings cannot replace its original
observation, nor can post-observation exclusion turn it into a passing gate.
`tools/validate_nat_forecast6.py` has eight guards for completeness, pinned
population, source, flags and timing provenance. Generator tests number four;
heap-failure recovery has 13, including nine prior recovery fixtures. Metered
records are in `results/nat-validation6/records`. No production GO is issued.

Recovery records: `nat-final-closed-allocation-20261009` reclaims 54,464,512
immutable duplicate bytes in 1.224958 CPU seconds. The first
`nat-repair-log-headroom-20261009` fails its 450-candidate guard before archival
(0.995083 CPU seconds), preserved and charged. Successful
`nat-repair-selected-log-headroom-20261009` archives only accepted finished child
logs from four terminal runs: 29,459,331 raw / 2,776,429 compressed bytes,
1.894317 CPU seconds, 10,641,321,984 allocated artifact bytes before repair.
Failed logs and all proof/data/interface/source bytes are preserved.

The current 95-file Agda/library identity remains
`729fae0e8b475a48630d4177fd1312fe982d09b87692f15dfd1ec446c40e3c40`;
all 94 source modules are safe and there are zero postulates. All 23 tagged P1
files retain `b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`.
Latest Everything6 cold acceptance costs 60.485060 CPU seconds / 1.593048 GiB
RSS, starting with zero interfaces and producing 88. The legacy complete
seven descendant guarantees and late-position 16–20 theorem remain intact.
The authoritative laptop allowance is 48 CPU-hours (172,800 seconds), with
actual outer charges and read-only desktop copies. There are no desktop proof
jobs pending launch; the Part243–266, 31-node and Root driver is in preparation.
Initial +4, SAME optimal initial 16–20 pair, root feasibility, production GO
and private packaging remain incomplete. Older records below are historical.


Historical records at 9 October, 13:46 UTC: the new 95-file Agda/library core
identity is `729fae0e8b475a48630d4177fd1312fe982d09b87692f15dfd1ec446c40e3c40`.
All 94 source modules carry safe/without-K/cubical-compatible options; scans
find zero postulates or proof escapes. All 23 tagged P1 bytes retain identity
`b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`.
The newly extended Everything6 accepts cold on the desktop: 60.485060 CPU
seconds, 1.593048 GiB RSS, exit 0, zero starting interfaces. Its source record
is `6b78bc4cdd5b8a6736b2cc652dc0f1d00fc537cf553cf884835a2939d93cd62b`. Closed predecessor
checks keep their original 93-file core and full checked-source identity
`86ffedf14980a40ea464fa6110db9d37130015d166ff31c39a361b5aed126233`.

| Run | Accepted scope | Outer CPU seconds | Report SHA256 |
| --- | --- | ---: | --- |
| `nat-descendant-20261009` | Family and Part0–171; Part172 CPU-censored | 3518.659479 | `a91cd4cff66566676ca388c9d2c3d3ee6e19c96b8d1d0cb39c2979709b11eab9` |
| `nat-descendant-finish-20261009` | Reused 172 parts plus Part172–224; Part225 CPU-censored | 1955.577965 | `c0127392ecf2a80f09cc9e91f2fd88684968d447a9f2c103a51862c938fa3a27` |
| `lazy-indexed-pilot-20261009` | Nine safe targets: fixtures, two real strict/lazy comparisons and two vector equalities | 110.304259 | `be4245b2672c1daf7fd0fb96e4ce4a96fdd1872f7c93ad172c3d8d48a758b22f` |
| `nat-row-forecast-20261009` | Native prospective row-only forecast; no new proof | 0.531134 | `91c12a35405fe82b7592b99b5d7843f1fee39149e1d9ac410b8d9c88bccfb1a7` |

The secondary interface-map file is
`f72f41c45b5e2a4d1ad1adde7fa68ddccf51ad980e17dd523dd9f9b9dec0a151`.
Its terminal outer receipt is
`afbb02a0b164e295a9f654da6a86fedd415cd3c382d41dd7eb5699734c1b4bcf`.
The lazy pilot interface map is
`7f5dcddcf1ec61a0f49233eb721f8bbf727babfa54a44339d25181d712cd8206`.
The original-vector equalities cost 0.526486 / 0.524091 CPU seconds. Strict/lazy
Part60 costs 23.136036 / 15.698397 CPU seconds, 0.857273 / 0.465439 GiB RSS;
Part231 costs 37.092931 / 20.028886, 1.275654 / 0.610863 GiB. All targets use
safe flags and the same desktop compiler. These are small comparisons only.

Exact closed duplicate recovery records are
`nat-primary-lazy-closed-allocation-20261009` (1.224994 CPU seconds,
28,770,304 bytes reclaimed) and `nat-prefix-closed-allocation-20261009`
(1.188289 CPU seconds, 47,108,096 bytes). Both verify unchanged sources,
interfaces and protected receipts. No accepted proof is deleted or rechecked.
At that launch, `nat-descendant-final-20261009` holds a 3,002-second kernel
reservation for the unfinished prefix suffix and hierarchy. Its
frozen outer source is
`949033a0c50793569047359401fd53a99a49a817698b3c426190dfeb29db3be2`.
At that checkpoint its terminal result is pending; the collected result is
recorded above. Row forecast validation requires all 66 fixed
held-out targets and does not validate whole-workflow cost or production.
Initial +4, its optimal initial pair and production GO remain unfinished.
Older records below retain their dated scope.

Historical checkpoint at 9 October, 12:28 UTC: every new numeric core module is safe,
without-K and cubical-compatible. The 93-file Agda/library identity is
`f32fd0adda8addd9f55a00170f17913c056fa8ed469f6f55aab7885004f6a891`.
All 23 tagged P1 source bytes remain unchanged:
`b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`.
Core scans find zero postulates or proof escapes. All acceptance records name
the source, compiler hash, flags, cache state, CPU, RSS and exit status.

Accepted and collected numeric experiments:

| Run | Scope | Outer CPU seconds | Report SHA256 |
| --- | --- | ---: | --- |
| `nat-indexed-pilot-20261009` | Rejection fixtures and balanced/numeric real parts 60, 120, 231 | 184.104485 | `1246d9c59ece7d27c461795b7722c97d19cc402786234ef8ade2702f4287ebcf` |
| `nat-shared-parser-pilot-20261009` | Same real comparisons with shared original state decoder | 184.688749 | `bb40c00ccd9cc721e3407eec35e6ec77ae7577193866d951b56aaa2e345cf565` |
| `nat-assembly-spike-checked-20261009` | Safe assembly fixture and updated Everything6 | 21.358566 | `5728ccaaee98de74d4d4980ead753eb249fbc2822a35f3ef1902c6be5accf155` |
| `nat-tree-pilot-fixed-20261009` | Generated hierarchy, 16 targets across both original-rule late bounds | 13.918766 | `29539abe145aa171a38e94c243cff55776f78426d54cf668abe863b68cbdd9ae` |

The desktop Everything6 target costs 17.725466 CPU seconds / 0.363827 GiB RSS;
its assembly fixture costs 0.756020 / 0.218262. The laptop cold assembly fixture
also accepts: 63.126902 / 1.402756. No desktop interface is copied to the laptop.
The optimized Part231 comparison reaches 1.397827 GiB RSS, so numeric IDs do
not establish a uniform memory gain. The generated numeric pilot checks late
bounds only, not the initial value or a new initial optimal joint play.

The balanced donor `indexed-slices-resume-20261009` retains all 267 accepted
parts and 30 hierarchy nodes. Report:
`824107fa5f818b6daec3010df3d32191cc4b8bcd59d5252617208fdd2a44193c`;
interface map:
`e9915310b42a02180a1fafdab3c0a197636b0b18355b8b42c1d3da7c36041fa4`.
It stops at the artifact guard, not an Agda error. `indexed-root-finish-20261009`
then fails during Node0 import loading with exit 251, 4.233023 child CPU seconds
and 2.608391 GiB RSS. Its 6.050075 outer CPU seconds are charged. Report:
`aff12b0cf6fde4a52dfe23dcdd6dbb25082eb10d97731e5e8df5eb4d017db98f`.
The final balanced root is not attempted, and the legacy accepted root persists.

The detached `nat-descendant-20261009` is a bounded full-descendant experiment,
not initial production. Its frozen outer source is
`0fc7c8998d243a59c580201bc9cd22510e9a10690d1408dedd6d90f6243b541d`;
source archive:
`1dfe31df155da2fa4c3d684415b9c6570430a82f32c5f30c4f10d9907bd552b9`.
At 12:01 UTC it has 19 numeric parts accepted; terminal assembly results are
pending. Every actual terminal receipt is collected exactly once. All template,
preflight, heap and CPU failures remain recorded and charged. Exact closed
allocation recovery and round-trip native archival change no proof bytes.
A second finite service, **`nat-descendant-finish-20261009`**, waits for the
first service to close. It authenticates the exact descendant source, compiler,
flags and accepted interface prefix, and resumes only after a CPU stop. A proof,
memory or storage failure stops the follow-up for diagnosis. Its independent
reservation is 2,002 CPU seconds; caps are 2,000 outer / 1,800 nested CPU seconds,
14,800 wall seconds, 1.5-GiB parts and 3-GiB diagnostic hierarchy. It needs no
laptop connection. Nine recovery regressions pass, including safety-flag and
live-predecessor rejection. Both terminal outer receipts must be collected once.

Initial +4, its optimal initial pair, production GO and packaging remain
unfinished. Older identities and observations below are historical.

Latest accepted split recovery, 9 October: `indexed-slices-headroom-20261009`
checks four 50-row Boolean facts plus complete original-ID recombination.
Peak slice/parent RSS is 0.620644 GiB; nested/outer CPU is
26.471766 / 32.284105 seconds. The unchanged accepted context is reused.
Report SHA256:
`eeb949ccde8663ddf269a1486fe775b05609bb803e445a1cd94ab6b950c1f950`.
Map-file SHA256:
`f18115eb37c8570e7b888cff8383205cbda400c236e86168984911c37e856e42`.
Checked-source SHA256:
`f88c0421efa18ca51ff809962c3d543c51b5fb1fad84fb593c148f4b13978b32`.
The initial numeric-name failure costs 15.088896 outer CPU seconds; the
corrected pre-check storage stop costs 0.608894. Both remain in the ledger.

`indexed-slices-resume-20261009` reuses all 233 accepted parts. Its first
cold target, updated `Everything6`, accepts with 19.819090 CPU seconds /
0.352985 GiB RSS. All checked sources are safe, without-K and
cubical-compatible, with saved-meta interfaces. The frozen checked source is
`324be42f91e0a6cbbb3a33a61e7d221c833cb88f30c0af1d276dd30166efff9a`.
The observation at 09:44 UTC has 237 accepted parts. A terminal receipt is
still needed for the complete remaining-parts/hierarchy run.

All 23 P1 source bytes match the tag:
`b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`.
The current 86-file Agda/library identity is
`572dcd58c090e27e35b772112820764724065e2f058a3cdeebf70453a3afcab1`.
Core scanning finds zero postulates or proof escapes. The bounded native
interface census finds no saved-meta bindings and six optional
`RewritesNothing` documents in the shared-instance samples. Its specific
warning-filter variant accepts with own interfaces 96,725 / 105,731 bytes;
these measurements are not proof premises or full production forecasts.

Completed logs are archived with verified gzip round trips; failed logs,
receipts and proof bytes stay unchanged. Closed source/cache hardlinks require
exact bytes, hashes, mtimes and modes; writable checking roots use private
copies. The initial theorem, optimal initial pair and production gates remain
unfinished. Earlier service observations below are historical.

Earlier hierarchical continuation, 9 October: `Game.BalancedDemand` accepts cold
on the laptop, 4.020558 CPU seconds / 0.154705 GiB RSS. The safe helper aligns
sparse data demands structurally with a symbolic global state resolver.
`indexed-tree-pilot-20261009` accepts all ten phases, including lower and
upper hierarchical roots, an actual same-strategy original-rule 16–20 play
from the late forced-pass position, and the extended `Everything6`.
Outer CPU is 32.091387 seconds / 0.380280 GiB RSS; nested CPU is 24.464109.
Final report SHA256:
`3c8164c99c77ea5fec2aeff47b1a4e2857e90154fb162d5449b47db651651000`.
The 85-file Agda/library identity is
`8bf6d7140e7917c7cf4b55896ba4b72b87023e7eb1f72b62737224536ac702b4`.

`indexed-wire-pilot-fixed-20261009` is now terminal and collected. Part0–171
accept; Part172 exhausts the last 3.020480 seconds of the nested allowance,
without producing its own proof interface. Nested CPU is 3,300.075346 seconds;
the outer receipt charges 3,625.038225 seconds once. No assembly was attempted.
Final report SHA256:
`3ebe3636d784dc95ba2a4f31011a82e370ab1fda023df0770185017cc6ef4aa3`.
Final interface-map file SHA256:
`597112f8c9c3bfb5a5763d9c7464737b7d582fa42a4433ef5a1924131d4b8d4d`.
All 172 accepted proofs are reused by the detached
`indexed-wire-resume-20261009`; it checks only the remaining parts and new
hierarchical modules. Its source snapshot is
`e5c8d67171067b3987a8edd48932a18838800a4e990d70c3e25dc265349b0a63`.

Two serialization experiments also finish and are collected. Normal mode
(`indexed-cache-mode-20261009`, 99.798383 outer CPU seconds) changes the two
measured part interfaces by less than 0.15%; report SHA256:
`7c6a36c047022f57557b79b9a360bb1755f58fae65b03d6182e6ee94f0a280f3`.
The source-local `-WnoUnsupportedIndexedMatch` experiment
(`indexed-warning-mode-20261009`, 53.135904 seconds) accepts the same Part60
and Part120 statements, reducing their own interfaces from 287,246 / 296,084
to 123,884 / 133,663 bytes. Report SHA256:
`c33de5896ca5bca467469d896241c5e3354255d824b6dddf1027ddce4f60eab9`.
This suppresses optional warning documents; all safe checking flags and saved
meta settings remain. The experiments have different dependency warmth and
do not supply a matched CPU comparison or a full artifact forecast.

Recorded lossless archives and exact duplicate allocation recovery affect only
closed frozen roots. Source bytes, mtimes, modes, proof-interface hashes and
actual receipts remain unchanged. Future writable roots use private `copy2`
copies. P1 remains the exact 23-file tagged identity
`b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`;
the core has zero postulates. The initial value and initial optimal pair remain
unproved, with no production GO. Earlier entries below are historical.

Latest independent-linking continuation, 9 October: the data-only job completes
and is collected, exit 0, 2,514.882605 outer CPU seconds / 0.615864 GiB RSS.
All 267 local Boolean parts accept, with 2,201.870592 total nested CPU seconds;
part-only old/new costs are 2,956.401151 / 2,199.811253 seconds. Final report
SHA256: `3cfbafef0089fdc3d214a7925b503f1254f4dcdfb6fd8ed09cc758d8e70f8b02`.
The experiment omits indexed order, compatibility, global soundness and joint
play. Historical data and accepted semantic interfaces remain unchanged.

`Game.Balanced` and its structural order/accessibility fixtures accept cold on
the laptop: 3.395192 CPU seconds / 0.182373 GiB RSS. `Game.Spine` and fixtures
accept cold: 3.343494 seconds / 0.182331 GiB. The compact fixed-vector indexed
decoder and rejection fixtures accept cold: 5.727592 seconds / 0.217834 GiB.
The decoder rejects malformed, missing/extra rows, forward/self references,
invalid tags and missing/wrong state imports; fallback data supplies no proof.

`indexed-spike-desktop-20261009` safely accepts three independent parts,
well-founded assembly, explicit spines, negative fixtures and the extended
`Everything6`. Final report SHA256:
`f8f27f52b672e6b32913f3c2ca81e80511f678a4ac38e8de1c3b76d4b3440125`.
Outer CPU: 71.278651 seconds, RSS 1.484520 GiB; nested CPU: 63.334932.
First part is cold, 41.152132 seconds / 1.457489 GiB; later parts reuse data
interfaces and import no earlier part proofs. Assembly costs 0.690527 seconds /
0.298115 GiB. The actual same certificates' completed 16–20 play is checked
from the late forced-pass position, with an opaque imported off-path witness.
Original-rule guarantees and completed-play/count equalities are constructed.
This proves no initial-board claim. The checked 84-file core identity is
`a19f9a6e8849cdb4160bbd54b67bb9845f1d725432cdcf264f60b69dd165932a`.

The complete descendant indexed pilot retains a pre-kernel file-path API failure
(0.619234 CPU seconds, collected); a new regression plus the four converter
fixtures pass (0.093158 seconds). Its corrected detached label is
`indexed-wire-pilot-fixed-20261009`. The additional symbolic data-leaf compatibility
helper is first checked there; do not equate its newer core identity with the
already accepted spike. All tagged P1 files and zero-postulate requirements remain.
Initial value, initial optimal pair and a production GO remain absent.

Latest accepted continuation, 9 October: `wire-cut-ply10-resume-20261009`
authenticates and reuses Part0–167, then safely accepts Part168–266 and the
original-rule lower 14-disc root assembly. New nested CPU is 1,550.960089 seconds;
new outer CPU is 1,713.755316, charged once. Final report SHA256:
`e16cd54b53d86fbed2c24466d6a2611124f858f42dcd9bc9013305579adaf08a`.
Final private interface-map digest:
`51128795fa2c08bd66527c22f97c9330b1c0dcff7154b2f8e0e534fc38be0184`.
Root assembly is cold for its target, exit 0, 1.166951 CPU seconds and
0.498760 GiB RSS. Historical source, interfaces and receipts remain unchanged.
This establishes a descendant bound, not the initial board or joint theorem.

`wire-layout-initial-20261009` completes both initial line-pinned native layout
measurements, 1,457.528206 outer CPU seconds / 4.711498 GiB RSS, source unchanged,
exit 0. Final driver report SHA256:
`a8165f303ee866200e52047f86af87b77a0656ff3a53f2549913c8eb713be4ec`.
Lower / upper full report SHA256:
`691464f5bd39a6c47ec92d37d8fd16672b64933eddfa848533b1cbe450100a36` /
`8549989821b630eb6d52138c2e7f112cbac85aaa1abd6753603e846ef94c50a5`.
Native statistics never enter proof premises. Four gate-screen fixtures pass
at 0.166077 CPU seconds. The pinned two-bound diagnostic costs 0.082209 seconds
and projects 17,504.27 CPU-hours from the earlier model; whole assembly and
full-scale model validation remain absent. This does not authorize production.

The new `Game.Indexed` proof first fails elaboration on inferred function
domains (2.666066 CPU seconds, retained). Explicit state/body function types
resolve it. `Tests.Indexed` then accepts cold on the laptop (2.973616 CPU seconds,
0.191231 GiB) and desktop (1.299047 CPU seconds, 0.185932 GiB), safe flags,
unchanged source and zero previous interfaces. All 77 current Agda/library
sources have identity
`644f71b505da1f0d8493db81602f94b59341e2a6fd1f1505132be7560bf18b40`.
The extended `Everything6` accepts cold on the desktop at 52.861050 CPU seconds,
1.458752 GiB, with the same Agda-source identity. P1's 23 source bytes remain
exactly tagged; its identity is unchanged. No source postulates are introduced.

The data-only measurement harness retains two pre-kernel failures (2.344619 /
2.746927 CPU seconds): an overbroad donor-file comparison, then an incorrect
supervisor metadata keyword. Four generator/cache-scope fixtures and the
installed supervisor API compatibility check pass before the corrected detached
job starts. It measures independent local Boolean facts only; global linking,
initial guarantees and joint strategy computation remain pending.

Earlier offline continuation, 9 October: `wire-cut-ply10-20261009` stops at the storage
guard after 168 consecutive safe cold part acceptances. Nested CPU is
1,406.608013 seconds; outer measured CPU is 1,604.490203 seconds, charged once.
The partial kernel report SHA256 is
`e605541041ecd1c3603bc1472875af4c81a5e68f83e8fde7cdb9439ff0eb2197`.
The immutable 199-interface pool SHA256 is
`f12424b9343f064b4ffd34ebe31f2eb55048348deab85b08904a05038765c225`.
Its root remains unchecked. The source-allocation helper's first import-path
failure costs 0.022548 CPU seconds; its corrected acceptance costs 1.964271.
All selected frozen source identities, timestamps/modes, proof interfaces and
measurement receipts remain unchanged. Retired native dump archival accepts
at 37.100090 CPU seconds; archive recovery mappings have SHA256
`62120ed99adb1d5c5a398bf01a0b769c8d8fa0f7213405bd0d02b6dc189ab8a0`.
The mappings record original and gzip hashes and are verified before unlinking
raw data; no proof caches are archived or removed.

The native layout experiment passes four unit fixtures, 72 reference counter
cases and independently replayed small partition/closure and pinned-line
cases before initial measurement. Unpinned/pinned fixture report SHA256:
`dc43aecff4f456ab8a2fbdb95eb78a680532b6ce65881a0d170536674b747d97` /
`b619f654550beb31d54fd4705df7df385946c804cf0a5594f80d164d10d9fca6`.
Full initial counts remain pending and cannot become a proof premise.

The prefix-resume tool passes 13 measured filesystem/provenance fixtures,
0.223081 CPU seconds, with source unchanged. It rejects altered source,
compiler, flags, cache digests, failed or reordered prefixes, unsupported
interfaces, cross-machine use and storage-stop continuation. The detached
kernel successor audits the original 168-part cache and checks remaining
targets privately; its launch is not a root acceptance.

Latest results, 9 October 2026: the detached ply-12 continuation accepts
both 16-disc original-rules +4 bounds and their root assemblies. Outer CPU
299.028761 seconds is charged once. Lower checker: 200.185947 CPU seconds,
24 parts plus assembly, maximum RSS 1.302769 GiB; report SHA256
`6815b14c5bf3772e38e3ef0da8bf25cfb6594792297de054c1c2c1a691f57832`.
Upper: 59.335214 CPU seconds, seven parts plus assembly, maximum RSS
0.577305 GiB; report SHA256
`4a751b8649abec4c8d97ffb11fad1bf42dd3d633c8d7e34f96ad23daaea10a55`.
All own targets were cold, generic imports reused only on their checking
machine, safe flags present, sources/imports unchanged. Final chain SHA256
`017b0465c49c4991d55a0d7862ff1d0a61cab86e64b9fa32fc3f5198fb436676`.
These prove descendants, not the initial board or optimal joint strategy pair.

The separate six-pilot audit accepts all source, target, receipt and interface
identities (0.717437 outer CPU seconds), report SHA256
`83ea5a32c125f0f2c614b39c4045ddc6b8ab99ccc6753585838e9b4b766dcae1`.
Its incomplete retrospective model never authorizes production.
The inline-cut exporter validation accepts 14 Python fixtures, two batches
of 72 native counter comparisons plus independent scalar certificate checks,
all forced-pass D4 images, losing-pin rejection and pinned late-line fixtures.
Outer CPU 3.108955 seconds; report SHA256
`d2e9a0b35cf9a330bcb48e6daa41c25f4b28ba0abb606ac041e81f5fb6a55cc0`.
Three extended driver guard fixtures pass at 0.114386 CPU seconds.

Exact duplicate interface allocation was shared only in six closed accepted
run roots, with nested source identities and every interface byte preserved.
The initial helper failed on its Python module path (0.022123 CPU seconds,
charged); the corrected helper accepts at 1.051491 CPU seconds. No unique
proof interface was deleted, and future mutable checks use private copies.
All 75 Agda/library sources, the P1 source identity and original native
solver remain unchanged. `wire-cut-ply10-20261009` is the new bounded detached
pilot, not a completed fact.

Latest streaming certificate checks, 8 October 2026: safe original-rule +4
lower/upper guarantees at line plies 14 and 16 accept cold for their own
targets, reusing only exact immutable same-machine generic interfaces.
The detached pilot has five accepted stages, 93.053027 nested checker CPU
seconds and maximum nested RSS 0.533032 GiB. Outer CPU is 110.603186 seconds,
charged once. Final report SHA256:
`6c7871fcefa69cfe0ac20970d1d856b1439d79b3c5b74b7611a69c54a8091c1b`.
All generated sources and borrowed imports remain unchanged. This proves
descendant bounds only; initial Problem 2 and the optimal joint play remain
unproved. P1 and the complete Agda-source identities below remain equal.

The revised lower heldout passes all four prospectively fixed predictions:
errors −0.44%, −18.14%, −21.40%, +1.07%; 11.943633 nested CPU seconds.
Report SHA256: `3c020d05457188f637d8ddafcaf04d7e8b9380dfa0c03e13de18bb18291fdf05`.
The upper heldout passes with errors +2.14%, +2.11%, −2.41%, −2.37%;
4.572268 nested CPU seconds. Report SHA256:
`bff7fb5b1bf966d2dae4d8cf1f33aeeac44a30c21f04b5964d4c49ba449cee40`.
The small assembly scale still prevents a full production GO.

The bounded streaming export's matching scalar tests and line-pinned tests
accept, including rejection of a legal losing pin, false bounds, fuel failure,
truncation, missing opponent replies and unsafe citations. The latest eight
Python wire/queue tests accept at 0.099959 outer CPU seconds. The complete
native preparation of four line roots accepts at 7.195089 CPU seconds.
The initial upper-training launch failed before Agda because of an executable
path typo (0.057826 CPU seconds), and the first detached launch failed on a
prepared-directory typo (0.458057 CPU seconds). Both failures are retained and
charged. Corrected runs accept; no acceptance is inferred from a failed launch.

The first earlier-position attempt preserves complete native lower data, then
fails before Agda on the conservative token-per-entry cap. Its 4.589828 CPU
seconds is charged. The corrected detached continuation reuses the unchanged
wire; larger token shards retain the original 1.5-GiB part memory limit.
Its eight Python tests accept at 0.103959 CPU seconds. Native data acceptance
does not establish a bound without the subsequent safe Agda checks.

Latest compute-stage checkpoint, 8 October 2026: the user authorized more
compute and the coordinator recorded an additional 24 CPU-hour grant, making
48 total. Before extending, the old ledger was saved in
`results/budget-extension6/ledger-before.json`; all 333 finished receipts and
all withholdings in that snapshot remain byte-for-byte equal as ledger entries.
P1's 23 Agda/library files still have identity
`b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`.
All 75 current Agda/library source files retain identity
`a6234e52829fe28e5cab81a53907d090b5d4ec3f0a9174c6dbf3c7671f38f839`.

The first local ledger-test invocation failed on its module search path and
charged 0.064845 CPU seconds. The corrected invocation ran all 15 tests,
including idempotent extensions, reservation preservation and rejection of
unrecorded limit edits: accepted, 2.916989 outer CPU seconds. Both receipts
are retained under `results/budget-extension6/`.

`canonical-compact-build-20261008` accepts at 0.484655 compiled CPU seconds.
The complete 59-bit ternary position/mover key occupies a 24-byte memo record
with exact tree/hint counters. Build report SHA256:
`cc8443536e1678a36fa7eb49d97f6c262496bc53ca64246986f3eb2fdb6eeb71`.
`canonical-compact-tests-20261008` accepts at 0.252716 native CPU seconds:
169 positions, 1,352 transformations, 72 scalar bound/graph cases and 72 exact
emitted-graph/counter comparisons with the accepted noncompact min-replies
census. Test report SHA256:
`4ef3d078c02b18879e7cd0b12abf81ff1f4b35168e3857b75f1458b33883cc46`.
These are native tests, not checked initial-board guarantees.

Both compact initial native censuses are complete and collected. Lower
`canonical-compact-20261008`: 67,468,478 distinct nodes, 81,816,862 edges and
713,527,417 expanded occurrences; 612.421619 outer CPU seconds, 5.037987 GiB RSS.
Upper `canonical-compact-upper-20261008`: 66,936,456 nodes, 80,917,299 edges and
207,779,198 occurrences; 630.726320 outer CPU seconds, 5.024456 GiB RSS.
Both report validated roots, true bounds, no overflow and no oracle abort.
Their report hashes are respectively
`e5601b1ef6b362802fbc36f3cf16ae8c8c9f866040d1105fbb48a02780c8c0ea` and
`17c60387ba4f6d7cc9c2958012daad3ee07a2853adf0f831594a36e795a7de10`.
Actual CPU is charged once and both reservations released. No witness graph
was emitted; line preservation is false. These are native measurements, so
the initial theorem and optimal strategy pair remain unproved. All earlier
safe proofs and same-machine caches remain preserved.

The bounded sampler matches all 72 original native reference graphs and
independently replays 362 complete descendant closures, including 234 forced
pass rows. It rejects 24 false bounds, 438 oversized attempts and nine invalid
or fuel cases. The matching native build and test receipts charge 0.619910 and
0.654466 CPU seconds. The sampler wrapper's first extraction fails before the
C program starts (0.078781 CPU seconds); its corrected injection boundary
passes a dedicated metadata-subprocess regression test (0.091950 CPU seconds).
A missing-file test fixture failure (0.093327 CPU seconds) is retained separately.

`census-pilot-smoke-20261008` accepts all nine safe, cold-target phases with
same-machine generic interface reuse. It includes a two-shard dependency and
four conditional original-rule guarantees from tiny fixtures. Nested kernel
CPU is 2.261987 seconds, outer CPU 3.664700 seconds, outer peak RSS 0.210434 GiB.
All borrowed interfaces, generated sources and donor identities remain equal.
This verifies generated proof syntax and imports; it supplies no initial-board
claim and is excluded from representative timing training.

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
| Problem 2: 6×6 value +4 and the SAME optimal pair ending16–20 | Safe Agda proved,19 October2026 | `Tests.CompleteUpperRows6.Result.initial6x6 : Problem2`; private checked package linked above |
| Problem 3: 8×8 draw | Statement only | `Othello.Statements.Problem3` |

The following22-module census describes the original5 October core. The
accepted6×6 package has the separate4128-module selected-source audit above.

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


## 6×6 feasibility study, 5 October 2026

This section concerns the `six` branch. The initial Problem 2 theorem remains
unproved. All new Agda modules are safe and contain zero postulates; the native
solver and compiled checker supply measurements and hints only. The original
23 tagged Agda/library files remain byte-identical to
`tpp-mark-2026-problem1`, with the original file-set hash quoted above.

The new foundations, equivalent faster rules, strict decoders, legal 16–20
line, negative fixtures and p26 local composition pilot passed the desktop cold
check `remote-kernel-smoke-20261005` in 16.123827 wall seconds with 0.953987 GiB
peak RSS. Adding `Tests.Perft6` then passed a cold desktop check in 1.954950
wall / 1.938830 CPU seconds, 0.082939 GiB RSS, zero prior interfaces. Original
6×6 perft counts through depth 4 are 1, 4, 12, 56 and 244. The integrated laptop
warm check including that fixture passed in 1.233129 wall / 1.176912 CPU
seconds, 0.142208 GiB RSS.

Detached desktop records are retained under ignored `results/remote6/LABEL/`,
and laptop records under `results/checks/`. Each records the exact frozen
source and binary hashes, command, cache state, final rusage, exit and resource
limits. Different snapshots have different aggregate identities; new modules
do not alter the original Problem 1 identity. The single coordinator ledger is
`results/study6-ledger.json`. Failed and cancelled searches are charged, not
removed from cost analysis.

Untrusted differential checks passed all 1000 seeded late-game positions,
including adjacent thresholds. Compiled evaluation passed 196 positive and
negative fixtures; its values are not imported into the proof. The assembly
pilot reused four independently checked abstract interfaces on the same
machine, without rechecking those parts. No Agda interface moved between
machines. The local assembly took 0.612188 wall / 0.602683 CPU seconds,
0.141270 GiB RSS. This does not establish the feasibility of full initial-board
assembly.

All 360 original cold sample measurements are collected: original rules accepted
143/180 and Fast6 accepted 171/180 under the configured caps. CPU/heap failures
remain observations, including failed held-out checks. A plain Boolean evaluator
has been proved pointwise equal to the original search and integrated into
composite solve leaves. Its integrated checks passed on the laptop (3.025246
wall seconds, 0.180374 GiB RSS) and cold desktop (20.305083 wall seconds,
1.041683 GiB RSS), binding Agda-source identity
`4a6d136f9c67b9dde6942aab1f25ef880b8c9ef11fbcfecd609369b7c314cf18`.
The Boolean follow-up completed all 180 bounds, with peak individual RSS at
most 1.039017 GiB. All 36 held-out CPU predictions passed the 30% gate. The
pooled model has an approximately 10.45-second cold intercept and 1.102 ms
per literal search node. Its 179-job main batch charged 4782.230882 CPU
seconds in 752.606940 wall seconds, with 6.238411 GiB aggregate peak RSS.
Six generated hinted-certificate fixtures also passed safe checks, including
a 23,909-node certificate. Their approximately 1.017 ms/node initial fit has
no held-out validation and is not a full skeleton-cost guarantee.

The initial native exact search returned raw White +4 after 34,872,958,530
native nodes and 2731.839943 CPU seconds. This is untrusted evidence, never
a proof assumption. Every first-round initial frontier case hit a cap, so
its tree/leaf counts are lower bounds. The larger detached follow-up finished
unattended with exit 0 and unchanged source on 5 October, at 17:07:18 UTC.
It charged 4294.814479 CPU seconds in 4300.265220 wall seconds and peaked at
1.552441 GiB RSS. Its 20-disc upper prefix completed with 361,999 expanded
nodes and 166,260 distinct leaves; the other three prefixes hit their 500 CPU
second caps. An accepted measurement does not make those three prefixes
complete. No total Agda-order leaf work or preserved joint line was measured.
The streamed, hash-bound TT checkpoint is saved on the desktop, remains
untrusted and never enters a proof. The result and provenance were collected
on 6 October; the coordinator ledger charges actual final rusage.
See [the feasibility log](feasibility6.md)
for the remaining frontier-work and hint/composition prediction gates. No full
Problem 2 release or submitted proof is claimed.


## 6×6 continuation, 6 October 2026

The plain Boolean local-certificate evaluator is proved pointwise equal to the
existing evidence evaluator. Transported soundness and all integrated fixtures
passed cold checks on both machines, at Agda-source identity
`ad702035c80d1c032077b65865e3e23e379be0b10004f5bb660782168c072e38`.
Laptop: 37.136944 wall / 36.815894 CPU seconds, 1.102703 GiB RSS.
Desktop: 15.957472 wall / 15.929149 CPU seconds, 1.048645 GiB RSS.
All 23 original tagged Agda/library files are still identical, and all 53 core
Agda modules retain safe/without-K/cubical-compatible options and zero postulates.

Three real 16-empty upper-bound certificates that previously exhausted their
heap now pass safe checks: 220,798 / 78,629 / 68,347 nodes; 255.581313 /
90.866199 / 78.386186 CPU seconds; peak RSS at most 1.268204 GiB. All three
held-out timing predictions are within 30%. Their earlier failures and separate
decoder-isolation experiments remain recorded. No decoder change was integrated.
The certificate batch's final nested integration launcher waited on its parent's
lock; the waiting child was terminated and audited, and a standalone desktop
cold check supplied the complete result above.

The first realistic large-shard assembly accepted all three independent shards,
but assembly itself hit the 60 CPU-second cap while converting transparent
data. Its interfaces were not rechecked, and the failure is retained. The
abstract-certificate retry passed: all three large shards accepted cold, then
assembly and three explicit Black guarantees under original rules accepted in
0.339270 wall / 0.331130 CPU seconds with 0.134602 GiB RSS. Accepted interfaces
were unchanged and no part was rechecked. All bodies are safe and add zero
postulates. This verifies three sampled 16-empty states, not the initial board
or assembly of the entire production frontier.

The complete upper 20-disc frontier has 166,260 distinct leaves. Independent
20- and 120-position literal-work samples are statistical evidence with recorded
seeds and uncertainty; they are not exact full W or proof assumptions. All 34
positions of the 16–20 line were verified natively to have exact value +4; that
optimality claim has not been proved in Agda. The initial Problem 2 theorem
remains unproved. See [the feasibility log](feasibility6.md) for the measurements,
failures, current production recommendation and bounded desktop jobs.
## Further frontier measurement, 6 October 2026

`native-upper22-cached-fixed-20261006` completed and was collected into the
single coordinator CPU ledger: 890.853773 CPU seconds, 895.853634 wall seconds,
1.715214 GiB RSS. Its native upper frontier has 665,398 distinct leaves;
120 uniformly sampled leaves and all 360 hint-depth profiles completed.
These are native/statistical measurements, not kernel acceptance of the
initial 6×6 theorem. The three abstract certificate shards and their assembled
Black guarantees remain the accepted kernel pilot. Their fetched source hashes
match their frozen assembly manifest. The cache-retaining lower-frontier
continuation subsequently completed and was collected: 1857.373622 CPU seconds,
1864.742184 wall seconds, 1.695236 GiB RSS. Its native lower frontier has
374,280 distinct leaves and 1,306,120 occurrence-weighted skeleton nodes.
Both detached frontier jobs have finished, with no active ledger reservation.

## Checked sharing and D4 transport, 6 October 2026

All 23 tagged Problem 1 Agda/library files remain byte-identical; their identity
is still `b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`.
At this stage, 70 Agda module files declare safe/without-K/cubical-compatible
options and contain no project postulates, holes or termination/positivity
escapes. The integrated entrypoint is `Everything6.agda`; benchmark/data files
outside that entrypoint are not additional initial-board proof claims.

Agda/library identity at this stage:
`70e34844644a696c7b04ff715430143de41185538e412c12d8a7b7c4b44e2969`.

| Integrated check | Cache | CPU s | Wall s | Peak RSS GiB | Accepted |
| --- | --- | ---: | ---: | ---: | --- |
| Laptop, `shared-symmetry-generated6-integration` | 63 → 64 interfaces | 0.722407 | 0.795157 | 0.181274 | yes |
| Desktop, `kernel-shared-generated-core-final-20261006` | cold, 0 → 64 interfaces | 55.127681 | 55.235847 | 1.319916 | yes |

Both use `--no-libraries --safe --without-K --cubical-compatible -i src`
and `+RTS -M1200M -RTS`. The laptop invocation is serialized with `flock`;
its actual Agda binary SHA256 is
`9ee82043d547e3c2e83bcf36ade67d3ab674347391996ca013583cf383449cba`.
The desktop directly invokes binary SHA256
`c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`.
Interfaces were never copied between machines. Individual predecessor records
retain the cold checks and failures before the final source changes.

The new soundness facts cover selective checked shard exports and imports,
tagged citations, and arbitrary-board D4 certificate transport with remapped
choice indices and reordered full opponent forks. Tests reject missing/future
imports, colliding state keys, omitted opponent replies, invalid tags and wrong
orientations. The real generated forced-pass lower/upper +4 fixtures are accepted
by `refl` and yield guarantees using the concrete proved Othello transport laws.

Eight real lower-bound shards with 10,743 exports and 168,465 tokens accepted
for a sampled 20-disc position. Their accepted CPU sums to 389.713193 seconds,
peak individual RSS is 1.410313 GiB, and final assembly constructs a guarantee
in 4.114520 CPU seconds. The initial combined RSS-stop and all accepted earlier
records are retained; the resume checks source manifests, compiler/machine
identity and dependency interfaces. This is a sampled-position theorem.
`Othello.SharedProof6.problem2-from-proven` is conditional and supplies no
inhabitant of the initial `Problem2` statement.

The final 6×6 Python suite (`python3 -m unittest discover -s tools -p
'test_*6.py'`) passes 90 tests, including native/scalar checks, negative
certificate fixtures, canonical index transport and statistical gate guards.
Record: `results/shared-tools6-checks/shared-tools6-final-90-tests.json`,
7.735473 CPU seconds, 0.125973 GiB RSS. These tests remain outside proof trust.

The current production recommendation is NO-GO for the per-leaf representation.
The shared held-out timing error is about 41%, exceeding 30%, and projected
encoded data exceeds the 10 GiB gate. Complete canonical-root samples project
122.57 GiB of that encoding and nominal components well above the 168-hour
desktop limit. These measurements use exact-state sharing within certificate
graphs from canonical roots, not a production-scale run of the new D4-citation
generator. The held-out cost model is not validated. Full skeleton and optimal joint-line
assembly remain unproved and unmeasured. Native graph counts and sampling
estimates are kept separate in `feasibility6.md` and the gate report. All jobs,
including failed setup, CPU/RSS stops and retries, are charged through the
single study ledger; no category is automatically reallocated.

Coordinator accounting at the end of the sharing study: 37,978.337004 measured CPU seconds charged,
310 seconds conservatively withheld, zero reserved and 48,111.662996 seconds
available within the 86,400-second study allowance. Every study job is finished
and collected. Proof and generator agents have completed their owned work.
The working tree remains uncommitted; no production, tag, push or email is
claimed.

## Compact decoder and bounded global pilot, 6 October 2026

At this stage the source had 72 Agda module files, all declaring
`--safe --without-K --cubical-compatible`, with no project postulates, holes or
termination/positivity escapes. The tagged 23-file P1 identity remains
`b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`.
Agda/library identity at this stage:
`a18830a559d557a10336488ed6b3ec4c4abc85809ee919389fabacf080de1764`.

`Everything6.agda` additionally imports the compact decoder and its Agda
fixtures. Passing this entrypoint establishes its imported development;
the source count includes benchmark/data modules and is not a claim that the
initial 6×6 theorem has been proved.

| Integrated check | Cache | CPU s | Wall s | Peak RSS GiB | Accepted |
| --- | --- | ---: | ---: | ---: | --- |
| Laptop, `compact-global6-integration-laptop` | 65 → 66 interfaces | 1.008590 | 1.114000 | 0.201733 | yes |
| Desktop, `kernel-global-compact-core-20261006` | cold, 0 → 66 interfaces | 56.277151 | 56.381136 | 1.318092 | yes |

Flags are `--no-libraries --safe --without-K --cubical-compatible -i src` with
`+RTS -M1200M -RTS`. The actual binary SHA256 values are unchanged:
laptop `9ee82043d547e3c2e83bcf36ade67d3ab674347391996ca013583cf383449cba`,
desktop `c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`.
The laptop uses its serialization lock. Interfaces stay on their original
machine and binary. Records are in `results/global-pilot6-checks/` and
`results/remote6/kernel-global-compact-core-20261006/` respectively.

The Python suite passes 103 tests in 8.409569 CPU seconds, at 0.141659 GiB RSS:
`results/global-pilot6-checks/compact-global6-python-suite.json`.
Four additional report guards pass in 0.078177 CPU seconds:
`results/global-pilot6-checks/global-report6-subset-tests.json`.
These cover incomplete assembly, mismatched plans/roots and statistical
projection boundaries, in addition to compact decoding and global graph
generation/replay. They remain outside proof trust.

The completed native graph for 100 canonical upper22 roots is scalar-replayed,
not kernel-accepted as a whole. Its plan SHA256 is
`d3c6fab0d3e0e6f9bd4f1bd7eeabf8599da28b99485e3469bed1e4ded7d6c485`.
The initial kernel job accepts 33 parts before Part33 exhausts its 1,200 MiB
heap. One recorded resume accepts six more parts before Part39 exhausts its
1,350 MiB heap. The part RSS guard remains 1.5 GiB. The unchanged generated
125-part source has Agda/library identity
`8a9f8581290e8aeba956f4681422e85f939adbfae09dfae0bb33738215052ea1`.
Borrowed source/interface hashes are checked before and after each target.

The 39 accepted parts export 11,700 local proved facts. They do not supply
the requested root guarantees. Assembly for the 28 roots covered by that
prefix also exhausts its 2,500 MiB heap; recorded RSS is 1.986740 GiB under
a 3 GiB guard. Thus **zero requested root guarantees** are accepted in this
pilot. Full 100-root assembly and the controlled encoding timing pair are not
reached. Failed logs and measurements are retained under these collected labels:

- `kernel-global-upper100-20261006`
- `kernel-global-upper100-resume-20261006`
- `kernel-global-upper-subset-20261006`

`results/global-pilot6/report.json` reports the partial result and no production
GO. Its native graph/data savings are separate from kernel claims; see
`feasibility6.md` for their sampling scope and limits. All jobs are finished
and collected. The pilot charges 629.478008 CPU seconds; the coordinator
ledger now charges 38,607.815012, with 310 withheld, zero reserved and
47,482.184988 available. No categories are reallocated. Problem 1 is preserved,
Problem 2 remains unproved, and no commit, push, tag or email was made.

## Memory diagnosis and repaired sampled bounds, 6 October 2026

The current source has 74 Agda module files, all declaring
`--safe --without-K --cubical-compatible`, with no project postulates, holes
or termination/positivity escapes. All 23 tagged P1 Agda/library files remain
byte-identical, with identity
`b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`.
Current Agda/library identity:
`a6234e52829fe28e5cab81a53907d090b5d4ec3f0a9174c6dbf3c7671f38f839`.

`Everything6.agda` additionally imports `Game.SharedExport` and
`Tests.SharedExport6`. The new soundness lemma transfers proved facts into a
literal export trie after a Boolean coverage check. Its fixtures reject
missing states, colliding keys and a bad branch. This optional template has
no measured performance gain and was not used in the accepted continuation.

| Integrated check | Cache | CPU s | Wall s | Peak RSS GiB | Accepted |
| --- | --- | ---: | ---: | ---: | --- |
| Laptop, `memory6-core-integration-laptop` | 67 → 68 interfaces | 0.775264 | 0.834833 | 0.209152 | yes |
| Desktop, `kernel-memory-core6-20261006` | cold, 0 → 68 interfaces | 56.497324 | 56.648637 | 1.268082 | yes |

Flags are `--no-libraries --safe --without-K --cubical-compatible -i src`
with `+RTS -M1200M -RTS`. The laptop check uses its serialization lock. The
actual Agda binary hashes remain
`9ee82043d547e3c2e83bcf36ade67d3ab674347391996ca013583cf383449cba`
(laptop) and
`c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`
(desktop). No interfaces cross machines or binaries. Records are in
`results/memory6-checks/` and
`results/remote6/kernel-memory-core6-20261006/`.

The full Python suite passes 115 tests in 7.782822 CPU seconds, at
0.150242 GiB RSS. After the last generator/CLI changes, 16 focused
generator/report tests pass in 0.103367 CPU seconds. Their records are
`results/memory6-checks/memory6-final-python-suite.json` and
`results/memory6-checks/memory6-final-generator-checks.json`.

Phase-isolated cold targets show that all 39 original accepted dependencies
load successfully. The unused full decoder equality fails at a 1,350 MiB
heap; removing it lets entry decoding and export-shape equality pass.
Certificate acceptance still fails without the runtime change. Thus the
remaining failure is not established as an export-shape equality problem.
Generated assembly now names each `Proven` pair and uses projections instead
of concrete `with` matching; the original covered 28-root assembly then passes.

The controlled Part39 comparison has byte-identical repaired source,
unchanged dependency interfaces, the same binary, a 1,350 MiB heap and a
1.5 GiB RSS guard. Adding the recorded compacting-GC flag `-c` changes the
result to acceptance: 23.865954 CPU seconds, 1.414177 GiB RSS. Its bounded
continuation accepts Part39 through Part76, giving **77 of 125 accepted
parts** and **23,100 local proved exports**. Maximum successful part RSS is
1.422405 GiB. Part77 exhausts the unchanged heap at 1.394135 GiB RSS; it is a
heap-cap failure rather than an RSS-guard stop. Full 100-root assembly is not
reached. Repaired source Agda/library identity:
`83f56266d070689bb1cff0e9810144e9ed022046d284a960501bfd938b118f30`.

The **57 roots** covered by that prefix assemble successfully under
`Rules.game six`, proving Black guarantees for `upperGoal 4`. The nested
kernel check takes 34.290445 CPU seconds and 34.359108 wall seconds at
2.066460 GiB RSS, with `-M2500M -c -s` and a 3 GiB RSS guard. Its generated
Agda/library identity is
`c37504daf30cd6d4ba9a2f82dc20ab70b76fd3f45a258aef16cdc475a612d230`.
The accepted source, record and log are collected under
`results/remote6/assembly-memory-covered6-20261006/artifacts/results/memory-covered6/`.
These are completion-selected sampled upper bounds. They establish no initial
board result, exact value, lower bound or validated population cost forecast.

`results/memory6/report.json` retains hashes, controlled comparisons and partial
proof scope, with recommendation `NO_PRODUCTION_GO`. The next unresolved
target is Part77's checker and growing retained import context, followed by
full sampled assembly and a two-sided held-out cost model. The opening
skeleton and actual optimal strategies' joint line remain undone.

The diagnostic charges **630.480305 CPU seconds**, within its 1,800-second
cap. The sole study ledger charges 39,238.295317 seconds, with 310 withheld,
zero reserved and 46,851.704683 available. Categories are unchanged; every
job, including failures, is finished and collected. Work remains uncommitted.
Problem 1 is preserved, the initial Problem 2 remains unproved, and no
production, push, tag or email was started.

## Checked literal-import recovery of Part77, 6 October 2026

The bounded `kernel-part77-pilot-20261006` comparison completes. All new
targets use `--no-libraries --safe --without-K --cubical-compatible`, the
recorded desktop binary and `-c`. Part limits stay at a 1,350 MiB heap and
1.5 GiB RSS; assembly stays at 2,500 MiB and 3 GiB. The original 77 parts and
their interfaces are unchanged and verified. The 74-file core identity remains
`a6234e52829fe28e5cab81a53907d090b5d4ec3f0a9174c6dbf3c7671f38f839`;
all 23 tagged P1 files are byte-identical.

The dependencies-only check passes in 1.468091 CPU seconds at 1.313824 GiB RSS.
Splitting Part77 isolates its 258-entry prefix, which passes, but the remaining
42 entries still exhaust the heap. The failure is retained and charged.

The literal-import module's coverage and soundness facts pass in 32.155593 CPU
seconds at 1.411297 GiB RSS; Part77 using those tables passes in 22.031480
seconds at 1.415840 GiB. Each imported table has checked full-state coverage
of its accepted owner through `Game.SharedExport`. Certificate acceptance and
soundness still use the original `checkShardBy` and `shardBy-sound` machinery.
The adapter and original Part78 then pass, giving **79/125 accepted original
parts** and **23,700 local proved exports**.

`CheckNew` constructs two further Black guarantees for `upperGoal 4` under
`Rules.game six`: 2.657851 CPU seconds, 1.349384 GiB RSS, cold target with
115 → 116 same-machine interfaces. Its Agda/library identity is
`092d25991a6a33a82529d7211b1e008ae889c50f53af40483a353b5553e5b633`.
The source, selected logs and all eight phase records are collected under
`results/remote6/kernel-part77-pilot-20261006/artifacts/results/part77-pilot6/`.
Together with the earlier 57-root acceptance, this gives **59 distinct sampled
upper bounds across two assemblies**. There is no combined 100-root proof,
initial-board theorem, lower-bound claim or new validated production forecast.

Eighteen relevant Python tests pass in 0.095742 CPU seconds; six final guards
pass in 0.082521 seconds after the adapter source reuse fix. Downstream roots
reuse the actual checked adapter source by immutable hard link, preserving its
timestamp; its interface is never paired with the old failed source body.
Use the checked `CheckNew` root as the future donor, not the top-level `source`
directory. Records are in `results/part77-checks/`.

`results/part77-pilot6/report.json` retains input hashes and continuation scope,
with recommendation `NO_PRODUCTION_GO`. This diagnostic charges 89.812847 CPU
seconds including the 89.634584-second desktop job. The sole study ledger now
charges 39,328.108164, with 310 withheld, zero reserved and 46,761.891836
available. All jobs are collected. No source is committed, pushed or tagged,
no production is started, and no email is sent.

## Full sampled upper coverage; failed combined collectors, 6 October 2026

The 74-file safe core remains at
`a6234e52829fe28e5cab81a53907d090b5d4ec3f0a9174c6dbf3c7671f38f839`.
All 23 files from `tpp-mark-2026-problem1` remain byte-identical, with P1
identity `b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`.
No core module changes, postulates, holes or termination/positivity escapes
are introduced. Existing paired core checks are not rerun for Python tooling
and documentation changes.

`kernel-global-continue-20261006` checks through original Part83 and seven new
original-rules root guarantees. It stops after both Part84 variants exhaust
the heap. Original accepted count is **84/125**, not 125/125. The original
sources and interfaces remain verified and unchanged.

`kernel-closed-roots-20261006` checks 112 parts and 34 guarantees in distinct
root namespaces, using the exact original graph's citation closures and
certificate bytes. All 146 targets pass cold with
`--no-libraries --safe --without-K --cubical-compatible`, `-M1350M -c -s`,
and a 1.5 GiB RSS stop. Maximum part RSS is 1.140427 GiB; maximum root-bound
RSS is 0.409538 GiB. The desktop binary SHA is
`c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`.
The generated base Agda/library identity is
`c73f6269165b482d5e1890757fe2de4ed85dcce29de3416ac9d8ab1f7d538eb0`.
All accepted records have unchanged expected source, cold own targets and
same-machine dependency hashes verified before and after checking.

The final `All100` collector fails its 2,500 MiB heap, after 3.007617 CPU
seconds at 2.507439 GiB RSS. Its source identity is
`7d78fb4ab9122279a6d42fc00b783269152cfabdff4f66406a20be6c3fb3b264`.
The bounded `kernel-collector-thin-20261006` alternative also fails that heap:
3.020439 CPU seconds, 2.513405 GiB RSS, source identity
`611407ba27bc27a2765923b97888d7be48349f9976fda67e78e535b8282e2dcd`.
Both retain a 3 GiB RSS guard, reuse 272 accepted interfaces and produce no
collector acceptance interface. A successful outer measurement is a completed
experiment, not acceptance of its failed Agda target.

The 147 root-local phase records are retained in the fetched
`results/closed-roots6/phase-records.json`, SHA
`65786fceb9c3632e581d0ede10e760454627546bb0e31e889ab55d2332371cbe`.
The frozen `closed.json` SHA is
`2942c685841feeb1e73ba1de25917df3b04a87fbc18f87cf30dd47b02a460427`.
The final coordinator report verifies that prior 57 + 2 + 7 and new 34 roots
are distinct and cover the exact original 100-position sample. **All 100
individual Black upper +4 guarantees are checked under original rules; no
combined theorem, lower-bound completion or initial Problem2 is claimed.**

Focused tool runs pass: 21 initial continuation checks, nine final continuation
guards, 13 closure/reuse guards, and two collector coverage checks (rerun after
making their fixture independent of ignored result artifacts). Their records
are in `results/global-continue6-checks/`. The full 115-test suite's earlier
acceptance remains historical; it is not a new full-suite result.

The final `results/global-continue6/report.json` and `budget.json` record
645.662083 CPU seconds charged within the 3,600-second cap. Study totals:
39,973.770247 charged, 310 withheld, zero reserved, 46,116.229753 available.
All desktop jobs are finished and collected. Production remains NO-GO; work
is uncommitted, and no push, tag or email has been made.

## Detached-run cache incident, collected 7 October 2026

`unattended-assembly-20261006` finished with exit 1 after 56.465985 wall
seconds and 60.189806 CPU seconds. Collection charges 60.189807 seconds after
rounding and releases its reservation. Its checkpoint still says `running`;
that checkpoint is incomplete and is not a successful final result. Six
import diagnostics completed; the first saved-meta regrouped part was
accepted before the harness rejected changed dependency hashes.

| Import-only target | Accepted | CPU s | Peak RSS GiB |
| --- | --- | ---: | ---: |
| Core | yes | 0.022796 | 0.067192 |
| Old57 | yes | 1.380848 | 1.141342 |
| Old66 | yes | 1.641391 | 1.491112 |
| New8 | yes | 0.666715 | 0.556660 |
| New34 | yes | 2.292085 | 2.061848 |
| All100 | no, heap | 2.985198 | 2.507957 |

These cold import targets retain a 2,500 MiB heap and 3 GiB RSS guard. Loading
the old proof modules alone exceeds that heap, before constructing the tuple
of guarantees. `group0-part0` accepts with safe flags and `--save-metas`, in
42.448066 CPU seconds at 1.457390 GiB RSS. Its own target is cold and its
expected source is unchanged. The subsequent harness failure is distinct
from the kernel acceptance of this part.

The old harness hard-linked writable dependency interfaces. Switching
interface storage mode caused Agda to rewrite generic files in place,
including their historical donors. Earlier before/after cache-identity claims
describe those checks at their recorded times; they do not describe these
cache bytes after this incident. The Agda sources and recorded compiler
acceptances remain unchanged. The affected default-mode cache pool is
quarantined: its old provenance guard rejects it. Its recorded digest is
`a37603ef275f2cdcc3c10d7613568423dea58243882d514ac1d560703bdd9485`;
the observed post-incident digest is
`1600a4a23814ca9c256da202f11db5c99bf7f920422cc84644567c02da11db4b`.
No old record is rewritten to bless that drift. Exact restoration was not
found among the tested core caches, and no speculative overwrite was made.

`tools/cache_resume6.py` instead uses separate inode copies and one privately
owned serial cache per group, checking hashes after every target. Three
copy-isolation guards pass, including a destination rewrite that leaves the
donor unchanged. The original unattended runner also now copies interfaces
and starts saved-meta dependencies cold. The restart reuses only the accepted
first part's frozen saved-mode seed; it does not reuse the changed old pool.
Core and P1 sources are unchanged. See the following completed result for the
restart's actual acceptance and resource evidence.

## Verified private-cache restart, 7 October 2026

`cache-resume-20261007` completes its bounded queue and is collected. Its
outer exit 0 is distinct from the final Agda collector's exit 251. All 263
regrouped parts, including the reused accepted seed, and all ten group-bound
targets are accepted. The final combined collector is not accepted. Original
global-layout coverage stays **84/125**, and initial Problem2 stays unproved.
Each group proves Black guarantees for `upperGoal 4` under `Rules.game six`.
The groups cover exactly the original 100-position upper sample in its
original order; they do not establish exact values or lower bounds there.

All 273 new phase receipts are validated against the recorded source/compiler
identities, cold own targets, private-inode cache policy and actual command:
`--no-libraries --safe --without-K --cubical-compatible --save-metas`.
Parts and ten-root bound assemblies retain `-M1350M -c -s` and a 1.5 GiB RSS
stop. Maximum part RSS including the seed is 1.457390 GiB; maximum group-bound
RSS is 0.906677 GiB. Every existing private-cache hash remains unchanged,
including after the failed collector. The saved seed's source and interface
maps are also unchanged. The 274 generated source files match a local
regeneration from the identical original graph; no certificate bytes or
citations are altered.

The combined target `Tests.Unattended6.All100` reuses 305 interfaces, fails
the 2,500 MiB heap with **3.030438 CPU seconds** and **2.505951 GiB RSS**, and
adds no own interface. Its 3 GiB RSS guard is unchanged. There is no accepted
single `AllUpper rootCodes` theorem. These figures do not test the larger
12 GiB production assembly gate. No unchanged retry or cap increase follows.

Frozen desktop root: `six-cache-resume-20261007`. Outer frozen-source SHA:
`cc4b69261fad9f28dd68ee2e73cdec69dd16cdd4fc3b9ff46bf174bb7fda41d9`.
Generated base source SHA:
`d54574b000ee37095994f74a0e8dc1ab1463f165c76ca5919bf74f0a10a05b15`;
generated Agda/library SHA:
`adf4e43a9d0d5bb1b13144cedbd0c0c3a1590560748907ecbc988230c76f1377`.
The desktop Agda binary SHA remains
`c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`.
`final.json` SHA is
`56d466ec8a1d1199e2f7393b10c5fd192f25e91f501c27a9998a4105c4eac9fa`;
the aggregate receipts/source-hash audit `phase-records.json` SHA is
`c8c18f8597b2090d5d927127a8e1bc13fe31e2f0d518589e61922e52090ff563`.
The failed collector record SHA is
`9dbbe9c89685c316cd41710941c69a4fe0c6bee208d3e43c41ebb9da851a8ee8`.
Artifacts and the failure log are fetched under
`results/remote6/cache-resume-20261007/`; no `.agdai` files cross machines.

The prospective upper-only timing holdout is statistical evidence, not an
Agda theorem. Group9 was designated before its measurements. A non-negative
four-feature model fitted on 231 parts from groups0–8 predicts the held-out
31-part total at 140.001206 CPU seconds versus actual 143.978214, **−2.7622%**.
Cold generic-core cost, generation, group/collector assembly, lower-side and
population sharing are outside this fit. Individual residuals are retained.
Passing this upper part-timing check does not validate the production gates.

The copy-isolation tests (three) and focused assembly guards (nine) pass. Core
and all 23 P1 sources remain byte-identical to their preceding paired checks;
no new core/full-suite check is claimed. No postulate or proof escape is
introduced. The restart charges 1,396.194090 CPU seconds, including its
supervisor, in 1,300.854178 wall seconds. Local tests charge 0.206847 seconds.
The seed is not rechecked or double-charged. The old failed overnight job is
separately collected at 60.189807 charged seconds.

`results/cache-resume6/report.json` and `budget.json` record exact coverage,
source/cache checks, failures and balanced accounting. The study charges
**41,430.455139 CPU seconds**, with 310 withheld, zero reserved and
**44,659.544861 available**. Categories are unchanged, all jobs are collected,
and production remains NO-GO. No commit, push, tag or email is made.

## Packed routing/export tables; full sample rechecked, 7 October 2026

The read-only original interface census preserves the verified donor's 305
hashes. It follows the pinned desktop compiler's `cb568525` x86_64 format,
rejecting incompatible versions and truncation. A failed initial reader is
charged, then corrected and tested. Encoded sizes/counts are diagnostic data,
not proof objects or measurements of live heap usage.

An explicit-argument A/B and a packed-table A/B both accept their representative
safe shard. The former gives no useful size reduction. The latter encodes
import keys and export state lists with the existing safe decoder, preserving
the exact actual certificate bytes, shape equality, Boolean acceptance equality
and soundness route. Its dummy leaf tags parse state lists only. It has 48,769
encoded nodes versus 109,586 originally. All tests preserving certificate data,
state order, proof obligations and rejection of changed/wrong-bound templates
pass. No core source changes are involved.

The exact packed Part0 is checked independently on the laptop with cold local
interfaces: exit 0, 81.616690 CPU seconds, 82.104964 wall seconds and 1.530319
GiB RSS including core imports. Target SHA:
`29651141e7f5a99bc8fca18e8154539c597e5141792efdaa85e238d86dc1cae6`.
The laptop compiler SHA remains
`9ee82043d547e3c2e83bcf36ade67d3ab674347391996ca013583cf383449cba`.
No `.agdai` file crosses machines. This cold laptop RSS is not a measurement
against the desktop's warm-dependency 1.5 GiB part gate.

`packed-assembly-20261007` checks 167 parts and six ten-root groups before its
10 GiB run-storage guard stops the queue. Its outer receipt is collected at
833.591719 CPU seconds. All 173 prefix phases are accepted, with 205 verified
interfaces. Completed warning logs are archived losslessly after verifying
their raw hashes and written gzip round trips. The old run's 272 accepted logs
and this prefix's 173 accepted logs retain exact recoverable bytes; failed logs,
JSON receipts, sources and interfaces are untouched. The initial filename-key
failure occurs before changing a log and is charged. Four archival guards pass.
Separate cleanup receipts record removal only of redundant borrowed interface
copies; every own proof interface and the canonical old 305-file donor remain.

`packed-continue-20261007` adopts the same serial private cache and checks only
the remaining 96 parts, four groups and collector. It charges 498.147100 outer
CPU seconds; the prefix is neither rechecked nor double-charged. The merged
audit validates all **274** phases and all **274** locally regenerated sources.
All **263 parts and ten group guarantees pass**, proving Black guarantees for
`upperGoal 4` under `Rules.game six` from exactly the original 100 sampled states.
This is upper-bound evidence, not exact values at those states or an initial
Problem2 proof. Maximum part/group RSS is 1.406540 / 0.979546 GiB. Existing
interface/source hashes remain unchanged; the checkpoint gains 100 interfaces.

Every target is cold in its own private cache, on the original pinned desktop
binary SHA `c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`.
All commands use `--no-libraries --safe --without-K --cubical-compatible
--save-metas`. Parts/groups retain `-M1350M -c -s`, RSS stop 1.5 GiB; the
collector retains `-M2500M -c -s`, RSS stop 3 GiB. It fails heap allocation with
exit 251, 3.001135 CPU seconds and 2.505371 GiB RSS; all 305 dependencies stay
unchanged and no own collector interface appears. Outer exit 0 records the
completed experiment and does not establish kernel acceptance. No unchanged
retry or cap increase is performed.

Frozen checking root:
`six-packed-assembly-20261007/results/packed-assembly6/check`.
The continuation harness is separately frozen at
`six-packed-continue-20261007`, outer-source SHA
`62997d3a8cd066017a1d784699a8d72bc23e73330bc5e2fc4e977297f18d1bb4`.
Checked full-source SHA:
`04b08bfc787d79e1c055116c9e686bdcc23a5e69aee5aed04aece7b62f2b6c3e`;
checked Agda/library SHA:
`b9ceb97a3903e884d96f3a3b922c98fb0b0eef14de3967e2b2b35dc01739ef34`.
Generated-source hash-map SHA:
`34e5876b7a7ce4b0fb196b3d3e0ae152185c08f33b4f0955dee1a1d268b73aad`.
Final report SHA:
`64d71adee91bd8c8fc47778d46fa79ddff319cd057ff6e820d6000e8f89e7b0e`;
merged phase-audit SHA:
`8cfec3ee53e8b96fa8d15b8e5d4072a1908b574be6f6aaf17057a6e22a072586`.
Failed collector log SHA:
`c4de4b93f6cdc58510cf40f04afa62a48e8c97bb50ba75aed440f71f2bdbd4d8`.
The final 305-interface map SHA is
`9bcce5d699d0afe9817b403e1cb96d5f671315fc726cf7f02fec02a93c6a35b8`.
Final metadata and the failure log are fetched under the continuation's
`results/remote6/` directory.

Group9's 31 held-out parts take 135.520128 CPU seconds versus a prospectively
declared non-negative four-feature prediction of 131.539437 (−2.9373%). The
232 training-part observations, residuals and declaration are retained in
`results/packed-assembly6/upper-cost.json`. This statistical fit excludes
generator, bound/collector assembly, lower-side and population costs and does
not satisfy the whole-workflow production gate.

The final read-only packed census preserves sources and all 305 interfaces.
It measures 14,056,447 encoded nodes and 457,630,539 payload bytes, versus
16,101,382 and 500,857,527 originally. Full-pool reductions are 12.7004% and
8.6306%; the one-shard result is not a population projection. Census SHA:
`2c85262cfc9142843c7c66b78d5b873e390c2c70293ae2290dc92d4e68ef1c64`.
Generic interface hashes and counts are identical between the two pools.

Coordinator scripts `results/packed-assembly6/validate_report.py`,
`upper_cost_report.py`, `footprint_report.py` and `accounting.py` reproduce metadata reports without
rerunning Agda. All 23 tagged P1 files remain byte-identical at
`b2f6cd2d35a03a2d02a44993c77e447a423f827202205b723b1b8cfef980b71f`;
the 74-module core retains
`a6234e52829fe28e5cab81a53907d090b5d4ec3f0a9174c6dbf3c7671f38f839`.
Existing paired core checks are preserved; no new full-suite run is claimed.
Static source inspection finds no postulates or proof escapes.

This request charges 1,526.918532 CPU seconds, including all failures and
supervision. All jobs are collected, with zero reservations; total charged
study CPU is 42,957.373671 seconds, 310 withheld, 43,132.626329 available.
Categories are unchanged. Production remains NO-GO and the initial Problem2
remains unproved. No commit, push, tag or email is made.

## Local warning filter and same-sample assembly, 7 October 2026

This experiment retains the exact original 100 sampled upper +4 roots,
certificates and ordinary equality goals. Only the new generated modules'
namespace and module-local `-WnoUnsupportedIndexedMatch` option differ from
the packed baseline. Source generation enforces the exact inverse comparison;
the predeclared 275-source map digest is
`5643a3fa38fd86cda9f2e17984c0ab1140916f25257e94814b2d20027a06e94c`.
This includes 263 parts, ten original-rule group bounds, a combined collector
and a deliberately false terminal upper certificate.

The private-import facade pilot checks successfully but saves only about 9%
of representative shard nodes. The global warning option also checks its Agda
target, but the cache policy rejects the resulting changes to 31 private
generic dependencies. Its failed measurement is retained and charged; the
canonical donor stays unchanged. The corrected module-local pilot checks its
two shards and original-rule guarantee while retaining all 32 generic hashes.
Shard nodes fall from 45,986 / 46,293 to 7,300 / 7,608; both interfaces keep
four other warnings and zero indexed-match warnings. The warning census is a
typed read-only format inspection, not an edited or imported proof interface.

The same two sources and guarantee check from a cold laptop cache, 0 → 34
interfaces: 93.712925 CPU seconds, 94.492551 wall seconds, 1.529297 GiB RSS,
exit 0, unchanged source. Laptop binary SHA:
`9ee82043d547e3c2e83bcf36ade67d3ab674347391996ca013583cf383449cba`.
Cold laptop source SHA:
`2518be2faa06801e50e33ec473726f2fe829ac45082a3cbff9c8fd545e88674f`;
Agda/library SHA:
`525c1c1a796b7212d531d1982e60fd46163f5541f53892a96ba0a78f525a64d0`.
No interface crosses machines. The laptop peak includes cold core checking
and is separate from desktop part RSS.

Agda rejects the false certificate with `[UnequalTerms]`, `true` versus `false`
at `Bool` when checking `refl`, exit 42 and no new interface. The first harness
stops because it expects an older diagnostic format; its exact rejection
receipt is reused after correcting and testing the parser. Raw failure log SHA:
`0541f9e07a69fd99349779da729d40ea86531558ecbaa753264f9e533d5f84c0`.
Fourteen final continuation/census/model guards pass before launching the
remaining queue; their capped measurement charges 0.158024 CPU seconds.

The first continuation accepts 128 parts and five group bounds (50 roots),
then stops at the unchanged 10 GiB aggregate artifact guard. All 133 accepted
raw logs are archived losslessly, 20,354,875 → 2,005,328 bytes, with raw and
compressed hashes and verified recovery. Sources, JSON receipts and the
165-interface pool stay unchanged. The archival job charges 0.261196 CPU
seconds and uses the existing frozen root under recorded caps, preserving the
new-run launch gate. The next continuation adopts this exact prefix and
archives each newly accepted log immediately. It preserves the same part/group
1,350 MiB heap / 1.5 GiB RSS and collector 2,500 MiB / 3 GiB limits.

Frozen proof source SHA:
`ecf3b080d1808ee364b102610981e84e3397068159f5dd40caeba07a065097a0`;
Agda/library SHA:
`9fde9b4dc22bb602e89ebb3bc1a29a5f56d5d0cdddaffffe5baa08d5d26618ec`.
The desktop binary remains
`c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`.
The final receipts and accounting are checked after completion; outer exit 0
alone is never treated as kernel acceptance.

The second group continuation accepts all 263 parts and ten group bounds, then
stops at the storage guard before starting collection. Its original 274-phase
report and audit are preserved with SHAs
`8a6ec1b760330afc82694154d5c53976ef7398963176c1e10d3028bed46bcc93` and
`46b3dfa6dcf30aa4387c903a2913cc22a6a5a1ac80cfc7767c338a0989ac663b`.
Writing its final audit adds about 1.4 MB after the recorded guard reading;
both values are retained. A capped archive of 39 accepted original-pilot logs
recovers storage, 6,752,408 → 620,228 bytes, without changing any source, proof
cache or JSON receipt. Failed logs stay raw. Its recorded raw hashes are
captured at archival, not represented as earlier measurement hashes.

`warning-collector-20261007` checks the previously untried collector against
the exact 305-interface prefix and predeclared generated sources. The cold
`Tests.WarningTables6.All100` target **passes**, exit 0, no resource stop:
**2.740962 CPU seconds**, **2.756004 wall seconds**, **2.422844 GiB RSS**.
Flags remain `--no-libraries --safe --without-K --cubical-compatible --save-metas`
and `-M2500M -c -s`; the RSS stop remains 3 GiB. No existing interface changes;
one accepted `All100.agdai` is added. The original-rule combined
`AllUpper rootCodes` theorem covers exactly the 100 sampled upper +4 roots.
Maximum part RSS is 1.212650 GiB, maximum group RSS 0.785439 GiB. This is not the
initial-board theorem. The collector was checked on the desktop; only the
two small exact shards and their guarantee have the new independent laptop check.

Collector report SHA:
`98be0603f302b2b4b266c5bfc5d3f6422ba3d66020ba699db43c3634cf3fa5d5`;
collector audit SHA:
`88576cdd971194e4c65cd048e2faea59d90b4dfea534a0d81a352b4e589f6dc1`;
raw collector log SHA:
`f07e9f3dd7e73b3eb5a692722b8f8f17a53636ce9f69293eb2ea7c42069dea84`;
gzip SHA:
`3d5dc04f3c2ace047e05c5932081d7576dae24a2c9bbf7f2a41dfafe2273de82`.
The detached collector harness source SHA is
`fcc69030ebbfbe7c5c69e2cf15b66897ec08e523ec9d859956e30bfc524ff699`;
the proof cache stays in the original warning-assembly root at source SHA
`ecf3b080d1808ee364b102610981e84e3397068159f5dd40caeba07a065097a0`.

Coordinator normalization preserves all original stop reports and prefix
receipts, appends only the cold collector receipt, and verifies **275 phases**,
263 parts, ten group bounds, the negative rejection and exact original coverage.
Normalized report SHA:
`ffaf21dbfea2e351b66093cbb52067fbf69fd5b324801d8caa1f884b42ff111b`;
normalized phase audit SHA:
`58bd30806f728d42e53bb6c3fc51d10515b83ec2b2060201d0fb18e2be759202`;
final 306-interface digest:
`bea149de03ae625d6f9996d033fc6a65b99a0ae6ef825c5a081d4e799cba4ee1`.
The source/cold-cache/flag/compiler and every prior-interface hash guard pass.
No Agda interface crosses machines. P1 remains byte-identical at `b2f6cd2d…`,
and all 74 core Agda/library files retain `a6234e52…`; static escape inspection
finds no postulates or unsafe flags. Existing paired core checks are preserved.

The fixed Group9 prediction, saved before its 31 checks with SHA
`0a55c023eab6822cd5f478896fa562a1ef0eb57ad8ce163d7a519fdb94e15d14`,
is 129.343050 CPU seconds versus 133.143559 actual, **−2.8544%**. It excludes
lower-side, generation, groups/collector, population and concurrent-throughput
costs; it is not a two-sided production forecast. The read-only census has
3,511,310 nodes and 182,087,351 payload / 22,189,636 compressed bytes across
306 interfaces: 75.0199%, 60.2108% and 64.7963% less than the 305-interface
packed baseline, including the new collector. The unchanged generic files keep
84 indexed-match warnings; every new accepted file has zero. These counts do
not estimate live heap.

Reproduction without rerunning Agda:
`results/warning-assembly6/validate_report.py` and `accounting.py`. The 20 outer
receipts measure 1,498.317367 CPU seconds and charge 1,498.317370 with the same
per-job microsecond ceiling as the ledger. Reused prefix and nested kernel CPU
are counted once. Total kernel work is 1,166.145596 CPU seconds; the four queue
and collector outer receipts total 1,334.485538 seconds. All jobs are collected,
categories unchanged, 44,455.691041 study CPU seconds charged, 310 withheld,
zero reserved, 41,634.308959 available. Final aggregate run storage is
10,735,058,944 bytes, below 10 GiB. The initial theorem and production GO remain
outstanding; no commit, push, tag or email is made.

## Matched lower pilot and checked covered roots, 7 October 2026

The twenty-root lower pilot is **incomplete**. Its uniform subsample seed
2026100701 is declared before generation or kernel timing, against all 120
completed canonical lower20 cases (original seed 2026100604, population 369,399
full-state classes). The canonical profile is retained unchanged:
`e6d42b54215f9a80572f38d7489d8616cb8677ea6354bf6c19f56b89aa096676`.
The trimmed copy produces the identical selected state sequence. Native
generation and independent scalar replay complete; those remain untrusted data
evidence. The sampled mean is 72,917.95 per-root D4 tokens, sampling SE
14,599.26. Sample-union sharing saves only about 0.26%; no population DAG ratio
or calibrated two-sided cost follows from this figure.

Preflight rejects ten entries larger than the fixed 32,000-token part cap.
Exact-state subtree factorization introduces 27 earlier citations without
removing a move or opponent reply. The original plan is retained, and the
factored plan passes scalar replay. Its 1,454,575 tokens equal the original
1,454,548 plus 27 citations. Its deterministic source-map identity is
`652dd6cab2d76e58c9b60aca443487f63f7d17cc7b340647d622daa7c30d8aaf`.
There are 714 parts (359/355 in the two ten-root groups), two group checks,
one collector and one negative fixture. Group 1 remains the unmeasured timing
holdout; no prediction or heldout result exists.

`lower20-kernel-20261007` first rejects the explicit false all-Black lower leaf.
It then accepts Parts0–121 with own targets cold and every existing private
interface hash unchanged. Part122 exits 251 with **heap exhaustion** at the
unchanged 1,350 MiB heap cap: 4.919099 CPU seconds, 1.383591 GiB RSS. Maximum
part RSS across attempts is 1.388000 GiB. The failed check leaves no own
interface. The 124 phases use 515.990358 nested CPU seconds; the outer driver
charges 637.460695 seconds, including source/cache/storage guards. Its safe
generated-source identity is
`1ddfb95561095750a5c83d502c6536df9469ab71c0b04d6f7a4d0448d870c3c5`,
Agda/library identity
`37287f2fa9014d4510469f1492a34e496ad32ce0e1714fb0b9b0ad938cb34fd0`.
The final pool has 32 generic plus 122 accepted own interfaces, with digest
`ee9b8d3afbf4b4ef40652ab59f67ab2ddf2dfe22ed0e0fcc06bcf6e0a3a9283c`.
No ten-root group or twenty-root collector is accepted.

`lower20-prefix-verify-20261007` verifies the stopped source/interface map and
exact recovery of all 122 accepted compressed logs, keeping the raw negative
and failure logs. It identifies two sampled roots already exported by Parts24
and 37. `lower20-covered-bounds-20261007` copies only the 32 generic interfaces
and Parts0–37 into a private same-binary cache, with immutable source links,
then checks the single cold `Tests.LowerPrefix6.Bounds` module. Agda accepts
`guarantee0` and `guarantee1`: **White guarantees raw difference at least +4
under original `Rules.game six` from sampled states `l109` and `l046`**.
These are lower bounds only. No certificate part is repeated. Assembly takes
1.290276 CPU / 1.304380 wall seconds at 0.586224 GiB RSS, with the same
1,350 MiB heap / 1.5 GiB RSS limits. The private cache grows from 70 to 71
interfaces, with all prior hashes unchanged and the original donor preserved.
New-source identity:
`29290a3d40ba8671001761cbe8cd08268f5fe2cce3ab32cfa98c7f3e8f501203`;
Agda/library identity:
`05a35f0989cd69627b0cee5b39bfd70cc9ea45cd7ffa0a5d02e6629f852db587`.

Both proof jobs use the recorded desktop binary
`c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`,
`--no-libraries --safe --without-K --cubical-compatible --save-metas`, and
module-local warning filtering only. No interface crosses machines, postulate
is introduced, or memory cap is raised. No initial-board theorem, full lower
sample, heldout gate or production GO is claimed.

The old raw native profile has 247 JSON files archived losslessly,
284,043,119 → 15,996,416 bytes, with reversible name and SHA maps. The first
archival CPU-limit failure is retained and charged; the corrected block-accounting
job preserves all source/proof hashes. Canonical native inputs are untouched.
The thirteen outer receipts, including tool/preflight failures, charge
**1,044.383477 CPU seconds** (raw sum 1,044.383476), using the same per-job
microsecond ceiling as the ledger. Nested phases are not added again. All jobs
are collected, category allocations unchanged, **45,500.074518 charged**,
310 withheld, zero reserved, **40,589.925482 available**. Last measured aggregate
run storage is 10,581,049,344 bytes, with 108,917,530,624 free; both guards hold.

Audits and normalized partial results: `results/lower-pilot6/audit.py`,
`accounting.py`, `report.json` and `budget.json`. Fetched original measurements
and source are under the matching `results/remote6/lower20-*` labels. All 23
P1 files and 74 core Agda/library sources retain their original identities.
## Lower memory recovery, 7 October 2026

The fixed sample remains seed 2026100701 from the complete canonical lower120
profile. A capped layout-only analysis selects index 4, `l015`, by the largest
transitive imported-state count among the eight unproved training roots. The
heldout group is not timed. The factored plan identity remains
`ce09d22ba8fb3f186b6510fcc161e0c73f4ef2abfb14799600e728e5a3a86e32`.
This is a deterministic stress choice, not another random timing sample.

`lower-local-kernel-20261007` checks a separate 118-part closure over exactly
17,232 entries / 195,314 tokens. It rejects the false terminal fixture, accepts
Parts0–113, and stops at Part114's unchanged 1,350 MiB heap. Its failed phase
has exit 251, 6.032481 CPU seconds and 1.388245 GiB RSS; all accepted parts
peak at most 1.392487 GiB. Nested kernel CPU is 475.907268; the outer receipt
charges 582.585790 seconds. The generated source identity is
`ae1a30081a29568539b7352988f0662ce67e698ff7b0652ce9d036e65ccb640b`;
Agda/library identity is
`9940bfd02faaf8e71783f31ea7322444fd506ea2d8176316e1c3045141f15f70`.
The original lower prefix and upper donor remain unchanged.

The independent prototype uses a safe generic `checkFrom-sound` proof over a
literal import trie. It requires `AllT (Proven …) imports` explicitly. Every
certificate byte and opponent reply is retained; routing-table dummy `L`
tags decode states and are never proof evidence. The first helper attempt
fails scope checking because `falseElim` was private in `Game.Shared`;
0.080864 nested / 2.570734 outer CPU seconds are recorded. A local two-line
impossibility proof corrects that helper in a new frozen root. No accepted
certificate is retried in this correction.

`independent-lower-kernel-fixed-20261007` checks the corrected generic proof
and rejects both false-terminal and missing-citation fixtures. It copies the
114-part checked prefix privately and checks only the four remaining
certificates as conditional facts:

| Conditional part | CPU seconds | Wall seconds | Peak RSS GiB |
| --- | ---: | ---: | ---: |
| 114 | 36.350433 | 36.417659 | 0.674271 |
| 115 | 48.128160 | 48.213852 | 0.805088 |
| 116 | 17.582574 | 17.621205 | 0.493362 |
| 117 | 40.888001 | 40.962375 | 0.792477 |

All use the original 1,350 MiB heap / 1.5 GiB RSS caps and safe,
without-K, cubical-compatible, saved-meta flags. Earlier proof modules are
not imported by these four checks. Their premises have **not** become
standalone root bounds. Root assembly discharges them from real earlier
exports using four trie-equality obligations, but stops at its 180-second
CPU cap (actual 180.057761), exit −9, with 2.566048 GiB RSS. The outer receipt
charges 352.356182 seconds, including 323.608460 nested kernel seconds.

The verified conditional cache has 151 interfaces, source identity
`0d35660bedd5982b4e70e0775dbf190f413dc1fc0472f4a2bce32c7b588b21ce`,
and Agda/library identity
`656ba63b962cbdf54b6f3a844a87cd9851555a3fd3303c54d54e7af5a5ba22fd`.
Its final report hash is
`ccc048e46062d64afb403da48b9c5829da67b424b77dd99275d646f36e8879d1`.
The phase-audit hash is
`7971e25a959b264d90528228903cef5122163929a942acd957bb08dab3493aa2`.
A separate read-only desktop audit verifies each receipt and exactly recovers
all five accepted logs, including the generic helper. Its report hash is
`1ac44472b677656b6721712a4a254c9d2df2e256d3fd8d294c2528541662904c`.

`independent-covered-root-20261007` reuses that complete prefix and all four
conditional parts without rechecking any certificate. A new collector replaces
the four trie equalities with checked Boolean `covered` obligations and
`covered-sound`. The transformation retains the literal imports and final
original-rule guarantee type. Its source hash is
`7c85f31519b3ac8b17cf992d26144a9d970afb642f303d2c7c7960c0430892bf`.
It uses the original 2,500 MiB heap / 3 GiB RSS caps, with only 74 CPU seconds
from the aggregate recovery budget remaining for this attempt. It stops at
74.085004 CPU seconds / 74.211477 wall seconds / 2.545609 GiB RSS, exit −9.
Total corrected recovery kernel CPU is 397.693464 of the declared 400 seconds;
including the earlier helper scope failure gives 397.774328, still below 400.
The collector-only outer charge is 80.233427 seconds.

The Boolean collector also rewrites one private `Game.SharedExport.agdai`,
from `af81ccdcf681af034eea4319860e3e82d1d2dadc97937e6acfcdd98c62124b05`
to `8e0eb05b3513fef00a2c349220fa811d393368e3eed066a1e43bc287e04f54f3`.
Every other copied interface and the original donor remain unchanged. This
cache is marked **not for reuse** locally and on the desktop; it is not
adopted as a checked continuation. The collector never creates its own
interface. Its raw log and failure receipt are retained. The independent
conditional cache remains the verified donor; its unused `Game.SharedExport`
interface must be checked in the new import context before reuse.

The coordinator's first normalization audit correctly stops on this private
interface change. The subsequent audit records the rejection and checks the
exact changed path/hashes rather than claiming an accepted cache. A separate
count assertion is corrected to distinguish 74 Agda modules from 75 files
including the library. The aggregate Agda/library identity remains
`a6234e52829fe28e5cab81a53907d090b5d4ec3f0a9174c6dbf3c7671f38f839`;
all 23 P1 files remain byte-identical with identity `b2f6cd2d…`. Source
inspection finds no postulates, holes or proof escapes. Existing paired core
checks are preserved; no new full-core or laptop proof check is claimed.

The twelve outer receipts charge 1,024.368889 CPU seconds once, including
both collector stops and the helper failure. Remaining CPU is
39,565.556593 seconds, with zero reservations and unchanged categories.
`results/lower-local6/{report.json,budget.json,audit.py,accounting.py,quarantine.json}`
records the normalized result. There are no new standalone lower guarantees;
only the earlier two sampled lower bounds remain complete. The full lower
holdout, twenty-root assembly, initial 6×6 theorem and production GO remain
outstanding. Next measurement: profile citation assembly and smaller per-owner
literal coverage obligations before another queue.

## Owner-directed citation assembly, 7 October 2026

`direct-citations-ready-20261007` accepts
`Tests.DirectCitations6.Root.guarantee` with type
`Guarantees (Rules.game six) white (lowerGoal 4) position`. The literal position
is the preselected training root `l015`, sample index 4:
`b000000001200101120111122120120200222` (20 discs, 16 empty squares).
It is one sampled lower bound, not the initial board or an exact-value theorem.
Together with the earlier `l109` and `l046`, it brings this fixed twenty-root
sample to three standalone original-rule lower +4 guarantees.

The new safe helper `coveredBy-sound` checks owner hints against actual
`CheckedExport` values. It reconstructs `AllT (Proven …)` on the literal target
trie using `knownIn-sound`, including full-state equality. Missing indices,
missing routes and omitted target branches fail closed. No computed union,
`selectExport` proof or imported native claim supplies evidence. The original
root position, terminal goal and original-rule transfer are preserved. All
114 accepted prefix parts and four accepted conditional parts are reused;
no certificate is changed or rechecked.

| Phase | CPU seconds | Wall seconds | Peak RSS GiB | Result |
| --- | ---: | ---: | ---: | --- |
| Generic coverage helper (earlier run) | 0.129976 | 0.140263 | 0.088509 | accepted |
| Corrected semantic fixtures | 0.108292 | 0.118360 | 0.094151 | accepted |
| Deliberately incorrect owner | 0.086609 | 0.096470 | 0.091225 | intended Boolean rejection |
| Import all accepted parts | 1.411647 | 1.424952 | 1.207924 | accepted |
| Discharge citations and prove root | 66.620216 | 66.766951 | 2.546799 | accepted |

All phases use the desktop Agda binary with SHA-256
`c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`,
`--safe --without-K --cubical-compatible --save-metas`, module-local optional
indexed-match warning filtering, and `-v tc.decl:10` for declaration profiling.
The assembly heap/RSS caps stay 2,500 MiB / 3 GiB; the root CPU cap stays 180
seconds. Certificate part caps are untouched and no new part is checked.
The import probe shows that loading alone does not account for the former
180-second merged-table timeout. The new root discharges 12,248 citations:
3,040, 4,101, 1,487 and 3,620 in the four suffix parts, respectively.
The separate earlier 74-second Boolean merged-table attempt remains censored.
No speed or full-population forecast is inferred from this single training root.

The complete cache is
`runs/six-direct-citations-ready-20261007/results/direct-citations6/check`.
It contains 154 interfaces, with source identity
`24d22f2515a1476d82cc42f6812857e84e573610e657877b42f8f2d2dac20e96`,
Agda/library identity
`5f4b564893111150c3576bd4993bf3f9b02770bc55b2f13732d5a38dccd0fa2b`,
and interface-pool identity
`bbc407e47e16d0e1b6978b3d0954bc07301f4144be15f34d7e1f7f1326d6c6ce`.
The accepted root interface hash is
`03e59f5e67f6a9ac84d0c2f2aa9c17d012fffd61d76997d680456ad8b08f96d1`.
The final report hash is
`e0daff978453825c97e4b6f66315857fedb2662727880795b2b225e94b38c085`.
The generated root source hash is
`4fc2490904b3c138605c026f6debd797255ad62a9c7d06eb8767414284b8f91a`.
The generic helper source hash is
`d59d4992ba0829f51f1082804171b5a6cb6e9c1083ad796405d0b4b5188e6028`.

The unused `Game.SharedExport` interface is excluded from the borrowed pool.
The newly used helper is compiled cold in the exact current mode, then reused
by source/interface hash. Original donors stay unchanged; the historically
quarantined Boolean collector cache is not borrowed or repaired.
`direct-citations-audit-20261007` verifies the original donor, the new pool,
all phase receipts, the intended false-owner diagnostic and exact recovery of
four accepted logs, including the reused helper. Its report hash is
`8a0aeee172e37a47c9f8885af691ae2e2b7517f544bbd6493acd24bc455c4ab3`.
The audit charges 0.336253 CPU seconds and accepts.

Two setup failures remain preserved: the first semantic fixture leaves the
game parameters of an empty export list unspecified (UnsolvedMetaVariables),
then a relaunch stops on a Python f-string escape error before any Agda
execution. Their outer charges are 3.030834 and 0.019448 CPU seconds. The
accepted helper is not repeated. Four generator guards pass before the first
launch and again after the fixture/generator fixes. The corrected detached run
charges 76.930824 outer CPU seconds, including 68.226764 nested Agda seconds.

All six outer receipts charge 80.498351 CPU seconds once. Remaining study CPU
is 39,485.058242 seconds, with zero reservations, fixed category allocations
and the existing 310-second withholding unchanged. No job remains active.
`results/citation-profile6/{report.json,budget.json,finish.py}` verifies
receipt accounting, all 23 original P1 files, the unchanged 75-file core
Agda/library identity `a6234e52829fe28e5cab81a53907d090b5d4ec3f0a9174c6dbf3c7671f38f839`,
and zero core postulates or proof escapes. No new full-core or laptop Agda
check is claimed. The untouched lower holdout, remaining seventeen sample
bounds, two-sided production forecast and initial theorem still need work.
Only about 21 MiB of study artifact headroom remains at the audit launch;
recover space with verified lossless archival before expanding the pilot.
## Owner-directed lower continuation, 8 October 2026

The persistent completion goal retains the existing study allocations and
production gates. No initial-board Problem2 inhabitant is asserted.
`owner-lower-preflight-20261008` describes the same fixed twenty roots and
preserves the ten-root timing holdout. The initial reuse boundary contains
35,296 states from the 122-part lower prefix and completed `l015` closure.
Later roots cite earlier new exports, so no accepted certificate is repeated.
Five generator guards, four prospective-estimator guards, and two split guards
pass in three metered laptop runs.

`owner-lower-training-20261008` accepts 36 conditional parts, nine citation
assemblies and two cold guarantee modules:

- `Tests.OwnerLower6.Root2.Check.guarantee`, original `Rules.game six` White
  lower +4: 1.439661 CPU seconds / 1.218624 GiB RSS.
- `Tests.OwnerLower6.Root3.Check.guarantee`, the same original-rule goal:
  1.492577 CPU seconds / 1.154846 GiB RSS.

The fixed sample now has five standalone bounds. Root 2's 9,749 citation
premises accept in 47.902797 CPU seconds at 2.525143 GiB RSS. Each premise
still uses a real owning export and full-state membership; dummy routing leaf
tags and owner indices supply no evidence. The conditional certificate parts
remain within the 1,350 MiB heap / 1.5 GiB RSS caps. Assemblies retain
2,500 MiB heap / 3 GiB RSS limits. Core/P1 source bytes stay unchanged.

Root 5's final assembly fails at Part26 coverage with exit 251, 9.811545 CPU
seconds and 2.510731 GiB RSS. The run preserves 323 interfaces; its 391.194316
nested CPU seconds are included in the single 449.659524-second outer charge.
The completed cache source hash is
`f9376a762ec8b553a02c8e93921ce1e1d39b6ea839cc1f6146e4dd78a0cb19f4`;
the interface-pool hash is
`2ecd5ca8763e4269ae7b9521f8b0da5d0f54dcc9e5082bc3343a7770047c4a04`.
The final report hash is
`30b6b89f982a86fb79e849517377cfc7f07fda9f2fffcc00de398f8374eb962d`.

`owner-lower-split-20261008` changes only that failed assembly in a new private
root. Its first two individual bindings accept in 4.665002 and 5.534221 CPU
seconds. The third still exhausts the 2,500 MiB heap (exit 251, 5.948411 CPU
seconds, 2.507130 GiB RSS). The facade and root guarantee are not checked.
No original source or accepted interface is modified. The 325-interface donor
source hash is
`8a10e0a422b2b88fa0bcb1facfdbe5f7954d4295fa573d03021fdf03a307dd77`;
its pool hash is
`9e5efaf41de499b192890d74d4b25c93520aff20311bf6bf6b5efd8f5f59104f`.
The split report hash is
`dfc012d745b1f09cd720fe350f89a5967b2371473720cfa4ff2e187637d8e56b`.
The 16.147634 nested CPU seconds are included in the 20.144886 outer charge.
Both failures are censored feasibility evidence. Splitting alone does not
solve this citation lookup's memory cost.

`owner-pilot-audit-20261008` accepts a read-only audit of both preserved prefixes,
including 47 original acceptances and two split acceptances, exact compressed
log recovery, all receipts, binary/safety flags and interface hashes. It charges
0.260358 CPU seconds. The initial +4 theorem, remaining lower roots and real
heldout prediction/check remain incomplete. The prospective driver is guarded
against incomplete or censored training; no actual fit is claimed.

`closed-native-archives-20261008` losslessly gzips seven closed iteration JSON
files. The mapping and original/archive hashes are recorded before unlinking
raw names, and decompression verifies the original bytes. Canonical inputs,
transposition tables, Agda sources/interfaces and measurement receipts remain
unchanged. Allocated study bytes fall from 10,718,699,520 to 10,153,734,144
(538.793945 MiB recovered), under the unchanged 10 GiB limit. This is archival,
not proof evidence. Its outer charge is 7.235950 CPU seconds.

`results/owner-lower6/finish.py` verifies eight collected outer receipts against
the sole coordinator ledger and writes the current report/budget. They charge
480.812801 CPU seconds once, including both failures (480.812800 measured,
rounded up to ledger microseconds). Categories are unchanged; available CPU
is 39,004.245441 seconds, with zero reservations. All 23 tagged
P1 files and the current 75 Agda/library files retain their recorded identities.
No postulate, native trust fallback, production run, commit, publication or
email is introduced.

## Opaque citation checkpoint, 8 October 2026

The later checkpoint takes precedence over the earlier budgets above.
`results/owner-memory6/finish.py` verifies seventeen collected outer receipts,
source/cache identities and unchanged P1/core. They charge 511.856835 CPU
seconds once, including failures; the ledger has 38,492.388606 available and
zero reserved. No category or memory/storage cap changes.

| Experiment | Checked result | Remaining failure |
| --- | --- | --- |
| States-only lookup and prefix-trie joining | Generic lemmas and negative fixtures | Closed coverage exhausts the desktop heap |
| List checker, 64 entries and then eight | Generic soundness and Boolean premises | Transparent proof application exhausts the heap |
| Separate data and proof modules | First eight Boolean premises | Transparent proof application still exhausts the heap |
| Opaque `Citations` API | First eight actual premises and conversion to `AllT Proven` | Does not itself prove the complete import invariant |
| 37 further opaque batches | All remaining 2,335 premises | Final binding exhausts the heap while loading interfaces |

All new Agda sources use safe checking and ordinary equality. `Citations` is
defined as the original list of `Proven` facts; its opaque API has checked
joining and trie-conversion lemmas. Owner hints are checked against full
states and actual checked exports. No Boolean lookup table supplies a proof
without its owner-association premise.

`owner-opaque-kernel-20261008` checks the first eight-entry proof in 2.776365
CPU seconds / 2.486202 GiB RSS, and its original trie invariant in 10.255166
CPU seconds / 2.507816 GiB RSS. Its 334-interface donor remains unchanged.
`owner-packed-ready-20261008` reuses these proofs and every conditional
certificate. Its 75 accepted phases comprise the closure lemma and 37 data /
proof pairs. All 2,343 citation premises now have checked opaque list proofs.
The 76th phase, Binding, fails during interface loading before any binding
declaration: exit 251, 2.862647 CPU seconds / 2.502350 GiB RSS, under the
unchanged 2,500 MiB heap / 3 GiB RSS limits. The whole-list join, complete
input invariant, facade and root5 guarantee remain unchecked.

The 409-interface prefix is preserved at
`runs/six-owner-packed-ready-20261008/results/owner-packed6/check` on the
desktop. Its source SHA256 is
`3a360ad15f3953c80b766e8ff3c2dcfd205806c402d43caa4ba3bb56d133f061`,
interface-pool SHA256 is
`c3173b242174c1e0aa9e2bb950283db29d0693dc76568e8a44c49dbceab9ff58`,
and final-report SHA256 is
`f0c0569eacffe64752b23608ece61f3ffab32d72e93a0d2b196b0d1350b809b4`.
The outer receipt charges 418.812644 CPU seconds, including 349.283599
nested kernel seconds. Desktop Agda binary SHA256 remains
`c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842`.

The fixed lower sample remains five of twenty guarantees. No lower holdout
is timed, no production GO is issued, and the initial 6×6 +4 theorem and
optimal 16–20 strategy pair remain unproved. No accepted certificate is
repeated, no postulate is introduced, and no publication or email occurs.

## Scope-compaction checkpoint, 8 October 2026

The read-only `owner-interface-census-ready-20261008` binds the preserved
409-interface pool and finds 4,933,708 nodes / 248,517,200 payload bytes.
Its 75 new interfaces contain 694,471 nodes / 42,132,778 bytes and zero
saved metavariables. The counts are serialization diagnostics, not kernel
acceptances or live-memory predictions. The earlier missing-output-directory
failure is retained and charged.

`owner-capsule-ready-20261008` accepts the same first new 64-state slice in a
single module with private imports: 6.328687 nested CPU seconds, 2.505985 GiB
RSS. Its 11,497 interface nodes compare with 18,577 for the former data/proof
pair; payload bytes are 616,465 versus 1,134,413. This changes wrapper layout,
not a certificate or a checker premise. The initial wrong-donor-hash launch
is rejected before Agda and is retained as a setup failure.

`owner-capsule-full-20261008` reuses that accepted capsule and the original
checked closure lemma. All 36 remaining capsules accept. The final binding
still fails during import loading, before declarations: exit 251,
2.829587 CPU seconds, 2.503807 GiB RSS, under the unchanged 2,500 MiB heap /
3 GiB RSS caps. Its 372-interface prefix is preserved; no final binding,
facade or root guarantee is accepted. Source/pool/report identities are in
the current handoff and `results/owner-scopes6/report.json`.

The single-scope alternative, `owner-single-20261008`, also fails during
imports (2.881043 CPU seconds, exit 251). A GC comparison's initial `-F0.5`
setting exits during runtime startup, with only 1,357,688 maximum-residency
bytes; it is not an import-cost measurement. The corrected
`owner-gc-ready-20261008` uses `-F1.1 -A1M`, with identical obligations,
borrowed interfaces and compiler. It still fails during imports:
5.543135 CPU seconds, 2.507442 GiB RSS, maximum residency 2,575,252,640 bytes,
exit 251. Its final-report SHA256 is
`966c1559b093d0b12fcb8e49b93999bcd5b6726f4b44193aaeb2ee313cc1580b`.
No heap, RSS, CPU allocation or production gate is increased.

`owner-cache-dedup-20261008` verifies ten closed caches and the original
325-interface donor, then replaces 3,250 timestamp/mode-identical duplicate
interfaces with immutable hardlinks to their byte-identical donor files.
All paths, source/interface bytes and measurement receipts remain unchanged.
Its reversible mapping is preserved. Allocated run-directory bytes fall from
10,638,430,208 to 10,378,829,824 (259,600,384 recovered), and the receipt
charges 2.845993 CPU seconds. Future checking uses private copies. This is
storage maintenance, not proof evidence.

`results/owner-scopes6/finish.py` verifies all ten outer receipts against the
sole coordinator ledger: 326.625488 CPU seconds charged once, including
failures, 38,165.763118 available, zero reserved. No study job remains active.
All 23 tagged P1 files and the 75 core Agda/library files retain their
recorded source identities. Conditional certificates are not repeated.
Postulates remain zero. The lower sample remains five of twenty guarantees,
the lower holdout is untimed, and production has no GO. The initial +4
theorem, optimal 16–20 pair and final submission package remain incomplete.
The current attempt stops at the approved desktop assembly memory limit.

## Owner-dependency checkpoint, 8 October 2026

The read-only `owner-closure-plan-20261008` emits unchecked proposals and a
lexical dependency comparison. It counts 305 existing interfaces originally
and 293 existing interfaces plus 28 new modules in the proposed individual
layout. Those counts establish no live-memory saving or proof acceptance.

`owner-pruned-20261008` instead checks nine grouped owner modules: isolated
root4 P114, root5 Assemble0–5, and separate P24/P25 bindings. Certificate
bytes, conditional soundness lemmas, routing literals and owner-block proof
bodies remain unchanged. Each new binding has a cold own target, exact
same-machine borrowed interfaces, the recorded Agda binary, safe flags,
`--save-metas`, `-M2500M`, and a 3 GiB RSS stop. All nine accept. The tenth
module, P26, exhausts the heap during its coverage Boolean reduction:
6.460138 CPU seconds, 2.507275 GiB RSS, exit 251. It emits no interface.
The root guarantee is not attempted or adopted.

The accepted 336-interface prefix is
`runs/six-owner-pruned-20261008/results/owner-pruned6/check`.
Source SHA256:
`dbadb290e9b18df75e2078d3e71ffe2a59c0b2adff7ef4b787936c5ec343dff6`.
Pool SHA256:
`94d49b5975e52fc3b2c7c3a5146772b38bdcf57189fa561c26b168528b9a7ec1`.
Report SHA256:
`3279a84f343383a7c41c0652a6eecb29c2ea6bf923dd82a08b4e53a71d5991e3`.

`owner-rebind-20261008` audits and stages those nine accepted proofs together
with the previously checked opaque API and generic closure. Its immutable
345-interface staging prefix supplies independent interface copies to a
fresh check root. The complete Citations module exhausts the same heap during
imports, before declarations: 2.932772 CPU seconds, 2.505623 GiB RSS, exit 251.
No new interface or bound is accepted. Source SHA256:
`0b4515f1c6f07c6fa5d86dfb66f4ad9b8d7a04421797bf92eb4f0c7e27f5e98a`.
Pool SHA256:
`204310ee1d68cfec80c51449705df6ad7e85094c3acc4df6aa0adf419f42ddee`.
Report SHA256:
`acc5731ac9fde89ee2db91aaf0ac6f648ddc3cc471dca19ed68da68dcd071229`.
All donors, accepted citation batches and failed sources/logs remain intact.

| Outer receipt | Category | Charged CPU seconds | Result |
|---|---|---:|---|
| owner-closure-plan-20261008 | native | 0.544297 | Diagnostic only |
| owner-pruned-20261008 | assembly | 100.708284 | Nine modules accepted; P26 heap failure |
| owner-rebind-20261008 | assembly | 6.451265 | Citation import heap failure |

`results/owner-dependencies6/finish.py` reconciles all three receipts against
the sole ledger and checks the phase cache chain, flags, source identities and
P1/core preservation. Exactly 107.703846 CPU seconds are charged once, leaving
38,058.059272 available with zero reserved. No study job is active. The study
allocations and all caps are unchanged. The current attempt stops at the
approved desktop heap limit. The lower sample remains five of twenty, the
holdout is untimed, and production has no GO. The initial +4 theorem, optimal
16–20 pair and final submission package remain incomplete; postulates are zero.

## Warning metadata and accepted root5 assembly, 8 October 2026

The read-only `owner-fields-20261008` census identifies four remaining
`RewritesNothing` warning documents with roughly 62,423 rendered characters
per original certificate interface. The diagnostic neither edits interfaces
nor establishes a proof. The warning tag is identified from the
[pinned Agda serialization source](https://raw.githubusercontent.com/agda/agda/cb568525/src/full/Agda/TypeChecking/Serialise/Instances/Errors.hs).

`rewrite-filter-20261008` checks two unchanged certificate bodies in fresh
namespaces with `-WnoRewritesNothing` in module-local options. The warning
option is absent from the CLI, preserving the accepted generic dependency
interfaces. Both own targets are cold, safe and accepted. Payload bytes fall
536,120 → 177,684 and 545,754 → 187,318; retained warnings become zero.
The compiler emits these interfaces normally; no serialized bytes are edited.

`rewrite-prefix-20261008` adopts those two accepted pilot interfaces and checks
the other 234 original prefix certificates cold. Certificate literals and
proof terms are unchanged apart from namespaces and local warning output.
All parts accept, with maximum part RSS 0.878365 GiB under the unchanged
1,350 MiB heap / 1.5 GiB RSS limits. The final pool has 267 interfaces.
Original donors, sources, generic interfaces and logs remain intact.

`rewrite-owners-20261008` reuses that complete prefix and 28 original conditional
parts in a fresh private cache. All eleven owner/assembly/root modules accept.
The complete P26 coverage check uses 11.150054 CPU seconds / 1.521591 GiB RSS;
the final original-rule root uses 1.046840 / 0.611038. Its existing caps are
2,500 MiB heap / 3 GiB RSS. The accepted fact is
`Tests.RewriteOwners6.Root.guarantee`, raising the fixed sampled lower bounds
from five to six of twenty. This is a sampled frontier position, not initial6.
The initial +4 theorem and optimal 16–20 pair remain unproved.

The complete owner donor is
`runs/six-rewrite-owners-20261008/results/rewrite-owners6/check`, 308 interfaces.
Its source SHA256 is
`7d430df537707a4aae4f00bbbd77b8531fc829c9f48df772ddd69f7675c9e51a`,
pool SHA256 is
`bd5c3829ff681ebe7ff9d6a2bae42911ad24c2f24f9515045547443b34c632f1`,
and final report SHA256 is
`079859e69971195de5640846bb083c37364360b2d74f696f51a95b5f79b42799`.

| Outer receipt | Category | Charged CPU seconds | Result |
|---|---|---:|---|
| owner-fields-20261008 | native | 0.423839 | Read-only diagnostic |
| rewrite-filter-20261008 | kernel | 8.022519 | Two new interfaces accepted |
| rewrite-prefix-20261008 | kernel | 1081.184765 | 234 further interfaces accepted |
| rewrite-owners-20261008 | assembly | 93.684616 | Original-rule sampled lower root accepted |

`results/rewrite-memory6/finish.py` reconciles these four receipts with the
sole ledger, safe flags and interface chain. It checks all 23 tagged P1 files
byte-for-byte and the unchanged 75-file core identity. Postulates remain zero.
The checkpoint charges 1,183.315740 CPU seconds once, leaving 36,874.743532
available with zero reserved at collection. No production gate is relaxed;
the timing holdout is untouched. A subsequent bounded training continuation
has its own reservation and must be reported separately.

## Complete lower training and fixed holdout launch, 8 October 2026

The first new training launch fails its source guard before any Agda check,
0.524393 CPU seconds. Its frozen log is retained. The retired failed combined
root5 binding had been replaced by the audited split facade; the new driver
imports no unchecked facade. Every actual training/holdout source remains
pinned to its original preflight hash. A read-only precheck fixes the new
namespace/private-scope layout, 0.849780 CPU seconds, and supplies no proof.

`rewrite-training-ready-20261008` accepts all 122 planned phases: six earlier
owner rebindings, 89 new conditional certificates, 23 citation bindings and
four original-rule root guarantees. Roots 6–9 raise the fixed sampled lower
bounds to ten of twenty. Every earlier conditional proof is reused unchanged.
Part RSS maximum is 0.657429 GiB, binding maximum 1.932735 GiB, within the
original 1.5 / 3 GiB guards. Actual outer CPU 770.326442 seconds includes
643.800157 nested checker seconds; charge the outer receipt only once.

The accepted 442-interface donor is
`runs/six-rewrite-training-ready-20261008/results/rewrite-training6/check`.
Source SHA256:
`e6d037a4fc2ff747dea8b9fd07341b9d7b560e1a5a7bcb6bbefc08f6fbb85518`.
Interface pool SHA256:
`e0264b83fc6c67c7fba9ea344b06c6c3557c90daaac722c3e4e60bb4517a25d7`.
Final report SHA256:
`fa3678d95569c1f55c6843a05ff5b63829b02205e7b350d749b028fab49bba73`.

Twelve focused guards pass, including censored/partial training rejection,
fixed untouched holdout preservation, missing/forward citations and withholding
the gate residual after incomplete holdout results. Local measured CPU is
0.089620 seconds. The read-only prospective fit audits the complete training
receipts, interfaces and recovered raw logs; actual native CPU 0.372803 seconds.
Its three nonnegative models predict 2,301.086121 nested CPU seconds across
451 heldout phases. Forecast SHA256 is
`c316151e5700de958f2cbad2ef8adaae1ef723b5bfabd61f859c0abd1c3785a3`.
Setup/driver and earlier rebindings are excluded and must be added in a full
workflow estimate. No heldout timing entered this fit.

The exact deduplication of 608 interfaces in three closed caches recovers
26,865,664 allocated bytes. The receipt charges 1.619319 native CPU seconds;
before/after proof bytes, source hashes, paths, timestamps/modes and receipts
are unchanged. Unique interfaces and all failed evidence remain intact. The
reversible mapping is `results/remote6/rewrite-cache-dedup-20261008/artifacts/results/rewrite-dedup6.json`,
SHA256 `ec9572730d0d792059393c8d057e628068bac71ecef3506261bea9670fdecc4f`.
All later mutable caches use independent copies.

The detached `rewrite-holdout-20261008` checks only the ten predeclared holdout
roots with that fixed forecast. It is live, with 4,000 outer CPU seconds,
3,300 nested seconds and unchanged part/assembly caps. A 4,002-second kernel
reservation remains held until collection; no final acceptance or residual is
claimed at launch. The current ledger is 49,989.038825 CPU seconds charged and
32,098.961175 available. P1/core and zero postulates are preserved. Production,
the initial +4 theorem, optimal pair and final submission package remain pending.


### 8 October: storage stop and guarded holdout continuation

`rewrite-holdout-20261008` accepts 287 cold phases with unchanged sources,
compiler and dependency hashes, including complete roots 10–12. All root13
conditional parts and its first two assembly modules also pass. This gives
thirteen of twenty sampled original-rule lower +4 guarantees. Its unchanged
10 GiB artifact guard stops before the next phase; no Agda rejection occurs.
The final 729-interface pool is preserved. Actual outer CPU is 1,709.532803
seconds; nested checker CPU is 1,416.590373. The collected outer receipt is
charged once, and its reservation released. The partial holdout residual is
censored, so no numerical prediction-gate acceptance is asserted.

Final holdout report SHA256:
`4590a46fdc10b1934dfde15b1881a92e75feea05e4d1aa3cfe09001c5f78b43b`.
Source SHA256:
`e6d037a4fc2ff747dea8b9fd07341b9d7b560e1a5a7bcb6bbefc08f6fbb85518`.
Pool SHA256:
`8a330bf11d7943d74b176868e2a8c48c61058f0a028070a8bb7526142fce8d24`.

`raw-headroom-20261008` archives the remaining 113 old raw native-profile JSON
iterations, with original digests, compressed digests, verified byte recovery
and mappings persisted before removing raw allocation. It recovers 77,488,128
bytes. The requested 512 MiB headroom is not met; its failure receipt and all
archives remain preserved. Actual assembly CPU 1.336207 seconds is charged.
Report SHA256:
`73a435fbe839958f7622e14aebf907e05b49496ca590750ba3fb71c0d6aac063`.
Canonical data, transposition tables, sources, proof caches, receipts and failed
proof logs remain untouched.

`closed-cache-allocation-20261008` shares allocation for 5,260 exact identical
interfaces in sixteen closed immutable runs. It recovers 265,662,464 bytes,
verifying unchanged source identities, interface bytes, paths, timestamps/modes
and receipts. Future mutable caches use independent copies. Actual assembly
CPU 2.550336 seconds is charged once. Report SHA256:
`2b5e147cba37cedd729d731170a5625f4ecd7cb1ddaf6fb1899522674b783fb7`.
The initial four-MiB artifact fetch is rejected by its transfer guard; a
sixteen-MiB fetch retrieves the unchanged 4,478,922-byte report. This changes
no study resource cap.

Seven focused resume/isolation tests pass, rejecting non-prefix, changed,
failed, miscounted or refitted holdout inputs, and checking private interface
copying. Local native CPU 0.094510 seconds is charged once.
`rewrite-holdout-resume-20261008` audits and copies the 729-interface donor and
287 phase receipts/log archives. It checks only the remaining 164 phases with
the same source, binary, part/assembly caps and prospectively frozen forecast.
The total nested allowance across both runs remains 3,300 CPU seconds. Its
outer cap is 1,900 seconds; a 1,902-second kernel reservation is held until a
real final receipt is collected. The last observed active MainPID is 2847796.
All previous cold proof checks retain their original receipt identities; reused
nested CPU is not charged again. At launch the ledger has 51,702.552681 seconds
charged and 32,485.447319 available. The initial theorem, optimal pair and
production GO remain pending; P1/core and zero postulates are preserved.


### 8 October: complete fixed lower holdout and resource screen

The continuation accepts all 164 remaining cold targets, reusing the original
287 accepted phase interfaces and exact receipt/log bytes. All ten predeclared
holdout roots now export original-rule lower +4 guarantees; the fixed lower
sample is twenty of twenty. The complete 451-phase holdout uses 2,365.059312
checker CPU seconds versus 2,301.086121 predicted before any holdout check:
relative error +0.0278013, within the approved ±30% gate. No refitting occurs.
Maximum part RSS is 0.846848 GiB; binding RSS 2.552452 GiB, under unchanged caps.
The new outer receipt charges 1,135.162970 CPU seconds once; the earlier
1,709.532803 disk-stop receipt remains separately charged. Reused nested CPU
is never charged again. The new reservation is released after collection.

Complete donor:
`runs/six-rewrite-holdout-resume-20261008/results/rewrite-heldout6/check`
(893 interfaces). Final report SHA256:
`9b82e8ddab8e533240e5f6394eb664880ae38fd88cd442fcd20aa031111f8e67`.
Source SHA256:
`e6d037a4fc2ff747dea8b9fd07341b9d7b560e1a5a7bcb6bbefc08f6fbb85518`.
Pool SHA256:
`84549d51d96db2c8522c79723e0bcb007e65f858c579d184a690beaf633ccfe7`.

Three resource-screen guards pass, rejecting incomplete or changed/refitted
holdout evidence, censored/wrong-population native samples, and production GO
from an incomplete workflow. Local native CPU 0.096208 seconds is charged.
`workflow-gate-20261008` performs a read-only audit of all 451 proof receipts,
compressed raw log recovery, exact source/IFace hashes, safe flags, caps and
cold targets. It charges 0.463490 native CPU seconds. Resource report SHA256:
`21bdddec935be9282e24702a96a1ec5ea308f0709ed761b15f5fe33d970e7476`.

The current per-frontier design has a nominal 9,166.459 token CPU-hours,
1,729.417 wall-hours with the older controlled 6.625-slot reference and 25%
margin, and 76.636 GiB compact certificate data. Both 168-hour / 10-GiB gates
fail before fixed exports/imports, assembly, initial skeleton, generation,
interfaces/logs, joint line and final checks. These are statistical components,
not rigorous runtime lower bounds. Small-sample union savings are not projected
onto the full population. The sampled timing and memory gates passing supplies
no production GO or initial-board proof.

A bounded native `full-dag-census-20261008` measures a single initial lower
certificate DAG, using the exact original full-key TT and binary read-only.
It emits counters only, not graph states or proof premises. Limits are 100
million retained states, 8,192 MiB native tables, 750 native / 820 outer CPU
seconds, 8.25 GiB sampled RSS and 1,200 seconds wall, within the unchanged shared
15-GiB slice and disk gates. Incomplete counts remain censored and cannot be
extrapolated into a production GO. Native TT SHA256 is
`7886f35fc835b64ad458e7ccb91475200bf44e4065e8d707d1a6ebcee61497d8`;
frozen measurement source SHA256 is
`94083a98be5c12dfd3acd4c57b1a6bfbffbd45d9872d2d0b5733bd879c500612`.
At its launch checkpoint, 52,838.275349 CPU seconds are charged, 822 reserved
and 32,429.724651 available. The original complete lower pilot, all safe proofs,
P1/core and zero postulates remain preserved. Initial +4, the optimal pair,
production and private final packaging remain unfinished.

### Initial census cap and canonical witness experiment, 8 October

`full-dag-census-20261008` is terminal and collected: 113.957753 outer native
CPU seconds, 6.995720 GiB peak RSS, unchanged donor/TT/binary. Its native
measurement reaches 100,000,000 retained states, 128,376,765 DAG edges and
554,741,296 expanded tree occurrences, then stops at the state cap. The report
is censored, not a complete graph estimate. Report SHA256:
`307231a823227098a9d93415cba2dfe6f9503a447b0606c61ed5a4c33f5c0e9d`.

`canonical-census-build-20261008` builds experimental generated C with D4
normalization before census memoization and witness move selection. Removing
that delta recovers every byte of the original solver/rules/TT source. The
original native binary and all core Agda files are untouched. Compiled CPU
0.473759 seconds is charged once; the build report SHA256 is
`326754c3b8799f630bfdeb3275fd3a8bbd1c6d1735568271229b6cbdcf6c5925`.

`canonical-census-tests-20261008` accepts 169 positions / 1,352 D4 images
against independent scalar transformations, moves and flips. Its 72 endgame
threshold cases compare exact scalar values, reject wrong bounds and replay
every node of accepted small canonical certificate graphs. Forced pass and
single-disc basis fixtures are included. Actual native CPU is 0.234764 seconds,
charged once. Test report SHA256:
`b835713944140e6f61140542f40c46bb3d40841180dbad00a9239f848eaacd7b`.

The matching counts-only `canonical-census-20261008` is launched separately,
with the same state/table/CPU/RSS caps and original read-only TT checkpoint.
Experimental native testing and counts remain outside proof premises; all
initial lower/upper checks and the optimal pair are still required. The
production gates, category allocations and zero-postulate rule are unchanged.

The canonical row-major census is now collected at its state cap: 413.817162
outer CPU seconds, 6.997715 GiB RSS, 100,000,000 retained nodes, 130,018,809
DAG edges and 522,665,308 partial tree occurrences. Its report SHA256 is
`2da635640c08b5e4eb55f0971172c5325ee64035cb4314c7cb32481529f3e8f1`.
Different visited prefixes prevent comparing censored ratios as whole-graph
improvements. No native count is used as an Agda premise.

`canonical-order-build-20261008` changes only census witness ordering: fewer
legal replies first, corners as a tie-breaker, and a bound query before every
selected move. Selected indices remain row-major. Compilation is accepted at
0.474887 compiled CPU seconds; build SHA256:
`8c3bbbad616897ec059943fa21533705a97dd43cd1e083ba9b61f9e9496e7ea6`.
Matching tests accept 1,352 images and 72 scalar bound/graph replays, charging
0.235208 native CPU seconds. Test SHA256:
`0e06ccc54e3d939e81bdd31b8bb700d750499f0cf81c5548bdec93b30d1b9ca5`.
The initial counts-only run is separately capped at 480 native / 520 outer CPU
seconds, 900 wall seconds and the unchanged state/table/RSS limits. The original
solver/rules/TT source and binary, safe proof donors and core/P1 are preserved.

The alternate-policy run is terminal and collected at its 480-native-CPU-second
cap: 480.000326 measured native / 481.580738 actual outer CPU seconds, 4.282242
GiB peak RSS, 39,203,503 retained states, 46,771,148 DAG edges and 97,872,172
partial tree occurrences. `oracle_aborted` is true and graph completeness false.
Donor, TT, binary and frozen source checks remain unchanged. Final report SHA256:
`40061d625bf7e3d4d16bac052cda8c0227aa1be3989f72234d9c0585495003c4`.

The checkpoint reconciles every new outer receipt once, with no outstanding
reservation or uncollected result. Charged CPU is 53,849.049620 seconds, total
available 32,240.950380, but native availability only 51.496772 seconds. No
categories are reallocated. All initial censuses remain censored and the
current per-frontier forecast fails production gates. This is a resource stop
in the feasibility study, not a completed initial theorem or proof of
infeasibility for every possible method. Initial +4, the optimal 16–20 pair,
final machine checks and private packaging remain required. P1/core exact
source identities and zero source postulates are verified again by the
coordinator checkpoint.
