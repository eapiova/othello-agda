"""Same directed row instance with old and proved direct D4 actions."""
import hashlib
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json, utc


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    source=prior.ROOT/'src/Othello/DirectSymmetry6.agda';raw=source.read_bytes()
    target=check/'src/Othello/DirectSymmetry6.agda';target.parent.mkdir(parents=True);target.write_bytes(raw)
    previous=prior.ROOT/'results/directed-move-probe6-20261018-fixed/check/src/Tests/DirectedProbe6/Variant.agda'
    baseline=previous.read_text().replace('module Tests.DirectedProbe6.Variant where','module Tests.DirectSymmetryProbe6.Baseline where')
    variant=baseline.replace('Tests.DirectSymmetryProbe6.Baseline','Tests.DirectSymmetryProbe6.Variant').replace('open import Othello.SharedSymmetry6 using (lowerTransport6)','open import Othello.DirectSymmetry6 using (lowerTransport6)')
    folder=check/'src/Tests/DirectSymmetryProbe6';folder.mkdir(parents=True)
    (folder/'Baseline.agda').write_text(baseline);(folder/'Variant.agda').write_text(variant)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-direct-symmetry6-sources-v1',created_utc=utc(),copied_core_sha256={str(source):hashlib.sha256(raw).hexdigest()},existing_rows=200,new_distinct_rows=0,changed_only_d4_action=True,mathematical_objective_complete=False))
    return source_identity(check)
