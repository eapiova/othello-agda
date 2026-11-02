#!/usr/bin/env python3
"""Plan smaller owner bindings from accepted conditional proofs.

This is a source and lexical-dependency diagnostic. Emitted bindings are
unchecked proposals; the original certificate data and interfaces are untouched.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import assembly6
import global_assembly6 as assembly
import owner_cuts6 as cuts
import owner_split6 as split
from provenance import digest_entries, source_identity
from run_job import atomic_json

PREFIX = 'Tests.OwnerClosure6'
DIRECTORY = 'src/Tests/OwnerClosure6'
OLD_ROOT = 'Tests.DirectCitations6.Root'
BLOCK = re.compile(r'^module P(\d+) where\n', re.M)
IMPORT = re.compile(r'^import (\S+) as (\S+)$', re.M)
LEXICAL = re.compile(r'^\s*(?:open\s+)?import\s+([A-Za-z0-9_.]+)', re.M)


def blocks(text):
    matches = list(BLOCK.finditer(text))
    if not matches:
        raise ValueError('owner source has no proof blocks')
    result = {}
    for j, match in enumerate(matches):
        end = matches[j+1].start() if j+1 < len(matches) else len(text)
        body = text[match.start():end].split('\nposition :', 1)[0].rstrip()+'\n'
        index = int(match[1])
        if index in result or 'coverage = refl {x = true}' not in body:
            raise ValueError('owner block differs from the accepted coverage layout')
        result[index] = body
    prefix = text[:matches[0].start()]
    if '\nroutesFor :' not in prefix:
        raise ValueError('owner routing helper missing')
    routing = 'routesFor :'+prefix.split('\nroutesFor :', 1)[1]
    return result, {alias: module for module, alias in IMPORT.findall(prefix)}, routing.rstrip()+'\n'


def proposed(root):
    original = {}
    locations = {}
    root4 = root/'src/Tests/DirectCitations6/Root.agda'
    candidates = [(4, root4)]
    for index in (2, 3, 5):
        candidates += [(index, path) for path in sorted(
            (root/f'src/Tests/OwnerLower6/Root{index}').glob('Assemble[0-9]*.agda'))
            if 'Split' not in path.stem and path.stem != 'Assemble6']
    candidates += [(5, root/f'{split.DIRECTORY}/Assemble6Split{j}.agda') for j in range(3)]
    for index, path in candidates:
        text = path.read_text()
        parts, aliases, routing = blocks(text)
        old_module = re.search(r'^module (\S+) where$', text, re.M)[1]
        for part, body in parts.items():
            key = (index, part)
            if key in original:
                raise ValueError('duplicate owner binding')
            original[key] = (body, aliases, routing, old_module)
            locations[(old_module, part)] = f'{PREFIX}.Root{index}.Part{part}'
    if set(k for k in original if k[0] == 4) != {(4, j) for j in range(114, 118)}:
        raise ValueError('root4 suffix changed')
    if set(k for k in original if k[0] == 5) != {(5, j) for j in range(27)}:
        raise ValueError('root5 conditional owner parts changed')

    sources, rows = {}, []
    for (index, part), (body, aliases, routing, old_module) in sorted(original.items()):
        # The original root defines preceding parts locally, including those
        # in the same assembly shard. Move these exact references to imports.
        rewritten = body
        selected = {}
        replacements = {}
        for match in re.finditer(r'\b([A-Za-z][A-Za-z0-9_]*)\.P(\d+)\.', body):
            alias, owner = match[1], int(match[2])
            if alias not in aliases:
                raise ValueError('unrecognized owner namespace')
            old = aliases[alias]
            if (old, owner) in locations:
                new_alias = f'{alias}_Part{owner}'
                replacements[f'{alias}.P{owner}.'] = f'{new_alias}.P{owner}.'
                selected[new_alias] = locations[(old, owner)]
        for match in re.finditer(r'(?<![A-Za-z0-9_.])P(\d+)\.', body):
            owner = int(match[1])
            if owner == part:
                raise ValueError('unexpected self reference')
            if (old_module, owner) in locations:
                alias = f'EarlierPart{owner}'
                replacements[f'P{owner}.'] = f'{alias}.P{owner}.'
                selected[alias] = locations[(old_module, owner)]
        if replacements:
            pattern = re.compile('|'.join(re.escape(s) for s in sorted(replacements, key=len, reverse=True)))
            rewritten = pattern.sub(lambda m: replacements[m[0]], body)
        for alias, old in aliases.items():
            if re.search(r'(?<![A-Za-z0-9_])'+re.escape(alias)+r'\.', rewritten):
                selected[alias] = old
        name = f'{PREFIX}.Root{index}.Part{part}'
        text = cuts.pilot.local_options(assembly.HEADER+f'module {name} where\n\n')
        common_aliases = {alias: module for module, alias in IMPORT.findall(assembly.COMMON)}
        private = assembly.COMMON + 'open import Tests.DirectCitations6.Coverage using (coveredBy; coveredBy-sound)\n'
        private += ''.join(f'import {module} as {alias}\n' for alias, module in sorted(selected.items())
                           if common_aliases.get(alias) != module) + '\n'+routing
        text += 'private\n'+''.join('  '+line+'\n' if line else '\n' for line in private.splitlines())
        text += '\n'+rewritten
        # Rewrite only names. Citation hint strings, imports, state definitions,
        # and all proof terms/coverage obligations otherwise remain identical.
        if re.findall(r'"([^"\n]*)"', rewritten) != re.findall(r'"([^"\n]*)"', body):
            raise ValueError('owner routing data changed')
        path = 'src/'+name.replace('.', '/')+'.agda'
        sources[path] = text
        rows.append(dict(root=index, part=part, module=name, original_module=old_module,
            source=path, imports=sorted(set(selected.values())),
            routing_literals_unchanged=True, accepted=False))
    return sources, rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--expected-report-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    previous = args.previous.resolve()
    if assembly6.sha(previous/'final.json') != args.expected_report_sha256:
        raise ValueError('owner split report differs')
    report = json.loads((previous/'final.json').read_text())
    root = Path(report['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    if (report['status'] != 'phase-failed' or report['accepted'] or len(pool) != 325 or
            pool != report['final_interfaces'] or identity['source_sha256'] != report['source_sha256'] or
            digest_entries(pool) != report['interfaces_sha256'] or
            not report['donor_unchanged'] or not report['generated_sources_unchanged']):
        raise ValueError('requires the unchanged owner split checkpoint')
    sources, rows = proposed(root)
    graph = {}
    for path in (root/'src').rglob('*.agda'):
        module = '.'.join(path.relative_to(root/'src').with_suffix('').parts)
        graph[module] = sorted(set(LEXICAL.findall(path.read_text())))
    for path, text in sources.items():
        graph[path[4:-5].replace('/', '.')] = sorted(set(LEXICAL.findall(text)))

    def closure(module):
        seen, pending = set(), [module]
        while pending:
            m = pending.pop()
            if m not in seen:
                seen.add(m)
                pending.extend(graph.get(m, []))
        names = {'_build/2.9.0/agda/src/'+m.replace('.', '/')+'.agdai' for m in seen}
        checked = sorted(names.intersection(pool))
        proposals = sorted(m for m in seen if m.startswith(PREFIX+'.'))
        return dict(checked_interfaces=len(checked), checked_interface_paths=checked,
            compressed_bytes=sum((root/n).stat().st_size for n in checked),
            unchecked_proposal_modules=proposals, lexical_modules=len(seen))

    before = 'Tests.OwnerLower6.Root5.Assemble6Split2'
    after = f'{PREFIX}.Root5.Part26'
    args.output.mkdir(parents=True, exist_ok=False)
    for path, text in sources.items():
        target = args.output/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    result = dict(format='othello-owner-closure-plan6-v1',
        scope='lexical dependency diagnostic and unchecked proof-binding proposals',
        previous=str(previous), previous_report_sha256=args.expected_report_sha256,
        source_sha256=identity['source_sha256'], interfaces_sha256=digest_entries(pool),
        generated_source_hashes=cuts.pilot.source_hashes(sources), rows=rows,
        original=closure(before), proposed=closure(after),
        conditional_certificates_rechecked=0, postulates=0,
        checked_lower_roots=5, initial_problem2_proved=False, production_authorized=False)
    if assembly6.interfaces(root) != pool or source_identity(root) != identity:
        raise ValueError('diagnostic changed its proof donor')
    result.update(donor_sources_unchanged=True, donor_interfaces_unchanged=True)
    atomic_json(args.output/'plan.json', result)
    print(json.dumps(dict(format=result['format'], original={k:v for k,v in result['original'].items()
        if k != 'checked_interface_paths'}, proposed={k:v for k,v in result['proposed'].items()
        if k != 'checked_interface_paths'}), indent=2))


if __name__ == '__main__':
    main()
