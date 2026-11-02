#!/usr/bin/env python3
"""Record a seeded lower sample without copying embedded certificate payloads."""
import argparse
import hashlib
import json
from pathlib import Path

import assembly6
from global_shared6 import select_cases
from run_job import atomic_json, utc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--declaration-sha256', required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args()
    raw = args.profile.read_bytes()
    original_hash = hashlib.sha256(raw).hexdigest()
    profile = json.loads(raw)
    rows = profile['cases']
    if (len(rows) != 120 or profile.get('sample_population_kind') !=
            'canonical frontier full-state classes'):
        raise ValueError('requires the recorded full canonical 120 lower sample')
    minimal = {name: profile.get(name) for name in
        ('format', 'sample_seed', 'sample_population_L', 'sample_population_kind')}
    minimal['cases'] = []
    for case in rows:
        if (case.get('direction') != 'lower' or case.get('frontier_discs') != 36 or
                case.get('status') != 'complete' or case['row'].get('value') != 4):
            raise ValueError('do not discard a censored or different-bound case')
        path = Path(case['native_path'])
        if not path.is_absolute():
            path = args.profile.parent/path
        if not path.is_file() or path.is_symlink():
            raise ValueError('canonical native input is absent or redirected')
        minimal['cases'].append(dict(row={name: case['row'].get(name) for name in
            ('id', 'state', 'value', 'empties', 'split')},
            direction=case['direction'], frontier_discs=case['frontier_discs'],
            status=case['status'], native_path=str(path)))
    chosen = select_cases(profile, 20, args.seed, 'lower')
    reduced = select_cases(minimal, 20, args.seed, 'lower')
    if [case['row']['state'] for case in chosen] != [case['row']['state'] for case in reduced]:
        raise ValueError('trimming changed the sampling population/order')
    args.output.mkdir(parents=True, exist_ok=False)
    minimal.update(original_profile=str(args.profile), original_profile_sha256=original_hash,
        original_profile_bytes=len(raw), selection_preserved=True,
        declaration_sha256=args.declaration_sha256)
    atomic_json(args.output/'profile.json', minimal)
    selected = []
    for case in reduced:
        path = Path(case['native_path'])
        selected.append(dict(id=case['row']['id'], state=case['row']['state'],
            native_path=str(path), native_bytes=path.stat().st_size,
            native_sha256=assembly6.sha(path)))
    if assembly6.sha(args.profile) != original_hash:
        raise ValueError('original canonical profile changed during preparation')
    receipt = dict(format='othello-lower-prepare6-v1', status='complete', selected_utc=utc(),
        original_profile=str(args.profile), original_profile_sha256=original_hash,
        original_profile_bytes=len(raw), trimmed_profile_sha256=assembly6.sha(args.output/'profile.json'),
        source_sample_seed=profile.get('sample_seed'), population=profile.get('sample_population_L'),
        population_kind=profile['sample_population_kind'], source_cases=120,
        selected_cases=20, subsample_seed=args.seed, selected=selected,
        group_size=10, heldout_groups=[1], declaration_sha256=args.declaration_sha256,
        selection_identical_to_full_profile=True, canonical_inputs_unchanged=True,
        largest_native_bytes=max(case['native_bytes'] for case in selected),
        total_native_bytes=sum(case['native_bytes'] for case in selected),
        initial_problem2_proved=False, production_authorized=False)
    atomic_json(args.output/'selection.json', receipt)
    print(json.dumps({key: receipt[key] for key in ('status', 'selected_cases', 'population',
        'original_profile_sha256', 'trimmed_profile_sha256', 'largest_native_bytes', 'total_native_bytes')}))


if __name__ == '__main__':
    main()
