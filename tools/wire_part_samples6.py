#!/usr/bin/env python3
"""UNTRUSTED bounded samples from an existing full child-first wire.

Two streaming scans replace a full graph/state dictionary. Only reference keys
used by the selected parts are indexed. The result has the existing sampler's
``cases``/``states`` interface; safe Agda must still check every new game row.
This module never runs the native solver or Agda and never modifies its input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import stat

from compact_shared6 import TRIPLES
from full_state_map6 import MAX_RECORD_BYTES, MAX_ROWS, ROWS_PER_PART
from native_layout_samples6 import convert_body
from wire_workflow6 import require

MAX_PARTS = 16
MAX_SAMPLE_BYTES = 32 * 2**20
MAX_REFERENCE_OCCURRENCES = MAX_PARTS * 32000
MAX_WIRE_BYTES = 512 * 2**20
ALPHABET = frozenset(TRIPLES.encode())


def _fingerprint(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def _state(raw):
    require(len(raw) == 13 and raw[:1] in (b'b', b'w')
            and all(c in ALPHABET for c in raw[1:]), 'invalid compact state')


def _records(path, expected_sha256, expected_rows, identity):
    """Every scan authenticates the entire file, including unselected rows."""
    h = hashlib.sha256()
    count = 0
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and _fingerprint(before) == identity,
                'wire identity changed before scan')
        while True:
            raw = stream.readline(MAX_RECORD_BYTES + 1)
            if not raw:
                break
            require(len(raw) <= MAX_RECORD_BYTES and raw.endswith(b'\n'),
                    'truncated or oversized wire record')
            h.update(raw)
            fields = raw[:-1].split(b'\t')
            require(len(fields) == 3, 'exactly three wire fields required')
            state, body, refs = fields
            _state(state)
            require(len(refs) % 13 == 0, 'invalid reference field length')
            require(count < expected_rows, 'extra wire rows')
            yield count, state, body, refs
            count += 1
        require(_fingerprint(os.fstat(stream.fileno())) == identity,
                'wire changed during scan')
    require(_fingerprint(path.stat()) == identity and not path.is_symlink(),
            'wire path changed during scan')
    require(count == expected_rows and h.hexdigest() == expected_sha256,
            'whole-wire row count or SHA256 mismatch')


def selection(parts, excluded, *, seed=2026101601, count=8):
    """Freeze disjoint strata before extracting data or observing timings."""
    require(type(parts) is int and 1 <= parts <= 40000, 'bounded part count required')
    require(type(count) is int and 2 <= count <= MAX_PARTS and count % 2 == 0
            and count <= parts, 'even bounded sample count required')
    require(type(seed) is int and isinstance(excluded, (list, tuple))
            and all(type(j) is int and 0 <= j < parts for j in excluded)
            and len(set(excluded)) == len(excluded), 'distinct bounded exclusions required')
    rng = random.Random(seed)
    denied = set(excluded)
    selected = []
    for k in range(count):
        candidates = [j for j in range(k * parts // count, (k + 1) * parts // count)
                      if j not in denied]
        require(candidates, 'an entire sample stratum was already checked')
        selected.append(rng.choice(candidates))
    return dict(seed=seed, selected=selected, training=selected[::2], held_out=selected[1::2],
                excluded=sorted(excluded), cost_forecast_frozen=False,
                held_out_kernel_checks_started=False)


def extract(wire, *, expected_sha256, expected_rows, selected,
            max_sample_bytes=MAX_SAMPLE_BYTES,
            max_reference_occurrences=MAX_REFERENCE_OCCURRENCES,
            max_unique_references=MAX_REFERENCE_OCCURRENCES,
            max_selected_parts=MAX_PARTS):
    require(isinstance(expected_sha256, str) and re.fullmatch('[0-9a-f]{64}', expected_sha256),
            'pinned whole-wire SHA256 required')
    require(type(expected_rows) is int and 1 <= expected_rows <= MAX_ROWS,
            'bounded row count required')
    parts = (expected_rows + ROWS_PER_PART - 1) // ROWS_PER_PART
    require(type(max_selected_parts) is int and 1 <= max_selected_parts <= 64,
            'explicit bounded selected-part limit required')
    require(isinstance(selected, (list, tuple)) and 1 <= len(selected) <= max_selected_parts
            and all(type(j) is int and 0 <= j < parts for j in selected)
            and list(selected) == sorted(set(selected)), 'sorted distinct bounded part IDs required')
    require(type(max_sample_bytes) is int and 1 <= max_sample_bytes <= MAX_SAMPLE_BYTES,
            'bounded sample output required')
    require(type(max_reference_occurrences) is int and type(max_unique_references) is int
            and 1 <= max_unique_references <= max_reference_occurrences <= MAX_REFERENCE_OCCURRENCES,
            'bounded reference index required')
    path = Path(wire).absolute()
    require(path == path.resolve() and not any(p.is_symlink() for p in (path, *path.parents)),
            'real nonsymlink wire path required')
    st = path.stat()
    require(stat.S_ISREG(st.st_mode) and 0 < st.st_size <= MAX_WIRE_BYTES,
            'bounded regular wire required')
    identity = _fingerprint(st)
    rows = {j: [] for j in selected}
    totals = {j: 0 for j in selected}
    wanted = set()
    retained_bytes = occurrences = 0
    for rank, state, body, refs in _records(path, expected_sha256, expected_rows, identity):
        j = rank // ROWS_PER_PART
        if j not in rows:
            continue
        retained_bytes += len(state) + len(body) + len(refs) + 3
        require(retained_bytes <= max_sample_bytes, 'selected wire byte cap reached')
        references = [refs[k:k + 13] for k in range(0, len(refs), 13)]
        for key in references:
            _state(key)
        occurrences += len(references)
        require(occurrences <= max_reference_occurrences, 'reference occurrence cap reached')
        wanted.update(references)
        require(len(wanted) <= max_unique_references, 'unique reference index cap reached')
        try:
            raw_body = body.decode('ascii')
        except UnicodeDecodeError as error:
            raise ValueError('non-ASCII selected body') from error
        # Syntax validation only. These placeholder IDs never enter the result.
        _, tokens = convert_body(raw_body, [0] * len(references))
        totals[j] += tokens
        require(totals[j] <= 32000, 'selected part token cap reached')
        rows[j].append((rank, state.decode('ascii'), raw_body, references))

    needed = set(selected)
    found = {}
    states = {}
    buffer = []
    for rank, state, _, _ in _records(path, expected_sha256, expected_rows, identity):
        j = rank // ROWS_PER_PART
        buffer.append(state.decode('ascii'))
        if state in wanted:
            require(state not in found, 'ambiguous duplicate referenced state')
            found[state] = rank
            needed.add(j)
        if len(buffer) == ROWS_PER_PART or rank + 1 == expected_rows:
            if j in needed:
                states[j] = dict(rows=len(buffer), text=''.join(buffer))
            buffer = []
    require(found.keys() == wanted, 'reference state absent from full wire')
    require(len(states) <= 8192 and states.keys() == needed, 'demanded state chunk cap reached')
    cases = []
    for j, part in rows.items():
        n = min(ROWS_PER_PART, expected_rows - ROWS_PER_PART * j)
        require(len(part) == n, 'incomplete selected part')
        numeric = []
        references = []
        for rank, own, body, keys in part:
            ids = [found[key] for key in keys]
            require(all(i < rank for i in ids), 'non-earlier citation refused')
            converted, _ = convert_body(body, ids)
            numeric.append(converted)
            references.extend(ids)
            require(own == states[j]['text'][13 * (rank % 200):13 * (rank % 200 + 1)],
                    'own state differs between scans')
        cases.append(dict(part=j, rows=n, state_text=states[j]['text'],
                          body_text=''.join(numeric), references=references,
                          dependencies=sorted({j} | {i // ROWS_PER_PART for i in references}),
                          tokens=totals[j]))
    result = dict(format='othello-wire-part-samples6-v1', cases=cases, states=states,
                  wire_sha256=expected_sha256, wire_rows=expected_rows, wire_bytes=st.st_size,
                  wire_scans=2, input_unchanged=True, selected=list(selected),
                  indexed_reference_states=len(found), reference_occurrences=occurrences,
                  whole_graph_index_retained=False, agda_checked=False,
                  initial_problem2_proved=False, optimal_initial_pair_proved=False,
                  production_authorized=False)
    require(len(json.dumps(result).encode()) <= max_sample_bytes, 'encoded sample byte cap reached')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wire', required=True, type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--rows', required=True, type=int)
    parser.add_argument('--parts', required=True, help='sorted comma-separated NEW part IDs')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--emit-check', type=Path)
    parser.add_argument('--prefix', default='Tests.WireLowerSample6')
    args = parser.parse_args()
    require(re.fullmatch(r'[0-9]+(?:,[0-9]+){0,15}', args.parts), 'bounded selected part list required')
    require(not args.output.exists() and 'results' in args.output.absolute().parts
            and not any(p.is_symlink() for p in (args.output.absolute(), *args.output.absolute().parents)),
            'fresh private sample output required')
    if args.emit_check is not None:
        require(not args.emit_check.exists() and 'results' in args.emit_check.absolute().parts
                and not any(p.is_symlink() for p in (args.emit_check.absolute(), *args.emit_check.absolute().parents)),
                'fresh private generated-source root required')
    result = extract(args.wire, expected_sha256=args.sha256, expected_rows=args.rows,
                     selected=[int(j) for j in args.parts.split(',')])
    if args.emit_check is not None:
        from lazy_sample_parts6 import emit
        result['generated'] = emit(args.emit_check, result, side='lower', prefix=args.prefix)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(complete=True, selected=result['selected'], scans=2,
                         indexed_reference_states=result['indexed_reference_states'],
                         game_rows_checked=0, production_authorized=False)))


if __name__ == '__main__':
    main()
