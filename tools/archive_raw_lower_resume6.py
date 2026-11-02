#!/usr/bin/env python3
"""Complete reversible archival with block accounting, not repeated tree scans."""
import hashlib
import json
from pathlib import Path

from archive_raw_lower6 import CODE as ORIGINAL, FROZEN
from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL = 'raw-lower-archives-resume-20261007'
RECEIPT = 'raw-lower-archives-resume6.json'


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('archival template differs')
    return text.replace(before, after, 1)


def code():
    text = replace_once(ORIGINAL,
        'files=sorted(directory.glob("native-*.json"),key=lambda p:(p.stat().st_size,p.name))\nif len(files)!=360:raise ValueError("different original raw-profile file set")',
        '''previous_path=Path(sys.argv[1])/"results/raw-lower-archives6.json"
previous=json.loads(previous_path.read_text());previous_hash=assembly6.sha(previous_path)
if previous["source_sha256"]!=source["source_sha256"]:raise ValueError("previous source identity differs")
for row in previous["records"]:
 raw=Path(row["original"]);packed=Path(row["archive"])
 if raw.exists() or not packed.is_file() or packed.parent!=directory or assembly6.sha(packed)!=row["archive_sha256"]:raise ValueError("previous archive changed")
files=sorted(directory.glob("native-*.json"),key=lambda p:(-p.stat().st_size,p.name))
if len(files)+len(previous["records"])!=360:raise ValueError("different original raw-profile file set")''')
    # Only the output path changes; the earlier receipt remains immutable.
    text = replace_once(text, 'out=Path(sys.argv[1])/"results/raw-lower-archives6.json"',
        'estimate=start;out=Path(sys.argv[1])/"results/raw-lower-archives-resume6.json"')
    text = replace_once(text, 'initial_runs_bytes=start,profile_sha256=profile_hash,maximum_runs_bytes=10*1024**3)',
        'initial_runs_bytes=start,profile_sha256=profile_hash,maximum_runs_bytes=10*1024**3,previous_receipt_sha256=previous_hash,previous_archives=len(previous["records"]),accounting="initial du plus st_blocks deltas; final du; one MiB metadata reserve")')
    text = replace_once(text, 'if allocated()<=10*1024**3-256*1024**2:break',
        'if estimate<=10*1024**3-256*1024**2:break')
    text = replace_once(text, 'room=10*1024**3-allocated()-128*1024',
        'room=10*1024**3-estimate-1024**2')
    text = replace_once(text, 'raw_hash=assembly6.sha(path);raw_bytes=path.stat().st_size',
        'raw_hash=assembly6.sha(path);raw_bytes=path.stat().st_size;raw_blocks=path.stat().st_blocks*512')
    text = replace_once(text, 'path.unlink()\n except BaseException:',
        'path.unlink();estimate+=target.stat().st_blocks*512-raw_blocks\n except BaseException:')
    return text


def main():
    root = Path(__file__).resolve().parents[1]
    output = root/'results/remote6'/LABEL
    output.mkdir(parents=True, exist_ok=False)
    ledger = Ledger(root/'results/study6-ledger.json')
    reservation = ledger.reserve('assembly', 47, LABEL)
    inline = code()
    digest = hashlib.sha256(inline.encode()).hexdigest()
    wrapper = '''from pathlib import Path
import sys,json
root=Path(sys.argv[1]);sys.path.insert(0,str(root/"tools"))
from run_job import run_job
r=run_job(sys.argv[2],["python3","-c",sys.argv[4],str(root)],root/"results",root=root,
 cpu_limit=45,timeout=180,rss_limit_gib=.5,log_limit_mib=1,reservation_id=sys.argv[3],
 expected_source_sha256="dae3b08693f1c4542d0f029c912fd7655501cb2505a01d84c2d1e8adb511dfd8",
 metadata={"purpose":"corrected streaming archival using block deltas; no proof or cap changes","inline_code_sha256":sys.argv[5]})
print(json.dumps(r))
'''
    atomic_json(output/'job.json', dict(label=LABEL, remote_root=FROZEN, host='desktop',
        category='assembly', reservation_id=reservation['reservation_id'],
        inline_code_sha256=digest, mode='capped existing-root housekeeping'))
    ssh('desktop', ['python3', '-c', wrapper, FROZEN, LABEL, reservation['reservation_id'], inline, digest])
    for name in (LABEL+'.json', LABEL+'.log', RECEIPT):
        (output/name).write_bytes(ssh('desktop', ['cat', FROZEN+'/results/'+name]).stdout)
    ledger.finish(reservation['reservation_id'], output/(LABEL+'.json'))
    record = json.loads((output/(LABEL+'.json')).read_text())
    receipt = json.loads((output/RECEIPT).read_text())
    print(json.dumps(dict(accepted=record['accepted'], cpu_seconds=record['cpu_seconds'],
        wall_seconds=record['wall_seconds'], archives=len(receipt['records']),
        final_runs_bytes=receipt.get('final_runs_bytes'),
        sources_unchanged=receipt.get('sources_unchanged'),
        interfaces_unchanged=receipt.get('interfaces_unchanged'))))
    if not record['accepted']:
        raise SystemExit('retain receipts and stop')


if __name__ == '__main__':
    main()
