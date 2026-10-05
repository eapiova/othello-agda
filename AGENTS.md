# othello-agda

This project proves the exact raw-score value of standard 4×4 Othello.
Use `--safe --without-K --cubical-compatible` in every core Agda module.
No postulates, holes, termination escapes, positivity escapes, or imported
solver claims are allowed in completed project proofs.
The core uses Agda.Builtin modules and a small checked Prelude. The laptop
compiler rejects a transitive standard-library 2.3 dependency that the desktop
accepts; do not enable unsafe irrelevance flags to bypass this mismatch.
Cubical modules may be separate optional modules; preserve the core build.
Source is authoritative on the laptop. Heavy checks run over `ssh desktop`.
Do not overlap Agda checks sharing build state. Record checked source hashes,
binary hashes, flags, cache state, exit codes, runtime and memory.
Use plain commit messages with no attribution trailers. Disclose AI assistance
in documentation. Do not send the submission email.
Multiple workers may edit disjoint owned modules: preserve others' changes.
