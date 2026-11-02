"""Coordinator reconciliation of one terminal bounded probe; no checker launch."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

import assembly6
from provenance import source_identity, digest_entries
from run_job import atomic_json, utc
from study6 import Ledger


def close(out, count, note, prior=None, scope=320, rows=200):
    root=Path(__file__).resolve().parents[1];out=Path(out).resolve()
    assert out.is_relative_to(root/'results') and not (out/'closure.json').exists()
    plan=json.loads((out/'plan.json').read_text());job=json.loads((out/'job.json').read_text())
    report=json.loads((out/'report.json').read_text())
    assert report['all_phases_accepted'] and report['accepted_donors_unchanged'] and report['p1_unchanged']
    assert source_identity(out/'check')==plan['source']
    interfaces=assembly6.interfaces(out/'check');assert len(interfaces)==count
    atomic_json(out/'interfaces.json',interfaces)
    frozen=out/'frozen-tools';frozen.mkdir()
    for name,pin in plan['helper_sha256'].items():
        source=root/'tools'/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==pin
        shutil.copy2(source,frozen/name)
    ledger=Ledger(root/'results/study6-ledger.json')
    actual=ledger.finish(job['reservation']['reservation_id'],out/'records'/(out.name+'.json'))
    priors=([prior] if isinstance(prior,Path) else prior) or []
    previous=[json.loads((Path(p)/'closure.json').read_text()) for p in priors]
    combined=actual['actual_cpu_seconds']+sum(p['charged_cpu_seconds'] for p in previous)+20
    assert combined<=scope
    journal=subprocess.run(['journalctl','--user','-u',job['unit'],'--no-pager','-n','8','-o','cat'],capture_output=True,text=True,check=True).stdout
    (out/'service-journal.log').write_text(journal)
    assert shutil.disk_usage(root).free-16*2**20>=80*2**30
    archive=out/'accepted-conditional-checkpoint.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for relative in ['check/src','check/_build','check/othello.agda-lib','records','plan.json','job.json','report.json','interfaces.json','frozen-tools','service-journal.log']:
            tar.add(out/relative,arcname=relative)
        for relative in ['formal-source-provenance.json','comparison-plan.json','forecast-freeze.json','holdout-comparison.json']:
            if (out/relative).exists():tar.add(out/relative,arcname=relative)
    summary=Ledger.summary(json.loads(ledger.path.read_text()))
    closure=dict(format='othello-bounded-probe-closure-v1',accepted=True,closed_utc=utc(),note=note,
        new_interfaces=count,new_distinct_rows=0,conditional_existing_rows=rows,
        source_sha256=plan['source']['source_sha256'],interface_pool_sha256=digest_entries(interfaces),
        charged_cpu_seconds=actual['actual_cpu_seconds'],shared_assembly_allowance_seconds=20,
        prior_attempts=[str(p) for p in priors],combined_scope_cpu_seconds=combined,scope_cap_cpu_seconds=scope,
        archive=str(archive.relative_to(root)),archive_bytes=archive.stat().st_size,
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),ledger_summary=summary,
        mathematical_objective_complete=False)
    atomic_json(out/'closure.json',closure)
    print(json.dumps(dict(closed=True,cpu_seconds=actual['actual_cpu_seconds'],available=summary['available_cpu_seconds'],kernel_available=summary['categories']['kernel']['available_cpu_seconds'],archive_bytes=archive.stat().st_size)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--interfaces',type=int,required=True)
    p.add_argument('--note',required=True);p.add_argument('--prior',type=Path,action='append');p.add_argument('--scope',type=int,default=320)
    p.add_argument('--rows',type=int,default=200)
    a=p.parse_args();close(a.out,a.interfaces,a.note,a.prior,a.scope,a.rows)
