"""Lossless read-only proof archive with exact timestamps and independent hashes."""
import hashlib
import json
from pathlib import Path
import stat
import struct
import zipfile

from provenance import source_identity, digest_entries
import assembly6
from run_job import atomic_json, utc


def pack(source, archive, manifest):
    source=Path(source);archive=Path(archive);manifest=Path(manifest)
    assert source.is_dir() and not archive.exists() and not manifest.exists()
    before=source_identity(source)
    interfaces=assembly6.interfaces(source)
    entries={};total=0
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for path in sorted(source.rglob('*')):
            assert not path.is_symlink() and (path.is_file() or path.is_dir())
            info=path.stat();relative=path.relative_to(source).as_posix()
            assert 0<=info.st_mtime_ns<2**63 and len(relative)<4094
            assert len(entries)<50000
            if path.is_dir():relative+='/'
            raw=path.read_bytes() if path.is_file() else b''
            total+=len(raw);assert len(raw)<=16*2**20 and total<=64*2**20
            entry=zipfile.ZipInfo(relative);entry.create_system=3
            entry.external_attr=info.st_mode<<16;entry.compress_type=zipfile.ZIP_DEFLATED
            entry.extra=struct.pack('<HHQ',0xa6da,8,info.st_mtime_ns)
            out.writestr(entry,raw)
            entries[relative]=dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                mode=info.st_mode,mtime_ns=info.st_mtime_ns)
    assert source_identity(source)==before and assembly6.interfaces(source)==interfaces
    with zipfile.ZipFile(archive) as saved:
        assert set(saved.namelist())==set(entries) and saved.testzip() is None
        for name,e in entries.items():assert hashlib.sha256(saved.read(name)).hexdigest()==e['sha256']
    result=dict(format='othello-sealed-zip-view6-v1',created_utc=utc(),source=str(source),
        source_identity=before,interfaces=interfaces,interface_pool_sha256=digest_entries(interfaces),
        entries=entries,raw_bytes=total,archive=str(archive),archive_bytes=archive.stat().st_size,
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        original_source_removed=False,mathematical_objective_complete=False)
    atomic_json(manifest,result)
    return result


def verify_view(view, manifest):
    view=Path(view);meta=json.loads(Path(manifest).read_text())
    names={p.relative_to(view).as_posix()+('/' if p.is_dir() else '') for p in view.rglob('*')}
    assert names==set(meta['entries'])
    for name,expected in meta['entries'].items():
        path=view/name;info=path.stat()
        assert not path.is_symlink() and stat.S_IFMT(info.st_mode)==stat.S_IFMT(expected['mode'])
        assert info.st_mode==expected['mode'] and info.st_mtime_ns==expected['mtime_ns']
        if path.is_file():
            assert info.st_size==expected['size']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==expected['sha256']
    assert source_identity(view)==meta['source_identity']
    assert assembly6.interfaces(view)==meta['interfaces']
    return dict(entries_verified=len(names),bytes_verified=meta['raw_bytes'],
        exact_source_identity=True,exact_interface_pool=True,exact_modes_and_timestamps=True)


if __name__=='__main__':
    import sys
    assert len(sys.argv)==4 and sys.argv[1]=='pack'
    out=Path(sys.argv[3]);assert not out.exists();out.mkdir()
    result=pack(Path(sys.argv[2]),out/'proof.zip',out/'archive-manifest.json')
    print(json.dumps(dict(raw_bytes=result['raw_bytes'],archive_bytes=result['archive_bytes'])))
