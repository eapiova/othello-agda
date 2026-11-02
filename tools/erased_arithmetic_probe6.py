"""AI-assisted irrelevant-witness comparison on the same accepted200 rows."""
import hashlib
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json, utc


def emit(check):
    check = Path(check)
    assert not check.exists()
    check.mkdir(parents=True)
    pins = {}
    for rel in ['Game/BooleanRecompute.agda', 'Othello/ErasedArithmeticState6.agda',
                'Othello/ErasedArithmeticGame6.agda', 'Othello/ErasedArithmeticRows6.agda']:
        source = prior.ROOT/'src'/rel
        raw = source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe', '--without-K', '--cubical-compatible'])
        target = check/'src'/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        pins[str(source)] = hashlib.sha256(raw).hexdigest()
    donor = prior.ROOT/'results/arithmetic-evaluation-probe6-20261018/check/src/Tests/ArithmeticGameProbe6'
    baseline = (donor/'Variant.agda').read_text().replace('module Tests.ArithmeticGameProbe6.Variant where', 'module Tests.ErasedArithmeticProbe6.Baseline where')
    variant = baseline.replace('Tests.ErasedArithmeticProbe6.Baseline', 'Tests.ErasedArithmeticProbe6.Variant')
    variant = variant.replace('Othello.ArithmeticRows6', 'Othello.ErasedArithmeticRows6').replace('Othello.ArithmeticState6', 'Othello.ErasedArithmeticState6')
    variant = variant.replace('Tests.ArithmeticGameProbe6.RefData', 'Tests.ErasedArithmeticProbe6.RefData')
    refs = (donor/'RefData.agda').read_text().replace('Tests.ArithmeticGameProbe6.RefData', 'Tests.ErasedArithmeticProbe6.RefData').replace('Othello.ArithmeticState6', 'Othello.ErasedArithmeticState6')
    folder = check/'src/Tests/ErasedArithmeticProbe6'
    folder.mkdir(parents=True)
    for name, body in [('RefData', refs), ('Baseline', baseline), ('Variant', variant)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json', dict(
        format='othello-erased-arithmetic6-sources-v1', created_utc=utc(), copied_core_sha256=pins,
        existing_rows=200, new_distinct_rows=0, native_solver_executed=False,
        canonical_witness_irrelevant=True, relevant_equality_recomputed_constructively=True,
        unsafe_irrelevance_flags=False, mathematical_objective_complete=False))
    return source_identity(check)
