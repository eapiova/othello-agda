#!/usr/bin/env python3
"""Measure one shared checker instance on two unchanged real row checks.

All inputs remain untrusted data. The new parts are checked by Agda, with no
prior part proof imported. The accepted warning-filtered baseline is preserved.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil

import assembly6
from cache_resume6 import copy_interface
from data_only_pilot6 import borrowed_sources
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require

PREFIX = 'Tests.IndexedWire6'
INSTANCE = 'module Lower = D.Checking Shape.shape Fast.fastGame6 white (lowerGoal 4) lowerTransport6\n'
WARNING = '-WnoUnsupportedIndexedMatch'


def shared_part(original: str) -> str:
    """Use qualified references, without a second module application/alias."""
    require(original.count(INSTANCE) == 1, 'one known lower checker instance required')
    require('Family.' not in original and '.Family as' not in original, 'already rewritten part')
    imported = 'import ' + PREFIX + '.Family as Family\n'
    text = original.replace(INSTANCE, imported, 1).replace('Lower.', 'Family.Lower.')
    require(text.replace('Family.Lower.', 'Lower.').replace(imported, INSTANCE, 1) == original,
            'change beyond checker import/qualification')
    require(not re.search(r'^\s*(?:open\s+)?import\s+\S*\.Part\d+', text, re.M),
            'local row checks must not import earlier proofs')
    return text


def shared_instance(original: str) -> str:
    start = original.index('open import Prelude\n')
    end = original.index(INSTANCE) + len(INSTANCE)
    imports_and_instance = original[start:end]
    return ('{-# OPTIONS --safe --without-K --cubical-compatible ' + WARNING + ' #-}\n'
            '-- AI-assisted. One ordinary safe checker instance shared by row parts.\n'
            'module ' + PREFIX + '.Family where\n\n' + imports_and_instance)


def pinned(path, digest):
    require(assembly6.sha(path) == digest, 'pinned artifact differs: ' + str(path))
    return json.loads(path.read_text())


def run(args):
    current = Path.cwd()
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh isolated experiment required')
    out.mkdir(parents=True)
    baseline = args.baseline.resolve()
    old = baseline / 'results/indexed-cache-mode6/check'
    report_path = baseline / 'results/indexed-cache-mode6/report.json'
    prior = pinned(report_path, args.expected_baseline_report_sha256)
    old_source = source_identity(old)
    require(prior['accepted'] and prior['local_warning_filter'] == WARNING and
            prior['checked_source'] == old_source and not prior['initial_problem2_proved'],
            'accepted unchanged warning-filtered baseline required')
    machine = assembly6.machine_identity(args.agda)
    require(machine['hostname'] == 'eapiova' and machine['agda_sha256'] == args.expected_agda_sha256 and
            prior['machine'] == machine, 'same pinned desktop compiler required')
    pool = pinned(baseline / 'results/indexed-cache-mode6/interface-map.json', args.expected_baseline_map_sha256)
    require(assembly6.interfaces(old) == pool and digest_entries(pool) == prior['last_interface_pool_sha256'],
            'baseline interface cache changed')
    targets = ['Part60', 'Part120']
    require([p['target'] for p in prior['phases']] == targets, 'exact measured baseline targets required')
    originals = {}
    direct_sources = set()
    own_interfaces = {}
    for phase in prior['phases']:
        record = phase['record']
        require(record['accepted'] and record['source_unchanged'] and record['expected_source_matches'] and
                record['source_sha256'] == old_source['source_sha256'] and
                record['machine'] == machine['hostname'] and record['executable_sha256'] == machine['agda_sha256'] and
                '--save-metas' in record['argv'] and record['peak_rss_gib'] <= 1.5,
                'unauthenticated baseline row check')
        target = phase['target']
        name = 'src/' + PREFIX.replace('.', '/') + '/' + target + '.agda'
        original = (old / name).read_text()
        require(original.startswith('{-# OPTIONS --safe --without-K --cubical-compatible ' + WARNING + ' #-}'),
                'baseline optional warning pragma differs')
        originals[target] = original
        for dependency in re.findall(r'^import (Tests\.IndexedWire6\.[A-Za-z0-9]+)', original, re.M):
            require(not dependency.split('.')[-1].startswith('Part'), 'baseline imports a proof')
            direct_sources.add('src/' + dependency.replace('.', '/') + '.agda')
        suffix = '/' + PREFIX.replace('.', '/') + '/' + target + '.agdai'
        names = [n for n in pool if n.endswith(suffix)]
        require(len(names) == 1, 'baseline own interface missing')
        own_interfaces[target] = dict(path=names[0], sha256=pool[names[0]], bytes=(old / names[0]).stat().st_size,
                                      record=record)
    borrowed = {n: h for n, h in pool.items() if '/Tests/' not in n or
                n.split('/agda/', 1)[1][:-1] in direct_sources}
    sources = borrowed_sources(borrowed)
    require(direct_sources <= sources and all('/Part' not in n for n in borrowed), 'incomplete data-only cache selection')
    projected = sum(((old / n).stat().st_size + 4095) // 4096 * 4096 for n in sources)
    projected += sum((old / n).stat().st_blocks * 512 for n in borrowed)
    report = dict(format='othello-indexed-family6-v1', accepted=False, status='preparing', created_utc=utc(),
                  machine=machine, baseline_report_sha256=args.expected_baseline_report_sha256,
                  baseline_map_sha256=args.expected_baseline_map_sha256, baselines=own_interfaces,
                  phases=[], kernel_cpu_seconds=0., initial_problem2_proved=False,
                  optimal_initial_pair_proved=False, production_authorized=False,
                  scope='two real data-only row parts; no global or initial theorem',
                  interface_policy='same-machine/compiler/save-metas; data/generic copy2; no part proof borrowed')
    report['redundant_rewrite_warning_filter'] = '-WnoRewritesNothing' if args.no_rewrite_warnings else None
    def save(): atomic_json(out / 'report.json', report)
    def guard(extra=0):
        used = allocated(current.parent)
        free = shutil.disk_usage(current.parent).free
        report['last_storage_gate'] = dict(allocated_study_bytes=used, free_bytes=free, checked_utc=utc())
        save()
        require(used + extra < 10 * 2**30 and free - extra >= 100 * 2**30, 'storage cap reached; baseline preserved')
    guard(projected + 4 * 2**20)
    check = out / 'check'
    check.mkdir()
    shutil.copy2(old / 'othello.agda-lib', check / 'othello.agda-lib')
    for name in sorted(sources):
        path = check / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old / name, path)
    for name, digest in borrowed.items(): copy_interface(old / name, check / name, digest)
    for target, original in originals.items():
        path = check / ('src/' + PREFIX.replace('.', '/') + '/' + target + '.agda')
        path.parent.mkdir(parents=True, exist_ok=True)
        text=shared_part(original)
        if args.no_rewrite_warnings:
            text=text.replace(WARNING+' #-}',WARNING+' -WnoRewritesNothing #-}',1)
        path.write_text(text)
    family = check / ('src/' + PREFIX.replace('.', '/') + '/Family.agda')
    text=shared_instance(originals['Part60'])
    if args.no_rewrite_warnings:
        text=text.replace(WARNING+' #-}',WARNING+' -WnoRewritesNothing #-}',1)
    family.write_text(text)
    source = source_identity(check)
    report.update(checked_source=source, borrowed_interfaces_sha256=digest_entries(borrowed),
                  borrowed_interfaces=len(borrowed), projected_private_bytes=projected)
    save()
    for index, target in enumerate(['Family', *targets]):
        guard()
        before = assembly6.interfaces(check)
        suffix = '/' + PREFIX.replace('.', '/') + '/' + target + '.agdai'
        require(not any(n.endswith(suffix) for n in before), 'own target is warm')
        left = args.kernel_cpu_limit - report['kernel_cpu_seconds']
        require(left >= 1, 'nested kernel cap reached; completed checks retained')
        argv = [args.agda, '--no-libraries', '-i', 'src', '--safe', '--without-K', '--cubical-compatible',
                '--save-metas', 'src/' + PREFIX.replace('.', '/') + '/' + target + '.agda',
                '+RTS', '-M1350M', '-c', '-s', '-RTS']
        record = run_job('target' + str(index), argv, out / 'records', root=check,
                         expected_source_sha256=source['source_sha256'], timeout=220, cpu_limit=min(100, left),
                         rss_limit_gib=1.5, log_limit_mib=2,
                         metadata=dict(target=target, own_target_cold=True, child_proof_imports=False,
                                       checker_instance_shared=True, local_warning_filter=WARNING))
        after = assembly6.interfaces(check)
        phase = dict(target=target, record=record, borrowed_interfaces_unchanged=all(after.get(n)==h for n,h in before.items()))
        report['phases'].append(phase)
        report['kernel_cpu_seconds'] += record['cpu_seconds']
        atomic_json(out / 'interface-map.json', after)
        report['last_interface_pool_sha256'] = digest_entries(after)
        save()
        require(phase['borrowed_interfaces_unchanged'] and record['accepted'], 'shared checker target failed: ' + target)
        names = [n for n in after if n.endswith(suffix)]
        require(len(names)==1, 'new own interface missing')
        phase['interface'] = dict(path=names[0], sha256=after[names[0]], bytes=(check / names[0]).stat().st_size)
        if target != 'Family':
            phase['baseline_to_shared_byte_ratio'] = own_interfaces[target]['bytes'] / phase['interface']['bytes']
        save()
    require(source_identity(old)==old_source and assembly6.interfaces(old)==pool, 'baseline sources or interfaces changed')
    report.update(accepted=True, status='complete', finished_utc=utc(), baseline_sources_and_interfaces_unchanged=True)
    save()
    print(json.dumps({'accepted': True, 'kernel_cpu_seconds': report['kernel_cpu_seconds'],
                      'own_interfaces': [p['interface'] for p in report['phases']]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'output'): parser.add_argument('--'+name, type=Path, required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-baseline-report-sha256', 'expected-baseline-map-sha256'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--kernel-cpu-limit', type=float, default=180.)
    parser.add_argument('--no-rewrite-warnings', action='store_true',
                        help='suppress only optional RewritesNothing warning documents in new modules')
    run(parser.parse_args())


if __name__ == '__main__': main()
