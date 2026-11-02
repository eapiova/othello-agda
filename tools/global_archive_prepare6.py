"""Source-only preparation for a bounded ZIP-view/global-row check."""
import json
from pathlib import Path
import shutil

from provenance import source_identity
from run_job import atomic_json,utc
from study_archive6 import pack

ROOT=Path(__file__).resolve().parents[1]
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'


def prepare(out):
    out=Path(out)
    request=json.loads((out/'input-request.json').read_text())
    assert not (out/'check').exists()
    folder=out/'check/src/Othello';folder.mkdir(parents=True)
    shutil.copy2(ROOT/'src/Othello/GlobalPackedRows6.agda',folder/'GlobalPackedRows6.agda')
    module='Tests.GlobalArchiveRows6.Part342'
    target=out/'check/src/Tests/GlobalArchiveRows6/Part342.agda';target.parent.mkdir(parents=True)
    target.write_text(HEADER+'-- AI-assisted: same1000 LOWER rows, direct global lookup, no local payload.\nmodule '+module+''' where

open import Prelude
import Game.NatMap as M
import Othello.GlobalPackedRows6 as Rows
import Othello.UnicodeCompact6 as Codec
import Tests.PackedCommonRows6.Data as Global
import Tests.BigRowsScaling6.TrainLow.TextBodies as Body

abstract
  partial : Rows.A.Partial Global.G (M.rows 68400 1000 (Rows.ps Global.G 68400 1000))
  partial = Rows.partial Global.G 68400 1000 (Codec.bodies 1000 Body.text) refl
-- Referenced rows, the remaining initial guarantees and the final pair are open.
''')
    shutil.copy2(ROOT/'othello.agda-lib',out/'check/othello.agda-lib')
    result=pack(Path(request['archive_source']),out/'proof.zip',out/'archive-manifest.json')
    assert result['source_identity']['source_sha256']==request['archive_source_sha256']
    assert result['interface_pool_sha256']==request['archive_interface_pool_sha256']
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(out/'check'),
        archive_source_identity=result['source_identity'],archive_interface_pool_sha256=result['interface_pool_sha256'],
        original_source_removed=False,archive_bytes=result['archive_bytes'],raw_archive_bytes=result['raw_bytes'],
        copied_core_sha256={'src/Othello/GlobalPackedRows6.agda':__import__('hashlib').sha256((folder/'GlobalPackedRows6.agda').read_bytes()).hexdigest()},
        repeated_rows=1000,no_new_wire_scan=True,no_solver=True,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
