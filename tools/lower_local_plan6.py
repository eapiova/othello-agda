#!/usr/bin/env python3
"""Describe exact root-local closures of the fixed lower sample, without Agda."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import assembly6
import global_assembly6 as assembly
from lower_pilot6 import validate_plan
from provenance import digest_entries, source_identity
from run_job import atomic_json, utc


def closure(entries, roots):
    by_state = {entry['state']: entry for entry in entries}
    seen, todo = set(), list(roots)
    while todo:
        state = todo.pop()
        if state not in seen:
            seen.add(state)
            todo.extend(by_state[state]['references'])
    return [entry for entry in entries if entry['state'] in seen]


def describe(entries, max_tokens=32000, max_entries=150):
    parts, owners = assembly.partition(entries, max_tokens, max_entries)
    ancestors, rows = [], []
    for index, part in enumerate(parts):
        direct = {owners[state] for entry in part for state in entry['references']
                  if owners[state] != index}
        inherited = set(direct)
        for parent in direct:
            inherited.update(ancestors[parent])
        ancestors.append(inherited)
        rows.append(dict(index=index, own_entries=len(part),
            tokens=sum(assembly.tokens(entry['certificate']) for entry in part),
            dependencies=sorted(direct), transitive_parts=len(inherited),
            imported_entries=sum(len(parts[parent]) for parent in inherited)))
    return dict(entries=len(entries), parts=len(parts),
        tokens=sum(row['tokens'] for row in rows),
        maximum_imported_entries=max(row['imported_entries'] for row in rows), rows=rows)


def run(args):
    previous = args.previous.resolve()
    old = json.loads((previous/'final.json').read_text())
    audit = json.loads((previous/'phase-records.json').read_text())
    pool = assembly6.interfaces(previous/'check')
    if (old['status'] != 'part-failed' or old['last_attempted_check']['label'] != 'group0-part122' or
            source_identity(previous/'check')['source_sha256'] != old['source_sha256'] or
            pool != audit['final_interfaces'] or len(pool) != 154 or
            audit['final_sha256'] != assembly6.sha(previous/'final.json') or
            audit['lower_sha256'] != assembly6.sha(previous/'lower.json')):
        raise ValueError('different checked lower prefix')
    plan_sha = assembly6.sha(args.plan)
    if plan_sha != old['plan_sha256']:
        raise ValueError('different fixed lower sample')
    plan = json.loads(args.plan.read_text())
    validate_plan(plan)
    group0 = closure(plan['entries'], plan['roots'][:10])
    old_parts, old_owners = assembly.partition(group0, 32000, 150)
    known = {state for state, owner in old_owners.items() if owner < 122}
    cases = []
    for index, root in enumerate(plan['roots']):
        entries = closure(plan['entries'], [root])
        stats = describe(entries)
        stats.update(index=index, state=root, training=index < 10,
            already_checked_root=root in known,
            already_checked_entries=sum(entry['state'] in known for entry in entries),
            unproved_entries=sum(entry['state'] not in known for entry in entries))
        cases.append(stats)
    training = [row for row in cases[:10] if not row['already_checked_root']]
    # A stress case is selected by layout features, never kernel timings.
    largest = max(training, key=lambda row: (row['maximum_imported_entries'], row['entries'], -row['index']))
    result = dict(format='othello-lower-local-plan6-v1', status='complete', created_utc=utc(),
        plan=str(args.plan), plan_sha256=plan_sha, previous=str(previous),
        previous_report_sha256=assembly6.sha(previous/'final.json'),
        previous_audit_sha256=assembly6.sha(previous/'phase-records.json'),
        previous_source_sha256=old['source_sha256'], previous_interfaces_sha256=digest_entries(pool),
        cases=cases, largest_unproved_training_index=largest['index'],
        choice_rule='maximum root-local transitive imported entries among unproved training roots; ties by closure size, then index',
        group0=describe(group0), failed_part_entries=[entry['state'] for entry in old_parts[122]],
        accepted_parts_untouched=True, heldout_group_kernel_unmeasured=True,
        description_is_untrusted=True, initial_problem2_proved=False, production_authorized=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output, result)
    print(json.dumps(dict(status='complete', largest_training_index=largest['index'],
        cases=[{key: row[key] for key in ('index', 'entries', 'parts', 'tokens',
            'maximum_imported_entries', 'already_checked_root', 'already_checked_entries', 'unproved_entries')}
               for row in cases])))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'previous', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    run(p.parse_args())
