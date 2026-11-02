#!/usr/bin/env python3
"""A bounded A/B test of explicit large arguments in accepted shard proofs.

Generated targets stay in frozen results roots. The original certificate data,
Boolean checks, state-equality proof and imported facts are unchanged. Writable
interfaces are always private copies on the original checking machine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface, selected_interfaces
import compact_shared6 as compact
import global_assembly6 as assembly
from interface_census6 import census_file
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job

PREFIX = 'Tests.ExplicitPilot6'


def explicit_source(original, name='Explicit25'):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*', name):
        raise ValueError('invalid pilot module name')
    required = ('  shape = refl\n', '  accepted = refl\n',
                '  sound = subst (AllT (Proven Fast.fastGame6 black (upperGoal 4))) shape\n',
                'export = checkedExport states sound\n')
    if any(original.count(text) != 1 for text in required):
        raise ValueError('unexpected accepted proof template')
    changed, count = re.subn(r'^module Tests\.Unattended6\.Group6\.Part25 where$',
                             f'module {PREFIX}.{name} where', original, flags=re.M)
    if count != 1 or '--save-metas --safe --without-K --cubical-compatible' not in changed:
        raise ValueError('requires the selected original saved-meta safe shard')
    changed = changed.replace(required[0], '  shape = refl {x = states}\n')
    changed = changed.replace(required[1], '  accepted = refl {x = true}\n')
    changed = changed.replace(required[2],
        '  sound = subst {A = Trie (State six)}\n'
        '    (AllT (Proven Fast.fastGame6 black (upperGoal 4)))\n'
        '    {x = shardStates keyed6 entries} {y = states} shape\n')
    changed = changed.replace(required[3],
        'export = checkedExport {S = State six} {g = Fast.fastGame6}\n'
        '  {p = black} {goal = upperGoal 4} states sound\n')
    return changed


def packed_source(original, name='Tables25'):
    """Encode routing keys and export states using the existing checked codec.

    The dummy L certificates below are used only to parse lists of states;
    they are never proof evidence. The original entry certificates and both
    refl proof obligations remain in the generated module.
    """
    return pack_tables(explicit_source(original,name))


def pack_tables(original):
    """Only replace literal routing/state expressions; leave proofs intact."""
    changed = original
    helper = '''importKeys : String → List (List Bool)
importKeys text = map (λ e → key6 (entryState e))
  (fromMaybe [] (decodeCompactEntries text))

'''
    old_imports = original.split('\nimports = ',1)[1].split('\n',1)[0]

    def pack_keys(match):
        body,owner = match.groups()
        codes = re.findall(r'key6 \(decode "([^"]+)"\)',body)
        expected = ' ∷ '.join(f'key6 (decode "{code}")' for code in codes)+' ∷ []'
        if not codes or body != expected or len(set(codes)) != len(codes):
            raise ValueError('unexpected import-key expression')
        for code in codes:compact.unpack_state(code)
        wire = ''.join(code+'L' for code in codes)
        return f'selectExport (importKeys "{wire}") {owner}.export'

    imports,count = re.subn(r'selectExport \((.*?)\) (P\d+)\.export',pack_keys,old_imports)
    if (count == 0 and old_imports != '[]') or 'key6 (decode ' in imports:
        raise ValueError('unexpected literal import table')
    if count:
        changed = changed.replace('\nimports :', '\n'+helper+'imports :',1)
    changed = changed.replace('\nimports = '+old_imports+'\n','\nimports = '+imports+'\n',1)
    old_states = original.split('\nstates = ',1)[1].split('\n',1)[0]
    codes = re.findall(r'insertT \(key6 \(decode "([^"]+)"\)\) \(decode "\1"\)',old_states)
    expected = 'tip'
    for code in reversed(codes):
        compact.unpack_state(code)
        expected = f'insertT (key6 (decode "{code}")) (decode "{code}") ({expected})'
    if not codes or old_states != expected:
        raise ValueError('unexpected export-state expression')
    wire = ''.join(code+'L' for code in codes)
    states = f'shardStates keyed6 (fromMaybe [] (decodeCompactEntries "{wire}"))'
    changed = changed.replace('\nstates = '+old_states+'\n','\nstates = '+states+'\n',1)
    return changed


def run(args):
    previous = args.previous.resolve()
    donor = previous/'collector'
    audit = json.loads((previous/'phase-records.json').read_text())
    final = json.loads((previous/'final.json').read_text())
    machine = assembly6.machine_identity(args.agda)
    identity = source_identity(donor)
    pool = audit['collector_interfaces']
    if (assembly6.sha(previous/'final.json') != audit['final_sha256'] or
            final['status'] != 'collector-failed' or final['accepted'] or
            final['completed_groups'] != list(range(10)) or
            final['checked_regrouped_upper_roots'] != 100 or machine != final['machine'] or
            identity['source_sha256'] != final['source_sha256'] or interfaces_changed(donor,pool)):
        raise ValueError('requires the verified completed sample on its original machine/binary')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = output/'check'; root.mkdir()
    for name,_ in source_files(donor):
        assembly.hardlink(donor/name, root/name)  # Immutable sources only.
    original_path = 'src/Tests/Unattended6/Group6/Part25.agda'
    stem = 'Tables25' if args.representation == 'tables' else 'Explicit25'
    target = f'src/Tests/ExplicitPilot6/{stem}.agda'
    generate = packed_source if args.representation == 'tables' else explicit_source
    changed = generate((donor/original_path).read_text())
    path = root/target;path.parent.mkdir(parents=True);path.write_text(changed)
    probes = {
        'ImportsBaseline': 'Tests.Unattended6.Group6.Part25',
        'ImportsExplicit': PREFIX+'.'+stem,
    }
    for name,module in probes.items():
        (path.parent/f'{name}.agda').write_text(
            assembly.HEADER.replace('--safe ', '--save-metas --safe ', 1)+
            f'module {PREFIX}.{name} where\n\nimport {module}\n')
    manifest = bench6.refresh_manifest(root, origin={k:identity[k] for k in ('revision','dirty')})
    for name,digest in selected_interfaces(pool,6).items():
        copy_interface(donor/name, root/name, digest)
    report = dict(format='othello-explicit-exports6-v1', status='running', accepted=False,
                  scope='one representative upper-only shard; no initial-board theorem',
                  selected_original_part='Group6/Part25', machine=machine,
                  representation=args.representation,
                  original_source_sha256=identity['source_sha256'],
                  source_sha256=manifest['source_sha256'], phases=[],
                  original_interface=None, explicit_interface=None,
                  initial_problem2_proved=False, production_authorized=False)
    spent = 0.0

    def save():
        atomic_json(output/'explicit.json',report)

    def check(label,target,cap=120):
        nonlocal spent
        before = assembly6.interfaces(root)
        suffix = '/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'
        if any(name.endswith(suffix) for name in before):
            raise ValueError('pilot target is not cold')
        if assembly6.machine_identity(args.agda) != machine:
            raise ValueError('compiler changed')
        record = run_job(label,[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
            '+RTS','-M1350M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=cap,timeout=cap*3,
            rss_limit_gib=1.5,log_limit_mib=2,
            metadata={'machine':machine,'own_target_cold':True,
                      'borrowed_interfaces_sha256':digest_entries(before),
                      'interface_isolation':'private inode copies'})
        spent += record['cpu_seconds']
        after = assembly6.interfaces(root)
        changes = [name for name,digest in before.items() if after.get(name) != digest]
        metric = assembly.metrics(record)
        metric.update(label=label,target=target,exit_code=record['exit_code'],
                      cache_changes=changes,
                      rts=rts_stats((output/'records'/f'{label}.log').read_text()))
        if changes or interfaces_changed(donor,pool) or source_identity(donor) != identity:
            raise ValueError('a verified dependency changed')
        report['phases'].append(metric)
        report['measured_kernel_cpu_seconds'] = spent
        save();print(json.dumps(metric),flush=True)
        return record,after

    save()
    record,after = check('explicit-part25',target)
    if record['accepted']:
        old_name = next(name for name in pool if name.endswith('/Group6/Part25.agdai'))
        new_name = next(name for name in after if name.endswith(f'/ExplicitPilot6/{stem}.agdai'))
        report['original_interface'] = census_file(donor/old_name,pool[old_name])
        report['explicit_interface'] = census_file(root/new_name,after[new_name])
        for name in probes:
            record,_ = check(name,f'src/Tests/ExplicitPilot6/{name}.agda',60)
            if not record['accepted']:
                report['status'] = 'import-probe-failed';break
        else:
            report['status'] = 'complete';report['accepted'] = True
    else:
        report['status'] = 'part-failed'
    report['donor_sources_unchanged'] = source_identity(donor) == identity
    report['donor_interfaces_unchanged'] = not interfaces_changed(donor,pool)
    save()
    records = {phase['label']:json.loads((output/'records'/f"{phase['label']}.json").read_text())
               for phase in report['phases']}
    atomic_json(output/'phase-records.json',dict(records=records,
        record_hashes={name:assembly6.sha(output/'records'/f'{name}.json') for name in records},
        log_hashes={name:assembly6.sha(output/'records'/f'{name}.log') for name in records},
        generated_sources={name:assembly6.sha(root/name) for name in manifest['files']
                           if name.startswith('src/Tests/ExplicitPilot6/')},
        final_interfaces=assembly6.interfaces(root)))


def interfaces_changed(donor,pool):
    return assembly6.interfaces(donor) != pool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--agda',required=True)
    parser.add_argument('--representation',choices=('explicit','tables'),default='explicit')
    run(parser.parse_args())


if __name__ == '__main__':
    main()
