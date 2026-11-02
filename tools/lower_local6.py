#!/usr/bin/env python3
"""Safe generated pilot for the largest unproved training root's exact closure.

Only the layout changes: every retained certificate and reference is byte for
byte from the fixed factored sample. Old accepted targets are never retried.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import assembly6
from closed_roots6 import root_sources
import lower_pilot6 as pilot
from lower_local_plan6 import closure, describe
from provenance import digest_entries, source_identity
from run_job import atomic_json, utc


def generated_layout(plan, index):
    pilot.validate_plan(plan)
    if not isinstance(index, int) or not 2 <= index < 10:
        raise ValueError('requires an unproved training root; heldout roots stay untimed')
    root = plan['roots'][index]
    original, parts = root_sources(plan, root, index)
    prefix = f'Tests.LowerLocal6.Root{index}'
    directory = 'src/'+prefix.replace('.', '/')
    old = f'Tests.ClosedPilot6.Root{index}'
    sources = {}
    for name, text in original.items():
        filename = Path(name).name
        text = text.replace(old, prefix+'.Group0')
        sources[directory+'/Group0/'+filename] = (pilot.packed_part(text)
            if filename.startswith('Part') else pilot.local_options(text))
    collector = pilot.collector_source([root], {root: (prefix+'.Group0.Check', 'guarantee0')})
    sources[directory+'/AllLower.agda'] = collector.replace(pilot.PREFIX, prefix)
    sources[directory+'/Negative.agda'] = pilot.negative_source().replace(pilot.PREFIX, prefix)
    entries = closure(plan['entries'], [root])
    return dict(sources=sources, groups=[dict(index=0, roots=[root], parts=len(parts), entries=len(entries))],
        roots=[root], directory=directory, root_index=index,
        partition=dict(max_tokens=32000, max_entries=150),
        scope='one largest unproved training root: White lower +4 under ORIGINAL Rules.game six',
        original_heldout_indices=list(range(10, 20)), original_heldout_kernel_unmeasured=True,
        certificate_and_reference_bytes_unchanged=True,
        old_accepted_targets_retried=False, transitive_layout=describe(entries))


def analysis_guard(path, plan, plan_sha):
    data = json.loads(path.read_text())
    if (data['format'] != 'othello-lower-local-plan6-v1' or data['status'] != 'complete' or
            data['plan_sha256'] != plan_sha or not data['heldout_group_kernel_unmeasured']):
        raise ValueError('different predeclared sample or analysis')
    index = data['largest_unproved_training_index']
    candidates = [row for row in data['cases'] if row['training'] and not row['already_checked_root']]
    chosen = max(candidates, key=lambda row: (row['maximum_imported_entries'], row['entries'], -row['index']))
    if index != chosen['index'] or chosen['state'] != plan['roots'][index]:
        raise ValueError('stress selection differs')
    actual = describe(closure(plan['entries'], [plan['roots'][index]]))
    if any(actual[key] != chosen[key] for key in actual):
        raise ValueError('root-local closure differs from its declaration')
    previous = Path(data['previous'])
    if (assembly6.sha(previous/'final.json') != data['previous_report_sha256'] or
            assembly6.sha(previous/'phase-records.json') != data['previous_audit_sha256'] or
            source_identity(previous/'check')['source_sha256'] != data['previous_source_sha256'] or
            digest_entries(assembly6.interfaces(previous/'check')) != data['previous_interfaces_sha256']):
        raise ValueError('old accepted prefix changed')
    return data, index


def preflight(args):
    plan_sha = assembly6.sha(args.plan)
    plan = json.loads(args.plan.read_text())
    provenance = json.loads(args.provenance.read_text())
    pilot.validate_provenance(plan, provenance, plan_sha)
    analysis, index = analysis_guard(args.analysis, plan, plan_sha)
    layout = generated_layout(plan, index)
    hashes = pilot.source_hashes(layout['sources'])
    identity = source_identity(args.donor)
    interfaces = assembly6.interfaces(args.donor)
    generic = pilot.generic_interfaces(interfaces)
    machine = assembly6.machine_identity(args.agda)
    if (identity['source_sha256'] != 'ecf3b080d1808ee364b102610981e84e3397068159f5dd40caeba07a065097a0' or
            identity['agda_source_sha256'] != '9fde9b4dc22bb602e89ebb3bc1a29a5f56d5d0cdddaffffe5baa08d5d26618ec' or
            digest_entries(interfaces) != 'bea149de03ae625d6f9996d033fc6a65b99a0ae6ef825c5a081d4e799cba4ee1' or
            machine['agda_sha256'] != 'c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842'):
        raise ValueError('original machine/compiler/donor changed')
    result = dict(format='othello-lower-local-preflight6-v1', status='complete', created_utc=utc(),
        plan_sha256=plan_sha, provenance_sha256=assembly6.sha(args.provenance),
        analysis_sha256=assembly6.sha(args.analysis), root_index=index,
        root=plan['roots'][index], modules=len(hashes), source_hashes=hashes,
        generated_sha256=digest_entries(hashes),
        generated_source_bytes=sum(len(text.encode()) for text in layout['sources'].values()),
        generic_bytes=sum((args.donor/name).stat().st_size for name in generic),
        donor_source_sha256=identity['source_sha256'], donor_agda_source_sha256=identity['agda_source_sha256'],
        donor_interfaces_sha256=digest_entries(interfaces), agda_sha256=machine['agda_sha256'],
        agda_path=machine['agda_path'], layout={key: value for key, value in layout.items() if key != 'sources'},
        heldout_unmeasured=True, initial_problem2_proved=False, production_authorized=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, result)
    print(json.dumps({key: result[key] for key in ('status', 'root_index', 'root', 'modules',
        'generated_source_bytes', 'generic_bytes', 'generated_sha256')}))


def main():
    import sys
    mode, argv = sys.argv[1], sys.argv[2:]
    if mode == 'preflight':
        p = argparse.ArgumentParser(description=__doc__)
        for name in ('analysis', 'plan', 'provenance', 'donor', 'output'):
            p.add_argument('--'+name, type=Path, required=True)
        p.add_argument('--agda', required=True)
        preflight(p.parse_args(argv))
    elif mode == 'run':
        p = pilot.parser()
        p.add_argument('--analysis', type=Path, required=True)
        p.add_argument('--expected-analysis-sha256', required=True)
        args = p.parse_args(argv)
        pilot.expected_hash(assembly6.sha(args.analysis), args.expected_analysis_sha256, 'analysis')
        plan_sha = assembly6.sha(args.plan)
        plan = json.loads(args.plan.read_text())
        pilot.expected_hash(plan_sha, args.expected_plan_sha256, 'plan')
        analysis, index = analysis_guard(args.analysis, plan, plan_sha)
        layout = generated_layout(plan, index)
        layout.update(analysis_sha256=args.expected_analysis_sha256,
            previous_source_sha256=analysis['previous_source_sha256'],
            previous_interfaces_sha256=analysis['previous_interfaces_sha256'])
        report = pilot.run(args, layout=layout)
        previous = Path(analysis['previous'])/'check'
        unchanged = (source_identity(previous)['source_sha256'] == analysis['previous_source_sha256'] and
            digest_entries(assembly6.interfaces(previous)) == analysis['previous_interfaces_sha256'] and
            assembly6.sha(args.analysis) == args.expected_analysis_sha256)
        atomic_json(args.output/'old-prefix-guard.json', dict(unchanged=unchanged,
            source_sha256=analysis['previous_source_sha256'], interfaces_sha256=analysis['previous_interfaces_sha256']))
        raise SystemExit(0 if report['accepted'] and unchanged else 2)
    else:
        raise SystemExit('expected preflight or run')


if __name__ == '__main__':
    main()
