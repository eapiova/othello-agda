#!/usr/bin/env python3
"""Continue fixed lower training using accepted warning-filtered exports.

Original certificates, goals, complete citation checks and Rules transfer are
preserved. Only namespaces, private import scopes and local warning output
change. No holdout target is checked by this driver.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import global_assembly6 as assembly
import owner_closure6 as closure
import owner_cuts6 as cuts
import rewrite_owners6 as owners
import rewrite_filter6 as filtered
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, positive, run_job, utc

PREFIX = 'Tests.RewriteTraining6'
DIRECTORY = 'src/Tests/RewriteTraining6'
TRAINING = [6, 7, 8, 9]
HELDOUT = list(range(10, 20))


def verified_donor(args):
    _, original, original_identity, original_pool, machine = cuts.verified_donor(
        args.original.resolve(), args.expected_original_sha256, args.agda)
    previous = args.previous.resolve()
    if assembly6.sha(previous/'final.json') != args.expected_previous_sha256:
        raise ValueError('complete root5 report differs')
    report = json.loads((previous/'final.json').read_text())
    root = Path(report['check_root'])
    identity, pool = source_identity(root), assembly6.interfaces(root)
    expected, targets, _ = owners.generated(original)
    if (report['format'] != 'othello-rewrite-owners6-v1' or report['status'] != 'complete' or
            not report['accepted'] or report['checked_sample_lower_roots'] != 6 or
            report['previous_report_sha256'] != args.expected_original_sha256 or
            report['machine'] != machine or not report['donor_unchanged'] or
            not report['prefix_donor_unchanged'] or not report['generated_sources_unchanged'] or
            report['certificate_parts_rechecked'] or report['postulates'] or
            report['initial_problem2_proved'] or report['heldout_measured'] or report['production_authorized'] or
            report['generated_source_hashes'] != cuts.pilot.source_hashes(expected) or
            identity['source_sha256'] != report['source_sha256'] or pool != report['final_interfaces'] or
            digest_entries(pool) != report['interfaces_sha256'] or len(pool) != 308 or
            any(assembly6.sha(root/name) != digest for name, digest in report['generated_source_hashes'].items())):
        raise ValueError('requires unchanged safe complete root5, certificates and compiler')
    staging = report['reused_generic_prefix']
    staging_root = Path(staging['root'])
    if (source_identity(staging_root) != staging['identity'] or
            assembly6.interfaces(staging_root) != staging['interfaces'] or
            staging['interfaces'] != report['borrowed_interfaces'] or
            assembly6.sha(Path(staging['previous'])/'final.json') != staging['report_sha256']):
        raise ValueError('checked prefix staging or its pinned report changed')
    before = dict(report['borrowed_interfaces'])
    for phase, (name, _, _) in zip(report['phases'], targets, strict=True):
        record = phase['record']
        receipt = previous/'records'/(name+'.json')
        packed = phase['archived_log']
        archive_path = previous/'records'/packed['archive_name']
        raw = gzip.decompress(archive_path.read_bytes())
        if (phase['label'] != name or not phase['expected_outcome_met'] or not record['accepted'] or
                record['stop_reason'] or phase['cache_changes'] or phase['unexpected_interfaces'] or
                len(phase['own_interfaces']) != 1 or record['borrowed_interfaces_sha256'] != digest_entries(before) or
                record['source_sha256'] != report['source_sha256'] or not record['source_unchanged'] or
                not record['expected_source_matches'] or not record['own_target_cold'] or
                record['executable_sha256'] != machine['agda_sha256'] or
                not all(flag in record['argv'] for flag in assembly6.FLAGS+['--save-metas', '-M2500M']) or
                record['rss_stop_threshold_gib'] != 3 or assembly6.sha(receipt) != phase['record_sha256'] or
                json.loads(receipt.read_text()) != record or assembly6.sha(archive_path) != packed['archive_sha256'] or
                hashlib.sha256(raw).hexdigest() != phase['raw_log_sha256'] or len(raw) != record['log_bytes']):
            raise ValueError('root5 phase receipt or log differs')
        before.update(phase['own_interfaces'])
    if before != pool:
        raise ValueError('unrecorded complete-owner interface')
    # All twelve conditional parts were previously accepted. New bindings
    # import these exact original names and receive private interface copies.
    extra_modules = [f'Tests.IndependentLower6.Part{j}' for j in (115, 116, 117)]
    extra_modules += [f'Tests.OwnerLower6.Root{i}.Part{j}' for i, n in ((2, 4), (3, 5)) for j in range(n)]
    extra = {'_build/2.9.0/agda/src/'+m.replace('.', '/')+'.agdai':
        original_pool['_build/2.9.0/agda/src/'+m.replace('.', '/')+'.agdai'] for m in extra_modules}
    for name, digest in extra.items():
        source = 'src/'+name.split('/agda/src/', 1)[1].removesuffix('.agdai')+'.agda'
        if (assembly6.sha(original/name) != digest or
                (original/source).read_bytes() != (root/source).read_bytes()):
            raise ValueError('accepted conditional certificate differs')
    return original, original_identity, original_pool, root, identity, pool, extra, machine


def rename(text, mapping):
    pattern = re.compile('|'.join(re.escape(s) for s in sorted(mapping, key=len, reverse=True)))
    changed = pattern.sub(lambda m: mapping[m[0]], text)
    reverse = {v: k for k, v in mapping.items()}
    if len(reverse) != len(mapping):
        raise ValueError('namespace mapping is not reversible')
    restoration = re.compile('|'.join(re.escape(s) for s in sorted(reverse, key=len, reverse=True)))
    if restoration.sub(lambda m: reverse[m[0]], changed) != text:
        raise ValueError('non-namespace change')
    return changed


def local_warning(text):
    if filtered.WARNING in text or text.count(' -WnoUnsupportedIndexedMatch #-}') != 1:
        raise ValueError('original local warning options differ')
    return text.replace(' -WnoUnsupportedIndexedMatch #-}',
        ' -WnoUnsupportedIndexedMatch '+filtered.WARNING+' #-}', 1)


def private_bindings(text, module, chosen=None, extra_private=''):
    parts, aliases, routing = closure.blocks(text)
    chosen = sorted(parts) if chosen is None else chosen
    body = '\n'.join(parts[j] for j in chosen)
    selected = {alias: name for alias, name in aliases.items()
        if re.search(r'(?<![A-Za-z0-9_])'+re.escape(alias)+r'\.', body)}
    common = {alias: name for name, alias in closure.IMPORT.findall(assembly.COMMON)}
    private = assembly.COMMON+'open import Tests.DirectCitations6.Coverage using (coveredBy; coveredBy-sound)\n'
    private += ''.join(f'import {name} as {alias}\n' for alias, name in sorted(selected.items())
        if common.get(alias) != name)+'\n'+extra_private+routing
    head = local_warning(cuts.pilot.local_options(assembly.HEADER+f'module {module} where\n\n'))
    result = head+'private\n'+''.join('  '+line+'\n' if line else '\n' for line in private.splitlines())+'\n'+body
    if re.findall(r'"([^"\n]*)"', result) != re.findall(r'"([^"\n]*)"', body):
        raise ValueError('routing literals changed while hiding imports')
    return result


def generated(args, original):
    if assembly6.sha(args.preflight) != args.expected_preflight_sha256:
        raise ValueError('fixed original preflight differs')
    declared = json.loads(args.preflight.read_text())
    if (declared['format'] != 'othello-owner-lower6-preflight-v1' or
            declared['heldout_indices'] != HELDOUT or not declared['heldout_declared_before_checks']):
        raise ValueError('requires the original predeclared training/holdout')
    differences = {name: dict(preflight_sha256=digest, current_sha256=assembly6.sha(original/name))
        for name, digest in declared['source_hashes'].items() if assembly6.sha(original/name) != digest}
    # The already audited split replaced this failed combined binding with an
    # unchecked facade. It is never imported here: the accepted replacement
    # owners get a fresh facade. All actual training/holdout inputs must agree.
    retired = 'src/Tests/OwnerLower6/Root5/Assemble6.agda'
    if set(differences) != {retired}:
        raise ValueError('unexpected preflight source differences: '+repr(sorted(differences)))
    declared['retired_source_differences'] = differences
    mapping = {filtered.OLD: filtered.PREFIX,
        'Tests.LowerLocal6.Root4.Group0': 'Tests.RewriteLocal6',
        'Tests.DirectCitations6.Root': PREFIX+'.Root4'}
    for i, n in ((2, 1), (3, 2)):
        for j in range(n):
            mapping[f'Tests.OwnerLower6.Root{i}.Assemble{j}'] = f'{PREFIX}.Root{i}.Assemble{j}'
    for j in range(6):
        mapping[f'Tests.OwnerLower6.Root5.Assemble{j}'] = f'{owners.PREFIX}.R5Assemble{j}'
    mapping['Tests.OwnerLower6.Root5.Assemble6'] = PREFIX+'.Root5.Assemble6'
    for i in TRAINING+HELDOUT:
        mapping[f'Tests.OwnerLower6.Root{i}'] = f'{PREFIX}.Root{i}'
    sources, repairs = {}, []
    suffix = private_bindings(rename((original/'src/Tests/DirectCitations6/Root.agda').read_text(), mapping),
        PREFIX+'.R4Suffix', chosen=[115, 116, 117],
        extra_private=f'import {owners.PREFIX}.R4P114 as Earlier\nmodule P114 = Earlier.P114\n')
    sources[f'{DIRECTORY}/R4Suffix.agda'] = suffix
    repairs.append(dict(label='rebind-r4-suffix', target=f'{DIRECTORY}/R4Suffix.agda',
        kind='rebind', heap_mib=2500, rss_gib=3, cpu_cap=180))
    head = local_warning(cuts.pilot.local_options(assembly.HEADER+f'module {PREFIX}.Root4 where\n\n'))
    sources[f'{DIRECTORY}/Root4.agda'] = head+f'''private
  import {owners.PREFIX}.R4P114 as A
  import {PREFIX}.R4Suffix as B

module P114 = A.P114
module P115 = B.P115
module P116 = B.P116
module P117 = B.P117
'''
    repairs.append(dict(label='rebind-r4-facade', target=f'{DIRECTORY}/Root4.agda',
        kind='rebind', heap_mib=2500, rss_gib=3, cpu_cap=60))
    for i, n in ((2, 1), (3, 2)):
        for j in range(n):
            name = f'{DIRECTORY}/Root{i}/Assemble{j}.agda'
            old = original/f'src/Tests/OwnerLower6/Root{i}/Assemble{j}.agda'
            sources[name] = private_bindings(rename(old.read_text(), mapping), f'{PREFIX}.Root{i}.Assemble{j}')
            repairs.append(dict(label=f'rebind-r{i}-assembly{j}', target=name,
                kind='rebind', heap_mib=2500, rss_gib=3, cpu_cap=180))
    head = local_warning(cuts.pilot.local_options(assembly.HEADER+f'module {PREFIX}.Root5.Assemble6 where\n\n'))
    sources[f'{DIRECTORY}/Root5/Assemble6.agda'] = head+'private\n'+''.join(
        f'  import {owners.PREFIX}.R5Part{j} as A{j}\n' for j in (24, 25, 26))+'\n'+''.join(
        f'module P{j} = A{j}.P{j}\n' for j in (24, 25, 26))
    repairs.append(dict(label='rebind-r5-facade', target=f'{DIRECTORY}/Root5/Assemble6.agda',
        kind='rebind', heap_mib=2500, rss_gib=3, cpu_cap=60))
    rows = []
    for row in declared['rows']:
        if row['index'] not in TRAINING+HELDOUT:
            continue
        phases = []
        for phase in row['phases']:
            old = (original/phase['target']).read_text()
            name = phase['target'].replace('src/Tests/OwnerLower6', DIRECTORY, 1)
            if phase['kind'] == 'assembly':
                module = name[4:-5].replace('/', '.')
                text = private_bindings(rename(old, mapping), module)
            else:
                text = local_warning(rename(old, mapping))
            if re.findall(r'"([^"\n]*)"', text) != re.findall(r'"([^"\n]*)"', old):
                raise ValueError('literal certificates or citation hints changed')
            sources[name] = text
            phases.append(dict(phase, target=name))
        rows.append(dict(row, phases=phases))
    return sources, repairs, rows, declared


def prepare(args):
    original, _, _, _, _, _, _, _ = verified_donor(args)
    sources, repairs, rows, declared = generated(args, original)
    sources_hashes = cuts.pilot.source_hashes(sources)
    active_imports = {name: closure.LEXICAL.findall(text) for name, text in sources.items()}
    if any(module.startswith((filtered.OLD, 'Tests.LowerLocal6.Root4.Group0',
            'Tests.DirectCitations6.Root')) for imported in active_imports.values() for module in imported):
        raise ValueError('old warning-heavy prefix import remains')
    report = dict(format='othello-rewrite-training6-layout-v1', created_utc=utc(),
        scope='unchecked generated layout; no Agda target run', accepted=False,
        previous_report_sha256=args.expected_previous_sha256,
        original_report_sha256=args.expected_original_sha256,
        original_preflight_sha256=args.expected_preflight_sha256,
        source_hashes=sources_hashes, generated_source_bytes=sum(len(t.encode()) for t in sources.values()),
        retired_source_differences=declared['retired_source_differences'], repairs=repairs,
        rows=rows, active_imports=active_imports, training_indices=TRAINING, heldout_indices=HELDOUT,
        heldout_measured=False, initial_problem2_proved=False, production_authorized=False)
    atomic_json(args.output, report)
    print(json.dumps({k: report[k] for k in ('scope', 'generated_source_bytes', 'training_indices', 'heldout_measured')}))


def run(args):
    original, original_identity, original_pool, donor, identity, pool, extra, machine = verified_donor(args)
    sources, repairs, rows, declared = generated(args, original)
    if not args.layout or not args.expected_layout_sha256 or assembly6.sha(args.layout) != args.expected_layout_sha256:
        raise ValueError('requires the pinned prospective layout before any training check')
    layout = json.loads(args.layout.read_text())
    if (layout['format'] != 'othello-rewrite-training6-layout-v1' or layout['accepted'] or
            layout['heldout_measured'] or layout['initial_problem2_proved'] or layout['production_authorized'] or
            layout['source_hashes'] != cuts.pilot.source_hashes(sources) or layout['rows'] != rows or
            layout['repairs'] != repairs or layout['retired_source_differences'] != declared['retired_source_differences']):
        raise ValueError('generated layout differs from the pinned precheck')
    output, runs = args.output.resolve(), args.runs_root.resolve()
    borrowed = {**pool, **extra}
    required = sum((donor/name if name in pool else original/name).stat().st_size for name in borrowed)
    required += sum(len(text.encode()) for text in sources.values())+32*1024**2
    if output.exists() or runs not in output.parents or not cuts.pilot.disk_allowed(cuts.pilot.disk_usage(runs), required):
        raise ValueError('fresh run root and unchanged storage headroom required')
    output.mkdir(parents=True)
    root = output/'check'; root.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor/name, root/name)
    for name, text in sources.items():
        path = root/name
        if path.exists():
            raise ValueError('fresh generated module already exists')
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
    for name, digest in borrowed.items():
        copy_interface(donor/name if name in pool else original/name, root/name, digest)
    manifest = bench6.refresh_manifest(root, origin={k: identity[k] for k in ('revision', 'dirty')})
    report = dict(format='othello-rewrite-training6-v1', status='checking', accepted=False,
        created_utc=utc(), previous=str(args.previous.resolve()), previous_report_sha256=args.expected_previous_sha256,
        original=str(args.original.resolve()), original_report_sha256=args.expected_original_sha256,
        original_preflight_sha256=args.expected_preflight_sha256, check_root=str(root), machine=machine,
        layout_sha256=args.expected_layout_sha256,
        source_sha256=manifest['source_sha256'], agda_source_sha256=source_identity(root)['agda_source_sha256'],
        borrowed_interfaces=borrowed, borrowed_interfaces_sha256=digest_entries(borrowed),
        generated_source_hashes=cuts.pilot.source_hashes(sources), rows=rows, repairs=repairs,
        training_indices=TRAINING, heldout_indices=HELDOUT, heldout_measured=False,
        completed_indices=[], phases=[], nested_cpu_seconds=0., nested_cpu_budget=args.kernel_cpu_budget,
        prior_checked_lower_roots=6, checked_sample_lower_roots=6,
        existing_conditional_parts_rechecked=0, new_certificate_parts_checked=0, postulates=0,
        initial_problem2_proved=False, production_authorized=False,
        literal_certificate_data_unchanged=True, warning_filter=filtered.WARNING,
        retired_source_differences=declared['retired_source_differences'])
    atomic_json(output/'preflight.json', report)
    selected = repairs+[dict(phase, root_index=row['index']) for row in rows if row['index'] in TRAINING for phase in row['phases']]
    for phase in selected:
        left = args.kernel_cpu_budget-report['nested_cpu_seconds']
        if left < 10 or not cuts.pilot.disk_allowed(cuts.pilot.disk_usage(runs), 16*1024**2):
            report['status'] = 'cpu-stop' if left < 10 else 'disk-stop'; break
        before = assembly6.interfaces(root)
        suffix = cuts.pilot.assert_cold(phase['target'], before, DIRECTORY)
        cap = min(phase['cpu_cap'], left-2)
        record = run_job(phase['label'], [machine['agda_path'], *assembly6.FLAGS, '--save-metas',
            '-v', 'tc.decl:10', '-i', 'src', phase['target'], '+RTS', f'-M{phase["heap_mib"]}M', '-c', '-s', '-RTS'],
            output/'records', root=root, expected_source_sha256=manifest['source_sha256'],
            cpu_limit=cap, timeout=cap*2+30, rss_limit_gib=phase['rss_gib'], log_limit_mib=8,
            metadata=dict(machine=machine, own_target_cold=True, timing_group='training',
                checker_kind=phase['kind'], borrowed_interfaces_sha256=digest_entries(before),
                existing_conditional_parts_rechecked=0))
        after = assembly6.interfaces(root)
        changes = cuts.pilot.cache_changes(before, after)
        own = {name: digest for name, digest in after.items() if name.endswith(suffix)}
        unexpected = [name for name in after if name not in before and name not in own]
        accepted = bool(record['accepted'] and len(own) == 1 and not changes and not unexpected and
            record['source_unchanged'] and record['expected_source_matches'] and
            record['executable_sha256'] == machine['agda_sha256'])
        path = output/'records'/(phase['label']+'.log')
        raw = path.read_text(); digest = assembly6.sha(path)
        packed = archive(path, digest) if accepted else None
        report['phases'].append(dict(phase, accepted=accepted, record=record,
            record_sha256=assembly6.sha(output/'records'/(phase['label']+'.json')),
            cache_changes=changes, unexpected_interfaces=unexpected, own_interfaces=own,
            raw_log_sha256=digest, archived_log=packed, rts=rts_stats(raw), declaration_tail=raw.splitlines()[-30:]))
        report['nested_cpu_seconds'] += record['cpu_seconds']
        if accepted and phase['kind'] == 'certificate':
            report['new_certificate_parts_checked'] += 1
        if accepted and phase['kind'] == 'root':
            report['completed_indices'].append(phase['root_index'])
            report['checked_sample_lower_roots'] += 1
        atomic_json(output/'running.json', report)
        if not accepted:
            report['status'] = 'cache-mismatch' if changes or unexpected else 'phase-failed'; break
    report.update(donor_unchanged=source_identity(donor) == identity and assembly6.interfaces(donor) == pool,
        original_donor_unchanged=source_identity(original) == original_identity and assembly6.interfaces(original) == original_pool,
        generated_sources_unchanged=all(assembly6.sha(root/name) == digest for name, digest in report['generated_source_hashes'].items()),
        final_interfaces=assembly6.interfaces(root), latest_disk=cuts.pilot.disk_usage(runs))
    report['interfaces_sha256'] = digest_entries(report['final_interfaces'])
    report['accepted'] = bool(report['completed_indices'] == TRAINING and len(report['phases']) == len(selected) and
        all(p['accepted'] for p in report['phases']) and report['donor_unchanged'] and report['original_donor_unchanged'] and
        report['generated_sources_unchanged'] and cuts.pilot.disk_allowed(report['latest_disk']))
    if report['accepted']:
        report['status'] = 'complete'
    atomic_json(output/'final.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'accepted', 'completed_indices',
        'checked_sample_lower_roots', 'nested_cpu_seconds')}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'original', 'preflight', 'output', 'runs-root'):
        parser.add_argument('--'+name, type=Path, required=True)
    for name in ('expected-previous-sha256', 'expected-original-sha256', 'expected-preflight-sha256', 'agda'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--kernel-cpu-budget', type=positive, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--layout', type=Path)
    parser.add_argument('--expected-layout-sha256')
    arguments = parser.parse_args()
    if arguments.prepare_only:
        prepare(arguments)
    else:
        raise SystemExit(0 if run(arguments)['accepted'] else 2)
