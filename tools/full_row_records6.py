"""Lossless bounded archives for full-row production evidence.

The caller owns synchronization.  This module never runs a checker and never
removes an input until the newly appended archive member has been fsynced and
read back byte-for-byte.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import base64
import stat
import tarfile
import zipfile

from compression import zstd


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(Path(path).read_bytes())


def fsync_file(path: Path) -> None:
    with Path(path).open("rb") as stream:
        os.fsync(stream.fileno())


def fsync_directory(path: Path) -> None:
    descriptor = os.open(Path(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_bytes(path: Path, raw: bytes, *, mode: int | None = None,
                 atime_ns: int | None = None, mtime_ns: int | None = None) -> None:
    path = Path(path)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    with temporary.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if mode is not None:
        os.chmod(temporary, mode)
    if atime_ns is not None and mtime_ns is not None:
        os.utime(temporary, ns=(atime_ns, mtime_ns))
    os.replace(temporary, path)
    fsync_directory(path.parent)


def journal_path(path: Path) -> Path:
    path = Path(path)
    return path.with_name(path.name + '.append-journal')


def _write_append_journal(path: Path, member: str, raw: bytes) -> dict:
    path = Path(path)
    if path.exists():
        with zipfile.ZipFile(path) as archive:
            start = archive.start_dir
        original_size = path.stat().st_size
        with path.open('rb') as stream:
            stream.seek(start)
            tail = stream.read()
    else:
        start = original_size = 0
        tail = b''
    journal = {'format': 'othello-durable-zip-append-v1', 'archive': str(path),
        'member': member, 'member_sha256': sha_bytes(raw), 'member_bytes': len(raw),
        'original_size': original_size, 'start_dir': start,
        'tail_sha256': sha_bytes(tail), 'tail_base64': base64.b64encode(tail).decode()}
    target = journal_path(path)
    if target.exists():
        raise ValueError(f'unresolved ZIP append journal: {target}')
    atomic_bytes(target, (json.dumps(journal, sort_keys=True)+'\n').encode(), mode=0o600)
    return journal


def read_append_journal(path: Path) -> dict | None:
    target = journal_path(path)
    return None if not target.exists() else json.loads(target.read_text())


def commit_append(path: Path) -> None:
    target = journal_path(path)
    if target.exists():
        target.unlink()
        fsync_directory(target.parent)


def recover_append(path: Path, committed) -> str:
    """Commit a proven append or restore the exact pre-append central-directory tail."""
    path = Path(path)
    target = journal_path(path)
    if not target.exists():
        return 'none'
    journal = json.loads(target.read_text())
    tail = base64.b64decode(journal['tail_base64'])
    if sha_bytes(tail) != journal['tail_sha256']:
        raise ValueError('ZIP append recovery tail changed')
    appended = False
    try:
        with zipfile.ZipFile(path) as archive:
            appended = (archive.namelist().count(journal['member']) == 1 and
                sha_bytes(archive.read(journal['member'])) == journal['member_sha256'])
    except (OSError, zipfile.BadZipFile, KeyError):
        appended = False
    if appended and committed(journal):
        commit_append(path)
        return 'committed'
    if journal['original_size'] == 0:
        if path.exists():
            path.unlink()
    else:
        with path.open('r+b') as stream:
            stream.seek(journal['start_dir'])
            stream.write(tail)
            stream.truncate(journal['original_size'])
            stream.flush(); os.fsync(stream.fileno())
        if path.stat().st_size != journal['original_size']:
            raise ValueError('ZIP append rollback size differs')
        with path.open('rb') as stream:
            stream.seek(journal['start_dir'])
            if stream.read() != tail:
                raise ValueError('ZIP append rollback tail differs')
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError('ZIP append rollback retained a corrupt member')
    commit_append(path)
    fsync_directory(path.parent)
    return 'rolled-back'


def append_stored(path: Path, member: str, raw: bytes) -> dict:
    """Append one uniquely named stored ZIP member and verify the new archive."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if path.exists():
        with zipfile.ZipFile(path) as archive:
            existing = set(archive.namelist())
            if member in existing:
                old = archive.read(member)
                if old != raw:
                    raise ValueError(f"archive member collision: {member}")
                return {"member": member, "sha256": sha_bytes(raw), "bytes": len(raw),
                        "archive_sha256": sha(path), "already_present": True}
    journal = _write_append_journal(path, member, raw)
    with zipfile.ZipFile(path, "a", allowZip64=True) as archive:
        archive.writestr(member, raw, compress_type=zipfile.ZIP_STORED)
    fsync_file(path)
    fsync_directory(path.parent)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names.count(member) != 1 or set(names) != existing | {member}:
            raise ValueError("ZIP member inventory changed unexpectedly")
        if archive.read(member) != raw:
            raise ValueError("ZIP readback differs from appended bytes")
    return {"member": member, "sha256": sha_bytes(raw), "bytes": len(raw),
            "archive_sha256": sha(path), "already_present": False,
            "append_journal": str(journal_path(path)),
            "original_size": journal['original_size'], "start_dir": journal['start_dir'],
            "saved_tail_sha256": journal['tail_sha256']}


