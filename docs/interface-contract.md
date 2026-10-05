# Shared implementation contract

Core flags: safe, without-K, cubical-compatible. Core uses builtins and Prelude.
The installed stdlib 2.3 failed a transitive irrelevant-field check on the laptop;
do not enable unsafe flags. Its source is retained only for reference.
Player comes from Game.Player (black, white, other, samePlayer).

Game.Core is generic over state S. Game record fields: turn : S → Player,
next : S → List S, forcedPass : S → Bool. It exposes Strategy, CompletedPlay,
Guarantees (forcing player, terminal predicate, starting state), WhiteGuarantees,
BlackGuarantees, and play determinism. Histories record successor indices.
Strategies return natural indices; out-of-range indices default to the head.
Guarantees contain a forcing strategy and, for each opposing strategy, an
actual completed play and a proof of the terminal predicate.

Game.Certificate exports Certificate constructors leaf, choice Nat Certificate,
fork (List Certificate), pass Certificate. Choice indices outside the legal
successor list are rejected (the total strategy convention does not excuse
invalid certificates). fork requires a nonempty list with exactly one child
per successor, in order. pass checks forcedPass and exactly one successor.
leaf checks terminality. Game.Soundness proves generic checker acceptance
implies Guarantees, with no assumptions about imported certificates.

Othello.Board exports Size (four six eight), dimension : Size → Nat,
Cell (empty blackCell whiteCell), Board : Size → Set (nested vectors),
State : Size → Set with state : Board size → Player → State size,
board and toMove projections, initial : (size : Size) → State size,
discs : Player → State size → Nat and score : State size → Int.

Othello.Rules exports legalMoves : State size → List (Fin n × Fin n)
in row-major order; applyMove; successors : State size → List (State size)
(placements, a single compulsory pass, or no successors when terminal),
forcedPass : State size → Bool, and game : (size : Size) → Game (State size).
Python uses cell integers 0 empty, 1 black, 2 white, and the standard central
W B / B W configuration. Certificates use successor-list indices, not board
hashes or precomputed child states. Both bounds use White-minus-Black scoring.

Workers can clarify exact implicit argument order with root, but must preserve
these names and semantic meanings. Root owns Python tools, scripts,
Othello.Statements, Othello.Proof4, the generated certificates and documentation.
