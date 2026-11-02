# Untrusted native 6×6 baseline

`vendor/solve6b.c` and `vendor/LICENSE` are unchanged MIT-licensed files from
Yasuhiko Kodama's `yaskodama/othello6x6` repository, commit
`26914118c5b7ed6839be21cf1d6641af2f64cf6e`:

- Source: <https://raw.githubusercontent.com/yaskodama/othello6x6/26914118c5b7ed6839be21cf1d6641af2f64cf6e/solve6b.c>
- License: <https://raw.githubusercontent.com/yaskodama/othello6x6/26914118c5b7ed6839be21cf1d6641af2f64cf6e/LICENSE>
- Original source SHA-256: `0f72cfa5393647d8eeead814c0473f340ff7c125f590724360cf44cdef4c9f9b`
- Original license SHA-256: `e39572d397370eae2f19869e73203cde6f28979b629929a278a626d40b371282`

`solve6.c` is a separate adaptation made with AI assistance, covered by the
same MIT license. It retains the upstream bitboard rules, corner ordering,
negamax, PVS, two-slot transposition table and mobility ordering. It replaces
hash-only table identity with both complete 64-bit board words and an explicit
validity bit; hashes only select a bucket. A self-test forces *identical full
hashes* for distinct boards and verifies that probes reject the collision.

The state normalization is only relative to the side to move: `P` is that
player's discs and `O` is the opponent's discs. Black to move maps to `(B,W)`;
White to move maps to `(W,B)`. Values in the table are disc differences from
`P`'s perspective. There is no rotation, reflection, color inversion or other
symmetry canonicalization. The public score is always **raw White minus
Black**, including terminal boards with empty cells. Negamax negates once
when converting a Black-to-move root to that public score.

A forced pass swaps `P,O` and uses one transition. A terminal board checks
that neither side can place and ends immediately. Perft counts paths of
exactly the requested depth, so terminal states contribute one at depth zero
and zero at positive depth; no fictitious terminal pass is inserted.

Commands, from the project root:

```sh
python3 tools/solve6.py build
python3 tools/solve6.py moves --position initial --turn black
python3 tools/solve6.py perft --depth 4
python3 tools/solve6.py solve --position 210222222222222222222222222222222222 --turn black
python3 tools/solve6.py bounds --position 210222222222222222222222222222222222 --turn black --direction lower --threshold 36
python3 tools/solve6.py tt-selftest --tt-bits 0
python3 tools/test_native6.py
```

The native binary accepts the same `solve`, `bounds`, `moves`, `perft` and
`tt-selftest` command syntax and produces one JSON object. A position is
`initial` or exactly 36 row-major characters (`0` empty, `1` Black, `2` White).
Coordinates and successor indices are zero-based. Moves are always emitted
in row-major order, independent of the search ordering; a forced pass is a
single successor with `"move":"pass"`; a terminal board has no successors.
`bounds --direction lower --threshold t` returns `holds` for value ≥ t;
`upper` returns `holds` for value ≤ t. A bounds response does not claim an
exact value. Perft depths are limited to 0..10 to keep its count in uint64.

`--tt-bits` accepts 0..26; default 18. Every bucket has two full-key slots:
48 bytes per bucket on the supported 64-bit compiler, and the JSON `tt_bytes`
records the exact actual allocation. Bits 18 allocate 12,582,912 bytes;
bits 25 allocate 1,610,612,736 bytes; bits 26 allocate 3,221,225,472 bytes.
The table is allocated only for solve/bounds/self-test. `--small 10` (default)
uses the upstream table-free endgame search below that many empty cells;
`--small 0` exercises full-key table probes in small differential tests.
JSON includes `nodes`, `tt_hits`, `tt_collisions` (occupied slots rejected
because their full keys differ), and process `cpu_seconds`.

The Python helpers are `query(command, position, **options)`, `solve(state)`,
`bounds(state, direction, threshold)`, `moves(state)`, `successors(state)` and
`perft(state, depth)`. They accept `ref.State` directly; `query`, `solve`,
`bounds`, `moves` and `perft` also accept `initial` or a pos012 string with
an explicit `turn` option. Build and query subprocesses use argument arrays
without a shell. Queries default to a 60-second wall timeout. The wrapper
builds to ignored `results/native6/solve6`, records source/vendor/license,
compiler and binary hashes in `build.json`, and rebuilds if those inputs or
the binary hash change. Tests write measured CPU/runtime and the build
manifest into ignored `results/native6/tests.json`.

The tests compare native rules and short perft with `tools/ref.py`, verify
forced passes and terminal boards, and clear the scalar value cache before
each of 16 deterministic reachable endgames with at most eight empty cells.
They also compare threshold queries, use tiny tables to force many bucket
collisions, and explicitly force identical full hashes in the table self-test.
They never run an initial-position full solve. All native results and tests
are untrusted computational evidence; they add no Agda postulates or claims.
