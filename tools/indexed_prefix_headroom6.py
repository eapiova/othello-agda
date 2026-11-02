#!/usr/bin/env python3
"""Preserve a capped indexed prefix while reclaiming immutable duplicates."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from archive_indexed_support6 import FROZEN, SOURCE
from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL='indexed-prefix-headroom-20261009'
CLEANUP='''import json,os,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
import assembly6
from compact_logs6 import archive
from owner_cache_dedup6 import allocated
from provenance import source_identity,digest_entries
from run_job import atomic_json,utc
runs=root.parent;out=root/"results/indexed-prefix-headroom6.json";assert not out.exists()
prefix=runs/"six-indexed-wire-pilot-fixed-20261009"
report_path=prefix/"results/indexed-wire6/report.json"
assert assembly6.sha(report_path)=="3ebe3636d784dc95ba2a4f31011a82e370ab1fda023df0770185017cc6ef4aa3"
d=json.loads(report_path.read_text());assert d["accepted_parts"]==172 and len(d["phases"])==173
assert not d["phases"][-1]["record"]["accepted"] and d["phases"][-1]["record"]["stop_reason"]=="cpu-limit"
check=prefix/"results/indexed-wire6/check";pool=assembly6.interfaces(check)
assert digest_entries(pool)==d["last_interface_pool_sha256"]
source=source_identity(check);assert source==d["checked_source"]
selected=[];protected={str(report_path):assembly6.sha(report_path)}
for p in d["phases"][:-1]:
 rec=p["record"];assert rec["accepted"] and rec["source_unchanged"] and rec["expected_source_matches"]
 path=prefix/"results/indexed-wire6/records"/(rec["label"]+".log")
 assert path.is_file() and not path.is_symlink() and path.stat().st_size==rec["log_bytes"]
 selected.append(dict(path=str(path),sha256=assembly6.sha(path)))
donor=runs/"six-rewrite-holdout-resume-20261008/results/rewrite-heldout6/check"
donor_source=source_identity(donor);donor_pool=assembly6.interfaces(donor)
generic={p:h for p,h in donor_pool.items() if "/src/Tests/" not in p}
assert len(generic)==31 and digest_entries(generic)=="93b45a9830cb7d8ac5618ee2580aaa4aa70092530b81fcc5d7c517bf2d4ebe73"
base=root/"results/data-only-pilot6";r=json.loads((base/"report.json").read_text())
work_roots={pathlib.Path(p["record"]["root"]) for p in r["phases"]+r["warm_phases"]}
work_roots|={check,runs/"six-indexed-spike-desktop-20261009/results/indexed-spike6/check",runs/"six-indexed-tree-pilot-20261009/results/indexed-tree6/check",runs/"six-indexed-everything-desktop-20261009/results/indexed-everything6/check"}
# The last older whole-core layout can differ: only existing exact matches
# below the verified immutable job are eligible.
work_roots={p for p in work_roots if p.is_dir()}
roots={};replacement=[];seen=set()
for p in sorted(work_roots):
 outer=p
 while outer.parent!=runs:outer=outer.parent
 label=outer.name.removeprefix("six-")
 unit=subprocess.run(["systemctl","--user","show","othello6-"+label+".service","-p","ActiveState","-p","MainPID"],capture_output=True,text=True,check=True).stdout
 assert "ActiveState=active" not in unit and "MainPID=0" in unit
 actual=outer/"results"/(label+".json");rec=json.loads(actual.read_text())
 assert rec.get("finished_utc") and rec["source_unchanged"] and rec["expected_source_matches"]
 identity=source_identity(p);interfaces=assembly6.interfaces(p)
 roots[str(p)]=dict(source=identity,pool=interfaces);protected[str(actual)]=assembly6.sha(actual)
 for name,h in generic.items():
  target=p/name;canonical=donor/name
  if interfaces.get(name)!=h or not target.is_file():continue
  a=target.stat();b=canonical.stat()
  if (a.st_dev,a.st_ino)==(b.st_dev,b.st_ino):continue
  if (a.st_size,a.st_mtime_ns,a.st_mode,a.st_dev)!=(b.st_size,b.st_mtime_ns,b.st_mode,b.st_dev):continue
  assert not target.is_symlink() and not canonical.is_symlink() and assembly6.sha(target)==h
  if str(target) in seen:continue
  seen.add(str(target));replacement.append(dict(path=str(target),canonical=str(canonical),sha256=h,mtime_ns=a.st_mtime_ns,mode=a.st_mode,original_inode=a.st_ino))
receipt=dict(format="othello-indexed-prefix-headroom6-v1",status="prepared",created_utc=utc(),
 scope="accepted terminal-prefix logs and identical terminal generic-cache allocation; no new proof claims",
 source=source,interface_pool_sha256=digest_entries(pool),protected_receipts=protected,
 selected_logs=selected,replacements=replacement,records=[],initial_allocated_bytes=allocated(runs),
 rollback="gzip restores raw logs; copy2 each canonical interface before any future mutable check")
atomic_json(out,receipt)
for entry in selected:
 p=pathlib.Path(entry["path"]);row=archive(p,entry["sha256"]);row["directory"]=str(p.parent)
 receipt["records"].append(row)
atomic_json(out,receipt)
for row in replacement:
 target=pathlib.Path(row["path"]);canonical=pathlib.Path(row["canonical"]);tmp=target.with_name(target.name+".closed-share-tmp")
 assert not tmp.exists() and assembly6.sha(target)==row["sha256"] and assembly6.sha(canonical)==row["sha256"]
 assert (target.stat().st_mtime_ns,target.stat().st_mode)==(row["mtime_ns"],row["mode"])
 os.link(canonical,tmp);os.replace(tmp,target)
assert source_identity(check)==source and assembly6.interfaces(check)==pool
assert source_identity(donor)==donor_source and assembly6.interfaces(donor)==donor_pool
assert all(source_identity(pathlib.Path(p))==v["source"] and assembly6.interfaces(pathlib.Path(p))==v["pool"] for p,v in roots.items())
assert all(assembly6.sha(pathlib.Path(p))==h for p,h in protected.items())
receipt.update(status="complete",finished_utc=utc(),sources_unchanged=True,interface_bytes_unchanged=True,protected_receipts_unchanged=True,
 original_log_bytes=sum(r["original_bytes"] for r in receipt["records"]),archive_log_bytes=sum(r["archive_bytes"] for r in receipt["records"]),
 replaced_generic_interfaces=len(replacement),final_allocated_bytes=allocated(runs))
atomic_json(out,receipt)
print(json.dumps({k:receipt[k] for k in ("status","original_log_bytes","archive_log_bytes","replaced_generic_interfaces","initial_allocated_bytes","final_allocated_bytes")}))
'''


def main():
    root=Path(__file__).resolve().parents[1];out=root/'results/remote6'/LABEL
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger(root/'results/study6-ledger.json')
    reservation=ledger.reserve('assembly',27,LABEL)
    wrapper='''import pathlib,json,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
from run_job import run_job
r=run_job(sys.argv[2],["python3","-c",sys.argv[4],str(root)],root/"results",root=root,
 timeout=100,cpu_limit=25,rss_limit_gib=.5,log_limit_mib=1,reservation_id=sys.argv[3],expected_source_sha256=sys.argv[5],
 metadata={"purpose":"preserve capped prefix and reclaim exact terminal duplicates","inline_code_sha256":sys.argv[6]})
print(json.dumps(r))
'''
    atomic_json(out/'job.json',dict(label=LABEL,host='desktop',remote_root=FROZEN,source_sha256=SOURCE,
        reservation_id=reservation['reservation_id'],category='assembly',mode='capped terminal-root headroom recovery',
        inline_code_sha256=hashlib.sha256(CLEANUP.encode()).hexdigest()))
    reply=ssh('desktop',['python3','-c',wrapper,FROZEN,LABEL,reservation['reservation_id'],CLEANUP,SOURCE,hashlib.sha256(CLEANUP.encode()).hexdigest()])
    record=json.loads(reply.stdout);atomic_json(out/(LABEL+'.json'),record)
    ledger.finish(reservation['reservation_id'],out/(LABEL+'.json'))
    for name in (LABEL+'.log','indexed-prefix-headroom6.json'):
        (out/name).write_bytes(ssh('desktop',['cat',FROZEN+'/results/'+name]).stdout)
    print(json.dumps({k:record[k] for k in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib')}))
    if not record['accepted']:raise SystemExit('prefix headroom recovery stopped; retain all receipts')


if __name__=='__main__':main()
