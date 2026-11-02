#!/usr/bin/env python3
"""Recover room from accepted, terminal support-job logs without changing proofs."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL = 'indexed-support-log-archives-20261009'
FROZEN = '/home/eapiova/projects/othello-agda/runs/six-data-only-wire-pilot-api-fixed-20261009'
SOURCE = '2b7b25430a3c2e5b164a5dbb7972b7b6806c51cafab3f8de55146cad88071672'
PLAN = [
    ('data-only-wire-pilot-api-fixed-20261009', 'data-only-pilot6', SOURCE,
     '3cfbafef0089fdc3d214a7925b503f1254f4dcdfb6fd8ed09cc758d8e70f8b02', 269),
    ('wire-cut-ply10-resume-20261009', 'wire-resume6',
     'e109b43cffb90a5ba6ed5342b421bc6760daeffcb8732afd05e0aacb69b8e898',
     'e16cd54b53d86fbed2c24466d6a2611124f858f42dcd9bc9013305579adaf08a', 100),
    ('indexed-spike-desktop-20261009', 'indexed-spike6',
     '793de9f53dfc0dcd54706d7f3266ac53607881af082e769492b2ee328939c2cd',
     'f8f27f52b672e6b32913f3c2ca81e80511f678a4ac38e8de1c3b76d4b3440125', 7),
]
CLEANUP = '''import json,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
import assembly6
from compact_logs6 import archive
from owner_cache_dedup6 import allocated
from provenance import source_identity,digest_entries
from run_job import atomic_json,utc
plan=json.loads(sys.argv[2]);runs=root.parent
out=root/"results/indexed-support-log-archives6.json"
assert not out.exists(), "fresh archive receipt required"
protected={};pools={};sources={};selected=[]
for label,sub,expected_source,expected_report,count in plan:
 p=runs/("six-"+label)
 unit=subprocess.run(["systemctl","--user","show","othello6-"+label+".service","-p","ActiveState","-p","MainPID"],capture_output=True,text=True,check=True).stdout
 assert "ActiveState=active" not in unit and "MainPID=0" in unit, "support service still live"
 actual=p/"results"/(label+".json");rec=json.loads(actual.read_text())
 assert rec["accepted"] and rec["source_unchanged"] and rec["expected_source_matches"] and rec["source_sha256"]==expected_source
 source=source_identity(p);assert source["source_sha256"]==expected_source
 report=p/"results"/sub/"report.json"
 assert assembly6.sha(report)==expected_report and json.loads(report.read_text())["accepted"]
 protected[str(actual)]=assembly6.sha(actual);protected[str(report)]=expected_report
 sources[str(p)]=source;pools[str(p)]=assembly6.interfaces(p)
 entries=[]
 for rpath in sorted((p/"results"/sub/"records").glob("*.json")):
  r=json.loads(rpath.read_text());log=rpath.with_suffix(".log")
  if not r.get("accepted"):continue
  assert not log.is_symlink() and log.is_file() and not log.with_suffix(".log.gz").exists()
  assert r["source_unchanged"] and r["expected_source_matches"] and log.stat().st_size==r["log_bytes"]
  protected[str(rpath)]=assembly6.sha(rpath)
  entries.append(dict(path=str(log),sha256=assembly6.sha(log),bytes=log.stat().st_size))
 assert len(entries)==count, "accepted log set differs"
 selected.extend(entries)
receipt=dict(format="othello-indexed-support-log-archives6-v1",created_utc=utc(),status="archiving",
 scope="completed accepted support logs only; recover original bytes with gzip",selected_log_manifest=selected,
 protected_receipts=protected,source_identities=sources,interface_pool_sha256={p:digest_entries(v) for p,v in pools.items()},
 initial_allocated_bytes=allocated(runs),records=[])
atomic_json(out,receipt)
for entry in selected:
 path=pathlib.Path(entry["path"])
 row=archive(path,entry["sha256"]);row["directory"]=str(path.parent)
 receipt["records"].append(row);atomic_json(out,receipt)
assert all(source_identity(pathlib.Path(p))==v for p,v in sources.items())
assert all(assembly6.interfaces(pathlib.Path(p))==v for p,v in pools.items())
assert all(assembly6.sha(pathlib.Path(p))==h for p,h in protected.items())
receipt.update(status="complete",sources_unchanged=True,interfaces_unchanged=True,protected_receipts_unchanged=True,
 original_bytes=sum(r["original_bytes"] for r in receipt["records"]),archive_bytes=sum(r["archive_bytes"] for r in receipt["records"]),
 final_allocated_bytes=allocated(runs),finished_utc=utc())
atomic_json(out,receipt)
print(json.dumps({k:v for k,v in receipt.items() if k not in ("records","protected_receipts","selected_log_manifest")}))
'''


def main():
    root = Path(__file__).resolve().parents[1]
    output = root/'results/remote6'/LABEL
    output.mkdir(parents=True, exist_ok=False)
    ledger = Ledger(root/'results/study6-ledger.json')
    reservation = ledger.reserve('assembly', 27, LABEL)
    wrapper = '''import json,pathlib,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
from run_job import run_job
r=run_job(sys.argv[2],["python3","-c",sys.argv[4],str(root),sys.argv[5]],root/"results",root=root,
 timeout=100,cpu_limit=25,rss_limit_gib=.5,log_limit_mib=1,reservation_id=sys.argv[3],expected_source_sha256=sys.argv[6],
 metadata={"purpose":"verified lossless terminal-job log archival; no proof or gate changes","inline_code_sha256":sys.argv[7]})
print(json.dumps(r))
'''
    atomic_json(output/'job.json', dict(label=LABEL, host='desktop', remote_root=FROZEN,
        reservation_id=reservation['reservation_id'], category='assembly', mode='capped cleanup in terminal frozen root',
        source_sha256=SOURCE, inline_code_sha256=hashlib.sha256(CLEANUP.encode()).hexdigest()))
    reply = ssh('desktop', ['python3', '-c', wrapper, FROZEN, LABEL, reservation['reservation_id'],
        CLEANUP, json.dumps(PLAN), SOURCE, hashlib.sha256(CLEANUP.encode()).hexdigest()])
    record = json.loads(reply.stdout)
    atomic_json(output/(LABEL+'.json'), record)
    ledger.finish(reservation['reservation_id'], output/(LABEL+'.json'))
    for filename in (LABEL+'.log', 'indexed-support-log-archives6.json'):
        (output/filename).write_bytes(ssh('desktop', ['cat', FROZEN+'/results/'+filename]).stdout)
    print(json.dumps({k:record[k] for k in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib')}))
    if not record['accepted']:
        raise SystemExit('archival stopped; retain all receipts and inspect the failure')


if __name__ == '__main__':
    main()
