#!/usr/bin/env python3
"""Independent scalar Othello oracle. No output from this file is trusted by Agda."""
from __future__ import annotations
import argparse
from functools import lru_cache
import json
from typing import NamedTuple

EMPTY, BLACK, WHITE = 0, 1, 2
DIRECTIONS = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if (r, c) != (0, 0))

class State(NamedTuple):
    size: int
    cells: tuple[int, ...]
    turn: int

def initial(size: int) -> State:
    if size not in (4, 6, 8):
        raise ValueError("supported board sizes are 4, 6 and 8")
    b = [EMPTY] * (size * size)
    a, z = size // 2 - 1, size // 2
    b[a * size + a] = b[z * size + z] = WHITE
    b[a * size + z] = b[z * size + a] = BLACK
    return State(size, tuple(b), BLACK)

def captured(s: State, row: int, col: int) -> tuple[int, ...]:
    n = s.size
    if not (0 <= row < n and 0 <= col < n) or s.cells[row * n + col] != EMPTY:
        return ()
    flips = []
    for dr, dc in DIRECTIONS:
        r, c = row + dr, col + dc
        ray = []
        while 0 <= r < n and 0 <= c < n and s.cells[r * n + c] == 3 - s.turn:
            ray.append(r * n + c)
            r, c = r + dr, c + dc
        if ray and 0 <= r < n and 0 <= c < n and s.cells[r * n + c] == s.turn:
            flips.extend(ray)
    return tuple(flips)

def placements(s: State) -> tuple[tuple[tuple[int, int], State], ...]:
    result = []
    for row in range(s.size):
        for col in range(s.size):
            flips = captured(s, row, col)
            if flips:
                cells = list(s.cells)
                cells[row * s.size + col] = s.turn
                for index in flips:
                    cells[index] = s.turn
                result.append(((row, col), State(s.size, tuple(cells), 3 - s.turn)))
    return tuple(result)

def successors(s: State) -> tuple[State, ...]:
    moves = placements(s)
    if moves:
        return tuple(t for _, t in moves)
    passed = State(s.size, s.cells, 3 - s.turn)
    return (passed,) if placements(passed) else ()

def score(s: State) -> int:
    return s.cells.count(WHITE) - s.cells.count(BLACK)

@lru_cache(maxsize=None)
def value(s: State) -> int:
    children = successors(s)
    if not children:
        return score(s)
    scores = [value(t) for t in children]
    return max(scores) if s.turn == WHITE else min(scores)

def perft(s: State, depth: int) -> int:
    """Count paths of exactly depth transitions; a compulsory pass is one ply."""
    if depth < 0:
        raise ValueError("negative perft depth")
    if depth == 0:
        return 1
    return sum(perft(t, depth - 1) for t in successors(s))

def perfect_line(s: State) -> list[dict]:
    line = []
    while (children := successors(s)):
        v = value(s)
        index = next(i for i, t in enumerate(children) if value(t) == v)
        moves = placements(s)
        line.append({"turn": "black" if s.turn == BLACK else "white",
                     "move": list(moves[index][0]) if moves else "pass",
                     "successor_index": index, "value": v})
        s = children[index]
    line.append({"terminal": True, "black": s.cells.count(BLACK),
                 "white": s.cells.count(WHITE), "empty": s.cells.count(EMPTY),
                 "score": score(s)})
    return line

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, choices=(4, 6, 8), default=4)
    parser.add_argument("--perft", type=int)
    args = parser.parse_args()
    s = initial(args.size)
    if args.perft is not None:
        print(json.dumps({"size": args.size, "perft": [perft(s, d) for d in range(args.perft + 1)]}))
    else:
        print(json.dumps({"size": args.size, "value": value(s), "line": perfect_line(s),
                          "cache": value.cache_info()._asdict()}, indent=2))

if __name__ == "__main__":
    main()
