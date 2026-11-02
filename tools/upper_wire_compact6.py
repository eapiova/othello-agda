"""Lossless ZIP/Zstandard container for the fresh UPPER wire; no proof job."""
import hashlib
import json
from pathlib import Path
import shutil
import stat
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
OUT=SOURCE.with_name('upper-wire-compact6-20261018')
UNIT='othello6-'+OUT.name+'.service'
CAP=80*2**20;RESERVE=120;OUTER=100;ALLOWANCE=5
previous.OUT=OUT;common.OUT=OUT;common.HARD_GIB=2;common.RESERVATION_CPU=RESERVE


def storage(frozen,reserve=0):
    own=batch.allocated(OUT);free=shutil.disk_usage(ROOT).free
    assert own+reserve<=CAP and frozen['prior_allocated_study_bytes']+own+reserve<12*2**30
    assert free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
    return dict(allocated_study_bytes=frozen['prior_allocated_study_bytes']+own,own_output_bytes=own,
        root_free_bytes=free,data_free_bytes=shutil.disk_usage(OUT).free,reserved_bytes=reserve,checked_utc=utc())


def worker():
    plan=json.loads((OUT/'plan.json').read_text());frozen=json.loads((OUT/'storage-freeze.json').read_text())
    assert common.sha(Path(__file__))==plan['helper_sha256']
    assert common.sha(Path(sys.executable))==plan['python_binary_sha256']
    common.storage=lambda reserve=0:storage(frozen,reserve)
    manifest=plan['wire'];path=Path(manifest['path']);before=path.stat()
    assert stat.S_ISREG(before.st_mode) and before.st_size==manifest['bytes']
    assert zipfile.ZIP_ZSTANDARD==93
    archive=OUT/'initial-upper.wire.zip';entry=zipfile.ZipInfo('initial-upper.wire')
    entry.create_system=3;entry.external_attr=before.st_mode<<16
    entry.extra=struct.pack('<HHQ',0xa6da,8,before.st_mtime_ns)
    entry.compress_type=zipfile.ZIP_ZSTANDARD;entry.compress_level=15
    h=hashlib.sha256();size=0
    with common.watched():
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_ZSTANDARD,compresslevel=15) as saved:
            with path.open('rb') as source,saved.open(entry,'w',force_zip64=True) as target:
                for block in iter(lambda:source.read(2**20),b''):
                    target.write(block);h.update(block);size+=len(block)
                    storage(frozen,8*2**20)
        assert size==manifest['bytes'] and h.hexdigest()==manifest['sha256']
        decoded=hashlib.sha256();count=rows=0
        with zipfile.ZipFile(archive) as saved:
            assert saved.namelist()==['initial-upper.wire']
            assert saved.getinfo('initial-upper.wire').file_size==manifest['bytes']
            with saved.open('initial-upper.wire') as source:
                for block in iter(lambda:source.read(2**20),b''):
                    decoded.update(block);count+=len(block);rows+=block.count(b'\n')
        assert decoded.hexdigest()==manifest['sha256'] and count==size and rows==manifest['rows']
        after=path.stat();assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
        assert all(common.sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        storage(frozen,8*2**20)
        atomic_json(OUT/'roundtrip.json',dict(finished_utc=utc(),accepted=True,archive=str(archive),
            archive_bytes=archive.stat().st_size,archive_sha256=common.sha(archive),
            archive_entry='initial-upper.wire',compression_method='ZIP_ZSTANDARD93',compression_level=15,
            raw_sha256=manifest['sha256'],raw_bytes=size,raw_rows=rows,exact_roundtrip_verified=True,
            source_unchanged=True,p1_unchanged=True,raw_source_not_removed_by_worker=True,
            agda_checks=0,native_solver_runs=0,mathematical_objective_complete=False))


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,previous.sandbox()+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],
        OUT/'records',root=OUT/'control',timeout=230,cpu_limit=OUTER,rss_limit_gib=1.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior=json.loads((SOURCE/'closure.json').read_text())['combined_family_cpu_seconds']
    assert prior+RESERVE+ALLOWANCE<=5650
    latest=OUT.with_name('lower-prefix-inline-probe6-20261018')
    frozen=json.loads((latest/'storage-freeze.json').read_text())
    used=frozen['prior_allocated_study_bytes']+batch.allocated(latest)
    assert used+CAP<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir();control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),prior_allocated_study_bytes=used,
        previous_closed_inventory=str(latest/'storage-freeze.json'),own_output_cap_bytes=CAP,
        retained_study_cap_gib=12,root_free_floor_gib=80,all_external_physical_bytes_counted=True))
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    plan=dict(created_utc=utc(),control_source=source_identity(control),helper_sha256=common.sha(Path(__file__)),
        python_binary_sha256=common.sha(Path(sys.executable)),python_version=sys.version,
        wire=json.loads((SOURCE/'wire-manifest.json').read_text()),p1_files=history['p1_files'],
        previous_combined_family_cpu_seconds=prior,family_cpu_cap=5650,
        reservation=RESERVE,outer_cpu_cap=OUTER,new_controller_allowance_seconds=ALLOWANCE,
        hard_memory_gib=2,swap_bytes=0,core_bytes=0,
        cleanup_policy='Coordinator may remove fresh raw wire only after completed job, exact roundtrip/hash verification and preserved archive; protected historical files remain untouched',
        accepted_proof=False,mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Lossless compaction of fresh UPPER wire after actual prefix/kernel checks; preserve global-native5650 cumulative family, all previous charges and physical12GiB cap')
    reservation=ledger.reserve('assembly',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    argv=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=2G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=250','--property=WorkingDirectory='+str(control),
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
