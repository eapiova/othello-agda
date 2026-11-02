"""Profile the already accepted directed/D4 row judgment in a fresh own module."""
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    source=prior.ROOT/'results/direct-symmetry-probe6-20261018/check/src/Tests/DirectSymmetryProbe6/Variant.agda'
    text=source.read_text().replace('module Tests.DirectSymmetryProbe6.Variant where','module Tests.CheckerProfile6.Root where')
    target=check/'src/Tests/CheckerProfile6/Root.agda';target.parent.mkdir(parents=True);target.write_text(text)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    return source_identity(check)
