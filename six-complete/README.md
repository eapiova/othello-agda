# Complete selected 6×6 proof sources

Riccardo Borsetto · TPP-mark 2026 · 15 November 2026

This separate source root contains all **4,128 selected non-builtin Agda modules**, plus the exact typed final wrapper (**4,129 modules**), with their own `othello.agda-lib`. Original source bodies are unchanged. Root `../src/` remains the historical development and is not the complete selected closure.

The accepted endpoint is `Tests.CompleteUpperRows6.Result.initial6x6 : Problem2`: raw White-minus-Black value +4 and a completed legal play of the SAME optimal forcing-strategy pair ending Black 16 / White 20, from the standard initial board with Black to move. Safe Agda acceptance is historical (19 October 2026), not a new check performed for this publication. Problem 3 (8×8) is NOT proved.

`SOURCE-INVENTORY.json` binds these sources to the accepted source audit. `DEPENDENCY-GRAPH.json.zlib` contains their exact declared dependency graph, using Python stdlib zlib. `evidence/` includes the small accepted completion and checker records. Run:

```
python3 -I -B verify-sources.py
```

This verifies identities, the exact declared graph closure and the typed wrapper, not mathematical correctness. Compiler builtins are external.

A syntactically derived fresh-check command, **not cold-rebuild tested or resource-validated**, is:

```
cd six-complete
agda --no-libraries --safe --without-K --cubical-compatible -i src src/Tests/FinalProblem2Check6.agda
```

A fresh run recomputes large Boolean row proofs; historical final-stage timings are NOT estimates of a cold rebuild. Use a disposable checkout and fresh cache. No Agda, solver or old controller is launched by this publication.

Full historical evidence, compiler/path-sensitive retained row interfaces, and downloadable archives are available in the [submission Release](https://github.com/eapiova/othello-agda/releases/tag/tpp2026-submission-20261115). Retained interfaces are evidence, not a portable cache. GitHub's automatic source archive does not include the retained interfaces or row receipts; download the named assets for those.

See the [LaTeX report](../docs/tpp2026/writeup.pdf), the AI-assistance section. No separate current disclosure file is required. Historical helper comments describing still-open premises are preserved: the final `Result` supplies the complete records and has no caller-supplied game-value premise.
