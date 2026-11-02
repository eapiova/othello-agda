#!/usr/bin/env python3
"""Measure independent large hint shards and assembly using local interfaces.

Run inside one coordinator reservation. Inputs are untrusted generated fixtures;
every shard receives a cold safe Agda check. Only accepted interfaces from the
same machine and binary may be copied to the assembly directory. This proves
acceptance of these sampled entries, not the initial 6x6 theorem.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import assembly6
import bench6
from provenance import source_identity
from run_job import atomic_json, positive, run_job

HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'
ROOT = Path(__file__).resolve().parents[1]


def part_source(job, name):
    if (job.get('direction'), job.get('threshold'), job.get('rules')) != ('upper', 4, 'fast'):
        raise ValueError('this pilot requires Fast6 upper +4 entries')
    bench6.decode(job['state'])
    text = job['generated_proof']
    if not isinstance(text, str) or len(text.encode()) > 1024 * 1024:
        raise ValueError('generated source exceeds pilot cap')
    state_line = f'position = fromMaybe (initial six) (decodeState "{job["state"]}")'
    if text.count(state_line) != 1:
        raise ValueError('generated position differs from job metadata')
    literals = [line[len('encoded = "'):-1] for line in text.splitlines()
                if line.startswith('encoded = "') and line.endswith('"')]
    if len(literals) != 1 or set(literals[0]) - set('LSPCF0123456789;'):
        raise ValueError('unexpected certificate literal')
    encoded = literals[0]
    if len(encoded) != job['encoded_bytes'] or sum(encoded.count(c) for c in 'LSPCF') != job['hint_tree_S']:
        raise ValueError('certificate byte/node counts differ from metadata')
    expected = 'accepted : checkLocal Fast.fastGame6 black (upperGoal (pos 4)) position certificate ≡ true\naccepted = refl\n'
    if not text.startswith(HEADER) or not text.endswith(expected):
        raise ValueError('unexpected generated proof template')
    text = text[:-len(expected)]
    text = text.replace('module Tests.Bench6.Check where',
                        f'module Tests.AssemblyHint6.{name} where', 1)
    text = text.replace('using (LocalCertificate; localLeaf; checkLocal)',
                        'using (LocalCertificate; localLeaf; Entry; entry; shardOK)', 1)
    start = text.index('certificate : LocalCertificate\n')
    # Keep states/table shape transparent for root lookup, while stopping closed
    # certificate evaluation during conversion in importing assembly modules.
    # Both the decoder fact and acceptance are checked inside this same module.
    text = text[:start] + 'abstract\n' + ''.join(
        '  ' + line + '\n' if line else '\n'
        for line in text[start:].splitlines()) + '\n'
    return text + '''entries : List (Entry (State six))
entries = entry position certificate ∷ []

abstract
  accepted : shardOK Fast.fastGame6 black (upperGoal (pos 4)) entries ≡ true
  accepted = refl
'''


def assembly_source(names):
    imports = ''.join(f'import Tests.AssemblyHint6.{name} as P{i}\n'
                      for i, name in enumerate(names))
    tables = ' ∷ '.join(f'P{i}.entries' for i in range(len(names))) + ' ∷ []'
    proof = 'refl'
    for i in reversed(range(len(names))):
        tail = ' ∷ '.join(f'P{j}.entries' for j in range(i + 1, len(names)))
        tail = f'({tail} ∷ [])' if tail else '[]'
        proof = (f'itemsOK-cons Fast.fastGame6 black (upperGoal (pos 4)) '
                 f'P{i}.entries {tail} P{i}.accepted ({proof})')
    guarantees = ''
    for i in range(len(names)):
        guarantees += f'''
root{i} : checkComposite stateEquality6 tables Fast.fastGame6 black
  (upperGoal (pos 4)) P{i}.position (lemma {i} 0) ≡ true
root{i} = refl

upper{i} : BlackGuarantees (Rules.game six) (upperGoal (pos 4)) P{i}.position
upper{i} = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement
  (compositionSound stateEquality6 tables Fast.fastGame6 black
    (upperGoal (pos 4)) P{i}.position (lemma {i} 0) accepted root{i})
'''
    return HEADER + '''module Tests.AssemblyHint6.Check where

open import Prelude
open import Game.Core using (black; BlackGuarantees)
open import Game.Composite using (Shards; itemsOK; itemsOK-cons;
  checkComposite; lemma; compositionSound)
open import Game.Transfer using (guarantees-transfer)
open import Othello.Board using (State; six)
open import Othello.Encode6 using (stateEquality6)
open import Othello.Proof6 using (fastAgreement)
open import Tests.Bench6.Goals
import Othello.Fast6 as Fast
import Othello.Rules as Rules
''' + imports + f'''
tables : Shards (State six)
tables = {tables}

accepted : itemsOK Fast.fastGame6 black (upperGoal (pos 4)) tables ≡ true
accepted = {proof}
''' + guarantees


def execute(args):
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'results') or output.exists():
        raise ValueError('use a new directory under results/')
    if not 2 <= len(args.jobs) <= 4:
        raise ValueError('pilot requires two to four independent shard fixtures')
    jobs, sources, names = [], {}, []
    for i, path in enumerate(args.jobs):
        path = path.resolve()
        if not path.is_relative_to(ROOT / 'results') or path.stat().st_size > 1024 * 1024:
            raise ValueError('job must be bounded and inside results/')
        job = json.loads(path.read_text())
        name = f'Part{i}'
        sources[f'src/Tests/AssemblyHint6/{name}.agda'] = part_source(job, name)
        jobs.append({'job_sha256': assembly6.sha(path), 'label': job['label'],
                     'hint_tree_S': job['hint_tree_S'], 'encoded_bytes': job['encoded_bytes']})
        names.append(name)
    sources['src/Tests/AssemblyHint6/Check.agda'] = assembly_source(names)
    machine = assembly6.machine_identity(args.agda)
    output.mkdir(parents=True)
    report = {'format': 'othello-large-hint-assembly6-v1', 'machine': machine,
              'inputs': jobs, 'parts': [], 'accepted': False,
              'scope': 'sampled upper entries only; no initial-board proof'}

    def save():
        atomic_json(output / 'assembly.json', report)

    def prepare(label):
        root = output / label
        root.mkdir()
        shutil.copytree(ROOT / 'src', root / 'src')
        shutil.copy2(ROOT / 'othello.agda-lib', root / 'othello.agda-lib')
        for relative, text in sources.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        manifest = bench6.refresh_manifest(root)
        if assembly6.interfaces(root):
            raise ValueError('prepared roots must contain no interfaces')
        return root, manifest['source_sha256']

    def check(root, digest, name, cpu):
        if assembly6.machine_identity(args.agda) != machine:
            raise ValueError('machine or compiler changed')
        command = [machine['agda_path'], *assembly6.FLAGS, '-i', 'src',
                   f'src/Tests/AssemblyHint6/{name}.agda',
                   '+RTS', f'-M{args.heap_mib}M', '-RTS']
        return run_job('hint-assembly6-' + name, command, output / 'records',
                       root=root, expected_source_sha256=digest,
                       timeout=args.timeout, cpu_limit=cpu,
                       rss_limit_gib=args.rss_limit_gib, log_limit_mib=2,
                       metadata={'same_machine': machine, 'role': name})

    target, target_digest = prepare('assembly')
    donors = []
    save()
    for name in names:
        root, digest = prepare(name)
        record = check(root, digest, name, args.part_cpu)
        report['parts'].append(record)
        save()
        if not record['accepted']:
            report['failure'] = name + ' failed; assembly not attempted'
            save()
            return report
        donors.append(root)
    copied = {}
    for donor in donors:
        if assembly6.machine_identity(args.agda) != machine:
            raise ValueError('machine or compiler changed before interface transfer')
        source_identity(donor)
        for relative, digest in assembly6.interfaces(donor).items():
            if relative in copied:
                continue
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(donor / relative, path)
            if assembly6.sha(path) != digest:
                raise ValueError('interface copy hash mismatch')
            copied[relative] = {'donor': str(donor), 'sha256': digest}
    part_suffixes = [f'/Tests/AssemblyHint6/{name}.agdai' for name in names]
    before = {k: v for k, v in assembly6.interfaces(target).items()
              if any(('/' + k).endswith(s) for s in part_suffixes)}
    if len(before) != len(names):
        raise ValueError('not all accepted part interfaces were copied')
    record = check(target, target_digest, 'Check', args.assembly_cpu)
    after = {k: v for k, v in assembly6.interfaces(target).items() if k in before}
    log = (output / 'records/hint-assembly6-Check.log').read_text()
    rechecked = [n for n in names if f'Checking Tests.AssemblyHint6.{n} ' in log]
    report.update(assembly=record, copied_interfaces=copied,
                  part_interfaces_before=before, part_interfaces_after=after,
                  rechecked_parts=rechecked,
                  accepted=record['accepted'] and before == after and not rechecked)
    if not report['accepted']:
        report['failure'] = 'assembly failed, rechecked parts, or changed accepted interfaces'
    save()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--agda', required=True)
    parser.add_argument('--part-cpu', type=positive, default=600)
    parser.add_argument('--assembly-cpu', type=positive, default=60)
    parser.add_argument('--timeout', type=positive, default=900)
    parser.add_argument('--rss-limit-gib', type=positive, default=1.5)
    parser.add_argument('--heap-mib', type=int, default=1200)
    args = parser.parse_args()
    if args.heap_mib <= 0:
        parser.error('heap cap must be positive')
    result = execute(args)
    print(json.dumps({'accepted': result['accepted'],
                      'report': str(args.output / 'assembly.json')}))
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
