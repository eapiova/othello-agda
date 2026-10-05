#!/usr/bin/env python3
"""Untrusted bitboard solver and strict data-only certificate emitter."""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import time
from typing import NamedTuple
import ref

class State(NamedTuple):
    size: int
    black: int
    white: int
    turn: int

@lru_cache(maxsize=3)
def geometry(n: int):
    masks = []
    for dr, dc in ref.DIRECTIONS:
        mask = sum(1 << (r * n + c) for r in range(n) for c in range(n)
                   if 0 <= r + dr < n and 0 <= c + dc < n)
        masks.append((mask, dr * n + dc))
    return tuple(masks)

def shift(bits: int, geom: tuple[int, int]) -> int:
    mask, delta = geom
    return (bits & mask) << delta if delta >= 0 else (bits & mask) >> -delta

def from_scalar(s: ref.State) -> State:
    return State(s.size, sum(1 << i for i, c in enumerate(s.cells) if c == ref.BLACK),
                 sum(1 << i for i, c in enumerate(s.cells) if c == ref.WHITE), s.turn)

def scalar(s: State) -> ref.State:
    return ref.State(s.size, tuple(ref.BLACK if s.black >> i & 1 else ref.WHITE if s.white >> i & 1
                                 else ref.EMPTY for i in range(s.size * s.size)), s.turn)

def placements(s: State) -> tuple[State, ...]:
    own, enemy = (s.black, s.white) if s.turn == ref.BLACK else (s.white, s.black)
    empty = ((1 << (s.size * s.size)) - 1) ^ (own | enemy)
    legal = 0
    for g in geometry(s.size):
        ray = shift(own, g) & enemy
        for _ in range(s.size - 2):
            ray |= shift(ray, g) & enemy
        legal |= shift(ray, g) & empty
    result = []
    while legal:
        move = legal & -legal
        legal ^= move
        flips = 0
        for g in geometry(s.size):
            front = shift(move, g) & enemy
            ray = front
            while front:
                following = shift(front, g)
                if following & own:
                    flips |= ray
                    break
                front = following & enemy
                ray |= front
        if not flips:
            raise AssertionError("legal bitboard move captures nothing")
        new_own, new_enemy = own | move | flips, enemy & ~flips
        b, w = (new_own, new_enemy) if s.turn == ref.BLACK else (new_enemy, new_own)
        result.append(State(s.size, b, w, 3 - s.turn))
    return tuple(result)

def successors(s: State) -> tuple[State, ...]:
    moves = placements(s)
    if moves:
        return moves
    passed = State(s.size, s.black, s.white, 3 - s.turn)
    return (passed,) if placements(passed) else ()

def score(s: State) -> int:
    return s.white.bit_count() - s.black.bit_count()

@lru_cache(maxsize=None)
def value(s: State) -> int:
    children = successors(s)
    if not children:
        return score(s)
    values = [value(t) for t in children]
    return max(values) if s.turn == ref.WHITE else min(values)

def certificate(s: State, direction: str, bound: int) -> dict:
    children = successors(s)
    if not children:
        if not (score(s) >= bound if direction == "lower" else score(s) <= bound):
            raise ValueError("terminal position fails bound")
        return {"kind": "leaf"}
    if not placements(s):
        return {"kind": "pass", "child": certificate(children[0], direction, bound)}
    forcing = ref.WHITE if direction == "lower" else ref.BLACK
    if s.turn == forcing:
        good = lambda t: value(t) >= bound if direction == "lower" else value(t) <= bound
        index = next(i for i, t in enumerate(children) if good(t))
        return {"kind": "choice", "index": index,
                "child": certificate(children[index], direction, bound)}
    return {"kind": "fork", "children": [certificate(t, direction, bound) for t in children]}

def validate_node(node: object, depth: int = 0) -> int:
    if depth > 128 or type(node) is not dict or type(node.get("kind")) is not str:
        raise ValueError("invalid certificate node or excessive depth")
    kind = node["kind"]
    if kind == "leaf" and set(node) == {"kind"}:
        return 1
    if kind == "choice" and set(node) == {"kind", "index", "child"}:
        if type(node["index"]) is not int or not 0 <= node["index"] < 64:
            raise ValueError("invalid choice index")
        return 1 + validate_node(node["child"], depth + 1)
    if kind == "pass" and set(node) == {"kind", "child"}:
        return 1 + validate_node(node["child"], depth + 1)
    if kind == "fork" and set(node) == {"kind", "children"}:
        if type(node["children"]) is not list or not 1 <= len(node["children"]) <= 64:
            raise ValueError("fork must have a nonempty bounded child list")
        return 1 + sum(validate_node(c, depth + 1) for c in node["children"])
    raise ValueError("unknown constructor or unexpected fields")

