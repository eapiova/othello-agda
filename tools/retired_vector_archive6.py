"""Durable file-by-file archive of the retired, unused UPPER vector cache.

Delete a file only after its exact bytes are durably stored and independently
verified. Receipts outside check/ and all protected original runs stay read-only.
"""
import hashlib,json,os,shutil,stat,struct,subprocess,sys,zipfile
from pathlib import Path
import assembly6
import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity,digest_entries
from run_job import atomic_json,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
SOURCE=BASE/'full-upper-probe6-20261018/check'
OUT=BASE/'retired-vector-archive6-20261018';UNIT='othello6-'+OUT.name+'.service'
RESERVE=140;OUTER=110;ALLOWANCE=10;CAP=160*2**20
previous.OUT=OUT;common.OUT=OUT;common.HARD_GIB=2;common.RESERVATION_CPU=RESERVE


def durable(path,data):
    atomic_json(path,data)
    with path.open('rb') as f:os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()


def worker():
    plan=json.loads((OUT/'plan.json').read_text());frozen=json.loads((OUT/'storage-freeze.json').read_text())
    assert sha(Path(__file__))==plan['helper_sha256']
    assert source_identity(SOURCE)['source_sha256']==plan['source_sha256']
    assert digest_entries(assembly6.interfaces(SOURCE))==plan['interface_pool_sha256']
    entries={};total=0
    for p in sorted(SOURCE.rglob('*')):
        s=p.lstat();assert not p.is_symlink() and (p.is_file() or p.is_dir()) and s.st_nlink>=1
        name=p.relative_to(SOURCE).as_posix()+('/' if p.is_dir() else '')
        assert len(name)<4094 and len(entries)<5000
        if p.is_file():assert s.st_nlink==1 and s.st_size<=16*2**20
        total+=s.st_size if p.is_file() else 0;assert total<=200*2**20
        entries[name]=dict(size=s.st_size if p.is_file() else 0,mode=s.st_mode,mtime_ns=s.st_mtime_ns,
            inode=s.st_ino,ctime_ns=s.st_ctime_ns,allocated_bytes=s.st_blocks*512,
            sha256=sha(p) if p.is_file() else hashlib.sha256(b'').hexdigest())
    journal=dict(created_utc=utc(),source=str(SOURCE),source_sha256=plan['source_sha256'],
        interface_pool_sha256=plan['interface_pool_sha256'],entries=entries,verified_and_removed=[],complete=False)
    durable(OUT/'journal.json',journal);released=0
    def storage(reserve=0):
        remaining=max(frozen['initial_source_allocated_bytes']-released,batch.allocated(SOURCE))
        own=batch.allocated(OUT);used=frozen['prior_without_source_allocated_bytes']+remaining+own
        assert own+reserve<=CAP and used+reserve<12*2**30
        free=shutil.disk_usage(ROOT).free;assert free-2**20>=80*2**30
        assert shutil.disk_usage(OUT).free-reserve>=80*2**30
        return dict(allocated_study_bytes=used,own_output_bytes=own,conservative_source_remaining_bytes=remaining,
            root_free_bytes=free,reserved_bytes=reserve,checked_utc=utc())
    common.storage=storage;archive=OUT/'retired-vector-check.zip'
    with common.watched():
        for name,e in entries.items():
            p=SOURCE/name;s=p.stat();assert s.st_ino==e['inode'] and s.st_mtime_ns==e['mtime_ns']
            raw=p.read_bytes() if p.is_file() else b'';assert len(raw)==e['size'] and hashlib.sha256(raw).hexdigest()==e['sha256']
            info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=e['mode']<<16
            info.extra=struct.pack('<HHQ',0xa6da,8,e['mtime_ns']);info.compress_type=zipfile.ZIP_DEFLATED
            with zipfile.ZipFile(archive,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as saved:saved.writestr(info,raw)
            with archive.open('rb') as f:os.fsync(f.fileno())
            with zipfile.ZipFile(archive) as saved:
                assert hashlib.sha256(saved.read(name)).hexdigest()==e['sha256']
                zi=saved.getinfo(name);assert zi.external_attr>>16==e['mode'] and zi.extra==info.extra
            journal['verified_and_removed'].append(name);durable(OUT/'journal.json',journal)
            if stat.S_ISREG(e['mode']):
                now=p.stat();assert (now.st_ino,now.st_size,now.st_mtime_ns,now.st_ctime_ns)==(e['inode'],e['size'],e['mtime_ns'],e['ctime_ns'])
                p.unlink();released+=e['allocated_bytes']
            storage(8*2**20)
        assert not any(p.is_file() or p.is_symlink() for p in SOURCE.rglob('*'))
        with zipfile.ZipFile(archive) as saved:
            assert set(saved.namelist())==set(entries)
            for name,e in entries.items():assert hashlib.sha256(saved.read(name)).hexdigest()==e['sha256']
        for p in sorted(SOURCE.rglob('*'),key=lambda p:len(p.parts),reverse=True):p.rmdir()
        assert all(sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        journal.update(complete=True,finished_utc=utc(),archive=str(archive),archive_sha256=sha(archive))
        durable(OUT/'journal.json',journal)
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=True,entries=len(entries),raw_bytes=total,
            archive=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),
            every_file_verified_before_removal=True,all_entries_reverified=True,all_original_metadata_preserved=True,
            empty_source_directory_remaining=True,p1_unchanged=True,old_desktop_runs_and_NAMOR_untouched=True,
            native_solver_runs=0,agda_checks=0,mathematical_objective_complete=False))


