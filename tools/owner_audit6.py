#!/usr/bin/env python3
"""Read-only audit of owner-directed lower pilot receipts and proof caches."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import assembly6
import lower_pilot6 as pilot
import owner_lower6 as owner
from provenance import digest_entries, source_identity
from run_job import atomic_json, utc


def audit(previous, expected):
    path=previous/'final.json'
    if assembly6.sha(path)!=expected:
        raise ValueError('final report differs from the coordinator identity')
    report=json.loads(path.read_text())
    if report['format'] not in ('othello-owner-lower6-training-v1','othello-owner-lower6-heldout-v1',
                                'othello-owner-lower6-split-v1','othello-rewrite-training6-v1',
                                'othello-rewrite-heldout6-v1'):
        raise ValueError('not an owner-directed lower pilot')
    root=Path(report['check_root'])
    pool=assembly6.interfaces(root)
    identity=source_identity(root)
    if (pool!=report['final_interfaces'] or digest_entries(pool)!=report['interfaces_sha256'] or
            identity['source_sha256']!=report['source_sha256'] or
            identity['agda_source_sha256']!=report['agda_source_sha256'] or
            not report['generated_sources_unchanged'] or
            report.get('certificate_parts_rechecked',report.get('existing_conditional_parts_rechecked'))!=0):
        raise ValueError('checked source or interfaces changed')
    generated=report.get('source_hashes',report.get('generated_source_hashes'))
    if not generated or any(assembly6.sha(root/name)!=digest for name,digest in generated.items()):
        raise ValueError('generated proof source differs')
    own={name:d for phase in report['phases'] for name,d in phase['own_interfaces'].items()}
    before={name:d for name,d in pool.items() if name not in own}
    if digest_entries(before)!=report['borrowed_interfaces_sha256']:
        raise ValueError('the original interface pool differs')
    recovered=0
    accepted=[]
    for phase in report['phases']:
        receipt=previous/'records'/(phase['label']+'.json')
        raw_record=json.loads(receipt.read_text())
        record=phase['record']
        if (raw_record!=record or assembly6.sha(receipt)!=phase['record_sha256'] or
                record['borrowed_interfaces_sha256']!=digest_entries(before) or
                record['executable_sha256']!=report['machine']['agda_sha256'] or
                not record['source_unchanged'] or not record['expected_source_matches'] or
                record['source_sha256']!=identity['source_sha256'] or
                not record['own_target_cold'] or phase['cache_changes'] or phase['unexpected_interfaces'] or
                not all(flag in record['argv'] for flag in assembly6.FLAGS+['--save-metas']) or
                f'-M{phase["heap_mib"]}M' not in record['argv'] or
                record['cpu_limit_seconds'] > phase['cpu_cap'] or
                record['rss_stop_threshold_gib']!=phase['rss_gib']):
            raise ValueError('receipt, flags, source or dependency provenance differs')
        directory = 'src/Tests/RewriteTraining6' if report['format'].startswith('othello-rewrite-') else owner.DIRECTORY
        suffix=pilot.target_suffix(phase['target'],directory)
        if any(name.endswith(suffix) for name in before):
            raise ValueError('an accepted target was repeated')
        if phase['accepted']:
            packed=phase['archived_log']
            archived=previous/'records'/packed['archive_name']
            raw=gzip.decompress(archived.read_bytes())
            if (not record['accepted'] or record['stop_reason'] or len(phase['own_interfaces'])!=1 or
                    not all(name.endswith(suffix) and pool.get(name)==d for name,d in phase['own_interfaces'].items()) or
                    assembly6.sha(archived)!=packed['archive_sha256'] or
                    hashlib.sha256(raw).hexdigest()!=phase['raw_log_sha256'] or
                    packed['original_sha256']!=phase['raw_log_sha256'] or
                    len(raw)!=record['log_bytes'] or len(raw)!=packed['original_bytes']):
                raise ValueError('accepted proof, log or interface no longer matches')
            before.update(phase['own_interfaces'])
            recovered+=len(raw)
            accepted.append(phase['label'])
        else:
            log=previous/'records'/(phase['label']+'.log')
            if (record['accepted'] or phase['own_interfaces'] or
                    assembly6.sha(log)!=phase['raw_log_sha256']):
                raise ValueError('failure record or log changed')
    if before!=pool:
        raise ValueError('final pool has an interface without an accepted receipt')
    expected_indices=([6,7,8,9] if report['format']=='othello-rewrite-training6-v1' else
                      list(range(10,20)) if report['format']=='othello-rewrite-heldout6-v1' else
                      owner.TRAINING if report['format'].endswith('training-v1') else
                      [5] if report['format'].endswith('split-v1') else owner.HELDOUT)
    if report['accepted'] and report['completed_indices']!=expected_indices:
        raise ValueError('a purported complete pilot is missing a root')
    return dict(format='othello-owner-lower6-audit-v1',status='complete',created_utc=utc(),
        report_sha256=expected,check_root=str(root),source_sha256=identity['source_sha256'],
        agda_source_sha256=identity['agda_source_sha256'],interfaces_sha256=digest_entries(pool),
        interfaces=len(pool),accepted_phases=len(accepted),exact_log_bytes_recovered=recovered,
        completed_indices=report['completed_indices'],checked_sample_lower_roots=report['checked_sample_lower_roots'],
        pilot_accepted=report['accepted'],pilot_status=report['status'],
        certificate_parts_rechecked=0,read_only=True,initial_problem2_proved=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--expected-report-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    r=audit(args.previous.resolve(),args.expected_report_sha256)
    atomic_json(args.output,r)
    print(json.dumps(r))
