#!/usr/bin/env python3
"""Rebind root5 owners with private, smaller dependency scopes.

Accepted conditional certificate modules remain byte-for-byte unchanged.
Every emitted owner coverage fact and the root guarantee are checked anew.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

import global_assembly6 as assembly
import owner_closure6 as closure
import owner_cuts6 as cuts
import owner_split6 as split
from run_job import positive

PREFIX = 'Tests.OwnerPruned6'
DIRECTORY = 'src/Tests/OwnerPruned6'


def generated(donor):
    original = []
    root4 = donor/'src/Tests/DirectCitations6/Root.agda'
    original.append(('R4P114', root4, [114]))
    for chunk in range(6):
        original.append((f'R5Assemble{chunk}',
            donor/f'src/Tests/OwnerLower6/Root5/Assemble{chunk}.agda', list(range(chunk*4, chunk*4+4))))
    for part in range(24, 27):
        original.append((f'R5Part{part}', donor/f'{split.DIRECTORY}/Assemble6Split{part-24}.agda', [part]))
    mapping = {}
    for name, path, _ in original:
        old_module = re.search(r'^module (\S+) where$', path.read_text(), re.M)[1]
        mapping[old_module] = f'{PREFIX}.{name}'
    sources, phases, rows = {}, [], []
    common_aliases = {alias: module for module, alias in closure.IMPORT.findall(assembly.COMMON)}
    for name, path, chosen in original:
        text = path.read_text()
        if assembly.COMMON not in text:
            raise ValueError('original common proof context changed')
        parts, aliases, routing = closure.blocks(text)
        if not set(chosen).issubset(parts):
            raise ValueError('required accepted owner block missing')
        body = '\n'.join(parts[j] for j in chosen)
        selected = {alias: module for alias, module in aliases.items()
                    if re.search(r'(?<![A-Za-z0-9_])'+re.escape(alias)+r'\.', body)}
        for alias, module in selected.items():
            if module == closure.OLD_ROOT and re.search(r'\b'+re.escape(alias)+r'\.P(?!114\b)\d+\.', body):
                raise ValueError('another root4 export is required')
        selected = {alias: mapping.get(module, module) for alias, module in selected.items()}
        private = assembly.COMMON+'open import Tests.DirectCitations6.Coverage using (coveredBy; coveredBy-sound)\n'
        private += ''.join(f'import {module} as {alias}\n' for alias, module in sorted(selected.items())
                           if common_aliases.get(alias) != module)+'\n'+routing
        proposed = cuts.pilot.local_options(assembly.HEADER+f'module {PREFIX}.{name} where\n\n')
        proposed += 'private\n'+''.join('  '+line+'\n' if line else '\n' for line in private.splitlines())
        proposed += '\n'+body
        sources[f'{DIRECTORY}/{name}.agda'] = proposed
        phases.append((name, 180, False))
        rows.append(dict(module=name, original_source=str(path.relative_to(donor)), parts=chosen,
            imports=sorted(set(selected.values())), body_unchanged=True,
            routing_literals_unchanged=True))
    root = (donor/f'{split.DIRECTORY}/Check.agda').read_text()
    root = root.replace(f'module {split.NAMESPACE}.Check where', f'module {PREFIX}.Root where', 1)
    old_import = f'import {split.NAMESPACE}.Assemble6 as A'
    if root.count(old_import) != 1 or 'A.P26.' not in root:
        raise ValueError('root guarantee import changed')
    root = root.replace(old_import, f'import {PREFIX}.R5Part26 as A', 1)
    sources[f'{DIRECTORY}/Root.agda'] = root
    phases.append(('Root', 180, False))
    return sources, phases, dict(bindings=rows, selected_root4_part=114,
        conditional_certificates_rechecked=0, original_root_membership_unchanged=True,
        original_guarantee_transfer_unchanged=True, production_authorized=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output', 'runs-root'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--expected-previous-sha256', required=True)
    p.add_argument('--agda', required=True)
    p.add_argument('--kernel-cpu-budget', type=positive, required=True)
    raise SystemExit(0 if cuts.run(p.parse_args(), generator=generated, directory=DIRECTORY,
        report_format='othello-owner-pruned6-v1', prefix_validator=lambda *a: None)['accepted'] else 2)
