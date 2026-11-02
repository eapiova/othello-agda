#!/usr/bin/env python3
"""Losslessly reclaim completed accepted logs with closed-run provenance."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from archive_indexed_support6 import FROZEN, SOURCE
from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL='terminal-log-archives-20261009'
CODE='''import json,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
import assembly6
from compact_logs6 import archive
from owner_cache_dedup6 import allocated
from provenance import source_identity,digest_entries
from run_job import atomic_json,utc
runs=root.parent;out=root/"results/terminal-log-archives6.json";assert not out.exists()
closed={};proof_roots={};protected={};selected=[];skipped=[]
for path in sorted(runs.rglob("*.log")):
 if path.is_symlink() or not path.is_file() or path.stat().st_blocks*512<32768:continue
 recpath=path.with_suffix(".json")
 if not recpath.is_file():continue
 try:rec=json.loads(recpath.read_text())
 except (OSError,ValueError):continue
 if not (rec.get("accepted") and rec.get("source_unchanged") and rec.get("expected_source_matches") and rec.get("finished_utc") and rec.get("exit_code")==0 and rec.get("stop_reason") is None):continue
 outer=path
 while outer.parent!=runs and outer!=outer.parent:outer=outer.parent
 if outer.parent!=runs or not outer.name.startswith("six-"):continue
 label=outer.name.removeprefix("six-")
 if label not in closed:
  ap=outer/"results"/(label+".json")
  if not ap.is_file():closed[label]=None;continue
  a=json.loads(ap.read_text());unit="othello6-"+label+".service"
  s=subprocess.run(["systemctl","--user","show",unit,"-p","LoadState","-p","ActiveState","-p","MainPID","-p","ControlPID"],capture_output=True,text=True,timeout=15)
  status=dict(line.split("=",1) for line in s.stdout.splitlines() if "=" in line)
  if not (s.returncode in (0,1) and status.get("LoadState") in ("loaded","not-found") and status.get("ActiveState") in ("inactive","failed") and status.get("MainPID")==status.get("ControlPID")=="0" and a.get("finished_utc") and a.get("source_unchanged") and a.get("expected_source_matches")):
   closed[label]=None;continue
  identity=source_identity(outer)
  if identity["source_sha256"]!=a["source_sha256"]:closed[label]=None;continue
  closed[label]=dict(root=str(outer),source=identity,status=status);protected[str(ap)]=assembly6.sha(ap)
 if closed[label] is None:continue
 checked=pathlib.Path(rec["root"])
 if not checked.is_relative_to(outer) or not checked.is_dir():continue
 if str(checked) not in proof_roots:
  proof_roots[str(checked)]=dict(source=source_identity(checked),interfaces=assembly6.interfaces(checked))
 if proof_roots[str(checked)]["source"]["source_sha256"]!=rec["source_sha256"]:
  skipped.append(str(path));continue
 assert path.stat().st_size==rec["log_bytes"]
 selected.append((path,assembly6.sha(path)));protected[str(recpath)]=assembly6.sha(recpath)
 assert len(selected)<=450
assert selected,"no eligible completed logs"
receipt=dict(format="othello-terminal-log-archives6-v1",status="prepared",created_utc=utc(),
 scope="accepted completed logs only, gzip round-trip verified; failed logs and all sources/interfaces/receipts preserved",
 protected_receipts=protected,closed_runs=closed,proof_roots={p:dict(source=d["source"],interface_pool_sha256=digest_entries(d["interfaces"])) for p,d in proof_roots.items()},
 skipped_source_mismatches=skipped,records=[],initial_allocated_study_bytes=allocated(runs))
atomic_json(out,receipt)
for path,h in selected:
 row=archive(path,h);row["directory"]=str(path.parent);receipt["records"].append(row)
atomic_json(out,receipt)
assert all(assembly6.sha(pathlib.Path(p))==h for p,h in protected.items())
assert all(source_identity(pathlib.Path(p))==d["source"] and assembly6.interfaces(pathlib.Path(p))==d["interfaces"] for p,d in proof_roots.items())
assert all(v is None or source_identity(pathlib.Path(v["root"]))==v["source"] for v in closed.values())
receipt.update(status="complete",finished_utc=utc(),sources_unchanged=True,interfaces_unchanged=True,receipts_unchanged=True,
 original_log_bytes=sum(x["original_bytes"] for x in receipt["records"]),archived_log_bytes=sum(x["archive_bytes"] for x in receipt["records"]),
 final_allocated_study_bytes=allocated(runs))
atomic_json(out,receipt)
print(json.dumps({k:receipt[k] for k in ("status","original_log_bytes","archived_log_bytes","initial_allocated_study_bytes","final_allocated_study_bytes")}))
'''


def main():
    root=Path(__file__).resolve().parents[1];out=root/'results/remote6'/LABEL
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger(root/'results/study6-ledger.json')
    reservation=ledger.reserve('assembly',47,LABEL)
    digest=hashlib.sha256(CODE.encode()).hexdigest()
    atomic_json(out/'job.json',dict(label=LABEL,host='desktop',remote_root=FROZEN,
        source_sha256=SOURCE,reservation_id=reservation['reservation_id'],category='assembly',inline_code_sha256=digest))
    wrapper='''import json,pathlib,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
from run_job import run_job
r=run_job(sys.argv[2],["python3","-c",sys.argv[4],str(root)],root/"results",root=root,
 timeout=120,cpu_limit=45,rss_limit_gib=.7,log_limit_mib=1,reservation_id=sys.argv[3],expected_source_sha256=sys.argv[5],
 metadata={"purpose":"verified lossless archival of closed accepted logs","inline_code_sha256":sys.argv[6]})
print(json.dumps(r))
'''
    r=json.loads(ssh('desktop',['python3','-c',wrapper,FROZEN,LABEL,reservation['reservation_id'],CODE,SOURCE,digest]).stdout)
    atomic_json(out/(LABEL+'.json'),r);ledger.finish(reservation['reservation_id'],out/(LABEL+'.json'))
    (out/(LABEL+'.log')).write_bytes(ssh('desktop',['cat',FROZEN+'/results/'+LABEL+'.log']).stdout)
    print(json.dumps({k:r[k] for k in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib')}))
    if not r['accepted']:raise SystemExit('archival stopped; retain receipts and do not rerun')
    (out/'terminal-log-archives6.json').write_bytes(ssh('desktop',['cat',FROZEN+'/results/terminal-log-archives6.json']).stdout)


if __name__=='__main__':main()
