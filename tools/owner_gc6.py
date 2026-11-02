#!/usr/bin/env python3
"""One bounded GC-frequency probe on the same failed citation sources/caps.

Only GHC runtime collection settings change. The compiler, interfaces, source
obligations, heap maximum, RSS stop and safe options remain identical.
"""
import argparse
import json
from pathlib import Path

import assembly6
import owner_capsule_full6 as full
import owner_cuts6 as cuts
import owner_single6 as single
from run_job import positive


def verified_prefix(args, original_pool, machine, sources):
    previous = args.failed_donor.resolve()
    r, root, identity, pool = full.checkpoint(previous, args.expected_failed_sha256, machine)
    if (r['format'] != 'othello-owner-single6-v1' or r['status'] != 'phase-failed' or r['accepted'] or
            [p['label'] for p in r['phases']] != ['Citations'] or
            r['phases'][0]['expected_outcome_met'] or r['phases'][0]['record']['exit_code'] != 251 or
            r['phases'][0]['record']['stop_reason'] or len(pool) != 336 or
            r['certificate_parts_rechecked'] != 0 or pool != r['borrowed_interfaces'] or
            r['generated_source_hashes'] != cuts.pilot.source_hashes(sources)):
        raise ValueError('requires the exact prior citation-loader heap failure')
    full.receipt_chain(previous, r, r['borrowed_interfaces'], machine)
    prefix = full.verified_prefix(args, original_pool, machine, sources)
    if prefix['interfaces'] != pool:
        raise ValueError('GC comparison does not retain the exact prior proof pool')
    if assembly6.interfaces(root) != pool or full.source_identity(root) != identity:
        raise ValueError('GC preflight changed its failed donor')
    prefix.update(gc_comparison_failed_report=str(previous),
        gc_comparison_failed_report_sha256=args.expected_failed_sha256,
        gc_settings=['-F1.1', '-A1M'], heap_maximum_unchanged=True,
        failed_obligations_byte_identical=True)
    return prefix


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'prefix-donor', 'packed-donor', 'failed-donor', 'output', 'runs-root'):
        p.add_argument('--'+name, type=Path, required=True)
    for name in ('previous', 'prefix', 'packed', 'failed'):
        p.add_argument('--expected-'+name+'-sha256', required=True)
    p.add_argument('--agda', required=True)
    p.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(p.parse_args(), generator=single.generated,
        directory=single.DIRECTORY, report_format='othello-owner-gc6-v1',
        prefix_validator=verified_prefix, rts_extra=('-F1.1', '-A1M'))['accepted'] else 2)
