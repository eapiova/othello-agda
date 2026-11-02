#!/usr/bin/env python3
"""Share exact immutable source copies in the completed data-only pilot."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from archive_indexed_support6 import FROZEN, SOURCE
from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL='indexed-data-source-allocation-20261009'
CLEANUP='''import json,os,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
import assembly6
from owner_cache_dedup6 import allocated
from provenance import source_identity,source_files,digest_entries
from run_job import atomic_json,utc
label="data-only-wire-pilot-api-fixed-20261009"
unit=subprocess.run(["systemctl","--user","show","othello6-"+label+".service","-p","ActiveState","-p","MainPID"],capture_output=True,text=True,check=True).stdout
assert "ActiveState=active" not in unit and "MainPID=0" in unit
out=root/"results/indexed-data-source-allocation6.json";assert not out.exists()
report_path=root/"results/data-only-pilot6/report.json"
assert assembly6.sha(report_path)=="3cfbafef0089fdc3d214a7925b503f1254f4dcdfb6fd8ed09cc758d8e70f8b02"
d=json.loads(report_path.read_text());assert d["accepted"] and d["complete_all_local_rows"]
expected={}
for phase in d["phases"]+d["warm_phases"]:
 r=phase["record"];assert r["accepted"] and r["source_unchanged"] and r["expected_source_matches"]
 p=pathlib.Path(r["root"]);assert root in p.parents
 if str(p) in expected:assert expected[str(p)]==r["source_sha256"]
 expected[str(p)]=r["source_sha256"]
assert len(expected)==10
base=root/"results/data-only-pilot6/source";sources={};pools={};paths={}
for p in [base]+[pathlib.Path(p) for p in sorted(expected)]:
 identity=source_identity(p)
 if str(p) in expected:assert identity["source_sha256"]==expected[str(p)]
 sources[str(p)]=identity;pools[str(p)]=assembly6.interfaces(p)
 for name,raw in source_files(p):
  path=p/name;assert not path.is_symlink() and path.is_file()
  st=path.stat();h=assembly6.sha(path)
  key=(name,h,st.st_size,st.st_mtime_ns,st.st_mode,st.st_dev)
  paths.setdefault(key,[]).append(path)
replacements=[]
for key,group in paths.items():
 canonical=group[0]
 for path in group[1:]:
  if path.stat().st_ino==canonical.stat().st_ino:continue
  replacements.append(dict(path=str(path),canonical=str(canonical),sha256=key[1],bytes=key[2],mtime_ns=key[3],mode=key[4],device=key[5],original_inode=path.stat().st_ino))
receipt=dict(format="othello-indexed-source-allocation6-v1",status="prepared",created_utc=utc(),
 scope="exact immutable source allocation only; bytes, paths, modes, timestamps and proof interfaces preserved",
 rollback="copy2 canonical into a fresh temporary file and replace each target before editing or checking",
 source_identities=sources,interface_pool_sha256={p:digest_entries(v) for p,v in pools.items()},
 report_sha256=assembly6.sha(report_path),replacements=replacements,initial_allocated_bytes=allocated(root.parent))
atomic_json(out,receipt)
for row in replacements:
 path=pathlib.Path(row["path"]);canonical=pathlib.Path(row["canonical"])
 a=path.stat();b=canonical.stat();temporary=path.with_name(path.name+".source-allocation-tmp")
 assert not temporary.exists() and assembly6.sha(path)==row["sha256"] and assembly6.sha(canonical)==row["sha256"]
 assert (a.st_size,a.st_mtime_ns,a.st_mode,a.st_dev)==(b.st_size,b.st_mtime_ns,b.st_mode,b.st_dev)
 os.link(canonical,temporary);os.replace(temporary,path)
assert all(source_identity(pathlib.Path(p))==v for p,v in sources.items())
assert all(assembly6.interfaces(pathlib.Path(p))==v for p,v in pools.items())
assert assembly6.sha(report_path)==receipt["report_sha256"]
receipt.update(status="complete",finished_utc=utc(),sources_unchanged=True,interfaces_unchanged=True,
 final_allocated_bytes=allocated(root.parent),replaced_files=len(replacements))
receipt["recovered_source_allocated_bytes"]=sum(pathlib.Path(row["canonical"]).stat().st_blocks*512 for row in replacements)
atomic_json(out,receipt)
print(json.dumps({k:receipt[k] for k in ("status","replaced_files","recovered_source_allocated_bytes","initial_allocated_bytes","final_allocated_bytes")}))
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
 metadata={"purpose":"immutable checked data-only source allocation, no proof computation","inline_code_sha256":sys.argv[6]})
print(json.dumps(r))
'''
    atomic_json(out/'job.json',dict(label=LABEL,host='desktop',remote_root=FROZEN,
        reservation_id=reservation['reservation_id'],category='assembly',source_sha256=SOURCE,
        mode='capped terminal-root source allocation',inline_code_sha256=hashlib.sha256(CLEANUP.encode()).hexdigest()))
    reply=ssh('desktop',['python3','-c',wrapper,FROZEN,LABEL,reservation['reservation_id'],CLEANUP,SOURCE,hashlib.sha256(CLEANUP.encode()).hexdigest()])
    record=json.loads(reply.stdout);atomic_json(out/(LABEL+'.json'),record)
    ledger.finish(reservation['reservation_id'],out/(LABEL+'.json'))
    for name in (LABEL+'.log','indexed-data-source-allocation6.json'):
        (out/name).write_bytes(ssh('desktop',['cat',FROZEN+'/results/'+name]).stdout)
    print(json.dumps({k:record[k] for k in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib')}))
    if not record['accepted']:raise SystemExit('source allocation stopped; preserve the recorded mappings')


if __name__=='__main__':main()
