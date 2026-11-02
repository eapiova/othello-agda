"""Losslessly compact completed, generated desktop logs; no proof inputs change."""
import hashlib, json, os, shutil, struct, subprocess, sys, zipfile
from pathlib import Path
from provenance import source_identity
from run_job import atomic_json, run_job, utc
from study6 import Ledger
import completion_batch6 as batch

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT = BASE/'study-log-archive6-20261018'
UNIT = 'othello6-'+OUT.name+'.service'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''): h.update(block)
    return h.hexdigest()


def worker():
    plan = json.loads((OUT/'plan.json').read_text())
    assert sha(Path(__file__)) == plan['helper_sha256']
    archive = OUT/'logs.zip'; entries = {}
    def storage():
        own = batch.allocated(OUT)
        released = sum(e['allocated_bytes'] for e in entries.values() if e.get('removed'))
        assert own+8*2**20 < 32*2**20
        assert plan['prior_allocated_study_bytes']+own-released+8*2**20 < 12*2**30
        assert shutil.disk_usage(ROOT).free-2**20 >= 80*2**30
    storage()
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as saved:
        for name, expected in plan['logs'].items():
            p = BASE/name; s = p.stat()
            assert not p.is_symlink() and p.is_file() and s.st_nlink == 1
            assert [s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_ino] == expected
            raw = p.read_bytes(); assert len(raw) == s.st_size <= 4*2**20
            info = zipfile.ZipInfo(name); info.create_system = 3
            info.external_attr = s.st_mode << 16; info.compress_type = zipfile.ZIP_DEFLATED
            info.extra = struct.pack('<HHQ', 0xa6da, 8, s.st_mtime_ns)
            saved.writestr(info, raw)
            entries[name] = dict(size=s.st_size, sha256=hashlib.sha256(raw).hexdigest(),
                mode=s.st_mode, mtime_ns=s.st_mtime_ns, identity=expected, allocated_bytes=s.st_blocks*512)
            storage()
    with archive.open('rb') as stream: os.fsync(stream.fileno())
    with zipfile.ZipFile(archive) as saved:
        assert set(saved.namelist()) == set(entries)
        for name, entry in entries.items():
            assert hashlib.sha256(saved.read(name)).hexdigest() == entry['sha256']
            assert saved.getinfo(name).external_attr >> 16 == entry['mode']
    manifest = dict(created_utc=utc(),archive=str(archive),archive_sha256=sha(archive),
        entries=entries,complete=False,original_desktop_runs_untouched=True,
        mathematical_objective_complete=False)
    atomic_json(OUT/'manifest.json', manifest)
    with (OUT/'manifest.json').open('rb') as stream: os.fsync(stream.fileno())
    fd = os.open(OUT, os.O_RDONLY); os.fsync(fd); os.close(fd)
    for name, e in entries.items():
        p = BASE/name; s = p.stat()
        assert [s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino] == e['identity']
        assert sha(p) == e['sha256']; p.unlink(); e['removed'] = True; storage()
    manifest.update(complete=True,finished_utc=utc(),archive_bytes=archive.stat().st_size)
    atomic_json(OUT/'manifest.json',manifest)


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    # Only registered generated desktop outputs are writable. Protected old runs stay read-only.
    args=['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(BASE),str(BASE),
        '--proc','/proc','--dev-bind','/dev','/dev','--tmpfs','/tmp','--die-with-parent','--']
    result=run_job(OUT.name,args+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],
        OUT/'records',root=OUT/'control',timeout=100,cpu_limit=30,rss_limit_gib=.8,
        log_limit_mib=1,reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized(); assert not OUT.exists()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    previous=json.loads((BASE/'sealed-text-cache6-20261018/closure.json').read_text())
    assert previous['combined_scope_cpu_seconds']+50 <= 1500
    # Exact fresh physical audit provided by the coordinator, including every registered root.
    audit=json.loads((ROOT/'results/pre-log-archive-storage6-20261018.json').read_text())
    assert audit['allocated_study_bytes']+32*2**20 < 12*2**30
    logs={p.relative_to(BASE).as_posix():[p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns,p.stat().st_ino]
        for p in sorted(BASE.rglob('*.log')) if p.is_file() and not p.is_symlink() and p.stat().st_size>=65536}
    assert len(logs)<=300 and sum(v[0] for v in logs.values())<=64*2**20
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    plan=dict(created_utc=utc(),helper_sha256=sha(Path(__file__)),logs=logs,
        prior_allocated_study_bytes=audit['allocated_study_bytes'],
        previous_combined_scope_cpu_seconds=previous['combined_scope_cpu_seconds'],
        reservation_cpu_seconds=40,controller_allowance_cpu_seconds=10,scope_cap_cpu_seconds=1500,
        hard_memory_gib=1,swap_bytes=0,core_bytes=0,own_output_cap_mib=32,
        retained_study_cap_gib=12,root_free_floor_gib=80,proof_sources_and_interfaces_unchanged=True)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json'); assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',10,'Losslessly compact completed generated logs before LOWER full-map preparation; preserve all old CPU and exact archived evidence')
    reservation=ledger.reserve('assembly',40,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=source_identity(OUT/'control')))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=1G',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%',
        '--property=TasksMax=64','--property=KillMode=control-group','--property=RuntimeMaxSec=120',
        '--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,logs=len(logs),reservation=reservation)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','supervise','worker']
    if sys.argv[1]=='launch': launch()
    elif sys.argv[1]=='worker': worker()
    else: raise SystemExit(supervise())
