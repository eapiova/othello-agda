#!/usr/bin/env python3
"""Probe opaque, separately checked Boolean and soundness modules for eight imports."""
from __future__ import annotations

import argparse
from pathlib import Path

import global_assembly6 as assembly
import owner_cuts6 as cuts
import owner_queries6 as queries
from run_job import positive

PREFIX = 'Tests.OwnerSeparated6'
DIRECTORY = 'src/Tests/OwnerSeparated6'


def generated(donor):
    full, _, summary = queries.generated(donor)
    original = full[queries.DIRECTORY+'/Chunk0.agda']
    marker = '\n  sound : AllL '
    if original.count(marker) != 1:
        raise ValueError('the exact unaccepted eight-entry soundness obligation is required')
    data = original.split(marker, 1)[0]+'\n'
    data = data.replace(f'module {queries.PREFIX}.Chunk0 where', f'module {PREFIX}.Data0 where', 1)
    proof = cuts.pilot.local_options(assembly.HEADER+f'module {PREFIX}.Proof0 where\n\n')+assembly.COMMON
    proof += f'''open import Tests.OwnerLists6.Lookup
import {PREFIX}.Data0 as D

abstract
  sound : AllL (λ e → Proven Fast.fastGame6 white (lowerGoal 4) (entryState e)) D.rows
  sound = listKnown-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
    D.sources D.tables D.hints D.rows D.association D.accepted
'''
    return {f'{DIRECTORY}/Data0.agda': data, f'{DIRECTORY}/Proof0.agda': proof}, [
        ('Data0', 60, False), ('Proof0', 60, False)], dict(summary, measured_chunks=1,
            standalone_lower_root_completed=False, soundness_separate_from_boolean=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'prefix-donor', 'output', 'runs-root'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--expected-previous-sha256', required=True)
    parser.add_argument('--expected-prefix-sha256', required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(parser.parse_args(), generator=generated, directory=DIRECTORY,
        report_format='othello-owner-separated-probe6-v1', negative_guard=queries.lists.rejected_missing,
        prefix_validator=queries.verified_prefix, complete_lower_root=False)['accepted'] else 2)
