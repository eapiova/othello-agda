"""AI-assisted fixed-ray count comparison; same existing200-row instance."""
import hashlib
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json,utc


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    pins={}
    for rel in ['Othello/LengthRays6.agda','Othello/LengthRules6.agda','Othello/LengthMoves6.agda','Othello/LengthRows6.agda']:
        source=prior.ROOT/'src'/rel;raw=source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe','--without-K','--cubical-compatible'])
        target=check/'src'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pins[str(source)]=hashlib.sha256(raw).hexdigest()
    old=prior.ROOT/'results/row-packed-probe6-20261018-fixed/check/src/Tests/RowPackedProbe6/Variant.agda'
    baseline=old.read_text().replace('module Tests.RowPackedProbe6.Variant where','module Tests.LengthProbe6.Baseline where')
    variant=baseline.replace('Tests.LengthProbe6.Baseline','Tests.LengthProbe6.Variant')
    variant=variant.replace('import Othello.RowPackedIndexed6 as Rows','import Othello.LengthRows6 as Rows')
    folder=check/'src/Tests/LengthProbe6';folder.mkdir(parents=True)
    for name,body in [('Baseline',baseline),('Variant',variant)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-length-rays6-sources-v1',created_utc=utc(),copied_core_sha256=pins,existing_rows=200,new_distinct_rows=0,native_solver_executed=False,generic_line_cases=728,ordered_game_agreement_required=True,mathematical_objective_complete=False))
    return source_identity(check)
