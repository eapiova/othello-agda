"""AI-assisted strict-field comparison, same 200 accepted rows."""
import hashlib
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json,utc


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    pins={}
    for rel in ['Othello/StrictPacked6.agda','Othello/StrictPackedGame6.agda','Othello/StrictPackedRows6.agda','Othello/StrictBoard6.agda','Othello/StrictBoardRows6.agda']:
        source=prior.ROOT/'src'/rel;raw=source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe','--without-K','--cubical-compatible'])
        target=check/'src'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pins[str(source)]=hashlib.sha256(raw).hexdigest()
    old=prior.ROOT/'results/packed-game-probe6-20261018/check/src/Tests/PackedGameProbe6/Variant.agda'
    baseline=old.read_text().replace('module Tests.PackedGameProbe6.Variant where','module Tests.StrictPackedProbe6.Baseline where')
    variant=baseline.replace('Tests.StrictPackedProbe6.Baseline','Tests.StrictPackedProbe6.Variant')
    variant=variant.replace('import Othello.PackedRows6 as Rows','import Othello.StrictPackedRows6 as Rows')
    old=prior.ROOT/'results/row-packed-probe6-20261018-fixed/check/src/Tests/RowPackedProbe6/Variant.agda'
    hybrid=old.read_text().replace('module Tests.RowPackedProbe6.Variant where','module Tests.StrictPackedProbe6.Hybrid where')
    board=hybrid.replace('Tests.StrictPackedProbe6.Hybrid','Tests.StrictPackedProbe6.BoardVariant').replace('import Othello.RowPackedIndexed6 as Rows','import Othello.StrictBoardRows6 as Rows')
    folder=check/'src/Tests/StrictPackedProbe6';folder.mkdir(parents=True)
    for name,body in [('Hybrid',hybrid),('Baseline',baseline),('Variant',variant),('BoardVariant',board)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-strict-packed6-sources-v1',created_utc=utc(),copied_core_sha256=pins,existing_rows=200,new_distinct_rows=0,native_solver_executed=False,agda_builtin_strict_primitive=True,forcing_identity_required=True,mathematical_objective_complete=False))
    return source_identity(check)
