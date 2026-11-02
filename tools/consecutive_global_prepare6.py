"""Reuse exact accepted compact state/body data; no new extraction."""
import hashlib
import json
from pathlib import Path
import shutil
from provenance import source_identity
from run_job import atomic_json,utc

ROOT=Path(__file__).resolve().parents[1]
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'


def prepare(out):
    out=Path(out);check=out/'check';assert not check.exists()
    target=check/'src/Othello/ConsecutivePackedRows6.agda';target.parent.mkdir(parents=True)
    core=ROOT/'src/Othello/ConsecutivePackedRows6.agda';shutil.copy2(core,target)
    folder=check/'src/Tests/ConsecutiveGlobalBatch6';folder.mkdir(parents=True)
    (folder/'Closed.agda').write_text(HEADER+'''-- AI-assisted same10000 rows; sequential owners and shared data.
module Tests.ConsecutiveGlobalBatch6.Closed where
open import Prelude
import Game.NatMap as M
import Othello.ConsecutivePackedRows6 as Rows
import Othello.UnicodeCompact6 as Codec
import Tests.CompactGlobalBatch6.Root as Global
import Tests.CompactGlobalBatch6.Body as Body
abstract
  partial : Rows.A.Partial Global.G (M.rows 68400 10000 (Rows.ps Global.G 68400 10000))
  partial = Rows.partial Global.G 68400 10000 (Codec.bodies 10000 Body.text) refl
-- All unowned rows, the initial bound and the SAME optimal pair remain open.
''')
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        copied_core_sha256={'src/Othello/ConsecutivePackedRows6.agda':hashlib.sha256(core.read_bytes()).hexdigest()},
        owned_rows=10000,additional_wire_scans=0,new_native_solver_runs=0,
        same_donor_state_and_body_sources=True,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
