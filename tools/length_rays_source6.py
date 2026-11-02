#!/usr/bin/env python3
"""Generate the canonical Othello.LengthRays6 Agda source."""

from itertools import product
from pathlib import Path


PLAYERS = (
    ("black", "whiteCell", "blackCell"),
    ("white", "blackCell", "whiteCell"),
)
CELLS = ("empty", "blackCell", "whiteCell")
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src" / "Othello" / "LengthRays6.agda"


def cell_arguments(n: int) -> str:
    return " ".join(f"c{i}" for i in range(1, n + 1))


def coord_arguments(n: int) -> str:
    return " ".join(f"q{i}" for i in range(1, n + 1))


def list_term(names: list[str]) -> str:
    return " ∷ ".join([*names, "[]"])


def paired_list_term(n: int) -> str:
    return list_term([f"(q{i} , c{i})" for i in range(1, n + 1)])


def count_definition(n: int) -> list[str]:
    arrows = " → Cell" * n
    lines = [f"count{n} : Player{arrows} → ℕ"]
    if n == 0:
        lines.append("count0 p = 0")
        return lines
    if n == 1:
        lines.append("count1 p c1 = 0")
        return lines

    for player, opponent, friendly in PLAYERS:
        for captured in range(1, n):
            patterns = [opponent] * captured
            patterns.append(friendly)
            patterns.extend(["_"] * (n - captured - 1))
            lines.append(
                f"count{n} {player} {' '.join(patterns)} = {captured}"
            )
    lines.append(f"count{n} p {cell_arguments(n)} = 0")
    return lines


def correctness_signature(n: int) -> list[str]:
    lines = [f"  correct{n} : ∀ (p : Player)"]
    if n:
        lines.append(f"    ({coord_arguments(n)} : Coord six)")
        lines.append(f"    ({cell_arguments(n)} : Cell) →")
    else:
        lines[-1] += " →"
    coords = list_term([f"q{i}" for i in range(1, n + 1)])
    cells = cell_arguments(n)
    count_call = f"count{n} p" + (f" {cells}" if cells else "")
    lines.append(f"    prefix ({count_call}) ({coords}) ≡")
    lines.append(f"    Rays.capturesCells p ({paired_list_term(n)})")
    return lines


def correctness_clauses(n: int) -> list[str]:
    lines: list[str] = []
    qs = coord_arguments(n)
    q_part = f" {qs}" if qs else ""
    for player, _, _ in PLAYERS:
        for cells in product(CELLS, repeat=n):
            cell_part = f" {' '.join(cells)}" if cells else ""
            lines.append(f"  correct{n} {player}{q_part}{cell_part} = refl")
    return lines


def generate() -> str:
    lines = [
        "{-# OPTIONS --safe --without-K --cubical-compatible #-}",
        "module Othello.LengthRays6 where",
        "",
        "open import Prelude",
        "open import Othello.Board using",
        "  ( Player; black; white; Cell; empty; blackCell; whiteCell",
        "  ; Coord; six",
        "  )",
        "import Othello.CellRays6 as Rays",
        "",
        "prefix : ℕ → List (Coord six) → List (Coord six)",
        "prefix zero xs = []",
        "prefix (suc n) [] = []",
        "prefix (suc n) (q ∷ qs) = q ∷ prefix n qs",
        "",
    ]

    for n in range(6):
        lines.extend(count_definition(n))
        lines.append("")

    lines.append("abstract")
    for n in range(6):
        lines.extend(correctness_signature(n))
        lines.extend(correctness_clauses(n))
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    OUTPUT.write_text(generate(), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
