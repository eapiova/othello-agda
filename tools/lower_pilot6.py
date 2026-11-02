#!/usr/bin/env python3
"""AI-assisted bounded LOWER +4 pilot inside one outer CPU reservation.

The input is the recorded twenty-root native/scalar graph, not proof evidence.
Only new safe Agda modules in a frozen results root can establish these bounds.
One serial private cache borrows only the unchanged donor's generic interfaces.
Stop on the first failure; this driver never retries, reserves CPU, or edits core.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import time

import assembly6
import bench6
from cache_resume6 import copy_interface
from closed_roots6 import closure_entries
from compact_logs6 import archive
from explicit_exports6 import pack_tables
import global_assembly6 as assembly
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, build_lock, positive, run_job, utc
import symmetry_stats6 as symmetry
from warning_cost6 import features, solve

PREFIX = 'Tests.LowerPilot6'
DIRECTORY = 'src/Tests/LowerPilot6'
WARNING = '-WnoUnsupportedIndexedMatch'
MIB = 1024**2
GIB = 1024**3
MAX_RUNS_BYTES = 10*GIB
MIN_FREE_BYTES = 100*GIB
INITIAL_HEADROOM = 100*MIB
FINAL_HEADROOM = 8*MIB
PHASE_HEADROOM = 8*MIB
FEATURE_NAMES = ['tokens/1000', 'own_exports/150',
                 'transitive_imported_exports/1000', 'intercept']


def validate_plan(plan):
    assembly.validate_plan(plan)
    if plan['direction'] != 'lower' or plan['threshold'] != 4 or len(plan['roots']) != 20:
        raise ValueError('requires exactly twenty recorded LOWER +4 roots')
    for state in plan['roots']:
        symmetry.validate_key(state)
        if symmetry.canonical_key(state)[0] != state:
            raise ValueError('root is not its recorded canonical representative')


def validate_provenance(plan, provenance, plan_sha256):
    validate_plan(plan)
    cases = provenance.get('cases', [])
    if (provenance.get('format') != 'othello-global-shared6-result-v1' or
            provenance.get('status') != 'complete' or
            provenance.get('direction') != 'lower' or provenance.get('threshold') != 4 or
            provenance.get('sample_size') != 20 or provenance.get('scalar_replay') is not True or
            provenance.get('plan_sha256') != plan_sha256 or
            provenance.get('source_population_kind') != 'canonical frontier full-state classes' or
            not isinstance(provenance.get('subsample_seed'), int) or
            [row.get('state') for row in cases] != plan['roots'] or
            any(not re.fullmatch(r'[0-9a-f]{64}', row.get('native_sha256', '')) for row in cases)):
        raise ValueError('recorded lower native/scalar provenance differs')


def local_options(text):
    options = '--safe --without-K --cubical-compatible'
    if text.count(options) != 1 or WARNING in text or '--save-metas' in text:
        raise ValueError('unexpected generated module options')
    return text.replace(options, '--save-metas '+options+' '+WARNING, 1)


def packed_part(text):
    before = text.split('  entries :', 1)[1].split('  shape :', 1)[0]
    if text.count('  shape = refl\n') != 1 or text.count('  accepted = refl\n') != 1:
        raise ValueError('missing original equality proof obligations')
    changed = pack_tables(text)
    changed = changed.replace('  shape = refl\n', '  shape = refl {x = states}\n')
    changed = changed.replace('  accepted = refl\n', '  accepted = refl {x = true}\n')
    after = changed.split('  entries :', 1)[1].split('  shape :', 1)[0]
    if before != after:
        raise ValueError('certificate bytes changed while packing routing tables')
    return local_options(changed)


def collector_source(roots, witnesses):
    if len(set(roots)) != len(roots) or set(roots) != set(witnesses):
        raise ValueError('collector needs exactly one witness per original lower root')
    modules = sorted({module for module, _ in witnesses.values()})
    aliases = {module: f'R{i}' for i, module in enumerate(modules)}
    text = assembly.HEADER + f'module {PREFIX}.AllLower where\n\n' + assembly.COMMON
    text += ''.join(f'import {module} as {aliases[module]}\n' for module in modules)
    text += '''
AllLower : List String → Set
AllLower [] = ⊤
AllLower (code ∷ codes) =
  Guarantees (Rules.game six) white (lowerGoal 4) (decode code) × AllLower codes

rootCodes : List String
rootCodes = '''
    text += ' ∷ '.join(f'"{assembly.compact.pack_state(state)}"' for state in roots)+' ∷ []\n'
    body = 'tt'
    for state in reversed(roots):
        module, fact = witnesses[state]
        body = f'{aliases[module]}.{fact} , ({body})'
    return local_options(text+'\nabstract\n  allLower : AllLower rootCodes\n  allLower = '+body+'\n')


def negative_source():
    # Black occupies every square: White cannot guarantee Black+4 ≤ White.
    state = 'w'+'1'*36
    text, _, _ = assembly.part_source(0, [dict(state=state, certificate='L', references=[])],
                                      {state: 0}, 'lower')
    text = text.replace(assembly.PREFIX+'.Part0', PREFIX+'.Negative')
    return packed_part(text)


def generated_sources(plan):
    """Preserve closures, order, certificates and the upper pilot's partition."""
    validate_plan(plan)
    sources, groups, witnesses = {}, [], {}
    for index, offset in enumerate(range(0, 20, 10)):
        roots = plan['roots'][offset:offset+10]
        entries = closure_entries(plan, roots)
        parts, owners = assembly.partition(entries, 32000, 150)
        namespace = f'{PREFIX}.Group{index}'
        for j, part in enumerate(parts):
            text, _, _ = assembly.part_source(j, part, owners, 'lower')
            sources[f'{DIRECTORY}/Group{index}/Part{j}.agda'] = packed_part(
                text.replace(assembly.PREFIX, namespace))
        text = assembly.assembly_source(roots, owners, 'lower').replace(assembly.PREFIX, namespace)
        # Positions stay transparent; elaborated evidence is abstract afterwards.
        text, count = re.subn(r'(\naccepted\d+ :.*?)(?=\nposition\d+ :|\Z)',
            lambda match: '\nabstract\n'+'\n'.join('  '+line if line else ''
                for line in match[1].lstrip('\n').splitlines())+'\n', text, flags=re.S)
        if count != 10:
            raise ValueError('different group guarantee template')
        sources[f'{DIRECTORY}/Group{index}/Check.agda'] = local_options(text)
        groups.append(dict(index=index, roots=roots, parts=len(parts), entries=len(entries)))
        witnesses.update({state: (namespace+'.Check', f'guarantee{j}')
                          for j, state in enumerate(roots)})
    sources[f'{DIRECTORY}/AllLower.agda'] = collector_source(plan['roots'], witnesses)
    sources[f'{DIRECTORY}/Negative.agda'] = negative_source()
    return sources, groups


