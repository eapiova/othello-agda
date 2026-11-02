#!/usr/bin/env python3
"""Check the one cold collector after all same-sample groups are accepted."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

import assembly6
from compact_logs6 import archive
from provenance import digest_entries,source_identity
from run_job import atomic_json,run_job
from memory_probe6 import rts_stats
from warning_tables6 import census_with_warnings


def run(args):
    previous=args.previous.resolve()
    if assembly6.sha(previous/'assembly.json')!=args.expected_report_sha256:
        raise ValueError('different completed-prefix report')
    if assembly6.sha(previous/'phase-records.json')!=args.expected_audit_sha256:
        raise ValueError('different completed-prefix audit')
    old=json.loads((previous/'assembly.json').read_text())
    audit=json.loads((previous/'phase-records.json').read_text())
    if (old['status']!='artifact-budget-stopped' or old['completed_groups']!=list(range(10)) or
            old['checked_sample_upper_roots']!=100 or len(old['phases'])!=274 or
            old['phases'][-1]['label']!='group9-bounds' or
            any(not p['accepted'] or not p['expected_outcome_met'] for p in old['phases'][1:])):
        raise ValueError('requires all 263 parts and ten accepted group bounds')
    root=Path(old['check_root']);identity=source_identity(root);before=assembly6.interfaces(root)
    machine=assembly6.machine_identity(args.agda)
    if (identity['source_sha256']!=old['source_sha256'] or identity['agda_source_sha256']!=old['agda_source_sha256'] or
            machine!=old['machine'] or before!=audit['final_interfaces'] or len(before)!=305 or
            digest_entries(old['generated_source_hashes'])!=args.expected_generated_sha256):
        raise ValueError('source/compiler/checked interface identity differs')
    if any(assembly6.sha(root/n)!=h for n,h in old['generated_source_hashes'].items()):
        raise ValueError('generated source differs')
    target='src/Tests/WarningTables6/All100.agda'
    suffix='/Tests/WarningTables6/All100.agdai'
    if any(n.endswith(suffix) for n in before):raise ValueError('collector not cold')
    runs=Path(__file__).resolve().parents[1].parent
    def usage():
        return dict(runs_bytes=int(subprocess.check_output(['du','-s','-B1',str(runs)]).split()[0]),
                    free_bytes=shutil.disk_usage(runs).free)
    start=usage()
    if start['runs_bytes']+1024**2>=10*1024**3 or start['free_bytes']<100*1024**3:
        raise ValueError('insufficient storage headroom for collector and receipts')
    args.output.mkdir(parents=True,exist_ok=False)
    record=run_job('warning-all100',[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
        '+RTS','-M2500M','-c','-s','-RTS'],args.output/'records',root=root,
        expected_source_sha256=identity['source_sha256'],cpu_limit=180,timeout=540,
        rss_limit_gib=3,log_limit_mib=2,metadata={'machine':machine,'own_target_cold':True,
            'borrowed_interfaces_sha256':digest_entries(before),'interface_isolation':'unchanged serial private cache'})
    after=assembly6.interfaces(root);changes=[n for n,h in before.items() if after.get(n)!=h]
    log=args.output/'records/warning-all100.log';text=log.read_text()
    metric={k:record[k] for k in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib','cache_state','stop_reason',
        'source_sha256','agda_source_sha256')}
    metric.update(label='warning-all100',target=target,exit_code=record['exit_code'],heap_mib=2500,
        rss_limit_gib=3,cache_changes=changes,rts=rts_stats(text),negative_fixture=False)
    own=[n for n in after if n.endswith(suffix)]
    accepted=record['accepted'] and not changes and len(after)==306 and len(own)==1
    if accepted:
        metric['interface']=census_with_warnings(root/own[0],after[own[0]])
        accepted=metric['interface']['unsupported_indexed_match_warnings']==0
    metric['accepted']=metric['expected_outcome_met']=bool(accepted)
    log_hash=assembly6.sha(log)
    if accepted:metric['archived_log']=archive(log,log_hash)
    if source_identity(root)!=identity:raise ValueError('source changed')
    totals=dict(old['interface_pool_totals'])
    if accepted:
        for key in totals:totals[key]+=metric['interface'][key]
    report=dict(format='othello-warning-collector6-v1',accepted=bool(accepted),phase=metric,
        source_sha256=identity['source_sha256'],agda_source_sha256=identity['agda_source_sha256'],
        machine=machine,previous=str(previous),previous_report_sha256=args.expected_report_sha256,
        previous_audit_sha256=args.expected_audit_sha256,check_root=str(root),
        checked_sample_upper_roots=100,reused_accepted_parts=263,reused_group_bounds=10,
        interfaces=len(after),interface_pool_totals=totals,initial_disk=start,final_disk=usage(),
        existing_interfaces_unchanged=not changes,source_unchanged=True,
        initial_problem2_proved=False,production_authorized=False)
    atomic_json(args.output/'collector.json',report)
    atomic_json(args.output/'phase-records.json',dict(record=record,
        record_sha256=assembly6.sha(args.output/'records/warning-all100.json'),log_sha256=log_hash,
        before_interfaces=before,final_interfaces=after))
    print(json.dumps({k:report[k] for k in ('accepted','interfaces','final_disk')}),flush=True)
    if not accepted:raise SystemExit('collector not accepted; retain failure without an unchanged retry')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-report-sha256','expected-audit-sha256','expected-generated-sha256'):
        p.add_argument('--'+name,required=True)
    run(p.parse_args())
