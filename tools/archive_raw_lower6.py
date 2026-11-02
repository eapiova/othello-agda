#!/usr/bin/env python3
"""Metered, reversible native-data archival inside an existing frozen run."""
import hashlib
import json
from pathlib import Path

from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL='raw-lower-archives-20261007'
FROZEN='/home/eapiova/projects/othello-agda/runs/six-warning-assembly-resume-20261007'
RECEIPT='raw-lower-archives6.json'
CODE='''import gzip,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/"tools"))
import assembly6
from provenance import source_identity,digest_entries
from run_job import atomic_json
base=Path(sys.argv[1]).parent
old=base/"six-native-lower120-profile-20261006"
done=json.loads((old/"results/native-lower120-profile-20261006.json").read_text())
if not done["accepted"] or done["exit_code"]!=0 or not done["source_unchanged"]:raise ValueError("profiling run not completed")
source=source_identity(old);pool=assembly6.interfaces(old)
donor=base/"six-warning-assembly-20261007/results/warning-assembly6/check"
donor_source=source_identity(donor);donor_pool=assembly6.interfaces(donor)
if donor_source["source_sha256"]!="ecf3b080d1808ee364b102610981e84e3397068159f5dd40caeba07a065097a0" or digest_entries(donor_pool)!="bea149de03ae625d6f9996d033fc6a65b99a0ae6ef825c5a081d4e799cba4ee1":raise ValueError("checked upper cache differs")
directory=old/"results/hint-profile6/lower120"
files=sorted(directory.glob("native-*.json"),key=lambda p:(p.stat().st_size,p.name))
if len(files)!=360:raise ValueError("different original raw-profile file set")
profile_hash=assembly6.sha(directory/"profile.json")
def allocated():return int(subprocess.check_output(["du","-s","-B1",str(base)]).split()[0])
start=allocated();out=Path(sys.argv[1])/"results/raw-lower-archives6.json"
receipt=dict(format="othello-raw-lower-archives6-v1",records=[],source_sha256=source["source_sha256"],
 scope="native JSON from completed raw profile only; canonical inputs, reports, source, proofs and logs untouched",
 raw_digest_provenance="captured at archival; capped and failing case contents remain recoverable",
 initial_runs_bytes=start,profile_sha256=profile_hash,maximum_runs_bytes=10*1024**3)
for path in files:
 if allocated()<=10*1024**3-256*1024**2:break
 room=10*1024**3-allocated()-128*1024
 if room<=0:raise ValueError("no archive staging headroom")
 raw_hash=assembly6.sha(path);raw_bytes=path.stat().st_size
 target=path.with_suffix(".json.gz");temporary=target.with_suffix(".tmp")
 if target.exists() or temporary.exists() or path.is_symlink():raise ValueError("archive target exists")
 try:
  with path.open("rb") as source_stream,temporary.open("xb") as destination:
   class Limited:
    def write(self,data):
     if destination.tell()+len(data)>room:raise ValueError("archive staging would exceed cap")
     return destination.write(data)
    def flush(self):return destination.flush()
    def tell(self):return destination.tell()
   with gzip.GzipFile(filename="",mode="wb",fileobj=Limited(),compresslevel=1,mtime=0) as packed:
    for chunk in iter(lambda:source_stream.read(1024*1024),b""):
     packed.write(chunk);packed.flush()
     if destination.tell()>room:raise ValueError("archive staging would exceed cap")
   destination.flush();os.fsync(destination.fileno())
  recovered=hashlib.sha256();count=0
  with gzip.open(temporary,"rb") as recovered_stream:
   for chunk in iter(lambda:recovered_stream.read(1024*1024),b""):
    recovered.update(chunk);count+=len(chunk)
  if recovered.hexdigest()!=raw_hash or count!=raw_bytes or assembly6.sha(path)!=raw_hash:raise ValueError("archive recovery differs")
  os.replace(temporary,target)
  row=dict(original=str(path),archive=str(target),original_sha256=raw_hash,archive_sha256=assembly6.sha(target),original_bytes=raw_bytes,archive_bytes=target.stat().st_size)
  receipt["records"].append(row);atomic_json(out,receipt)
  path.unlink()
 except BaseException:
  temporary.unlink(missing_ok=True)
  raise
if source_identity(old)!=source or assembly6.interfaces(old)!=pool or source_identity(donor)!=donor_source or assembly6.interfaces(donor)!=donor_pool or assembly6.sha(directory/"profile.json")!=profile_hash:raise ValueError("source/proof/report changed")
receipt.update(sources_unchanged=True,interfaces_unchanged=True,profile_unchanged=True,
 final_runs_bytes=allocated(),original_bytes=sum(r["original_bytes"] for r in receipt["records"]),archive_bytes=sum(r["archive_bytes"] for r in receipt["records"]))
atomic_json(out,receipt)
if receipt["final_runs_bytes"]>10*1024**3-192*1024**2:raise ValueError("insufficient recovered headroom")
print(json.dumps({k:v for k,v in receipt.items() if k!="records"}))
'''


def main():
    root=Path(__file__).resolve().parents[1]
    output=root/'results/remote6'/LABEL;output.mkdir(parents=True,exist_ok=False)
    ledger=Ledger(root/'results/study6-ledger.json');reservation=ledger.reserve('assembly',92,LABEL)
    wrapper='''from pathlib import Path
import sys,json
root=Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
from run_job import run_job
r=run_job(sys.argv[2],["python3","-c",sys.argv[4],str(root)],root/"results",root=root,
 cpu_limit=90,timeout=600,rss_limit_gib=.5,log_limit_mib=1,reservation_id=sys.argv[3],
 expected_source_sha256="dae3b08693f1c4542d0f029c912fd7655501cb2505a01d84c2d1e8adb511dfd8",
 metadata={"purpose":"streaming reversible archival of native JSON; no Agda or cap relaxation","inline_code_sha256":sys.argv[5]})
print(json.dumps(r))
'''
    digest=hashlib.sha256(CODE.encode()).hexdigest()
    atomic_json(output/'job.json',dict(label=LABEL,remote_root=FROZEN,host='desktop',category='assembly',
        reservation_id=reservation['reservation_id'],inline_code_sha256=digest,mode='capped existing-root housekeeping'))
    ssh('desktop',['python3','-c',wrapper,FROZEN,LABEL,reservation['reservation_id'],CODE,digest])
    for name in (LABEL+'.json',LABEL+'.log',RECEIPT):
        (output/name).write_bytes(ssh('desktop',['cat',FROZEN+'/results/'+name]).stdout)
    ledger.finish(reservation['reservation_id'],output/(LABEL+'.json'))
    record=json.loads((output/(LABEL+'.json')).read_text())
    print(json.dumps({k:record[k] for k in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib')}))
    if not record['accepted']:raise SystemExit('archival failed; retain receipts and stop')


if __name__=='__main__':main()