def source_hashes(sources):
    return {name: hashlib.sha256(text.encode()).hexdigest() for name, text in sources.items()}


def negative_rejected(record, changes, own, text):
    if (record['accepted'] or record['exit_code'] is None or record['exit_code'] <= 0 or
            record['stop_reason'] or changes or own):
        return False
    # A scope/type/resource error cannot masquerade as the intended false Bool.
    if re.findall(r'error: \[([^]]+)\]', text) != ['UnequalTerms']:
        return False
    diagnostic = text.split('error: [UnequalTerms]', 1)[1]
    terms = re.search(r'\b(true|false)\s+and\s+(true|false)\s+are not equal at type Bool', diagnostic)
    return bool(terms and terms[1] != terms[2] and 'refl {x = true}' in diagnostic and
                re.search(r'checkShardBy\s+keyed6\s+Fast\.fastGame6\s+white\s+\(lowerGoal 4\)', diagnostic) and
                re.search(r'lowerTransport6\s+imports\s+entries', diagnostic))


def target_suffix(target, directory=DIRECTORY):
    if not target.startswith(directory+'/') or not target.endswith('.agda'):
        raise ValueError('target is outside the generated lower namespace')
    return '/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'


def assert_cold(target, pool, directory=DIRECTORY):
    suffix = target_suffix(target, directory)
    if any(name.endswith(suffix) for name in pool):
        raise ValueError('own target is not cold; unchanged retry prohibited')
    return suffix


