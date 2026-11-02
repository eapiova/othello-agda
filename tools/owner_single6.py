#!/usr/bin/env python3
"""Check the complete opaque citation list in one scope before final binding.

This removes the batch-interface import burden. All original conditional
certificates and the checked opaque API/closure are reused unchanged.
"""
import argparse
from pathlib import Path
import re

import global_assembly6 as assembly
import owner_capsule6 as capsule
import owner_capsule_full6 as full
import owner_cuts6 as cuts
import owner_packed6 as packed
import owner_split6 as split
from run_job import positive

PREFIX = 'Tests.OwnerSingle6'
DIRECTORY = 'src/Tests/OwnerSingle6'


def header(name):
    return cuts.pilot.local_options(assembly.HEADER + f'module {PREFIX}.{name} where\n\n')


def generated(donor):
    original = (donor / f'{split.DIRECTORY}/Assemble6Split2.agda').read_text()
    routing = cuts.routing(original)
    old, _, partition = packed.generated(donor)  # Exact original input guard.
    ordered = sorted(routing)
    modules = {alias: module for module, alias in re.findall(
        r'^import (\S+) as (\S+)$', original, re.M)}
    source = capsule.capsule_source(0, 0, ordered, routing, modules, entire=True)
    source = source.replace(f'module {capsule.PREFIX}.Chunk0 where', f'module {PREFIX}.Citations where', 1)
    binding = header('Binding') + 'private\n'
    dependencies = assembly.COMMON + '''open import Tests.OwnerPacked6.Closure
import Tests.OwnerLists6.Inputs as I
import Tests.OwnerLower6.Root5.Part26 as I26
import Tests.OwnerSingle6.Citations as D
'''
    binding += ''.join('  '+line+'\n' if line else '\n' for line in dependencies.splitlines())
    binding += '''
module P26 where
  states : Trie (State six)
  states = I26.states

  abstract
    inputShape : I26.imports ≡ shardStates keyed6 I.entries
    inputShape = refl {x = I26.imports}

    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = closeCitations keyed6 Fast.fastGame6 white (lowerGoal 4) I.entries
      I26.imports I26.states inputShape I26.sound D.sound

  export : CheckedExport Fast.fastGame6 white (lowerGoal 4)
  export = checkedExport states sound
'''
    sources = {f'{DIRECTORY}/Citations.agda': source, f'{DIRECTORY}/Binding.agda': binding}
    for name in ('Facade', 'Root'):
        sources[f'{DIRECTORY}/{name}.agda'] = old[f'{packed.DIRECTORY}/{name}.agda'].replace(packed.PREFIX, PREFIX)
    partition.update(single_scope=True, entire_original_import_list=True,
        conditional_certificates_reused=True, original_generic_closure_reused=True,
        no_accepted_batch_interface_modified=True)
    phases = [('Citations', 180, False), ('Binding', 180, False), ('Facade', 30, False), ('Root', 180, False)]
    return sources, phases, partition


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'prefix-donor', 'packed-donor', 'output', 'runs-root'):
        p.add_argument('--'+name, type=Path, required=True)
    for name in ('previous', 'prefix', 'packed'):
        p.add_argument('--expected-'+name+'-sha256', required=True)
    p.add_argument('--agda', required=True)
    p.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(p.parse_args(), generator=generated, directory=DIRECTORY,
        report_format='othello-owner-single6-v1', prefix_validator=full.verified_prefix)['accepted'] else 2)
