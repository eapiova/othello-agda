"""AI-assisted exact-entry inlining comparison; same accepted200 rows."""
import hashlib
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json,utc


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    pins={}
    for rel in ['Othello/InlineEntries6.agda','Othello/InlineRows6.agda']:
        source=prior.ROOT/'src'/rel;raw=source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe','--without-K','--cubical-compatible'])
        target=check/'src'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pins[str(source)]=hashlib.sha256(raw).hexdigest()
    old=prior.ROOT/'results/length-rays-probe6-20261018/check/src/Tests/LengthProbe6/Variant.agda'
    baseline=old.read_text().replace('module Tests.LengthProbe6.Variant where','module Tests.InlineProbe6.Baseline where')
    variant=baseline.replace('Tests.InlineProbe6.Baseline','Tests.InlineProbe6.Variant').replace('import Othello.LengthRows6 as Rows','import Othello.InlineRows6 as Rows')
    compact=variant.replace('Tests.InlineProbe6.Variant','Tests.InlineProbe6.Compact')
    compact=compact.replace('import Tests.DirectedProbe6.Data as Data','import Tests.DirectedProbe6.Data as Data\nimport Tests.UnicodeCodecProbe6.Data as Text\nimport Othello.UnicodeCompact6 as Codec').replace('Data.newBodies','(Codec.bodies 200 Text.text)')
    folder=check/'src/Tests/InlineProbe6';folder.mkdir(parents=True)
    for name,body in [('Baseline',baseline),('Variant',variant),('Compact',compact)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-inline-entries6-sources-v1',created_utc=utc(),copied_core_sha256=pins,existing_rows=200,new_distinct_rows=0,native_solver_executed=False,exact_entry_equality_required=True,mathematical_objective_complete=False))
    return source_identity(check)
