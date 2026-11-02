#!/usr/bin/env python3
"""Recover completed original-pilot log bytes; retain failures and proofs."""
import archive_warning_prefix6 as job

job.LABEL='original-global-log-archives-20261007'
job.RECEIPT='original-global-log-archives6.json'
job.CLEANUP='''import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/"tools"))
import assembly6
from compact_logs6 import archive
from provenance import source_identity,digest_entries
from run_job import atomic_json
base=Path(sys.argv[1]).parent
names=("six-kernel-global-upper100-20261006","six-kernel-global-upper100-resume-20261006")
before={};selected=[]
for name in names:
 root=base/name;before[name]=(source_identity(root),assembly6.interfaces(root))
 for path in sorted((root/"results").rglob("*.log")):
  rec=path.with_suffix(".json")
  if not rec.exists():continue
  data=json.loads(rec.read_text())
  if data.get("accepted") and data.get("source_unchanged") and data.get("exit_code")==0:
   selected.append((path,assembly6.sha(path),rec,assembly6.sha(rec)))
if len(selected)!=39:raise ValueError("different completed original-pilot logs")
receipt=dict(format="othello-original-global-log-archives6-v1",records=[],
 raw_digest_provenance="captured at archival; no previously recorded log digest is assumed")
out=Path(sys.argv[1])/"results/original-global-log-archives6.json"
for path,digest,rec,rec_hash in selected:
 row=archive(path,digest);row.update(directory=str(path.parent),record_sha256=rec_hash)
 receipt["records"].append(row);atomic_json(out,receipt)
 if assembly6.sha(rec)!=rec_hash:raise ValueError("receipt changed")
for name,(source,pool) in before.items():
 if source_identity(base/name)!=source or assembly6.interfaces(base/name)!=pool:raise ValueError("source or proof cache changed")
receipt.update(sources_unchanged=True,interfaces_unchanged=True,
 source_hashes={n:s["source_sha256"] for n,(s,p) in before.items()},
 interface_hashes={n:digest_entries(p) for n,(s,p) in before.items()},
 original_bytes=sum(r["original_bytes"] for r in receipt["records"]),
 archive_bytes=sum(r["archive_bytes"] for r in receipt["records"]))
atomic_json(out,receipt);print(json.dumps({k:v for k,v in receipt.items() if k!="records"}))
'''

if __name__=='__main__':job.main()
