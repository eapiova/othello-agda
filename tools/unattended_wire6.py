#!/usr/bin/env python3
"""Detached desktop continuation: fixed heldout check and four wire root checks.

The laptop reserves the entire envelope before launch. This driver never edits
a ledger, commits, publishes or emails. Every completed nested check and every
failure is checkpointed; accepted source/interface donors stay immutable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import time

import assembly6
import census_pilot6 as census
from owner_cache_dedup6 import allocated
from provenance import source_identity
from run_job import atomic_json, utc
import wire_pilot6 as wire


def closed_record(record, source_hash):
    if (record.get('accepted') is not True or record.get('source_unchanged') is not True or
            record.get('expected_source_matches') is not True or record.get('source_sha256')!=source_hash or
            record.get('stop_reason') is not None or record.get('exit_code')!=0):
        raise ValueError('preparation failed, hit a cap or changed source; no dependent checks launched')


def run(args):
    output=args.output.resolve()
    if output.exists() or 'results' not in output.parts:raise ValueError('fresh isolated output required')
    output.mkdir(parents=True)
    prepare=args.prepare_root.resolve();runs=prepare.parent
    machine=assembly6.machine_identity(args.agda)
    if machine['hostname']!=args.expected_hostname or machine['agda_sha256']!=args.expected_agda_sha256:
        raise ValueError('original desktop machine/compiler required')
    report=dict(format='othello-unattended-wire6-v1',status='waiting-for-native-preparation',accepted=False,
        created_utc=utc(),prepare_root=str(prepare),prepare_source_sha256=args.expected_prepare_source_sha256,
        cpu_budget=args.kernel_cpu_budget,kernel_cpu_seconds=0.,phases=[],machine=machine,
        production_authorized=False,initial_problem2_proved=False,laptop_required_during_execution=False)
    def save():atomic_json(output/'report.json',report)
    save()
    def guard(target=None):
        used=allocated(runs);free=shutil.disk_usage(runs).free
        if used>=10*1024**3 or free<100*1024**3:
            raise ValueError('desktop storage gate reached; accepted checkpoints preserved')
        report['last_storage_gate']=dict(allocated_runs_bytes=used,free_bytes=free,checked_utc=utc())
        save()
    guard()
    # Check the already frozen upper forecast while the independent native
    # preparation finishes. Its own build directory is separate.
    shared=dict(donor=args.donor,agda=args.agda,expected_hostname=args.expected_hostname,
        expected_agda_sha256=args.expected_agda_sha256,
        expected_donor_source_sha256=args.expected_donor_source_sha256,
        expected_generic_interfaces_sha256=args.expected_generic_interfaces_sha256,
        part_cpu_limit=120.,assembly_cpu_limit=180.)
    upper=argparse.Namespace(**shared,prepared=args.upper_prepared,output=output/'upper-heldout',
        expected_plan_sha256=args.expected_upper_plan_sha256,phase='heldout',
        training_report=args.upper_training_report,forecast=args.upper_forecast,
        expected_forecast_sha256=args.expected_upper_forecast_sha256,kernel_cpu_budget=180.)
    report['status']='checking-upper-heldout';save()
    accepted=census.check(upper,preflight=guard)
    checked=json.loads((upper.output/'report.json').read_text())
    report['kernel_cpu_seconds']+=checked['cpu_seconds']
    report['phases'].append(dict(label='upper-heldout',accepted=accepted,report=str(upper.output/'report.json'),
        report_sha256=assembly6.sha(upper.output/'report.json')))
    if not accepted:report['status']='upper-heldout-failed';save();return False
    native_record=prepare/'results/wire-root-prepare-20261008.json'
    deadline=time.monotonic()+args.wait_timeout
    report['status']='waiting-for-native-preparation';save()
    while not native_record.exists():
        if time.monotonic()>=deadline:
            report['status']='preparation-wait-timeout';save();return False
        guard();time.sleep(min(10.,max(.1,deadline-time.monotonic())))
    record=json.loads(native_record.read_text());closed_record(record,args.expected_prepare_source_sha256)
    if source_identity(prepare)['source_sha256']!=args.expected_prepare_source_sha256:
        raise ValueError('frozen preparation source changed')
    index=prepare/'results/wire-roots6/index.json';data=json.loads(index.read_text())
    cases=data.get('cases',[])
    if (data.get('format')!='othello-wire-root-study6-v1' or
            [c.get('label') for c in cases]!=['lower-ply16','upper-ply16','lower-ply14','upper-ply14']):
        raise ValueError('complete planned native case index required')
    report['prepare_record_sha256']=assembly6.sha(native_record);report['native_index_sha256']=assembly6.sha(index)
    report['native_censored_roots']=[]
    for case in cases:
        label=case['label']
        if case.get('native_complete') is not True:
            report['native_censored_roots'].append(label);save();continue
        relative=Path(case['prepared'])
        if relative.is_absolute() or '..' in relative.parts or relative.parts[:2]!=('results','wire-roots6'):
            raise ValueError('prepared path escapes the frozen native results')
        prepared=prepare/relative;plan=prepared/'plan.json'
        remaining=args.kernel_cpu_budget-report['kernel_cpu_seconds']
        if remaining<100:report['status']='internal-cpu-stop';save();return False
        check=argparse.Namespace(**shared,prepared=prepared,output=output/label,
            expected_plan_sha256=assembly6.sha(plan),phase='training',training_report=None,
            forecast=None,expected_forecast_sha256=None,kernel_cpu_budget=min(1200.,remaining-64))
        report['status']='checking-'+label;save()
        accepted=census.check(check,required_roots=1,expected_format=wire.FORMAT,preflight=guard)
        checked=json.loads((check.output/'report.json').read_text())
        report['kernel_cpu_seconds']+=checked['cpu_seconds']
        report['phases'].append(dict(label=label,accepted=accepted,report=str(check.output/'report.json'),
            report_sha256=assembly6.sha(check.output/'report.json'),plan_sha256=check.expected_plan_sha256,
            checked_parts=sum(p['target']['kind']=='part' for p in checked['phases']),
            peak_rss_gib=max((p['record']['peak_rss_gib'] for p in checked['phases']),default=0.)))
        save()
        if not accepted:report['status']='kernel-check-failed';save();return False
        guard()
    report['accepted']=not report['native_censored_roots']
    report['status']='complete-pilot' if report['accepted'] else 'complete-with-censored-native-roots'
    report['finished_utc']=utc();save()
    return report['accepted']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('prepare-root','donor','output','upper-prepared','upper-training-report','upper-forecast'):
        p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-hostname','expected-agda-sha256','expected-prepare-source-sha256',
                 'expected-donor-source-sha256','expected-generic-interfaces-sha256',
                 'expected-upper-plan-sha256','expected-upper-forecast-sha256'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--kernel-cpu-budget',type=float,default=5300.);p.add_argument('--wait-timeout',type=float,default=1500.)
    args=p.parse_args()
    if not 180<=args.kernel_cpu_budget<=5400 or not 1<=args.wait_timeout<=1800:p.error('invalid reserved queue caps')
    try:return 0 if run(args) else 1
    except Exception as error:
        report=args.output.resolve()/'report.json'
        if report.is_file():
            current=json.loads(report.read_text());current.update(status='driver-failed',accepted=False,
                error_type=type(error).__name__,error=str(error),finished_utc=utc());atomic_json(report,current)
        raise


if __name__=='__main__':raise SystemExit(main())
