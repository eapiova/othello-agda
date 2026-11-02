#!/usr/bin/env python3
"""One bounded, safe recovery of the completed sample's failed collector.

Reuse unchanged accepted interfaces on their original machine. Narrow the
imported names and group proof tuples; keep the same 100 roots and resource
limits. A failed collector never invalidates the individually checked bounds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import assembly6
import bench6
import global_assembly6 as assembly
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job


def thin_source(original):
    """Re-express the already generated exact tuple without changing witnesses."""
    import re
    modules = re.findall(r'^import (Tests\.[\w.]+) as (R\d+)$', original, re.M)
    body = original.split('  allUpper = ', 1)[1]
    facts = re.findall(r'(R\d+)\.(guarantee\d+)\s*,', body)
    literal = original.split('rootCodes = ', 1)[1].split('\n', 1)[0]
    codes = re.findall(r'"([^"]+)"', literal)
    if len(codes) != 100 or len(set(codes)) != 100 or len(facts) != 100:
        raise ValueError('requires the exact original 100 distinct roots and witnesses')
    aliases = {alias: module for module, alias in modules}
    if len(aliases) != len(modules) or any(alias not in aliases for alias, _ in facts):
        raise ValueError('collector import aliases are malformed')
    text = assembly.HEADER + '''module Tests.ClosedPilot6.All100Thin where

open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (black; Guarantees)
open import Othello.Board using (State; six; initial)
open import Othello.CompactShared6 using (decodeCompactState)
open import Othello.Statements using (upperGoal)
import Othello.Rules as Rules

decode : String → State six
decode text = fromMaybe (initial six) (decodeCompactState text)

'''
    for module, alias in modules:
        names = sorted({fact for owner, fact in facts if owner == alias})
        if not names:
            raise ValueError('original collector has an unused proof import')
        text += f'import {module} as {alias} using ({"; ".join(names)})\n'
    text += '''
AllUpper : List String → Set
AllUpper [] = ⊤
AllUpper (code ∷ codes) =
  Guarantees (Rules.game six) black (upperGoal 4) (decode code) × AllUpper codes

appendUpper : ∀ xs ys → AllUpper xs → AllUpper ys → AllUpper (xs ++ ys)
appendUpper [] ys tt right = right
appendUpper (code ∷ codes) ys (bound , rest) right =
  bound , appendUpper codes ys rest right
'''
    groups = [codes[i:i+5] for i in range(0, 100, 5)]
    for i, group in enumerate(groups):
        text += f'\ncodes{i} : List String\ncodes{i} = '
        text += ' ∷ '.join(f'"{code}"' for code in group) + ' ∷ []\n'
        tuple_body = 'tt'
        for alias, fact in reversed(facts[5*i:5*i+5]):
            tuple_body = f'{alias}.{fact} , ({tuple_body})'
        text += f'\nabstract\n  upper{i} : AllUpper codes{i}\n  upper{i} = {tuple_body}\n'
    rest, proof = '[]', 'tt'
    for i in reversed(range(len(groups))):
        proof = f'appendUpper codes{i} ({rest}) upper{i} ({proof})'
        rest = f'codes{i} ++ ({rest})'
    text += f'\nrootCodes : List String\nrootCodes = {rest}\n'
    text += f'\nabstract\n  allUpper : AllUpper rootCodes\n  allUpper = {proof}\n'
    return text


def run(args):
    previous = args.previous.resolve()
    report = json.loads((previous / 'closed.json').read_text())
    record = json.loads((previous / 'records/all100.json').read_text())
    donor = previous / 'all100'
    machine = assembly6.machine_identity(args.agda)
    origin = source_identity(donor)
    before = assembly6.interfaces(donor)
    if (report.get('status') != 'collector-failed' or report.get('accepted') or
            report.get('checked_sample_upper_roots') != 100 or
            len(report.get('new_checked_roots', [])) != 34 or
            not report.get('preserved_sources_unchanged') or
            not report.get('preserved_interfaces_unchanged') or
            machine != report['machine'] or machine != record['machine'] or
            record['accepted'] or not record['source_unchanged'] or
            not record['expected_source_matches'] or
            origin['source_sha256'] != record['source_sha256'] or
            digest_entries(before) != record['borrowed_interfaces_sha256']):
        raise ValueError('requires the unchanged, completed 100-root checkpoint')
    for phase in report['phases'][:-1]:
        if not phase['accepted']:
            raise ValueError('the prior roots have not all passed')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = output / 'check'
    root.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor / name, root / name)
    target = 'src/Tests/ClosedPilot6/All100Thin.agda'
    source = thin_source((donor / 'src/Tests/ClosedPilot6/All100.agda').read_text())
    (root / target).write_text(source)
    for name in before:
        assembly.hardlink(donor / name, root / name)
    if any(p.endswith('/All100Thin.agdai') for p in before):
        raise ValueError('recovery target already has an interface')
    manifest = bench6.refresh_manifest(root, origin={k: origin[k] for k in ['revision', 'dirty']})
    checked = run_job('all100-thin', [args.agda, *assembly6.FLAGS, '-i', 'src', target,
                       '+RTS', '-M2500M', '-c', '-s', '-RTS'], output / 'records', root=root,
                       expected_source_sha256=manifest['source_sha256'],
                       cpu_limit=180, timeout=360, rss_limit_gib=3, log_limit_mib=2,
                       metadata={'machine': machine, 'own_target_cold': True,
                                 'borrowed_interfaces_sha256': digest_entries(before)})
    after = assembly6.interfaces(root)
    if (any(after.get(p) != d for p, d in before.items()) or
            source_identity(donor)['source_sha256'] != origin['source_sha256'] or
            assembly6.interfaces(donor) != before):
        raise ValueError('an accepted dependency changed')
    result = dict(format='othello-collector-thin6-v1',
                  accepted=checked['accepted'],
                  status='complete' if checked['accepted'] else 'collector-failed',
                  checked_sample_upper_roots=100, initial_problem2_proved=False,
                  source_sha256=checked['source_sha256'],
                  machine=machine, preserved_sources_unchanged=True,
                  preserved_interfaces_unchanged=True,
                  assembly=assembly.metrics(checked),
                  rts=rts_stats((output / 'records/all100-thin.log').read_text()))
    atomic_json(output / 'collector.json', result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--agda', required=True)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
