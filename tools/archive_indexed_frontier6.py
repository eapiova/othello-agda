#!/usr/bin/env python3
"""Losslessly archive a closed native frontier JSON to fund final assembly."""
import hashlib
import json
from pathlib import Path

from archive_indexed_support6 import FROZEN, SOURCE
from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL='indexed-frontier-archive-20261009'
CODE='''import json,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
import assembly6
from archive_closed_native6 import stream_archive
from owner_cache_dedup6 import allocated
from provenance import source_identity
from run_job import atomic_json,utc
previous=root.parent/"six-native-upper22-cached-fixed-20261006";label=previous.name.removeprefix("six-")
actual=previous/"results"/(label+".json");record=json.loads(actual.read_text())
status=subprocess.run(["systemctl","--user","show","othello6-"+label+".service","-p","ActiveState","-p","MainPID","-p","ControlPID"],capture_output=True,text=True,timeout=15)
state=dict(s.split("=",1) for s in status.stdout.splitlines() if "=" in s)
assert status.returncode in (0,1) and state.get("ActiveState") in ("inactive","failed") and state.get("MainPID")==state.get("ControlPID")=="0"
assert record.get("finished_utc") and record["source_unchanged"] and record["expected_source_matches"]
source=source_identity(previous);pool=assembly6.interfaces(previous);assert source["source_sha256"]==record["source_sha256"]
path=previous/"results/native6/upper22.json";assert path.is_file() and not path.is_symlink()
out=root/"results/indexed-frontier-archive6.json";assert not out.exists()
before=allocated(root.parent);room=10*2**30-before-2*2**20;assert room>0
receipt=dict(format="othello-indexed-frontier-archive6-v1",status="prepared",created_utc=utc(),
 scope="closed untrusted frontier JSON only; exact bytes recoverable; no proof caches, TT or source changes",
 closed_service=state,source=source,actual_receipt_sha256=assembly6.sha(actual),initial_allocated_study_bytes=before,
 restore="gzip -dc archived JSON into a fresh path before any later consumer requiring the raw name")
atomic_json(out,receipt)
row=stream_archive(path,room);receipt["archive"]=row;atomic_json(out,receipt)
path.unlink()
assert source_identity(previous)==source and assembly6.interfaces(previous)==pool and assembly6.sha(actual)==receipt["actual_receipt_sha256"]
receipt.update(status="complete",finished_utc=utc(),sources_unchanged=True,interfaces_unchanged=True,receipts_unchanged=True,
 final_allocated_study_bytes=allocated(root.parent))
atomic_json(out,receipt)
print(json.dumps({k:receipt[k] for k in ("status","archive","initial_allocated_study_bytes","final_allocated_study_bytes")}))
'''


def main():
    root=Path(__file__).resolve().parents[1];out=root/'results/remote6'/LABEL;out.mkdir(parents=True,exist_ok=False)
    ledger=Ledger(root/'results/study6-ledger.json');reservation=ledger.reserve('assembly',47,LABEL)
    digest=hashlib.sha256(CODE.encode()).hexdigest()
    atomic_json(out/'job.json',dict(label=LABEL,host='desktop',remote_root=FROZEN,source_sha256=SOURCE,
        reservation_id=reservation['reservation_id'],category='assembly',inline_code_sha256=digest))
    wrapper='''import json,pathlib,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
from run_job import run_job
r=run_job(sys.argv[2],["python3","-c",sys.argv[4],str(root)],root/"results",root=root,
 timeout=100,cpu_limit=45,rss_limit_gib=.5,log_limit_mib=1,reservation_id=sys.argv[3],expected_source_sha256=sys.argv[5],
 metadata={"purpose":"lossless closed untrusted frontier archival","inline_code_sha256":sys.argv[6]})
print(json.dumps(r))
'''
    r=json.loads(ssh('desktop',['python3','-c',wrapper,FROZEN,LABEL,reservation['reservation_id'],CODE,SOURCE,digest]).stdout)
    atomic_json(out/(LABEL+'.json'),r);ledger.finish(reservation['reservation_id'],out/(LABEL+'.json'))
    (out/(LABEL+'.log')).write_bytes(ssh('desktop',['cat',FROZEN+'/results/'+LABEL+'.log']).stdout)
    print(json.dumps({k:r[k] for k in ('accepted','cpu_seconds','peak_rss_gib')}))
    if not r['accepted']:raise SystemExit('frontier archive stopped; retain raw data and receipt')
    (out/'indexed-frontier-archive6.json').write_bytes(ssh('desktop',['cat',FROZEN+'/results/indexed-frontier-archive6.json']).stdout)


if __name__=='__main__':main()