def _entry(path: Path, relative: str) -> tuple[dict, bytes]:
    info = path.stat()
    raw = path.read_bytes()
    return ({"path": relative, "sha256": sha_bytes(raw), "bytes": len(raw),
             "mode": stat.S_IMODE(info.st_mode), "atime_ns": info.st_atime_ns,
             "mtime_ns": info.st_mtime_ns}, raw)


def cohort_blob(root: Path, relatives: list[str], metadata: dict) -> tuple[bytes, dict]:
    """Encode exact file bytes plus mode and nanosecond timestamps in one zstd tar."""
    root = Path(root)
    entries = []
    payloads = {}
    for relative in sorted(set(relatives)):
        path = root / relative
        if not path.is_file():
            raise ValueError(f"missing cohort input: {relative}")
        entry, raw = _entry(path, relative)
        entries.append(entry)
        payloads[relative] = raw
    manifest = {"format": "othello-full-row-record-cohort-v1",
                "metadata": metadata, "entries": entries}
    manifest_raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    memory = io.BytesIO()
    with tarfile.open(fileobj=memory, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for entry in entries:
            info = tarfile.TarInfo("files/" + entry["path"])
            info.size = entry["bytes"]
            info.mode = entry["mode"]
            info.mtime = entry["mtime_ns"] // 1_000_000_000
            archive.addfile(info, io.BytesIO(payloads[entry["path"]]))
        info = tarfile.TarInfo("MANIFEST.json")
        info.size = len(manifest_raw)
        info.mode = 0o444
        info.mtime = 0
        archive.addfile(info, io.BytesIO(manifest_raw))
    blob = zstd.compress(memory.getvalue(), level=19)
    verify_cohort_blob(blob, manifest, payloads)
    return blob, manifest


def verify_cohort_blob(blob: bytes, expected_manifest: dict | None = None,
                       expected_payloads: dict[str, bytes] | None = None) -> dict:
    decoded = zstd.decompress(blob)
    with tarfile.open(fileobj=io.BytesIO(decoded), mode="r:") as archive:
        manifest = json.loads(archive.extractfile("MANIFEST.json").read())
        if expected_manifest is not None and manifest != expected_manifest:
            raise ValueError("cohort manifest readback differs")
        for entry in manifest["entries"]:
            raw = archive.extractfile("files/" + entry["path"]).read()
            if len(raw) != entry["bytes"] or sha_bytes(raw) != entry["sha256"]:
                raise ValueError("cohort payload readback differs")
            if expected_payloads is not None and raw != expected_payloads[entry["path"]]:
                raise ValueError("cohort source bytes differ")
    return manifest


def archive_cohort(zip_path: Path, member: str, root: Path, relatives: list[str],
                   metadata: dict) -> dict:
    payloads = {relative: (Path(root) / relative).read_bytes()
                for relative in sorted(set(relatives))}
    blob, manifest = cohort_blob(root, relatives, metadata)
    result = append_stored(zip_path, member, blob)
    with zipfile.ZipFile(zip_path) as archive:
        verify_cohort_blob(archive.read(member), manifest, payloads)
    result.update(decoded_tar_sha256=sha_bytes(zstd.decompress(blob)),
                  manifest=manifest)
    return result
