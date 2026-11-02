"""Untrusted fresh sample sources reusing the full map's canonical text names.

No accepted source or interface is rewritten. Row certificates still require
their own safe Agda checks. This changes no game rule or proof premise.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from full_state_map6 import _namespace
from lazy_sample_parts6 import emit
from wire_workflow6 import require


def emit_canonical(check, sample, full, *, side='lower', prefix='Tests.CanonicalSample6'):
    check = Path(check).absolute()
    _namespace(prefix)
    require(not check.exists() and not any(p.is_symlink() for p in (check, *check.parents)),
            'fresh nonsymlink root required; accepted sources and caches cannot be converted')
    require(side == 'lower', 'only the existing complete lower map is supported')
    require(full.get('complete') is True and full.get('rows_per_part') == 200
            and type(full.get('rows')) is int and 0 < full['rows'] <= 8000000
            and full.get('parts') == (full['rows'] + 199) // 200,
            'complete bounded contiguous map required')
    require(sample.get('wire_sha256') == full.get('wire_sha256')
            and isinstance(full.get('wire_sha256'), str) and len(full['wire_sha256']) == 64
            and sample.get('wire_rows') == full['rows'], 'different wire epochs refused')
    chunks = {c['part']: c for c in full['chunks']}
    require(len(chunks) == len(full['chunks']) == full['parts']
            and set(chunks) == set(range(full['parts'])), 'complete unique map chunks required')
    exports = {}
    for j, state in sample['states'].items():
        require(type(j) is int and j in chunks, 'sample state absent from full map')
        desc = chunks[j]
        module = desc['module']
        _namespace(module)
        require(not module.startswith(prefix + '.'), 'self-importing canonical alias refused')
        require(desc['rows'] == state['rows'] == min(200, full['rows'] - 200 * j)
                and hashlib.sha256(state['text'].encode()).hexdigest() == desc['text_sha256'],
                'canonical source must describe the identical state literal')
        exports[j] = module
    generated = emit(check, sample, side=side, prefix=prefix, state_exports=exports)
    generated.update(format='othello-canonical-sample-parts6-v1', canonical_state_exports=exports,
                     agda_checked=False, production_authorized=False,
                     scope='fresh sample only; safe row checking and full-map assembly still required')
    return generated