def cache_changes(before, after):
    return [dict(path=name, before=digest, after=after.get(name))
            for name, digest in before.items() if after.get(name) != digest]


def generic_interfaces(pool):
    generic = {name: digest for name, digest in pool.items() if '/Tests/' not in name}
    if (len(pool) != 306 or len(generic) != 32 or
            any('/Tests/WarningTables6/' not in name for name in pool if name not in generic)):
        raise ValueError('requires the recorded 306-interface donor with 32 generic interfaces')
    return generic


def predict(plan, report):
    """Fixed four-feature NNLS, trained on group 0 before any group 1 check."""
    if (report['completed_groups'] != [0] or report['training_groups'] != [0] or
            report['heldout_groups'] != [1] or not report['heldout_declared_before_checks'] or
            any(phase['label'].startswith('group1-') for phase in report['phases'])):
        raise ValueError('heldout group must remain unmeasured when fitting')
    rows = features(plan, report['groups'])
    measured = {phase['label']: phase for phase in report['phases']}
    training = []
    for row in rows:
        if row['group'] != 0:
            continue
        phase = measured.get(f"group0-part{row['part']}")
        if not phase or not phase['accepted'] or not math.isfinite(phase['cpu_seconds']) or phase['cpu_seconds'] < 0:
            raise ValueError('incomplete lower training parts')
        training.append(dict(row, cpu_seconds=phase['cpu_seconds']))
    if not training:
        raise ValueError('no lower training data')
    best = (sum(row['cpu_seconds']**2 for row in training), [0.0]*4)
    for count in range(1, 5):
        for active in itertools.combinations(range(4), count):
            a = [[sum(row['x'][i]*row['x'][j] for row in training) for j in active] for i in active]
            b = [sum(row['x'][i]*row['cpu_seconds'] for row in training) for i in active]
            fitted = solve(a, b)
            if fitted is None or any(not math.isfinite(value) for value in fitted) or min(fitted) < -1e-9:
                continue
            coefficients = [0.0]*4
            for i, value in zip(active, fitted):
                coefficients[i] = max(0.0, value)
            error = sum((sum(c*x for c, x in zip(coefficients, row['x']))-row['cpu_seconds'])**2
                        for row in training)
            if error < best[0]:
                best = (error, coefficients)
    heldout = [dict(row, predicted_cpu_seconds=sum(c*x for c, x in zip(best[1], row['x'])))
               for row in rows if row['group'] == 1]
    return dict(format='othello-lower-pilot6-cost-v1', fitted_utc=utc(),
        training_groups=[0], heldout_groups=[1], features=FEATURE_NAMES,
        coefficients=best[1], training_rows=training, training_parts=len(training),
        training_squared_error=best[0], heldout_rows=heldout, heldout_parts=len(heldout),
        heldout_predicted_cpu_seconds=sum(row['predicted_cpu_seconds'] for row in heldout),
        estimator='fixed four-feature nonnegative least squares', heldout_measured_when_fitted=False,
        scope='LOWER sampled part CPU only; group checks and collector excluded',
        upper_timings_used=False, production_authorized=False, full_population_go=False)


def residuals(prediction, phases):
    measured = {phase['label']: phase for phase in phases}
    rows = []
    for expected in prediction['heldout_rows']:
        label = f"group1-part{expected['part']}"
        phase = measured.get(label)
        row = dict(expected, label=label, measured=phase is not None)
        if phase:
            row.update(cpu_seconds=phase['cpu_seconds'], accepted=phase['accepted'],
                       residual_cpu_seconds=(phase['cpu_seconds']-expected['predicted_cpu_seconds']
                                             if phase['accepted'] else None))
        rows.append(row)
    return dict(format='othello-lower-pilot6-residuals-v1', rows=rows,
                failed_checks_are_censored=True, upper_timings_used=False)


