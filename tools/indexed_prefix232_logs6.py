#!/usr/bin/env python3
"""Losslessly archive the 60 accepted logs of the closed 232-part prefix."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from archive_indexed_support6 import FROZEN, SOURCE
from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL='indexed-prefix232-logs-fixed-20261009'
CODE='''import json,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
import assembly6
from compact_logs6 import archive
from owner_cache_dedup6 import allocated
from provenance import source_identity,digest_entries
from run_job import atomic_json,utc
previous=root.parent/"six-indexed-wire-resume-20261009";base=previous/"results/indexed-wire-resume6"
rp=base/"report.json";mp=base/"interface-map.json";ap=previous/"results/indexed-wire-resume-20261009.json"
assert assembly6.sha(rp)=="83f573687b162e1cafb786b1f5fadde067b5d19a2545fc85102edb5f99d184fe"
assert assembly6.sha(mp)=="4d88e78ef673086e21721a041c80bd1107d2226086e95189d468d00c3832a632"
assert assembly6.sha(ap)=="e5a8cc5542a53a30cc45097091f228355603ef5a576aaf4e4ea83ad6656cf9eb"
report=json.loads(rp.read_text());actual=json.loads(ap.read_text())
result=subprocess.run(["systemctl","--user","show",actual["remote_unit"],"-p","LoadState","-p","ActiveState","-p","SubState","-p","MainPID","-p","ControlPID","-p","ExecMainStatus"],capture_output=True,text=True,timeout=15)
service=dict(s.split("=",1) for s in result.stdout.splitlines() if "=" in s)
assert result.returncode in (0,1) and service.get("LoadState") in ("loaded","not-found") and service.get("ActiveState") in ("inactive","failed") and service.get("SubState") in ("dead","failed") and service.get("MainPID")==service.get("ControlPID")=="0"
assert service["LoadState"]=="not-found" or service.get("ExecMainStatus")==str(actual["exit_code"])
assert actual["source_unchanged"] and actual["expected_source_matches"] and actual.get("finished_utc")
outer=source_identity(previous);assert outer["source_sha256"]==actual["source_sha256"]
check=base/"check";identity=source_identity(check);pool=assembly6.interfaces(check)
assert identity==report["checked_source"] and pool==json.loads(mp.read_text()) and digest_entries(pool)==report["last_interface_pool_sha256"]
assert report["reused_parts"]==172 and len(report["phases"])==61 and not report["phases"][-1]["record"]["accepted"]
out=root/"results/indexed-prefix232-log-archives6.json";assert not out.exists()
protected={str(p):assembly6.sha(p) for p in (rp,mp,ap)};selected=[]
for phase in report["phases"][:-1]:
 rec=phase["record"];assert rec["accepted"] and rec["source_unchanged"] and rec["expected_source_matches"]
 p=base/"records"/(rec["label"]+".log");assert p.is_file() and not p.is_symlink() and p.stat().st_size==rec["log_bytes"]
 selected.append((p,assembly6.sha(p)))
receipt=dict(format="othello-indexed-prefix232-log-archives6-v1",status="prepared",created_utc=utc(),
 scope="60 accepted terminal logs only; failed log stays plain; no source or proof changes",closed_service=service,
 protected_receipts=protected,checked_source=identity,interface_pool_sha256=digest_entries(pool),records=[],
 initial_allocated_study_bytes=allocated(root.parent))
atomic_json(out,receipt)
for p,h in selected:
 row=archive(p,h);row["directory"]=str(p.parent);receipt["records"].append(row);atomic_json(out,receipt)
assert source_identity(previous)==outer and source_identity(check)==identity and assembly6.interfaces(check)==pool
assert all(assembly6.sha(pathlib.Path(p))==h for p,h in protected.items())
receipt.update(status="complete",finished_utc=utc(),sources_unchanged=True,interfaces_unchanged=True,
 original_log_bytes=sum(p["original_bytes"] for p in receipt["records"]),
 archived_log_bytes=sum(p["archive_bytes"] for p in receipt["records"]),final_allocated_study_bytes=allocated(root.parent))
atomic_json(out,receipt)
print(json.dumps({k:v for k,v in receipt.items() if k not in ("records","protected_receipts")}))
'''


def main():
    root=Path(__file__).resolve().parents[1];out=root/'results/remote6'/LABEL
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger(root/'results/study6-ledger.json')
    reservation=ledger.reserve('assembly',17,LABEL)
    wrapper='''import pathlib,json,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
from run_job import run_job
r=run_job(sys.argv[2],["python3","-c",sys.argv[4],str(root)],root/"results",root=root,
 timeout=50,cpu_limit=15,rss_limit_gib=.5,log_limit_mib=1,reservation_id=sys.argv[3],expected_source_sha256=sys.argv[5],
 metadata={"purpose":"lossless terminal accepted log archival","inline_code_sha256":sys.argv[6]})
print(json.dumps(r))
'''
    digest=hashlib.sha256(CODE.encode()).hexdigest()
    atomic_json(out/'job.json',dict(label=LABEL,host='desktop',remote_root=FROZEN,source_sha256=SOURCE,
        reservation_id=reservation['reservation_id'],category='assembly',inline_code_sha256=digest))
    reply=ssh('desktop',['python3','-c',wrapper,FROZEN,LABEL,reservation['reservation_id'],CODE,SOURCE,digest])
    record=json.loads(reply.stdout);atomic_json(out/(LABEL+'.json'),record)
    ledger.finish(reservation['reservation_id'],out/(LABEL+'.json'))
    print(json.dumps({k:record[k] for k in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib')}))
    if not record['accepted']:
        (out/(LABEL+'.log')).write_bytes(ssh('desktop',['cat',FROZEN+'/results/'+LABEL+'.log']).stdout)
        raise SystemExit('archival stopped; preserve receipts')
    for name in (LABEL+'.log','indexed-prefix232-log-archives6.json'):
        (out/name).write_bytes(ssh('desktop',['cat',FROZEN+'/results/'+name]).stdout)


if __name__=='__main__':main()
