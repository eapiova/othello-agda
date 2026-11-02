"""Remove inactive cache copies only when exact bytes remain in a pinned TAR.

AI-assisted maintenance. Source and every active donor remain untouched.
"""
import hashlib,json,os,shutil,subprocess,sys,tarfile
from pathlib import Path
import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity
from run_job import atomic_json,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OLD=BASE/'relocated-current-artifacts'
OUT=BASE/'archived-cache-duplicates6-20261018'
UNIT='othello6-'+OUT.name+'.service'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for b in iter(lambda:stream.read(2**20),b''):h.update(b)
    return h.hexdigest()


def worker():
    plan=json.loads((OUT/'plan.json').read_text())
    assert sha(Path(__file__))==plan['helper_sha256']
    by_name={};found={}
    for name,e in plan['candidates'].items():by_name.setdefault(Path(name).name,[]).append((name,e))
    for archive,identity in plan['archives'].items():
        file=Path(archive);s=file.stat()
        assert [s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino]==identity
        pin=sha(file)
        with tarfile.open(file,'r|gz') as saved:
            for member in saved:
                choices=by_name.get(Path(member.name).name,[])
                if not member.isfile() or not choices or member.size>16*2**20:continue
                choices=[(n,e) for n,e in choices if n not in found and e['bytes']==member.size]
                if not choices:continue
                raw=saved.extractfile(member).read();digest=hashlib.sha256(raw).hexdigest()
                for name,e in choices:
                    if digest==e['sha256']:
                        found[name]=dict(**e,archive=archive,archive_sha256=pin,
                            member=member.name,member_mode=member.mode,member_mtime=member.mtime)
        assert sha(file)==pin
    atomic_json(OUT/'restore-map.json',dict(created_utc=utc(),original_root=str(OLD),entries=found,
        all_removed_bytes_retained_exact_in_existing_archives=True,original_desktop_runs_untouched=True))
    with (OUT/'restore-map.json').open('rb') as stream:os.fsync(stream.fileno())
    fd=os.open(OUT,os.O_RDONLY);os.fsync(fd);os.close(fd)
    released=0
    for name,e in found.items():
        file=OLD/name;s=file.stat()
        assert [s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino]==e['identity']
        assert s.st_nlink==1 and sha(file)==e['sha256']
        assert not any(file.resolve().is_relative_to(Path(p).resolve()) for p in plan['protected_roots'])
        file.unlink();released+=e['allocated_bytes']
    assert all(sha(ROOT/n)==h for n,h in plan['p1_files'].items())
    own=batch.allocated(OUT)
    assert own<4*2**20 and plan['prior_allocated_study_bytes']+own-released<12*2**30
    assert shutil.disk_usage(ROOT).free-2**20>=80*2**30
    atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=True,removed_cache_copies=len(found),
        released_allocated_bytes=released,unmatched_candidates_left_in_place=len(plan['candidates'])-len(found),
        source_and_active_donors_untouched=True,p1_unchanged=True,restore_map=str(OUT/'restore-map.json'),
        all_proof_bytes_still_preserved_in_existing_archives=True,mathematical_objective_complete=False))


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    sandbox=['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(BASE),str(BASE),
        '--proc','/proc','--dev-bind','/dev','/dev','--tmpfs','/tmp','--die-with-parent','--']
    r=run_job(OUT.name,sandbox+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],
        OUT/'records',root=OUT/'control',timeout=500,cpu_limit=150,rss_limit_gib=1.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if r['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior=json.loads((BASE/'complete-row-preflight6-20261018/closure.json').read_text())
    assert prior['accepted'] and prior['combined_scope_cpu_seconds']+190<=6000
    common.OUT=ROOT/'results/audit-no-output6-20261018';legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    paths={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    reg=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths|={Path(e['path']) for e in reg['roots'] if Path(e['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+4*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    donors=json.loads((BASE/'packed-lower-cache6-20261018/plan.json').read_text())['donors']
    protected=[Path(p).resolve() for p in donors]
    candidates={}
    for file in sorted(OLD.rglob('*.agdai')):
        if file.is_symlink() or not file.is_file() or any(file.resolve().is_relative_to(p) for p in protected):continue
        s=file.stat()
        if s.st_nlink!=1:continue
        candidates[file.relative_to(OLD).as_posix()]=dict(bytes=s.st_size,sha256=sha(file),
            allocated_bytes=s.st_blocks*512,mode=s.st_mode,mtime_ns=s.st_mtime_ns,
            identity=[s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino])
    archives={}
    for file in sorted(OLD.rglob('*.tar.gz')):
        if file.is_file() and not file.is_symlink():
            s=file.stat();archives[str(file)]=[s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino]
    assert len(candidates)<=1000 and sum(e['bytes'] for e in candidates.values())<=64*2**20
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    plan=dict(created_utc=utc(),helper_sha256=sha(Path(__file__)),control_source=source_identity(OUT/'control'),
        candidates=candidates,archives=archives,protected_roots=list(donors),p1_files=history['p1_files'],
        prior_allocated_study_bytes=used,previous_combined_scope_cpu_seconds=prior['combined_scope_cpu_seconds'],
        new_controller_allowance_seconds=10,scope_cpu_cap=6000,hard_memory_gib=2,swap_bytes=0,core_bytes=0,
        root_free_floor_gib=80,retained_study_cap_gib=12,mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',10,'Remove inactive cache duplicates only after durable exact-byte restore map to unchanged existing archives; active source/proof donors and all original runs remain untouched; inline6000 preserved')
    reservation=ledger.reserve('assembly',180,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=2G',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%',
        '--property=TasksMax=64','--property=KillMode=control-group','--property=RuntimeMaxSec=530',
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,candidates=len(candidates),archives=len(archives))))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
