"""AI-assisted hybrid row-code cache comparison; no new game rows."""
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
    for rel in ['Othello/CachedRow6.agda', 'Othello/RowCacheState6.agda', 'Othello/RowCacheGame6.agda', 'Othello/RowCacheRows6.agda']:
        source = prior.ROOT/'src'/rel
        raw = source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe', '--without-K', '--cubical-compatible'])
        target = check/'src'/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        pins[str(source)] = hashlib.sha256(raw).hexdigest()
    donor = prior.ROOT/'results/inline-entries-probe6-20261018/check/src/Tests/InlineProbe6/Variant.agda'
    baseline = donor.read_text().replace('module Tests.InlineProbe6.Variant where', 'module Tests.RowCacheProbe6.Baseline where')
    variant = baseline.replace('Tests.RowCacheProbe6.Baseline', 'Tests.RowCacheProbe6.Variant').replace('Othello.InlineRows6', 'Othello.RowCacheRows6')
    variant = variant.replace('import Othello.RowPacked6 as Packed', 'import Othello.RowPacked6 as Packed\nimport Othello.RowCacheState6 as Cache')
    variant = variant.replace('ss : B.Vec (State six) 200\nss = Lazy.states 200 Own.text', '''packVec : ∀ {n} → B.Vec (State six) n → B.Vec Cache.CachedState n
packVec B.nil = B.nil
packVec (B.cons s ss) = B.cons (Cache.pack s) (packVec ss)
ss : B.Vec Cache.CachedState 200
ss = packVec (Lazy.states 200 Own.text)''')
    variant = variant.replace('λ j → Packed.decode (G j)', 'λ j → Rows.decode (G j)')
    compact = variant.replace('Tests.RowCacheProbe6.Variant', 'Tests.RowCacheProbe6.Compact')
    compact = compact.replace('import Tests.DirectedProbe6.Data as Data', 'import Tests.DirectedProbe6.Data as Data\nimport Tests.UnicodeCodecProbe6.Data as Text\nimport Othello.UnicodeCompact6 as Codec').replace('Data.newBodies', '(Codec.bodies 200 Text.text)')
    folder = check/'src/Tests/RowCacheProbe6'
    folder.mkdir(parents=True)
    for name, body in [('Baseline', baseline), ('Variant', variant), ('Compact', compact)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json', dict(
        format='othello-row-cache6-sources-v1', created_utc=utc(), copied_core_sha256=pins,
        existing_rows=200, new_distinct_rows=0, native_solver_executed=False,
        cached_row_codes=True, exact_ordered_moves_and_pass_refinement_required=True,
        mathematical_objective_complete=False))
    return source_identity(check)
