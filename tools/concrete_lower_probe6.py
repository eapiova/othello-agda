"""AI-assisted comparison of equivalent generic and closed-instance checkers."""
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
    for rel in ['Othello/ConcreteLowerChecker6.agda', 'Othello/ConcreteLowerRows6.agda']:
        source = prior.ROOT/'src'/rel
        raw = source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe', '--without-K', '--cubical-compatible'])
        target = check/'src'/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        pins[str(source)] = hashlib.sha256(raw).hexdigest()
    donor = prior.ROOT/'results/inline-entries-probe6-20261018/check/src/Tests/InlineProbe6/Variant.agda'
    baseline = donor.read_text().replace('Tests.InlineProbe6.Variant', 'Tests.ConcreteLowerProbe6.Baseline')
    variant = baseline.replace('Tests.ConcreteLowerProbe6.Baseline', 'Tests.ConcreteLowerProbe6.Variant')
    variant = variant.replace('import Othello.InlineRows6 as Rows', 'import Othello.ConcreteLowerRows6 as Check')
    variant = variant.replace('module Check = Rows.Checking white (lowerGoal 4) lowerTransport6\n', '')
    compact = variant.replace('Tests.ConcreteLowerProbe6.Variant', 'Tests.ConcreteLowerProbe6.Compact')
    compact = compact.replace('import Tests.DirectedProbe6.Data as Data', 'import Tests.DirectedProbe6.Data as Data\nimport Tests.UnicodeCodecProbe6.Data as Text\nimport Othello.UnicodeCompact6 as Codec').replace('Data.newBodies', '(Codec.bodies 200 Text.text)')
    folder = check/'src/Tests/ConcreteLowerProbe6'
    folder.mkdir(parents=True)
    for name, body in [('Baseline', baseline), ('Variant', variant), ('Compact', compact)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json', dict(
        format='othello-concrete-lower6-sources-v1', created_utc=utc(), copied_core_sha256=pins,
        generic_checker_source_sha256=hashlib.sha256((prior.ROOT/'src/Game/EncodedResolver.agda').read_bytes()).hexdigest(),
        existing_rows=200, new_distinct_rows=0, native_solver_executed=False,
        full_checker_soundness_retained=True, fixed_lower_instance=True,
        mathematical_objective_complete=False))
    return source_identity(check)
