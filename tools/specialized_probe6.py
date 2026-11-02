"""AI-assisted safe specialization comparison over the same existing 200 rows."""
import hashlib
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json, utc


def emit(check, prefix=''):
    check=Path(check)
    assert not check.exists() and not prefix
    check.mkdir(parents=True)
    pins={}
    for rel in ['Othello/CellRays6.agda','Othello/Specialized6.agda','Othello/AgreedIndexed6.agda']:
        source=prior.ROOT/'src'/rel; raw=source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe','--without-K','--cubical-compatible'])
        target=check/'src'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pins[str(source)]=hashlib.sha256(raw).hexdigest()
    source=prior.ROOT/'results/fused-row-probe6-20261018-fixed/check/src/Tests/FusedRowFixed6/FastChar.agda'
    baseline=source.read_text().replace('Tests.FusedRowFixed6.FastChar','Tests.SpecializedProbe6.Baseline')
    variant=baseline.replace('Tests.SpecializedProbe6.Baseline','Tests.SpecializedProbe6.Variant')
    variant=variant.replace('import Othello.IncrementalIndexed6 as Faster', 'import Othello.AgreedIndexed6 as Agreed\nimport Othello.Specialized6 as New\nmodule Faster = Agreed.With New.specializedGame6 New.agreement')
    folder=check/'src/Tests/SpecializedProbe6';folder.mkdir(parents=True)
    (folder/'Baseline.agda').write_text(baseline)
    (folder/'Variant.agda').write_text(variant)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-specialized-rule6-sources-v1',created_utc=utc(),copied_core_sha256=pins,source_part=33154,conditional_existing_rows_per_variant=200,new_distinct_rows=0,arbitrary_board_agreement_required=True,mathematical_objective_complete=False))
    return source_identity(check)
