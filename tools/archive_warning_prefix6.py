#!/usr/bin/env python3
"""Capped cleanup in an existing frozen run, so the storage gate stays fixed."""
import hashlib
import json
from pathlib import Path
import sys

from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL='warning-prefix-log-archives-20261007'
RECEIPT='warning-prefix-log-archives6.json'
FROZEN='/home/eapiova/projects/othello-agda/runs/six-warning-assembly-resume-20261007'
CLEANUP='''import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/"tools"))
import assembly6
from compact_logs6 import archive
from provenance import source_identity,digest_entries
from run_job import atomic_json
p=Path(sys.argv[1])/"results/warning-assembly6"
if assembly6.sha(p/"assembly.json")!="6a3389d7fc7a0ebe7fd4eba627e69869dd34225a17bd0adb87a3d92a8a43bda9":raise ValueError("report differs")
if assembly6.sha(p/"phase-records.json")!="7147bd1b79416badea98b42cec13a1054870f854e5153bee142e1e82b6256ed8":raise ValueError("audit differs")
r=json.loads((p/"assembly.json").read_text());a=json.loads((p/"phase-records.json").read_text())
root=Path(r["check_root"]);source=source_identity(root);pool=assembly6.interfaces(root)
if r["status"]!="artifact-budget-stopped" or r["completed_groups"]!=list(range(5)) or pool!=a["final_interfaces"] or len(pool)!=165 or source["source_sha256"]!=r["source_sha256"]:raise ValueError("checkpoint differs")
receipt=dict(format="othello-warning-prefix-log-archives6-v1",records={},source_sha256=source["source_sha256"],interfaces_sha256=digest_entries(pool))
out=Path(sys.argv[1])/"results/warning-prefix-log-archives6.json"
for phase in r["phases"][1:]:
 label=phase["label"];rec=a["records"][label]
 if not phase["accepted"] or not rec["accepted"]:raise ValueError("not a completed accepted phase")
 path=p/"records"/(label+".log")
 row=archive(path,a["log_hashes"][label]);row["directory"]=str(path.parent)
 receipt["records"][label]=row;atomic_json(out,receipt)
if source_identity(root)!=source or assembly6.interfaces(root)!=pool:raise ValueError("proof changed")
receipt.update(sources_unchanged=True,interfaces_unchanged=True,original_bytes=sum(v["original_bytes"] for v in receipt["records"].values()),archive_bytes=sum(v["archive_bytes"] for v in receipt["records"].values()))
atomic_json(out,receipt);print(json.dumps({k:v for k,v in receipt.items() if k!="records"}))
'''


def main():
    root=Path(__file__).resolve().parents[1]
    output=root/'results/remote6'/LABEL;output.mkdir(parents=True,exist_ok=False)
    ledger=Ledger(root/'results/study6-ledger.json')
    reservation=ledger.reserve('assembly',32,LABEL)
    wrapper='''from pathlib import Path
import sys,json
root=Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
from run_job import run_job
record=run_job(sys.argv[2],["python3","-c",sys.argv[4],str(root)],root/"results",root=root,
 cpu_limit=30,timeout=120,rss_limit_gib=.5,log_limit_mib=1,reservation_id=sys.argv[3],
 expected_source_sha256="dae3b08693f1c4542d0f029c912fd7655501cb2505a01d84c2d1e8adb511dfd8",
 metadata={"purpose":"recoverable log archival only; no Agda run or storage gate relaxation","inline_code_sha256":sys.argv[5]})
print(json.dumps(record))
'''
    args=['python3','-c',wrapper,FROZEN,LABEL,reservation['reservation_id'],CLEANUP,
          hashlib.sha256(CLEANUP.encode()).hexdigest()]
    atomic_json(output/'job.json',dict(label=LABEL,host='desktop',remote_root=FROZEN,
        reservation_id=reservation['reservation_id'],category='assembly',mode='capped synchronous cleanup in existing frozen run',
        inline_code_sha256=hashlib.sha256(CLEANUP.encode()).hexdigest()))
    reply=ssh('desktop',args)
    for filename in (LABEL+'.json',LABEL+'.log',RECEIPT):
        (output/filename).write_bytes(ssh('desktop',['cat',FROZEN+'/results/'+filename]).stdout)
    ledger.finish(reservation['reservation_id'],output/(LABEL+'.json'))
    record=json.loads((output/(LABEL+'.json')).read_text())
    print(json.dumps({k:record[k] for k in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib')}))
    if not record['accepted']:raise SystemExit('archive job failed; inspect retained receipts')


if __name__=='__main__':main()