def validate_document(document: object) -> dict:
    if type(document) is not dict or set(document) != {"format", "size", "scoring", "bound", "lower", "upper"}:
        raise ValueError("invalid certificate document fields")
    if document["format"] != "othello-strategy-tree-v1" or type(document["size"]) is not int or document["size"] != 4:
        raise ValueError("unsupported format or board size")
    if document["scoring"] != "white-minus-black" or type(document["bound"]) is not int or document["bound"] != 8:
        raise ValueError("unsupported scoring or bound")
    validate_node(document["lower"])
    validate_node(document["upper"])
    return document

def independent_check(s: ref.State, node: dict, direction: str, bound: int,
                      visited: set[ref.State] | None = None) -> bool:
    if visited is not None:
        visited.add(s)
    children = ref.successors(s)
    kind = node["kind"]
    if kind == "leaf":
        return not children and (ref.score(s) >= bound if direction == "lower" else ref.score(s) <= bound)
    if not children:
        return False
    if not ref.placements(s):
        return kind == "pass" and independent_check(children[0], node["child"], direction, bound, visited)
    if kind == "pass":
        return False
    forcing = ref.WHITE if direction == "lower" else ref.BLACK
    if s.turn == forcing:
        return (kind == "choice" and node["index"] < len(children)
                and independent_check(children[node["index"]], node["child"], direction, bound, visited))
    return (kind == "fork" and len(node["children"]) == len(children)
            and all(independent_check(t, c, direction, bound, visited)
                    for t, c in zip(children, node["children"])))

def emit_node(node: dict) -> str:
    kind = node["kind"]
    if kind == "leaf":
        return "leaf"
    if kind == "choice":
        return f"(choice {node['index']} {emit_node(node['child'])})"
    if kind == "pass":
        return f"(pass {emit_node(node['child'])})"
    return "(fork (" + " ∷ ".join(emit_node(c) for c in node["children"]) + " ∷ []))"

def emit_agda(document: dict) -> str:
    validate_document(document)
    return ("{-# OPTIONS --safe --without-K --cubical-compatible #-}\n"
            "-- Generated data only. Agda independently checks both certificates.\n"
            "module Othello.Generated4 where\n\n"
            "open import Agda.Builtin.List using ([]; _∷_)\n"
            "open import Game.Certificate using (Certificate; leaf; choice; fork; pass)\n\n"
            "lowerCertificate : Certificate\nlowerCertificate = " + emit_node(document["lower"]) + "\n\n"
            "upperCertificate : Certificate\nupperCertificate = " + emit_node(document["upper"]) + "\n")

def strict_load(path: Path) -> dict:
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError("duplicate JSON key")
            out[k] = v
        return out
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("certificate JSON exceeds 4 MiB")
    return validate_document(json.loads(path.read_text(), object_pairs_hook=pairs))

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--from-json", type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    start = from_scalar(ref.initial(4))
    if args.from_json:
        document = strict_load(args.from_json)
    else:
        v = value(start)
        if v != 8:
            raise AssertionError(f"unexpected exact value {v}")
        document = {"format": "othello-strategy-tree-v1", "size": 4,
                    "scoring": "white-minus-black", "bound": 8,
                    "lower": certificate(start, "lower", 8), "upper": certificate(start, "upper", 8)}
        validate_document(document)
    visited = set()
    for direction in ("lower", "upper"):
        if not independent_check(ref.initial(4), document[direction], direction, 8, visited):
            raise AssertionError("independent scalar certificate check rejected")
    for s in visited:
        if tuple(scalar(t) for t in successors(from_scalar(s))) != ref.successors(s):
            raise AssertionError("bitboard/scalar rules disagreement")
    raw = (json.dumps(document, separators=(",", ":"), sort_keys=True) + "\n").encode()
    cert_path = args.root / "certificates/four-v1.json"
    agda_path = args.root / "src/Othello/Generated4.agda"
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_bytes(raw)
    agda_path.write_text(emit_agda(document))
    stats = {"format": document["format"], "value": 8, "json_sha256": hashlib.sha256(raw).hexdigest(),
             "json_bytes": len(raw), "agda_bytes": agda_path.stat().st_size,
             "lower_nodes": validate_node(document["lower"]), "upper_nodes": validate_node(document["upper"]),
             "independently_compared_positions": len(visited), "wall_seconds": time.monotonic() - started,
             "solver_cache": value.cache_info()._asdict(), "trust": "untrusted generator; Agda proof required"}
    (args.root / "certificates/generation.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
