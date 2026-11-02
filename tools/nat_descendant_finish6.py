#!/usr/bin/env python3
"""Wait for the numeric descendant, then reuse it or finish its CPU-stop prefix.

Finite detached continuation only. It never launches initial production and
does not migrate an AI coding session or write the coordinator's ledger.
"""
import argparse
import json
from pathlib import Path
import time
from types import SimpleNamespace

import assembly6
import nat_descendant_resume6 as resume
from provenance import source_identity
from run_job import atomic_json, utc
from wire_workflow6 import require


def run(args):
    previous = args.previous.resolve()
    label = previous.name.removeprefix('six-')
    receipt_path = previous / 'results' / (label + '.json')
    require(source_identity(previous)['source_sha256'] == args.expected_previous_source_sha256,
            'predecessor frozen source changed')
    out = args.output.resolve()
    require(not out.exists() and 'results' in out.parts, 'fresh private continuation output required')
    out.mkdir(parents=True)
    report = dict(format='othello-nat-descendant-finish6-v1', status='waiting', accepted=False,
        created_utc=utc(), previous_root=str(previous), previous_source_sha256=args.expected_previous_source_sha256,
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        laptop_required_during_execution=False, kernel_cpu_seconds=0.,
        scope='bounded numeric descendant completion after a CPU stop; no initial production')
    save = lambda: atomic_json(out / 'report.json', report)
    save()
    deadline = time.monotonic() + args.wait_timeout
    while True:
        if receipt_path.exists():
            actual = json.loads(receipt_path.read_text())
            try:
                state = resume.closed_worker(actual)
            except ValueError:
                state = None
            if state is not None:
                break
        require(time.monotonic() < deadline, 'predecessor did not close before the wait deadline')
        time.sleep(8)
    require(actual['source_unchanged'] and actual['expected_source_matches']
            and actual['source_sha256'] == args.expected_previous_source_sha256
            and source_identity(previous)['source_sha256'] == args.expected_previous_source_sha256,
            'terminal predecessor source identity changed')
    base = previous / 'results/nat-descendant6'
    prior_path = base / 'report.json'
    map_path = base / 'interface-map.json'
    prior = json.loads(prior_path.read_text())
    require(prior['checked_source']['source_sha256'] == args.expected_check_source_sha256
            and source_identity(base / 'check') == prior['checked_source']
            and prior['machine'] == assembly6.machine_identity(args.agda)
            and prior['machine']['agda_sha256'] == args.expected_agda_sha256
            and not prior['initial_problem2_proved'] and not prior['production_authorized'],
            'the exact same descendant and compiler are required')
    pins = dict(receipt_sha256=assembly6.sha(receipt_path), report_sha256=assembly6.sha(prior_path),
                map_sha256=assembly6.sha(map_path))
    report.update(predecessor_pins=pins, predecessor_closed_service=state,
                  predecessor_accepted_parts=prior['accepted_parts'])
    if actual['accepted'] and prior['accepted']:
        require(prior['descendant_original_lower_checked'], 'no completed original-rule descendant proof')
        report.update(accepted=True, status='predecessor-complete', finished_utc=utc(),
                      reused_complete_proof=True, descendant_original_lower_checked=True)
        save()
        return
    cpu_stop = actual['stop_reason'] == 'cpu-limit'
    if prior['phases'] and not prior['phases'][-1]['record']['accepted']:
        cpu_stop = cpu_stop or prior['phases'][-1]['record']['stop_reason'] == 'cpu-limit'
    report.update(status='authenticating-prefix', stopped_predecessor_cpu_limited=cpu_stop)
    save()
    require(cpu_stop, 'predecessor did not stop for CPU; no automatic retry of proof/memory/storage failure')
    report.update(status='resuming', resume_results='results/nat-finish6/resume')
    save()
    resume.run(SimpleNamespace(previous=previous, previous_results='results/nat-descendant6', output=out / 'resume',
        agda=args.agda, expected_agda_sha256=args.expected_agda_sha256,
        expected_previous_receipt_sha256=pins['receipt_sha256'], expected_previous_report_sha256=pins['report_sha256'],
        expected_previous_map_sha256=pins['map_sha256'], kernel_cpu_limit=args.kernel_cpu_limit))
    final = json.loads((out / 'resume/report.json').read_text())
    require(final['accepted'] and final['descendant_original_lower_checked'], 'resume did not complete')
    report.update(accepted=True, status='complete', finished_utc=utc(),
        kernel_cpu_seconds=final['kernel_cpu_seconds'], descendant_original_lower_checked=True,
        resume_report_sha256=assembly6.sha(out / 'resume/report.json'),
        resume_map_sha256=assembly6.sha(out / 'resume/interface-map.json'))
    save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('agda', 'expected-agda-sha256', 'expected-previous-source-sha256', 'expected-check-source-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--wait-timeout', type=float, default=11000)
    parser.add_argument('--kernel-cpu-limit', type=float, default=1800)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
