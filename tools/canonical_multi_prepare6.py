#!/usr/bin/env python3
"""Bounded OFFLINE canonical row/bridge preparation; never runs a checker.

Input pins identify retained data, not permission to run it. The joint module
only imports the per-part bridge roots. Their separate certificate maps are
not a combined body map and imply no initial-board coverage theorem.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

from canonical_sample_parts6 import emit_canonical
from compact_shared6 import TRIPLES
from full_state_map6 import _namespace
from new_row_bridge6 import HEADER, emit as emit_bridge
from wire_workflow6 import require


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _pinned_json(path, expected, cap):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)) and path.is_file(),
            'regular nonsymlink input required')
    require(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected),
            'exact caller-supplied input SHA256 required')
    require(path.stat().st_size <= cap, 'bounded input required')
    raw = path.read_bytes()
    require(len(raw) <= cap and _sha(raw) == expected, 'retained input SHA256 differs')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON field refused')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def prepare(sample_path, full_path, *, parts, output, prefix='Tests.CanonicalMulti6',
            expected_sample_sha256, expected_full_sha256):
    """Prepare fresh per-part layouts plus an import-only joint target.

    At most sixteen positive parts are selected. All emitters validate in a
    temporary staging root before the requested output is created. No accepted
    source, cache, donor, receipt, authorization, or budget ledger is changed.
    """
    require(isinstance(parts, (list, tuple)) and 1 <= len(parts) <= 16
            and all(type(j) is int and 0 < j < 40000 for j in parts)
            and len(set(parts)) == len(parts), 'unique bounded positive part set required')
    parts = sorted(parts)
    _namespace(prefix)
    # Leave room for the existing row emitter's stricter namespace bounds.
    require(len(prefix) <= 140 and len(prefix.split('.')) <= 8,
            'bounded namespace with room for per-part suffixes required')
    output = Path(output).absolute()
    require(not output.exists() and not any(p.is_symlink() for p in (output, *output.parents)),
            'fresh nonsymlink output required')
    sample = _pinned_json(sample_path, expected_sample_sha256, 128 * 2**20)
    full = _pinned_json(full_path, expected_full_sha256, 64 * 2**20)
    _namespace(full['prefix'])
    require(full.get('complete') is True and full.get('rows_per_part') == 200
            and type(full.get('rows')) is int and 0 < full['rows'] <= 8000000
            and type(full.get('parts')) is int and full['parts'] == (full['rows'] + 199)//200,
            'complete bounded contiguous full map required')
    require(isinstance(full.get('wire_sha256'), str)
            and re.fullmatch('[0-9a-f]{64}', full['wire_sha256'])
            and sample.get('wire_sha256') == full['wire_sha256']
            and type(sample.get('wire_rows')) is int and sample['wire_rows'] == full['rows'],
            'retained wire identity differs')
    require(isinstance(full.get('chunks'), list) and len(full['chunks']) == full['parts'],
            'complete full chunk manifest required')
    chunks = {}
    modules = set()
    for desc in full['chunks']:
        j = desc['part']
        require(type(j) is int and 0 <= j < full['parts'] and j not in chunks
                and type(desc['rows']) is int
                and desc['rows'] == min(200, full['rows'] - 200*j),
                'full chunk index or row count differs')
        module = _namespace(desc['module'])
        require(module not in modules and not module.startswith(prefix + '.')
                and module != prefix and full['prefix'] != prefix
                and not full['prefix'].startswith(prefix + '.'),
                'distinct safe canonical module namespaces required')
        require(isinstance(desc.get('text_sha256'), str)
                and re.fullmatch('[0-9a-f]{64}', desc['text_sha256']),
                'exact full chunk text hash required')
        chunks[j] = desc
        modules.add(module)
    require(set(chunks) == set(range(full['parts'])), 'missing full map part')
    require(isinstance(sample.get('states'), dict) and 0 < len(sample['states']) <= 8192,
            'bounded retained states required')
    states = {}
    for key, state in sample['states'].items():
        require(isinstance(key, str) and re.fullmatch('0|[1-9][0-9]*', key),
                'canonical numeric state key required')
        j = int(key)
        require(j in chunks and type(state['rows']) is int
                and state['rows'] == chunks[j]['rows']
                and isinstance(state['text'], str) and len(state['text']) == 13*state['rows']
                and _sha(state['text'].encode()) == chunks[j]['text_sha256'],
                'retained state literal differs from full manifest')
        text = state['text']
        require(all(text[i] in 'bw' and all(c in TRIPLES for c in text[i+1:i+13])
                    for i in range(0, len(text), 13)), 'unsafe compact state literal')
        states[j] = state
    require(isinstance(sample.get('cases'), list) and 1 <= len(sample['cases']) <= 16,
            'bounded retained cases required')
    cases = {}
    for case in sample['cases']:
        j = case['part']
        require(type(j) is int and j in states and j not in cases
                and type(case['rows']) is int and case['rows'] == chunks[j]['rows'],
                'duplicate or inconsistent retained case')
        cases[j] = case
    require(set(parts) <= cases.keys(), 'requested part missing from retained sample')
    if 'selected' in sample:
        require(sample['selected'] == sorted(cases), 'retained selection differs from cases')
    sample['states'] = states
    layouts = []
    library = (Path(__file__).resolve().parents[1]/'othello.agda-lib').read_bytes()
    # A literal results directory also satisfies the bridge emitter's private-root gate.
    with tempfile.TemporaryDirectory(prefix='canonical-multi-prepare6-') as temporary:
        # Validate the entire pinned retained sample, including unselected cases,
        # against the same canonical emitter before constructing selected layouts.
        validation = Path(temporary)/'validation'
        emit_canonical(validation, sample, full, prefix=prefix + '.Validation')
        shutil.rmtree(validation)
        stage = Path(temporary)/'results'
        for j in parts:
            case = cases[j]
            ds = case['dependencies']
            require(isinstance(ds, list) and all(type(d) is int for d in ds)
                    and ds == sorted(set(ds)) and set(ds) <= states.keys(),
                    'sorted existing state demands required')
            subset = copy.deepcopy(sample)
            subset.update(cases=[case], states={d: states[d] for d in ds}, selected=[j])
            row_prefix = prefix + '.Rows' + str(j)
            bridge_prefix = prefix + '.Bridge' + str(j)
            row_root = Path('parts')/str(j)/'rows'
            bridge_root = Path('parts')/str(j)/'bridge'
            rows = emit_canonical(stage/row_root, subset, full, prefix=row_prefix)
            (stage/row_root/'othello.agda-lib').write_bytes(library)
            bridge = emit_bridge(stage/bridge_root, full, subset, part=j,
                                 row_prefix=row_prefix, prefix=bridge_prefix,
                                 state_exports=rows['canonical_state_exports'])
            layouts.append(dict(part=j, rows=case['rows'], row_root=row_root.as_posix(),
                bridge_root=bridge_root.as_posix(), row_layout=rows, bridge_layout=bridge,
                features=dict(reference_occurrences=len(case['references']),
                    distinct_references=len(set(case['references'])),
                    state_dependencies=len(ds), body_bytes=len(case['body_text'].encode()),
                    tokens=case['tokens'])))
        joint_module = prefix + '.Joint'
        relative = 'joint/src/' + joint_module.replace('.', '/') + '.agda'
        raw = (HEADER + '-- AI-assisted OFFLINE import target; no combined body-map theorem.\n'
               + 'module ' + joint_module + ' where\n\n'
               + ''.join(f'import {prefix}.Bridge{j}.Root as Part{j}\n' for j in parts)).encode()
        target = stage/relative
        target.parent.mkdir(parents=True)
        target.write_bytes(raw)
        (stage/'joint/othello.agda-lib').write_bytes(library)
        sources = {p.relative_to(stage).as_posix(): _sha(p.read_bytes())
                   for p in sorted(stage.rglob('*')) if p.is_file()}
        helper_names = ['canonical_multi_prepare6.py', 'canonical_sample_parts6.py',
                        'lazy_sample_parts6.py', 'new_row_bridge6.py']
        manifest = dict(format='othello-canonical-multi-prepare6-v1', parts=parts,
            wire_sha256=full['wire_sha256'], wire_rows=full['rows'], full_parts=full['parts'],
            sample_sha256=expected_sample_sha256, full_manifest_sha256=expected_full_sha256,
            helper_sha256={n: _sha(Path(__file__).with_name(n).read_bytes()) for n in helper_names},
            prefix=prefix, layouts=layouts, selected_rows=sum(cases[j]['rows'] for j in parts),
            retained_cases=len(cases), retained_state_chunks=len(states),
            distinct_demanded_state_chunks=len({d for j in parts for d in cases[j]['dependencies']}),
            joint_root='joint', joint_module=joint_module, joint_target=relative,
            generated_sha256=sources, generated_files=len(sources),
            generated_bytes=sum(p.stat().st_size for p in stage.rglob('*') if p.is_file()),
            agda_checked=False, partial_only=True, joint_target_is_import_only=True,
            combined_body_map_coverage_proved=False, initial_problem2_proved=False,
            optimal_initial_pair_proved=False, production_authorized=False,
            scope='offline preparation only; each bridge has a separate body map; '
                  'joint imports prove no combined or initial coverage')
        (stage/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
        require(not output.exists() and not any(p.is_symlink() for p in (output, *output.parents)),
                'fresh nonsymlink output required')
        output.mkdir(parents=True, exist_ok=False)
        shutil.copytree(stage, output, dirs_exist_ok=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', required=True, type=Path)
    parser.add_argument('--full', required=True, type=Path)
    parser.add_argument('--parts', required=True, nargs='+', type=int)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--prefix', default='Tests.CanonicalMulti6')
    parser.add_argument('--sample-sha256', required=True)
    parser.add_argument('--full-sha256', required=True)
    args = parser.parse_args()
    result = prepare(args.sample, args.full, parts=args.parts, output=args.output,
                     prefix=args.prefix, expected_sample_sha256=args.sample_sha256,
                     expected_full_sha256=args.full_sha256)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
