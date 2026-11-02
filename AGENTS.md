# othello-agda

Current6×6 status,19 October2026: safe Agda accepted the full standard initial
raw+4 theorem and the SAME optimal pair's Black16/White20 completed legal play.
The canonical completion/evidence record is
`results/problem2-completion6-20261019.json`; the private package/restoration
guide is `docs/private-problem2-package6.md`. All23 tagged P1 sources remain
unchanged. Stage descriptions below retain history; accepted/failed terminal
jobs are not unfinished jobs to restart.

This project proves the exact raw-score value of standard 4×4 Othello.
Use `--safe --without-K --cubical-compatible` in every core Agda module.
No postulates, holes, termination escapes, positivity escapes, or imported
solver claims are allowed in completed project proofs.
The core uses Agda.Builtin modules and a small checked Prelude. The laptop
compiler rejects a transitive standard-library 2.3 dependency that the desktop
accepts; do not enable unsafe irrelevance flags to bypass this mismatch.
Cubical modules may be separate optional modules; preserve the core build.
Source and the single writable study6 ledger are authoritative on desktop
at `/home/eapiova/projects/othello-agda-main` (host `eapiova`). The laptop
copy is an archived, blocked reference; do not restart its coordinator.
The migration handoff and preserved conversation history are in
`/home/eapiova/Documents/Codex/othello-desktop-migration-20261018/handoff.json`.
The standard initial6x6 White-minus-Black+4 theorem with the SAME optimal pair
ending Black16/White20 has an accepted safe Agda proof. Preserve its exact
sources, receipts, private package, tagged P1 and zero postulates. Original4x4
results remain preserved. Consult the canonical completion record for current
ledger and resource status.
The user revoked MIGRATION-HOLD on 18 October 2026; the current override is
`results/migration-hold-revocation6-20261018.json`. It supersedes only the
migration execution hold in the preserved handoff. Work must respect existing
experiment authorizations, CPU budgets, and storage limits. The revocation
grants no extra budget or new experiment authorization.
On 18 October 2026 the user separately authorized continued formalization and
all tests needed to complete 6x6 within the already assigned budgets and all
existing limits, without confirmation for each individual test. See
`results/completion6-continuation-authorization-20261018.json`. Preserve prior
charges and previously recorded stage usage. On18 October2026 at12:32:55UTC
the user explicitly approved transferring32000 unused native CPU seconds to
Agda kernel and authorized necessary compute increases under finite,
proportionate recorded caps, preserving RAM/disk/stability safeguards and
without paid services or purchases. See
`results/completion6-budget-authorization-20261018.json`. Applied allocations:
native39602, kernel109800, compiled1798, assembly21600 CPU seconds; total172800
is unchanged. The additional unused-category transfer (8000 compiled and5000
native seconds to kernel) and finite full-row production caps are recorded in
`results/full-row-production-authorization6-20261018.json`. Do not reset prior consumption or silently extend caps.
The reviewed recovery is recorded in
`results/full-row-resume-authorization6-20261019.json`: an additional unused
3000 native and1700 compiled CPU seconds were reassigned to kernel, with no
increase of the172800 total. Current allocations are native36602,
kernel116000, compiled98, assembly20100 after separately recorded400CPU,
200CPU,300CPU and600CPU assembly-to-kernel final-check transfers. Total172800 remains unchanged.
The original controller, plan and
failed-stage receipts remain immutable; the recovery has its own pinned
controller, effective plan and16000 CPU-second reservation. Do not change
either stage's pinned helpers or plans while the recovery is active.
The second stage closed after32 further accepted batches with a
FileNotFoundError, with all516 accepted batches preserved and both prior
stages reconciled. The current third-stage authorization is
`results/full-row-stage3-authorization6-20261019.json`, with a13500 CPU-second
reservation and unchanged total allocations. Its separate controller
serializes resource-state writes; preserve all three stages' pinned sources,
plans and receipts. The latest final-controller preparation is
`results/final-problem2-stage3-adaptation6-20261019.json` and still claims no
final Agda theorem check. All667 row batches subsequently completed and were
reconciled in `results/full-row-stage3-reconciliation6-20261019.json`.
The first final checker stopped before Agda on incompatible ZIP metadata;
its failed receipt is preserved and reconciled. An accepted bounded diagnostic
verified all1337 row payloads and their exact lineage metadata through a
separate read-only filesystem. The current finite final check uses
`tools/final_problem2_resume6.py` and
`results/final-problem2-recovery-authorization6-20261019.json`; its live index
is `results/final-problem2-current6-20261019.json`. Preserve its controller,
metadata sidecars, filesystem binary, source/cache archives and donor pools
while active. Full Problem2 acceptance and private package closure remain
required; row coverage alone is not completion. That metadata recovery passed
the4128-module source audit but Agda exhausted its9000MiB heap. Its failed
receipt and whole-service212.354194CPU remain reconciled. The current final
controller is `tools/final_problem2_compacting6.py`, authorized in
`results/final-problem2-compacting-authorization6-20261019.json`; it adds GHC
`-c` compaction with the same9000MiB heap and12GiB total RAM limit. Preserve
all prior final controllers and all frozen final-stage inputs. The compacting
attempt also exhausted its heap; its254.775942CPU and six-view cleanup are
reconciled. The current finite controller is
`tools/final_problem2_gc_threshold6.py`, authorized in
`results/final-problem2-gc-threshold-authorization6-20261019.json`. It adds
`-F1.2` earlier major collections to `-M9000M -c`, retaining all hard limits.
That attempt also exhausted its heap and is fully reconciled. The accepted
private-cache pilot is indexed in
`results/final-problem2-ephemeral-cache-pilot-review6-20261019.json`: all1337
Rows were read-only and unchanged; two Body data interfaces were checked once;
actual namespace-local build locks were held; no persistent interface was
written; all six views closed. Failed pilot launches and guards remain charged.
The current full controller is `tools/final_problem2_ephemeral6.py`, authorized
in `results/final-problem2-ephemeral-authorization6-20261019.json`. It preserves
all accepted Rows/donors read-only and permits new interfaces only in private
512MiB proof and16MiB checker tmpfs mounts, both counted inside the same12GiB
aggregate RAM limit. Preserve `tools/ephemeral_body_cache6.py` and all pinned
inputs while active. The full Agda output is retained losslessly compressed.
Keep the ordinary 80 GiB free-disk floor; the temporary 60 GiB exception is
consumed. Original desktop run directories and NAMOR must remain untouched.
Laptop compiler caches are archived outside this live project; do not reuse
them as desktop proof evidence. Historical receipts retain their old paths.
Do not overlap Agda checks sharing build state. Record checked source hashes,
binary hashes, flags, cache state, exit codes, runtime and memory.
The current full-row service and the first stage's historical cgroup meter are indexed in
`results/full-row-production-current6-20261018.json`. While that service is
active, preserve its pinned controller helpers, forecast and continuation.
Its outer wait4 receipt counts reaped descendants; the supervisor's own CPU
must also be accounted from whole-service cgroup evidence within the same
reserved stage envelope. Finish each outer reservation once, then record any
positive service-minus-wait4 residual conservatively; never charge nested
checker receipts again. Aggregate Othello RAM remains12GiB, including the
meter, and retained physical study artifacts remain limited to12GiB.
Final checker source preparation is indexed in
`results/final-problem2-controller-preparation6-20261018.json`; it is not an
accepted final theorem check. Read the full completion requirements in
`results/problem2-completion-requirements6-20261018.json` before claiming success.
Use plain commit messages with no attribution trailers. Disclose AI assistance
in documentation. Do not send the submission email.
Multiple workers may edit disjoint owned modules: preserve others' changes.
