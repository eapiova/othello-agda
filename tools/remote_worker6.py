#!/usr/bin/env python3
"""Desktop-side lifecycle for detached, measured study jobs (no public listener)."""
from __future__ import annotations
import argparse
import fcntl
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from provenance import source_identity
from run_job import atomic_json, run_job, utc
from closed_pilot_policy6 import free_disk_gib, artifact_cap_gib

GIB = 1024 ** 3
SLICE = "othello6.slice"


def checked_label(label):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", label):
        raise ValueError("label must be 1–64 safe filename characters")
    return label


def read_job(root):
    path = root / "results" / "remote-job.json"
    job = json.loads(path.read_text())
    checked_label(job["label"])
    if job["source_sha256"] != source_identity(root)["source_sha256"]:
        raise ValueError("frozen job source does not match its manifest")
    if not job["command"] or not all(isinstance(x, str) for x in job["command"]):
        raise ValueError("command must be an argv list")
    return job


def provision_slice():
    # A separate aggregate cgroup covers every study job on this desktop.
    directory = Path.home() / ".config/systemd/user"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / SLICE
    content = ("[Unit]\nDescription=Othello feasibility study jobs\n\n[Slice]\n"
               "MemoryAccounting=yes\nMemoryMax=15G\nMemorySwapMax=0\n")
    if path.exists() and path.read_text() != content:
        raise ValueError("existing othello6.slice differs; inspect it before replacing")
    if not path.exists():
        path.write_text(content)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)


def disk_preflight(root, job):
    # The cleanup gate remains mandatory for study jobs. Smoke jobs are bounded
    # plumbing checks while the archive is still in progress, never searches.
    smoke = job.get("smoke", False)
    if smoke and (job["cpu_limit"] > 30 or job["rss_limit_gib"] > 1):
        raise ValueError("smoke jobs must fit 30 CPU seconds and 1 GiB")
    floor = free_disk_gib(job['label'], job['command'], job['cpu_limit'], job['rss_limit_gib'], smoke=smoke)
    needed = (8 if smoke else floor) * GIB
    free = shutil.disk_usage(root).free
    if free < needed:
        raise ValueError(f"desktop has {free/GIB:.2f} GiB free; requires {needed/GIB:.0f}")
    runs = root.parent
    # du counts allocated bytes, including separate isolated build directories.
    result = subprocess.run(["du", "-s", "-B1", str(runs)], check=True,
                            text=True, capture_output=True)
    allocated = int(result.stdout.split()[0])
    cap = artifact_cap_gib(job["label"], job["command"], job["cpu_limit"], job["rss_limit_gib"], smoke=smoke)
    if allocated >= cap * GIB:
        raise ValueError(f"study run directories already occupy the {cap} GiB allowance")
    return {"disk_free_bytes": free, "run_directories_bytes": allocated,
            "required_free_bytes": needed}


def start(root):
    job = read_job(root)
    output = root / "results"
    with (output / "launch.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        started = output / "remote-start.json"
        if started.exists():
            # An uncertain SSH response can be retried without launching twice.
            record = json.loads(started.read_text())
            if record.get("launch_exit_code", 0):
                raise ValueError("previous launch failed; inspect status before starting another job")
            return record
        preflight = disk_preflight(root, job)
        provision_slice()
        unit = "othello6-" + job["label"] + ".service"
        command = ["systemd-run", "--user", "--quiet", "--unit=" + unit,
                   "--slice=" + SLICE, "--service-type=exec",
                   "--property=MemoryAccounting=yes",
                   "--property=MemoryMax=" + str(int((job["rss_limit_gib"] + .25) * GIB)),
                   "--property=MemorySwapMax=0", "--property=KillMode=mixed",
                   "--property=TimeoutStopSec=20", "--property=RuntimeMaxSec=" + str(job["timeout"] + 30),
                   "--property=StandardOutput=null", "--property=StandardError=journal",
                   "--working-directory=" + str(root), sys.executable,
                   str(root / "tools/remote_worker6.py"), "run", "--root", str(root)]
        # Persist launch intent first. If systemd-run loses its reply, status can
        # distinguish an absent unit from a launched job; never silently retry it.
        record = {"unit": unit, "label": job["label"], "root": str(root),
                  "launch_requested_utc": utc(), **preflight}
        atomic_json(started, record)
        result = subprocess.run(command, capture_output=True, text=True)
        record.update(launch_exit_code=result.returncode, launch_stderr=result.stderr[-4096:])
        atomic_json(started, record)
        if result.returncode:
            raise ValueError("systemd launch failed; reservation remains held: " + result.stderr)
        return record


def status(root):
    job = read_job(root)
    unit = "othello6-" + job["label"] + ".service"
    proc = subprocess.run(["systemctl", "--user", "show", unit,
                           "--property=LoadState,ActiveState,SubState,Result,MainPID,CPUUsageNSec,MemoryCurrent,MemoryPeak"],
                          capture_output=True, text=True)
    state = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
    result = root / "results" / (job["label"] + ".json")
    return {"label": job["label"], "unit": unit, "systemd": state,
            "measurement": json.loads(result.read_text()) if result.exists() else None}


def cancel(root):
    job = read_job(root)
    subprocess.run(["systemctl", "--user", "stop", "othello6-" + job["label"] + ".service"], check=True)
    return status(root)


def run(root):
    job = read_job(root)
    result = run_job(job["label"], job["command"], root / "results", root=root,
                     timeout=job["timeout"], cpu_limit=job["cpu_limit"],
                     rss_limit_gib=job["rss_limit_gib"], log_limit_mib=job["log_limit_mib"],
                     reservation_id=job["reservation_id"],
                     expected_source_sha256=job["source_sha256"],
                     metadata={"remote_unit": "othello6-" + job["label"] + ".service",
                               "remote_transport": "SSH; detached systemd user service"})
    return 0 if result["accepted"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "status", "cancel", "run"))
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action == "run":
        return run(root)
    print(json.dumps(globals()[args.action](root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