def supervise():
    job=json.loads((OUT/'job.json').read_text());sandbox=previous.sandbox()
    sandbox=sandbox[:-1]+['--bind',str(SOURCE),str(SOURCE),'--']
    result=run_job(OUT.name,sandbox+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=300,cpu_limit=OUTER,rss_limit_gib=1.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and SOURCE.is_dir() and not SOURCE.is_symlink()
    assert not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running','--type=service','--no-legend','--plain','othello*'],text=True).strip()
    latest=json.loads((BASE/'text-parametric-assembly6-20261018/closure.json').read_text());prior=latest['combined_scope_cpu_seconds']
    assert latest['accepted'] and prior+RESERVE+ALLOWANCE<=1500
    expected=json.loads((BASE/'text-parametric-assembly6-20261018/plan.json').read_text())['donors'];assert str(SOURCE) not in expected
    old=json.loads((SOURCE.parent/'closure.json').read_text());assert old['accepted_full_state_data'] and not old['accepted']
    snapshot=json.loads((ROOT/'results/full-text-upper-final-audit6-20261018.json').read_text())
    used=snapshot['allocated_study_bytes'];assert used+16*2**20<12*2**30
    OUT.mkdir();control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),prior_allocated_study_bytes=used,
        initial_source_allocated_bytes=batch.allocated(SOURCE),prior_without_source_allocated_bytes=used-batch.allocated(SOURCE),
        own_output_cap_bytes=CAP,retained_study_cap_gib=12,ordinary_root_floor_gib=80,rolling_input_and_archive_physical_bytes_counted=True))
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    plan=dict(created_utc=utc(),control_source=source_identity(control),helper_sha256=sha(Path(__file__)),
        source_sha256=old['source_sha256'],interface_pool_sha256=old['interface_pool_sha256'],p1_files=history['p1_files'],
        retired_vector_dataset_excluded_from_current_accepted_donors=True,
        previous_combined_scope_cpu_seconds=prior,scope_cpu_cap=1500,reservation=RESERVE,outer_cpu_cap=OUTER,
        new_controller_allowance_seconds=ALLOWANCE,hard_memory_gib=2,swap_bytes=0,core_bytes=0,
        mutation_scope=str(SOURCE),authorization='Authorized cleanup/necessary proof storage: byte-exact recoverable archive before releasing unused generated cache files',mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Durable staged archive of unused full vector dataset, all files/metadata retained, live text cache untouched; include all old inline1500 actuals')
    reservation=ledger.reserve('assembly',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    argv=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=2G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=320','--property=WorkingDirectory='+str(control),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(argv,capture_output=True,text=True);atomic_json(OUT/'dispatch.json',dict(argv=argv,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,combined_scope_reserved=prior+RESERVE+ALLOWANCE)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','supervise','worker']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
