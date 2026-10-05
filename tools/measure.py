#!/usr/bin/env python3
"""Measure one serialized Agda check; retain exact provenance and exit status."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from provenance import source_identity

def memory_info() -> dict:
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, data = line.split(":", 1)
        if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            values[key + "_kib"] = int(data.split()[0])
    return values

def stop(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("target")
    parser.add_argument("output", type=Path)
    parser.add_argument("heap", nargs="?", default="12G")
    parser.add_argument("--cold", action="store_true")
    parser.add_argument("--html", action="store_true")
    parser.add_argument("--timeout", type=float, default=7200)
    parser.add_argument("--rss-limit-gib", type=float, default=16)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.label):
        parser.error("invalid label")
    if not re.fullmatch(r"[1-9][0-9]*[kKmMgG]?", args.heap):
        parser.error("invalid heap cap")
    if args.timeout <= 0 or args.rss_limit_gib <= 0:
        parser.error("limits must be positive")
    root = Path(__file__).resolve().parents[1]
    target = (root / args.target).resolve()
    if not target.is_relative_to(root / "src") or target.suffix != ".agda" or not target.is_file():
        parser.error("target must be an existing project Agda module")
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output.resolve()
    with (Path(tempfile.gettempdir()) / "othello-agda-local-check.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        source = source_identity(root)
        agda = Path(shutil.which("agda") or Path.home() / ".local/bin/agda").resolve()
        version = subprocess.run([str(agda), "--version"], capture_output=True, text=True, check=True).stdout.strip()
        command = [str(agda), "+RTS", "-M" + args.heap, "-RTS", "--no-libraries",
                   "--safe", "--without-K", "--cubical-compatible", "-i", "src"]
        if args.cold:
            command.append("--ignore-interfaces")
        if args.html:
            command.extend(["--html", "--html-dir=dist/html"])
        command.append(args.target)
        result = {"format": "othello-agda-check-v1", "label": args.label, "target": args.target,
                  **source, "machine": socket.gethostname(), "agda_version": version,
                  "agda_path": str(agda), "agda_binary_sha256": hashlib.sha256(agda.read_bytes()).hexdigest(),
                  "command": command, "cold": args.cold, "heap_cap": args.heap,
                  "rss_stop_threshold_gib": args.rss_limit_gib, "timeout_seconds": args.timeout,
                  "started_utc": datetime.now(timezone.utc).isoformat(),
                  "memory_before": memory_info(), "disk_free_bytes_before": shutil.disk_usage(root).free,
                  "interfaces_before": len(list(root.rglob("*.agdai")))}
        started = time.monotonic()
        peak = 0
        stop_reason = None
        process = None
        try:
            with (output / (args.label + ".log")).open("wb") as log:
                process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                while process.poll() is None:
                    try:
                        status = Path(f"/proc/{process.pid}/status").read_text()
                        fields = {line.split(":", 1)[0]: line.split(":", 1)[1] for line in status.splitlines()}
                        peak = max(peak, int(fields.get("VmHWM", "0 kB").split()[0]))
                    except FileNotFoundError:
                        pass
                    if peak > args.rss_limit_gib * 1024 * 1024:
                        stop_reason = "rss-threshold"
                    elif time.monotonic() - started > args.timeout:
                        stop_reason = "timeout"
                    elif log.tell() > 8 * 1024 * 1024:
                        stop_reason = "log-size"
                    if stop_reason:
                        stop(process)
                        break
                    time.sleep(0.1)
                code = process.wait()
        except BaseException:
            if process is not None and process.poll() is None:
                stop(process)
            raise
        peak = max(peak, resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
        result.update(exit_code=code, wall_seconds=time.monotonic() - started,
                      peak_rss_kib=peak, peak_rss_gib=peak / (1024 * 1024), stop_reason=stop_reason,
                      finished_utc=datetime.now(timezone.utc).isoformat(),
                      interfaces_after=len(list(root.rglob("*.agdai"))))
        try:
            result["source_unchanged"] = source_identity(root)["source_sha256"] == source["source_sha256"]
        except ValueError:
            result["source_unchanged"] = False
        result["accepted"] = code == 0 and stop_reason is None and result["source_unchanged"]
        (output / (args.label + ".json")).write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 0 if result["accepted"] else (code if code > 0 else 1)

if __name__ == "__main__":
    sys.exit(main())
