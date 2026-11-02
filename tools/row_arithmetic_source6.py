#!/usr/bin/env python3
"""Generate the exhaustive safe proofs in Othello.RowArithmetic6."""

from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "Othello" / "RowArithmetic6.agda"

CELLS = ("empty", "blackCell", "whiteCell")


def fin_pattern(index: int) -> str:
    term = "F.zero"
    for _ in range(index):
        term = f"F.suc ({term})"
    return term if index == 0 else f"({term})"


def row_pattern(cells: tuple[str, ...]) -> str:
    return "(" + " F.∷ ".join(cells) + " F.∷ F.[])"


def generate() -> str:
    lines = [
        "{-# OPTIONS --safe --without-K --cubical-compatible #-}",
        "-- AI-assisted exhaustive proofs for arithmetic on packed 6-cell rows.",
        "module Othello.RowArithmetic6 where",
        "",
        "open import Prelude",
        "open import Agda.Builtin.Nat",
        "  using (_+_; _*_; div-helper; mod-helper)",
        "  renaming (_-_ to _∸_)",
        "open import Othello.Board",
        "import Othello.Finite as F",
        "import Othello.RowPacked6 as Packed",
        "",
        "power : F.Fin 6 → ℕ",
        "power F.zero = 1",
        "power (F.suc F.zero) = 3",
        "power (F.suc (F.suc F.zero)) = 9",
        "power (F.suc (F.suc (F.suc F.zero))) = 27",
        "power (F.suc (F.suc (F.suc (F.suc F.zero)))) = 81",
        "power (F.suc (F.suc (F.suc (F.suc (F.suc F.zero))))) = 243",
        "",
        "cellCode : Cell → ℕ",
        "cellCode empty = 0",
        "cellCode blackCell = 1",
        "cellCode whiteCell = 2",
        "",
        "cell : ℕ → Cell",
        "cell zero = empty",
        "cell (suc zero) = blackCell",
        "cell (suc (suc n)) = whiteCell",
        "",
        "oldDigit : ℕ → F.Fin 6 → ℕ",
        "oldDigit n i = mod-helper 0 2",
        "  (div-helper 0 (power i ∸ 1) n (power i ∸ 1)) 2",
        "",
        "read : ℕ → F.Fin 6 → Cell",
        "read n i = cell (oldDigit n i)",
        "",
        "replace : ℕ → F.Fin 6 → Cell → ℕ",
        "replace n i c =",
        "  (n ∸ (oldDigit n i * power i)) + (cellCode c * power i)",
        "",
        "read-encode : ∀ (row : F.Vec Cell 6) (i : F.Fin 6) →",
        "  read (Packed.encodeRow row) i ≡ F.lookup row i",
    ]

    rows = list(product(CELLS, repeat=6))
    for row in rows:
        pattern = row_pattern(row)
        for index in range(6):
            lines.append(f"read-encode {pattern} {fin_pattern(index)} = refl")

    lines.extend(
        [
            "",
            "replace-encode : ∀ (row : F.Vec Cell 6) (i : F.Fin 6) (c : Cell) →",
            "  replace (Packed.encodeRow row) i c ≡",
            "  Packed.encodeRow (F.updateAt row i (λ _ → c))",
        ]
    )
    for row in rows:
        pattern = row_pattern(row)
        for index in range(6):
            fin = fin_pattern(index)
            for replacement in CELLS:
                lines.append(
                    f"replace-encode {pattern} {fin} {replacement} = refl"
                )

    expected_read = 3**6 * 6
    expected_replace = expected_read * 3
    actual_read = sum(line.startswith("read-encode (") for line in lines)
    actual_replace = sum(line.startswith("replace-encode (") for line in lines)
    if (actual_read, actual_replace) != (expected_read, expected_replace):
        raise RuntimeError(
            f"clause count mismatch: read={actual_read}, replace={actual_replace}"
        )

    source = "\n".join(lines) + "\n"
    if len(source.encode("utf-8")) >= 10 * 1024 * 1024:
        raise RuntimeError("generated source exceeds the 10 MiB limit")
    return source


def main() -> None:
    TARGET.write_text(generate(), encoding="utf-8")


if __name__ == "__main__":
    main()
