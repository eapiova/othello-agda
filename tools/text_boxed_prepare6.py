"""Opaque proof fields for the full actual text map; no game-row rechecking."""
import json
from pathlib import Path
import shutil
from provenance import source_identity
from run_job import atomic_json,utc
from full_upper_prepare6 import HEADER

ROOT=Path(__file__).resolve().parents[1]


def prepare(out):
    out=Path(out);check=out/'check';assert not check.exists()
    core=check/'src/Othello/TextCertifiedAssembly6.agda';core.parent.mkdir(parents=True)
    shutil.copy2(ROOT/'src/Othello/TextCertifiedAssembly6.agda',core)
    donor=out.with_name('text-upper-probe6-20261018-fixed')/'check'
    folder=check/'src/Tests/CertifiedFullUpper6';folder.mkdir(parents=True)
    source=(donor/'src/Tests/TextUpperPacked6/Assembly.agda').read_text()
    source=source.replace('module Tests.TextUpperPacked6.Assembly','module Tests.CertifiedFullUpper6.Assembly')
    source=source.replace('import Othello.TextStateAssembly6 as Assembly','import Othello.TextCertifiedAssembly6 as Assembly')
    source=source.replace('Parts.Partial','Parts.Certified')
    source=source.replace('complete : CheckedParts → ∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (Global.G key))',
        'complete : CheckedParts → Parts.ProvenMap Global.G')
    (folder/'Assembly.agda').write_text(source)
    (folder/'Samples.agda').write_text(HEADER+'''-- AI-assisted. Reuse both accepted10000-row Parts; no Boolean rerun.
module Tests.CertifiedFullUpper6.Samples where
open import Game.Core using (black)
open import Othello.Statements using (upperGoal)
import Othello.TextCertifiedAssembly6 as Box
import Tests.TextUpperPacked6.Root as Global
import Tests.TextUpperPacked6.Group6 as G6
import Tests.TextUpperPacked6.Group652 as G652
import Tests.TextUpperPacked6.Rows6 as P6
import Tests.TextUpperPacked6.Rows652 as P652
module Parts = Box.Assembly black (upperGoal 4)
abstract
  part6 : Parts.Certified Global.G G6.table
  part6 = Parts.certify Global.G G6.table P6.partial
  part652 : Parts.Certified Global.G G652.table
  part652 = Parts.certify Global.G G652.table P652.partial
''')
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        full_state_rows=6530011,reused_owned_rows=20000,additional_boolean_row_checks=0,
        additional_zip_scans=0,proof_container_has_only_constructor_requiring_Partial=True,
        initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
