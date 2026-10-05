#!/usr/bin/env python3
"""Package a tagged, clean source tree with matching successful cold checks."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
from provenance import source_identity

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="tpp-mark-2026-problem1")
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("dist/othello-agda-tpp2026-problem1.tar.gz"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True)
    if dirty.stdout.strip():
        raise SystemExit("refusing package: commit the source changes first")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    tag = subprocess.run(["git", "rev-parse", args.tag + "^{commit}"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    if tag != head:
        raise SystemExit("refusing package: requested tag does not identify HEAD")
    identity = source_identity(root)
    results_dir = (root / args.results).resolve()
    matches = []
    for path in sorted(results_dir.glob("*.json")):
        result = json.loads(path.read_text())
        if (result.get("format") == "othello-agda-check-v1" and result.get("accepted") is True
            and result.get("cold") is True and result.get("exit_code") == 0
            and result.get("source_unchanged") is True and result.get("target") == "src/Everything.agda"
            and result.get("agda_source_sha256") == identity["agda_source_sha256"]):
            matches.append((path, result))
    if len({r["machine"] for _, r in matches}) < 2:
        raise SystemExit("refusing package: matching cold Everything checks from two machines are required")
    if not any("--html" in r["command"] for _, r in matches):
        raise SystemExit("refusing package: a matching cold HTML check is required")
    html = root / "dist/html"
    if not (html / "Othello.Proof4.html").is_file():
        raise SystemExit("refusing package: generate proof HTML first")
    writeup = root / "dist/writeup.pdf"
    if not writeup.is_file():
        raise SystemExit("refusing package: compile docs/writeup.typ first")
    source = subprocess.run(["git", "archive", "--format=tar", "--prefix=othello-agda/", args.tag],
                            cwd=root, capture_output=True, check=True).stdout
    manifest = {"format": "othello-submission-v1", "tag": args.tag, "revision": head,
                "agda_source_sha256": identity["agda_source_sha256"],
                "writeup_sha256": hashlib.sha256(writeup.read_bytes()).hexdigest(),
                "checks": [{"file": p.name, "machine": r["machine"], "wall_seconds": r["wall_seconds"],
                            "peak_rss_gib": r["peak_rss_gib"], "agda_binary_sha256": r["agda_binary_sha256"]}
                           for p, r in matches],
                "proved": ["Problem 1: White wins", "4×4 raw score value +8 with both strategies"],
                "statement_only": ["Problem 2: 6×6, 20–16", "Problem 3: 8×8, draw"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as output:
        with tarfile.open(fileobj=io.BytesIO(source), mode="r:") as original:
            for member in original:
                output.addfile(member, original.extractfile(member) if member.isfile() else None)
        extras = [("SUBMISSION.json", (json.dumps(manifest, indent=2) + "\n").encode())]
        extras.append(("writeup.pdf", writeup.read_bytes()))
        for path, result in matches:
            extras.append(("verification/" + path.name, path.read_bytes()))
            log = path.with_suffix(".log")
            if log.is_file():
                extras.append(("verification/" + log.name, log.read_bytes()))
        for path in sorted(html.rglob("*")):
            if path.is_file():
                extras.append(("html/" + path.relative_to(html).as_posix(), path.read_bytes()))
        for name, data in extras:
            member = tarfile.TarInfo("othello-agda/" + name)
            member.size = len(data)
            member.mode = 0o644
            member.mtime = 0
            output.addfile(member, io.BytesIO(data))
    args.output.write_bytes(gzip.compress(buffer.getvalue(), mtime=0))
    print(json.dumps({"archive": str(args.output), "bytes": args.output.stat().st_size,
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(), **manifest}, indent=2))

if __name__ == "__main__":
    main()
