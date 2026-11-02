"""Bounded two-pass input extraction and source emission; no solver/checker."""
import json
from pathlib import Path
import sys
import hashlib

from big_rows_scaling6 import BUNDLES, emit
from provenance import source_identity
from run_job import atomic_json, utc
from wire_part_samples6 import extract


def main():
    out = Path(sys.argv[1]).resolve()
    request = json.loads((out/'input-request.json').read_text())
    selected = sorted(p for parts in BUNDLES.values() for p in parts)
    assert selected == request['selected_parts'] and not (out/'check').exists()
    if 'reused_verified_sample' in request:
        prior = Path(request['reused_verified_sample'])
        raw = prior.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == request['reused_sample_sha256']
        sample = json.loads(raw)
        assert sample['wire_sha256'] == request['wire_sha256']
        assert sample['wire_rows'] == request['wire_rows'] and sample['selected'] == selected
        assert sample['input_unchanged'] and sample['wire_scans'] == 2
        (out/'sample.json').write_bytes(raw)
    else:
        sample = extract(Path(request['wire']), expected_sha256=request['wire_sha256'],
            expected_rows=request['wire_rows'], selected=selected)
        atomic_json(out/'sample.json', sample)
    # JSON round-trip is also the normalization boundary for integer state keys.
    sample = json.loads((out/'sample.json').read_text())
    emit(out/'check', sample)
    root = Path(__file__).resolve().parents[1]
    (out/'check/othello.agda-lib').write_bytes((root/'othello.agda-lib').read_bytes())
    atomic_json(out/'emission.json', dict(created_utc=utc(), source=source_identity(out/'check'),
        wire_sha256=sample['wire_sha256'], whole_wire_scans=sample['wire_scans'],
        input_unchanged=sample['input_unchanged'], solver_executed=False,
        reused_verified_sample=request.get('reused_verified_sample'),
        additional_wire_scans=0 if 'reused_verified_sample' in request else 2,
        agda_checked=False, mathematical_objective_complete=False))


if __name__ == '__main__':
    main()
