"""AI-assisted repacking experiment; existing rows only, no solver claims."""
import hashlib
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json,utc


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    pins={}
    for rel in ['Othello/PackedGame6.agda','Othello/PackedRows6.agda']:
        source=prior.ROOT/'src'/rel;raw=source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe','--without-K','--cubical-compatible'])
        target=check/'src'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pins[str(source)]=hashlib.sha256(raw).hexdigest()
    old=prior.ROOT/'results/row-packed-probe6-20261018-fixed/check/src/Tests/RowPackedProbe6/Variant.agda'
    baseline=old.read_text().replace('module Tests.RowPackedProbe6.Variant where','module Tests.PackedGameProbe6.Baseline where')
    variant=baseline.replace('Tests.PackedGameProbe6.Baseline','Tests.PackedGameProbe6.Variant')
    variant=variant.replace('import Othello.RowPackedIndexed6 as Rows','import Othello.PackedRows6 as Rows')
    variant=variant.replace('ss : B.Vec (State six) 200\nss = Lazy.states 200 Own.text','''packVec : ∀ {n} → B.Vec (State six) n → B.Vec Packed.PackedState n
packVec B.nil = B.nil
packVec (B.cons s ss) = B.cons (Packed.encode s) (packVec ss)
ss : B.Vec Packed.PackedState 200
ss = packVec (Lazy.states 200 Own.text)''')
    variant=variant.replace('Check.V.Old.TreeOK (λ j → Packed.decode (G j))','Check.V.TreeOK G')
    folder=check/'src/Tests/PackedGameProbe6';folder.mkdir(parents=True)
    for name,body in [('Baseline',baseline),('Variant',variant)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-packed-game6-sources-v1',created_utc=utc(),copied_core_sha256=pins,existing_rows=200,new_distinct_rows=0,native_solver_executed=False,working_states_are_six_nat_codes=True,arbitrary_state_refinement_required=True,mathematical_objective_complete=False))
    return source_identity(check)
