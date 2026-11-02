"""Journalled lossless wire conversion under the unchanged physical study cap.

Only the fresh UPPER wire may be truncated, after a durable exact tail copy.
Any interrupted conversion is recoverable from its journal, parts and raw prefix.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile
import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity
from run_job import atomic_json,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018/upper-wire-export6-20261018')
FAILED=SOURCE.with_name('upper-wire-compact6-20261018')
OUT=SOURCE.with_name('upper-wire-staged6-20261018');UNIT='othello6-'+OUT.name+'.service'
RAW=SOURCE/'initial-upper.wire';CHUNK=32*2**20;CAP=320*2**20
RESERVE=240;OUTER=210;ALLOWANCE=10
previous.OUT=OUT;common.OUT=OUT;common.HARD_GIB=2;common.RESERVATION_CPU=RESERVE


def fingerprint(path):
    s=path.stat();return [s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def durable_json(path,data):
    atomic_json(path,data)
    with path.open('rb') as f:os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def sync_file(path):
    with path.open('rb') as f:os.fsync(f.fileno())


def storage(frozen,reserve=0):
    own=batch.allocated(OUT);raw=RAW.stat().st_blocks*512 if RAW.exists() else 0
    used=frozen['prior_without_raw_allocated_bytes']+raw+own;free=shutil.disk_usage(ROOT).free
    assert own+reserve<=CAP and used+reserve<12*2**30
    assert free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
    return dict(allocated_study_bytes=used,own_output_bytes=own,raw_allocated_bytes=raw,
        root_free_bytes=free,data_free_bytes=shutil.disk_usage(OUT).free,reserved_bytes=reserve,checked_utc=utc())


def info(name,mode,ns):
    entry=zipfile.ZipInfo(name);entry.create_system=3;entry.external_attr=mode<<16
    entry.extra=struct.pack('<HHQ',0xa6da,8,ns);entry.compress_type=93;entry.compress_level=15
    return entry


def verified_bytes(archive,entry):
    h=hashlib.sha256();size=rows=0
    with zipfile.ZipFile(archive) as saved:
        assert saved.namelist()==[entry]
        with saved.open(entry) as f:
            for block in iter(lambda:f.read(2**20),b''):
                h.update(block);size+=len(block);rows+=block.count(b'\n')
    return dict(bytes=size,sha256=h.hexdigest(),rows=rows)


def worker():
    plan=json.loads((OUT/'plan.json').read_text());frozen=json.loads((OUT/'storage-freeze.json').read_text())
    assert common.sha(Path(__file__))==plan['helper_sha256']
    common.storage=lambda reserve=0:storage(frozen,reserve)
    wire=plan['wire'];assert RAW.stat().st_size==wire['bytes'] and common.sha(RAW)==wire['sha256']
    original=RAW.stat();current=fingerprint(RAW)
    journal=dict(format='othello-recoverable-wire-tail-journal-v1',created_utc=utc(),wire=wire,
        source=str(RAW),raw_fingerprint=current,verified_parts=[],original_source_mode=original.st_mode,
        original_source_mtime_ns=original.st_mtime_ns,raw_prefix_bytes=wire['bytes'],complete=False)
    durable_json(OUT/'journal.json',journal)
    with common.watched():
        count=(wire['bytes']+CHUNK-1)//CHUNK
        for index in reversed(range(count)):
            start=index*CHUNK;end=min(wire['bytes'],start+CHUNK)
            assert fingerprint(RAW)==current and RAW.stat().st_size==end
            archive=OUT/f'part-{index:05d}.zip';h=hashlib.sha256();copied=0
            with zipfile.ZipFile(archive,'x',compression=93,compresslevel=15) as saved:
                with RAW.open('rb') as source,saved.open(info('wire-part.bin',original.st_mode,original.st_mtime_ns),'w',force_zip64=True) as target:
                    source.seek(start);remaining=end-start
                    while remaining:
                        block=source.read(min(2**20,remaining));assert block
                        target.write(block);h.update(block);copied+=len(block);remaining-=len(block)
                        storage(frozen,8*2**20)
            sync_file(archive);restored=verified_bytes(archive,'wire-part.bin')
            assert restored['bytes']==copied==end-start and restored['sha256']==h.hexdigest()
            assert fingerprint(RAW)==current
            part=dict(index=index,start=start,end=end,archive=str(archive),entry='wire-part.bin',
                archive_bytes=archive.stat().st_size,archive_sha256=common.sha(archive),raw_sha256=h.hexdigest())
            journal['verified_parts'].append(part);journal['pending_truncation_to']=start
            durable_json(OUT/'journal.json',journal)
            # The archive and its journal are durable BEFORE releasing the tail.
            with RAW.open('r+b') as source:
                source.truncate(start);source.flush();os.fsync(source.fileno())
            current=fingerprint(RAW);journal.update(raw_fingerprint=current,raw_prefix_bytes=start,pending_truncation_to=None)
            durable_json(OUT/'journal.json',journal);storage(frozen,8*2**20)
        assert RAW.stat().st_size==0
        archive=OUT/'initial-upper.wire.zip';h=hashlib.sha256();size=rows=0
        with zipfile.ZipFile(archive,'x',compression=93,compresslevel=15) as saved:
            with saved.open(info('initial-upper.wire',original.st_mode,original.st_mtime_ns),'w',force_zip64=True) as target:
                for part in sorted(journal['verified_parts'],key=lambda x:x['index']):
                    assert common.sha(Path(part['archive']))==part['archive_sha256']
                    with zipfile.ZipFile(part['archive']) as chunk,chunk.open(part['entry']) as source:
                        for block in iter(lambda:source.read(2**20),b''):
                            target.write(block);h.update(block);size+=len(block);rows+=block.count(b'\n')
                            storage(frozen,8*2**20)
        sync_file(archive)
        assert h.hexdigest()==wire['sha256'] and size==wire['bytes'] and rows==wire['rows']
        restored=verified_bytes(archive,'initial-upper.wire')
        assert restored==dict(bytes=wire['bytes'],sha256=wire['sha256'],rows=wire['rows'])
        assert all(common.sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        journal.update(complete=True,finished_utc=utc(),consolidated_archive=str(archive),consolidated_archive_sha256=common.sha(archive))
        durable_json(OUT/'journal.json',journal)
        atomic_json(OUT/'roundtrip.json',dict(finished_utc=utc(),accepted=True,archive=str(archive),
            archive_bytes=archive.stat().st_size,archive_sha256=common.sha(archive),archive_entry='initial-upper.wire',
            compression_method='ZIP_ZSTANDARD93',compression_level=15,raw_sha256=wire['sha256'],raw_bytes=size,raw_rows=rows,
            exact_roundtrip_verified=True,parts=len(journal['verified_parts']),all_tails_durable_before_truncation=True,
            raw_prefix_bytes_remaining=0,p1_unchanged=True,old_desktop_runs_and_NAMOR_untouched=True,
            native_solver_runs=0,agda_checks=0,mathematical_objective_complete=False))


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    sandbox=previous.sandbox();sandbox=sandbox[:-1]+['--bind',str(RAW),str(RAW),'--']
    result=run_job(OUT.name,sandbox+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=360,cpu_limit=OUTER,rss_limit_gib=1.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    closed=json.loads((FAILED/'closure.json').read_text());assert not closed['accepted'] and closed['raw_original_preserved']
    prior=closed['combined_family_cpu_seconds'];assert prior+RESERVE+ALLOWANCE<=5650
    previous_storage=json.loads((FAILED/'storage-freeze.json').read_text())
    used=previous_storage['prior_allocated_study_bytes']+batch.allocated(FAILED)
    assert used+CHUNK+8*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir();control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),prior_allocated_study_bytes=used,
        prior_without_raw_allocated_bytes=used-RAW.stat().st_blocks*512,
        initial_raw_allocated_bytes=RAW.stat().st_blocks*512,own_output_cap_bytes=CAP,
        largest_input_segment_bytes=CHUNK,retained_study_cap_gib=12,root_free_floor_gib=80,
        rolling_actual_raw_allocation_counted=True,all_external_physical_bytes_counted=True))
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    plan=dict(created_utc=utc(),control_source=source_identity(control),helper_sha256=common.sha(Path(__file__)),
        python_binary_sha256=common.sha(Path(sys.executable)),python_version=sys.version,
        wire=json.loads((SOURCE/'wire-manifest.json').read_text()),p1_files=history['p1_files'],
        authorization='Authorized cleanup and necessary formalization storage: preserve every byte durably before releasing only fresh UPPER raw tails',
        previous_combined_family_cpu_seconds=prior,family_cpu_cap=5650,reservation=RESERVE,outer_cpu_cap=OUTER,
        new_controller_allowance_seconds=ALLOWANCE,hard_memory_gib=2,swap_bytes=0,core_bytes=0,
        recovery_journal=str(OUT/'journal.json'),original_historical_desktop_runs_writable=False,
        only_fresh_raw_wire_file_made_writable=True,accepted_proof=False,mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'One staged lossless recovery after whole-wire copy hit unchanged disk cap;32MiB durable tail copies, full consolidation/SHA roundtrip, all earlier global-native5650 charges preserved')
    reservation=ledger.reserve('assembly',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    argv=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=2G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=380','--property=WorkingDirectory='+str(control),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(argv,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=argv,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,family_envelope=prior+RESERVE+ALLOWANCE)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','supervise','worker']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
