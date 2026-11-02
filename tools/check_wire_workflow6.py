#!/usr/bin/env python3
"""Freeze an exact manifest for the six completed wire pilots, then audit it.

Run only on the checking desktop. This reads accepted frozen pilot roots; it
does not re-check Agda, modify a cache, write a ledger or authorize production.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import socket

import assembly6
from owner_cache_dedup6 import allocated
from run_job import atomic_json
import wire_workflow6 as workflow


def pin(path):
    return dict(path=str(path.resolve()), sha256=assembly6.sha(path))


def run(args):
    runs = args.runs_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    previous = runs/'six-wire-unattended-fixed-20261008/results/unattended-wire6/report.json'
    advance = runs/'six-wire-advance-reuse-ply12-20261008/results/wire-advance6/report.json'
    chains, pilots = [], []
    for final in (previous, advance):
        data = json.loads(final.read_text())
        children = {}
        for phase in data['phases']:
            label = phase['label']
            receipt = Path(phase.get('kernel_report', phase.get('report')))
            children[label] = pin(receipt)
            if label == 'upper-heldout':
                continue
            checked = json.loads(receipt.read_text())
            ply = int(label.rsplit('ply', 1)[1])
            native_dir = (advance.parent if ply == 12 else
                          runs/'six-wire-root-prepare-20261008/results/wire-roots6')
            native = native_dir/(label+'-native.json' if ply == 12 else label+'.json')
            pilots.append(dict(label=label, ply=ply, direction=label.split('-')[0],
                               report=pin(receipt), plan=pin(native_dir/(label+'-prepared/plan.json')),
                               native=pin(native), wire=pin(native_dir/(label+'.wire')),
                               prepared_root=str(native_dir/(label+'-prepared')),
                               check_root=checked['check_root']))
        spec = pin(final)
        spec['children'] = children
        chains.append(spec)
    global_dir = runs/'six-census-global-pilot-prepare-20261008/results'
    counts = {d:dict(receipt=pin(global_dir/('census-'+d+'-counts6.json')),
                   data=pin(global_dir/('census-'+d+'-data6.json')))
              for d in ('lower', 'upper')}
    manifest = dict(format='othello-wire-workflow6-input-v1',
        identity=dict(hostname='eapiova',
                      agda_sha256='c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842',
                      donor_source_sha256='e6d037a4fc2ff747dea8b9fd07341b9d7b560e1a5a7bcb6bbefc08f6fbb85518',
                      generic_interfaces_sha256='93b45a9830cb7d8ac5618ee2580aaa4aa70092530b81fcc5d7c517bf2d4ebe73'),
        line=pin(Path('certificates/six-line.json')),
        donor_root=str(runs/'six-rewrite-holdout-resume-20261008/results/rewrite-heldout6/check'),
        chains=chains, pilots=pilots, counts=counts, decode_interfaces=False,
        bounds=dict(cpu_hours=48, artifacts_gib=10, part_rss_gib=1.5, assembly_rss_gib=3,
                    allocated_artifacts_bytes=allocated(runs), free_disk_bytes=shutil.disk_usage(runs).free,
                    min_free_disk_gib=100))
    atomic_json(output/'input.json', manifest)
    workflow.require(socket.gethostname() == manifest['identity']['hostname'], 'original host required')
    frozen, digest = workflow.pinned(output, pin(output/'input.json'))
    result = workflow.audit(frozen, output)
    result['manifest_sha256'] = digest
    atomic_json(output/'report.json', result)
    print(json.dumps({k:result[k] for k in
        ('recommendation', 'failed_gates', 'accepted_pilot_audit',
         'combined_known_feature_partial_cpu_hours', 'combined_token_scaled_source_bytes',
         'combined_token_scaled_compressed_interface_bytes', 'measured_peak_rss_gib')}))
    return result['recommendation'] != 'NO_GO'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    return 0 if run(parser.parse_args()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
