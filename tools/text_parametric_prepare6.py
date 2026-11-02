"""Keep G symbolic while checking the654-field actual-map composition."""
import textwrap
from pathlib import Path
import shutil
from provenance import source_identity
from run_job import atomic_json,utc

ROOT=Path(__file__).resolve().parents[1]


def prepare(out):
    out=Path(out);check=out/'check';assert not check.exists()
    source=out.with_name('text-boxed-assembly6-20261018')/'check/src/Tests/CertifiedFullUpper6'
    folder=check/'src/Tests/ParametricFullUpper6';folder.mkdir(parents=True)
    old=(source/'Assembly.agda').read_text()
    start=old.index('record CheckedParts : Set where');end=old.index('  complete : CheckedParts')
    declarations=old[start:end].replace('Global.G','G')
    header=old[:start].replace('module Tests.CertifiedFullUpper6.Assembly','module Tests.ParametricFullUpper6.Assembly')
    body=header+'module Generic (G : ℕ → Packed.PackedState) where\n'+textwrap.indent(declarations,'  ')+'''
module Actual = Generic Global.G
abstract
  complete : Actual.CheckedParts → Parts.ProvenMap Global.G
  complete accepted = Parts.finish Global.table Global.fallback Global.fallback-won (Actual.assemble accepted)
-- The654 certified fields are still required. This is conditional closure.
'''
    (folder/'Assembly.agda').write_text(body)
    samples=(source/'Samples.agda').read_text().replace('module Tests.CertifiedFullUpper6.Samples','module Tests.ParametricFullUpper6.Samples')
    (folder/'Samples.agda').write_text(samples)
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        full_state_rows=6530011,reused_owned_rows=20000,additional_boolean_row_checks=0,additional_zip_scans=0,
        G_symbolic_while_checking_all654_field_types=True,actual_G_instantiated_only_after_generic_definition=True,
        initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
