#!/usr/bin/env python3
"""AI-assisted same-machine, cold-shard assembly experiment for local p26.

Run this harness inside ONE study6 ledger reservation; its nested run_job records
are measurements, not additional reservations. No network or external interfaces
are used. prepare only freezes sources; run performs two cold checks followed by
assembly. Resource limits apply separately to each of the three checks; reserve
at least their sum plus harness overhead in the outer study job.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess

from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, positive, run_job, utc

ROOT = Path(__file__).resolve().parents[1]
PARTS = ('Lower0', 'Lower1', 'Upper0', 'Upper1')
FLAGS = ['--no-libraries', '--safe', '--without-K', '--cubical-compatible']
HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'
IMPORTERS = {
    'cold-lower': ('ColdLower', 'import Othello.Proof6.Lower0\nimport Othello.Proof6.Lower1\n'),
    'cold-upper': ('ColdUpper', 'import Othello.Proof6.Upper0\nimport Othello.Proof6.Upper1\n'),
    'assembly': ('Check', 'open import Othello.Pilot6 using (completedOptimalPair)\n'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interfaces(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*.agdai'))}


def part_interfaces(root):
    found = {}
    for part in PARTS:
        suffix = f'/Othello/Proof6/{part}.agdai'
        matches = [p for p in root.rglob('*.agdai') if p.as_posix().endswith(suffix)]
        if len(matches) > 1:
            raise ValueError(f'ambiguous {part} interface in {root}')
        found[part] = None if not matches else {
            'path': matches[0].relative_to(root).as_posix(), 'sha256': sha(matches[0])}
    return found


def machine_identity(agda):
    executable = Path(shutil.which(agda) or agda).resolve(strict=True)
    return {'hostname': socket.gethostname(),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'agda_path': str(executable), 'agda_sha256': sha(executable),
            'agda_version': subprocess.check_output([str(executable), '--version'], text=True).strip()}


def prepare(root, output):
    root, output = root.resolve(), output.resolve()
    if root not in output.parents or 'results' not in output.relative_to(root).parts:
        raise ValueError('experiment directories must be inside source-root results/')
    origin = source_identity(root)
    # Materialize before creating output so recursive discovery cannot include it.
    files = list(source_files(root))
    if output.exists():
        raise ValueError('use a new output directory for each experiment')
    parts = {}
    for part in PARTS:
        path = root / f'src/Othello/Proof6/{part}.agda'
        text = path.read_text()
        if 'abstract\n  accepted :' not in text or 'accepted = refl' not in text:
            raise ValueError('pilot acceptance terms must already be abstract')
        parts[part] = {'proof_sha256': sha(path),
                       'data_sha256': sha(root / f'src/Othello/Data6/{part}.agda')}
    output.mkdir(parents=True)
    roots = {}
    for key, (module, imports) in IMPORTERS.items():
        destination = output / key
        for name, raw in files:
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        relative = f'src/Tests/Assembly6/{module}.agda'
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(HEADER + '-- AI-assisted experiment importer.\n' +
                        f'module Tests.Assembly6.{module} where\n\n' + imports)
        entries = {name: hashlib.sha256(raw).hexdigest() for name, raw in source_files(destination)}
        atomic_json(destination / 'SNAPSHOT.json', {
            'format': 'othello-source-snapshot-v1', 'files': entries,
            'source_sha256': digest_entries(entries),
            'git': {'revision': origin['revision'], 'dirty': origin['dirty']}, 'created_utc': utc()})
        identity = source_identity(destination)
        if interfaces(destination):
            raise ValueError('prepared source root must have zero interfaces')
        roots[key] = {'root': str(destination), 'importer': relative, **identity}
    plan = {'format': 'othello-assembly6-plan-v1', 'created_utc': utc(),
            'origin': origin, 'parts': parts, 'pilot_sha256': sha(root / 'src/Othello/Pilot6.agda'),
            'roots': roots, 'scope': 'p26 local completedOptimalPair; no initial-position claim'}
    atomic_json(output / 'plan.json', plan)
    return plan


def execute(args, plan):
    output = args.output.resolve()
    machine = machine_identity(args.agda)
    result = {'format': 'othello-assembly6-result-v1', 'machine': machine,
              'plan': plan, 'jobs': [], 'accepted': False, 'started_utc': utc()}
    report = output / 'assembly.json'

    def save():
        atomic_json(report, result)

    def check(key):
        item = plan['roots'][key]
        root = Path(item['root'])
        if source_identity(root)['source_sha256'] != item['source_sha256']:
            raise ValueError('source root differs from its frozen plan')
        if machine_identity(args.agda) != machine:
            raise ValueError('machine or Agda identity changed before checking')
        command = [machine['agda_path'], *FLAGS, '-i', 'src', item['importer'],
                   '+RTS', '-M' + str(args.heap_mib) + 'M', '-RTS']
        record = run_job('assembly6-' + key, command, root / 'results', root=root,
                         timeout=args.timeout, cpu_limit=args.cpu_limit,
                         rss_limit_gib=args.rss_limit_gib, log_limit_mib=args.log_limit_mib,
                         expected_source_sha256=item['source_sha256'],
                         metadata={'assembly_role': key, 'same_machine': machine,
                                   'proof_parts': plan['parts'], 'agda_version': machine['agda_version']})
        result['jobs'].append(record)
        result.setdefault('part_interfaces', {})[key] = part_interfaces(root)
        save()
        return record

    save()
    for key in ('cold-lower', 'cold-upper'):
        root = Path(plan['roots'][key]['root'])
        if interfaces(root):
            raise ValueError('cold source roots must have zero interfaces before launch')
        if not check(key)['accepted']:
            result['failure'] = key + ' check failed; assembly not attempted'
            result['finished_utc'] = utc()
            save()
            return result
    target = Path(plan['roots']['assembly']['root'])
    if interfaces(target):
        raise ValueError('assembly root must have zero interfaces before copying')
    copied, alternatives = {}, []
    for key in ('cold-lower', 'cold-upper'):
        donor = Path(plan['roots'][key]['root'])
        if machine_identity(args.agda) != machine:
            raise ValueError('machine or Agda identity changed during experiment')
        for relative, digest in interfaces(donor).items():
            if relative in copied:
                alternatives.append({'path': relative, 'donor': key, 'sha256': digest,
                                     'matches_chosen': digest == copied[relative]['sha256']})
                continue
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(donor / relative, path)
            copied[relative] = {'donor': key, 'sha256': digest}
    before = part_interfaces(target)
    result.update(copied_interfaces=copied, duplicate_interfaces=alternatives,
                  assembly_interfaces_before=len(interfaces(target)), accepted_parts_before=before)
    if not all(before.values()):
        raise ValueError('all four checked acceptance modules must be available before assembly')
    # Manifest still matches: only .agdai files have been inserted.
    source_identity(target)
    record = check('assembly')
    after = part_interfaces(target)
    log = (target / 'results/assembly6-assembly.log').read_text()
    recomputed = [part for part in PARTS if f'Checking Othello.Proof6.{part} ' in log]
    result.update(accepted_parts_after=after, assembly_interfaces_after=len(interfaces(target)),
                  acceptance_interfaces_unchanged=before == after,
                  acceptance_modules_rechecked=recomputed,
                  finished_utc=utc(), assembly_wall_seconds=record['wall_seconds'],
                  assembly_cpu_seconds=record['cpu_seconds'], assembly_peak_rss_gib=record['peak_rss_gib'])
    result['accepted'] = record['accepted'] and before == after and not recomputed
    save()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--agda', default='agda')
    parser.add_argument('--timeout', type=positive, default=1800)
    parser.add_argument('--cpu-limit', type=positive, default=1800)
    parser.add_argument('--rss-limit-gib', type=positive, default=10)
    parser.add_argument('--heap-mib', type=int, default=8192)
    parser.add_argument('--log-limit-mib', type=positive, default=8)
    args = parser.parse_args()
    if args.heap_mib <= 0:
        parser.error('heap MiB must be positive')
    plan = prepare(args.root, args.output)
    if args.action == 'prepare':
        print(json.dumps({'plan': str(args.output.resolve() / 'plan.json'), 'roots': plan['roots']}))
        return 0
    result = execute(args, plan)
    print(json.dumps({'report': str(args.output.resolve() / 'assembly.json'), 'accepted': result['accepted']}))
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
