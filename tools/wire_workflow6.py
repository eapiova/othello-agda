#!/usr/bin/env python3
"""Audit accepted packed-table wire pilots and screen incomplete workflow costs.

Read-only, AI-assisted diagnostics. Run on the checking desktop: interfaces are
read in place and only hashes, counts and sizes are emitted. No Agda process,
ledger write, network operation or proof premise is created.

CLI: --manifest INPUT --expected-manifest-sha256 SHA [--output JSON]. Paths in
INPUT are absolute or relative to INPUT's directory. The manifest has format
othello-wire-workflow6-input-v1 and these required fields:
  identity: hostname, agda_sha256, donor_source_sha256,
            generic_interfaces_sha256
  line: {path, sha256}; donor_root: path
  chains: [{path, sha256, children: {label: {path, sha256}}}]
  pilots: [{label, ply, direction, report: {path, sha256},
            plan: {path, sha256}, native: {path, sha256},
            wire: {path, sha256}, prepared_root: path, check_root: path}]
  counts: {lower: {receipt: {path, sha256}, data: {path, sha256}}, upper: ...}
  bounds: cpu_hours, artifacts_gib, part_rss_gib, assembly_rss_gib,
          allocated_artifacts_bytes, free_disk_bytes, min_free_disk_gib
Optional decode_interfaces=true uses the pinned Agda interface census reader.
The chains must contain all six lower/upper ply12/14/16 pilots, and every chain
child (including the older heldout census) is SHA-pinned. Heldout census costs
are excluded from the homogeneous fit. Counts describe the original unpinned
global graph, even when the conditional pilots use a pinned line.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import socket

import assembly6
from owner_continue6 import nnls
from provenance import digest_entries, source_identity
from run_job import atomic_json

FORMAT = 'othello-wire-workflow6-v1'
WIRE = 'othello-wire-pilot6-v1'
REQUIRED = {f'{d}-ply{p}' for d in ('lower', 'upper') for p in (12, 14, 16)}
FEATURES = ['tokens/1000', 'entries/1000', 'imported_citations/1000',
            'transitive_entries/1000', 'part_intercept']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, label, minimum=0):
    require(type(value) is int and minimum <= value <= 2**64-1, 'invalid ' + label)
    return value


def positive(value, label):
    require(type(value) in (int, float) and math.isfinite(value) and 0 < value < 1e12,
            'missing or invalid ' + label)
    return float(value)


def digest(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'missing exact SHA identity')
    return value


def path(base, name):
    require(type(name) is str and name, 'missing artifact path')
    p = Path(name)
    return (p if p.is_absolute() else base / p).resolve()


def pinned(base, spec, *, json_data=True):
    require(type(spec) is dict, 'missing pinned artifact')
    p = path(base, spec.get('path'))
    expected = digest(spec.get('sha256'))
    require(assembly6.sha(p) == expected, 'pinned artifact changed: ' + str(p))
    return (json.loads(p.read_text()) if json_data else p), expected


def no_claim(data):
    require(data.get('production_authorized') is False, 'input claims production authorization')
    for key in ('initial_theorem_proved', 'initial_problem2_proved', 'optimal_pair_proved'):
        require(data.get(key, False) is False, 'input claims an initial theorem')


def bounds(data):
    require(type(data) is dict, 'missing resource bounds')
    result = {k: positive(data.get(k), k) for k in
              ('cpu_hours', 'artifacts_gib', 'part_rss_gib', 'assembly_rss_gib',
               'min_free_disk_gib')}
    for k in ('allocated_artifacts_bytes', 'free_disk_bytes'):
        result[k] = integer(data.get(k), k)
    return result


def audit_chains(base, specs, identity):
    require(type(specs) is list and specs, 'missing accepted chain')
    found, prior = {}, set()
    for spec in specs:
        chain, sha = pinned(base, spec)
        no_claim(chain)
        expected = {'othello-unattended-wire6-v1':'complete-pilot',
                    'othello-unattended-wire-advance6-v1':'complete-earlier-roots'}
        require(chain.get('format') in expected and chain.get('accepted') is True and
                chain.get('status') == expected[chain['format']], 'failed or partial accepted chain')
        require(chain.get('machine', {}).get('hostname') == identity['hostname'] and
                chain.get('machine', {}).get('agda_sha256') == identity['agda_sha256'],
                'chain machine identity mismatch')
        predecessor = chain.get('predecessor_report_sha256')
        require(predecessor is None or predecessor in prior, 'unverified predecessor chain')
        require(chain['format'] != 'othello-unattended-wire-advance6-v1' or predecessor in prior,
                'advance chain needs exact accepted predecessor')
        phases, children = chain.get('phases'), spec.get('children')
        require(type(phases) is list and phases and type(children) is dict and
                set(children) == {p.get('label') for p in phases} and
                len(children) == len(phases), 'missing, duplicate or partial chain children')
        for phase in phases:
            label = phase['label']
            child, child_sha = pinned(base, children[label])
            require(phase.get('accepted') is True and child.get('accepted') is True and
                    child.get('status') == 'complete', 'failed or partial chain child')
            require(child_sha == phase.get('kernel_report_sha256', phase.get('report_sha256')),
                    'chain child identity mismatch')
            no_claim(child)
            if label in REQUIRED:
                require(label not in found, 'duplicate pilot in accepted chain')
                found[label] = dict(report_sha256=child_sha, plan_sha256=phase.get('plan_sha256'),
                                   native_report_sha256=phase.get('native_report_sha256'))
        prior.add(sha)
    require(set(found) == REQUIRED, 'accepted chain does not cover all six wire pilots')
    return found


def target_path(name):
    p = Path(name)
    require(not p.is_absolute() and '..' not in p.parts and p.parts[0] == 'src' and
            p.suffix == '.agda', 'generated target escapes source root')
    return p


def validate_targets(plan):
    targets = plan.get('targets')
    require(type(targets) is list and len(targets) >= 2, 'missing wire targets')
    require([t.get('kind') for t in targets] == ['part'] * (len(targets)-1) + ['assembly'],
            'partial or reordered wire targets')
    hashes = plan.get('generated_hashes')
    require(type(hashes) is dict and set(hashes) == {t.get('path') for t in targets} and
            len(hashes) == len(targets), 'generated target/hash mismatch')
    closure, entries = [], []
    for index, t in enumerate(targets):
        target_path(t['path']); digest(hashes[t['path']])
        require(t.get('root_index') == 0, 'mixed root pilot')
        integer(t.get('source_bytes'), 'source bytes', 1)
        if t['kind'] == 'part':
            require(type(t.get('part')) is int and t['part'] == index, 'reordered parts')
            for field in ('entries', 'tokens', 'compact_bytes'):
                integer(t.get(field), field, 1)
            integer(t.get('imported_citations'), 'imported citations')
            deps = t.get('dependencies')
            require(type(deps) is list and len(set(deps)) == len(deps) and
                    all(type(d) is int and 0 <= d < index for d in deps), 'bad part dependencies')
            ancestors = set(deps)
            for d in deps:
                ancestors.update(closure[d])
            closure.append(ancestors); entries.append(t['entries'])
            require(t['entries'] <= integer(plan.get('max_entries'), 'entry cap', 1) and
                    t['tokens'] <= integer(plan.get('max_tokens'), 'token cap', 1), 'declared part cap exceeded')
        else:
            # Check references the root owner; its exact closure is recorded.
            ancestors = closure[-1] | {len(entries)-1}
        require(t.get('transitive_parts') == len(ancestors) and
                t.get('transitive_entries') == sum(entries[d] for d in ancestors),
                'dishonest transitive workload')
    root = plan['roots'][0]
    require(root.get('entries') == sum(entries) and root.get('checked_tokens') ==
            sum(t['tokens'] for t in targets[:-1]) and plan.get('total_generated_source_bytes') ==
            sum(t['source_bytes'] for t in targets), 'dishonest pilot totals')
    return targets


def audit_pilot(base, spec, identity, chain, line, line_sha, generic, decode=False):
    label = spec.get('label')
    require(label in REQUIRED and label == f"{spec.get('direction')}-ply{spec.get('ply')}",
            'wrong pilot root label')
    report, report_sha = pinned(base, spec.get('report'))
    plan, plan_sha = pinned(base, spec.get('plan'))
    native, native_sha = pinned(base, spec.get('native'))
    wire, wire_sha = pinned(base, spec.get('wire'), json_data=False)
    for item in (report, plan, native): no_claim(item)
    require(report_sha == chain[label]['report_sha256'] and
            plan_sha == chain[label]['plan_sha256'] == report.get('plan_sha256'), 'chain/plan identity mismatch')
    require(chain[label]['native_report_sha256'] in (None, native_sha) and
            native_sha == plan.get('native_report_sha256') and
            wire_sha == native.get('wire_output_sha256') == plan.get('wire_sha256'), 'native/wire identity mismatch')
    require(plan.get('format') == report.get('format') == WIRE and
            report.get('phase') == 'training' and report.get('status') == 'complete' and
            report.get('accepted') is True and report.get('donor_unchanged') is True and
            report.get('generated_sources_unchanged') is True and
            plan.get('scalar_replay_complete') is True and plan.get('packed_export_tables') is True and
            plan.get('forced_splits') in (None, []) and 'cuts' not in plan,
            'requires complete original packed-table wire evidence')
    require(native.get('format') == 'othello-census-wire6-run-v1' and
            native.get('status') == 'complete-untrusted-wire' and native.get('native_complete') is True and
            native.get('wire_complete') is True and native.get('donor_unchanged') is True and
            native.get('table_unchanged') is True and native.get('exit_code') == 0,
            'incomplete or failed native wire')
    root = plan.get('roots')
    require(type(root) is list and len(root) == 1, 'conditional single root required')
    root = root[0]
    require(root.get('key') == native.get('root_key') == line['states'][spec['ply']] and
            root.get('direction') == native.get('request', {}).get('direction') == spec['direction'] and
            native.get('request', {}).get('threshold') == 4 and
            native.get('build', {}).get('line_sha256') == line_sha and native['build'].get('pins'),
            'line/root/bound identity mismatch')
    counts = native.get('counts', {})
    require(counts.get('wire_records') == root.get('entries') and counts.get('wire_bytes') == wire.stat().st_size,
            'native wire counts mismatch')
    targets = validate_targets(plan)
    prepared, check = path(base, spec.get('prepared_root')), path(base, spec.get('check_root'))
    require((check / 'SNAPSHOT.json').is_file(), 'checking source requires frozen SNAPSHOT')
    require(source_identity(check)['source_sha256'] == report.get('source_sha256') and
            report.get('donor_source', {}).get('source_sha256') == identity['donor_source_sha256'] and
            report.get('borrowed_interfaces_sha256') == identity['generic_interfaces_sha256'],
            'source/donor/generic identity mismatch')
    machine = report.get('machine', {})
    require(machine.get('hostname') == identity['hostname'] and
            machine.get('agda_sha256') == identity['agda_sha256'], 'compiler/machine identity mismatch')
    for t in targets:
        name = t['path']
        require(assembly6.sha(prepared/name) == plan['generated_hashes'][name] == assembly6.sha(check/name) and
                (prepared/name).stat().st_size == t['source_bytes'], 'generated source changed')
    pool = assembly6.interfaces(check)
    require(digest_entries(pool) == report.get('final_interfaces_sha256'), 'accepted final interfaces changed')
    borrowed, rows = dict(generic), []
    phases = report.get('phases')
    require(type(phases) is list and len(phases) == len(targets), 'partial checked targets')
    for phase, t in zip(phases, targets):
        record = phase.get('record', {})
        require(phase.get('target') == t and phase.get('changed_imports') == [] and
                record.get('format') == 'othello-job-v2' and record.get('accepted') is True and
                record.get('stop_reason') is None and record.get('exit_code') == 0 and
                all(record.get(k) is True for k in ('own_target_cold', 'source_unchanged', 'expected_source_matches')),
                'failed, partial, warm or modified kernel target')
        require(record.get('source_sha256') == record.get('expected_source_sha256') == report['source_sha256'] and
                record.get('executable_sha256') == identity['agda_sha256'] and
                record.get('machine') == machine and record.get('root') == report.get('check_root') and
                record.get('borrowed_interfaces_sha256') == digest_entries(borrowed),
                'kernel source/compiler/import identity mismatch')
        require(all(flag in record.get('argv', []) for flag in (*assembly6.FLAGS, '--save-metas')) and
                t['path'] in record['argv'], 'missing safe kernel flags or target')
        for key, value in t.items(): require(record.get(key) == value, 'kernel target metadata differs')
        suffix = '/' + t['path'].removeprefix('src/').removesuffix('.agda') + '.agdai'
        matches = [n for n in pool if n.endswith(suffix)]
        require(len(matches) == 1 and matches[0] not in borrowed, 'missing, ambiguous or warm own interface')
        name = matches[0]
        interface = dict(sha256=pool[name], compressed_bytes=(check/name).stat().st_size)
        if decode:
            from interface_census6 import census_file
            interface = census_file(check/name, pool[name])
        cpu = positive(record.get('cpu_seconds'), 'measured CPU')
        rss = positive(record.get('peak_rss_gib'), 'measured RSS')
        positive(record.get('cpu_limit_seconds'), 'record CPU bound')
        positive(record.get('rss_stop_threshold_gib'), 'record RSS bound')
        require(cpu < record['cpu_limit_seconds'], 'accepted record exceeded CPU bound')
        require(rss < record['rss_stop_threshold_gib'], 'accepted record exceeded RSS bound')
        rows.append(dict(target=t, cpu_seconds=cpu, peak_rss_gib=rss, interface=interface))
        borrowed[name] = pool[name]
    require(borrowed == pool, 'unexpected interfaces outside the accepted target chain')
    require(math.isclose(sum(r['cpu_seconds'] for r in rows), positive(report.get('cpu_seconds'), 'total CPU'),
                         rel_tol=1e-9, abs_tol=1e-6), 'dishonest total type-check CPU')
    require(report['cpu_seconds'] < positive(report.get('cpu_budget'), 'pilot CPU budget'),
            'pilot exceeded its CPU budget')
    require(assembly6.interfaces(check) == pool and source_identity(check)['source_sha256'] == report['source_sha256'],
            'source/interface changed during diagnostic')
    return dict(label=label, direction=spec['direction'], ply=spec['ply'], report_sha256=report_sha,
                plan_sha256=plan_sha, native_report_sha256=native_sha, wire_sha256=wire_sha,
                wire_bytes=wire.stat().st_size, source_bytes=plan['total_generated_source_bytes'],
                entries=root['entries'], tokens=root['checked_tokens'], rows=rows,
                type_check_cpu_seconds=sum(r['cpu_seconds'] for r in rows),
                peak_rss_gib=max(r['peak_rss_gib'] for r in rows),
                compressed_interface_bytes=sum(r['interface']['compressed_bytes'] for r in rows))


def audit_counts(base, spec, direction):
    receipt, receipt_sha = pinned(base, spec.get('receipt'))
    data, data_sha = pinned(base, spec.get('data'))
    no_claim(receipt); no_claim(data)
    c = receipt.get('counts', {})
    require(receipt.get('format') == 'othello-census-samples6-run-v1' and
            receipt.get('status') == 'complete-native-census' and receipt.get('native_complete') is True and
            receipt.get('exit_code') == 0 and receipt.get('donor_unchanged') is True and
            receipt.get('table_unchanged') is True and receipt.get('partial_counts_are_lower_bounds') is False and
            receipt.get('incomplete_count_extrapolated') is False and
            receipt.get('samples_output_sha256') == data_sha and data.get('native_census') == c and
            data.get('format') == 'othello-census-samples6-v1', 'incomplete or mismatched global counts receipt')
    require(c.get('direction') == direction and c.get('threshold') == 4 and
            all(c.get(k) is True for k in ('complete', 'root_validated', 'root_holds', 'sampling_complete')) and
            all(c.get(k) is False for k in ('count_overflow', 'oracle_aborted', 'line_maintained')) and
            c.get('frontier_discs') == 36 and receipt.get('request', {}).get('position') == 'initial',
            'counts are not a complete original unpinned initial graph')
    s = data.get('statistics', {})
    keys = ('sharing_entries', 'reference_edges', 'ideal_grammar_tokens', 'ideal_grammar_ascii_bytes',
            'chosen_edges', 'leaf_occurrences', 'nonidentity_D4_citation_edges')
    for k in keys: integer(s.get(k), 'global ' + k)
    kinds = s.get('node_kinds', {})
    require(type(kinds) is dict and set(kinds) == {'leaf', 'pass', 'forcing', 'opponent'},
            'missing or unknown node kinds')
    for k in ('leaf', 'pass', 'forcing', 'opponent'): integer(kinds.get(k), 'node kind ' + k)
    require(sum(kinds.values()) == integer(c.get('unique_dag_nodes'), 'DAG nodes', 1) and
            s['chosen_edges'] == c.get('dag_edges') and s['sharing_entries'] < c['unique_dag_nodes'] and
            s['reference_edges'] >= 2*s['sharing_entries'] and
            s['nonidentity_D4_citation_edges'] <= s['reference_edges'], 'dishonest global counts')
    expected_tokens = kinds['pass']+kinds['forcing']+kinds['opponent']+s['leaf_occurrences']+s['reference_edges']
    expected_bytes = (kinds['pass']+2*(kinds['forcing']+kinds['opponent'])+s['leaf_occurrences']+
                      s['reference_edges']+s['nonidentity_D4_citation_edges']+13*(s['sharing_entries']+1))
    require(s['ideal_grammar_tokens'] == expected_tokens and s['ideal_grammar_ascii_bytes'] == expected_bytes,
            'global grammar count identity failed')
    return dict(direction=direction, receipt_sha256=receipt_sha, data_sha256=data_sha,
                statistics=s, line_pinned=False, agda_accepted=False)


def screen(pilots, counts, limits):
    limits = bounds(limits)
    components, models = [], {}
    for direction in ('lower', 'upper'):
        selected = [p for p in pilots if p['direction'] == direction]
        rows = [r for p in selected for r in p['rows'] if r['target']['kind'] == 'part']
        require(len(rows) >= 2, 'insufficient homogeneous wire measurements')
        fitted = nnls([dict(x=[r['target'][k]/1000 for k in
                              ('tokens', 'entries', 'imported_citations', 'transitive_entries')] + [1.],
                           cpu_seconds=r['cpu_seconds']) for r in rows], len(FEATURES))
        fitted.update(feature_names=FEATURES, retrospectively_fitted=True,
                      independent_holdout_validated=False, sample_parts=len(rows))
        models[direction] = fitted
        s = counts[direction]['statistics']; entries = s['sharing_entries']+1
        coefficients = fitted['coefficients']
        token_cpu = coefficients[0]*s['ideal_grammar_tokens']/1000
        entry_cpu = coefficients[1]*entries/1000
        tokens = sum(r['target']['tokens'] for r in rows)
        measured_source = sum(r['target']['source_bytes'] for r in rows)
        interfaces = sum(r['interface']['compressed_bytes'] for r in rows)
        capacity = max(r['target']['entries'] for r in rows)
        scenario_parts = math.ceil(entries/capacity)
        components.append(dict(direction=direction, original_unpinned_counts=counts[direction],
            token_component_cpu_hours=token_cpu/3600, entry_component_cpu_hours=entry_cpu/3600,
            known_feature_partial_cpu_hours=(token_cpu+entry_cpu)/3600,
            hypothetical_entry_limited_parts=scenario_parts,
            hypothetical_part_intercept_cpu_hours=coefficients[4]*scenario_parts/3600,
            imported_citations=None, transitive_entries=None, whole_assembly_cpu_hours=None,
            whole_assembly_peak_rss_gib=None, optimal_joint_line_cpu_hours=None,
            ideal_compact_grammar_bytes=s['ideal_grammar_ascii_bytes'],
            token_scaled_source_bytes=s['ideal_grammar_tokens']*measured_source/tokens,
            token_scaled_compressed_interface_bytes=s['ideal_grammar_tokens']*interfaces/tokens,
            measured_part_cpu_seconds=sum(r['cpu_seconds'] for r in rows),
            measured_assembly_cpu_seconds=sum(r['cpu_seconds'] for p in selected for r in p['rows']
                                               if r['target']['kind'] == 'assembly'),
            measured_max_part_rss_gib=max(r['peak_rss_gib'] for r in rows),
            source_and_interface_scaling='rough observed ratio; no error bound or storage gate certificate'))
    failed = []
    parts = [r for p in pilots for r in p['rows'] if r['target']['kind'] == 'part']
    assemblies = [r for p in pilots for r in p['rows'] if r['target']['kind'] == 'assembly']
    if max(r['peak_rss_gib'] for r in parts) >= limits['part_rss_gib']: failed.append('measured-part-rss')
    if max(r['peak_rss_gib'] for r in assemblies) >= limits['assembly_rss_gib']: failed.append('measured-assembly-rss')
    if limits['allocated_artifacts_bytes'] >= limits['artifacts_gib']*2**30: failed.append('current-artifact-allocation')
    if limits['free_disk_bytes'] < limits['min_free_disk_gib']*2**30: failed.append('current-free-disk')
    # A regression extrapolation is not a rigorous runtime/storage lower bound.
    # Report budget ratios without pretending that they establish a failed gate.
    partial = sum(c['known_feature_partial_cpu_hours'] for c in components)
    compact_bytes = sum(c['ideal_compact_grammar_bytes'] for c in components)
    return dict(recommendation='NO_GO' if failed else 'NEEDS_FULL_PINNED_INITIAL_WORKFLOW_PILOT',
                failed_gates=failed, bounds=limits, models=models, components=components,
                combined_known_feature_partial_cpu_hours=partial,
                partial_cpu_budget_ratio=partial/limits['cpu_hours'],
                combined_ideal_compact_grammar_bytes=compact_bytes,
                combined_token_scaled_source_bytes=sum(c['token_scaled_source_bytes'] for c in components),
                combined_token_scaled_compressed_interface_bytes=
                    sum(c['token_scaled_compressed_interface_bytes'] for c in components),
                full_workflow_cpu_hours=None, full_workflow_artifacts_bytes=None,
                full_pinned_workload_counts_known=False)


def audit(manifest, base):
    require(manifest.get('format') == 'othello-wire-workflow6-input-v1', 'wrong input format')
    identity = manifest.get('identity', {})
    require(type(identity.get('hostname')) is str and identity['hostname'], 'missing machine hostname')
    for k in ('agda_sha256', 'donor_source_sha256', 'generic_interfaces_sha256'): digest(identity.get(k))
    bounds(manifest.get('bounds'))
    line, line_sha = pinned(base, manifest.get('line'))
    require(type(line.get('states')) is list and len(line['states']) > 16, 'missing pinned line states')
    chains = audit_chains(base, manifest.get('chains'), identity)
    donor = path(base, manifest.get('donor_root'))
    require((donor/'SNAPSHOT.json').is_file() and
            source_identity(donor)['source_sha256'] == identity['donor_source_sha256'], 'donor snapshot identity mismatch')
    pool = assembly6.interfaces(donor)
    generic = {n:d for n,d in pool.items() if '/src/Tests/' not in n}
    require(generic and digest_entries(generic) == identity['generic_interfaces_sha256'], 'generic interfaces changed')
    specs = manifest.get('pilots')
    require(type(specs) is list and len(specs) == len(REQUIRED) and {s.get('label') for s in specs} == REQUIRED,
            'missing or duplicate accepted wire pilots')
    decode = manifest.get('decode_interfaces', False)
    require(type(decode) is bool, 'invalid interface decode option')
    pilots = [audit_pilot(base, s, identity, chains, line, line_sha, generic, decode) for s in specs]
    counts = {d:audit_counts(base, manifest['counts'][d], d) for d in ('lower', 'upper')}
    require(source_identity(donor)['source_sha256'] == identity['donor_source_sha256'] and
            assembly6.interfaces(donor) == pool, 'diagnostic changed donor')
    result = screen(pilots, counts, manifest['bounds'])
    result.update(format=FORMAT, accepted_pilot_audit=True, production_authorized=False,
                  initial_theorem_proved=False, initial_problem2_proved=False, optimal_pair_proved=False,
                  data_supplies_agda_premise=False, line_sha256=line_sha, identity=identity, pilots=pilots,
                  measured_type_check_cpu_seconds=sum(p['type_check_cpu_seconds'] for p in pilots),
                  measured_peak_rss_gib=max(p['peak_rss_gib'] for p in pilots),
                  excluded_work=['full pinned initial graph and its changed witness policy',
                                 'full import/export closure and cumulative interface loading',
                                 'whole initial root assembly and joint optimal Black16 White20 line',
                                 'generation, native solving, generic cold build, transfer, logs and packaging',
                                 'duplicate source/check roots and retained donors'],
                  limitations=['Only original accepted packed-table wire parts fit the model; raw Board census and forced cuts are excluded.',
                               'Models are retrospective and correlated; no independent prediction error bound is available.',
                               'Global totals cannot determine imported states, transitive closure, token-constrained shard counts or peak memory.',
                               'Known-feature projections omit unknown positive costs and are not rigorous runtime lower bounds.',
                               'Tiny conditional root assemblies are measured only; no million-entry assembly extrapolation is made.',
                               'An incomplete workflow cannot authorize production or establish either initial theorem.'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--expected-manifest-sha256', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        manifest, manifest_sha = pinned(args.manifest.resolve().parent,
                                       dict(path=str(args.manifest.resolve()), sha256=args.expected_manifest_sha256))
        require(socket.gethostname() == manifest.get('identity', {}).get('hostname'),
                'interfaces must be audited in place on the original checking host')
        result = audit(manifest, args.manifest.resolve().parent)
        result['manifest_sha256'] = manifest_sha
    except (ValueError, KeyError, TypeError, IndexError, OverflowError, OSError) as error:
        result = dict(format=FORMAT, recommendation='NO_GO', accepted_pilot_audit=False,
                      failed_gates=['input-audit'], error=str(error), production_authorized=False,
                      initial_theorem_proved=False, initial_problem2_proved=False,
                      optimal_pair_proved=False, data_supplies_agda_premise=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(args.output, result)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 1 if result['recommendation'] == 'NO_GO' else 0


if __name__ == '__main__': raise SystemExit(main())
