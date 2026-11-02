#!/usr/bin/env python3
"""Pin the actual twenty-root LOWER input and deterministic generated sources."""
import argparse
import json
from pathlib import Path

import assembly6
import lower_pilot6 as pilot
from provenance import digest_entries, source_identity
from run_job import atomic_json, utc


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'provenance', 'selection', 'native-receipt', 'donor', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--agda', required=True)
    args = p.parse_args()
    measurement = json.loads(args.native_receipt.read_text())
    if not all(measurement.get(key) for key in ('accepted', 'source_unchanged', 'expected_source_matches')):
        raise ValueError('native generation did not complete within its recorded limits')
    plan = json.loads(args.plan.read_text())
    native = json.loads(args.provenance.read_text())
    selected = json.loads(args.selection.read_text())
    plan_sha = assembly6.sha(args.plan)
    pilot.validate_provenance(plan, native, plan_sha)
    if (selected.get('status') != 'complete' or selected.get('subsample_seed') != 2026100701 or
            native.get('subsample_seed') != 2026100701 or native.get('source_sample_seed') != 2026100604 or
            native.get('source_population') != 369399 or
            native.get('profile_sha256') != selected.get('trimmed_profile_sha256') or
            [row['state'] for row in selected['selected']] != plan['roots'] or
            [row['native_sha256'] for row in selected['selected']] !=
            [row['native_sha256'] for row in native['cases']]):
        raise ValueError('actual inputs differ from the recorded uniform selection')
    if assembly6.sha(Path(selected['original_profile'])) != selected['original_profile_sha256']:
        raise ValueError('original canonical profile changed')
    for row in selected['selected']:
        if assembly6.sha(Path(row['native_path'])) != row['native_sha256']:
            raise ValueError('selected canonical input changed')
    sources, groups = pilot.generated_sources(plan)
    hashes = pilot.source_hashes(sources)
    identity = source_identity(args.donor)
    interfaces = assembly6.interfaces(args.donor)
    generic = pilot.generic_interfaces(interfaces)
    machine = assembly6.machine_identity(args.agda)
    if (identity['source_sha256'] != 'ecf3b080d1808ee364b102610981e84e3397068159f5dd40caeba07a065097a0' or
            identity['agda_source_sha256'] != '9fde9b4dc22bb602e89ebb3bc1a29a5f56d5d0cdddaffffe5baa08d5d26618ec' or
            digest_entries(interfaces) != 'bea149de03ae625d6f9996d033fc6a65b99a0ae6ef825c5a081d4e799cba4ee1' or
            machine['agda_sha256'] != 'c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842'):
        raise ValueError('recorded desktop donor/compiler changed')
    args.output.mkdir(parents=True, exist_ok=False)
    atomic_json(args.output/'expected-sources.json', dict(files=hashes, sha256=digest_entries(hashes)))
    receipt = dict(format='othello-lower-preflight6-v1', status='complete', created_utc=utc(),
        plan=str(args.plan), plan_sha256=plan_sha, provenance=str(args.provenance),
        provenance_sha256=assembly6.sha(args.provenance), selection_sha256=assembly6.sha(args.selection),
        native_receipt_sha256=assembly6.sha(args.native_receipt),
        donor=str(args.donor), donor_source_sha256=identity['source_sha256'],
        donor_agda_source_sha256=identity['agda_source_sha256'],
        donor_interfaces_sha256=digest_entries(interfaces), agda_path=machine['agda_path'],
        agda_sha256=machine['agda_sha256'], generated_sha256=digest_entries(hashes),
        generated_source_bytes=sum(len(text.encode()) for text in sources.values()),
        private_generic_bytes=sum((args.donor/name).stat().st_size for name in generic),
        groups=groups, modules=len(sources), sample_size=20, threshold=4, direction='lower',
        heldout_groups=[1], kernel_cpu_budget=2200, scalar_replay=True,
        native_stats=native['stats'], expected_sources_sha256=assembly6.sha(args.output/'expected-sources.json'),
        initial_problem2_proved=False, production_authorized=False)
    atomic_json(args.output/'preflight.json', receipt)
    print(json.dumps({key: receipt[key] for key in ('status', 'modules', 'groups',
        'generated_source_bytes', 'private_generic_bytes', 'generated_sha256')}))


if __name__ == '__main__':
    main()
