# Formal-source map

See `formal-source.html` for verbatim statements, guarantee definitions and endpoints.

- `statements`: Shared theorem statements (problem2/core-source.zip: src/Othello/Statements.agda)
- `guarantees`: Strategy and guarantee definitions (same ZIP: src/Game/Core.agda)
- `p1-problem1`: Problem 1 (nested problem1 archive: src/Othello/Proof4.agda)
- `p2-initial6x6`: Problem 2 (problem2/checked-source/src/Tests/CompleteUpperRows6/Result.agda)
- `p2-wrapper`: Typed final wrapper (problem2/checked-source/src/Tests/FinalProblem2Check6.agda)
- `p3-conditional`: Conditional Problem 3 wrapper (problem3-partial/Integration.agda; dependencies not included)

The 6×6 Result source has no explicit remaining premise; imported checked rows supply its proof. The 8×8 endpoint explicitly requires premises and is not closed.
