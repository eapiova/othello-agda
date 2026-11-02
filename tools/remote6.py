#!/usr/bin/env python3
"""Freeze, submit, inspect and collect desktop study jobs over authenticated SSH.

The desktop service continues after the SSH connection and laptop disappear.
Only the coordinator writes the CPU ledger; collect charges actual final rusage.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile

from provenance import source_files, digest_entries, git_info, source_identity
from remote_worker6 import checked_label
from run_job import add_caps, atomic_json, utc
from study6 import Ledger
from closed_pilot_policy6 import free_disk_gib, full_map_exception

ROOT = Path(__file__).resolve().parents[1]


def ssh(host, argv, data=None):
    # OpenSSH sends a command string to a login shell; quote each argument once.
    return subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                           host, shlex.join(argv)], input=data, capture_output=True, check=True)


def snapshot(root, path):
    root = Path(root).resolve()
    # An emitted benchmark already has a frozen manifest. Validate it and keep
    # its Git origin when making the second transport snapshot.
    source_identity(root)
    previous = root / "SNAPSHOT.json"
    origin = json.loads(previous.read_text())["git"] if previous.exists() else git_info(root)
    captured = list(source_files(root))
    files = {name: hashlib.sha256(data).hexdigest() for name, data in captured}
    manifest = {"format": "othello-source-snapshot-v1", "files": files,
                "source_sha256": digest_entries(files), "git": origin, "created_utc": utc()}
    with tarfile.open(path, "w:gz") as archive:
        extra = [("SNAPSHOT.json", (json.dumps(manifest, indent=2) + "\n").encode())]
        for name, data in captured + extra:
            item = tarfile.TarInfo(name)
            item.size = len(data)
            item.mode = 0o755 if name.startswith("scripts/") and name.endswith(".sh") else 0o644
            archive.addfile(item, io.BytesIO(data))
    return manifest


def worker(host, remote, action):
    reply = ssh(host, ["python3", remote + "/tools/remote_worker6.py", action, "--root", remote])
    return json.loads(reply.stdout)


def submit(args, command):
    checked_label(args.label)
    if args.smoke and (args.cpu_limit > 30 or args.rss_limit_gib > 1):
        raise ValueError("--smoke requires --cpu-limit <=30 and --rss-limit-gib <=1")
    if args.rss_limit_gib + .25 > 15:
        raise ValueError("per-job memory plus supervisor margin must fit the 15 GiB slice")
    scope_approval = None
    if full_map_exception(args.label, command, args.cpu_limit, args.rss_limit_gib, smoke=args.smoke):
        approval = json.loads((ROOT / 'results/full-state-map6-20261016/authorization.json').read_text())
        if (approval.get('approved') is not True or
                approval.get('answer') != 'Sì, autorizzo questo test completo delle mappe' or
                approval['resources'] != dict(total_cpu_seconds=3600,hard_memory_gib=12,
                    artifact_cap_gib=12,free_disk_gib=80,heavy_jobs=1)):
            raise ValueError('exact human-approved full-map stage required')
        current = Ledger(args.ledger).status()
        spent = current['charged_cpu_seconds'] - approval['ledger_at_approval']['charged_cpu_seconds']
        stage_unknown = current['withheld_cpu_seconds'] - approval['ledger_at_approval']['withheld_cpu_seconds']
        allowance = args.cpu_limit + max(2,(os.cpu_count() or 1)*.1)
        if spent < 0 or stage_unknown < 0 or spent + stage_unknown + current['reserved_cpu_seconds'] + allowance > 3600:
            raise ValueError('full-map stage CPU ceiling reached; no new launch')
        if current['outstanding']:
            raise ValueError('full-map pilot requires no other outstanding heavy job')
        if args.label == 'full-map-lower-row-link-20261016':
            scope_approval = json.loads((ROOT / 'results/full-map-alignment6-20261016/row-link-authorization.json').read_text())
            if (scope_approval.get('approved') is not True or
                    scope_approval.get('answer') != 'Sì, autorizzo solo questo collegamento' or
                    scope_approval.get('cpu_max_seconds') != 300 or
                    scope_approval.get('hard_memory_gib') != 12 or
                    scope_approval.get('artifact_cap_gib') != 12 or
                    scope_approval.get('free_disk_gib') != 80 or
                    scope_approval.get('new_boolean_rows') != 0):
                raise ValueError('separate approved row-link scope required')
            row_spent = current['charged_cpu_seconds'] - scope_approval['ledger_at_approval']['charged_cpu_seconds']
            row_unknown = current['withheld_cpu_seconds'] - scope_approval['ledger_at_approval']['withheld_cpu_seconds']
            if row_spent + row_unknown + allowance > 300:
                raise ValueError('row-link test CPU ceiling reached')
    directory = ROOT / "results/remote6" / args.label
    directory.mkdir(parents=True, exist_ok=False)
    archive = directory / "source.tar.gz"
    manifest = snapshot(args.root, archive)
    prepare = '''import pathlib,shutil,sys
p=pathlib.Path.home()/"projects/othello-agda/runs"/("six-"+sys.argv[1])
need=int(sys.argv[2])*1024**3
if shutil.disk_usage(pathlib.Path.home()).free<need: raise SystemExit("desktop disk cleanup gate not met")
p.mkdir(parents=True,exist_ok=False)
print(p)
'''
    floor = free_disk_gib(args.label, command, args.cpu_limit, args.rss_limit_gib, smoke=args.smoke)
    remote = ssh(args.host, ["python3", "-c", prepare, args.label,
                             "8" if args.smoke else str(floor)]).stdout.decode().strip()
    extract = '''import hashlib,io,pathlib,sys,tarfile
p=pathlib.Path(sys.argv[1]); raw=sys.stdin.buffer.read()
if hashlib.sha256(raw).hexdigest()!=sys.argv[2]: raise SystemExit("archive hash mismatch")
with tarfile.open(fileobj=io.BytesIO(raw),mode="r:gz") as a:
 for m in a.getmembers():
  if not m.isfile() or pathlib.PurePosixPath(m.name).is_absolute() or ".." in pathlib.PurePosixPath(m.name).parts: raise SystemExit("unsafe archive member")
 a.extractall(p,filter="data")
'''
    raw = archive.read_bytes()
    ssh(args.host, ["python3", "-c", extract, remote, hashlib.sha256(raw).hexdigest()], raw)
    # Deployment completes before reserving. An ambiguous launch keeps the
    # reservation held until a real final record can be collected.
    ledger = Ledger(args.ledger)
    reservation = ledger.reserve(args.category, args.cpu_limit + max(2, (os.cpu_count() or 1) * .1), args.label)
    job = {"label": args.label, "host": args.host, "remote_root": remote,
           "local_source_root": str(args.root.resolve()),
           "source_sha256": manifest["source_sha256"], "archive_sha256": hashlib.sha256(raw).hexdigest(),
           "ledger": str(args.ledger.resolve()), "reservation_id": reservation["reservation_id"],
           "category": args.category, "command": command, "timeout": args.timeout,
           "cpu_limit": args.cpu_limit, "rss_limit_gib": args.rss_limit_gib,
           "log_limit_mib": args.log_limit_mib, "smoke": args.smoke, "created_utc": utc()}
    if scope_approval is not None:
        job["scope_approval"] = scope_approval
    atomic_json(directory / "job.json", job)
    write = '''import pathlib,sys
p=pathlib.Path(sys.argv[1])/"results"; p.mkdir(exist_ok=True)
(p/"remote-job.json").write_bytes(sys.stdin.buffer.read())
'''
    ssh(args.host, ["python3", "-c", write, remote], json.dumps(job).encode())
    try:
        return {"job": job, "started": worker(args.host, remote, "start")}
    except subprocess.CalledProcessError as error:
        raise ValueError("remote launch uncertain or failed; reservation retained. Use status/collect. "
                         + error.stderr.decode(errors="replace")) from error


def existing(args):
    checked_label(args.label)
    directory = ROOT / "results/remote6" / args.label
    job = json.loads((directory / "job.json").read_text())
    result = worker(job["host"], job["remote_root"], "cancel" if args.action == "cancel" else "status")
    if args.action == "collect":
        if result["measurement"] is None:
            raise ValueError("no complete measurement yet; reservation remains held")
        for suffix in ("json", "log"):
            filename = args.label + "." + suffix
            data = ssh(job["host"], ["cat", job["remote_root"] + "/results/" + filename]).stdout
            (directory / filename).write_bytes(data)
        Ledger(job["ledger"]).finish(job["reservation_id"], directory / (args.label + ".json"))
        result["collected_to"] = str(directory)
    return result


def fetch(args):
    """Retrieve explicitly named result artifacts, without copying interfaces."""
    checked_label(args.label)
    directory = ROOT / "results/remote6" / args.label
    job = json.loads((directory / "job.json").read_text())
    script = '''import pathlib,sys
root=pathlib.Path(sys.argv[1]).resolve(); relative=pathlib.PurePosixPath(sys.argv[2])
if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0]!="results": raise SystemExit("only relative results artifacts are allowed")
path=root.joinpath(*relative.parts)
if path.is_symlink() or not path.resolve().is_relative_to(root/"results") or not path.is_file(): raise SystemExit("invalid result artifact")
maximum=int(sys.argv[3])
with path.open("rb") as stream:
 data=stream.read(maximum+1)
 if len(data)>maximum: raise SystemExit("artifact exceeds transfer cap")
 sys.stdout.buffer.write(data)
'''
    records = []
    for relative in args.files:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "results":
            raise ValueError("only relative results artifacts are allowed")
        if path.suffix in (".agdai", ".o", ".hi"):
            raise ValueError("build interfaces and object files stay on their checking machine")
        data = ssh(job["host"], ["python3", "-c", script, job["remote_root"],
                                  path.as_posix(), str(args.max_mib * 1024**2)]).stdout
        destination = directory / "artifacts" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        records.append({"path": path.as_posix(), "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest()})
    atomic_json(directory / "artifacts/last-transfer.json", {"created_utc": utc(), "files": records})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    start = subs.add_parser("submit")
    start.add_argument("category", choices=("native", "kernel", "compiled", "assembly"))
    start.add_argument("label")
    start.add_argument("--host", default="desktop")
    start.add_argument("--ledger", type=Path, default=ROOT / "results/study6-ledger.json")
    start.add_argument("--root", type=Path, default=ROOT,
                       help="source root, including a separately frozen benchmark root")
    start.add_argument("--smoke", action="store_true", help="bounded plumbing test before the 100 GiB gate")
    add_caps(start)
    for action in ("status", "collect", "cancel"):
        subs.add_parser(action).add_argument("label")
    transfer = subs.add_parser("fetch")
    transfer.add_argument("label")
    transfer.add_argument("files", nargs="+")
    transfer.add_argument("--max-mib", type=int, choices=range(1, 129), default=32)
    split = sys.argv.index("--") if "--" in sys.argv else len(sys.argv)
    args = parser.parse_args(sys.argv[1:split])
    try:
        if args.action == "submit":
            if split == len(sys.argv) or not sys.argv[split + 1:]:
                parser.error("submit requires -- COMMAND")
            if not re.fullmatch(r"[A-Za-z0-9_.@-]+", args.host):
                parser.error("use a configured SSH hostname")
            result = submit(args, sys.argv[split + 1:])
        elif args.action == "fetch":
            result = fetch(args)
        else:
            result = existing(args)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