def disk_usage(runs):
    return dict(runs_bytes=int(subprocess.check_output(['du', '-s', '-B1', str(runs)], text=True).split()[0]),
                free_bytes=shutil.disk_usage(runs).free)


def disk_allowed(usage, required=FINAL_HEADROOM+PHASE_HEADROOM):
    return usage['runs_bytes']+required < MAX_RUNS_BYTES and usage['free_bytes'] >= MIN_FREE_BYTES


def expected_hash(actual, expected, label):
    if not re.fullmatch(r'[0-9a-f]{64}', expected) or actual != expected:
        raise ValueError(label+' hash differs from the explicit provenance')


def run(args, *, layout=None):
    started = time.monotonic()
    donor, output, runs = args.donor.resolve(), args.output.resolve(), args.runs_root.resolve()
    if runs not in output.parents or 'results' not in output.relative_to(runs).parts or donor in output.parents:
        raise ValueError('new output must be inside runs/results and outside the donor')
    if output.exists():
        raise ValueError('use a fresh output; this driver never resumes or retries')
    if not math.isfinite(args.kernel_cpu_budget) or args.kernel_cpu_budget <= 0:
        raise ValueError('explicit positive nested kernel CPU budget required')
    plan_sha = assembly6.sha(args.plan)
    provenance_sha = assembly6.sha(args.provenance)
    expected_hash(plan_sha, args.expected_plan_sha256, 'plan')
    expected_hash(provenance_sha, args.expected_provenance_sha256, 'native/scalar report')
    plan = json.loads(args.plan.read_text())
    provenance = json.loads(args.provenance.read_text())
    validate_provenance(plan, provenance, plan_sha)
    identity, pool = source_identity(donor), assembly6.interfaces(donor)
    expected_hash(identity['source_sha256'], args.expected_donor_source_sha256, 'donor source')
    expected_hash(identity['agda_source_sha256'], args.expected_donor_agda_source_sha256, 'donor Agda/library')
    expected_hash(digest_entries(pool), args.expected_donor_interfaces_sha256, 'donor interfaces')
    generic = generic_interfaces(pool)
    machine = assembly6.machine_identity(args.agda)
    expected_hash(machine['agda_sha256'], args.expected_agda_sha256, 'Agda executable')
    if layout is None:
        sources, groups = generated_sources(plan)
        required_roots, directory = plan['roots'], DIRECTORY
        training_groups, heldout_groups = [0], [1]
        scope = 'twenty recorded canonical LOWER +4 roots under ORIGINAL Rules.game six'
    else:
        sources, groups = layout['sources'], layout['groups']
        required_roots, directory = layout['roots'], layout['directory']
        training_groups, heldout_groups = [0], []
        scope = layout['scope']
    generated_hashes = source_hashes(sources)
    expected_hash(digest_entries(generated_hashes), args.expected_generated_sha256, 'generated sources')
    expected_checks = 2+sum(group['parts']+1 for group in groups)
    audit_reserve = max(FINAL_HEADROOM, expected_checks*64*1024)
    initial_disk = disk_usage(runs)
    preparation_bytes = sum((donor/name).stat().st_size for name in generic)+sum(len(text.encode()) for text in sources.values())
    if not disk_allowed(initial_disk, max(INITIAL_HEADROOM, preparation_bytes+audit_reserve+PHASE_HEADROOM)):
        raise ValueError('requires 100 MiB aggregate runs headroom and 100 GiB free before preparation')
    output.mkdir(parents=True, exist_ok=False)
    root = output/'check'
    root.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor/name, root/name)  # Immutable source bytes only.
    for name, text in sources.items():
        path = root/name
        if path.exists():
            raise ValueError('new lower namespace already exists in donor')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    manifest = bench6.refresh_manifest(root, origin={key: identity[key] for key in ('revision', 'dirty')})
    for name, digest in generic.items():
        copy_interface(donor/name, root/name, digest)
    if assembly6.interfaces(root) != generic:
        raise ValueError('prepared cache is not exactly the 32 private generic copies')
    atomic_json(output/'expected-sources.json', dict(format='othello-lower-pilot6-sources-v1',
        files=generated_hashes, sha256=digest_entries(generated_hashes)))
    records, record_hashes, raw_log_hashes, archives = {}, {}, {}, {}
    report = dict(format='othello-lower-pilot6-v1', status='running', accepted=False,
        direction='lower', threshold=4, roots=required_roots, groups=groups,
        completed_groups=[], accepted_roots=[], checked_sample_lower_roots=0,
        initial_problem2_proved=False, production_authorized=False, full_population_go=False,
        scope=scope, original_sample_roots=plan['roots'],
        evidence='native certificates and scalar replay are untrusted until safe Agda acceptance',
        machine=machine, driver_sha256=assembly6.sha(Path(__file__)),
        plan_sha256=plan_sha, provenance_sha256=provenance_sha,
        donor=str(donor), donor_source_sha256=identity['source_sha256'],
        donor_agda_source_sha256=identity['agda_source_sha256'], donor_interfaces_sha256=digest_entries(pool),
        generic_interfaces_sha256=digest_entries(generic), generic_interfaces=generic,
        check_root=str(root), source_sha256=manifest['source_sha256'],
        agda_source_sha256=source_identity(root)['agda_source_sha256'],
        generated_source_hashes=generated_hashes, expected_sources_sha256=assembly6.sha(output/'expected-sources.json'),
        phases=[], measured_kernel_cpu_seconds=0.0, kernel_cpu_budget=args.kernel_cpu_budget,
        kernel_budget_scope='nested Agda CPU; outer reservation separately charges driver overhead and overshoot',
        training_groups=training_groups, heldout_groups=heldout_groups, heldout_declared_before_checks=True,
        heldout_declaration_utc=utc(), cost_features=FEATURE_NAMES,
        interface_policy='one serial private cache; own targets cold; every prior hash preserved after every check',
        warning_filter=WARNING, warning_filter_scope='generated module OPTIONS only; absent from CLI',
        maximum_runs_bytes=MAX_RUNS_BYTES, minimum_free_bytes=MIN_FREE_BYTES,
        expected_check_count=expected_checks, final_audit_reserve_bytes=audit_reserve, initial_disk=initial_disk)
    if layout is not None:
        report['layout'] = {key: value for key, value in layout.items()
                            if key not in ('sources', 'groups')}
    prediction = None

    def save():
        atomic_json(output/'lower.json', report)
        atomic_json(output/'phase-records.json', dict(format='othello-lower-pilot6-audit-v1',
            records=records, record_hashes=record_hashes, log_hashes=raw_log_hashes,
            log_archives=archives, generated_source_hashes=generated_hashes,
            final_interfaces=assembly6.interfaces(root),
            final_interfaces_sha256=digest_entries(assembly6.interfaces(root))))

    def donor_unchanged():
        try:
            return source_identity(donor) == identity and assembly6.interfaces(donor) == pool
        except (OSError, ValueError):
            return False

    def check(label, target, *, collector=False, negative=False):
        left = args.kernel_cpu_budget-report['measured_kernel_cpu_seconds']
        if left < 15:
            report['status'] = 'kernel-budget-stopped'
            return None
        usage = disk_usage(runs)
        report['latest_disk'] = usage
        if not disk_allowed(usage, audit_reserve+PHASE_HEADROOM):
            report['status'] = 'artifact-budget-stopped'
            return None
        before = assembly6.interfaces(root)
        suffix = assert_cold(target, before, directory)
        if not donor_unchanged() or source_identity(root)['source_sha256'] != manifest['source_sha256']:
            raise ValueError('source or donor provenance changed before check')
        if assembly6.sha(args.plan) != plan_sha or assembly6.sha(args.provenance) != provenance_sha:
            raise ValueError('recorded plan or native/scalar provenance changed before check')
        if assembly6.machine_identity(args.agda) != machine:
            raise ValueError('compiler or machine changed before check')
        if label.startswith('group1-') and 1 in heldout_groups:
            if prediction is None or assembly6.sha(output/'prediction.json') != report['prediction_sha256']:
                raise ValueError('group 1 needs the unchanged predeclared lower prediction')
        heap, rss, cap = (2500, 3, 180) if collector else (1350, 1.5, 90)
        command = [machine['agda_path'], *assembly6.FLAGS, '--save-metas', '-i', 'src', target,
                   '+RTS', f'-M{heap}M', '-c', '-s', '-RTS']
        report['last_attempted_check'] = dict(label=label, target=target)
        record = run_job(label, command, output/'records', root=root,
            expected_source_sha256=manifest['source_sha256'], cpu_limit=min(cap, left),
            timeout=cap*3, rss_limit_gib=rss, log_limit_mib=2,
            metadata=dict(machine=machine, own_target_cold=True, plan_sha256=plan_sha,
                provenance_sha256=provenance_sha, borrowed_interfaces_sha256=digest_entries(before),
                interface_isolation='private inode copies; serial cache', negative_certificate_fixture=negative))
        report['measured_kernel_cpu_seconds'] += record['cpu_seconds']
        records[label] = record
        record_hashes[label] = assembly6.sha(output/'records'/f'{label}.json')
        log = output/'records'/f'{label}.log'
        raw_log_hashes[label] = assembly6.sha(log)
        after = assembly6.interfaces(root)
        changes = cache_changes(before, after)
        own = [name for name in after if name.endswith(suffix)]
        unexpected = [name for name in after if name not in before and name not in own]
        text = log.read_text()
        metric = assembly.metrics(record)
        metric.update(label=label, target=target, exit_code=record['exit_code'], heap_mib=heap,
            rss_limit_gib=rss, cpu_limit_seconds=min(cap, left), timeout_seconds=cap*3,
            cache_changes=changes, unexpected_interfaces=unexpected,
            interfaces_before_sha256=digest_entries(before), interfaces_after_sha256=digest_entries(after),
            rts=rts_stats(text), negative_fixture=negative)
        violations = []
        if changes or unexpected:
            violations.append('prior cache changed or unexpected interfaces added')
        if not donor_unchanged():
            violations.append('original donor changed')
        if not record['source_unchanged'] or not record['expected_source_matches']:
            violations.append('generated source identity changed')
        if record['executable_sha256'] != machine['agda_sha256']:
            violations.append('checked executable differs')
        if not negative and record['accepted'] and len(own) != 1:
            violations.append('accepted target interface missing or ambiguous')
        metric['accepted'] = bool(record['accepted'] and not violations)
        metric['proof_issues'] = violations
        if own:
            metric['own_interfaces'] = {name: after[name] for name in own}
        metric['expected_outcome_met'] = (negative_rejected(record, changes, own+unexpected, text)
                                          and not violations if negative else metric['accepted'])
        report['phases'].append(metric)
        if metric['accepted']:
            archives[label] = archive(log, raw_log_hashes[label])
            metric['archived_log'] = archives[label]
        # A rejected false certificate and every genuine failure retain raw logs.
        save()
        print(json.dumps(metric), flush=True)
        return metric

    save()  # This persists the group-1 declaration and expected map before checks.
    try:
        with build_lock(root):
            result = check('negative-terminal-lower', f'{directory}/Negative.agda', negative=True)
            if result is not None and not result['expected_outcome_met']:
                report['status'] = 'negative-fixture-failed'
            elif result is not None:
                for group in groups:
                    i = group['index']
                    if i in heldout_groups:
                        prediction = predict(plan, report)
                        atomic_json(output/'prediction.json', prediction)
                        report['prediction_sha256'] = assembly6.sha(output/'prediction.json')
                        report['prediction_declared_before_heldout_checks'] = True
                        save()
                    for j in range(group['parts']):
                        result = check(f'group{i}-part{j}', f'{directory}/Group{i}/Part{j}.agda')
                        if result is None or not result['accepted']:
                            if result is not None:
                                report['status'] = 'part-failed'
                            break
                    else:
                        result = check(f'group{i}-bounds', f'{directory}/Group{i}/Check.agda')
                        if result is not None and result['accepted']:
                            report['completed_groups'].append(i)
                            report['accepted_roots'].extend(group['roots'])
                            report['checked_sample_lower_roots'] = len(report['accepted_roots'])
                            save()
                            continue
                        if result is not None:
                            report['status'] = 'group-assembly-failed'
                    break
                else:
                    result = check('all-lower', f'{directory}/AllLower.agda', collector=True)
                    report['accepted'] = bool(result is not None and result['accepted'])
                    if result is not None:
                        report['status'] = 'complete' if report['accepted'] else 'collector-failed'
    except Exception as error:
        report.update(status='harness-failed', accepted=False,
                      error=dict(type=type(error).__name__, message=str(error)))
    if prediction is not None:
        atomic_json(output/'residuals.json', residuals(prediction, report['phases']))
        report['residuals_sha256'] = assembly6.sha(output/'residuals.json')
        if assembly6.sha(output/'prediction.json') != report['prediction_sha256']:
            report.update(status='prediction-changed', accepted=False)
    try:
        report['donor_sources_unchanged'] = source_identity(donor) == identity
        report['donor_interfaces_unchanged'] = assembly6.interfaces(donor) == pool
        report['generated_sources_unchanged'] = source_identity(root)['source_sha256'] == manifest['source_sha256']
    except (OSError, ValueError):
        report.update(donor_sources_unchanged=False, donor_interfaces_unchanged=False,
                      generated_sources_unchanged=False)
    if not all(report[key] for key in ('donor_sources_unchanged', 'donor_interfaces_unchanged', 'generated_sources_unchanged')):
        report.update(status='provenance-changed', accepted=False)
    report['exact_accepted_root_coverage'] = report['accepted_roots'] == required_roots
    if report['accepted'] and not report['exact_accepted_root_coverage']:
        report.update(status='coverage-mismatch', accepted=False)
    try:
        report['plan_unchanged'] = assembly6.sha(args.plan) == plan_sha
        report['provenance_unchanged'] = assembly6.sha(args.provenance) == provenance_sha
        report['compiler_unchanged'] = assembly6.machine_identity(args.agda) == machine
    except (OSError, ValueError, subprocess.SubprocessError):
        report.update(plan_unchanged=False, provenance_unchanged=False, compiler_unchanged=False)
    if not report['plan_unchanged'] or not report['provenance_unchanged']:
        report.update(status='input-provenance-changed', accepted=False)
    if not report['compiler_unchanged']:
        report.update(status='compiler-changed', accepted=False)
    report['latest_disk'] = disk_usage(runs)
    if not disk_allowed(report['latest_disk'], audit_reserve):
        report.update(status='artifact-budget-exceeded', accepted=False)
    report['driver_wall_seconds'] = time.monotonic()-started
    report['finished_utc'] = utc()
    save()
    atomic_json(output/'final.json', report)
    audit = json.loads((output/'phase-records.json').read_text())
    audit.update(final_sha256=assembly6.sha(output/'final.json'), lower_sha256=assembly6.sha(output/'lower.json'))
    atomic_json(output/'phase-records.json', audit)
    print(json.dumps({key: report[key] for key in ('status', 'accepted', 'checked_sample_lower_roots',
                                                'measured_kernel_cpu_seconds')}), flush=True)
    return report


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'output', 'donor', 'provenance', 'runs-root'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--agda', required=True)
    for name in ('plan', 'provenance', 'donor-source', 'donor-agda-source',
                 'donor-interfaces', 'agda', 'generated'):
        p.add_argument('--expected-'+name+'-sha256', required=True)
    p.add_argument('--kernel-cpu-budget', type=positive, required=True)
    return p


def main():
    report = run(parser().parse_args())
    raise SystemExit(0 if report['accepted'] else 2)


if __name__ == '__main__':
    main()
