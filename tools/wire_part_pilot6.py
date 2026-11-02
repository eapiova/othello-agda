#!/usr/bin/env python3
"""Scoped eight-part NEW lower-row pilot; blocked until explicit human approval.

Launch inside a measured, detached desktop job with a 3-GiB memory cgroup,
840-CPU-second outer cap and a coordinator reservation. Nested receipts are
diagnostics; charge the enclosing run_job receipt once, including failures.
No solver, full-map import, initial theorem or production is run here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import shutil

import assembly6
import full_map_pilot6 as pilot
from lazy_sample_parts6 import emit
from owner_continue6 import nnls
from provenance import source_identity, digest_entries
from readonly_dependencies6 import command
from run_job import atomic_json, build_lock, run_job, utc
from wire_part_samples6 import selection, _fingerprint
from wire_workflow6 import require

WIRE_SHA = 'd6b4786ebafc86c5f1513d8e300366b9baf3ff06879defa8e2cb19998dc3a762'
ANSWER = 'Sì, autorizzo questo test di nuove righe'
SCOPE = 'eight-new-lower-wire-parts-20261016'


def plan(accepted):
    require(accepted['accepted'] and accepted['layout']['side'] == 'lower'
            and accepted['layout']['owned_rows'] == 3047
            and len(accepted['layout']['owned_parts']) == 16,
            'accepted original16-part lower layout required')
    return dict(format='othello-wire-new-lower-pilot-plan6-v1', scope=SCOPE,
                selection=selection(34366, accepted['layout']['owned_parts']),
                wire_sha256=WIRE_SHA, wire_rows=6873047, wire_bytes=498606513,
                donor_report_sha256=pilot.DONOR_REPORT_SHA,
                donor_source_sha256=pilot.DONOR_SOURCE_SHA,
                donor_interface_pool_sha256=pilot.DONOR_POOL_SHA,
                checker_binary_sha256=pilot.AGDA_SHA, new_rows=1600,
                cpu_max_seconds=900, outer_cpu_cap_seconds=840, outer_reservation_seconds=860,
                extraction_cpu_cap_seconds=180, part_cpu_cap_seconds=60,
                hard_memory_gib=3, part_rss_limit_gib=1.5, part_heap_mib=1100,
                artifact_cap_gib=12, free_disk_gib=80, one_heavy_job=True,
                initial_problem2_proved=False, optimal_initial_pair_proved=False,
                production_authorized=False, native_search_allowed=False,
                training_before_holdout=True, validation_relative_error_limit=.30,
                whole_workflow_validated=False,
                features=['tokens/1000', 'demanded state chunks/1000', 'intercept'])


def approved(spec, plan_raw, approval):
    require(approval.get('approved') is True and approval.get('answer') == ANSWER
            and approval.get('scope') == SCOPE
            and approval.get('plan_sha256') == hashlib.sha256(plan_raw).hexdigest()
            and isinstance(approval.get('question_item'), str) and approval['question_item']
            and all(approval.get(k) == spec[k] for k in ('cpu_max_seconds', 'hard_memory_gib',
                        'artifact_cap_gib', 'free_disk_gib', 'new_rows'))
            and approval.get('native_search_allowed') is False
            and approval.get('production_authorized') is False,
            'explicit new-row human scope approval missing or mismatched')


def _limits():
    cap = resource.getrlimit(resource.RLIMIT_CPU)[0]
    require(cap != resource.RLIM_INFINITY and 0 < cap <= 840,
            'measured outer CPU cap required')
    paths = [line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
             if line.startswith('0::')]
    require(len(paths) == 1, 'one unified memory cgroup required')
    memory = (Path('/sys/fs/cgroup') / paths[0].lstrip('/') / 'memory.max').read_text().strip()
    require(memory.isdigit() and 0 < int(memory) <= 3 * 2**30,
            'at-most3-GiB hard memory cgroup required')


def run(current, out, plan_path, approval_path):
    raw = plan_path.read_bytes()
    spec = json.loads(raw)
    approval = json.loads(approval_path.read_bytes())
    approved(spec, raw, approval)
    _limits()
    require(not out.exists() and 'results' in out.parts
            and not any(p.is_symlink() for p in (out, *out.parents)), 'fresh private output required')
    with build_lock(pilot.DONOR):
        old, donor_source, donor_pool, machine = pilot.donor_identity()
        require(spec == plan(old), 'frozen sample or resources changed')
        native = pilot.checked_native()
        require(native['wire_output_sha256'] == WIRE_SHA, 'native wire pin changed')
        wire = pilot.NATIVE_EXPORT / 'initial-lower.wire'
        wire_stat = wire.stat()
        pilot.storage(current, 128 * 2**20)
        out.mkdir(parents=True)
        report = dict(format='othello-wire-new-lower-pilot6-v1', accepted=False, status='extracting',
                      created_utc=utc(), source=source_identity(current), plan=spec,
                      plan_sha256=hashlib.sha256(raw).hexdigest(), scope_approval=approval,
                      machine=machine, donor_source=donor_source, phases=[], new_rows_accepted=0,
                      initial_problem2_proved=False, optimal_initial_pair_proved=False,
                      production_authorized=False, whole_workflow_validated=False,
                      charge='outer receipt only; nested rusage included, not charged twice')
        def save():
            atomic_json(out / 'report.json', report)
        save()
        extract_root = out / 'extract'
        extract_root.mkdir()
        sample_path = extract_root / 'results/sample.json'
        extraction = run_job('extract-existing-wire', ['python3', str(current / 'tools/wire_part_samples6.py'),
            '--wire', str(wire), '--sha256', WIRE_SHA, '--rows', '6873047', '--parts',
            ','.join(map(str, spec['selection']['selected'])), '--output', str(sample_path)],
            out / 'records', root=extract_root, timeout=450, cpu_limit=180,
            rss_limit_gib=.75, log_limit_mib=2,
            metadata=dict(native_search_run=False, game_rows_checked=0))
        report['extraction'] = extraction
        save()
        require(extraction['accepted'], 'bounded existing-wire extraction failed')
        data = json.loads(sample_path.read_text())
        data['states'] = {int(j): value for j, value in data['states'].items()}
        report['sample_sha256'] = assembly6.sha(sample_path)
        report['case_summaries'] = [dict(part=c['part'], rows=c['rows'], tokens=c['tokens'],
                                       dependencies=len(c['dependencies'])) for c in data['cases']]
        cases = {c['part']: c for c in data['cases']}
        require(set(cases) == set(spec['selection']['selected'])
                and sum(c['rows'] for c in cases.values()) == 1600, 'new selected parts incomplete')
        layouts = {}
        for j, case in cases.items():
            check = out / ('part-' + str(j))
            one = dict(cases=[case], states={d: data['states'][d] for d in case['dependencies']})
            prefix = 'Tests.FullWireNewLower' + str(j)
            layout = emit(check, one, side='lower', prefix=prefix)
            shutil.copy2(current / 'othello.agda-lib', check / 'othello.agda-lib')
            layouts[j] = (check, layout, source_identity(check))
        report['layouts'] = {str(j): layout for j, (_, layout, _) in layouts.items()}
        report['status'] = 'checking-training'
        save()
        training = []
        forecast = None
        with pilot.watched_storage(current, out):
            for split in ('training', 'held_out'):
                if split == 'held_out':
                    model = nnls(training, 3)
                    forecast = dict(model=model, frozen_utc=utc(), held_out_measured=False,
                                    relative_error_limit=.30,
                                    predictions={str(j): sum(c*x for c,x in zip(model['coefficients'],
                                        [cases[j]['tokens']/1000, len(cases[j]['dependencies'])/1000, 1.]))
                                        for j in spec['selection']['held_out']})
                    require(all(v > 0 for v in forecast['predictions'].values()), 'nonpositive prediction')
                    atomic_json(out / 'forecast.json', forecast)
                    report['forecast_sha256'] = assembly6.sha(out / 'forecast.json')
                    report['status'] = 'checking-held-out'
                    save()
                for j in spec['selection'][split]:
                    check, layout, source = layouts[j]
                    require(not assembly6.interfaces(check), 'each part must have a cold own cache')
                    target = layout['prefix'] + '.Part' + str(j)
                    argv = command(machine, target, check, pilot.DONOR)
                    argv[argv.index('-M2700M')] = '-M1100M'
                    pilot.storage(current, 64 * 2**20)
                    rec = run_job('new-part-' + str(j), argv, out / 'records', root=check,
                        expected_source_sha256=source['source_sha256'], timeout=180, cpu_limit=60,
                        rss_limit_gib=1.5, log_limit_mib=4,
                        metadata=dict(own_target_cold=True, checker_binary_sha256=pilot.AGDA_SHA,
                                      split=split, old_row_proofs_rechecked=0, new_rows=cases[j]['rows']))
                    pool = assembly6.interfaces(check)
                    suffix = '/' + target.replace('.', '/') + '.agdai'
                    ok = rec['accepted'] and len([n for n in pool if n.endswith(suffix)]) == 1
                    report['phases'].append(dict(part=j, split=split, record=rec,
                        own_interface_pool_sha256=digest_entries(pool), accepted=bool(ok)))
                    atomic_json(out / ('interfaces-part-' + str(j) + '.json'), pool)
                    if ok:
                        report['new_rows_accepted'] += cases[j]['rows']
                    save()
                    require(ok, 'cold new part failed; no retry or production is launched')
                    if split == 'training':
                        training.append(dict(x=[cases[j]['tokens']/1000,
                            len(cases[j]['dependencies'])/1000, 1.], cpu_seconds=rec['cpu_seconds']))
        require(forecast and assembly6.sha(out / 'forecast.json') == report['forecast_sha256'],
                'prospective forecast changed')
        measured = sum(p['record']['cpu_seconds'] for p in report['phases'] if p['split'] == 'held_out')
        predicted = sum(forecast['predictions'].values())
        unchanged = (source_identity(pilot.DONOR) == donor_source
                     and assembly6.interfaces(pilot.DONOR) == donor_pool
                     and _fingerprint(wire.stat()) == _fingerprint(wire_stat))
        report.update(accepted=bool(unchanged and report['new_rows_accepted'] == 1600),
                      status='complete' if unchanged else 'dependency-changed',
                      borrowed_source_interfaces_unchanged=unchanged,
                      heldout_measured_cpu_seconds=measured, heldout_predicted_cpu_seconds=predicted,
                      heldout_relative_error=abs(measured-predicted)/predicted,
                      row_prediction_gate_passed=abs(measured-predicted)/predicted <= .30,
                      storage=pilot.storage(current), finished_utc=utc())
        save()
        require(report['accepted'], 'donor or wire changed; pilot not accepted')
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--approval', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(Path.cwd().resolve(), args.output.absolute(), args.plan, args.approval)


if __name__ == '__main__':
    main()
