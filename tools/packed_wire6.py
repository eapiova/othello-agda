"""Authenticated bounded streaming of a sealed wire ZIP; untrusted data only."""
import hashlib
import os
from pathlib import Path
import stat
import zipfile
from wire_part_samples6 import _fingerprint,_state,MAX_RECORD_BYTES,MAX_WIRE_BYTES


def records(meta):
    path=Path(meta['archive']).absolute()
    assert path==path.resolve() and not any(p.is_symlink() for p in (path,*path.parents))
    before=path.stat();identity=_fingerprint(before)
    assert stat.S_ISREG(before.st_mode) and before.st_size==meta['archive_bytes']<=MAX_WIRE_BYTES
    physical=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):physical.update(block)
    assert physical.hexdigest()==meta['archive_sha256']
    h=hashlib.sha256();rank=size=0
    with path.open('rb') as physical,zipfile.ZipFile(physical) as saved:
        assert _fingerprint(os.fstat(physical.fileno()))==identity
        assert saved.namelist()==[meta['archive_entry']]
        info=saved.getinfo(meta['archive_entry'])
        assert info.file_size==meta['raw_bytes']<=MAX_WIRE_BYTES and info.compress_type==93
        with saved.open(meta['archive_entry']) as f:
            while raw:=f.readline(MAX_RECORD_BYTES+1):
                assert len(raw)<=MAX_RECORD_BYTES and raw.endswith(b'\n') and rank<meta['raw_rows']
                h.update(raw);size+=len(raw);assert size<=meta['raw_bytes']
                fields=raw[:-1].split(b'\t');assert len(fields)==3
                state,body,refs=fields;_state(state);assert len(refs)%13==0
                yield rank,state,body,refs
                rank+=1
        assert _fingerprint(os.fstat(physical.fileno()))==identity
    assert rank==meta['raw_rows'] and size==meta['raw_bytes'] and h.hexdigest()==meta['raw_sha256']
    assert _fingerprint(path.stat())==identity
