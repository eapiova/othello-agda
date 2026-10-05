#!/usr/bin/env python3
"""Freeze a source snapshot and a manifest before transferring a compute job."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
from datetime import datetime, timezone
from provenance import source_files, digest_entries, git_info

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    captured = list(source_files(root))
    entries = {name: hashlib.sha256(data).hexdigest() for name, data in captured}
    manifest = {"format": "othello-source-snapshot-v1", "source_sha256": digest_entries(entries),
                "files": entries, "git": git_info(root),
                "created_utc": datetime.now(timezone.utc).isoformat()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.output, "w:gz") as archive:
        for name, data in captured + [("SNAPSHOT.json", (json.dumps(manifest, indent=2) + "\n").encode())]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755 if name.startswith("scripts/") and name.endswith(".sh") else 0o644
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))
    print(json.dumps({"archive": str(args.output), "archive_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                      "bytes": args.output.stat().st_size, "source_sha256": manifest["source_sha256"]}, indent=2))

if __name__ == "__main__":
    main()
