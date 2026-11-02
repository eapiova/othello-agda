"""Seal the complete live text cache without modifying its plaintext source."""
import hashlib,json,stat,struct,zipfile
from pathlib import Path
import assembly6
from provenance import source_identity,digest_entries
from run_job import atomic_json,utc


def prepare(out):
    out=Path(out);request=json.loads((out/'input-request.json').read_text());source=Path(request['source'])
    identity=source_identity(source);pool=assembly6.interfaces(source)
    assert identity['source_sha256']==request['source_sha256'] and digest_entries(pool)==request['interface_pool_sha256']
    archive=out/'text-cache.zip';assert not archive.exists();entries={};total=0
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as saved:
        for p in sorted(source.rglob('*')):
            s=p.stat();assert not p.is_symlink() and (p.is_file() or p.is_dir())
            name=p.relative_to(source).as_posix()+('/' if p.is_dir() else '')
            raw=p.read_bytes() if p.is_file() else b'';total+=len(raw)
            assert len(entries)<5000 and len(raw)<=16*2**20 and total<=192*2**20
            info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=s.st_mode<<16
            info.extra=struct.pack('<HHQ',0xa6da,8,s.st_mtime_ns);info.compress_type=zipfile.ZIP_DEFLATED
            saved.writestr(info,raw)
            entries[name]=dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=s.st_mode,mtime_ns=s.st_mtime_ns)
    assert source_identity(source)==identity and assembly6.interfaces(source)==pool
    with zipfile.ZipFile(archive) as saved:
        assert set(saved.namelist())==set(entries)
        for name,e in entries.items():assert hashlib.sha256(saved.read(name)).hexdigest()==e['sha256']
    h=hashlib.sha256()
    with archive.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    atomic_json(out/'archive-manifest.json',dict(format='othello-sealed-full-text-cache-v1',created_utc=utc(),
        source=str(source),source_identity=identity,interfaces=pool,interface_pool_sha256=digest_entries(pool),entries=entries,
        raw_bytes=total,archive=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=h.hexdigest(),
        original_source_removed=False,mathematical_objective_complete=False))
    check=out/'check';(check/'src/Tests').mkdir(parents=True)
    (check/'src/Tests/SealedTextReplay6.agda').write_text('''{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted: load the exact accepted dense-row interface through the sealed view.
module Tests.SealedTextReplay6 where
import Tests.TextUpperPacked6.Rows652
''')
    root=Path(__file__).resolve().parents[1]
    __import__('shutil').copy2(root/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),archive_bytes=archive.stat().st_size,
        additional_game_row_checks=0,new_native_solver_runs=0,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
