"""Exact source and executable identities for checking claims."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess

EXCLUDED = {".git", ".codex", "_build", "deps", "results", "dist", "__pycache__"}

def source_files(root: Path):
    for parent, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED)
        for name in sorted(files):
            if name.endswith((".agdai", ".pyc", ".lock")) or name == "SNAPSHOT.json":
                continue
            path = Path(parent) / name
            yield path.relative_to(root).as_posix(), path.read_bytes()

def digest_entries(entries: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def git_info(root: Path) -> dict:
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True)
    return {"revision": head.stdout.strip() if head.returncode == 0 else None,
            "dirty": bool(status.stdout.strip()) if status.returncode == 0 else None}

def source_identity(root: Path) -> dict:
    entries = {name: hashlib.sha256(data).hexdigest() for name, data in source_files(root)}
    manifest_path = root / "SNAPSHOT.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if entries != manifest["files"] or digest_entries(entries) != manifest["source_sha256"]:
            raise ValueError("transferred snapshot changed: source manifest does not match files")
        origin = manifest["git"]
    else:
        origin = git_info(root)
    return {"source_sha256": digest_entries(entries), "source_files": len(entries), **origin}
