#!/usr/bin/env python3
"""Measure one serialized Agda check with bounded process-tree execution."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from run_job import add_caps, build_lock, run_job


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("target")
    parser.add_argument("output", type=Path)
    parser.add_argument("heap", nargs="?", default="12G")
    parser.add_argument("--cold", action="store_true")
    parser.add_argument("--html", action="store_true")
    parser.add_argument("--reservation-id")
    parser.add_argument("--expected-source-sha256")
    add_caps(parser)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.label):
        parser.error("invalid label")
    if not re.fullmatch(r"[1-9][0-9]*[kKmMgG]?", args.heap):
        parser.error("invalid heap cap")
    root = Path(__file__).resolve().parents[1]
    target = (root / args.target).resolve()
    if not target.is_relative_to(root / "src") or target.suffix != ".agda" or not target.is_file():
        parser.error("target must be an existing project Agda module")
    with build_lock(root):
        agda = Path(shutil.which("agda") or Path.home() / ".local/bin/agda").resolve()
        version = subprocess.run([str(agda), "--version"], capture_output=True,
                                 text=True, check=True, timeout=10).stdout.strip()
        command = [str(agda), "+RTS", "-M" + args.heap, "-RTS", "--no-libraries",
                   "--safe", "--without-K", "--cubical-compatible", "-i", "src"]
        if args.cold:
            command.append("--ignore-interfaces")
        if args.html:
            command.extend(["--html", "--html-dir=dist/html"])
        command.append(args.target)
        result = run_job(args.label, command, args.output, root=root, locked=True,
                         timeout=args.timeout, cpu_limit=args.cpu_limit,
                         rss_limit_gib=args.rss_limit_gib, log_limit_mib=args.log_limit_mib,
                         reservation_id=args.reservation_id,
                         expected_source_sha256=args.expected_source_sha256,
                         metadata={"format": "othello-agda-check-v2", "target": args.target,
                                   "agda_version": version, "agda_path": str(agda),
                                   "agda_binary_sha256": hashlib.sha256(agda.read_bytes()).hexdigest(),
                                   "cold": args.cold, "heap_cap": args.heap})
    print(json.dumps(result, indent=2))
    return 0 if result["accepted"] else (result["exit_code"] if result["exit_code"] and result["exit_code"] > 0 else 1)


if __name__ == "__main__":
    sys.exit(main())
